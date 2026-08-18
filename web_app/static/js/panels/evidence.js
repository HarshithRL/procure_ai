// Evidence overlay: the 470px panel that opens over the sources column when
// a numbered evidence chip is clicked (in chat or studio). Renders the
// source document, locator, highlighted snippet, extraction confidence and,
// when available, the graph edge the evidence supports.

"use strict";

const EvidencePanel = (() => {
    function el(id) {
        return document.getElementById(id);
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str == null ? "" : String(str);
        return div.innerHTML;
    }

    function kindOf(name) {
        const ext = String(name || "").split(".").pop().toUpperCase();
        return ["PDF", "DOCX", "XLSX"].includes(ext) ? ext : "DOC";
    }

    // ref: { document_id?, document_name?, locator?, snippet?, confidence? }
    // extras: { triple? }
    function show(ref, number, extras) {
        const panel = el("evidence-panel");
        const body = el("evidence-body");
        const title = el("evidence-title");
        if (!panel || !body) return;

        const docName = ref.document_name || ref.document_id || "Unknown source";
        if (title) title.textContent = number ? `Evidence ${number}` : "Evidence";

        const tripleHtml = extras && extras.triple
            ? `
                <hr class="hr">
                <h6 style="margin:0 0 6px">Graph edge this supports</h6>
                <p class="app-num" style="font-size:11.5px;margin:0 0 10px">${escapeHtml(extras.triple)}</p>`
            : "";

        const confidence = typeof ref.confidence === "number" ? ref.confidence.toFixed(2) : (ref.confidence || "—");

        body.innerHTML = `
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:3px">
                <span class="tag tag-outline app-num" style="font-size:9px;padding:0 4px">${kindOf(docName)}</span>
                <span class="app-num" style="font-size:12.5px">${escapeHtml(docName)}</span>
            </div>
            <p class="app-faint app-num" style="font-size:10.5px;margin:0 0 14px">${escapeHtml(ref.locator || "")}</p>
            <div style="border:1px solid var(--color-divider);border-radius:var(--radius-md);padding:14px 16px;font-size:13.5px;line-height:1.7">
                <span class="app-mark">${escapeHtml(ref.snippet || "No snippet recorded.")}</span>
            </div>
            ${tripleHtml}
            <hr class="hr">
            <div class="app-num" style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:11px">
                <span><span class="app-faint" style="display:block;font-size:9.5px">Extraction confidence</span>${escapeHtml(String(confidence))}</span>
                <span><span class="app-faint" style="display:block;font-size:9.5px">Source</span>${escapeHtml(String(ref.document_id || "—"))}</span>
            </div>`;

        panel.classList.remove("hidden");
    }

    function hide() {
        const panel = el("evidence-panel");
        if (panel) panel.classList.add("hidden");
    }

    function init() {
        const close = el("evidence-close");
        if (close) close.addEventListener("click", hide);
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape") hide();
        });
    }

    return { init, show, hide };
})();
