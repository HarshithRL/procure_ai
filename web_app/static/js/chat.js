// chat.js - Session-aware chat page for Procura AI.
//
// Depends on (loaded before this script in base.html + chat.html):
//   - Log (core/logger.js) - structured client logging
//   - Api (core/api.js) - fetch wrapper with 401 handling
//   - marked (vendor/marked.min.js) - markdown -> HTML
//
// API contract assumed (Sprint 1 stubs):
//   GET  /api/chat/sessions              -> [{id, title, preview, updated_at}]
//   POST /api/chat/sessions              -> {id, title, preview, updated_at}
//   GET  /api/chat/sessions/<id>         -> {id, title, messages:[{role,content}]}
//   POST /api/chat/sessions/<id>/message -> {role:"assistant", content}

"use strict";

var ChatPage = (() => {
    // State
    let _activeSessionId = null;   // currently loaded session ID (string|null)
    let _isSending = false;        // true while waiting for AI response

    // localStorage keys for Power User feature flags and rail collapse
    const LS_POWER_USER = "procure_ai_power_user";
    const LS_DEV_MODE   = "procure_ai_dev_mode";
    const LS_RAIL_COLLAPSED = "procure_ai_chat_rail_collapsed";

    // DOM helpers
    function el(id) { return document.getElementById(id); }

    function escapeHtml(str) {
        const d = document.createElement("div");
        d.textContent = str == null ? "" : String(str);
        return d.innerHTML;
    }

    function relativeTime(iso) {
        if (!iso) return "";
        const diff = Date.now() - new Date(iso).getTime();
        const mins = Math.floor(diff / 60000);
        if (mins < 1)  return "just now";
        if (mins < 60) return `${mins}m ago`;
        const hrs = Math.floor(mins / 60);
        if (hrs < 24)  return `${hrs}h ago`;
        return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short" });
    }

    // Markdown rendering
    let _markedConfigured = false;
    function _ensureMarked() {
        if (typeof marked === "undefined" || _markedConfigured) return;
        marked.use({ gfm: true, breaks: true });
        _markedConfigured = true;
    }

    function renderMarkdown(content) {
        const raw = String(content || "");
        _ensureMarked();
        let html;
        if (typeof marked !== "undefined") {
            try {
                html = marked.parse(raw);
            } catch (err) {
                Log.warn("chat", "Markdown parse failed, falling back", err);
                html = raw.split(/\n{2,}/)
                    .filter(p => p.trim())
                    .map(p => `<p>${escapeHtml(p.trim())}</p>`)
                    .join("");
            }
        } else {
            html = raw.split(/\n{2,}/)
                .filter(p => p.trim())
                .map(p => `<p>${escapeHtml(p.trim())}</p>`)
                .join("");
        }
        return `<div class="chat-md">${html}</div>`;
    }

    // Scroll
    function scrollToBottom() {
        const msgs = el("chat-messages");
        if (msgs) msgs.scrollTop = msgs.scrollHeight;
    }

    // Empty state
    function setEmptyState(visible) {
        const empty = el("chat-messages-empty");
        if (!empty) return;
        empty.classList.toggle("hidden", !visible);
    }

    // Message rendering
    function appendMessage(message) {
        const thread = el("chat-messages");
        if (!thread) return null;

        setEmptyState(false);

        const wrap = document.createElement("div");
        wrap.className = "chat-msg-wrap";

        if (message.role === "user") {
            wrap.innerHTML = `
                <div class="chat-msg-user">
                    <p class="chat-msg-user-bubble">${escapeHtml(message.content)}</p>
                </div>`;
        } else {
            wrap.innerHTML = `
                <div class="chat-msg-ai">
                    <span class="chat-msg-ai-label" aria-hidden="true">AI</span>
                    <div class="chat-msg-ai-content">
                        ${renderMarkdown(message.content)}
                    </div>
                </div>`;
        }

        thread.appendChild(wrap);
        scrollToBottom();
        return wrap;
    }

    // Typing indicator
    function showTyping() {
        const thread = el("chat-messages");
        if (!thread) return null;
        removeTyping();
        const typing = document.createElement("div");
        typing.id = "chat-typing-indicator";
        typing.className = "chat-msg-wrap chat-typing-row";
        typing.innerHTML = `
            <span class="chat-msg-ai-label" aria-hidden="true">AI</span>
            <span class="app-typing" role="status" aria-label="AI is thinking">
                <i></i><i></i><i></i>
            </span>
            <span class="chat-typing-label">processing...</span>`;
        thread.appendChild(typing);
        scrollToBottom();
        return typing;
    }

    function removeTyping() {
        const t = el("chat-typing-indicator");
        if (t) t.remove();
    }

    // Dev panel
    function _devLog(meta) {
        const panel = el("dev-panel");
        if (!panel || panel.classList.contains("hidden")) return;
        const body = el("dev-panel-body");
        if (body) {
            body.textContent = JSON.stringify(meta, null, 2);
        }
    }

    // Session list rendering
    function renderSessionList(sessions) {
        const list = el("chat-session-list");
        const empty = el("chat-session-empty");
        if (!list) return;

        list.querySelectorAll(".chat-session-item").forEach(n => n.remove());

        if (!sessions || sessions.length === 0) {
            if (empty) empty.classList.remove("hidden");
            return;
        }

        if (empty) empty.classList.add("hidden");

        sessions.forEach(session => {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "chat-session-item";
            btn.dataset.sessionId = session.id;
            btn.setAttribute("role", "listitem");
            btn.setAttribute("aria-label", `Open conversation: ${session.title || "Untitled"}`);
            btn.innerHTML = `
                <span class="chat-session-item-title">${escapeHtml(session.title || "Untitled")}</span>
                <div class="chat-session-item-meta">
                    <span class="chat-session-item-preview">${escapeHtml(session.last_message || "")}</span>
                    <span class="chat-session-item-time">${relativeTime(session.created_at)}</span>
                </div>`;
            btn.addEventListener("click", () => loadSession(session.id));
            list.appendChild(btn);
        });

        _updateActiveSessionHighlight();
    }

    function prependSessionItem(session) {
        const list = el("chat-session-list");
        const empty = el("chat-session-empty");
        if (!list) return;
        if (empty) empty.classList.add("hidden");

        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "chat-session-item";
        btn.dataset.sessionId = session.id;
        btn.setAttribute("role", "listitem");
        btn.setAttribute("aria-label", `Open conversation: ${session.title || "Untitled"}`);
        btn.innerHTML = `
            <span class="chat-session-item-title">${escapeHtml(session.title || "Untitled")}</span>
            <div class="chat-session-item-meta">
                <span class="chat-session-item-preview"></span>
                <span class="chat-session-item-time">${relativeTime(session.created_at)}</span>
            </div>`;
        btn.addEventListener("click", () => loadSession(session.id));
        list.insertBefore(btn, list.firstChild);
    }

    function _updateActiveSessionHighlight() {
        const list = el("chat-session-list");
        if (!list) return;
        list.querySelectorAll(".chat-session-item").forEach(btn => {
            btn.classList.toggle("is-active", btn.dataset.sessionId === _activeSessionId);
            btn.setAttribute("aria-pressed", btn.dataset.sessionId === _activeSessionId ? "true" : "false");
        });
    }

    // Session header
    function setSessionTitle(title) {
        const h = el("chat-session-title");
        if (h) h.textContent = title || "Procura AI Chat";
    }

    // URL hash sync
    function _setHash(sessionId) {
        const url = new URL(window.location.href);
        url.hash = sessionId ? `session-${sessionId}` : "";
        window.history.replaceState(null, "", url.toString());
    }

    function _getHashSessionId() {
        const hash = window.location.hash.replace("#", "");
        if (hash.startsWith("session-")) return hash.slice("session-".length);
        return null;
    }

    // Data loading
    async function loadSessions() {
        try {
            const sessions = await Api.get("/api/chat/sessions");
            renderSessionList(sessions);

            const hashId = _getHashSessionId();
            const targetId = hashId || (sessions && sessions.length > 0 ? sessions[0].id : null);
            if (targetId) {
                await loadSession(targetId);
            }
        } catch (err) {
            Log.error("chat", "Failed to load sessions", err);
            renderSessionList([]);
        }
    }

    async function loadSession(sessionId) {
        if (!sessionId) return;
        _activeSessionId = sessionId;
        _setHash(sessionId);
        _updateActiveSessionHighlight();

        const thread = el("chat-messages");
        if (thread) {
            thread.querySelectorAll(".chat-msg-wrap").forEach(n => n.remove());
        }

        try {
            const session = await Api.get(`/api/chat/sessions/${sessionId}`);
            setSessionTitle(session.title);

            const messages = session.messages || [];
            if (messages.length === 0) {
                setEmptyState(true);
            } else {
                setEmptyState(false);
                messages.forEach(appendMessage);
            }
        } catch (err) {
            Log.error("chat", `Failed to load session ${sessionId}`, err);
            setSessionTitle("Procura AI Chat");
            setEmptyState(true);
        }
    }

    // New session
    async function createNewSession() {
        try {
            const session = await Api.post("/api/chat/sessions", {});
            prependSessionItem(session);
            await loadSession(session.id);
        } catch (err) {
            Log.error("chat", "Failed to create new session", err);
        }
    }

    // Send message
    async function sendMessage(content) {
        if (!content || _isSending) return;

        if (!_activeSessionId) {
            try {
                const session = await Api.post("/api/chat/sessions", {});
                prependSessionItem(session);
                _activeSessionId = session.id;
                _setHash(session.id);
                _updateActiveSessionHighlight();
            } catch (err) {
                Log.error("chat", "Cannot send: failed to create session", err);
                return;
            }
        }

        _isSending = true;
        _setInputEnabled(false);

        appendMessage({ role: "user", content });
        showTyping();

        const t0 = Date.now();
        let responseData = null;

        try {
            const body = { content };
            responseData = await Api.post(
                `/api/chat/sessions/${_activeSessionId}/message`,
                body
            );

            removeTyping();

            if (responseData && responseData.content) {
                appendMessage({ role: "assistant", content: responseData.content });
            }

            _devLog({
                url: `/api/chat/sessions/${_activeSessionId}/message`,
                requestBody: body,
                response: responseData,
                durationMs: Date.now() - t0,
            });

        } catch (err) {
            Log.error("chat", "Failed to send message", err);
            removeTyping();
            appendMessage({
                role: "assistant",
                content: "_The assistant is unavailable right now. Please try again._",
            });
        } finally {
            _isSending = false;
            _setInputEnabled(true);
            const input = el("chat-input");
            if (input) input.focus();
        }
    }

    // Input enable/disable
    function _setInputEnabled(enabled) {
        const input  = el("chat-input");
        const btn    = el("chat-send-btn");
        if (input) {
            input.disabled = !enabled;
            if (enabled) input.value = "";
        }
        if (btn) btn.disabled = !enabled;
    }

    // Power User toggles
    function _initPowerUser() {
        const puCheck  = el("toggle-power-user");
        const devCheck = el("toggle-dev-mode");
        if (!puCheck) return;

        puCheck.checked  = localStorage.getItem(LS_POWER_USER) === "true";
        if (devCheck) devCheck.checked = localStorage.getItem(LS_DEV_MODE) === "true";

        _applyPowerUser();

        puCheck.addEventListener("change", () => {
            localStorage.setItem(LS_POWER_USER, puCheck.checked ? "true" : "false");
            if (!puCheck.checked && devCheck) {
                devCheck.checked = false;
                localStorage.setItem(LS_DEV_MODE, "false");
            }
            _applyPowerUser();
        });

        if (devCheck) {
            devCheck.addEventListener("change", () => {
                localStorage.setItem(LS_DEV_MODE, devCheck.checked ? "true" : "false");
                _applyDevMode();
            });
        }
    }

    function _applyPowerUser() {
        const puCheck    = el("toggle-power-user");
        const devModeRow = el("dev-mode-row");
        if (!puCheck) return;

        const isOn = puCheck.checked;
        if (devModeRow) devModeRow.classList.toggle("hidden", !isOn);

        _applyDevMode();
    }

    function _applyDevMode() {
        const puCheck  = el("toggle-power-user");
        const devCheck = el("toggle-dev-mode");
        const devPanel = el("dev-panel");
        if (!devPanel) return;

        const showPanel = puCheck && puCheck.checked && devCheck && devCheck.checked;
        devPanel.classList.toggle("hidden", !showPanel);
    }

    // Dev panel clear button
    function _bindDevPanelClear() {
        const btn = el("dev-panel-clear");
        if (!btn) return;
        btn.addEventListener("click", () => {
            const body = el("dev-panel-body");
            if (body) body.textContent = "";
        });
    }

    // Form binding
    function _bindForm() {
        const form  = el("chat-form");
        const input = el("chat-input");
        if (!form || !input) return;

        form.addEventListener("submit", (e) => {
            e.preventDefault();
            const text = input.value.trim();
            if (text) sendMessage(text);
        });

        input.addEventListener("input", () => {
            input.style.height = "auto";
            input.style.height = Math.min(input.scrollHeight, 140) + "px";
        });

        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                const text = input.value.trim();
                if (text && !input.disabled) sendMessage(text);
            }
        });
    }

    // New Chat button
    function _bindNewChat() {
        const btn = el("chat-new-btn");
        if (!btn) return;
        btn.addEventListener("click", createNewSession);
    }

    // Hash change listener
    function _bindHashChange() {
        window.addEventListener("hashchange", () => {
            const id = _getHashSessionId();
            if (id && id !== _activeSessionId) loadSession(id);
        });
    }

    // Rail collapse toggle
    function _initRailCollapse() {
        const rail = el("chat-session-rail");
        const btn  = el("chat-rail-collapse-btn");
        if (!rail || !btn) return;

        // Read persisted state from localStorage
        const isCollapsed = localStorage.getItem(LS_RAIL_COLLAPSED) === "true";
        if (isCollapsed) {
            _applyRailCollapsed(true);
        }

        // Bind toggle click
        btn.addEventListener("click", () => {
            const nowCollapsed = rail.classList.contains("is-collapsed");
            _applyRailCollapsed(!nowCollapsed);
        });

        // Bind keyboard: spacebar/Enter on the toggle button
        btn.addEventListener("keydown", (e) => {
            if (e.key === " " || e.key === "Enter") {
                e.preventDefault();
                btn.click();
            }
        });
    }

    function _applyRailCollapsed(isCollapsed) {
        const rail      = el("chat-session-rail");
        const btn       = el("chat-rail-collapse-btn");
        const layout    = el("chat-app");
        if (!rail || !btn) return;

        // Update rail and layout state
        rail.classList.toggle("is-collapsed", isCollapsed);
        if (layout) layout.classList.toggle("rail-collapsed", isCollapsed);

        // Update ARIA attribute on button
        btn.setAttribute("aria-expanded", isCollapsed ? "false" : "true");

        // Persist to localStorage
        localStorage.setItem(LS_RAIL_COLLAPSED, isCollapsed ? "true" : "false");
    }

    // Entry point
    function init() {
        _bindForm();
        _bindNewChat();
        _initRailCollapse();
        _bindHashChange();
        _bindDevPanelClear();
        _initPowerUser();
        loadSessions();
    }

    return { init };
})();

// Auto-run when DOM is ready
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => ChatPage.init());
} else {
    ChatPage.init();
}

