"""Link node: merge extracted entities into project knowledge graph.

Responsibilities:
1. Collect all extracted nodes and edges from parallel extract() branches
2. Deduplicate nodes by slug (merge similar vendors, requirements)
3. Resolve deferred edges by matching source/target slugs to node IDs
4. Write nodes and edges to the SQLite vault
5. Return counts for observability
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from agent_server.ingestion.state import IngestionState
from agent_server.knowledge_graph.schema import (
    Edge,
    Node,
    ExtractedNode,
    ExtractedEdge,
    EvidenceRef,
)

logger = logging.getLogger(__name__)


def _get_sqlite_connection(db_path: str) -> sqlite3.Connection:
    """Get SQLite connection and ensure schema exists."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Ensure tables exist
    cursor = conn.cursor()
    
    # Nodes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            id TEXT PRIMARY KEY,
            project_id INTEGER NOT NULL,
            node_type TEXT NOT NULL,
            label TEXT NOT NULL,
            slug TEXT NOT NULL,
            description TEXT,
            metadata TEXT,  -- JSON
            evidence TEXT,  -- JSON list of EvidenceRef
            confidence REAL,
            created_at TEXT,
            UNIQUE(project_id, node_type, slug)
        )
    """)
    
    # Edges table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            id TEXT PRIMARY KEY,
            project_id INTEGER NOT NULL,
            source_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            edge_type TEXT NOT NULL,
            metadata TEXT,  -- JSON
            evidence TEXT,  -- JSON
            confidence REAL,
            created_at TEXT,
            FOREIGN KEY(source_id) REFERENCES nodes(id),
            FOREIGN KEY(target_id) REFERENCES nodes(id)
        )
    """)
    
    conn.commit()
    return conn


def _node_id(project_id: int, node_type: str, slug: str) -> str:
    """Generate stable node ID."""
    return f"project_{project_id}_{node_type}_{slug}".replace("-", "_")


def _insert_or_merge_node(
    conn: sqlite3.Connection,
    project_id: int,
    extracted_node: ExtractedNode,
) -> str:
    """Insert or merge node into SQLite, return node ID."""
    cursor = conn.cursor()
    node_id = _node_id(project_id, extracted_node.node_type.value, extracted_node.slug)
    
    now = datetime.utcnow().isoformat()
    
    metadata_json = json.dumps(extracted_node.metadata or {})
    evidence_json = json.dumps([
        {
            "document_id": ref.document_id,
            "locator": ref.locator,
            "snippet": ref.snippet,
        }
        for ref in (extracted_node.evidence or [])
    ])
    
    try:
        cursor.execute("""
            INSERT INTO nodes 
            (id, project_id, node_type, label, slug, description, metadata, evidence, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            node_id,
            project_id,
            extracted_node.node_type.value,
            extracted_node.label,
            extracted_node.slug,
            extracted_node.description,
            metadata_json,
            evidence_json,
            extracted_node.confidence or 0.8,
            now,
        ))
        conn.commit()
        logger.debug(f"Inserted node {node_id}")
    except sqlite3.IntegrityError:
        # Node already exists (duplicate slug); merge evidence
        logger.debug(f"Node {node_id} already exists; merging evidence")
        cursor.execute("""
            UPDATE nodes
            SET evidence = ?, confidence = MAX(confidence, ?)
            WHERE id = ?
        """, (evidence_json, extracted_node.confidence or 0.8, node_id))
        conn.commit()
    
    return node_id


def _resolve_node_id(
    conn: sqlite3.Connection,
    project_id: int,
    node_type: str,
    slug: str,
) -> str | None:
    """Resolve slug to node ID, return None if not found."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM nodes
        WHERE project_id = ? AND node_type = ? AND slug = ?
        LIMIT 1
    """, (project_id, node_type, slug))
    row = cursor.fetchone()
    return row[0] if row else None


def _insert_edge(
    conn: sqlite3.Connection,
    project_id: int,
    source_id: str,
    target_id: str,
    edge_type: str,
    evidence: list[dict],
    confidence: float,
) -> str:
    """Insert edge into SQLite, return edge ID."""
    cursor = conn.cursor()
    edge_id = f"{source_id}_{edge_type}_{target_id}".replace("-", "_")
    
    now = datetime.utcnow().isoformat()
    evidence_json = json.dumps(evidence)
    
    try:
        cursor.execute("""
            INSERT INTO edges
            (id, project_id, source_id, target_id, edge_type, evidence, confidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            edge_id,
            project_id,
            source_id,
            target_id,
            edge_type,
            evidence_json,
            confidence,
            now,
        ))
        conn.commit()
        logger.debug(f"Inserted edge {edge_id}")
    except sqlite3.IntegrityError:
        logger.debug(f"Edge {edge_id} already exists")
    
    return edge_id


