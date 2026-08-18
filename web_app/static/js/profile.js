// Profile page: identity + progressive Databricks asset sections.

"use strict";

(() => {
    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str == null ? "" : String(str);
        return div.innerHTML;
    }

    function initials(user) {
        if (user.display_name) {
            return user.display_name.split(/\s+/).map((s) => s[0]).join("").toUpperCase().slice(0, 2);
        }
        return (user.user_name || "?").slice(0, 2).toUpperCase();
    }

    function stateTag(state) {
        if (!state) return '<span class="tag tag-neutral">—</span>';
        const s = String(state).toUpperCase();
        const running = ["RUNNING", "ONLINE", "READY", "DEPLOYING"].includes(s);
        const cls = running ? "tag-accent" : "tag-neutral";
        return `<span class="tag ${cls}">${escapeHtml(state)}</span>`;
    }

    function assetRow(name, sub, state) {
        return `<div class="profile-asset-row">
            <div style="min-width:0;flex:1">
                <div style="font-size:12.5px;font-weight:500">${escapeHtml(name || "—")}</div>
                ${sub ? `<div class="app-faint" style="font-size:11px;margin-top:2px">${escapeHtml(sub)}</div>` : ""}
            </div>
            ${state !== undefined ? stateTag(state) : ""}
        </div>`;
    }

    function metaRow(label, value) {
        return `<div><span class="app-faint" style="display:inline-block;width:110px">${escapeHtml(label)}</span>${escapeHtml(value || "—")}</div>`;
    }

    async function loadIdentity() {
        const user = await Api.get("/api/auth/profile");
        const avatar = document.getElementById("profile-avatar");
        const nameEl = document.getElementById("profile-name");
        const emailEl = document.getElementById("profile-email");
        const activeEl = document.getElementById("profile-active");
        const metaEl = document.getElementById("profile-meta");
        const groupsEl = document.getElementById("profile-groups");

        if (avatar) avatar.textContent = initials(user);
        if (nameEl) nameEl.textContent = user.display_name || user.user_name || "User";
        if (emailEl) emailEl.textContent = user.email || user.user_name || "";
        if (activeEl) {
            activeEl.classList.toggle("hidden", !user.active);
            activeEl.textContent = user.active ? "Active" : "Inactive";
            activeEl.className = user.active ? "tag tag-accent" : "tag tag-neutral";
        }
        if (metaEl) {
            metaEl.innerHTML = [
                metaRow("User name", user.user_name),
                metaRow("Email", user.email),
                metaRow("User id", user.id),
                metaRow("Given name", user.given_name),
                metaRow("Family name", user.family_name),
            ].join("");
        }
        if (groupsEl) {
            const pills = [];
            (user.groups || []).forEach((g) => pills.push(`<span class="tag tag-outline">${escapeHtml(g)}</span>`));
            (user.entitlements || []).forEach((e) => pills.push(`<span class="tag tag-neutral">${escapeHtml(e)}</span>`));
            groupsEl.innerHTML = pills.length ? pills.join("") : '<span class="app-faint" style="font-size:12px">No groups or entitlements listed.</span>';
        }
        return user;
    }

    function sectionEls(section) {
        const root = document.querySelector(`.profile-section[data-section="${section}"]`);
        if (!root) return {};
        return {
            root,
            body: root.querySelector(".profile-body"),
            count: root.querySelector(".profile-count"),
        };
    }

    function renderError(section, message) {
        const { body, count } = sectionEls(section);
        if (count) count.textContent = "";
        if (body) {
            body.innerHTML = `<div style="display:flex;align-items:center;justify-content:space-between;gap:10px">
                <span class="app-muted">${escapeHtml(message)}</span>
                <button type="button" class="btn btn-secondary profile-retry" data-section="${section}" style="font-size:11px">Retry</button>
            </div>`;
            body.querySelector(".profile-retry")?.addEventListener("click", () => loadSection(section));
        }
    }

    function renderCompute(data) {
        const { body, count } = sectionEls("compute");
        const warehouses = data.warehouses || [];
        const clusters = data.clusters || [];
        if (count) count.textContent = `${warehouses.length + clusters.length}`;
        if (!body) return;
        if (!warehouses.length && !clusters.length) {
            body.innerHTML = '<p class="app-faint" style="margin:0">No warehouses or running clusters.</p>';
            return;
        }
        const rows = [];
        warehouses.forEach((w) => rows.push(assetRow(w.name, w.cluster_size || w.warehouse_type, w.state)));
        clusters.forEach((c) => rows.push(assetRow(c.cluster_name, c.spark_version, c.state)));
        body.innerHTML = rows.join("");
    }

    function renderAi(data) {
        const { body, count } = sectionEls("ai");
        const serving = data.serving_endpoints || [];
        const vector = data.vector_search_endpoints || [];
        if (count) count.textContent = `${serving.length + vector.length}`;
        if (!body) return;
        if (!serving.length && !vector.length) {
            body.innerHTML = '<p class="app-faint" style="margin:0">No serving or vector search endpoints.</p>';
            return;
        }
        const rows = [];
        serving.forEach((e) => rows.push(assetRow(e.name, "Model serving", e.ready || e.config_update)));
        vector.forEach((e) => rows.push(assetRow(e.name, e.endpoint_type || "Vector Search", e.state)));
        body.innerHTML = rows.join("");
    }

    function renderData(data) {
        const { body, count } = sectionEls("data");
        const catalogs = data.catalogs || [];
        if (count) count.textContent = `${catalogs.length}`;
        if (!body) return;
        if (!catalogs.length) {
            body.innerHTML = '<p class="app-faint" style="margin:0">No catalogs visible.</p>';
            return;
        }
        body.innerHTML = catalogs.map((c) => assetRow(c.name, c.owner ? `owned by ${c.owner}` : c.catalog_type, null)).join("");
    }

    function renderApps(data) {
        const { body, count } = sectionEls("apps");
        const apps = data.apps || [];
        if (count) count.textContent = `${apps.length}`;
        if (!body) return;
        if (!apps.length) {
            body.innerHTML = '<p class="app-faint" style="margin:0">No Databricks Apps.</p>';
            return;
        }
        body.innerHTML = apps.map((a) => assetRow(a.name, a.description, a.state)).join("");
    }

    async function loadSection(section) {
        const { body } = sectionEls(section);
        if (body) body.innerHTML = '<span class="app-faint">Loading…</span>';
        try {
            const data = await Api.get(`/api/profile/assets/${section}`);
            if (section === "compute") renderCompute(data);
            else if (section === "ai") renderAi(data);
            else if (section === "data") renderData(data);
            else if (section === "apps") renderApps(data);
        } catch (err) {
            renderError(section, err.message || "Failed to load");
            Log.error("profile", `assets ${section} failed`, err);
        }
    }

    function refreshAll() {
        ["compute", "ai", "data", "apps"].forEach(loadSection);
    }

    document.addEventListener("DOMContentLoaded", async () => {
        try {
            await loadIdentity();
        } catch (err) {
            Log.error("profile", "identity failed", err);
            return;
        }
        refreshAll();
        document.getElementById("profile-refresh")?.addEventListener("click", refreshAll);
    });
})();
