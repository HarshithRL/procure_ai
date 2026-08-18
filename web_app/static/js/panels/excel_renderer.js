// excel_renderer.js — Excel workbook preview with edge case handling
// Handles: wide tables, many tabs, empty sheets, large files, embedded charts

"use strict";

const ExcelRenderer = (() => {
    let currentWorkbook = null;
    let currentSheetName = null;

    function escapeHtml(str) {
        const div = document.createElement("div");
        div.textContent = str == null ? "" : String(str);
        return div.innerHTML;
    }

    function renderSpinner() {
        return `
            <div class="preview-spinner">
                <div class="preview-spinner-dot"></div>
                <div class="preview-spinner-dot"></div>
                <div class="preview-spinner-dot"></div>
                <span style="font-size:12px;color:var(--color-text)">Loading workbook…</span>
            </div>
        `;
    }

    function renderEmpty() {
        return `
            <div class="preview-empty">
                <div>
                    <div class="preview-empty-icon">📄</div>
                    <div class="preview-empty-text">Sheet is empty</div>
                    <div class="preview-empty-hint">No data to display</div>
                </div>
            </div>
        `;
    }

    function renderChartBanner() {
        return `
            <div class="preview-chart-banner">
                Charts not rendered — download the file to view charts.
            </div>
        `;
    }

    function renderSheet(bodyEl, wb, sheetName) {
        if (!bodyEl || !wb || !sheetName) {
            console.error("ExcelRenderer.renderSheet: missing arguments");
            return;
        }

        const ws = wb.Sheets[sheetName];
        if (!ws) {
            bodyEl.innerHTML = renderEmpty();
            return;
        }

        // Detect embedded charts (SheetJS stores them in ws['!charts'])
        const hasCharts = ws["!charts"] && ws["!charts"].length > 0;

        // Convert sheet to HTML table
        const range = XLSX.utils.decode_range(ws["!ref"] || "A1");
        const rows = [];

        // Build table rows
        for (let R = range.s.r; R <= range.e.r; R++) {
            const cells = [];
            for (let C = range.s.c; C <= range.e.c; C++) {
                const cellAddress = XLSX.utils.encode_cell({ r: R, c: C });
                const cell = ws[cellAddress];
                const value = cell ? (cell.v !== undefined ? cell.v : "") : "";
                cells.push(escapeHtml(String(value)));
            }
            rows.push(cells);
        }

        // Check if sheet is empty
        if (rows.length === 0 || rows.every(r => r.every(c => c === ""))) {
            bodyEl.innerHTML = renderEmpty();
            return;
        }

        // Build HTML table
        let html = "";
        if (hasCharts) {
            html += renderChartBanner();
        }

        html += '<table><thead><tr>';
        // First row as header
        if (rows.length > 0) {
            rows[0].forEach(cell => {
                html += `<th>${cell}</th>`;
            });
        }
        html += '</tr></thead><tbody>';

        // Data rows
        for (let i = 1; i < rows.length; i++) {
            html += '<tr>';
            rows[i].forEach(cell => {
                html += `<td>${cell}</td>`;
            });
            html += '</tr>';
        }

        html += '</tbody></table>';
        bodyEl.innerHTML = html;
    }

    function renderTabs(containerEl, wb) {
        if (!containerEl || !wb) return;

        const sheetNames = wb.SheetNames || [];
        let html = '';

        sheetNames.forEach((name, idx) => {
            const isActive = idx === 0 ? 'is-active' : '';
            html += `<button class="preview-tab ${isActive}" data-sheet="${escapeHtml(name)}" title="${escapeHtml(name)}">${escapeHtml(name)}</button>`;
        });

        containerEl.innerHTML = html;

        // Attach click handlers
        containerEl.querySelectorAll('.preview-tab').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const sheetName = e.target.getAttribute('data-sheet');
                if (sheetName) {
                    switchSheet(sheetName);
                }
            });
        });

        // Auto-scroll active tab into view
        const activeTab = containerEl.querySelector('.preview-tab.is-active');
        if (activeTab) {
            activeTab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'nearest' });
        }
    }

    function switchSheet(sheetName) {
        if (!currentWorkbook || !sheetName) return;

        currentSheetName = sheetName;

        // Update active tab
        document.querySelectorAll('.preview-tab').forEach(btn => {
            btn.classList.toggle('is-active', btn.getAttribute('data-sheet') === sheetName);
        });

        // Render sheet
        const bodyEl = document.getElementById('preview-body');
        if (bodyEl) {
            renderSheet(bodyEl, currentWorkbook, sheetName);
        }
    }

    function mount(context) {
        if (!context || !context.exportId) {
            console.error("ExcelRenderer.mount: missing context");
            return;
        }

        const panelSources = document.getElementById('panel-sources');
        if (!panelSources) return;

        // Show loading spinner
        const container = panelSources.querySelector('#preview-container');
        if (container) {
            container.innerHTML = renderSpinner();
        }

        // Fetch the Excel file
        Api.get(`/api/exports/${context.exportId}/download`, { responseType: 'arraybuffer' })
            .then(arrayBuffer => {
                // Parse workbook (defer to next frame to allow spinner to paint)
                requestAnimationFrame(() => {
                    try {
                        currentWorkbook = XLSX.read(arrayBuffer, { type: 'array' });
                        currentSheetName = currentWorkbook.SheetNames[0] || null;

                        // Render tabs and first sheet
                        const tabsEl = panelSources.querySelector('#preview-tabs');
                        if (tabsEl) {
                            renderTabs(tabsEl, currentWorkbook);
                        }

                        const bodyEl = panelSources.querySelector('#preview-body');
                        if (bodyEl && currentSheetName) {
                            renderSheet(bodyEl, currentWorkbook, currentSheetName);
                        }
                    } catch (err) {
                        console.error("ExcelRenderer: failed to parse workbook", err);
                        if (container) {
                            container.innerHTML = `<div class="preview-empty"><div><div class="preview-empty-text">Failed to load workbook</div><div class="preview-empty-hint">${escapeHtml(err.message)}</div></div></div>`;
                        }
                    }
                });
            })
            .catch(err => {
                console.error("ExcelRenderer: failed to fetch file", err);
                if (container) {
                    container.innerHTML = `<div class="preview-empty"><div><div class="preview-empty-text">Failed to download file</div><div class="preview-empty-hint">${escapeHtml(err.message)}</div></div></div>`;
                }
            });
    }

    function unmount() {
        currentWorkbook = null;
        currentSheetName = null;
    }

    return {
        mount,
        unmount,
        renderSheet,
    };
})();

// Register with PreviewPanel
if (typeof PreviewPanel !== 'undefined') {
    PreviewPanel.register('excel', ExcelRenderer);
}

window.ExcelRenderer = ExcelRenderer;
