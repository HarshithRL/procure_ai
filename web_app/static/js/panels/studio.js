// Studio panel: tri-column knowledge-graph SVG (Vendor | Requirement |
// Article / Term) ported from the design prototype, weighted ranking +
// requirement matrix, TCO view, and the comparison-workbook tab. Also fills
// the KPI strip above the chat. Talks to /api/projects/<id>/graph,
// /comparison and /exports.

"use strict";

const StudioPanel = (() => {
    let projectId = null;
    let graph = { nodes: [], edges: [], stats: {} };
    let comparison = { vendors: [] };
    let selectedVendor = null;
    let graphView = "graph"; // graph | table
    let genState = 0; // 0 = generate, 1 = generating, 2 = download
    let downloadUrl = null;
    let graphHealth = null;
    let maintainBusy = false;

    const SHEETS = [
        "Pricing Scheme", "Executive Summary", "Supplier Ranking", "3-Year Cost View",
        "Commercial Terms", "Next Steps", "RACI",
    ];

    function el(id) {
        return document.getElementById(id);
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str == null ? "" : String(str);
        return div.innerHTML;
    }

    function fmtEur(value) {
        if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
        return new Intl.NumberFormat("en-US", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(value);
    }

    function fmtEurM(value) {
        if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
        return `€${(Number(value) / 1_000_000).toFixed(2)} M`;
    }

    // ---- data shaping --------------------------------------------------------

    function nodesByType(type) {
        return graph.nodes.filter((node) => node.type === type);
    }

    function shortName(name, max = 20) {
        const value = String(name || "");
        return value.length > max ? `${value.slice(0, max - 1)}…` : value;
    }

    // Vendor -> displayed-target edges. price_quote hops are collapsed into
    // vendor -> article so the tri-column layout stays readable.
    function displayEdges() {
        const quoteToArticle = new Map();
        graph.edges.forEach((edge) => {
            if (edge.relation === "prices_article") quoteToArticle.set(edge.source_id, edge.target_id);
        });
        const out = [];
        graph.edges.forEach((edge) => {
            if (edge.relation === "extracted_from") return;
            if (edge.relation === "prices_article") return;
            let target = edge.target_id;
            if (edge.relation === "quotes") {
                target = quoteToArticle.get(edge.target_id) || null;
                if (!target) return;
            }
            out.push({ source: edge.source_id, target, edge });
        });
        return out;
    }

    // ---- KPI strip -----------------------------------------------------------

    function renderKpis() {
        const stats = graph.stats || {};
        const vendors = comparison.vendors || [];

        const coverage = vendors.length ? Math.max(...vendors.map((v) => v.weighted_coverage_pct || 0)) : null;
        if (el("kpi-coverage")) {
            el("kpi-coverage").textContent = coverage === null ? "—" : `${Math.round(coverage)}%`;
            el("kpi-coverage-bar").style.width = coverage === null ? "0%" : `${Math.min(100, Math.round(coverage))}%`;
        }

        const totals = vendors.map((v) => Number(v.total_tco)).filter((v) => !Number.isNaN(v) && v > 0);
        if (el("kpi-tco")) {
            if (totals.length >= 2) {
                const low = Math.min(...totals);
                const high = Math.max(...totals);
                el("kpi-tco").textContent = `${(((high - low) / low) * 100).toFixed(1)}%`;
                el("kpi-tco-range").textContent = `${fmtEurM(low)} — ${fmtEurM(high)}`;
            } else {
                el("kpi-tco").textContent = "—";
                el("kpi-tco-range").textContent = "needs two priced vendors";
            }
        }

        if (el("kpi-evidence")) {
            const edges = stats.edges || 0;
            const linked = stats.evidence_linked || 0;
            el("kpi-evidence").textContent = edges === 0 ? "—" : `${Math.round((linked / edges) * 100)}%`;
            el("kpi-evidence-detail").textContent = edges === 0
                ? "no graph yet"
                : `${linked.toLocaleString("en-US")} of ${edges.toLocaleString("en-US")} edges`;
        }

        if (el("kpi-contradictions")) {
            el("kpi-contradictions").textContent = String(stats.contradictions ?? 0);
        }

        if (el("studio-graph-count")) {
            el("studio-graph-count").textContent = (stats.nodes || stats.edges)
                ? `${(stats.nodes || 0).toLocaleString("en-US")} nodes · ${(stats.edges || 0).toLocaleString("en-US")} edges`
                : "";
        }
    }

    // ---- Graph tab -----------------------------------------------------------

    const SVG_NS = "http://www.w3.org/2000/svg";

    function svgEl(tag, attrs, text) {
        const node = document.createElementNS(SVG_NS, tag);
        Object.entries(attrs || {}).forEach(([key, value]) => node.setAttribute(key, value));
        if (text !== undefined) node.textContent = text;
        return node;
    }

    function buildSvg(vendors, mids, rights, edges) {
        const rows = Math.max(vendors.length, 4);
        const height = Math.max(346, 46 + rows * 39 + 24);
        const pos = {};
        vendors.forEach((v, i) => { pos[v.id] = { x: 112, y: 46 + i * 39 }; });
        const midStep = Math.max(48, (height - 100) / Math.max(1, mids.length));
        mids.forEach((m, i) => { pos[m.id] = { x: 250, y: 74 + i * midStep }; });
        const rightStep = Math.max(48, (height - 100) / Math.max(1, rights.length));
        rights.forEach((r, i) => { pos[r.id] = { x: 366, y: 74 + i * rightStep }; });

        const svg = svgEl("svg", { viewBox: `0 0 420 ${height}`, width: "100%", style: "display:block" });

        [["VENDOR", 112], ["REQUIREMENT", 250], ["ARTICLE / TERM", 366]].forEach(([label, x]) => {
            svg.appendChild(svgEl("text", {
                x, y: 16, "text-anchor": "middle", "font-size": 8, fill: "currentColor",
                opacity: 0.45, "letter-spacing": "0.1em",
            }, label));
        });

        edges.forEach(({ source, target }) => {
            const a = pos[source];
            const b = pos[target];
            if (!a || !b) return;
            const on = source === selectedVendor;
            svg.appendChild(svgEl("path", {
                d: `M${a.x} ${a.y} C${a.x + 48} ${a.y} ${b.x - 48} ${b.y} ${b.x} ${b.y}`,
                fill: "none",
                stroke: on ? "var(--color-accent)" : "currentColor",
                "stroke-width": on ? 1.25 : 0.7,
                opacity: on ? 0.85 : 0.08,
            }));
        });

        const selTargets = new Set(edges.filter((e) => e.source === selectedVendor).map((e) => e.target));
        mids.concat(rights).forEach((node) => {
            const p = pos[node.id];
            const on = selTargets.has(node.id);
            svg.appendChild(svgEl("text", {
                x: p.x, y: p.y - 9, "text-anchor": "middle", "font-size": 8.5,
                fill: "currentColor", opacity: on ? 0.92 : 0.4,
            }, shortName(node.name, 24)));
            svg.appendChild(svgEl("circle", {
                cx: p.x, cy: p.y, r: 3.4, fill: "var(--color-bg)",
                stroke: on ? "var(--color-accent)" : "currentColor", "stroke-width": 1, opacity: on ? 1 : 0.4,
            }));
        });

        vendors.forEach((vendor) => {
            const p = pos[vendor.id];
            const on = vendor.id === selectedVendor;
            const group = svgEl("g", { style: "cursor:pointer" });
            group.appendChild(svgEl("rect", { x: 4, y: p.y - 9, width: 112, height: 18, fill: "transparent" }));
            group.appendChild(svgEl("text", {
                x: p.x - 11, y: p.y + 3, "text-anchor": "end", "font-size": 9.5,
                fill: "currentColor", opacity: on ? 1 : 0.6, "font-weight": on ? 600 : 400,
            }, shortName(vendor.name, 18)));
            group.appendChild(svgEl("circle", {
                cx: p.x, cy: p.y, r: on ? 5 : 3.4,
                fill: on ? "var(--color-accent)" : "var(--color-bg)",
                stroke: on ? "var(--color-accent)" : "currentColor", "stroke-width": 1, opacity: on ? 1 : 0.45,
            }));
            group.addEventListener("click", () => {
                selectedVendor = vendor.id;
                renderGraphPane();
            });
            svg.appendChild(group);
        });

        return svg;
    }

    function relationLabel(edge) {
        const verdict = edge.attributes && (edge.attributes.verdict || edge.attributes.status);
        if (verdict) return String(verdict).toUpperCase();
        return String(edge.relation || "").toUpperCase();
    }

    function nodeName(id) {
        const node = graph.nodes.find((n) => n.id === id);
        return node ? node.name : id;
    }

    function vendorCard(vendor, vendorEdges) {
        const comp = (comparison.vendors || []).find((v) => v.vendor === vendor.name) || {};
        const evidence = vendorEdges.flatMap(({ edge }) => edge.evidence || []);
        const grounded = evidence.slice(0, 3);
        const rows = grounded.length
            ? grounded
                .map((ev, index) => `
                    <button class="app-row-btn app-num card-ev" data-ev-i="${index}" style="display:flex;gap:7px;font-size:10.5px;padding:4px 2px">
                        <span class="app-accent-text">${index + 1}</span>
                        <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(ev.document_id)}</span>
                        <span class="app-faint">${escapeHtml(ev.locator || "")}</span>
                    </button>`)
                .join("")
            : '<span class="app-faint" style="font-size:10.5px">No evidence recorded yet.</span>';

        return `
            <hr class="hr">
            <div class="card">
                <span class="card-kicker">Selected node</span>
                <span class="card-title">${escapeHtml(vendor.name)}</span>
                <div class="app-num" style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:11px">
                    <span><span class="app-faint" style="display:block;font-size:9.5px">Type</span>Vendor</span>
                    <span><span class="app-faint" style="display:block;font-size:9.5px">Degree</span>${vendorEdges.length}</span>
                    <span><span class="app-faint" style="display:block;font-size:9.5px">Evidence refs</span>${evidence.length}</span>
                    <span><span class="app-faint" style="display:block;font-size:9.5px">Coverage</span>${comp.weighted_coverage_pct != null ? `${comp.weighted_coverage_pct}%` : "—"}</span>
                </div>
                <hr class="hr" style="margin:2px 0">
                <span class="app-faint" style="font-size:9.5px;letter-spacing:.1em;text-transform:uppercase">Grounded in</span>
                ${rows}
            </div>`;
    }

    function renderGraphPane() {
        const pane = el("studio-pane-graph");
        if (!pane) return;

        const vendors = nodesByType("vendor").slice(0, 10);
        if (vendors.length === 0) {
            pane.innerHTML = '<p class="app-faint" style="font-size:11.5px;margin:6px 2px">No knowledge graph yet — upload and ingest vendor documents first.</p>';
            return;
        }
        if (!selectedVendor || !vendors.some((v) => v.id === selectedVendor)) {
            selectedVendor = vendors[0].id;
        }

        const mids = nodesByType("requirement").slice(0, 6);
        const rights = nodesByType("article").concat(nodesByType("commercial_term")).slice(0, 6);
        const shown = new Set([...vendors, ...mids, ...rights].map((n) => n.id));
        const edges = displayEdges().filter((e) => shown.has(e.source) && shown.has(e.target));
        const vendorEdges = displayEdges().filter((e) => e.source === selectedVendor);

        pane.innerHTML = `
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
                <span class="app-faint" style="font-size:10.5px;flex:1">Vendor → requirement → article. Click a vendor to trace its edges.</span>
                <button class="app-tab" id="gv-graph" aria-pressed="${graphView === "graph"}">Graph</button>
                <button class="app-tab" id="gv-table" aria-pressed="${graphView === "table"}">Triples</button>
                <button class="app-tab" id="gv-expand" title="Open the full interactive graph">⛶ Expand</button>
            </div>
            <div id="gv-body"></div>`;

        const body = pane.querySelector("#gv-body");
        if (graphView === "graph") {
            const frame = document.createElement("div");
            frame.style.cssText = "border:1px solid var(--color-divider);border-radius:var(--radius-md);padding:8px 6px";
            frame.appendChild(buildSvg(vendors, mids, rights, edges));
            body.appendChild(frame);
            const legend = document.createElement("div");
            legend.className = "app-faint";
            legend.style.cssText = "display:flex;gap:14px;font-size:10px;margin-top:8px";
            legend.innerHTML = `
                <span style="display:flex;align-items:center;gap:5px"><i class="app-dot"></i>selected vendor</span>
                <span style="display:flex;align-items:center;gap:5px"><i class="app-dot is-quiet"></i>other node</span>
                <span>${shown.size} of ${graph.nodes.length} nodes shown</span>`;
            body.appendChild(legend);
        } else {
            const rows = vendorEdges
                .map(({ edge, target }, index) => {
                    const ev = (edge.evidence || [])[0];
                    return `
                        <div class="app-div-b" style="display:grid;grid-template-columns:1fr 92px 1fr 30px;gap:4px;font-size:11px;padding:6px 2px;align-items:baseline">
                            <span>${escapeHtml(nodeName(edge.source_id))}</span>
                            <span class="app-accent-text app-num" style="font-size:9.5px">${escapeHtml(relationLabel(edge))}</span>
                            <span>${escapeHtml(nodeName(target))}</span>
                            <span style="text-align:right">${ev ? `<button class="app-chip triple-ev" data-edge-i="${index}" type="button">${index + 1}</button>` : ""}</span>
                        </div>`;
                })
                .join("");
            body.innerHTML = `
                <div class="app-num app-div-b" style="display:grid;grid-template-columns:1fr 92px 1fr 30px;font-size:9px;letter-spacing:.08em;text-transform:uppercase;padding:0 2px 6px;color:color-mix(in srgb, var(--color-text) 58%, transparent)">
                    <span>Subject</span><span>Predicate</span><span>Object</span><span style="text-align:right">Ev</span>
                </div>
                ${rows || '<p class="app-faint" style="font-size:11px;padding:8px 2px">No edges for this vendor yet.</p>'}`;
            body.querySelectorAll(".triple-ev").forEach((chip) => {
                chip.addEventListener("click", () => {
                    const entry = vendorEdges[Number(chip.dataset.edgeI)];
                    const ev = entry && (entry.edge.evidence || [])[0];
                    if (ev && typeof EvidencePanel !== "undefined") {
                        EvidencePanel.show(ev, Number(chip.dataset.edgeI) + 1, {
                            triple: `${nodeName(entry.edge.source_id)} —[${relationLabel(entry.edge)}]→ ${nodeName(entry.target)}`,
                        });
                    }
                });
            });
        }

        const selVendorNode = vendors.find((v) => v.id === selectedVendor);
        pane.insertAdjacentHTML("beforeend", vendorCard(selVendorNode, vendorEdges));
        pane.querySelectorAll(".card-ev").forEach((btn) => {
            btn.addEventListener("click", () => {
                const evidence = vendorEdges.flatMap(({ edge }) => edge.evidence || []);
                const ev = evidence[Number(btn.dataset.evI)];
                if (ev && typeof EvidencePanel !== "undefined") {
                    EvidencePanel.show(ev, Number(btn.dataset.evI) + 1);
                }
            });
        });

        // Add intelligence, evaluation, and decision sections
        pane.insertAdjacentHTML("beforeend", renderIntelligenceSection());
        pane.insertAdjacentHTML("beforeend", renderEvaluationSection());
        pane.insertAdjacentHTML("beforeend", renderDecisionSection());

        pane.querySelector("#gv-graph").addEventListener("click", () => { graphView = "graph"; renderGraphPane(); });
        pane.querySelector("#gv-table").addEventListener("click", () => { graphView = "table"; renderGraphPane(); });
        pane.querySelector("#gv-expand").addEventListener("click", () => {
            if (typeof GraphExplorer !== "undefined") {
                GraphExplorer.open(graph, { projectId, focusNodeId: selectedVendor });
            }
        });
    }

    // ---- Intelligence section -----------------------------------------------

    function renderIntelligenceSection() {
        const findings = nodesByType("finding");
        const risks = nodesByType("risk");
        const opportunities = nodesByType("opportunity");
        const missingInfo = nodesByType("missing_information");
        
        if (findings.length + risks.length + opportunities.length + missingInfo.length === 0) return "";
        
        const sections = [
            { type: "finding", label: "Findings", icon: "💡", nodes: findings },
            { type: "risk", label: "Risks", icon: "⚠️", nodes: risks },
            { type: "opportunity", label: "Opportunities", icon: "✨", nodes: opportunities },
            { type: "missing_information", label: "Information Gaps", icon: "❓", nodes: missingInfo },
        ];
        
        const content = sections
            .filter(s => s.nodes.length > 0)
            .map(section => {
                const list = section.nodes.slice(0, 4)
                    .map(n => `<div style="font-size:11px;padding:4px 0;overflow:hidden;text-overflow:ellipsis">${section.icon} ${escapeHtml(shortName(n.name, 40))}</div>`)
                    .join("");
                return `<div style="flex:1">
                    <h6 style="margin:0 0 4px;font-size:11px">${section.label} <span class="app-faint app-num">(${section.nodes.length})</span></h6>
                    ${list}
                </div>`;
            })
            .join("");
        
        return `<hr class="hr">
            <h6 style="margin:0 0 8px">Intelligence</h6>
            <div style="display:flex;gap:12px">${content}</div>`;
    }

    // ---- Evaluation section -------------------------------------------------

    function renderEvaluationSection() {
        const evals = nodesByType("evaluation");
        if (evals.length === 0) return "";
        
        const scoreTypes = ["technical", "commercial", "financial", "operational"];
        let content = "";
        
        scoreTypes.forEach(type => {
            const vendors = (comparison.vendors || []).slice(0, 5);
            if (vendors.length === 0) return;
            
            const rows = vendors
                .map(v => {
                    const score = v[`${type}_score`];
                    const maxScore = 100;
                    return `<div class="app-div-b" style="display:grid;grid-template-columns:1fr 60px;gap:6px;font-size:11px;padding:4px 2px;align-items:center">
                        <span>${escapeHtml(shortName(v.vendor, 16))}</span>
                        <span class="app-num" style="text-align:right">${score != null ? `${score}/100` : "—"}</span>
                    </div>`;
                })
                .join("");
            
            content += `<div style="flex:1">
                <h6 style="margin:0 0 4px;font-size:11px;text-transform:capitalize">${type}</h6>
                ${rows}</div>`;
        });
        
        return content ? `<hr class="hr"><h6 style="margin:0 0 8px">Evaluation Scores</h6><div style="display:flex;gap:12px">${content}</div>` : "";
    }

    // ---- Decision section ---------------------------------------------------

    function renderDecisionSection() {
        const decisions = nodesByType("decision");
        const awards = nodesByType("award");
        const stakeholders = nodesByType("stakeholder");
        
        if (decisions.length === 0 && awards.length === 0) return "";
        
        const decision = decisions[0];
        const award = awards[0];
        
        let content = `<hr class="hr"><h6 style="margin:0 0 8px">Decision & Outcome</h6>`;
        
        if (decision) {
            const status = decision.attributes && (decision.attributes.status || decision.attributes.verdict) || "pending";
            content += `<div class="app-div-b" style="padding:6px;border-radius:var(--radius-md);background:color-mix(in srgb, var(--color-accent) 8%, transparent)">
                <div style="font-size:11px;font-weight:500">Decision Status</div>
                <div style="font-size:12px;color:var(--color-accent);margin-top:2px">${escapeHtml(String(status).toUpperCase())}</div>
            </div>`;
        }
        
        if (award) {
            const awardVendor = award.attributes && award.attributes.vendor_name || award.name;
            const contractValue = award.attributes && award.attributes.contract_value || "—";
            content += `<div class="app-div-b" style="padding:6px;border-radius:var(--radius-md);background:color-mix(in srgb, var(--color-accent) 8%, transparent);margin-top:6px">
                <div style="font-size:11px;font-weight:500">Award</div>
                <div style="font-size:12px;color:var(--color-accent);margin-top:2px">${escapeHtml(shortName(awardVendor, 30))}</div>
                <div style="font-size:10px;color:var(--color-accent);opacity:0.7">Value: ${fmtEur(contractValue)}</div>
            </div>`;
        }
        
        if (stakeholders.length > 0) {
            const stakeholderList = stakeholders.slice(0, 3)
                .map(s => `<div style="font-size:10px;padding:2px 0">${escapeHtml(shortName(s.name, 24))}</div>`)
                .join("");
            content += `<div style="margin-top:6px">
                <div style="font-size:10px;font-weight:500;color:var(--color-accent);margin-bottom:3px">Committee</div>
                ${stakeholderList}</div>`;
        }
        
        return content;
    }

    // ---- Ranking tab ---------------------------------------------------------

    const GLYPHS = { satisfies: "✓", meets: "✓", partial: "~", fails: "✗", unevidenced: "·" };

    function matrixGlyph(edge) {
        if (!edge) return "·";
        const verdict = String((edge.attributes && (edge.attributes.verdict || edge.attributes.status)) || "satisfies").toLowerCase();
        return GLYPHS[verdict] || "✓";
    }

    function renderRankPane() {
        const pane = el("studio-pane-rank");
        if (!pane) return;
        const vendors = comparison.vendors || [];
        if (vendors.length === 0) {
            pane.innerHTML = '<p class="app-faint" style="font-size:11.5px;margin:6px 2px">Ingest documents to see a ranking.</p>';
            return;
        }

        const maxScore = Math.max(...vendors.map((v) => Number(v.weighted_score) || 0), 0.001);
        const rows = vendors
            .map(
                (v) => `
                <div class="app-div-b" style="display:grid;grid-template-columns:20px 1fr 42px 84px 52px;gap:6px;font-size:11.5px;padding:7px 2px;align-items:center">
                    <span class="app-num app-faint">${v.rank}</span>
                    <span>${escapeHtml(v.vendor)}</span>
                    <span class="app-num" style="text-align:right">${v.weighted_coverage_pct != null ? `${v.weighted_coverage_pct}%` : "—"}</span>
                    <span style="display:flex;align-items:center;gap:6px">
                        <span class="app-bar" style="flex:1"><i style="width:${Math.round(((Number(v.weighted_score) || 0) / maxScore) * 100)}%"></i></span>
                        <span class="app-num" style="font-size:10.5px">${v.weighted_score ?? "—"}</span>
                    </span>
                    <span class="app-num app-faint" style="text-align:right">${v.total_tco ? fmtEurM(v.total_tco) : "—"}</span>
                </div>`
            )
            .join("");

        // Requirement matrix: vendor × up to 4 requirement nodes.
        const reqNodes = nodesByType("requirement").slice(0, 4);
        const vendorNodes = nodesByType("vendor");
        const meetsEdges = graph.edges.filter((e) => e.relation === "meets_requirement");
        let matrixHtml = "";
        if (reqNodes.length > 0 && vendorNodes.length > 0) {
            const header = reqNodes
                .map((r) => `<span style="text-align:center" title="${escapeHtml(r.name)}">${escapeHtml(shortName((r.attributes && r.attributes.code) || r.name, 6))}</span>`)
                .join("");
            const matrixRows = vendorNodes
                .map((vendor) => {
                    const cells = reqNodes
                        .map((req) => {
                            const edge = meetsEdges.find((e) => e.source_id === vendor.id && e.target_id === req.id);
                            return `<span class="app-num" style="text-align:center">${matrixGlyph(edge)}</span>`;
                        })
                        .join("");
                    return `
                        <div class="app-div-b" style="display:grid;grid-template-columns:1fr repeat(${reqNodes.length},34px);font-size:11.5px;padding:6px 2px">
                            <span>${escapeHtml(shortName(vendor.name, 24))}</span>${cells}
                        </div>`;
                })
                .join("");
            matrixHtml = `
                <hr class="hr">
                <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:8px">
                    <h6 style="margin:0">Requirement matrix</h6>
                    <span class="app-faint" style="font-size:10.5px;flex:1">✓ met · ~ partial · ✗ failed · · unevidenced</span>
                </div>
                <div class="app-num app-div-b" style="display:grid;grid-template-columns:1fr repeat(${reqNodes.length},34px);font-size:9px;letter-spacing:.06em;text-transform:uppercase;padding:0 2px 6px;color:color-mix(in srgb, var(--color-text) 58%, transparent)">
                    <span></span>${header}
                </div>
                ${matrixRows}`;
        }

        pane.innerHTML = `
            <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:10px">
                <h6 style="margin:0">Weighted ranking</h6>
                <span class="app-faint" style="font-size:10.5px;flex:1">weights from the brief</span>
            </div>
            <div class="app-num app-div-b" style="display:grid;grid-template-columns:20px 1fr 42px 84px 52px;font-size:9px;letter-spacing:.08em;text-transform:uppercase;padding:0 2px 6px;color:color-mix(in srgb, var(--color-text) 58%, transparent)">
                <span>#</span><span>Supplier</span><span style="text-align:right">Cov.</span><span>Score</span><span style="text-align:right">3-yr</span>
            </div>
            ${rows}
            ${matrixHtml}`;
    }

    // ---- TCO tab -------------------------------------------------------------

    function renderTcoPane() {
        const pane = el("studio-pane-tco");
        if (!pane) return;
        const vendors = comparison.vendors || [];
        const years = comparison.years || [];
        if (vendors.length === 0) {
            pane.innerHTML = '<p class="app-faint" style="font-size:11.5px;margin:6px 2px">Ingest documents to see a cost breakdown.</p>';
            return;
        }

        const yearCols = years.map((y) => `<span style="text-align:right">${y}</span>`).join("");
        const rows = vendors
            .map((v) => {
                const cells = years
                    .map((y) => `<span class="app-num app-muted" style="text-align:right">${v.tco_by_year && v.tco_by_year[String(y)] != null ? fmtEurM(v.tco_by_year[String(y)]) : "—"}</span>`)
                    .join("");
                return `
                    <div class="app-div-b" style="display:grid;grid-template-columns:1fr repeat(${years.length},64px) 64px;font-size:11.5px;padding:7px 2px;align-items:baseline">
                        <span>${escapeHtml(shortName(v.vendor, 22))}</span>${cells}
                        <span class="app-num" style="text-align:right">${fmtEurM(v.total_tco)}</span>
                    </div>`;
            })
            .join("");

        pane.innerHTML = `
            <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:10px">
                <h6 style="margin:0">3-year cost of ownership</h6>
                <span class="app-faint" style="font-size:10.5px;flex:1">from quoted prices, per year</span>
            </div>
            <div class="app-num app-div-b" style="display:grid;grid-template-columns:1fr repeat(${years.length},64px) 64px;font-size:9px;letter-spacing:.06em;text-transform:uppercase;padding:0 2px 6px;color:color-mix(in srgb, var(--color-text) 58%, transparent)">
                <span>Supplier</span>${yearCols}<span style="text-align:right">Total</span>
            </div>
            ${rows}
            ${renderNegotiation(comparison.negotiation_opportunities || [])}`;
    }

    function renderNegotiation(opportunities) {
        if (opportunities.length === 0) return "";
        const rows = opportunities
            .slice(0, 4)
            .map(
                (o) => `
                <div class="app-div-b" style="display:grid;grid-template-columns:64px 1fr;gap:12px;padding:10px 12px">
                    <span class="app-num app-accent-text" style="font-family:var(--font-heading);font-size:17px">${o.delta_pct != null ? `${o.delta_pct}%` : "—"}</span>
                    <span style="font-size:12.5px">${escapeHtml(o.vendor)} is above ${escapeHtml(o.best_vendor)} on ${escapeHtml(o.article)}.</span>
                </div>`
            )
            .join("");
        return `
            <hr class="hr">
            <div style="display:flex;align-items:baseline;gap:8px;margin-bottom:8px">
                <h6 style="margin:0">Negotiation openings</h6>
            </div>
            <div class="card" style="gap:0;padding:0">${rows}</div>`;
    }

    // ---- Workbook tab --------------------------------------------------------

    function genLabel() {
        return ["Generate workbook", "Generating…", "Download .xlsx"][genState];
    }

    async function renderWorkPane() {
        const pane = el("studio-pane-work");
        if (!pane) return;

        let exportsHtml = "";
        try {
            const response = await Api.raw(`/api/projects/${projectId}/exports`);
            if (response.ok) {
                const exports = await response.json();
                if (exports.length > 0) {
                    exportsHtml = exports
                        .map(
                            (exp) => `
                            <a class="app-row-btn app-num" style="display:flex;gap:8px;font-size:10.5px;padding:5px 2px;text-decoration:none;color:inherit" href="/api/projects/${projectId}/exports/${exp.id}/download">
                                <span class="app-accent-text">↓</span>
                                <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(exp.filename)}</span>
                                <span class="app-faint">${escapeHtml((exp.created_at || "").slice(0, 16))}</span>
                            </a>`
                        )
                        .join("");
                    exportsHtml = `<hr class="hr"><h6 style="margin:0 0 6px">Previous exports</h6>${exportsHtml}`;
                }
            }
        } catch (err) {
            Log.error("studio", "Failed to load exports", err);
        }

        const chips = SHEETS.map((sheet) => `<span class="app-tab" style="cursor:default">${sheet}</span>`).join("");
        pane.innerHTML = `
            <div class="card" style="margin-bottom:12px">
                <span class="card-kicker">Comparison workbook</span>
                <span class="card-title app-num" style="font-size:14px">Vendor comparison — every cell traced to source</span>
                <span class="app-faint app-num" style="font-size:10.5px">${SHEETS.length} sheets + Traceability appendix</span>
                <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:2px">${chips}</div>
            </div>
            <div style="display:flex;align-items:center;gap:10px;margin-top:12px">
                <p class="app-faint" style="font-size:10.5px;margin:0;flex:1">A Traceability sheet is appended — every cell carries its document, page or cell, and snippet id.</p>
                <button id="wb-generate" class="btn btn-primary" style="font-size:12px;white-space:nowrap">${genLabel()}</button>
            </div>
            <p id="wb-status" class="app-faint" style="font-size:10.5px;margin:8px 0 0"></p>
            ${exportsHtml}`;

        pane.querySelector("#wb-generate").addEventListener("click", onGenerate);
    }

    async function onGenerate() {
        const button = el("studio-pane-work").querySelector("#wb-generate");
        const status = el("studio-pane-work").querySelector("#wb-status");
        if (genState === 1) return;
        if (genState === 2 && downloadUrl) {
            window.location.href = downloadUrl;
            return;
        }

        genState = 1;
        button.textContent = genLabel();
        button.disabled = true;
        try {
            const response = await Api.raw(`/api/projects/${projectId}/exports/excel`, { method: "POST" });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "Export failed");
            downloadUrl = data.download_url;
            genState = 2;
            if (status) status.textContent = `${data.filename || "Workbook"} ready.`;
        } catch (err) {
            genState = 0;
            if (status) status.textContent = err.message;
            Log.error("studio", "Excel export failed", err);
        } finally {
            button.disabled = false;
            button.textContent = genLabel();
        }
    }

    // ---- graph health + maintenance ------------------------------------------

    function renderGraphHealthBadge() {
        const badge = el("studio-graph-health");
        if (!badge) return;
        if (!graphHealth || graphHealth.healthy) {
            badge.classList.add("hidden");
            badge.textContent = "";
            return;
        }
        const errors = (graphHealth.issues || []).filter((issue) => issue.severity === "error").length;
        const warnings = (graphHealth.issues || []).filter((issue) => issue.severity === "warning").length;
        badge.classList.remove("hidden");
        badge.textContent = errors > 0 ? `${errors} issue${errors === 1 ? "" : "s"}` : `${warnings} warn`;
        badge.title = (graphHealth.issues || []).map((issue) => issue.message).join("\n");
    }

    async function fetchGraphHealth() {
        try {
            const response = await Api.raw(`/api/projects/${projectId}/graph/health`);
            if (response.ok) {
                graphHealth = await response.json();
                renderGraphHealthBadge();
            }
        } catch (err) {
            Log.error("studio", "Failed to load graph health", err);
        }
    }

    async function maintainGraph() {
        const button = el("studio-maintain-btn");
        if (!button || maintainBusy) return;
        maintainBusy = true;
        button.disabled = true;
        button.textContent = "Maintaining…";
        try {
            const response = await Api.raw(`/api/projects/${projectId}/graph/maintain`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ mode: "fast", reason: "Manual maintain graph from Studio" }),
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || "Maintenance failed");
            graphHealth = data.health || graphHealth;
            renderGraphHealthBadge();
            await refresh();
        } catch (err) {
            Log.error("studio", "Graph maintenance failed", err);
            alert(err.message);
        } finally {
            maintainBusy = false;
            button.disabled = false;
            button.textContent = "Maintain graph";
        }
    }

    // ---- tabs + data loading -------------------------------------------------

    function switchTab(tab) {
        ["graph", "rank", "tco", "work"].forEach((name) => {
            el(`studio-pane-${name}`).classList.toggle("hidden", name !== tab);
        });
        if (tab === "graph") renderGraphPane();
        if (tab === "rank") renderRankPane();
        if (tab === "tco") renderTcoPane();
        if (tab === "work") renderWorkPane();
    }

    function bindTabs() {
        document.querySelectorAll('input[name="studio-tab"]').forEach((input) => {
            input.addEventListener("change", () => switchTab(input.value));
        });
        const exportBtn = el("ws-export-btn");
        if (exportBtn) {
            exportBtn.addEventListener("click", () => {
                const workRadio = document.querySelector('input[name="studio-tab"][value="work"]');
                if (workRadio) workRadio.checked = true;
                switchTab("work");
            });
        }
    }

    async function refresh() {
        try {
            const [graphRes, compRes] = await Promise.all([
                Api.raw(`/api/projects/${projectId}/graph`),
                Api.raw(`/api/projects/${projectId}/comparison`),
            ]);
            if (graphRes.ok) graph = await graphRes.json();
            if (compRes.ok) comparison = await compRes.json();
        } catch (err) {
            Log.error("studio", "Failed to load studio data", err);
        }
        renderKpis();
        renderGraphPane();
        renderRankPane();
        renderTcoPane();
        fetchGraphHealth();
    }

    function init(id) {
        projectId = id;
        bindTabs();
        const maintainBtn = el("studio-maintain-btn");
        if (maintainBtn) maintainBtn.addEventListener("click", maintainGraph);
        refresh();
        document.addEventListener("sources:updated", refresh);
    }

    return { init };
})();
