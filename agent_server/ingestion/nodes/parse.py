"""Parse node: dispatch to parser by file type."""

from __future__ import annotations

from agent_server.ingestion.parsers import parse_docx, parse_pdf, parse_xlsx
from agent_server.ingestion.state import IngestionState


def parse_node(state: IngestionState) -> dict:
    """Parse document by file type and return chunks."""
    file_type = state["file_type"].lower()
    file_content = state["file_content"]
    document_id = state["document_id"]
    
    try:
        if file_type == "pdf":
            chunks = parse_pdf(file_content, document_id)
        elif file_type == "docx":
            chunks = parse_docx(file_content, document_id)
        elif file_type == "xlsx":
            chunks = parse_xlsx(file_content, document_id)
        else:
            return {"chunks": [], "errors": [f"Unsupported file type: {file_type}"]}
        
        return {"chunks": chunks}
    except Exception as e:
        return {"chunks": [], "errors": [f"Parse error: {str(e)}"]}


def route_chunks_to_extract(state: IngestionState) -> str:
    """Route: if chunks exist, go to extract; otherwise skip to link."""
    chunks = state.get("chunks", [])
    if chunks:
        return "extract"
    else:
        return "link"
