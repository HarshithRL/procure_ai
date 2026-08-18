// Structured client-side logger with optional server shipping.
// Loaded as a classic <script> before all other app scripts so the global
// `Log` object is available everywhere without imports.
//
// Usage:
//   Log.info("sources", "loaded 12 documents");
//   Log.error("chat", "stream failed", { status: 502 });
//   Log.warn("studio", "graph health degraded");

"use strict";

var Log = (() => {
    const LEVELS = { debug: 0, info: 1, warn: 2, error: 3 };
    const _level = (localStorage.getItem("log_level") || "info").toLowerCase();
    const _threshold = LEVELS[_level] ?? 1;
    const _shipErrors = true; // POST warn/error entries to /api/logs
    const _queue = [];
    let _flushTimer = null;

    function _ts() {
        return new Date().toISOString();
    }

    function _shouldLog(level) {
        return (LEVELS[level] ?? 1) >= _threshold;
    }

    function _emit(level, module, message, extra) {
        if (!_shouldLog(level)) return;

        const entry = { ts: _ts(), level, module, message };
        if (extra !== undefined) entry.extra = extra;

        // Console output (preserves browser dev-tools experience).
        const fn = level === "error" ? console.error
            : level === "warn" ? console.warn
            : level === "debug" ? console.debug
            : console.log;
        const tag = `[${module}]`;
        if (extra !== undefined) {
            fn(tag, message, extra);
        } else {
            fn(tag, message);
        }

        // Ship warn/error to the backend for server-side aggregation.
        if (_shipErrors && LEVELS[level] >= LEVELS.warn) {
            _queue.push(entry);
            _scheduleFlush();
        }
    }

    function _scheduleFlush() {
        if (_flushTimer) return;
        _flushTimer = setTimeout(_flush, 2000);
    }

    function _flush() {
        _flushTimer = null;
        if (_queue.length === 0) return;
        const batch = _queue.splice(0, 20);
        // Fire-and-forget; we intentionally swallow errors to avoid loops.
        try {
            navigator.sendBeacon(
                "/api/logs",
                new Blob([JSON.stringify(batch)], { type: "application/json" })
            );
        } catch (_) { /* swallow */ }
    }

    // Flush remaining entries when the page unloads.
    window.addEventListener("pagehide", _flush);

    return {
        debug: (module, message, extra) => _emit("debug", module, message, extra),
        info:  (module, message, extra) => _emit("info",  module, message, extra),
        warn:  (module, message, extra) => _emit("warn",  module, message, extra),
        error: (module, message, extra) => _emit("error", module, message, extra),
    };
})();
