"""Link node: merge extracted entities into project knowledge graph (STUB for Sprint 1)."""

from __future__ import annotations

from agent_server.ingestion.state import IngestionState


def link_node(state: IngestionState) -> dict:
    """Link extracted nodes/edges into the project graph (STUB: no-op for now)."""
    # In Sprint 2, this will:
    # 1. Resolve node slugs to global IDs
    # 2. Merge into SQLite index
    # 3. Write to vault (if enabled)
    # For now, return counts of 0.
    return {
        "nodes_written": 0,
        "edges_written": 0,
    }
