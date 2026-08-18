"""HTTP / external API utility clients."""

from shared_libraries.utilities.api.you_search import (
    YouSearchClient,
    YouSearchHit,
    YouSearchResult,
    extract_urls_from_text,
    normalize_freshness,
    resolve_you_api_key,
)

__all__ = [
    "YouSearchClient",
    "YouSearchHit",
    "YouSearchResult",
    "extract_urls_from_text",
    "normalize_freshness",
    "resolve_you_api_key",
]
