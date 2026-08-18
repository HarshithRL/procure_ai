// Thin fetch wrapper used by all panels. Provides:
//  - automatic JSON parsing
//  - structured error logging via Log
//  - central 401 → Databricks login redirect
//
// Usage:
//   const data = await Api.get(`/api/projects/${id}`);
//   const result = await Api.post(`/api/projects/${id}/chat`, { message });

"use strict";

var Api = (() => {
    function _redirectToLogin() {
        const next = encodeURIComponent(window.location.pathname + window.location.search);
        window.location.href = `/login?next=${next}`;
    }

    async function _request(method, url, body) {
        const opts = { method, credentials: "same-origin" };
        if (body !== undefined) {
            opts.headers = { "Content-Type": "application/json" };
            opts.body = JSON.stringify(body);
        }
        const response = await fetch(url, opts);
        if (response.status === 401) {
            _redirectToLogin();
            throw new Error("Not authenticated");
        }
        // Return raw response for non-JSON endpoints (binary downloads, SSE).
        const ct = response.headers.get("content-type") || "";
        if (!ct.includes("application/json")) return response;
        const data = await response.json();
        if (!response.ok) {
            const msg = data.error || `${method} ${url} failed (${response.status})`;
            Log.error("api", msg, { status: response.status, url });
            throw new Error(msg);
        }
        return data;
    }

    async function raw(url, opts) {
        const response = await fetch(url, { credentials: "same-origin", ...(opts || {}) });
        if (response.status === 401) {
            _redirectToLogin();
            throw new Error("Not authenticated");
        }
        return response;
    }

    return {
        get:    (url)       => _request("GET", url),
        post:   (url, body) => _request("POST", url, body),
        put:    (url, body) => _request("PUT", url, body),
        delete: (url)       => _request("DELETE", url),
        // Raw fetch with credentials + 401 handling (FormData uploads / SSE).
        raw,
        redirectToLogin: _redirectToLogin,
    };
})();
