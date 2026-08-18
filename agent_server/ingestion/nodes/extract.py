"""Extract node: LLM entity/edge extraction (STUB for Sprint 1)."""

from __future__ import annotations

from agent_server.ingestion.state import IngestionState


def extract_node(state: IngestionState) -> dict:
    """Extract entities and edges from chunk (STUB: returns empty for now)."""
    # In Sprint 2, this will call an LLM to extract nodes/edges from the chunk.
    # For now, return empty lists to allow the DAG to flow through.
    return {
        "entities": [],
        "edges": [],
        "deferred_edges": [],
    }
