"""Backward-compatible shim — use ``core.identity``."""

from shared_library.databricks_connectors.core.identity import (  # noqa: F401
    ConciergeContext,
    IdentityManager,
    IdentitySnapshot,
    UserIdentity,
    WorkspaceUserMetadata,
    get_verified_user_from_headers,
    resolve_identity,
)

__all__ = [
    "ConciergeContext",
    "IdentityManager",
    "IdentitySnapshot",
    "UserIdentity",
    "WorkspaceUserMetadata",
    "get_verified_user_from_headers",
    "resolve_identity",
]

