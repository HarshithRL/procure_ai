"""Embed node: FAISS indexing (STUB for Sprint 1)."""

from __future__ import annotations

from agent_server.ingestion.state import IngestionState


def embed_node(state: IngestionState) -> dict:
    """Embed chunks into FAISS index (STUB: no-op for now)."""
    # In Sprint 2, this will:
    # 1. Embed chunks using a model (e.g., sentence-transformers)
    # 2. Index into FAISS
    # 3. Store index to disk
    # For now, return counts of 0.
    return {
        "chunks_embedded": 0,
        "embedding_stats": {},
    }
