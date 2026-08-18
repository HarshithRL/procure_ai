"""Backward-compatible shim — use ``utils.exceptions``."""

from shared_library.databricks_connectors.utils.exceptions import (  # noqa: F401
    AuthError,
    ConnectorError,
    IdentityError,
    RateLimitError,
    RestError,
)

__all__ = [
    "AuthError",
    "ConnectorError",
    "IdentityError",
    "RateLimitError",
    "RestError",
]

