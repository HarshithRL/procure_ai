// Obsidian-style knowledge-graph explorer: a full-screen popup with a
// force-directed canvas (vendored force-graph lib), zoom/pan, node drag,
// hover neighbor-highlighting with dimming, zoom-dependent labels, type
// filters, force sliders, search, and a local "focus" mode (N-hop
// neighborhood). Opened from the Studio panel's Graph tab.
//
// v1.2 additions (Phase 1 Steps 13-14):
//   - View toggle: "Detail" (all nodes) vs "Overview" (Tier-1 only)
//   - Re-fetches from /api/projects/<id>/graph?view=<mode> on toggle
//   - Orphan dimming: nodes with no edges are drawn at 18% alpha + red ring
//   - Bridge edges: when Tier-2 types are hidden, synthetic dashed edges
//     connect visible neighbors through the hidden node
//   - Stats panel includes orphan count

"use strict";

// ---- Module-level constants (shared across open/close cycles) ---------------

/** Tier-1 node types: always visible in overview mode. */
const GX_NODE_TIER = {
    project: 1, vendor: 1, requirement: 1, evaluation: 1,
    comparison: 1, recommendation: 1, decision: 1, contract: 1,
    // All other types default to tier 2
};

const GraphExplorer = (() => {
    const TYPE_ORDER = [
        "project", "business_context", "stakeholder", "evaluation_committee",
        "requirement", "source_document", "vendor", "company_profile", "technical_offer",
        "article", "price_quote", "commercial_term", "certification", "support_service",
        "delivery_term", "warranty", "finding", "risk", "opportunity", "negotiation_point",
        "missing_information", "evaluation", "recommendation", "deliverable", "decision", "award"
    ];
    
    const TYPE_LABELS = {
        project: "Project",
        business_context: "Business Context",
        stakeholder: "Stakeholder",
        evaluation_committee: "Committee",
        requirement: "Requirement",
        source_document: "Document",
        vendor: "Vendor",
        company_profile: "Company Profile",
        technical_offer: "Technical Offer",
        article: "Article",
        price_quote: "Price Quote",
        commercial_term: "Commercial Term",
        certification: "Certification",
        support_service: "Support Service",
        delivery_term: "Delivery Term",
        warranty: "Warranty",
        finding: "Finding",
        risk: "Risk",
        opportunity: "Opportunity",
        negotiation_point: "Negotiation Point",
        missing_information: "Missing Info",
        evaluation: "Evaluation",
        recommendation: "Recommendation",
        deliverable: "Deliverable",
        decision: "Decision",
        award: "Award",
    };
    
    // Layer assignment for column-constrained layout (x-position force)
    const LAYER_X = {
        project: 50,
        business_context: 150,
        stakeholder: 150,
        evaluation_committee: 150,
        requirement: 270,
        source_document: 390,
        deliverable: 390,
        vendor: 520,
        company_profile: 520,
        technical_offer: 650,
        article: 650,
        price_quote: 650,
        commercial_term: 650,
        certification: 650,
        support_service: 650,
        delivery_term: 650,
        warranty: 650,
        finding: 780,
        risk: 780,
        opportunity: 780,
        negotiation_point: 780,
        missing_information: 780,
        evaluation: 900,
        recommendation: 1020,
        decision: 1020,
        award: 1020,
    };
    
    // Fixed hues tuned per Etex theme
    const PALETTES = {
        light: {
            project: "#F06D0C",
            business_context: "#e8a020",
            stakeholder: "#d4c040",
            evaluation_committee: "#b5c730",
            requirement: "#b83a3a",
            source_document: "#8a8781",
            deliverable: "#a0789a",
            vendor: "#F06D0C",
            company_profile: "#ff9a4d",
            technical_offer: "#3a7bb5",
            article: "#4060b0",
            price_quote: "#3a8f8f",
            commercial_term: "#5a7a8f",
            certification: "#2ea86a",
            support_service: "#4a8f5e",
            delivery_term: "#3a8f5e",
            warranty: "#309f70",
            finding: "#9b59b6",
            risk: "#e74c3c",
            opportunity: "#27ae60",
            negotiation_point: "#f39c12",
            missing_information: "#c0392b",
            evaluation: "#1abc9c",
            recommendation: "#2ecc71",
            decision: "#f1c40f",
            award: "#e67e22",
        },
        dark: {
            project: "#ff8a3d",
            business_context: "#ffb347",
            stakeholder: "#ffe45e",
            evaluation_committee: "#d4ff33",
            requirement: "#e06a6a",
            source_document: "#99979e",
            deliverable: "#c9a0c9",
            vendor: "#ff8a3d",
            company_profile: "#ffb87d",
            technical_offer: "#6aa8e0",
            article: "#7080d0",
            price_quote: "#5ababa",
            commercial_term: "#8aaaaf",
            certification: "#50d09a",
            support_service: "#6aba80",
            delivery_term: "#5aba80",
            warranty: "#50cfaa",
            finding: "#b878d4",
            risk: "#ff6b6b",
            opportunity: "#51cf66",
            negotiation_point: "#ffa94d",
            missing_information: "#ff5555",
            evaluation: "#37d9d9",
            recommendation: "#69db7c",
            decision: "#ffd43b",
            award: "#ff922b",
        },
    };

    const DEFAULT_SETTINGS = {
        sizeScale: 3,
        linkWidth: 1,
        labelZoom: 1.2,
        centerForce: 0.4,
        repelForce: 180,
        linkForce: 0.4,
        linkDistance: 45,
        showTypes: {
            project: true,
            business_context: true,
            stakeholder: true,
            evaluation_committee: true,
            requirement: true,
            source_document: true,
            vendor: true,
            company_profile: true,
            technical_offer: true,
            article: true,
            price_quote: true,
            commercial_term: true,
            certification: true,
            support_service: true,
            delivery_term: true,
            warranty: true,
            finding: true,
            risk: true,
            opportunity: true,
            negotiation_point: true,
            missing_information: true,
            evaluation: true,
            recommendation: true,
            deliverable: true,
            decision: true,
            award: true,
        },
        showOrphans: true,
    };

    const TYPE_GLYPHS = {
        project: "⬡", business_context: "≡", stakeholder: "◯",
        evaluation_committee: "◎", requirement: "◈", source_document: "▤",
        vendor: "★", company_profile: "◉", technical_offer: "⊙",
        article: "▣", price_quote: "€", commercial_term: "⊞",
        certification: "✓", support_service: "⊕", delivery_term: "→",
        warranty: "⊛", finding: "✦", risk: "⚠", opportunity: "↗",
        negotiation_point: "⚖", missing_information: "?",
        evaluation: "⊙", recommendation: "✓", deliverable: "⬡",
        decision: "◉", award: "★",
    };

    let fg = null;            // ForceGraph instance
    let overlay = null;
    let settings = null;
    let storageKey = "graphExplorer";
    let allNodes = [];        // cloned nodes with degree
    let allLinks = [];        // {source, target, relation, evidence}
    let neighborIds = new Map();  // id -> Set(id)
    let nodeById = new Map();
    let hoverNode = null;
    let selectedNode = null;
    let focusNodeId = null;
    let focusDepth = 1;
    let searchTerm = "";
    let colors = null;
    let lastClick = { id: null, t: 0 };
    let minimapBounds = null; // { minX, maxX, minY, maxY, scaleX, scaleY }

    // ---- View toggle state --------------------------------------------------
    let graphView = "detail";   // "detail" | "overview"
    let currentProjectId = null; // stored from open() options for re-fetching

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str == null ? "" : String(str);
        return div.innerHTML;
    }

    function isDark() {
        return document.body.classList.contains("ds-nocturne");
    }

    function readTheme() {
        const style = getComputedStyle(document.body);
        colors = {
            bg: style.getPropertyValue("--color-bg").trim() || (isDark() ? "#212121" : "#ffffff"),
            text: style.getPropertyValue("--color-text").trim() || (isDark() ? "#ffffff" : "#1c1e21"),
            accent: style.getPropertyValue("--color-accent").trim() || "#f06d0c",
            palette: PALETTES[isDark() ? "dark" : "light"],
        };
    }

    function loadSettings() {
        try {
            const raw = localStorage.getItem(storageKey);
            if (raw) {
                const saved = JSON.parse(raw);
                return {
                    ...DEFAULT_SETTINGS,
                    ...saved,
                    showTypes: { ...DEFAULT_SETTINGS.showTypes, ...(saved.showTypes || {}) },
                };
            }
        } catch (err) { /* corrupted settings — fall through to defaults */ }
        return JSON.parse(JSON.stringify(DEFAULT_SETTINGS));
    }

    function saveSettings() {
        try {
            localStorage.setItem(storageKey, JSON.stringify(settings));
        } catch (err) { /* storage full/blocked — settings just won't persist */ }
    }

    // ---- data prep -----------------------------------------------------------

    function prepare(graphData) {
        nodeById = new Map();
        neighborIds = new Map();
        allNodes = (graphData.nodes || []).map((n) => ({
            id: n.id,
            type: n.type,
            name: n.name,
            evidence: n.evidence || [],
            orphan: !!n.orphan,   // preserve backend-computed orphan flag
            degree: 0,
        }));
        allNodes.forEach((n) => {
            nodeById.set(n.id, n);
            neighborIds.set(n.id, new Set());
        });
        allLinks = (graphData.edges || [])
            .filter((e) => nodeById.has(e.source_id) && nodeById.has(e.target_id))
            .map((e) => ({
                source: e.source_id,
                target: e.target_id,
                relation: e.relation,
                evidence: e.evidence || [],
                bridge: false,    // synthetic bridge edges are marked true
            }));
        allLinks.forEach((l) => {
            nodeById.get(l.source).degree += 1;
            nodeById.get(l.target).degree += 1;
            neighborIds.get(l.source).add(l.target);
            neighborIds.get(l.target).add(l.source);
        });
        computeCurvatures();
    }

    function computeCurvatures() {
        const pairs = new Map();
        allLinks.forEach(l => {
            const key = [l.source, l.target].sort().join("|");
            if (!pairs.has(key)) pairs.set(key, []);
            pairs.get(key).push(l);
        });
        pairs.forEach(group => {
            const n = group.length;
            if (n === 1) { group[0]._curvature = 0; return; }
            const spread = 0.25;
            group.forEach((l, i) => {
                l._curvature = (i - (n - 1) / 2) * (spread * 2 / Math.max(n - 1, 1));
            });
        });
    }

    function typeVisible(type) {
        return settings.showTypes[type] !== false;
    }

    function visibleData() {
        let keep = new Set(allNodes.filter((n) => typeVisible(n.type)).map((n) => n.id));

        // Focus mode: BFS N hops from the focus node over type-visible nodes.
        if (focusNodeId && keep.has(focusNodeId)) {
            const reach = new Set([focusNodeId]);
            let frontier = [focusNodeId];
            for (let hop = 0; hop < focusDepth; hop++) {
                const next = [];
                frontier.forEach((id) => {
                    neighborIds.get(id).forEach((nb) => {
                        if (keep.has(nb) && !reach.has(nb)) {
                            reach.add(nb);
                            next.push(nb);
                        }
                    });
                });
                frontier = next;
            }
            keep = reach;
        }

        // Search: matches + their direct neighbors survive.
        if (searchTerm) {
            const q = searchTerm.toLowerCase();
            const matched = new Set();
            keep.forEach((id) => {
                if (nodeById.get(id).name.toLowerCase().includes(q)) matched.add(id);
            });
            const withNeighbors = new Set(matched);
            matched.forEach((id) => neighborIds.get(id).forEach((nb) => {
                if (keep.has(nb)) withNeighbors.add(nb);
            }));
            keep = withNeighbors;
        }

        let links = allLinks.filter((l) => {
            const s = typeof l.source === "object" ? l.source.id : l.source;
            const t = typeof l.target === "object" ? l.target.id : l.target;
            return keep.has(s) && keep.has(t);
        });

        // Bridge edges: when a Tier-2 node type is hidden, synthesise a dashed
        // edge connecting its visible neighbours so the graph stays connected.
        const bridgeLinks = computeBridgeEdges(keep);
        links = links.concat(bridgeLinks);

        let nodes = allNodes.filter((n) => keep.has(n.id));
        if (!settings.showOrphans && !searchTerm && !focusNodeId) {
            const linked = new Set();
            links.forEach((l) => {
                linked.add(typeof l.source === "object" ? l.source.id : l.source);
                linked.add(typeof l.target === "object" ? l.target.id : l.target);
            });
            nodes = nodes.filter((n) => linked.has(n.id));
        }
        return { nodes, links };
    }

    /**
     * Compute synthetic "bridge" edges for hidden intermediate nodes.
     *
     * When a node type is toggled off, any real edge that crosses through a
     * hidden node would disappear, disconnecting visible neighbours.  For each
     * hidden node we find all pairs of visible neighbours and emit one dashed
     * bridge edge per pair (de-duplicated).  Bridge edges carry the relation
     * label "via <hidden-type>" so the user understands the indirection.
     *
     * @param {Set<string>} keep - set of currently visible node IDs
     * @returns {Array} synthetic link objects with bridge:true
     */
    function computeBridgeEdges(keep) {
        const bridges = [];
        const seen = new Set(); // "srcId|tgtId" to avoid duplicates

        allNodes.forEach((hiddenNode) => {
            if (keep.has(hiddenNode.id)) return; // node is visible — skip

            // Collect visible neighbours of this hidden node
            const visibleNeighbours = [];
            allLinks.forEach((l) => {
                const s = typeof l.source === "object" ? l.source.id : l.source;
                const t = typeof l.target === "object" ? l.target.id : l.target;
                if (s === hiddenNode.id && keep.has(t)) visibleNeighbours.push(t);
                if (t === hiddenNode.id && keep.has(s)) visibleNeighbours.push(s);
            });

            if (visibleNeighbours.length < 2) return; // nothing to bridge

            // Emit one bridge edge per unique pair of visible neighbours
            for (let i = 0; i < visibleNeighbours.length; i++) {
                for (let j = i + 1; j < visibleNeighbours.length; j++) {
                    const a = visibleNeighbours[i];
                    const b = visibleNeighbours[j];
                    const key = [a, b].sort().join("|");
                    if (seen.has(key)) continue;
                    seen.add(key);
                    bridges.push({
                        source: a,
                        target: b,
                        relation: `via ${hiddenNode.type}`,
                        evidence: [],
                        bridge: true,
                        _curvature: 0,
                    });
                }
            }
        });

        return bridges;
    }

    function refreshData() {
        if (!fg) return;
        fg.graphData(visibleData());
        updateCounts();
        refreshVisualization();
    }

    // ---- rendering -----------------------------------------------------------

    function nodeRadius(node) {
        return 2.5 + Math.sqrt(node.degree || 1) * (settings.sizeScale * 0.6);
    }

    function highlightSet() {
        const anchor = hoverNode || selectedNode;
        if (!anchor) return null;
        const set = new Set([anchor.id]);
        (neighborIds.get(anchor.id) || []).forEach((id) => set.add(id));
        return set;
    }

    function paintNode(node, ctx, k) {
        const r = nodeRadius(node);
        const hl = highlightSet();
        const dim = hl && !hl.has(node.id);

        // Orphan nodes are dimmed to 18% alpha in detail view (not in overview,
        // where the backend already filters them out).
        const isOrphan = node.orphan && graphView === "detail";
        const baseAlpha = isOrphan ? 0.18 : 1;

        ctx.globalAlpha = dim ? Math.min(0.1, baseAlpha) : baseAlpha;
        ctx.beginPath();
        ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
        ctx.fillStyle = colors.palette[node.type] || colors.text;
        ctx.fill();

        // Accent ring for selected / hovered / focused nodes
        if (!dim && (node === selectedNode || node === hoverNode || node.id === focusNodeId)) {
            ctx.lineWidth = 1.5 / k;
            ctx.strokeStyle = colors.accent;
            ctx.globalAlpha = baseAlpha;
            ctx.beginPath();
            ctx.arc(node.x, node.y, r + 2.5 / k, 0, 2 * Math.PI);
            ctx.stroke();
        }

        // Red ring for orphan nodes (drawn on top of fill, before glyph)
        if (isOrphan && r >= 3 && !dim) {
            ctx.lineWidth = Math.max(1, 1.5 / k);
            ctx.strokeStyle = "#e74c3c";
            ctx.globalAlpha = 0.7;
            ctx.beginPath();
            ctx.arc(node.x, node.y, r + 1 / k, 0, 2 * Math.PI);
            ctx.stroke();
        }

        // Draw type glyph inside circle
        const glyph = TYPE_GLYPHS[node.type] || "·";
        if (r >= 5 && !dim) {
            const glyphSize = Math.min(r * 1.1, 14) / k;
            ctx.font = `${glyphSize}px system-ui, sans-serif`;
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.globalAlpha = isOrphan ? 0.18 * 0.88 : 0.88;
            ctx.fillStyle = "rgba(255,255,255,0.88)";
            ctx.fillText(glyph, node.x, node.y);
            ctx.globalAlpha = 1;
        }

        // Obsidian-style labels: fade in with zoom; anchored nodes always labeled.
        let alpha = Math.max(0, Math.min(1, (k - settings.labelZoom) / Math.max(0.4, settings.labelZoom)));
        if (hl && hl.has(node.id)) alpha = 1;
        if (dim) alpha = 0;
        if (isOrphan) alpha *= 0.4; // labels even more faint for orphans
        if (alpha > 0.03) {
            const fontSize = 12 / k;
            ctx.font = `500 ${fontSize}px Inter, system-ui, sans-serif`;
            ctx.textAlign = "center";
            ctx.textBaseline = "top";
            ctx.globalAlpha = alpha;
            ctx.fillStyle = colors.text;
            ctx.fillText(node.name, node.x, node.y + r + 3 / k);
        }
        ctx.globalAlpha = 1;
    }

    function linkColor(link) {
        // Bridge edges are always semi-transparent grey regardless of highlight
        if (link.bridge) return "rgba(128,128,128,0.25)";

        const hl = highlightSet();
        if (hl) {
            const s = typeof link.source === "object" ? link.source.id : link.source;
            const t = typeof link.target === "object" ? link.target.id : link.target;
            const anchor = (hoverNode || selectedNode).id;
            if (s === anchor || t === anchor) return colors.accent;
            return hexAlpha(colors.text, 0.04);
        }
        return hexAlpha(colors.text, 0.16);
    }

    function hexAlpha(hex, alpha) {
        // colors from tokens are #rrggbb; fall back gracefully otherwise
        if (/^#[0-9a-f]{6}$/i.test(hex)) {
            const a = Math.round(alpha * 255).toString(16).padStart(2, "0");
            return hex + a;
        }
        return hex;
    }

    function applyForces() {
        if (!fg) return;
        const charge = fg.d3Force("charge");
        if (charge) charge.strength(-settings.repelForce);
        const link = fg.d3Force("link");
        if (link) {
            link.distance(settings.linkDistance);
            link.strength(settings.linkForce);
        }
        const center = fg.d3Force("center");
        if (center && center.strength) center.strength(settings.centerForce);
        
        // Add x-position layer force: custom force that pulls nodes toward their type's column
        fg.d3Force("x", (alpha) => {
            allNodes.forEach((node) => {
                const targetX = LAYER_X[node.type] ?? 500;
                const dx = targetX - (node.x || 0);
                node.vx = (node.vx || 0) + dx * alpha * 0.25 * 0.01; // strength=0.25
            });
        });
        
        fg.d3ReheatSimulation();
    }

    // ---- selection card + focus mode ----------------------------------------

    function renderSelectionCard() {
        const card = overlay.querySelector("#gx-selection");
        if (!card) return;
        if (!selectedNode) {
            card.classList.add("hidden");
            return;
        }
        const node = selectedNode;
        const evidence = node.evidence.concat(
            allLinks
                .filter((l) => {
                    const s = typeof l.source === "object" ? l.source.id : l.source;
                    const t = typeof l.target === "object" ? l.target.id : l.target;
                    return s === node.id || t === node.id;
                })
                .flatMap((l) => l.evidence)
        ).slice(0, 4);

        const evRows = evidence.length
            ? evidence
                .map(
                    (ev, i) => `
                    <button class="app-row-btn app-num gx-ev" data-i="${i}" style="display:flex;gap:7px;font-size:10.5px;padding:4px 2px">
                        <span class="app-accent-text">${i + 1}</span>
                        <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(ev.document_id)}</span>
                        <span class="app-faint">${escapeHtml(ev.locator || "")}</span>
                    </button>`
                )
                .join("")
            : '<span class="app-faint" style="font-size:10.5px">No evidence recorded.</span>';

        const inFocus = focusNodeId === node.id;
        
        // Build relationships section
        const relatedLinks = allLinks.filter((l) => {
            const s = typeof l.source === "object" ? l.source.id : l.source;
            const t = typeof l.target === "object" ? l.target.id : l.target;
            return s === node.id || t === node.id;
        });
        
        const relRows = relatedLinks.slice(0, 6).map((link) => {
            const s = typeof link.source === "object" ? link.source.id : link.source;
            const t = typeof link.target === "object" ? link.target.id : link.target;
            const relNode = nodeById.get(s === node.id ? t : s);
            const direction = s === node.id ? "→" : "←";
            return `<div style="font-size:10px;display:flex;gap:4px;align-items:center;padding:3px 0;overflow:hidden">
                <span class="app-faint">${direction}</span>
                <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${escapeHtml(relNode.name)}">${escapeHtml(relNode.name.substring(0, 30))}</span>
                <span class="app-faint" style="font-size:9px">${escapeHtml(link.relation || "?")}</span>
            </div>`;
        }).join("");
        
        card.innerHTML = `
            <span class="card-kicker">${escapeHtml(TYPE_LABELS[node.type] || node.type)}</span>
            <span class="card-title" style="font-size:15px">${escapeHtml(node.name)}</span>
            <div class="app-num" style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:11px">
                <span><span class="app-faint" style="display:block;font-size:9.5px">Connections</span>${node.degree}</span>
                <span><span class="app-faint" style="display:block;font-size:9.5px">Evidence refs</span>${evidence.length}</span>
            </div>
            ${relRows ? `<span class="app-faint" style="font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;margin-top:6px;display:block">Relationships</span><div style="display:grid;gap:2px">${relRows}</div>` : ""}
            <span class="app-faint" style="font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;margin-top:6px;display:block">Grounded in</span>
            ${evRows}
            <div style="display:flex;gap:6px;align-items:center;margin-top:8px">
                <button id="gx-focus-btn" class="btn ${inFocus ? "btn-primary" : "btn-secondary"}" style="font-size:11px">${inFocus ? "Exit focus" : "Focus"}</button>
                <label class="app-faint" style="font-size:10px;display:flex;align-items:center;gap:5px;flex:1">
                    depth
                    <input id="gx-focus-depth" type="range" min="1" max="3" step="1" value="${focusDepth}" style="flex:1">
                    <span class="app-num">${focusDepth}</span>
                </label>
            </div>`;
        card.classList.remove("hidden");

        card.querySelectorAll(".gx-ev").forEach((btn) => {
            btn.addEventListener("click", () => {
                const ev = evidence[Number(btn.dataset.i)];
                if (ev && typeof EvidencePanel !== "undefined") EvidencePanel.show(ev, Number(btn.dataset.i) + 1);
            });
        });
        card.querySelector("#gx-focus-btn").addEventListener("click", () => {
            focusNodeId = inFocus ? null : node.id;
            refreshData();
            renderSelectionCard();
            setTimeout(() => fg && fg.zoomToFit(400, 60), 350);
        });
        card.querySelector("#gx-focus-depth").addEventListener("input", (event) => {
            focusDepth = Number(event.target.value);
            renderSelectionCard();
            if (focusNodeId) refreshData();
        });
    }

    function setSelected(node) {
        selectedNode = node;
        renderSelectionCard();
    }

    function renderSearchDropdown() {
        const resultsEl = overlay && overlay.querySelector("#gx-search-results");
        if (!resultsEl) return;
        if (!searchTerm) { resultsEl.classList.add("hidden"); return; }

        const q = searchTerm.toLowerCase();
        const matches = allNodes
            .filter(n => n.name.toLowerCase().includes(q))
            .sort((a, b) => b.degree - a.degree)
            .slice(0, 8);

        if (matches.length === 0) { resultsEl.classList.add("hidden"); return; }

        resultsEl.innerHTML = matches.map(n => `
            <button class="gx-search-result app-row-btn" data-id="${escapeHtml(String(n.id))}">
                <i class="app-dot" style="background:${colors.palette[n.type] || "#888"};flex:none"></i>
                <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px">${escapeHtml(n.name)}</span>
                <span class="app-faint" style="font-size:10px;flex:none">${escapeHtml(TYPE_LABELS[n.type] || n.type)}</span>
            </button>`).join("");
        resultsEl.classList.remove("hidden");

        resultsEl.querySelectorAll(".gx-search-result").forEach(btn => {
            btn.addEventListener("click", () => {
                const node = nodeById.get(btn.dataset.id)
                          || allNodes.find(n => String(n.id) === btn.dataset.id);
                if (!node) return;
                searchTerm = "";
                overlay.querySelector("#gx-search").value = "";
                resultsEl.classList.add("hidden");
                refreshData();
                setSelected(node);
                if (node.x != null) {
                    fg.centerAt(node.x, node.y, 600);
                    fg.zoom(3, 600);
                }
            });
        });
    }

    // ---- controls drawer -----------------------------------------------------

    function slider(id, label, min, max, step, value) {
        return `
            <label style="display:flex;flex-direction:column;gap:3px;font-size:10.5px" class="app-muted">
                <span style="display:flex;justify-content:space-between"><span>${label}</span><span class="app-num" id="${id}-val">${value}</span></span>
                <input id="${id}" type="range" min="${min}" max="${max}" step="${step}" value="${value}">
            </label>`;
    }

    function drawerHtml() {
        const typeRows = TYPE_ORDER.map((type) => {
            const count = allNodes.filter((n) => n.type === type).length;
            if (count === 0 && type !== "source_document") return "";
            return `
                <label style="display:flex;align-items:center;gap:8px;padding:3px 0;cursor:pointer;font-size:11.5px">
                    <input type="checkbox" class="app-check gx-type" data-type="${type}" ${typeVisible(type) ? "checked" : ""}>
                    <i class="app-dot" style="background:${(colors.palette[type]) || "#888"}"></i>
                    <span style="flex:1">${TYPE_LABELS[type]}</span>
                    <span class="app-faint app-num" style="font-size:10px">${count}</span>
                </label>`;
        }).join("");

        return `
            <h6 style="margin:0 0 6px">Filters</h6>
            <div style="display:flex;gap:6px;margin-bottom:8px">
                <button id="gx-show-all" class="btn btn-secondary" style="font-size:10px;flex:1;padding:4px">Show all</button>
                <button id="gx-hide-all" class="btn btn-secondary" style="font-size:10px;flex:1;padding:4px">Hide all</button>
            </div>
            ${typeRows}
            <label style="display:flex;align-items:center;gap:8px;padding:3px 0;cursor:pointer;font-size:11.5px">
                <input type="checkbox" class="app-check" id="gx-orphans" ${settings.showOrphans ? "checked" : ""}>
                <span style="flex:1">Show orphan nodes</span>
            </label>
            <hr class="hr" style="margin:10px 0">
            <h6 style="margin:0 0 6px">Display</h6>
            <div style="display:grid;gap:8px">
                ${slider("gx-size", "Node size", 1, 8, 0.5, settings.sizeScale)}
                ${slider("gx-linkwidth", "Link width", 0.4, 3, 0.2, settings.linkWidth)}
                ${slider("gx-labelzoom", "Label threshold", 0.4, 3, 0.1, settings.labelZoom)}
            </div>
            <hr class="hr" style="margin:10px 0">
            <h6 style="margin:0 0 6px">Forces</h6>
            <div style="display:grid;gap:8px">
                ${slider("gx-center", "Center force", 0, 1, 0.05, settings.centerForce)}
                ${slider("gx-repel", "Repel force", 20, 600, 10, settings.repelForce)}
                ${slider("gx-linkforce", "Link force", 0.05, 1, 0.05, settings.linkForce)}
                ${slider("gx-linkdist", "Link distance", 10, 140, 5, settings.linkDistance)}
            </div>
            <hr class="hr" style="margin:10px 0">
            <button id="gx-reset" class="btn btn-ghost" style="font-size:11px;width:100%">Reset to defaults</button>`;
    }

    function bindDrawer() {
        overlay.querySelectorAll(".gx-type").forEach((checkbox) => {
            checkbox.addEventListener("change", () => {
                settings.showTypes[checkbox.dataset.type] = checkbox.checked;
                saveSettings();
                refreshData();
            });
        });
        overlay.querySelector("#gx-orphans").addEventListener("change", (event) => {
            settings.showOrphans = event.target.checked;
            saveSettings();
            refreshData();
        });
        
        // Show/hide all buttons
        const showAllBtn = overlay.querySelector("#gx-show-all");
        const hideAllBtn = overlay.querySelector("#gx-hide-all");
        if (showAllBtn) {
            showAllBtn.addEventListener("click", () => {
                TYPE_ORDER.forEach(type => settings.showTypes[type] = true);
                saveSettings();
                const drawer = overlay.querySelector("#gx-drawer");
                drawer.innerHTML = drawerHtml();
                bindDrawer();
                refreshData();
            });
        }
        if (hideAllBtn) {
            hideAllBtn.addEventListener("click", () => {
                TYPE_ORDER.forEach(type => settings.showTypes[type] = false);
                saveSettings();
                const drawer = overlay.querySelector("#gx-drawer");
                drawer.innerHTML = drawerHtml();
                bindDrawer();
                refreshData();
            });
        }

        const bindSlider = (id, apply) => {
            const input = overlay.querySelector(`#${id}`);
            const val = overlay.querySelector(`#${id}-val`);
            input.addEventListener("input", () => {
                const value = Number(input.value);
                if (val) val.textContent = String(value);
                apply(value);
                saveSettings();
            });
        };
        bindSlider("gx-size", (v) => { settings.sizeScale = v; fg && fg.nodeRelSize(v); refreshCanvas(); });
        bindSlider("gx-linkwidth", (v) => { settings.linkWidth = v; fg && fg.linkWidth(() => settings.linkWidth); fg && fg.linkDirectionalArrowLength(v * 1.4); });
        bindSlider("gx-labelzoom", (v) => { settings.labelZoom = v; refreshCanvas(); });
        bindSlider("gx-center", (v) => { settings.centerForce = v; applyForces(); });
        bindSlider("gx-repel", (v) => { settings.repelForce = v; applyForces(); });
        bindSlider("gx-linkforce", (v) => { settings.linkForce = v; applyForces(); });
        bindSlider("gx-linkdist", (v) => { settings.linkDistance = v; applyForces(); });

        overlay.querySelector("#gx-reset").addEventListener("click", () => {
            settings = JSON.parse(JSON.stringify(DEFAULT_SETTINGS));
            saveSettings();
            const drawer = overlay.querySelector("#gx-drawer");
            drawer.innerHTML = drawerHtml();
            bindDrawer();
            applyForces();
            refreshData();
        });
    }

    function refreshCanvas() {
        // force-graph repaints continuously while the simulation is warm; a
        // zero-distance pan nudges a repaint when it's cold.
        if (fg) fg.centerAt(undefined, undefined, 0);
    }

    function updateCounts() {
        const countEl = overlay && overlay.querySelector("#gx-counts");
        if (!countEl || !fg) return;
        const data = fg.graphData();
        countEl.textContent = `${data.nodes.length} of ${allNodes.length} nodes · ${data.links.length} links`;
    }

    function updateZoomLabel(k) {
        const zoomEl = overlay && overlay.querySelector("#gx-zoom-label");
        if (zoomEl) zoomEl.textContent = `${Math.round(k * 100)}%`;
    }

    function updateStats() {
        const statsEl = overlay && overlay.querySelector("#gx-stats");
        if (!statsEl || !fg) return;
        const data = fg.graphData();
        
        // Count by type for visible data
        const typeCounts = {};
        TYPE_ORDER.forEach(type => typeCounts[type] = 0);
        data.nodes.forEach(n => {
            if (typeCounts.hasOwnProperty(n.type)) typeCounts[n.type]++;
        });
        
        // Build summary stats
        const vendorCount = typeCounts.vendor || 0;
        const docCount = typeCounts.source_document || 0;
        const findCount = (typeCounts.finding || 0) + (typeCounts.risk || 0) + (typeCounts.opportunity || 0);
        const missCount = typeCounts.missing_information || 0;
        const orphanCount = data.nodes.filter(n => n.orphan).length;
        const bridgeCount = data.links.filter(l => l.bridge).length;
        
        const orphanBadge = orphanCount > 0
            ? `<span title="Nodes with no edges"><strong style="color:#e74c3c">${orphanCount}</strong> orphans</span>`
            : "";
        const bridgeBadge = bridgeCount > 0
            ? `<span title="Synthetic edges bridging hidden nodes" style="opacity:0.7"><strong>${bridgeCount}</strong> bridges</span>`
            : "";
        
        statsEl.innerHTML = `
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;white-space:nowrap">
                <span><strong>${data.nodes.length}</strong> nodes</span>
                <span><strong>${data.links.length}</strong> edges</span>
                <span><strong>${vendorCount}</strong> vendors</span>
                <span><strong>${docCount}</strong> docs</span>
                <span><strong>${findCount}</strong> insights</span>
                <span><strong>${missCount}</strong> gaps</span>
                ${orphanBadge}
                ${bridgeBadge}
            </div>`;
    }

    function updateMinimap() {
        const minimapEl = overlay && overlay.querySelector("#gx-minimap");
        if (!minimapEl || !fg) return;
        
        const canvas = minimapEl.querySelector("canvas");
        if (canvas) canvas.remove();
        
        const data = fg.graphData();
        if (data.nodes.length === 0) return;
        
        // Create a tiny canvas for the minimap
        const mmCanvas = document.createElement("canvas");
        mmCanvas.width = 120;
        mmCanvas.height = 90;
        const ctx = mmCanvas.getContext("2d");
        
        // Calculate bounds of all nodes
        let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
        data.nodes.forEach(n => {
            minX = Math.min(minX, n.x || 0);
            maxX = Math.max(maxX, n.x || 0);
            minY = Math.min(minY, n.y || 0);
            maxY = Math.max(maxY, n.y || 0);
        });
        
        const padX = (maxX - minX) * 0.1 || 100;
        const padY = (maxY - minY) * 0.1 || 100;
        minX -= padX; maxX += padX;
        minY -= padY; maxY += padY;
        
        const scaleX = mmCanvas.width / (maxX - minX || 1);
        const scaleY = mmCanvas.height / (maxY - minY || 1);
        
        // Store bounds for click handler
        minimapBounds = { minX, maxX, minY, maxY, scaleX, scaleY };
        
        // Draw background
        ctx.fillStyle = "rgba(0,0,0,0.3)";
        ctx.fillRect(0, 0, mmCanvas.width, mmCanvas.height);
        
        // Draw nodes
        data.nodes.forEach(n => {
            const x = ((n.x || 0) - minX) * scaleX;
            const y = ((n.y || 0) - minY) * scaleY;
            const r = Math.max(1, Math.min(3, Math.sqrt(n.degree || 1) * 0.5));
            
            ctx.fillStyle = colors.palette[n.type] || colors.text;
            ctx.globalAlpha = 0.7;
            ctx.beginPath();
            ctx.arc(x, y, r, 0, 2 * Math.PI);
            ctx.fill();
        });
        
        // Draw edges (faint)
        ctx.globalAlpha = 0.2;
        ctx.strokeStyle = colors.text;
        ctx.lineWidth = 0.5;
        data.links.forEach(l => {
            const sx = ((l.source.x || 0) - minX) * scaleX;
            const sy = ((l.source.y || 0) - minY) * scaleY;
            const tx = ((l.target.x || 0) - minX) * scaleX;
            const ty = ((l.target.y || 0) - minY) * scaleY;
            ctx.beginPath();
            ctx.moveTo(sx, sy);
            ctx.lineTo(tx, ty);
            ctx.stroke();
        });
        
        ctx.globalAlpha = 1;
        
        // Draw actual viewport rectangle
        const zoom = fg.zoom();
        const camCenter = fg.centerAt();
        if (camCenter && zoom) {
            const hostEl = overlay.querySelector("#gx-canvas");
            const vHalfW = (hostEl.clientWidth  / 2) / zoom;
            const vHalfH = (hostEl.clientHeight / 2) / zoom;
            const vx = (camCenter.x - vHalfW - minX) * scaleX;
            const vy = (camCenter.y - vHalfH - minY) * scaleY;
            const vw = vHalfW * 2 * scaleX;
            const vh = vHalfH * 2 * scaleY;
            ctx.strokeStyle = colors.accent;
            ctx.lineWidth = 1.5;
            ctx.globalAlpha = 0.7;
            ctx.strokeRect(vx, vy, vw, vh);
            ctx.globalAlpha = 1;
        }
        
        minimapEl.appendChild(mmCanvas);
    }

    function refreshVisualization() {
        refreshCanvas();
        updateStats();
        updateMinimap();
    }

    // ---- view toggle + data reload ------------------------------------------

    /**
     * Inject the Detail / Overview toggle buttons into the graph header.
     * Called once after buildOverlay() so the header DOM exists.
     */
    function addViewToggleButtons() {
        const header = overlay.querySelector(".app-div-b");
        if (!header) return;

        const wrap = document.createElement("div");
        wrap.className = "gx-view-toggle";
        wrap.setAttribute("role", "group");
        wrap.setAttribute("aria-label", "Graph view mode");
        wrap.innerHTML = `
            <button class="gx-view-btn${graphView === "detail" ? " active" : ""}"
                    data-view="detail"
                    aria-pressed="${graphView === "detail"}"
                    title="Show all nodes and edges">Detail</button>
            <button class="gx-view-btn${graphView === "overview" ? " active" : ""}"
                    data-view="overview"
                    aria-pressed="${graphView === "overview"}"
                    title="Show Tier-1 anchor nodes only">Overview</button>`;

        // Insert before the search wrap (second-to-last child group)
        const searchWrap = header.querySelector(".gx-search-wrap");
        header.insertBefore(wrap, searchWrap);

        wrap.querySelectorAll(".gx-view-btn").forEach((btn) => {
            btn.addEventListener("click", () => {
                if (btn.dataset.view === graphView) return; // no-op
                graphView = btn.dataset.view;

                // Update active state
                wrap.querySelectorAll(".gx-view-btn").forEach((b) => {
                    const active = b.dataset.view === graphView;
                    b.classList.toggle("active", active);
                    b.setAttribute("aria-pressed", String(active));
                });

                reloadGraphData();
            });
        });
    }

    /**
     * Re-fetch graph data from the API using the current graphView and
     * re-initialise the visualisation.  Called when the view toggle changes.
     */
    async function reloadGraphData() {
        if (!currentProjectId) return;

        // Show a lightweight loading indicator in the counts bar
        const countEl = overlay && overlay.querySelector("#gx-counts");
        if (countEl) countEl.textContent = "Loading…";

        try {
            const resp = await fetch(`/api/projects/${currentProjectId}/graph?view=${graphView}`);
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            const data = await resp.json();

            // Reset interaction state so stale references don't linger
            hoverNode = null;
            selectedNode = null;
            focusNodeId = null;
            searchTerm = "";
            const searchInput = overlay && overlay.querySelector("#gx-search");
            if (searchInput) searchInput.value = "";

            prepare(data);
            fg.graphData(visibleData());
            updateCounts();
            updateStats();
            updateMinimap();
            applyForces();
            setTimeout(() => fg && fg.zoomToFit(500, 60), 600);
        } catch (err) {
            if (countEl) countEl.textContent = "Failed to load graph";
            Log.error("graph_explorer", "reloadGraphData failed", err);
        }
    }

    // ---- overlay -------------------------------------------------------------

    function buildOverlay() {
        overlay = document.createElement("div");
        overlay.id = "gx-overlay";
        overlay.className = "dialog-backdrop gx-backdrop";
        overlay.innerHTML = `
            <div class="gx-panel elev-lg">
                <div class="app-div-b" style="display:flex;align-items:center;gap:12px;padding:12px 16px;flex:none">
                    <h6 style="margin:0">Knowledge graph</h6>
                    <span id="gx-counts" class="app-faint app-num" style="font-size:10.5px;flex:1"></span>
                    <div class="gx-search-wrap">
                        <input id="gx-search" class="input" placeholder="Search nodes…" style="width:220px;font-size:12px;padding:5px 9px">
                        <div id="gx-search-results" class="gx-search-results hidden"></div>
                    </div>
                    <button id="gx-settings-toggle" class="app-tab" aria-pressed="true" title="Toggle controls">Controls</button>
                    <button id="gx-close" class="btn btn-ghost btn-icon" style="width:26px;height:26px" aria-label="Close">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M6 6l12 12M18 6L6 18"></path></svg>
                    </button>
                </div>
                <div style="display:flex;flex:1;min-height:0;position:relative">
                    <div id="gx-canvas" style="flex:1;min-width:0"></div>
                    <div id="gx-drawer" class="app-div-l app-scroll gx-drawer"></div>
                    <div id="gx-selection" class="card gx-selection hidden"></div>
                    <div id="gx-stats" class="gx-stats" style="position:absolute;bottom:12px;left:12px;background:rgba(0,0,0,0.5);border-radius:4px;padding:6px 10px;font-size:10px;color:#bbb;backdrop-filter:blur(4px)"></div>
                    <div id="gx-minimap" class="gx-minimap" style="position:absolute;bottom:12px;right:12px;width:120px;height:90px;background:rgba(0,0,0,0.5);border-radius:4px;overflow:hidden;border:1px solid rgba(255,255,255,0.1);cursor:crosshair"></div>
                    <div class="gx-zoom">
                        <button id="gx-zoom-out" class="btn btn-secondary btn-icon" aria-label="Zoom out">−</button>
                        <span id="gx-zoom-label" class="app-faint app-num" style="font-size:10px;min-width:34px;text-align:center">100%</span>
                        <button id="gx-zoom-in" class="btn btn-secondary btn-icon" aria-label="Zoom in">+</button>
                        <button id="gx-zoom-fit" class="btn btn-secondary btn-icon" aria-label="Fit" title="Fit to view">⛶</button>
                    </div>
                </div>
            </div>`;
        document.body.appendChild(overlay);

        overlay.querySelector("#gx-close").addEventListener("click", close);
        overlay.addEventListener("click", (event) => {
            if (event.target === overlay) close();
        });
        overlay.querySelector("#gx-settings-toggle").addEventListener("click", (event) => {
            const drawer = overlay.querySelector("#gx-drawer");
            const pressed = event.currentTarget.getAttribute("aria-pressed") === "true";
            event.currentTarget.setAttribute("aria-pressed", String(!pressed));
            drawer.classList.toggle("hidden", pressed);
            resizeCanvas();
        });
        overlay.querySelector("#gx-search").addEventListener("input", (event) => {
            searchTerm = event.target.value.trim();
            refreshData();
            renderSearchDropdown();
        });
        overlay.querySelector("#gx-zoom-in").addEventListener("click", () => fg && fg.zoom(fg.zoom() * 1.4, 250));
        overlay.querySelector("#gx-zoom-out").addEventListener("click", () => fg && fg.zoom(fg.zoom() / 1.4, 250));
        overlay.querySelector("#gx-zoom-fit").addEventListener("click", () => fg && fg.zoomToFit(400, 60));
        
        // Minimap click navigation
        overlay.querySelector("#gx-minimap").addEventListener("click", (event) => {
            if (!fg || !minimapBounds) return;
            const { minX, minY, scaleX, scaleY } = minimapBounds;
            const rect = event.currentTarget.getBoundingClientRect();
            const worldX = (event.clientX - rect.left) / scaleX + minX;
            const worldY = (event.clientY - rect.top)  / scaleY + minY;
            fg.centerAt(worldX, worldY, 400);
        });
    }

    function canvasSize() {
        const host = overlay.querySelector("#gx-canvas");
        return { width: host.clientWidth, height: host.clientHeight };
    }

    function resizeCanvas() {
        if (!fg || !overlay) return;
        requestAnimationFrame(() => {
            const { width, height } = canvasSize();
            fg.width(width).height(height);
        });
    }

    function onThemeChange() {
        if (!fg) return;
        readTheme();
        fg.backgroundColor(colors.bg);
        const drawer = overlay.querySelector("#gx-drawer");
        if (!drawer.classList.contains("hidden")) {
            drawer.innerHTML = drawerHtml();
            bindDrawer();
        }
        refreshCanvas();
    }

    function onKeyDown(event) {
        if (event.key === "Escape") close();
    }

    function open(graphData, options = {}) {
        if (typeof ForceGraph === "undefined") {
            Log.error("graph_explorer", "force-graph library not loaded");
            return;
        }
        if (overlay) close();

        // Store project ID for view-toggle re-fetches
        currentProjectId = options.projectId || null;
        // Always start in detail view when opening fresh
        graphView = "detail";

        storageKey = `graphExplorer:${options.projectId || "default"}`;
        settings = loadSettings();
        hoverNode = null;
        selectedNode = null;
        focusNodeId = null;
        focusDepth = 1;
        searchTerm = "";

        readTheme();
        prepare(graphData);
        buildOverlay();

        // Inject view toggle buttons into the header (requires overlay to exist)
        addViewToggleButtons();

        const drawer = overlay.querySelector("#gx-drawer");
        drawer.innerHTML = drawerHtml();
        bindDrawer();

        const host = overlay.querySelector("#gx-canvas");
        const { width, height } = canvasSize();

        fg = ForceGraph()(host)
            .width(width)
            .height(height)
            .backgroundColor(colors.bg)
            .nodeId("id")
            .nodeVal((node) => Math.max(1, node.degree))
            .nodeLabel(() => "") // labels drawn in nodeCanvasObject
            .nodeCanvasObject((node, ctx, k) => paintNode(node, ctx, k))
            .nodePointerAreaPaint((node, color, ctx) => {
                ctx.fillStyle = color;
                ctx.beginPath();
                ctx.arc(node.x, node.y, nodeRadius(node) + 4, 0, 2 * Math.PI);
                ctx.fill();
            })
            .linkColor(linkColor)
            .linkWidth((link) => {
                // Bridge edges are drawn entirely by linkCanvasObject (dashed);
                // returning 0 here suppresses the default solid line.
                if (link.bridge) return 0;
                const hl = highlightSet();
                if (hl) {
                    const s = typeof link.source === "object" ? link.source.id : link.source;
                    const t = typeof link.target === "object" ? link.target.id : link.target;
                    const anchor = (hoverNode || selectedNode).id;
                    if (s === anchor || t === anchor) return settings.linkWidth * 1.8;
                }
                return settings.linkWidth;
            })
            .linkCurvature(l => l._curvature || 0)
            .linkDirectionalArrowLength(link => {
                // No arrows on bridge edges
                if (link.bridge) return 0;
                const hl = highlightSet();
                if (!hl) return 3.5;
                const s = typeof link.source === "object" ? link.source.id : link.source;
                const t = typeof link.target === "object" ? link.target.id : link.target;
                const anchor = (hoverNode || selectedNode)?.id;
                return (s === anchor || t === anchor) ? 6 : 2;
            })
            .linkDirectionalArrowRelPos(1)
            .linkDirectionalArrowColor(linkColor)
            .linkCanvasObjectMode(() => "after")
            .linkCanvasObject((link, ctx, k) => {
                const s = link.source, t = link.target;
                if (!s || !t || s.x == null) return;

                // ---- Bridge edge: draw dashed line manually -----------------
                if (link.bridge) {
                    const dashLen = 5 / k;
                    ctx.save();
                    ctx.setLineDash([dashLen, dashLen]);
                    ctx.strokeStyle = "rgba(128,128,128,0.28)";
                    ctx.lineWidth = 0.8 / k;
                    ctx.globalAlpha = 0.6;
                    ctx.beginPath();
                    ctx.moveTo(s.x, s.y);
                    ctx.lineTo(t.x, t.y);
                    ctx.stroke();
                    ctx.restore();

                    // Label at midpoint (only at higher zoom)
                    if (k >= 2.5) {
                        const mx = (s.x + t.x) / 2;
                        const my = (s.y + t.y) / 2;
                        const label = (link.relation || "").replace(/_/g, " ");
                        const fontSize = 8 / k;
                        ctx.save();
                        ctx.font = `italic ${fontSize}px Inter, system-ui, sans-serif`;
                        ctx.textAlign = "center";
                        ctx.textBaseline = "middle";
                        ctx.globalAlpha = 0.45;
                        ctx.fillStyle = colors.text;
                        ctx.fillText(label, mx, my);
                        ctx.restore();
                    }
                    return;
                }

                // ---- Normal edge: relation label at zoom threshold ----------
                const threshold = 1.8;
                if (k < threshold) return;
                const alpha = Math.min(1, (k - threshold) / 0.5);

                const mx = (s.x + t.x) / 2;
                const my = (s.y + t.y) / 2;

                const hl = highlightSet();
                const sId = typeof s === "object" ? s.id : s;
                const tId = typeof t === "object" ? t.id : t;
                const anchor = (hoverNode || selectedNode)?.id;
                const isHighlighted = hl && (sId === anchor || tId === anchor);
                const labelAlpha = isHighlighted ? alpha : alpha * 0.35;
                if (labelAlpha < 0.05) return;

                const label = (link.relation || "").replace(/_/g, " ");
                const fontSize = 9 / k;
                ctx.font = `${fontSize}px Inter, system-ui, sans-serif`;
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";

                const tw = ctx.measureText(label).width;
                const pad = 2 / k;
                ctx.globalAlpha = labelAlpha * 0.75;
                ctx.fillStyle = colors.bg;
                ctx.fillRect(mx - tw / 2 - pad, my - fontSize / 2 - pad, tw + pad * 2, fontSize + pad * 2);

                ctx.globalAlpha = labelAlpha;
                ctx.fillStyle = colors.text;
                ctx.fillText(label, mx, my);
                ctx.globalAlpha = 1;
            })
            .onNodeHover((node) => {
                hoverNode = node || null;
                host.style.cursor = node ? "pointer" : "";
            })
            .onNodeClick((node) => {
                const now = Date.now();
                if (lastClick.id === node.id && now - lastClick.t < 350) {
                    // double-click = quick focus toggle
                    focusNodeId = focusNodeId === node.id ? null : node.id;
                    refreshData();
                    setTimeout(() => fg && fg.zoomToFit(400, 60), 350);
                }
                lastClick = { id: node.id, t: now };
                setSelected(node);
            })
            .onBackgroundClick(() => setSelected(null))
            .onZoom(({ k }) => {
                updateZoomLabel(k);
                updateMinimap();
            })
            .autoPauseRedraw(false) // keep repainting so hover dimming works after the sim cools
            .cooldownTicks(200)
            .d3VelocityDecay(0.3);

        applyForces();
        fg.graphData(visibleData());
        updateCounts();
        updateStats();
        updateMinimap();

        if (options.focusNodeId && nodeById.has(options.focusNodeId)) {
            setSelected(nodeById.get(options.focusNodeId));
        }
        setTimeout(() => fg && fg.zoomToFit(600, 60), 700);

        document.addEventListener("keydown", onKeyDown);
        document.addEventListener("themechange", onThemeChange);
        window.addEventListener("resize", resizeCanvas);
        document.body.style.overflow = "hidden";
    }

    function close() {
        document.removeEventListener("keydown", onKeyDown);
        document.removeEventListener("themechange", onThemeChange);
        window.removeEventListener("resize", resizeCanvas);
        document.body.style.overflow = "";
        if (fg) {
            fg._destructor && fg._destructor();
            fg = null;
        }
        if (overlay) {
            overlay.remove();
            overlay = null;
        }
        // Reset view state so next open() starts fresh
        graphView = "detail";
        currentProjectId = null;
    }

    return { open, close };
})();
