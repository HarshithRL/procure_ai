"""Exponential backoff with full jitter for transient Databricks API errors."""

from __future__ import annotations

import logging
import random
import time
from typing import Any, Callable, Optional, Set, TypeVar

from shared_library.databricks_connectors.utils.exceptions import RateLimitError, RestError

logger = logging.getLogger("databricks_connectors.retry")

T = TypeVar("T")

RETRYABLE_STATUS_HINTS: Set[str] = {
    "429",
    "500",
    "502",
    "503",
    "504",
    "RESOURCE_EXHAUSTED",
    "TEMPORARILY_UNAVAILABLE",
    "SERVICE_UNDER_MAINTENANCE",
}

NON_RETRYABLE_HINTS: Set[str] = {
    "401",
    "403",
    "UNAUTHENTICATED",
    "PERMISSION_DENIED",
}


def _error_text(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {exc}".upper()


def is_retryable_error(exc: BaseException) -> bool:
    text = _error_text(exc)
    if any(h in text for h in NON_RETRYABLE_HINTS):
        return False
    return any(h in text for h in RETRYABLE_STATUS_HINTS)


def extract_retry_after_seconds(exc: BaseException) -> Optional[float]:
    """Best-effort parse of Retry-After from exception / response attrs."""
    headers = getattr(exc, "headers", None) or getattr(getattr(exc, "response", None), "headers", None)
    if not headers:
        return None
    raw = None
    if hasattr(headers, "get"):
        raw = headers.get("Retry-After") or headers.get("retry-after")
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 5.0


def compute_full_jitter_delay(
    attempt: int,
    *,
    base_delay_seconds: float = 1.0,
    max_delay_seconds: float = 30.0,
    retry_after: Optional[float] = None,
) -> float:
    if retry_after is not None and retry_after > 0:
        return float(retry_after)
    exponential = base_delay_seconds * (2**attempt)
    capped = min(exponential, max_delay_seconds)
    return random.uniform(0.1, capped)


def execute_with_full_jitter(
    fn: Callable[[], T],
    *,
    max_retries: int = 5,
    base_delay_seconds: float = 1.0,
    max_delay_seconds: float = 30.0,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> T:
    """Run ``fn`` with full-jitter backoff on transient errors.

    Never retries 401/403. Honors ``Retry-After`` when present on the error.
    """
    last_exc: Optional[BaseException] = None
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 — classified below
            last_exc = exc
            if not is_retryable_error(exc):
                raise RestError(f"Non-retryable REST failure: {exc}") from exc
            if attempt >= max_retries:
                if is_retryable_error(exc) and ("429" in _error_text(exc) or "RESOURCE_EXHAUSTED" in _error_text(exc)):
                    raise RateLimitError(f"Rate limit persisted after {max_retries} retries: {exc}") from exc
                raise RestError(f"Retries exhausted ({max_retries}): {exc}") from exc

            wait = compute_full_jitter_delay(
                attempt,
                base_delay_seconds=base_delay_seconds,
                max_delay_seconds=max_delay_seconds,
                retry_after=extract_retry_after_seconds(exc),
            )
            logger.warning(
                "Transient Databricks error (attempt %s/%s); sleeping %.2fs: %s",
                attempt + 1,
                max_retries,
                wait,
                exc,
            )
            sleep_fn(wait)

    assert last_exc is not None
    raise RestError(f"Retries exhausted: {last_exc}") from last_exc

