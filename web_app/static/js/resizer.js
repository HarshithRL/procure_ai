// resizer.js — Drag-to-resize panel splitters for the 3-column workspace.
// Sources (left) | Chat (center, elastic) | Studio (right)
//
// Left handle:  drag right → Sources wider  · double-click → collapse/expand
// Right handle: drag left  → Studio wider   · double-click → reset to default
//
// Widths persisted to localStorage. CSS custom properties (--panel-sources-w,
// --panel-studio-w) are kept in sync so the Evidence overlay and any other
// CSS consumers update automatically.

"use strict";

const PanelResizer = (() => {
    const DEFAULTS   = { sources: 268, studio: 452 };
    const COLLAPSED  = 48;
    const LIMITS     = {
        sources: { min: 180, max: 400 },
        studio:  { min: 280, max: 600 },
    };
    const STORAGE_KEY = 'procura-panel-widths';

    let rowEl    = null;
    let panelEls = {};   // sources, chat, studio
    let widths   = { ...DEFAULTS };
    let sourcesPreviousWidth = DEFAULTS.sources;  // restored on un-collapse

    // ── Persistence ──────────────────────────────────────────────────────────

    function load() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            if (!raw) return { ...DEFAULTS };
            const parsed = JSON.parse(raw);
            return {
                sources: clamp(parsed.sources, LIMITS.sources.min, LIMITS.sources.max) || DEFAULTS.sources,
                studio:  clamp(parsed.studio,  LIMITS.studio.min,  LIMITS.studio.max)  || DEFAULTS.studio,
            };
        } catch (_) {
            return { ...DEFAULTS };
        }
    }

    function save() {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(widths));
        } catch (_) { /* quota exceeded or private browsing — silently ignore */ }
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    function clamp(val, min, max) {
        const n = Number(val);
        if (!isFinite(n)) return min;
        return Math.min(max, Math.max(min, n));
    }

    // ── DOM apply ─────────────────────────────────────────────────────────────

    function apply() {
        const sw = widths.sources;
        const dw = widths.studio;

        panelEls.sources.style.flexBasis = sw + 'px';
        panelEls.sources.style.width     = sw + 'px';
        panelEls.studio.style.flexBasis  = dw + 'px';
        panelEls.studio.style.width      = dw + 'px';

        // CSS custom properties — consumed by Evidence overlay + CSS selectors
        document.documentElement.style.setProperty('--panel-sources-w', sw + 'px');
        document.documentElement.style.setProperty('--panel-studio-w',  dw + 'px');
    }

    // ── Drag ──────────────────────────────────────────────────────────────────

    function startDrag(e, resizerId, panel, getNewWidth) {
        if (e.button !== 0) return;
        e.preventDefault();

        const resizerEl = document.getElementById(resizerId);
        resizerEl.classList.add('is-dragging');
        rowEl.classList.add('is-resizing');

        const startX     = e.clientX;
        const startWidth = widths[panel];
        const limits     = LIMITS[panel];

        function onMove(ev) {
            const newWidth = clamp(getNewWidth(ev.clientX, startX, startWidth), limits.min, limits.max);
            widths[panel] = newWidth;
            // If Sources was collapsed, un-collapse it when dragged open
            if (panel === 'sources' && panelEls.sources.classList.contains('is-collapsed')) {
                panelEls.sources.classList.remove('is-collapsed');
            }
            apply();
        }

        function onUp() {
            resizerEl.classList.remove('is-dragging');
            rowEl.classList.remove('is-resizing');
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mouseup',   onUp);
            save();
        }

        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup',   onUp);
    }

    // Touch version — delegates to startDrag logic via synthetic coords
    function startTouchDrag(e, resizerId, panel, getNewWidth) {
        if (e.touches.length !== 1) return;
        e.preventDefault();

        const resizerEl = document.getElementById(resizerId);
        resizerEl.classList.add('is-dragging');
        rowEl.classList.add('is-resizing');

        const startX     = e.touches[0].clientX;
        const startWidth = widths[panel];
        const limits     = LIMITS[panel];

        function onMove(ev) {
            if (!ev.touches.length) return;
            const newWidth = clamp(getNewWidth(ev.touches[0].clientX, startX, startWidth), limits.min, limits.max);
            widths[panel] = newWidth;
            if (panel === 'sources' && panelEls.sources.classList.contains('is-collapsed')) {
                panelEls.sources.classList.remove('is-collapsed');
            }
            apply();
        }

        function onEnd() {
            resizerEl.classList.remove('is-dragging');
            rowEl.classList.remove('is-resizing');
            document.removeEventListener('touchmove', onMove);
            document.removeEventListener('touchend',  onEnd);
            save();
        }

        document.addEventListener('touchmove', onMove, { passive: false });
        document.addEventListener('touchend',  onEnd);
    }

    // ── Width calculators ─────────────────────────────────────────────────────

    // Left handle: drag right → sources wider (delta is positive)
    const leftWidth  = (x, sx, sw) => sw + (x - sx);

    // Right handle: drag left → studio wider (delta is negative = positive width gain)
    const rightWidth = (x, sx, sw) => sw + (sx - x);

    // ── Collapse / expand (Sources only) ──────────────────────────────────────

    function toggleCollapse() {
        const col = panelEls.sources;
        if (col.classList.contains('is-collapsed')) {
            // Expand — restore previous width
            widths.sources = sourcesPreviousWidth;
            col.classList.remove('is-collapsed');
        } else {
            // Collapse — save current width, snap to strip
            sourcesPreviousWidth = widths.sources;
            widths.sources = COLLAPSED;
            col.classList.add('is-collapsed');
        }
        apply();
        save();
    }

    // Reset Studio to default
    function resetStudio() {
        widths.studio = DEFAULTS.studio;
        apply();
        save();
    }

    // ── Init ─────────────────────────────────────────────────────────────────

    function init() {
        rowEl = document.getElementById('panel-row');
        if (!rowEl) return;

        panelEls.sources = document.getElementById('panel-sources');
        panelEls.chat    = document.getElementById('panel-chat');
        panelEls.studio  = document.getElementById('panel-studio');

        if (!panelEls.sources || !panelEls.chat || !panelEls.studio) return;

        widths = load();
        apply();

        const rLeft  = document.getElementById('resizer-left');
        const rRight = document.getElementById('resizer-right');

        // Mouse drag
        rLeft.addEventListener('mousedown',  e => startDrag(e, 'resizer-left',  'sources', leftWidth));
        rRight.addEventListener('mousedown', e => startDrag(e, 'resizer-right', 'studio',  rightWidth));

        // Touch drag
        rLeft.addEventListener('touchstart',  e => startTouchDrag(e, 'resizer-left',  'sources', leftWidth),  { passive: false });
        rRight.addEventListener('touchstart', e => startTouchDrag(e, 'resizer-right', 'studio',  rightWidth), { passive: false });

        // Double-click actions
        rLeft.addEventListener('dblclick',  toggleCollapse);
        rRight.addEventListener('dblclick', resetStudio);
    }

    return { init };
})();
