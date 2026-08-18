"""Search evidence tool: find chunks by text similarity."""

from __future__ import annotations

from langchain_core.tools import tool


def make_search_evidence_tool(project_id: int, db_path: str):
    """Create a tool for searching evidence chunks."""
    
    @tool
    def search_evidence(query: str, limit: int = 20) -> list[dict]:
        """
        Search for evidence chunks matching a query.
        
        Args:
            query: Search term or phrase
            limit: Maximum number of results to return
        
        Returns:
            List of matching chunks with document, locator, and snippet
        """
        # STUB: Return mock results for now
        # In Sprint 2, this will use FAISS or SQLite full-text search
        return [
            {
                "document_id": "doc-001",
                "locator": "p.5",
                "snippet": "ACME Corporation provides high-quality components with ISO 9001 certification.",
            },
            {
                "document_id": "doc-002",
                "locator": "Sheet1!A10:D10",
                "snippet": "ACME | Unit Price: $50 | MOQ: 100 | Lead Time: 2 weeks",
            },
        ]
    
    return search_evidence
