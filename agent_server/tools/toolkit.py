"""Shared tool assembly for agent builders."""

from __future__ import annotations

from agent_server.tools.generate_excel import make_generate_excel_tool
from agent_server.tools.query_knowledge_graph import make_query_knowledge_graph_tool
from agent_server.tools.search_evidence import make_search_evidence_tool


def make_analysis_tools(project_id: int, db_path: str) -> list:
    """
    Create the analysis toolset for the brain agent.
    
    Includes:
    - query_knowledge_graph: search nodes and edges
    - search_evidence: find chunks by text similarity
    - generate_excel: create comparison workbooks
    """
    return [
        make_query_knowledge_graph_tool(project_id, db_path),
        make_search_evidence_tool(project_id, db_path),
        make_generate_excel_tool(project_id, db_path),
    ]
