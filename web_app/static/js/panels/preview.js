// preview.js — Preview panel for generated exports (Excel, PPTX, etc.)
// Manages state transitions: Sources → Preview → Sources
// Renderer registry for pluggable export type handlers

"use strict";

const PreviewPanel = (() => {
    // ── State ──────────────────────────────────────────────────────────────

    let currentContext = null;  // { exportId, kind, filename }
    let sourcesPreviousWidth = null;  // restore on exit
    let sourcesPreviousContent = null;  // restore on exit
    let sourcesPreviousTab = null;  // restore on exit

    // Renderer registry: { excel: { mount, unmount }, pptx: { mount, unmount }, ... }
    const renderers = {};

    // ── Helpers ────────────────────────────────────────────────────────────

    function el(id) {
        return document.getElementById(id);
    }

    function closeEvidenceOverlay() {
        const overlay = el("evidence-overlay");
        if (overlay && overlay.classList.contains("is-open")) {
            overlay.classList.remove("is-open");
        }
    }

    // ── Public API ─────────────────────────────────────────────────────────

    function init() {
        // Called once on page load; sets up any global listeners if needed
    }

    function register(kind, renderer) {
        // renderer = { mount(context), unmount() }
        if (!renderer || typeof renderer.mount !== "function") {
            console.warn(`PreviewPanel.register: renderer for '${kind}' missing mount()`);
            return;
        }
        renderers[kind] = renderer;
    }

    function enterPreview(context) {
        // context = { exportId, kind, filename }
        if (!context || !context.kind) {
            console.error("PreviewPanel.enterPreview: missing context or kind");
            return;
        }

        const panelSources = el("panel-sources");
        if (!panelSources) {
            console.error("PreviewPanel.enterPreview: #panel-sources not found");
            return;
        }

        // Stash current state
        currentContext = context;
        sourcesPreviousWidth = panelSources.style.width || "";
        sourcesPreviousContent = panelSources.innerHTML;
        sourcesPreviousTab = document.querySelector(".sidebar-nav-btn.is-active")?.getAttribute("data-tab") || "files";

        // Close Evidence overlay if open
        closeEvidenceOverlay();

        // Remove collapsed class if present
        panelSources.classList.remove("is-collapsed");

        // Add preview mode class
        panelSources.classList.add("is-preview");

        // Render preview shell
        renderPreviewShell(context);

        // Call renderer's mount
        const renderer = renderers[context.kind];
        if (renderer && typeof renderer.mount === "function") {
            renderer.mount(context);
        } else {
            console.warn(`PreviewPanel.enterPreview: no renderer for kind '${context.kind}'`);
        }
    }

    function exitPreview() {
        if (!currentContext) {
            console.warn("PreviewPanel.exitPreview: no active preview");
            return;
        }

        const panelSources = el("panel-sources");
        if (!panelSources) {
            console.error("PreviewPanel.exitPreview: #panel-sources not found");
            return;
        }

        // Call renderer's unmount
        const renderer = renderers[currentContext.kind];
        if (renderer && typeof renderer.unmount === "function") {
            renderer.unmount();
        }

        // Remove preview mode class
        panelSources.classList.remove("is-preview");

        // Restore previous content
        if (sourcesPreviousContent) {
            panelSources.innerHTML = sourcesPreviousContent;
        }

        // Restore previous width
        if (sourcesPreviousWidth) {
            panelSources.style.width = sourcesPreviousWidth;
        }

        // Restore previous tab (re-attach event listeners if needed)
        if (sourcesPreviousTab) {
            const tabBtn = document.querySelector(`.sidebar-nav-btn[data-tab="${sourcesPreviousTab}"]`);
            if (tabBtn) {
                tabBtn.click();
            }
        }

        // Clear state
        currentContext = null;
        sourcesPreviousWidth = null;
        sourcesPreviousContent = null;
        sourcesPreviousTab = null;
    }

    // ── Preview Shell Renderer ─────────────────────────────────────────────

    function renderPreviewShell(context) {
        const panelSources = el("panel-sources");
        if (!panelSources) return;

        // Build preview header + tabs + body container
        const html = `
            <div class="app-div-b" style="display:flex;align-items:center;gap:6px;padding:13px 14px 11px">
                <button id="preview-back-btn" class="btn btn-icon" title="Back to sources" style="padding:4px;margin-right:6px">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M19 12H5M12 19l-7-7 7-7"/>
                    </svg>
                </button>
                <h6 style="margin:0;flex:1;font-size:13px;font-weight:500">${escapeHtml(context.filename)}</h6>
                <span class="app-faint" style="font-size:11px">${escapeHtml((context.kind || "").toUpperCase())}</span>
            </div>
            <div id="preview-tabs" class="preview-tabs"></div>
            <div id="preview-body" class="preview-body"></div>
            <div id="preview-container" class="app-scroll" style="flex:1;min-height:0;padding:12px;display:flex;align-items:center;justify-content:center">
                <div style="text-align:center;color:var(--color-faint)">
                    <p style="margin:0 0 8px;font-size:12px">Renderer not loaded</p>
                    <p style="margin:0;font-size:11px;opacity:0.7">${escapeHtml(context.kind)}</p>
                </div>
            </div>
        `;

        panelSources.innerHTML = html;

        // Attach back button listener
        const backBtn = el("preview-back-btn");
        if (backBtn) {
            backBtn.addEventListener("click", exitPreview);
        }
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str == null ? "" : String(str);
        return div.innerHTML;
    }

    // ── Exports ────────────────────────────────────────────────────────────

    return {
        init,
        register,
        enterPreview,
        exitPreview,
    };
})();

// Expose on window for global access
window.PreviewPanel = PreviewPanel;
