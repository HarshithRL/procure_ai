"""Shared exception hierarchy for ``shared_libraries.utilities``."""

from __future__ import annotations


class UtilitiesError(Exception):
    """Base error for utility subsystem failures."""


class YouSearchError(UtilitiesError):
    """Base error for You.com search client failures."""


class YouSearchConfigError(YouSearchError):
    """Missing or invalid You.com client configuration (e.g. API key)."""


class YouSearchHttpError(YouSearchError):
    """You.com API returned an HTTP error or non-JSON body."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        detail: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.detail = detail


class YouSearchTimeoutError(YouSearchError):
    """You.com request timed out."""


class DocumentTextError(UtilitiesError):
    """Base error for document text service failures."""
