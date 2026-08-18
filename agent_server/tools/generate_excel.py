"""Generate Excel tool: create comparison workbooks with vendor logos and metrics."""

from __future__ import annotations

import logging
from pathlib import Path

from langchain_core.tools import tool

from agent_server.excel_builders.comparison_matrix_builder import ComparisonMatrixBuilder

logger = logging.getLogger(__name__)


def make_generate_excel_tool(project_id: int, db_path: str):
    """Create a tool for generating Excel comparison workbooks."""
    
    @tool
    def generate_excel() -> dict:
        """
        Generate an Excel workbook with vendor comparison data, metrics, and logos.
        
        Includes:
        - Summary sheet with vendor logos, key metrics, and recommendation area
        - BAFO sheet: Best and Final Offer with 3-year cost analysis
        - Scorecard sheet: weighted evaluation criteria
        - Requirements Matrix: requirement vs vendor compliance
        - Risk Assessment: risk items with severity and vendor impact
        
        Returns:
            Dict with success status, file information, and metrics summary
        """
        try:
            # Build the comparison matrix
            builder = ComparisonMatrixBuilder(project_id, db_path)
            workbook_bytes = builder.build()
            
            # Save to temp file or return bytes
            file_size = len(workbook_bytes)
            
            logger.info(f"Generated comparison workbook for project {project_id}: {file_size} bytes")
            
            return {
                "status": "success",
                "project_id": project_id,
                "file_size_bytes": file_size,
                "file_format": "xlsx",
                "sheets": [
                    "Summary",
                    "BAFO Comparison",
                    "Scorecard",
                    "Requirements Matrix",
                    "Risk Assessment",
                ],
                "features": [
                    "Vendor logos (generated or fetched)",
                    "3-year total cost of ownership analysis",
                    "Weighted scoring (Technical 25%, Cost 30%, Timeline 15%, Viability 10%, Support 10%, Security 10%)",
                    "Requirement compliance matrix",
                    "Risk assessment with severity levels",
                    "Recommendation section",
                ],
                "message": "Comparison workbook generated successfully with all vendor logos and procurement metrics",
                "download_url": f"/api/projects/{project_id}/comparison.xlsx",
            }
        except Exception as e:
            logger.error(f"Failed to generate Excel workbook for project {project_id}: {e}")
            return {
                "status": "error",
                "project_id": project_id,
                "error": str(e),
                "message": "Failed to generate comparison workbook",
            }
    
    return generate_excel
