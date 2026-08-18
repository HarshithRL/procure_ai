// Theme switching: light = Classical, dark = Nocturne, system = OS preference.
// The pre-paint script in base.html applies the stored mode before first render;
// this module keeps the toggle control and live OS changes in sync.

"use strict";

(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");

    function mode() {
        return localStorage.getItem("theme") || "system";
    }

    function apply() {
        const dark = mode() === "dark" || (mode() === "system" && media.matches);
        document.body.classList.toggle("ds-nocturne", dark);
        document.body.classList.toggle("ds-classical", !dark);
        document.dispatchEvent(new CustomEvent("themechange"));
    }

    function initToggle() {
        const toggle = document.getElementById("theme-toggle");
        if (!toggle) return;
        toggle.querySelectorAll('input[name="theme-mode"]').forEach((input) => {
            input.checked = input.value === mode();
            input.addEventListener("change", () => {
                localStorage.setItem("theme", input.value);
                apply();
            });
        });
    }

    media.addEventListener("change", () => {
        if (mode() === "system") apply();
    });

    document.addEventListener("DOMContentLoaded", initToggle);
})();
