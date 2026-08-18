"""Generate Excel tool: create comparison workbooks."""

from __future__ import annotations

from langchain_core.tools import tool


def make_generate_excel_tool(project_id: int, db_path: str):
    """Create a tool for generating Excel comparison workbooks."""
    
    @tool
    def generate_excel(project_id: int) -> dict:
        """
        Generate an Excel workbook with vendor comparison data.
        
        Args:
            project_id: Project ID to generate comparison for
        
        Returns:
            Dict with file_url and file_size (or error message)
        """
        # STUB: Return mock response for now
        # In Sprint 2, this will use openpyxl to build a real workbook
        return {
            "status": "success",
            "file_url": f"/api/projects/{project_id}/comparison.xlsx",
            "file_size_bytes": 45678,
            "message": "Comparison workbook generated successfully",
        }
    
    return generate_excel
