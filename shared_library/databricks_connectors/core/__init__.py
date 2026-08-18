"""Core platform security modules (auth + identity)."""

from shared_library.databricks_connectors.core.auth import (
    AuthManager,
    AuthProvider,
    AuthenticationResolver,
    DatabricksHttpxAuth,
)
from shared_library.databricks_connectors.core.identity import (
    ConciergeContext,
    IdentityManager,
    IdentitySnapshot,
    UserIdentity,
    WorkspaceUserMetadata,
    get_verified_user_from_headers,
    resolve_identity,
)

__all__ = [
    "AuthManager",
    "AuthProvider",
    "AuthenticationResolver",
    "ConciergeContext",
    "DatabricksHttpxAuth",
    "IdentityManager",
    "IdentitySnapshot",
    "UserIdentity",
    "WorkspaceUserMetadata",
    "get_verified_user_from_headers",
    "resolve_identity",
]

