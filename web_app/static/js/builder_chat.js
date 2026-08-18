// Option 1 — chat + upload project builder.

"use strict";

(() => {
    let projectId = null;
    const staged = [];
    let streaming = false;

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

    function renderMarkdown(text) {
        if (typeof marked !== "undefined") {
            return marked.parse(text || "", { breaks: true, gfm: true });
        }
        return escapeHtml(text).replace(/\n/g, "<br>");
    }

    function appendMessage(role, content) {
        const wrap = document.createElement("div");
        wrap.style.cssText = role === "user"
            ? "align-self:flex-end;max-width:88%;padding:10px 12px;border-radius:var(--radius-md);background:color-mix(in srgb, var(--color-accent) 14%, var(--color-bg));font-size:13px"
            : "align-self:flex-start;max-width:92%;padding:10px 12px;border-radius:var(--radius-md);background:var(--color-surface-2);font-size:13px;line-height:1.5";
        if (role === "user") {
            wrap.innerHTML = escapeHtml(content).replace(/\n/g, "<br>");
        } else {
            wrap.classList.add("chat-md");
            wrap.innerHTML = renderMarkdown(content);
        }
        el("bc-messages").appendChild(wrap);
        el("bc-messages").scrollTop = el("bc-messages").scrollHeight;
        return wrap;
    }

    function applyDefinition(def) {
        if (!def) return;
        el("bc-name").value = def.name || "";
        el("bc-category").value = def.category || "";
        el("bc-region").value = def.region || "";
        el("bc-spend").value = def.target_spend_eur != null ? def.target_spend_eur : "";
        el("bc-horizon").value = def.award_horizon || "";
        el("bc-description").value = def.description || "";
        const reqs = def.requirements || [];
        const list = el("bc-req-list");
        if (!reqs.length) {
            list.textContent = "No requirements yet";
            list.className = "app-muted";
            return;
        }
        list.className = "";
        list.innerHTML = reqs
            .map((r) => `<div class="app-div-b" style="padding:4px 0;font-size:12px"><span class="app-num app-faint">${escapeHtml(r.code)}</span> · ${escapeHtml(r.text)} <span class="app-faint">(${r.weight})</span></div>`)
            .join("");
    }

    async function refreshDefinition() {
        if (!projectId) return;
        try {
            const def = await Api.get(`/api/projects/${projectId}/builder/definition`);
            applyDefinition(def);
        } catch (err) {
            Log.error("builder_chat", "definition refresh failed", err);
        }
    }

    async function ensureProject() {
        if (projectId) return projectId;
        const project = await Api.post("/api/projects", {
            name: "Untitled sourcing project",
            description: "",
            creation_path: "chat",
        });
        projectId = project.id;
        return projectId;
    }

    async function saveDefinitionFromForm() {
        if (!projectId) return;
        const payload = {
            name: el("bc-name").value.trim(),
            description: el("bc-description").value.trim(),
            category: el("bc-category").value.trim(),
            region: el("bc-region").value.trim(),
            award_horizon: el("bc-horizon").value.trim(),
        };
        const spend = el("bc-spend").value;
        if (spend) payload.target_spend_eur = Number(spend);
        await Api.raw(`/api/projects/${projectId}/builder/definition`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
    }

    async function sendMessage() {
        const input = el("bc-input");
        const text = input.value.trim();
        if (!text || streaming) return;
        input.value = "";
        streaming = true;
        el("bc-send").disabled = true;
        appendMessage("user", text);

        try {
            await ensureProject();
            const assistantEl = appendMessage("assistant", "");
            const res = await Api.raw(`/api/projects/${projectId}/builder/chat/stream`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text }),
            });
            if (!res.ok || !res.body) {
                assistantEl.textContent = "The agent is unavailable right now.";
                return;
            }

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let raw = "";
            let reply = "";
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                raw += decoder.decode(value, { stream: true });
                const blocks = raw.split("\n\n");
                raw = blocks.pop() || "";
                for (const block of blocks) {
                    let eventName = "message";
                    let data = "";
                    block.split("\n").forEach((line) => {
                        if (line.startsWith("event: ")) eventName = line.slice(7);
                        if (line.startsWith("data: ")) data += line.slice(6);
                    });
                    if (eventName === "token") {
                        reply += data;
                        assistantEl.innerHTML = renderMarkdown(reply);
                        el("bc-messages").scrollTop = el("bc-messages").scrollHeight;
                    }
                }
            }
            await refreshDefinition();
        } catch (err) {
            appendMessage("assistant", err.message || "Something went wrong.");
        } finally {
            streaming = false;
            el("bc-send").disabled = false;
            input.focus();
        }
    }

    function renderStaged() {
        const list = el("bc-staged");
        list.innerHTML = staged
            .map((file, index) => `
                <div class="app-div-b" style="display:flex;align-items:center;gap:8px;padding:5px 0;font-size:12px">
                    <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(file.name)}</span>
                    <span class="app-faint app-num">${fmtSize(file.size)}</span>
                    <button class="btn btn-ghost btn-icon" data-index="${index}" style="width:20px;height:20px" aria-label="Remove">&times;</button>
                </div>`)
            .join("");
        list.querySelectorAll("button[data-index]").forEach((btn) => {
            btn.addEventListener("click", () => {
                staged.splice(Number(btn.dataset.index), 1);
                renderStaged();
            });
        });
    }

    function stageFiles(files) {
        Array.from(files || []).forEach((file) => {
            if (!/\.(pdf|docx|xlsx)$/i.test(file.name)) return;
            staged.push(file);
        });
        renderStaged();
    }

    function bindDropzone() {
        const drop = el("bc-drop");
        const input = el("bc-file-input");
        drop.addEventListener("click", () => input.click());
        input.addEventListener("change", (e) => {
            stageFiles(e.target.files);
            input.value = "";
        });
        drop.addEventListener("dragover", (e) => {
            e.preventDefault();
            drop.style.borderColor = "var(--color-accent)";
        });
        drop.addEventListener("dragleave", () => {
            drop.style.borderColor = "";
        });
        drop.addEventListener("drop", (e) => {
            e.preventDefault();
            drop.style.borderColor = "";
            stageFiles(e.dataTransfer && e.dataTransfer.files);
        });
    }

    async function build() {
        const buildBtn = el("bc-build");
        buildBtn.disabled = true;
        buildBtn.textContent = "Preparing…";
        try {
            await ensureProject();
            await saveDefinitionFromForm();
            const name = el("bc-name").value.trim();
            if (!name) {
                alert("Enter a project name in the brief preview.");
                buildBtn.disabled = false;
                buildBtn.textContent = "Build knowledge graph";
                return;
            }
            await KgBuild.run(projectId, staged.slice());
        } catch (err) {
            alert(err.message);
            buildBtn.disabled = false;
            buildBtn.textContent = "Build knowledge graph";
        }
    }

    document.addEventListener("DOMContentLoaded", () => {
        appendMessage(
            "assistant",
            "Tell me what you are sourcing — category, region, spend, and what matters in the evaluation. You can upload vendor files on the right at any time."
        );
        el("bc-send").addEventListener("click", sendMessage);
        el("bc-input").addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        bindDropzone();
        el("bc-build").addEventListener("click", build);
    });
})();
