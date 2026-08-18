// Shared knowledge-graph build progress: dialog, upload loop, polling.
// Used by new_project.js (manual form) and builder_chat.js (chat path).

"use strict";

const KgBuild = (() => {
    const logged = new Map();

    function el(id) {
        return document.getElementById(id);
    }

    function appendLog(line) {
        const logEl = el("np-ing-log");
        if (!logEl) return;
        const div = document.createElement("div");
        div.style.whiteSpace = "pre";
        div.textContent = line;
        logEl.appendChild(div);
        logEl.scrollTop = logEl.scrollHeight;
    }

    function stageFor(pct) {
        if (pct < 25) return "Parsing & OCR";
        if (pct < 50) return "Extracting entities";
        if (pct < 80) return "Resolving & linking";
        return "Writing the graph";
    }

    function resetDialog() {
        logged.clear();
        const logEl = el("np-ing-log");
        if (logEl) logEl.innerHTML = "";
        const bar = el("np-ing-bar");
        if (bar) bar.style.width = "0%";
        const pct = el("np-ing-pct");
        if (pct) pct.textContent = "0%";
        const stage = el("np-ing-stage");
        if (stage) stage.textContent = "Parsing & OCR";
        const nodes = el("np-ing-nodes");
        if (nodes) nodes.textContent = "0";
        const edges = el("np-ing-edges");
        if (edges) edges.textContent = "0";
        const docs = el("np-ing-docs");
        if (docs) docs.textContent = "0 / 0";
        const openBtn = el("np-open-workspace");
        if (openBtn) openBtn.classList.add("hidden");
    }

    function showDialog(projectId) {
        resetDialog();
        const dialog = el("np-dialog");
        dialog.classList.remove("hidden");
        const openBtn = el("np-open-workspace");
        openBtn.replaceWith(openBtn.cloneNode(true));
        el("np-open-workspace").addEventListener("click", () => {
            window.location.href = `/projects/${projectId}`;
        });
        // Initialize draggable if available
        if (typeof DraggablePanel !== "undefined") {
            const panel = el("np-dialog-content");
            if (panel) DraggablePanel.init(panel);
        }
    }

    async function uploadFiles(projectId, files) {
        let uploaded = 0;
        for (const file of files) {
            appendLog(`upload  ${file.name}`);
            const form = new FormData();
            form.append("file", file);
            const up = await Api.raw(`/api/projects/${projectId}/documents`, { method: "POST", body: form });
            if (up.ok) {
                uploaded += 1;
            } else {
                let errorMsg = "upload failed";
                try {
                    const data = await up.json();
                    errorMsg = data.error || `HTTP ${up.status}`;
                } catch (_parseErr) {
                    const text = await up.text().catch(() => "");
                    errorMsg = `HTTP ${up.status}` + (text ? ` — ${text.slice(0, 120)}` : "");
                }
                Log.error("kg_build", `upload failed for ${file.name}`, { status: up.status, error: errorMsg });
                appendLog(`error   ${file.name} — ${errorMsg}`);
            }
        }
        return uploaded;
    }

    async function pollProgress(projectId, total) {
        let done = false;
        while (!done) {
            await new Promise((resolve) => setTimeout(resolve, 1200));
            try {
                const status = await Api.get(`/api/projects/${projectId}/build/status`);
                const docs = status.documents || [];
                const graph = status.graph || { nodes: [], edges: [] };

                docs.forEach((doc) => {
                    const prev = logged.get(doc.id);
                    if (doc.status !== prev) {
                        logged.set(doc.id, doc.status);
                        if (doc.status === "processing") appendLog(`parse   ${doc.filename}`);
                        if (doc.status === "completed") appendLog(`graph   ${doc.filename} — linked`);
                        if (doc.status === "failed") appendLog(`error   ${doc.filename} — ${doc.error_message || "failed"}`);
                    }
                });

                const finished = docs.filter((d) => d.status === "completed" || d.status === "failed");
                const pct = total === 0 ? 100 : Math.round((finished.length / total) * 100);
                el("np-ing-bar").style.width = `${pct}%`;
                el("np-ing-pct").textContent = `${pct}%`;
                el("np-ing-stage").textContent = pct >= 100 ? "Done" : stageFor(pct);
                el("np-ing-docs").textContent = `${finished.length} / ${total}`;
                el("np-ing-nodes").textContent = String((graph.nodes || []).length);
                el("np-ing-edges").textContent = ((graph.edges || []).length).toLocaleString("en-US");

                done = status.complete === true || finished.length >= total;
            } catch (err) {
                Log.error("kg_build", "Polling failed", err);
            }
        }
        appendLog("done    knowledge graph ready");
        el("np-open-workspace").classList.remove("hidden");
    }

    async function run(projectId, files) {
        showDialog(projectId);
        if (!files || files.length === 0) {
            window.location.href = `/projects/${projectId}`;
            return;
        }
        const uploaded = await uploadFiles(projectId, files);
        await Api.post(`/api/projects/${projectId}/build`, {});
        await pollProgress(projectId, uploaded);
    }

    return { run, uploadFiles, pollProgress, showDialog, resetDialog, appendLog };
})();
