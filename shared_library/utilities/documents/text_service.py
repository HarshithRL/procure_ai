"""Pure document markdown / chunk text operations.

No agent session state, no LangChain. Callers supply markdown, chunks, and
document metadata dicts; tool adapters live in ``agent_server.tools``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence


class DocumentTextService:
    """Production helpers for overview, search, and excerpt over extracted text.

    Example::

        svc = DocumentTextService()
        text = svc.search("pricing", markdown=md, chunks=chunks)
    """

    def __init__(
        self,
        *,
        default_preview_chars: int = 2000,
        default_max_hits: int = 12,
        max_excerpt_chars: int = 12_000,
    ) -> None:
        self.default_preview_chars = int(default_preview_chars)
        self.default_max_hits = int(default_max_hits)
        self.max_excerpt_chars = int(max_excerpt_chars)

    @staticmethod
    def resolve_meta_path(doc_meta: Mapping[str, Any] | None) -> Path | None:
        """Resolve ``_meta.json`` path from doc metadata or sibling of markdown."""
        if not isinstance(doc_meta, Mapping):
            return None
        meta_path = str(doc_meta.get("meta_path") or "").strip()
        if meta_path:
            return Path(meta_path)
        md_path = str(doc_meta.get("markdown_path") or "").strip()
        if not md_path:
            return None
        p = Path(md_path)
        sibling = p.with_name(p.name.replace("_document.md", "_meta.json"))
        if sibling.name.endswith("_meta.json"):
            return sibling
        return None

    def overview(
        self,
        doc_meta: Mapping[str, Any],
        markdown: str,
        *,
        preview_chars: int | None = None,
    ) -> str:
        """Format metadata + short markdown preview for agent consumption."""
        limit = (
            self.default_preview_chars
            if preview_chars is None
            else max(0, int(preview_chars))
        )
        preview = markdown[:limit] if markdown else "(no markdown available)"
        return (
            f"file_name: {doc_meta.get('file_name')}\n"
            f"document_id: {doc_meta.get('document_id')}\n"
            f"pages: {doc_meta.get('page_count')}\n"
            f"parser: {doc_meta.get('parser')}\n"
            f"file_type: {doc_meta.get('file_type')}\n"
            f"ingest_status: {doc_meta.get('ingest_status')}\n"
            f"markdown_length: {doc_meta.get('markdown_length')}\n"
            f"chunk_count: {doc_meta.get('chunk_count')}\n"
            f"markdown_path: {doc_meta.get('markdown_path')}\n\n"
            f"Preview:\n{preview}"
        )

    def search(
        self,
        query: str,
        *,
        markdown: str = "",
        chunks: Sequence[Mapping[str, Any]] | None = None,
        max_hits: int | None = None,
    ) -> str:
        """Case-insensitive search preferring chunk index, then full markdown."""
        q = (query or "").strip()
        if not q:
            return "Empty query. Provide search terms."

        needle = q.lower()
        limit = self.default_max_hits if max_hits is None else max(1, int(max_hits))
        chunk_list = list(chunks or [])

        if chunk_list:
            hits: list[str] = []
            for ch in chunk_list:
                if not isinstance(ch, Mapping):
                    continue
                text = str(ch.get("text") or "")
                if needle not in text.lower():
                    continue
                heading = ch.get("heading") or ch.get("page_or_sheet") or ch.get("chunk_id")
                idx = text.lower().find(needle)
                lo = max(0, idx - 120)
                hi = min(len(text), idx + len(q) + 280)
                snippet = text[lo:hi]
                hits.append(
                    f"{heading} [{ch.get('chunk_id')}] "
                    f"chars {ch.get('start_char')}-{ch.get('end_char')}:\n{snippet}"
                )
                if len(hits) >= limit:
                    break
            if hits:
                return (
                    f"Found {len(hits)} chunk match(es) for {q!r}:\n\n"
                    + "\n\n---\n\n".join(hits)
                )

        if not markdown:
            return "Document markdown is empty or missing."

        lines = markdown.splitlines()
        line_hits: list[str] = []
        for i, line in enumerate(lines):
            if needle in line.lower():
                start = max(0, i - 1)
                end = min(len(lines), i + 2)
                snippet = "\n".join(lines[start:end])
                line_hits.append(f"L{i + 1}: {snippet}")
                if len(line_hits) >= limit:
                    break

        if not line_hits:
            idx = markdown.lower().find(needle)
            if idx < 0:
                return f"No matches for {q!r}."
            lo = max(0, idx - 200)
            hi = min(len(markdown), idx + len(q) + 400)
            return f"Match near offset {idx}:\n{markdown[lo:hi]}"

        return (
            f"Found {len(line_hits)} match group(s) for {q!r}:\n\n"
            + "\n\n---\n\n".join(line_hits)
        )

    def excerpt(
        self,
        markdown: str,
        start_char: int = 0,
        max_chars: int = 4000,
    ) -> str:
        """Return a character-range slice of markdown with offset metadata."""
        if not markdown:
            return "Document markdown is empty or missing."

        start = max(0, int(start_char or 0))
        limit = min(max(1, int(max_chars or 4000)), self.max_excerpt_chars)
        slice_text = markdown[start : start + limit]
        return (
            f"offset={start} length={len(slice_text)} total={len(markdown)}\n\n"
            f"{slice_text}"
        )
