"""Shared exceptions for ``databricks_connectors``."""

from __future__ import annotations


class ConnectorError(Exception):
    """Base error for ``databricks_connectors``."""


class AuthError(ConnectorError):
    """Credential resolution or token refresh failed."""


class IdentityError(ConnectorError):
    """Current-user / identity lookup failed."""


class RateLimitError(ConnectorError):
    """HTTP 429 / RESOURCE_EXHAUSTED after retries exhausted."""

    def __init__(self, message: str, *, status_code: int | None = 429) -> None:
        super().__init__(message)
        self.status_code = status_code


class RestError(ConnectorError):
    """Explicit ``.rest()`` gateway failure (non-retryable or exhausted)."""
