/**
 * Sidebar collapse controller.
 * Manages the collapsible primary sidebar (.sidebar in .app-shell).
 *
 * - Reads localStorage["procure_ai_sidebar_collapsed"] on page load
 * - Applies .is-collapsed class to #app-sidebar
 * - Binds toggle button (#sidebar-toggle) to collapse/expand
 * - Supports keyboard access (Space/Enter)
 * - Persists state on toggle
 */

"use strict";

const SidebarCollapse = (() => {
    const STORAGE_KEY = "procure_ai_sidebar_collapsed";
    const SIDEBAR_ID = "app-sidebar";
    const TOGGLE_ID = "sidebar-toggle";

    /**
     * Initialize sidebar collapse on page load.
     * Reads localStorage, applies class, and binds event listeners.
     */
    function init() {
        const sidebar = document.getElementById(SIDEBAR_ID);
        const toggle = document.getElementById(TOGGLE_ID);

        if (!sidebar || !toggle) {
            console.warn("SidebarCollapse: sidebar or toggle button not found");
            return;
        }

        // Read stored state; default to false (expanded)
        const isCollapsed = localStorage.getItem(STORAGE_KEY) === "true";

        // Apply initial class
        if (isCollapsed) {
            sidebar.classList.add("is-collapsed");
            toggle.setAttribute("aria-expanded", "false");
        }

        // Bind toggle button
        toggle.addEventListener("click", () => {
            toggleCollapse(sidebar, toggle);
        });

        // Keyboard support: Space or Enter to toggle
        toggle.addEventListener("keydown", (e) => {
            if (e.code === "Space" || e.code === "Enter") {
                e.preventDefault();
                toggleCollapse(sidebar, toggle);
            }
        });
    }

    /**
     * Toggle sidebar between expanded and collapsed states.
     * @param {Element} sidebar The <aside class="sidebar"> element
     * @param {Element} toggle The toggle button element
     */
    function toggleCollapse(sidebar, toggle) {
        const isCurrentlyCollapsed = sidebar.classList.contains("is-collapsed");
        const newCollapsedState = !isCurrentlyCollapsed;

        // Update class
        sidebar.classList.toggle("is-collapsed", newCollapsedState);

        // Update aria-expanded for accessibility
        toggle.setAttribute("aria-expanded", !newCollapsedState);

        // Persist to localStorage
        localStorage.setItem(STORAGE_KEY, newCollapsedState.toString());
    }

    return {
        init,
    };
})();

// Auto-initialize on DOM ready
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", SidebarCollapse.init);
} else {
    SidebarCollapse.init();
}
