// Workspace bootstrap: reads the project id from the DOM, loads the project
// header (name + code), and wires up the three panels plus the evidence
// overlay. Home and new-project pages have their own modules
// (home.js / new_project.js).

"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const workspace = document.querySelector(".workspace");
    if (!workspace) return;

    const projectId = workspace.dataset.projectId;

    Api.get(`/api/projects/${projectId}`)
        .then((project) => {
            if (!project) return;
            const nameEl = document.getElementById("ws-project-name");
            if (nameEl) nameEl.textContent = project.name;
            const codeEl = document.getElementById("ws-project-code");
            if (codeEl && project.code) {
                codeEl.textContent = project.code;
                codeEl.classList.remove("hidden");
            }
            document.title = `${project.name} — Procura AI`;
        })
        .catch((err) => Log.error("app", "Failed to load project", err));

    if (typeof PanelResizer !== "undefined") PanelResizer.init();
    if (typeof EvidencePanel !== "undefined") EvidencePanel.init();
    if (typeof PreviewPanel !== "undefined") PreviewPanel.init();
    if (typeof SourcesPanel !== "undefined") SourcesPanel.init(projectId);
    if (typeof ChatPanel !== "undefined") ChatPanel.init(projectId);
    if (typeof StudioPanel !== "undefined") StudioPanel.init(projectId);
});
