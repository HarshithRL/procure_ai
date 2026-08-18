// Home screen: sourcing-projects table fed by GET /api/projects.

"use strict";

(() => {
    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str == null ? "" : String(str);
        return div.innerHTML;
    }

    function fmtSpend(eur) {
        const value = Number(eur);
        if (!eur || Number.isNaN(value) || value <= 0) return "—";
        return `€${(value / 1_000_000).toFixed(1)} M`;
    }

    function fmtNodes(project) {
        if (project.active_doc_count > 0 && project.node_count === 0) return '<span class="app-faint">building…</span>';
        if (!project.node_count) return '<span class="app-faint">—</span>';
        return `${project.node_count.toLocaleString("en-US")} / ${project.edge_count.toLocaleString("en-US")}`;
    }

    function statusTag(project) {
        if (project.active_doc_count > 0) return '<span class="tag tag-accent">Extracting</span>';
        if (project.node_count > 0) return '<span class="tag tag-outline">Ready to decide</span>';
        return '<span class="tag tag-neutral">Draft brief</span>';
    }

    function relTime(iso) {
        if (!iso) return "—";
        const then = new Date(iso.endsWith("Z") || iso.includes("+") ? iso : iso.replace(" ", "T") + "Z");
        const mins = Math.floor((Date.now() - then.getTime()) / 60000);
        if (Number.isNaN(mins)) return "—";
        if (mins < 1) return "now";
        if (mins < 60) return `${mins} min ago`;
        const hours = Math.floor(mins / 60);
        if (hours < 24) return `${hours} h ago`;
        const days = Math.floor(hours / 24);
        if (days === 1) return "yesterday";
        if (days < 30) return `${days} d ago`;
        return then.toLocaleDateString("en-GB", { day: "2-digit", month: "short" });
    }

    function summaryLine(projects) {
        const active = projects.filter((p) => p.node_count > 0 || p.active_doc_count > 0 || p.doc_count > 0).length;
        const spend = projects.reduce((sum, p) => sum + (Number(p.target_spend_eur) || 0), 0);
        const docs = projects.reduce((sum, p) => sum + (p.doc_count || 0), 0);
        const bits = [];
        bits.push(`${projects.length} project${projects.length === 1 ? "" : "s"} · ${active} active`);
        if (spend > 0) bits.push(`€${(spend / 1_000_000).toFixed(1)} M under evaluation`);
        bits.push(`${docs} vendor document${docs === 1 ? "" : "s"} indexed`);
        return bits.join(" · ");
    }

    function updateKpis(projects) {
        const active = projects.filter((p) => p.node_count > 0 || p.active_doc_count > 0 || p.doc_count > 0).length;
        const spend = projects.reduce((sum, p) => sum + (Number(p.target_spend_eur) || 0), 0);
        const docs = projects.reduce((sum, p) => sum + (p.doc_count || 0), 0);
        const el = (id) => document.getElementById(id);
        if (el("kpi-projects")) el("kpi-projects").textContent = String(projects.length);
        if (el("kpi-active")) el("kpi-active").textContent = String(active);
        if (el("kpi-spend")) el("kpi-spend").textContent = spend > 0 ? `€${(spend / 1_000_000).toFixed(1)} M` : "—";
        if (el("kpi-docs")) el("kpi-docs").textContent = String(docs);
    }

    function rowHtml(project) {
        return `
            <button class="app-row-btn" data-project-id="${project.id}">
                <span class="app-num app-div-b" style="display:grid;grid-template-columns:2.1fr 1fr .9fr 52px 52px 96px 76px 122px 78px;align-items:center;font-size:13px;padding:11px 8px">
                    <span style="font-family:var(--font-heading);font-size:16px">${escapeHtml(project.name)}</span>
                    <span class="app-muted">${escapeHtml(project.category || "—")}</span>
                    <span class="app-muted">${escapeHtml(project.region || "—")}</span>
                    <span>${project.vendor_count || "—"}</span>
                    <span>${project.doc_count || "—"}</span>
                    <span>${fmtNodes(project)}</span>
                    <span>${fmtSpend(project.target_spend_eur)}</span>
                    <span>${statusTag(project)}</span>
                    <span class="app-faint">${relTime(project.updated_at)}</span>
                </span>
            </button>`;
    }

    async function load() {
        const rowsEl = document.getElementById("project-rows");
        const summaryEl = document.getElementById("projects-summary");
        if (!rowsEl) return;
        try {
            const projects = await Api.get("/api/projects");

            if (summaryEl) summaryEl.textContent = summaryLine(projects);
            updateKpis(projects);
            if (projects.length === 0) {
                rowsEl.innerHTML = '<p class="app-faint" style="font-size:12.5px;padding:14px 8px">No sourcing projects yet — create one to get started.</p>';
                return;
            }
            rowsEl.innerHTML = projects.map(rowHtml).join("");
            rowsEl.querySelectorAll(".app-row-btn").forEach((btn) => {
                btn.addEventListener("click", () => {
                    window.location.href = `/projects/${btn.dataset.projectId}`;
                });
            });
        } catch (err) {
            rowsEl.innerHTML = '<p class="app-faint" style="font-size:12.5px;padding:14px 8px">Failed to load projects.</p>';
            Log.error("home", "Failed to load projects", err);
        }
    }

    document.addEventListener("DOMContentLoaded", load);
})();
