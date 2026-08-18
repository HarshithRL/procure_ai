"""PDF parsing via PyMuPDF: text + tables per page."""

from __future__ import annotations

import fitz  # PyMuPDF

from agent_server.knowledge_graph.schema import Chunk

_MIN_CHUNK_CHARS = 40


def parse_pdf(file_content: bytes, document_id: str) -> list[Chunk]:
    """Parse a PDF into one `Chunk` per non-trivial paragraph (plus one per
    detected table), each carrying a `'p.<n>'` locator precise enough to cite
    directly as evidence."""
    chunks: list[Chunk] = []
    with fitz.open(stream=file_content, filetype="pdf") as document:
        for page_index, page in enumerate(document, start=1):
            text = page.get_text("text")
            for paragraph_index, paragraph in enumerate(_split_paragraphs(text), start=1):
                if len(paragraph) < _MIN_CHUNK_CHARS:
                    continue
                chunks.append(
                    Chunk(
                        document_id=document_id,
                        locator=f"p.{page_index}",
                        text=paragraph,
                        metadata={"page": page_index, "paragraph": paragraph_index},
                    )
                )
            for table_index, table_text in enumerate(_extract_tables(page), start=1):
                chunks.append(
                    Chunk(
                        document_id=document_id,
                        locator=f"p.{page_index} table {table_index}",
                        text=table_text,
                        metadata={"page": page_index, "table": table_index},
                    )
                )
    return chunks


def _split_paragraphs(text: str) -> list[str]:
    return [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]


def _extract_tables(page: fitz.Page) -> list[str]:
    """Best-effort table extraction using PyMuPDF's built-in table finder."""
    rendered: list[str] = []
    try:
        found = page.find_tables()
    except Exception:  # noqa: BLE001 - table detection is best-effort
        return rendered

    for table in found.tables:
        try:
            rows = table.extract()
        except Exception:  # noqa: BLE001 - skip unparsable tables, keep the rest
            continue
        lines = [" | ".join("" if cell is None else str(cell) for cell in row) for row in rows]
        table_text = "\n".join(line for line in lines if line.strip(" |"))
        if table_text:
            rendered.append(table_text)
    return rendered