def link_node(state: IngestionState) -> dict:
    """Link extracted nodes/edges into the project graph.
    
    Fanned in from all parallel extract() branches via the state reducer (operator.add).
    Collects all entities and edges, deduplicates, resolves references, and writes to SQLite.
    """
    project_id = state.get("project_id")
    db_path = state.get("db_path")
    
    if not project_id or not db_path:
        return {"nodes_written": 0, "edges_written": 0, "errors": ["Missing project_id or db_path"]}
    
    entities = state.get("entities", [])
    deferred_edges = state.get("deferred_edges", [])
    
    try:
        conn = _get_sqlite_connection(db_path)
    except Exception as e:
        return {"nodes_written": 0, "edges_written": 0, "errors": [f"DB connection failed: {str(e)}"]}
    
    nodes_written = 0
    edges_written = 0
    errors = []
    
    # Insert nodes
    node_id_map: dict[str, str] = {}  # (node_type, slug) -> node_id
    
    for entity in entities:
        try:
            node_id = _insert_or_merge_node(conn, project_id, entity)
            node_id_map[(entity.node_type.value, entity.slug)] = node_id
            nodes_written += 1
        except Exception as e:
            logger.error(f"Failed to insert node {entity.slug}: {e}")
            errors.append(f"Node insert failed: {str(e)}")
    
    # Ensure project node exists (root god-node)
    project_node_id = _resolve_node_id(conn, project_id, "project", "project")
    if not project_node_id:
        from agent_server.knowledge_graph.schema import NodeType
        # Insert project node if it doesn't exist
        project_node_id = _insert_or_merge_node(
            conn,
            project_id,
            ExtractedNode(
                node_type=NodeType.PROJECT,
                label=f"Project {project_id}",
                slug="project",
                description=None,
                evidence=[],
                metadata={},
                confidence=1.0,
            ),
        )
        node_id_map[("project", "project")] = project_node_id
        nodes_written += 1
    
    # Resolve and insert edges
    for edge in deferred_edges:
        try:
            # Resolve source and target
            source_id = node_id_map.get((edge.source_type.value, edge.source_slug))
            target_id = node_id_map.get((edge.target_type.value, edge.target_slug))
            
            if not source_id:
                source_id = _resolve_node_id(conn, project_id, edge.source_type.value, edge.source_slug)
            if not target_id:
                target_id = _resolve_node_id(conn, project_id, edge.target_type.value, edge.target_slug)
            
            if source_id and target_id:
                evidence_dicts = [
                    {
                        "document_id": ref.document_id,
                        "locator": ref.locator,
                        "snippet": ref.snippet,
                    }
                    for ref in (edge.evidence or [])
                ]
                _insert_edge(
                    conn,
                    project_id,
                    source_id,
                    target_id,
                    edge.edge_type.value,
                    evidence_dicts,
                    edge.confidence or 0.8,
                )
                edges_written += 1
            else:
                # Keep deferred if we can't resolve yet (cross-chunk reference)
                logger.debug(
                    f"Cannot resolve edge {edge.source_type.value}/{edge.source_slug} "
                    f"-> {edge.target_type.value}/{edge.target_slug}; deferring to next batch"
                )
        except Exception as e:
            logger.error(f"Failed to insert edge: {e}")
            errors.append(f"Edge insert failed: {str(e)}")
    
    conn.close()
    
    return {
        "nodes_written": nodes_written,
        "edges_written": edges_written,
        "errors": errors,
    }
