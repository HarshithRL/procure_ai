""" Backward-compatible shim — use ``core.auth``."""

from shared_library.databricks_connectors.core.auth import (  # noqa: F401
    AuthManager,
    AuthProvider,
    AuthenticationResolver,
    DatabricksHttpxAuth,
    configure_connection_pooling,
)

__all__ = [
    "AuthManager",
    "AuthProvider",
    "AuthenticationResolver",
    "DatabricksHttpxAuth",
    "configure_connection_pooling",
]

