// Draggable panel manager — makes .draggable-panel movable via .draggable-header
// Persists position to localStorage per element id

"use strict";

const DraggablePanel = (() => {
    const STATE_KEY = "draggable-positions";

    function loadPositions() {
        try {
            const stored = localStorage.getItem(STATE_KEY);
            return stored ? JSON.parse(stored) : {};
        } catch {
            return {};
        }
    }

    function savePositions(positions) {
        try {
            localStorage.setItem(STATE_KEY, JSON.stringify(positions));
        } catch (err) {
            console.warn("Failed to save draggable positions", err);
        }
    }

    function restorePosition(panel) {
        if (!panel.id) return;
        const positions = loadPositions();
        const saved = positions[panel.id];
        if (saved) {
            const rect = panel.getBoundingClientRect();
            const newX = saved.left;
            const newY = saved.top;
            panel.style.left = `${newX}px`;
            panel.style.top = `${newY}px`;
            panel.style.transform = "none"; // Override centered transform
        }
    }

    function init(panel) {
        if (!panel.classList.contains("draggable-panel")) return;
        
        const header = panel.querySelector(".draggable-header");
        const closeBtn = panel.querySelector("[id$='-close']");
        if (!header) return;

        let isDragging = false;
        let startX = 0;
        let startY = 0;
        let startLeft = 0;
        let startTop = 0;
        let hasMovedOnce = false;

        // Set initial grab cursor
        header.style.cursor = "grab";

        header.addEventListener("mousedown", (e) => {
            // Don't drag if clicking the close button or its contents
            if (closeBtn && (closeBtn === e.target || closeBtn.contains(e.target))) return;
            
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            
            const rect = panel.getBoundingClientRect();
            startLeft = rect.left;
            startTop = rect.top;
            
            header.style.cursor = "grabbing";
            
            // Remove centered transform on first drag
            if (!hasMovedOnce) {
                panel.style.transform = "none";
                panel.style.left = `${startLeft}px`;
                panel.style.top = `${startTop}px`;
                hasMovedOnce = true;
            }
            
            e.preventDefault();
        });

        const handleMouseMove = (e) => {
            if (!isDragging) return;
            
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            
            const newX = startLeft + dx;
            const newY = Math.max(0, startTop + dy); // Prevent moving off-screen top
            
            panel.style.left = `${newX}px`;
            panel.style.top = `${newY}px`;
        };

        const handleMouseUp = () => {
            if (!isDragging) return;
            isDragging = false;
            header.style.cursor = "grab";
            
            // Save position
            if (panel.id) {
                const rect = panel.getBoundingClientRect();
                const positions = loadPositions();
                positions[panel.id] = {
                    left: rect.left,
                    top: rect.top,
                };
                savePositions(positions);
            }
        };

        document.addEventListener("mousemove", handleMouseMove);
        document.addEventListener("mouseup", handleMouseUp);

        // Close button handler
        if (closeBtn) {
            closeBtn.addEventListener("click", () => {
                panel.classList.add("hidden");
            });
        }

        // Restore saved position on init
        restorePosition(panel);
    }

    return { init };
})();
