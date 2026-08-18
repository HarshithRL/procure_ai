// Chat panel: assistant conversation rendered in the design language —
// right-aligned user bubbles, "AI" gutter answers, numbered evidence chips
// that open the evidence overlay, confidence tag, and a "How this was
// derived" trace block. Talks to /api/projects/<id>/chat (+ /stream SSE).

"use strict";

const ChatPanel = (() => {
    let projectId = null;

    const SUGGESTIONS = [
        "Which vendors meet every mandatory requirement? Flag anything you cannot evidence.",
        "3-year TCO ranking and cost drivers",
        "Where can we negotiate?",
        "Which claims are contradicted across documents?",
    ];
    const asked = new Set();

    function el(id) {
        return document.getElementById(id);
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str == null ? "" : String(str);
        return div.innerHTML;
    }

    // Configure marked once (GFM tables, smart line-breaks).
    // Called lazily on first use so it runs after the script is loaded.
    let _markedConfigured = false;
    function configureMarked() {
        if (typeof marked === "undefined" || _markedConfigured) return;
        marked.use({ gfm: true, breaks: true });
        _markedConfigured = true;
    }

    function contentHtml(content, evidenceCount) {
        const used = new Set();
        const raw = String(content || "");

        // Step 1: extract [ev:N] positions → placeholders.
        // Use a marker unlikely to appear in markdown output.
        const placeholder = (n) => `EVCHIP${n}EVCHIP`;
        const placeholderRe = /EVCHIP(\d+)EVCHIP/g;

        const withPlaceholders = raw.replace(/\[ev:(\d+)\]/g, (_, n) => {
            const number = Number(n);
            if (number >= 1 && number <= evidenceCount) {
                used.add(number);
                return placeholder(number);
            }
            return "";
        });

        // Step 2: render markdown → HTML with proper formatting
        let html;
        if (typeof marked !== "undefined") {
            configureMarked();
            try {
                // marked returns HTML string
                const rawHtml = marked.parse(withPlaceholders);
                // Ensure proper escaping while preserving HTML structure
                html = rawHtml;
            } catch (err) {
                Log.error("chat", "Markdown parsing failed", err);
                // Fallback: plain-text paragraph split
                html = withPlaceholders
                    .split(/\n{2,}/)
                    .filter((p) => p.trim().length > 0)
                    .map((p) => `<p>${escapeHtml(p.trim())}</p>`)
                    .join("");
            }
        } else {
            // Fallback: plain-text paragraph split (original behaviour).
            html = withPlaceholders
                .split(/\n{2,}/)
                .filter((p) => p.trim().length > 0)
                .map((p) => `<p>${escapeHtml(p.trim())}</p>`)
                .join("");
        }

        // Step 3: swap placeholders back to chip buttons.
        html = html.replace(placeholderRe, (_, n) => chipHtml(Number(n)));

        // Step 4: wrap in a prose container for consistent typography.
        return { html: `<div class="chat-md">${html}</div>`, used };
    }

    function scrollToBottom() {
        const container = el("chat-messages");
        if (container) container.scrollTop = container.scrollHeight;
    }

    function chipHtml(number) {
        return `<button class="app-chip ev-chip" data-ev-n="${number}" type="button">${number}</button>`;
    }

    function confidenceHtml(message) {
        if (!message.confidence) return "";
        const refs = (message.evidence || []).length;
        const label = message.confidence.charAt(0).toUpperCase() + message.confidence.slice(1);
        return `
            <div style="display:flex;align-items:center;gap:8px;font-size:11px;margin-bottom:8px">
                <span class="tag tag-accent">Confidence ${escapeHtml(label.toLowerCase())}</span>
                <span class="app-faint app-num">${refs} reference${refs === 1 ? "" : "s"}</span>
            </div>`;
    }

    function traceHtml(trace) {
        if (!trace || trace.length === 0) return "";
        const lines = trace
            .map((step) => `<div>${escapeHtml(step.label || step.tool || "")}</div>`)
            .join("");
        return `
            <div class="app-num app-tint" style="padding:8px 11px;font-size:10.5px;line-height:1.7;border-radius:var(--radius-sm);margin-bottom:8px">
                <div class="app-faint" style="letter-spacing:.1em;text-transform:uppercase;font-size:9px;margin-bottom:3px">How this was derived</div>
                ${lines}
            </div>`;
    }

    function chipRowHtml(evidence, used) {
        const remaining = (evidence || [])
            .map((ref, index) => index + 1)
            .filter((n) => !used.has(n));
        if (remaining.length === 0) return "";
        return `
            <div class="app-faint app-num" style="font-size:10.5px;margin-bottom:8px">
                Evidence: ${remaining.map(chipHtml).join(" ")}
            </div>`;
    }

    function bindChips(scope, evidence) {
        scope.querySelectorAll(".ev-chip").forEach((chip) => {
            chip.addEventListener("click", () => {
                const number = Number(chip.dataset.evN);
                const ref = (evidence || [])[number - 1];
                if (ref && typeof EvidencePanel !== "undefined") {
                    EvidencePanel.show(ref, number);
                }
            });
        });
    }

    function appendMessage(message) {
        const container = el("chat-messages");
        if (!container) return null;

        const wrap = document.createElement("div");
        wrap.style.marginBottom = "24px";

        if (message.role === "user") {
            wrap.innerHTML = `
                <div style="display:flex;justify-content:flex-end">
                    <p style="max-width:74%;margin:0;font-size:13.5px;padding:9px 14px;border:1px solid var(--color-divider);border-radius:var(--radius-md)">${escapeHtml(message.content)}</p>
                </div>`;
        } else {
            const evidence = message.evidence || [];
            const { html, used } = contentHtml(message.content, evidence.length);
            wrap.innerHTML = `
                <div style="display:flex;gap:14px">
                    <span class="app-accent-text" style="font-family:var(--font-heading);font-size:10px;letter-spacing:.14em;width:26px;flex:none;padding-top:4px">AI</span>
                    <div class="chat-answer" style="min-width:0;flex:1">
                        ${html}
                        ${chipRowHtml(evidence, used)}
                        ${confidenceHtml(message)}
                        ${traceHtml(message.trace)}
                    </div>
                </div>`;
            bindChips(wrap, evidence);
        }

        container.appendChild(wrap);
        scrollToBottom();
        return wrap;
    }

    function showTyping() {
        const container = el("chat-messages");
        if (!container) return null;
        const typing = document.createElement("div");
        typing.id = "chat-typing";
        typing.innerHTML = `
            <div style="display:flex;gap:14px;margin-bottom:24px;align-items:center">
                <span class="app-accent-text" style="font-family:var(--font-heading);font-size:10px;letter-spacing:.14em;width:26px;flex:none">AI</span>
                <span class="app-typing" style="display:inline-flex;gap:4px"><i></i><i></i><i></i></span>
                <span class="app-faint app-num" style="font-size:10.5px">querying knowledge graph…</span>
            </div>`;
        container.appendChild(typing);
        scrollToBottom();
        return typing;
    }

    function removeTyping() {
        const typing = el("chat-typing");
        if (typing) typing.remove();
    }

    function renderSuggestions() {
        const row = el("chat-suggestions");
        if (!row) return;
        row.innerHTML = "";
        SUGGESTIONS.filter((q) => !asked.has(q)).slice(0, 3).forEach((question) => {
            const btn = document.createElement("button");
            btn.className = "app-tab";
            btn.type = "button";
            btn.textContent = question.length > 44 ? `${question.slice(0, 42)}…` : question;
            btn.title = question;
            btn.addEventListener("click", () => send(question));
            row.appendChild(btn);
        });
    }

    async function loadHistory() {
        try {
            const messages = await Api.get(`/api/projects/${projectId}/chat`);
            messages.forEach(appendMessage);
        } catch (err) {
            Log.error("chat", "Failed to load chat history", err);
        }
    }

    function parseSseBuffer(raw) {
        const events = raw.split("\n\n");
        const remainder = events.pop() || "";
        const parsed = events.map((block) => {
            let eventName = "message";
            let data = "";
            block.split("\n").forEach((line) => {
                if (line.startsWith("event: ")) eventName = line.slice(7);
                if (line.startsWith("data: ")) data += line.slice(6);
            });
            return { eventName, data };
        });
        return { parsed, remainder };
    }

    async function streamReply(content) {
        showTyping();
        let bubble = null;
        let textEl = null;
        let buffer = "";

        function ensureBubble() {
            if (bubble) return;
            removeTyping();
            bubble = appendMessage({ role: "assistant", content: "", evidence: [] });
            textEl = bubble.querySelector(".chat-answer");
        }

        const response = await Api.raw(`/api/projects/${projectId}/chat/stream`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: content }),
        });

        if (!response.ok || !response.body) {
            ensureBubble();
            textEl.innerHTML = '<p class="app-muted" style="font-size:13px;margin:0">The assistant is unavailable right now.</p>';
            return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let raw = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            raw += decoder.decode(value, { stream: true });

            const { parsed, remainder } = parseSseBuffer(raw);
            raw = remainder;

            for (const { eventName, data } of parsed) {
                if (eventName === "token") {
                    ensureBubble();
                    buffer += data;
                    const { html } = contentHtml(buffer, 0);
                    textEl.innerHTML = html;
                    // Rebind chips if any exist in the accumulated buffer
                    bindChips(textEl, []);
                    scrollToBottom();
                } else if (eventName === "done" || eventName === "error") {
                    try {
                        const saved = JSON.parse(data);
                        if (bubble) bubble.remove();
                        removeTyping();
                        appendMessage({ role: "assistant", ...saved });
                        bubble = null;
                    } catch (err) {
                        // Keep the accumulated token buffer if the payload isn't JSON.
                        ensureBubble();
                    }
                }
            }
        }
        removeTyping();
    }

    async function send(content) {
        const input = el("chat-input");
        if (!content) return;
        asked.add(content);
        renderSuggestions();
        if (input) {
            input.value = "";
            input.disabled = true;
        }
        appendMessage({ role: "user", content, evidence: [] });
        document.dispatchEvent(new CustomEvent("chat:sent", { detail: { text: content } }));
        try {
            await streamReply(content);
        } catch (err) {
            Log.error("chat", "Chat stream failed", err);
            removeTyping();
        } finally {
            if (input) {
                input.disabled = false;
                input.focus();
            }
        }
    }

    function bindForm() {
        const form = el("chat-form");
        const input = el("chat-input");
        if (!form || !input) return;
        form.addEventListener("submit", (event) => {
            event.preventDefault();
            send(input.value.trim());
        });
    }

    function init(id) {
        projectId = id;
        bindForm();
        renderSuggestions();
        loadHistory();
    }

    return { init };
})();
