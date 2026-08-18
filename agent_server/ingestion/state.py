"""Shared state for the ingestion graph."""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from agent_server.knowledge_graph.schema import Chunk, ExtractedEdge, ExtractedNode


class IngestionStateRequired(TypedDict):
    """Required keys that are always present in IngestionState."""
    project_id: int
    document_id: str
    file_content: bytes
    file_type: str  # "pdf" | "docx" | "xlsx"
    db_path: str


class IngestionStateOptional(TypedDict, total=False):
    """Optional keys that may or may not be present."""
    file_path: str  # optional legacy path for dev_run CLI

    # Populated by the parse node; fanned out over by Send() in extract.py.
    chunks: Annotated[list[Chunk], operator.add]
    # Per-Send-branch input; not a reducer target (each extract() call reads
    # its own single chunk and never returns this key back into state).
    chunk: Chunk

    # Fanned in from every parallel extract() branch.
    entities: Annotated[list[ExtractedNode], operator.add]
    edges: Annotated[list[ExtractedEdge], operator.add]
    # Edges whose endpoints live in another chunk or in the pre-existing graph.
    # `link` resolves these against the whole project rather than discarding them.
    deferred_edges: Annotated[list[ExtractedEdge], operator.add]
    # Count of nodes/edges dropped for unverifiable evidence, for observability.
    evidence_rejected: Annotated[int, operator.add]
    errors: Annotated[list[str], operator.add]

    # Set by the link node once the vault + SQLite index have been updated.
    nodes_written: int
    edges_written: int

    # Set by the embed node after FAISS indexing completes.
    chunks_embedded: int
    embedding_stats: dict


class IngestionState(IngestionStateRequired, IngestionStateOptional):
    """Full ingestion state combining required and optional keys."""
    pass
