"""You.com web search client — framework-agnostic HTTP API wrapper.

No LangChain / tool decorators. Agent wrappers live in ``agent_server.tools``.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx

from shared_libraries.utilities.exceptions import (
    YouSearchConfigError,
    YouSearchHttpError,
    YouSearchTimeoutError,
)

_DEFAULT_SEARCH_URL = "https://api.you.com/v1/search"
_URL_RE = re.compile(r"https?://[^\s\]\)\"'<>]+")
_DEFAULT_TIMEOUT_S = 20.0
_VALID_FRESHNESS = frozenset({"day", "week", "month", "year"})


@dataclass(frozen=True)
class YouSearchHit:
    """One web/news hit from You.com."""

    title: str
    url: Optional[str]
    passages: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass(frozen=True)
class YouSearchResult:
    """Structured search response."""

    query: str
    hits: list[YouSearchHit]
    count_requested: int
    freshness: Optional[str] = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def urls(self) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for hit in self.hits:
            if hit.url and hit.url not in seen:
                seen.add(hit.url)
                out.append(hit.url)
        return out


def resolve_you_api_key(
    api_key: Optional[str] = None,
    *,
    env: Optional[dict[str, str]] = None,
) -> Optional[str]:
    """Resolve API key from explicit arg or ``YDC_API_KEY`` / ``YOU_API_KEY``."""
    if api_key and str(api_key).strip():
        return str(api_key).strip()
    source = env if env is not None else os.environ
    return (
        (source.get("YDC_API_KEY") or "").strip()
        or (source.get("YOU_API_KEY") or "").strip()
        or None
    )


def extract_urls_from_text(text: str) -> list[str]:
    """Unique http(s) URLs in text order (Developer Mode / turn metrics)."""
    seen: set[str] = set()
    out: list[str] = []
    for m in _URL_RE.finditer(text or ""):
        url = m.group(0).rstrip(".,);]")
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out


def _passages_from_raw_hit(hit: dict[str, Any]) -> list[str]:
    passages: list[str] = []
    contents = hit.get("contents") if isinstance(hit.get("contents"), dict) else {}
    highlights = contents.get("highlights") if isinstance(contents, dict) else None
    if isinstance(highlights, list):
        for h in highlights:
            text = (
                str(h).strip()
                if not isinstance(h, dict)
                else str(h.get("text") or h.get("snippet") or h).strip()
            )
            if text:
                passages.append(text)
    if not passages:
        snippets = hit.get("snippets") or []
        if isinstance(snippets, list):
            passages.extend(str(s).strip() for s in snippets if str(s).strip())
    if not passages:
        desc = str(hit.get("description") or "").strip()
        if desc:
            passages.append(desc)
    return passages


def parse_hit(raw: dict[str, Any]) -> YouSearchHit:
    """Parse a single You.com result dict into ``YouSearchHit``."""
    title = str(raw.get("title") or "Untitled").strip()
    url = str(raw.get("url") or "").strip() or None
    return YouSearchHit(
        title=title,
        url=url,
        passages=_passages_from_raw_hit(raw),
        raw=raw,
    )


def normalize_freshness(freshness: Optional[str]) -> Optional[str]:
    """Normalize freshness filter; invalid values become ``None``."""
    fresh = (freshness or "").strip().lower() or None
    if fresh and fresh not in _VALID_FRESHNESS:
        return None
    return fresh


def clamp_count(count: int | None, *, default: int = 5, lo: int = 1, hi: int = 10) -> int:
    """Clamp result count into ``[lo, hi]``."""
    try:
        value = int(count if count is not None else default)
    except (TypeError, ValueError):
        value = default
    return max(lo, min(value, hi))


class YouSearchClient:
    """Production You.com search client (sync + async).

    Example::

        client = YouSearchClient.from_env()
        result = client.search("vendor pricing", count=5, freshness="week")
        text = client.format_for_agent(result)
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: str = _DEFAULT_SEARCH_URL,
        timeout_s: float = _DEFAULT_TIMEOUT_S,
        require_api_key: bool = True,
    ) -> None:
        self.api_key = (api_key or "").strip() or None
        self.base_url = (base_url or _DEFAULT_SEARCH_URL).rstrip("/")
        self.timeout_s = float(timeout_s)
        self.require_api_key = bool(require_api_key)

    @classmethod
    def from_env(
        cls,
        *,
        timeout_s: float = _DEFAULT_TIMEOUT_S,
        base_url: str = _DEFAULT_SEARCH_URL,
        require_api_key: bool = True,
    ) -> "YouSearchClient":
        """Build a client using ``YDC_API_KEY`` or ``YOU_API_KEY``."""
        return cls(
            api_key=resolve_you_api_key(),
            base_url=base_url,
            timeout_s=timeout_s,
            require_api_key=require_api_key,
        )

    def _ensure_api_key(self) -> str:
        if self.api_key:
            return self.api_key
        if self.require_api_key:
            raise YouSearchConfigError(
                "You.com API key missing. Set YDC_API_KEY (or YOU_API_KEY) "
                "in the environment and retry."
            )
        raise YouSearchConfigError("You.com API key is not configured.")

    def _headers(self, api_key: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {api_key}",
            "X-API-Key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _build_payload(
        self,
        query: str,
        *,
        count: int = 5,
        freshness: Optional[str] = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "query": query,
            "count": clamp_count(count),
            "extraction": {"extraction_mode": "highlights"},
        }
        fresh = normalize_freshness(freshness)
        if fresh:
            payload["freshness"] = fresh
        return payload

    def _parse_response(
        self,
        data: dict[str, Any],
        *,
        query: str,
        count: int,
        freshness: Optional[str],
    ) -> YouSearchResult:
        results = (data or {}).get("results") or {}
        web = results.get("web") or []
        news = results.get("news") or []
        raw_hits = [h for h in list(web) + list(news) if isinstance(h, dict)]
        hits = [parse_hit(h) for h in raw_hits[:count]]
        return YouSearchResult(
            query=query,
            hits=hits,
            count_requested=count,
            freshness=normalize_freshness(freshness),
            raw=data if isinstance(data, dict) else {},
        )

    def _raise_for_response(self, resp: httpx.Response) -> dict[str, Any]:
        if resp.status_code >= 400:
            detail = (resp.text or "")[:300]
            raise YouSearchHttpError(
                f"You.com HTTP {resp.status_code}: {detail}",
                status_code=resp.status_code,
                detail=detail,
            )
        try:
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            raise YouSearchHttpError(
                "You.com returned non-JSON response.",
                status_code=resp.status_code,
            ) from exc
        if not isinstance(data, dict):
            raise YouSearchHttpError(
                "You.com returned unexpected JSON payload.",
                status_code=resp.status_code,
            )
        return data

    def search(
        self,
        query: str,
        *,
        count: int = 5,
        freshness: Optional[str] = None,
    ) -> YouSearchResult:
        """Execute a synchronous You.com search."""
        q = (query or "").strip()
        if not q:
            raise YouSearchConfigError("query is required.")

        api_key = self._ensure_api_key()
        payload = self._build_payload(q, count=count, freshness=freshness)

        try:
            with httpx.Client(timeout=self.timeout_s) as client:
                resp = client.post(
                    self.base_url,
                    json=payload,
                    headers=self._headers(api_key),
                )
        except httpx.TimeoutException as exc:
            raise YouSearchTimeoutError(
                f"You.com search timed out after {self.timeout_s:.0f}s."
            ) from exc
        except httpx.HTTPError as exc:
            raise YouSearchHttpError(
                f"You.com request failed: {type(exc).__name__}: {exc}"
            ) from exc

        data = self._raise_for_response(resp)
        return self._parse_response(
            data,
            query=q,
            count=int(payload["count"]),
            freshness=payload.get("freshness"),
        )

    async def asearch(
        self,
        query: str,
        *,
        count: int = 5,
        freshness: Optional[str] = None,
    ) -> YouSearchResult:
        """Execute an asynchronous You.com search."""
        q = (query or "").strip()
        if not q:
            raise YouSearchConfigError("query is required.")

        api_key = self._ensure_api_key()
        payload = self._build_payload(q, count=count, freshness=freshness)

        try:
            async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                resp = await client.post(
                    self.base_url,
                    json=payload,
                    headers=self._headers(api_key),
                )
        except httpx.TimeoutException as exc:
            raise YouSearchTimeoutError(
                f"You.com search timed out after {self.timeout_s:.0f}s."
            ) from exc
        except httpx.HTTPError as exc:
            raise YouSearchHttpError(
                f"You.com request failed: {type(exc).__name__}: {exc}"
            ) from exc

        data = self._raise_for_response(resp)
        return self._parse_response(
            data,
            query=q,
            count=int(payload["count"]),
            freshness=payload.get("freshness"),
        )

    @staticmethod
    def format_hit(idx: int, hit: YouSearchHit) -> tuple[str, Optional[str]]:
        """Format one hit for agent-facing text; returns ``(block, url)``."""
        header = f"[{idx}] {hit.title}"
        if hit.url:
            header = f"{header} — {hit.url}"
        body = (
            "\n".join(f"    {p}" for p in hit.passages[:3])
            if hit.passages
            else "    (no excerpt)"
        )
        return f"{header}\n{body}", hit.url

    def format_for_agent(self, result: YouSearchResult) -> str:
        """Render structured results as the legacy agent/LLM string format."""
        if not result.hits:
            return "No web results found for this query."

        blocks: list[str] = []
        for i, hit in enumerate(result.hits, start=1):
            block, _url = self.format_hit(i, hit)
            blocks.append(block)

        header = (
            f"Web search results for: {result.query}\n"
            f"Cite sources inline as [n] and include the URL when stating facts.\n"
        )
        return header + "\n\n".join(blocks)

    def search_as_text(
        self,
        query: str,
        *,
        count: int = 5,
        freshness: Optional[str] = None,
    ) -> str:
        """Search and return agent-facing text (raises on transport/config errors)."""
        return self.format_for_agent(
            self.search(query, count=count, freshness=freshness)
        )

    async def asearch_as_text(
        self,
        query: str,
        *,
        count: int = 5,
        freshness: Optional[str] = None,
    ) -> str:
        """Async search returning agent-facing text."""
        return self.format_for_agent(
            await self.asearch(query, count=count, freshness=freshness)
        )

    @staticmethod
    def extract_urls(text: str) -> list[str]:
        """Unique http(s) URLs in tool/output text order."""
        return extract_urls_from_text(text)

    def error_message(self, exc: BaseException) -> str:
        """Map client exceptions to legacy ``ERROR: ...`` agent strings."""
        if isinstance(exc, YouSearchConfigError):
            msg = str(exc)
            if "API key" in msg:
                return f"ERROR: {msg}"
            if "query is required" in msg.lower():
                return "ERROR: query is required."
            return f"ERROR: {msg}"
        if isinstance(exc, YouSearchTimeoutError):
            return f"ERROR: {exc}"
        if isinstance(exc, YouSearchHttpError):
            return f"ERROR: {exc}"
        return f"ERROR: You.com request failed: {type(exc).__name__}: {exc}"
