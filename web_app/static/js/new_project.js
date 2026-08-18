// Manual project form (Option 2): brief + requirements + file staging.
// "Build knowledge graph" creates the project, uploads staged files, then
// drives the shared KgBuild progress dialog.

"use strict";

(() => {
    const staged = [];

    function el(id) {
        return document.getElementById(id);
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str == null ? "" : String(str);
        return div.innerHTML;
    }

    function fmtSize(bytes) {
        if (bytes >= 1_048_576) return `${(bytes / 1_048_576).toFixed(1)} MB`;
        return `${Math.max(1, Math.round(bytes / 1024))} KB`;
    }

    function kindOf(name) {
        const ext = name.split(".").pop().toUpperCase();
        return ["PDF", "DOCX", "XLSX"].includes(ext) ? ext : "FILE";
    }

    function addReqRow(prefill) {
        const rows = el("np-req-rows");
        const count = rows.children.length + 1;
        const row = document.createElement("div");
        row.className = "app-div-b";
        row.style.cssText = "display:grid;grid-template-columns:66px 1fr 40px 24px;gap:6px;padding:5px 0;align-items:center";
        row.innerHTML = `
            <input class="input app-num np-req-code" style="font-size:12px;padding:4px 6px" placeholder="REQ-${String(count).padStart(2, "0")}" value="${escapeHtml((prefill && prefill.code) || "")}">
            <input class="input np-req-text" style="font-size:12.5px;padding:4px 8px" placeholder="Requirement text…" value="${escapeHtml((prefill && prefill.text) || "")}">
            <input class="input app-num np-req-weight" style="font-size:12px;padding:4px 6px;text-align:right" type="number" min="0" max="100" placeholder="Wt" value="${(prefill && prefill.weight) || ""}">
            <button class="btn btn-ghost btn-icon np-req-remove" style="width:22px;height:22px" aria-label="Remove">&times;</button>`;
        row.querySelector(".np-req-remove").addEventListener("click", () => {
            row.remove();
            updateReqHint();
        });
        row.querySelector(".np-req-weight").addEventListener("input", updateReqHint);
        rows.appendChild(row);
    }

    function collectRequirements() {
        return Array.from(el("np-req-rows").children)
            .map((row) => ({
                code: row.querySelector(".np-req-code").value.trim(),
                text: row.querySelector(".np-req-text").value.trim(),
                weight: Number(row.querySelector(".np-req-weight").value || 0),
            }))
            .filter((req) => req.code || req.text);
    }

    function updateReqHint() {
        const reqs = collectRequirements();
        const total = reqs.reduce((sum, r) => sum + r.weight, 0);
        el("np-req-hint").textContent = reqs.length
            ? `${reqs.length} line${reqs.length === 1 ? "" : "s"} · weights sum to ${total}`
            : "Weighted lines every vendor claim is scored against";
    }

    function renderStaged() {
        const listEl = el("np-staged");
        listEl.innerHTML = staged
            .map(
                (file, index) => `
                <div class="app-div-b" style="display:flex;align-items:center;gap:9px;padding:6px 0">
                    <span class="tag tag-outline app-num" style="font-size:9px;padding:0 4px">${kindOf(file.name)}</span>
                    <span style="font-size:12.5px;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(file.name)}</span>
                    <span class="app-faint app-num" style="font-size:10.5px">${fmtSize(file.size)}</span>
                    <button class="btn btn-ghost btn-icon np-unstage" data-index="${index}" style="width:22px;height:22px" aria-label="Remove">&times;</button>
                </div>`
            )
            .join("");
        listEl.querySelectorAll(".np-unstage").forEach((btn) => {
            btn.addEventListener("click", () => {
                staged.splice(Number(btn.dataset.index), 1);
                renderStaged();
            });
        });
        el("np-staged-hint").textContent = staged.length
            ? `${staged.length} file${staged.length === 1 ? "" : "s"} staged`
            : "No files staged yet";
    }

    function stageFiles(files) {
        Array.from(files || []).forEach((file) => {
            if (!/\.(pdf|docx|xlsx)$/i.test(file.name)) return;
            staged.push(file);
        });
        renderStaged();
    }

    function bindDropzone() {
        const drop = el("np-drop");
        const input = el("np-file-input");
        drop.addEventListener("click", () => input.click());
        input.addEventListener("change", (event) => {
            stageFiles(event.target.files);
            input.value = "";
        });
        drop.addEventListener("dragover", (event) => {
            event.preventDefault();
            drop.style.borderColor = "var(--color-accent)";
        });
        drop.addEventListener("dragleave", () => {
            drop.style.borderColor = "";
        });
        drop.addEventListener("drop", (event) => {
            event.preventDefault();
            drop.style.borderColor = "";
            stageFiles(event.dataTransfer && event.dataTransfer.files);
        });
    }

    async function build() {
        const name = el("np-name").value.trim();
        if (!name) {
            el("np-name").focus();
            return;
        }
        const buildBtn = el("np-build");
        buildBtn.disabled = true;
        buildBtn.textContent = "Creating project…";

        try {
            const payload = {
                name,
                description: el("np-description").value.trim(),
                category: el("np-category").value.trim(),
                region: el("np-region").value.trim(),
                award_horizon: el("np-horizon").value.trim(),
                requirements: collectRequirements(),
                creation_path: "manual",
            };
            const spend = el("np-spend").value;
            if (spend) payload.target_spend_eur = Number(spend);

            const project = await Api.post("/api/projects", payload);
            await KgBuild.run(project.id, staged.slice());
        } catch (err) {
            alert(err.message);
            buildBtn.disabled = false;
            buildBtn.textContent = "Build knowledge graph";
        }
    }

    document.addEventListener("DOMContentLoaded", () => {
        addReqRow();
        addReqRow();
        el("np-add-req").addEventListener("click", () => addReqRow());
        bindDropzone();
        el("np-build").addEventListener("click", build);
    });
})();
