"""Databricks connectors — enterprise auth, identity, and hybrid API hub.

Public API is re-exported here. Prefer::

    from shared_library.databricks_connectors import get_hub, ConnectorHub
"""

from __future__ import annotations

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
from shared_library.databricks_connectors.hub import (
    ConnectorHub,
    get_current_identity,
    get_hub,
    hub_identity_ready,
    reset_default_hub,
)
from shared_library.databricks_connectors.utils.env_reader import (
    EnvironmentConfig,
    resolve_config_dir,
    resolve_env_profile,
)
from shared_library.databricks_connectors.utils.exceptions import (
    AuthError,
    ConnectorError,
    IdentityError,
    RateLimitError,
    RestError,
)
from shared_library.databricks_connectors.utils.retry import execute_with_full_jitter
from shared_library.databricks_connectors.utils.log_redaction import (
    SensitiveDataRedactor,
    install_databricks_log_redaction,
    redact_secrets,
)

__all__ = [
    "AuthError",
    "AuthManager",
    "AuthProvider",
    "AuthenticationResolver",
    "ConciergeContext",
    "ConnectorError",
    "ConnectorHub",
    "DatabricksHttpxAuth",
    "EnvironmentConfig",
    "IdentityError",
    "IdentityManager",
    "IdentitySnapshot",
    "RateLimitError",
    "RestError",
    "SensitiveDataRedactor",
    "UserIdentity",
    "WorkspaceUserMetadata",
    "execute_with_full_jitter",
    "get_current_identity",
    "get_hub",
    "get_verified_user_from_headers",
    "hub_identity_ready",
    "install_databricks_log_redaction",
    "redact_secrets",
    "reset_default_hub",
    "resolve_config_dir",
    "resolve_env_profile",
    "resolve_identity",
]

