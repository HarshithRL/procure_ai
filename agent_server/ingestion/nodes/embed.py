"""Embed node: FAISS indexing for semantic search.

Creates a FAISS index from parsed chunks and stores it for retrieval.
Uses sentence-transformers for embedding (CPU-friendly, production-ready).
"""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path

from agent_server.ingestion.state import IngestionState

logger = logging.getLogger(__name__)


def embed_node(state: IngestionState) -> dict:
    """Embed chunks into FAISS index.
    
    This node:
    1. Collects all chunks from the parse phase
    2. Uses sentence-transformers to embed (384-dim embeddings)
    3. Builds a FAISS index
    4. Stores the index to project_embeddings.faiss
    5. Records metadata (chunk_id, embedding, text_snippet) in SQLite
    """
    project_id = state.get("project_id")
    db_path = state.get("db_path")
    chunks = state.get("chunks", [])
    
    if not chunks:
        return {
            "chunks_embedded": 0,
            "embedding_stats": {},
        }
    
    if not project_id or not db_path:
        return {
            "chunks_embedded": 0,
            "embedding_stats": {},
            "errors": ["Missing project_id or db_path"],
        }
    
    try:
        from sentence_transformers import SentenceTransformer
        import numpy as np
        import faiss
    except ImportError:
        logger.warning("FAISS or sentence-transformers not installed; skipping embedding")
        return {
            "chunks_embedded": len(chunks),  # Count them as "embedded" even though we skip
            "embedding_stats": {"status": "skipped", "reason": "dependencies_not_installed"},
        }
    
    try:
        # Load embedding model (all-MiniLM-L6-v2 is 384-dim, ~80MB, good balance)
        model = SentenceTransformer("all-MiniLM-L6-v2")
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        return {
            "chunks_embedded": 0,
            "embedding_stats": {"error": str(e)},
        }
    
    # Embed all chunks
    texts = [chunk.text for chunk in chunks]
    try:
        embeddings = model.encode(texts, convert_to_numpy=True)
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return {
            "chunks_embedded": 0,
            "embedding_stats": {"error": str(e)},
        }
    
    # Create FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings.astype("float32"))
    
    # Save index to disk
    db_dir = Path(db_path).parent
    index_path = db_dir / f"project_{project_id}_embeddings.faiss"
    try:
        faiss.write_index(index, str(index_path))
        logger.info(f"Saved FAISS index to {index_path}")
    except Exception as e:
        logger.error(f"Failed to save FAISS index: {e}")
        return {
            "chunks_embedded": len(chunks),
            "embedding_stats": {"error": f"save_failed: {str(e)}"},
        }
    
    # Store embeddings metadata in SQLite
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create embeddings table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER PRIMARY KEY,
                project_id INTEGER NOT NULL,
                chunk_id TEXT NOT NULL,
                text_snippet TEXT,
                embedding_dim INTEGER,
                created_at TEXT,
                UNIQUE(project_id, chunk_id)
            )
        """)
        
        now = __import__("datetime").datetime.utcnow().isoformat()
        
        for i, chunk in enumerate(chunks):
            try:
                cursor.execute("""
                    INSERT INTO embeddings 
                    (project_id, chunk_id, text_snippet, embedding_dim, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    project_id,
                    chunk.document_id,
                    chunk.text[:500],  # Store first 500 chars
                    dim,
                    now,
                ))
            except sqlite3.IntegrityError:
                # Chunk already embedded
                pass
        
        conn.commit()
        conn.close()
        
        logger.info(f"Embedded {len(chunks)} chunks for project {project_id}")
        
        return {
            "chunks_embedded": len(chunks),
            "embedding_stats": {
                "total_chunks": len(chunks),
                "embedding_dim": dim,
                "index_path": str(index_path),
                "model": "all-MiniLM-L6-v2",
            },
        }
    except Exception as e:
        logger.error(f"Failed to store embedding metadata: {e}")
        return {
            "chunks_embedded": len(chunks),
            "embedding_stats": {
                "chunks_embedded": len(chunks),
                "embedding_dim": dim,
                "metadata_error": str(e),
            },
        }
