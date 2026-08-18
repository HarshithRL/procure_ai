"""In-process TTL cache for local Databricks CLI OAuth tokens.

``Config.oauth_token()`` shells out to ``databricks auth token --force-refresh``,
which routinely takes 10–15s. Caching until near expiry avoids that cost on
every Streamlit / agent_server request while keeping OAuth (no PAT).

Never logs raw access tokens.
"""

from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
from datetime import datetime
from typing import Any, Optional

logger = logging.getLogger("databricks_connectors.cli_token_cache")

# Refresh this many seconds before expiry (Databricks access tokens ~1h).
_DEFAULT_SKEW_SECONDS = 300
_DEFAULT_TTL_SECONDS = 3300  # ~55 min when expiry metadata is missing
# Cap force-refresh so DNS/OIDC outages do not block agent turns for minutes.
_DEFAULT_REFRESH_TIMEOUT_SECONDS = 8.0

_lock = threading.Lock()
_refresh_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="cli-oauth")
# (host, profile) -> (access_token, expires_at_epoch)
_cache: dict[tuple[str, str], tuple[str, float]] = {}


def _cache_key(host: Optional[str], profile: Optional[str]) -> tuple[str, str]:
    return (str(host or "").rstrip("/").lower(), str(profile or "DEFAULT"))


def _expiry_epoch(token_info: Any) -> float:
    """Best-effort expiry from SDK token info; default ~55 minutes from now."""
    now = time.time()

    for attr in ("expiry", "expires_at", "expires_on"):
        val = getattr(token_info, attr, None)
        if val is None and isinstance(token_info, dict):
            val = token_info.get(attr)
        if val is None:
            continue
        if isinstance(val, (int, float)):
            return float(val) if val > 1e9 else now + float(val)
        if hasattr(val, "timestamp"):
            try:
                return float(val.timestamp())
            except Exception:  # noqa: BLE001
                pass
        if isinstance(val, str):
            try:
                return datetime.fromisoformat(val.replace("Z", "+00:00")).timestamp()
            except ValueError:
                pass

    expires_in = getattr(token_info, "expires_in", None)
    if expires_in is None and isinstance(token_info, dict):
        expires_in = token_info.get("expires_in")
    if expires_in is not None:
        try:
            return now + float(expires_in)
        except (TypeError, ValueError):
            pass

    return now + _DEFAULT_TTL_SECONDS


def peek_cached_cli_oauth_token(
    *,
    host: Optional[str] = None,
    profile: Optional[str] = None,
    skew_seconds: int = _DEFAULT_SKEW_SECONDS,
) -> Optional[str]:
    """Return a still-valid cached token without triggering CLI refresh."""
    key = _cache_key(host, profile)
    now = time.time()
    with _lock:
        hit = _cache.get(key)
        if hit is None:
            return None
        token, expires_at = hit
        if token and now < (expires_at - skew_seconds):
            return token
    return None


def get_cached_cli_oauth_token(
    *,
    host: Optional[str] = None,
    profile: Optional[str] = None,
    http_timeout_seconds: Optional[int] = None,
    skew_seconds: int = _DEFAULT_SKEW_SECONDS,
    force_refresh: bool = False,
    refresh_timeout_seconds: float = _DEFAULT_REFRESH_TIMEOUT_SECONDS,
) -> Optional[str]:
    """Return a local CLI OAuth access token, cached until near expiry.

    Concurrent callers for the same (host, profile) share one refresh under
    the module lock so Streamlit + API do not each spawn ``--force-refresh``.
    Refresh is hard-capped so DNS/OIDC failures fail fast instead of hanging.
    """
    key = _cache_key(host, profile)
    now = time.time()

    with _lock:
        if not force_refresh:
            hit = _cache.get(key)
            if hit is not None:
                token, expires_at = hit
                if token and now < (expires_at - skew_seconds):
                    logger.debug("CLI OAuth token cache hit profile=%s", profile)
                    return token

        from databricks.sdk.core import Config

        cfg_kwargs: dict[str, Any] = {"profile": profile or "DEFAULT"}
        if host:
            cfg_kwargs["host"] = host
        if http_timeout_seconds is not None:
            cfg_kwargs["http_timeout_seconds"] = http_timeout_seconds

        cfg = Config(**cfg_kwargs)

        def _refresh() -> Any:
            return cfg.oauth_token()

        try:
            future = _refresh_executor.submit(_refresh)
            token_info = future.result(timeout=max(1.0, float(refresh_timeout_seconds)))
        except FuturesTimeout as exc:
            future.cancel()
            logger.warning(
                "CLI OAuth token refresh timed out after %.1fs profile=%s",
                refresh_timeout_seconds,
                profile,
            )
            raise TimeoutError(
                f"CLI OAuth token refresh timed out after {refresh_timeout_seconds:.0f}s"
            ) from exc

        access = getattr(token_info, "access_token", None) if token_info else None
        if not access and isinstance(token_info, dict):
            access = token_info.get("access_token")
        if not access:
            return None

        access_str = str(access)
        expires_at = _expiry_epoch(token_info)
        _cache[key] = (access_str, expires_at)
        logger.debug(
            "CLI OAuth token cached profile=%s expires_in=%.0fs",
            profile,
            max(0.0, expires_at - time.time()),
        )
        return access_str


def clear_cli_oauth_token_cache() -> None:
    """Drop all cached CLI tokens (tests / forced re-auth)."""
    with _lock:
        _cache.clear()
