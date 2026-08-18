"""Optional framework integrations for databricks_connectors."""

from __future__ import annotations

__all__: list[str] = []

try:
    from shared_library.databricks_connectors.integrations.fastapi_deps import (
        AuthenticatedUser,
        DatabricksSecurityManager,
        get_obo_token,
        get_sp_client,
        get_verified_user_context,
        verified_user,
    )

    __all__ = [
        "AuthenticatedUser",
        "DatabricksSecurityManager",
        "get_obo_token",
        "get_sp_client",
        "get_verified_user_context",
        "verified_user",
    ]
except ImportError:
    pass

