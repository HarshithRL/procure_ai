// Sources panel: grouped document list (Requirements vs Vendor proposals),
// grounding checkboxes, uploads, per-document ingestion status polling,
// and tabbed sidebar navigation (Files | Requirements | Vendors | Saved views | History).
// Talks to /api/projects/<id>/documents and /api/projects/<id>/graph.

"use strict";

const SourcesPanel = (() => {
    let projectId = null;
    let pollTimer = null;
    let lastDocuments = [];
    // Grounding selection is UI-side only for now (not yet threaded into the
    // assistant's tool calls).
    const excludedDocumentIds = new Set();

    // Tab state
    let activeTab = "files";
    const tabInitialized = { files: true };
    let graphCache = null;
    let graphFetchPromise = null;

    // Chat history for History tab
    let chatHistory = [];

    // Generated exports (Excel workbooks)
    let exports = [];
    let exportsFetch = null;

    function el(id) {
        return document.getElementById(id);
    }

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str == null ? "" : String(str);
        return div.innerHTML;
    }

    function kindTag(fileType) {
        return (fileType || "").toUpperCase() || "FILE";
    }

    function statusMeta(doc) {
        switch (doc.status) {
            case "pending":
                return "queued for ingestion";
            case "processing":
                return "extracting\u2026";
            case "completed":
                return doc.processed_at ? "in the knowledge graph" : "ready";
            case "failed":
                return doc.error_message || "ingestion failed";
            default:
                return doc.status || "";
        }
    }

    function isRequirementDoc(doc) {
        return /rfq|requirement|brief|tender/i.test(doc.filename || "");
    }

    function updateSelectAllState() {
        const selectAll = el("sources-select-all");
        const count = el("sources-select-count");
        if (!selectAll || !count) return;

        const total = lastDocuments.length;
        const included = total - excludedDocumentIds.size;
        selectAll.checked = total > 0 && included === total;
        selectAll.indeterminate = included > 0 && included < total;
        count.textContent = total === 0
            ? "grounding the assistant"
            : `${included} of ${total} sources grounding the assistant`;
    }

    function rowHtml(doc) {
        const checked = excludedDocumentIds.has(doc.id) ? "" : "checked";
        const failed = doc.status === "failed";
        return `
            <label style="display:flex;gap:9px;align-items:flex-start;padding:6px 12px;cursor:pointer;min-width:0">
                <input type="checkbox" class="app-check source-check" style="margin-top:3px;flex:none" data-doc-id="${doc.id}" ${checked}>
                <span style="min-width:0;flex:1;display:flex;flex-direction:column;gap:2px">
                    <span style="display:flex;align-items:center;gap:6px;min-width:0">
                        <span class="tag ${failed ? "tag-neutral" : "tag-outline"} app-num" style="font-size:9px;padding:0 4px;flex:none">${kindTag(doc.file_type)}</span>
                        <span style="font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0;flex:1" title="${escapeHtml(doc.filename)}">${escapeHtml(doc.filename)}</span>
                    </span>
                    <span class="app-faint app-num" style="display:block;font-size:10px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(statusMeta(doc))}</span>
                </span>
            </label>`;
    }

    function groupHeader(label) {
        return `<div class="app-faint" style="font-size:10px;letter-spacing:.1em;text-transform:uppercase;padding:12px 12px 4px">${label}</div>`;
    }

    function prettyBytes(bytes) {
        if (bytes === 0) return "0 B";
        const k = 1024;
        const sizes = ["B", "KB", "MB", "GB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 10) / 10 + " " + sizes[i];
    }

    function timeAgo(isoString) {
        const date = new Date(isoString);
        const now = new Date();
        const seconds = Math.floor((now - date) / 1000);
        if (seconds < 60) return "just now";
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return minutes + "m ago";
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return hours + "h ago";
        const days = Math.floor(hours / 24);
        return days + "d ago";
    }

    function exportRowHtml(exp) {
        return `
            <button class="gen-file-row" data-export-id="${exp.id}" data-kind="${exp.kind}" data-filename="${escapeHtml(exp.filename)}" style="display:flex;gap:9px;align-items:flex-start;padding:6px 12px;cursor:pointer;border:none;background:none;width:100%;text-align:left;min-width:0">
                <span style="min-width:0;flex:1;display:flex;flex-direction:column;gap:2px">
                    <span style="display:flex;align-items:center;gap:6px;min-width:0">
                        <span class="tag tag-outline app-num" style="font-size:9px;padding:0 4px;flex:none">${kindTag(exp.kind)}</span>
                        <span style="font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0;flex:1" title="${escapeHtml(exp.filename)}">${escapeHtml(exp.filename)}</span>
                    </span>
                    <span class="app-faint app-num" style="display:block;font-size:10px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${prettyBytes(exp.size_bytes)} · ${timeAgo(exp.created_at)}</span>
                </span>
            </button>`;
    }

    async function loadExports() {
        if (exportsFetch) return exportsFetch;
        exportsFetch = (async () => {
            try {
                const data = await Api.get(`/api/projects/${projectId}/exports`);
                exports = Array.isArray(data) ? data : [];
                return exports;
            } catch (err) {
                Log.error("sources", "Failed to load exports", err);
                exports = [];
                return [];
            } finally {
                exportsFetch = null;
            }
        })();
        return exportsFetch;
    }

    function renderDocuments(documents) {
        const list = el("sources-list");
        if (!list) return;
        lastDocuments = documents;

        if (documents.length === 0 && exports.length === 0) {
            list.innerHTML = '<p class="app-faint" style="font-size:11.5px;padding:12px 12px">No documents yet \u2014 add vendor proposals to build the knowledge graph.</p>';
            updateSelectAllState();
            return;
        }

        const reqDocs = documents.filter(isRequirementDoc);
        const vendorDocs = documents.filter((doc) => !isRequirementDoc(doc));

        let html = "";
        if (exports.length > 0) {
            html += groupHeader("Generated files");
            html += exports.map(exportRowHtml).join("");
        }
        if (reqDocs.length > 0) {
            html += groupHeader("Requirements");
            html += reqDocs.map(rowHtml).join("");
        }
        if (documents.length > 0) {
            html += groupHeader(`Vendor proposals \u00b7 ${vendorDocs.length}`);
            html += vendorDocs.map(rowHtml).join("");
        }
        list.innerHTML = html;

        list.querySelectorAll(".source-check").forEach((checkbox) => {
            checkbox.addEventListener("change", () => {
                const docId = Number(checkbox.dataset.docId);
                if (checkbox.checked) {
                    excludedDocumentIds.delete(docId);
                } else {
                    excludedDocumentIds.add(docId);
                }
                updateSelectAllState();
            });
        });

        list.querySelectorAll(".gen-file-row").forEach((btn) => {
            btn.addEventListener("click", () => {
                const exportId = Number(btn.dataset.exportId);
                const kind = btn.dataset.kind;
                const filename = btn.dataset.filename;
                if (window.PreviewPanel && window.PreviewPanel.enterPreview) {
                    window.PreviewPanel.enterPreview({ exportId, kind, filename });
                }
            });
        });

        updateSelectAllState();
    }

    async function fetchDocuments() {
        try {
            const documents = await Api.get(`/api/projects/${projectId}/documents`);
            renderDocuments(documents);
            return documents;
        } catch (err) {
            Log.error("sources", "Failed to load documents", err);
            return null;
        }
    }

    function hasActiveIngestion(documents) {
        return documents.some((doc) => doc.status === "pending" || doc.status === "processing");
    }

    function stopPolling() {
        if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
    }

    function startPolling() {
        stopPolling();
        pollTimer = setInterval(async () => {
            const documents = await fetchDocuments();
            if (documents && !hasActiveIngestion(documents)) {
                stopPolling();
                document.dispatchEvent(new CustomEvent("sources:updated", { detail: documents }));
            }
        }, 3000);
    }

    async function uploadFile(file) {
        const formData = new FormData();
        formData.append("file", file);

        const uploadStatus = el("upload-status");
        if (uploadStatus) uploadStatus.textContent = `Uploading ${file.name}\u2026`;

        try {
            const response = await Api.raw(`/api/projects/${projectId}/documents`, {
                method: "POST",
                body: formData,
            });
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || "Upload failed");
            }
            if (uploadStatus) uploadStatus.textContent = "";
            await fetchDocuments();
            startPolling();
        } catch (err) {
            if (uploadStatus) uploadStatus.textContent = err.message;
            Log.error("sources", "Upload failed", err);
        }
    }

    function bindUpload() {
        const input = el("upload-input");
        const addBtn = el("sources-add-btn");
        if (addBtn && input) {
            addBtn.addEventListener("click", () => input.click());
            input.addEventListener("change", (event) => {
                Array.from(event.target.files || []).forEach(uploadFile);
                input.value = "";
            });
        }
    }

    function bindSelectAll() {
        const selectAll = el("sources-select-all");
        if (!selectAll) return;
        selectAll.addEventListener("change", () => {
            excludedDocumentIds.clear();
            if (!selectAll.checked) {
                lastDocuments.forEach((doc) => excludedDocumentIds.add(doc.id));
            }
            renderDocuments(lastDocuments);
        });
    }

    function getIncludedDocumentIds() {
        return lastDocuments.map((doc) => doc.id).filter((id) => !excludedDocumentIds.has(id));
    }

    // ---- Tab controller --------------------------------------------------------

    function switchTab(tabName) {
        activeTab = tabName;

        // Update nav button active states
        document.querySelectorAll("#sidebar-nav .sidebar-nav-btn").forEach((btn) => {
            btn.classList.toggle("is-active", btn.dataset.tab === tabName);
        });

        // Show/hide panes
        document.querySelectorAll(".sidebar-pane").forEach((pane) => {
            pane.classList.toggle("is-active", pane.id === `sidebar-pane-${tabName}`);
        });

        // Lazy-init tabs on first activation
        if (!tabInitialized[tabName]) {
            tabInitialized[tabName] = true;
            if (tabName === "reqs") loadRequirementsTab();
            else if (tabName === "vendors") loadVendorsTab();
            else if (tabName === "saved") renderSavedTab();
            else if (tabName === "history") renderHistoryTab();
        }
    }

    function bindNavButtons() {
        document.querySelectorAll("#sidebar-nav .sidebar-nav-btn").forEach((btn) => {
            btn.addEventListener("click", () => switchTab(btn.dataset.tab));
        });
    }

    // ---- Graph API helper (shared + cached) ------------------------------------

    async function fetchGraph() {
        if (graphCache) return graphCache;
        if (graphFetchPromise) return graphFetchPromise;

        graphFetchPromise = (async () => {
            try {
                const data = await Api.get(`/api/projects/${projectId}/graph`);
                graphCache = data;
                return data;
            } catch (err) {
                Log.error("sources", "Failed to load graph", err);
                graphFetchPromise = null;
                return null;
            }
        })();

        return graphFetchPromise;
    }

    function invalidateGraphCache() {
        graphCache = null;
        graphFetchPromise = null;
    }

    // ---- Requirements tab ------------------------------------------------------

    async function loadRequirementsTab() {
        const content = el("reqs-content");
        if (!content) return;

        content.innerHTML = '<p class="app-faint" style="font-size:11.5px;padding:12px">Loading requirements\u2026</p>';

        const graph = await fetchGraph();
        if (!graph || !graph.nodes) {
            content.innerHTML = '<p class="app-faint" style="font-size:11.5px;padding:12px">Ingest documents with requirement specifications to see structured requirements.</p>';
            return;
        }

        const reqNodes = graph.nodes.filter((n) => n.type === "requirement");

        if (reqNodes.length === 0) {
            content.innerHTML = '<p class="app-faint" style="font-size:11.5px;padding:12px">No requirements extracted yet. Upload an RFQ or brief document to populate requirements.</p>';
            return;
        }

        let html = "";
        reqNodes.forEach((node) => {
            const attrs = node.attributes || {};
            const status = (attrs.coverage || attrs.status || "").toLowerCase();
            let icon, iconClass;
            if (status === "met" || status === "satisfied") {
                icon = "\u2713";
                iconClass = "req-met";
            } else if (status === "partial" || status === "pending") {
                icon = "\u26A0";
                iconClass = "req-partial";
            } else if (status === "unmet" || status === "not_met" || status === "gap") {
                icon = "\u2717";
                iconClass = "req-unmet";
            } else {
                icon = "\u2022";
                iconClass = "app-muted";
            }
            html += `
                <div class="sidebar-row">
                    <span class="sidebar-row-icon ${iconClass}">${icon}</span>
                    <span class="sidebar-row-label" title="${escapeHtml(node.name)}">${escapeHtml(node.name)}</span>
                </div>`;
        });

        content.innerHTML = html;
    }

    // ---- Vendors tab -----------------------------------------------------------

    async function loadVendorsTab() {
        const content = el("vendors-content");
        if (!content) return;

        content.innerHTML = '<p class="app-faint" style="font-size:11.5px;padding:12px">Loading vendors\u2026</p>';

        const graph = await fetchGraph();
        if (!graph || !graph.nodes) {
            content.innerHTML = '<p class="app-faint" style="font-size:11.5px;padding:12px">Upload vendor proposals to extract vendor information.</p>';
            return;
        }

        const vendorNodes = graph.nodes.filter((n) => n.type === "vendor");
        const edges = graph.edges || [];

        if (vendorNodes.length === 0) {
            content.innerHTML = '<p class="app-faint" style="font-size:11.5px;padding:12px">No vendors identified yet.</p>';
            return;
        }

        // Build a set of vendor IDs that have PRICE_QUOTE children via "quotes" edge
        const quotedVendorIds = new Set();
        edges.forEach((edge) => {
            if (edge.relation === "quotes") {
                quotedVendorIds.add(edge.source_id);
            }
        });

        let html = "";
        vendorNodes.forEach((node) => {
            const isPriced = quotedVendorIds.has(node.id);
            const badgeClass = isPriced ? "badge-priced" : "badge-tbc";
            const badgeText = isPriced ? "priced" : "TBC";
            html += `
                <div class="sidebar-row">
                    <span class="sidebar-row-label" title="${escapeHtml(node.name)}">${escapeHtml(node.name)}</span>
                    <span class="sidebar-row-meta"><span class="${badgeClass}">${badgeText}</span></span>
                </div>`;
        });

        content.innerHTML = html;
    }

    // ---- Saved views tab (static placeholder) -----------------------------------

    function renderSavedTab() {
        const content = el("saved-content");
        if (!content) return;

        content.innerHTML = `
            <div class="sidebar-row saved-star">
                <span class="sidebar-row-icon">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                </span>
                <span class="sidebar-row-label">3-year TCO ranking</span>
            </div>
            <div class="sidebar-row saved-star">
                <span class="sidebar-row-icon">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                </span>
                <span class="sidebar-row-label">Mandatory compliance</span>
            </div>
            <div class="sidebar-row saved-star">
                <span class="sidebar-row-icon">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
                </span>
                <span class="sidebar-row-label">Price comparison by SKU</span>
            </div>
            <p class="app-faint" style="font-size:10.5px;padding:12px;margin:0">Save views to bookmark your most-used analysis queries.</p>`;
    }

    // ---- History tab -----------------------------------------------------------

    function renderHistoryTab() {
        const content = el("history-content");
        if (!content) return;

        if (chatHistory.length === 0) {
            content.innerHTML = '<p class="app-faint" style="font-size:11.5px;padding:12px">No questions asked yet. Start a conversation in the chat panel.</p>';
            return;
        }

        const items = chatHistory.slice().reverse();
        let html = "";
        items.forEach((text) => {
            html += `
                <div class="sidebar-row-click" data-question="${escapeHtml(text)}">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" style="flex:none;opacity:.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                    <span class="sidebar-row-label">${escapeHtml(text)}</span>
                </div>`;
        });

        content.innerHTML = html;

        // Bind click to replay question in chat input
        content.querySelectorAll("[data-question]").forEach((row) => {
            row.addEventListener("click", () => {
                const question = row.dataset.question;
                const input = document.getElementById("chat-input");
                const form = document.getElementById("chat-form");
                if (input) {
                    input.value = question;
                    input.focus();
                }
                if (form) {
                    form.dispatchEvent(new Event("submit", { cancelable: true }));
                }
            });
        });
    }

    function addToHistory(text) {
        if (!text || chatHistory.includes(text)) return;
        chatHistory.push(text);
        // Only re-render if the history tab is active
        if (activeTab === "history") {
            renderHistoryTab();
        }
    }

    // ---- Chat event listener ---------------------------------------------------

    function bindChatEvents() {
        document.addEventListener("chat:sent", (event) => {
            if (event.detail && event.detail.text) {
                addToHistory(event.detail.text);
            }
        });
    }

    // ---- Init ------------------------------------------------------------------

    async function init(id) {
        projectId = id;
        bindUpload();
        bindSelectAll();
        bindNavButtons();
        bindChatEvents();
        // Initialize Files tab content (legacy behavior)
        const documents = await fetchDocuments();
        await loadExports();
        if (documents && hasActiveIngestion(documents)) {
            startPolling();
        }
        // Pre-render saved views statically
        renderSavedTab();
        tabInitialized.saved = true;
    }

    async function refreshExports() {
        exportsFetch = null;
        await loadExports();
        renderDocuments(lastDocuments);
    }

    // Public API for other panels
    document.addEventListener("sources:updated", () => {
        // Invalidate graph cache so Requirements/Vendors tabs re-fetch on next view
        invalidateGraphCache();
    });

    return { init, getIncludedDocumentIds, refreshExports };
})();