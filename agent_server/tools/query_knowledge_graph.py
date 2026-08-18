"""Query knowledge graph tool: search nodes and edges by type or name."""

from __future__ import annotations

from langchain_core.tools import tool


def make_query_knowledge_graph_tool(project_id: int, db_path: str):
    """Create a tool for querying the knowledge graph."""
    
    @tool
    def query_knowledge_graph(query: str, limit: int = 10) -> list[dict]:
        """
        Query the knowledge graph for nodes matching a search term.
        
        Args:
            query: Search term (node name, type, or attribute)
            limit: Maximum number of results to return
        
        Returns:
            List of matching nodes with type, name, and ID
        """
        # STUB: Return mock results for now
        # In Sprint 2, this will query the SQLite index
        return [
            {
                "id": "vendor--acme-corp",
                "type": "vendor",
                "name": "ACME Corporation",
                "attributes": {"country": "USA"},
            },
            {
                "id": "vendor--globex-inc",
                "type": "vendor",
                "name": "Globex Inc",
                "attributes": {"country": "Canada"},
            },
        ]
    
    return query_knowledge_graph
