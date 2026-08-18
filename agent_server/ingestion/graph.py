"""Builds the LangGraph StateGraph for ingestion.

Flow: parse (PyMuPDF / python-docx / openpyxl) -> extract (LLM entity/edge
extraction with evidence refs) -> link (merge into the project knowledge graph) -> embed (FAISS indexing).
"""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from agent_server.ingestion.nodes.embed import embed_node
from agent_server.ingestion.nodes.extract import extract_node
from agent_server.ingestion.nodes.link import link_node
from agent_server.ingestion.nodes.parse import parse_node, route_chunks_to_extract
from agent_server.ingestion.state import IngestionState


def build_ingestion_graph() -> CompiledStateGraph:
    """Compile `parse -> extract -> link -> embed`."""
    graph = StateGraph(IngestionState)

    graph.add_node("parse", parse_node)
    graph.add_node("extract", extract_node)
    graph.add_node("link", link_node)
    graph.add_node("embed", embed_node)

    graph.add_edge(START, "parse")
    graph.add_conditional_edges("parse", route_chunks_to_extract, ["extract", "link"])
    graph.add_edge("extract", "link")
    graph.add_edge("link", "embed")
    graph.add_edge("embed", END)

    return graph.compile()
