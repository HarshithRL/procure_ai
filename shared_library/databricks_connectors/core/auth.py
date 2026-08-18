"""Production authentication layer — UCA, httpx middleware, OIDC timeout hardening."""

from __future__ import annotations

import logging
import os
from typing import Any, Callable, Dict, Generator, Optional

import httpx
import urllib3
from databricks.sdk import AccountClient, WorkspaceClient
from databricks.sdk.core import Config

from shared_library.databricks_connectors.utils.env_reader import EnvironmentConfig
from shared_library.databricks_connectors.utils.exceptions import AuthError

logger = logging.getLogger("databricks_connectors.auth")

_DEFAULT_POOL_SIZE = 100


class DatabricksHttpxAuth(httpx.Auth):
    """Bridge SDK ``authenticate()`` into sync/async httpx clients."""

    def __init__(self, authenticate_callback: Callable[[], Dict[str, str]]) -> None:
        self.authenticate_callback = authenticate_callback

    def auth_flow(self, request: httpx.Request) -> Generator[httpx.Request, httpx.Response, None]:
        headers = self.authenticate_callback()
        for key, value in headers.items():
            request.headers[key] = value
        yield request


def configure_connection_pooling(pool_size: int = _DEFAULT_POOL_SIZE) -> None:
    """Bound urllib3 defaults and expand retry verbs for agent write paths.

    SDK ``Config(connection_pool_size=...)`` is the primary pool lever for
    WorkspaceClient; this also sets process-level urllib3 defaults so
    background retries and shared sessions respect the configured ceiling.
    """
    size = max(1, int(pool_size))
    urllib3.util.Retry.DEFAULT_ALLOWED_METHODS = frozenset(
        urllib3.util.Retry.DEFAULT_ALLOWED_METHODS | {"POST", "PATCH", "DELETE"}
    )
    # urllib3 >=2 uses DEFAULT_POOLSIZE on PoolManager; set both for compatibility
    try:
        urllib3.poolmanager.PoolManager.DEFAULT_POOLSIZE = size  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        logger.debug("Could not set PoolManager.DEFAULT_POOLSIZE", exc_info=True)
    try:
        urllib3.connectionpool.HTTPConnectionPool.default_pool_timeout = None
    except Exception:  # noqa: BLE001
        pass
    logger.debug("Connection pooling configured pool_size=%s", size)


class AuthProvider:
    """Centralized auth + Config manager (environment-aware UCA).

    Also exposes AuthManager-style factory methods from the enterprise blueprint.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        profile: Optional[str] = None,
        token: Optional[str] = None,
        account_id: Optional[str] = None,
        *,
        env: Optional[EnvironmentConfig] = None,
        connection_pool_size: Optional[int] = None,
        http_timeout_seconds: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        self.env = env or EnvironmentConfig()
        self.default_timeout = (
            http_timeout_seconds
            if http_timeout_seconds is not None
            else self.env.http_timeout_seconds
        )
        pool = (
            connection_pool_size
            if connection_pool_size is not None
            else self.env.connection_pool_size
        )
        self.config = self.resolve_environment_config(
            host=host,
            profile=profile,
            token=token,
            account_id=account_id,
            connection_pool_size=pool,
            http_timeout_seconds=self.default_timeout,
            **kwargs,
        )

        configure_connection_pooling(pool)
        self._pool_size = pool
        self._is_obo = token is not None

        logger.info(
            "AuthProvider ready host=%s auth_type=%s obo=%s profile_env=%s "
            "http_timeout_seconds=%s connection_pool_size=%s",
            getattr(self.config, "host", None),
            getattr(self.config, "auth_type", None),
            self._is_obo,
            self.env.env_profile,
            self.default_timeout,
            self._pool_size,
        )

    def resolve_environment_config(
        self,
        host: Optional[str] = None,
        profile: Optional[str] = None,
        token: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        account_id: Optional[str] = None,
        **kwargs: Any,
    ) -> Config:
        """Build an isolated ``Config`` without mutating ``os.environ``."""
        config_kwargs = self.env.sdk_config_kwargs(
            host=host,
            profile=profile,
            token=token,
            account_id=account_id,
            **kwargs,
        )
        # Explicit SP credentials (Apps / M2M) when provided
        resolved_client_id = client_id or os.getenv("DATABRICKS_CLIENT_ID")
        resolved_client_secret = client_secret or os.getenv("DATABRICKS_CLIENT_SECRET")
        if token is None and resolved_client_id and resolved_client_secret and not self.env.is_local:
            config_kwargs.setdefault("client_id", resolved_client_id)
            config_kwargs.setdefault("client_secret", resolved_client_secret)

        try:
            return Config(**config_kwargs)
        except Exception as exc:
            raise AuthError(f"Failed to build Databricks Config: {exc}") from exc

    def create_workspace_client(self, config: Optional[Config] = None) -> WorkspaceClient:
        """Instantiate an isolated WorkspaceClient."""
        try:
            return WorkspaceClient(config=config or self.config)
        except Exception as exc:
            raise AuthError(f"WorkspaceClient init failed: {exc}") from exc

    def create_account_client(self, config: Optional[Config] = None) -> AccountClient:
        """Instantiate AccountClient; requires account_id on config or env."""
        cfg = config or self.config
        account_id = getattr(cfg, "account_id", None) or os.getenv("DATABRICKS_ACCOUNT_ID")
        if not account_id:
            raise AuthError(
                "AccountClient requires account_id or DATABRICKS_ACCOUNT_ID"
            )
        if not getattr(cfg, "account_id", None):
            # Rebuild with account_id rather than mutating shared config in place
            cfg = self.resolve_environment_config(
                host=getattr(cfg, "host", None),
                account_id=account_id,
                http_timeout_seconds=self.default_timeout,
            )
        try:
            return AccountClient(config=cfg)
        except Exception as exc:
            raise AuthError(f"AccountClient init failed: {exc}") from exc

    def create_obo_client(self, host: str, user_token: str) -> WorkspaceClient:
        """Request-scoped OBO WorkspaceClient (isolated pool)."""
        if not host or not user_token:
            raise AuthError("create_obo_client requires host and user_token")
        config = Config(
            host=host.rstrip("/"),
            token=user_token,
            http_timeout_seconds=self.default_timeout,
            connection_pool_size=10,
        )
        return WorkspaceClient(config=config)

    def get_config(self) -> Config:
        return self.config

    def get_auth_headers(self) -> Dict[str, str]:
        try:
            headers = self.config.authenticate()
        except Exception as exc:
            raise AuthError(f"authenticate() failed: {exc}") from exc
        if not isinstance(headers, dict):
            raise AuthError(f"authenticate() returned {type(headers).__name__}, expected dict")
        return headers

    def get_sync_httpx_client(self) -> httpx.Client:
        auth = DatabricksHttpxAuth(self.config.authenticate)
        limits = httpx.Limits(
            max_keepalive_connections=20,
            max_connections=self._pool_size,
        )
        return httpx.Client(auth=auth, base_url=self.config.host, limits=limits)

    def get_async_httpx_client(self) -> httpx.AsyncClient:
        auth = DatabricksHttpxAuth(self.config.authenticate)
        limits = httpx.Limits(
            max_keepalive_connections=20,
            max_connections=self._pool_size,
        )
        return httpx.AsyncClient(auth=auth, base_url=self.config.host, limits=limits)

    @classmethod
    def from_env(cls, **kwargs: Any) -> "AuthProvider":
        return cls(**kwargs)

    @classmethod
    def from_obo_token(
        cls,
        token: str,
        host: Optional[str] = None,
        **kwargs: Any,
    ) -> "AuthProvider":
        if not token or not str(token).strip():
            raise AuthError("OBO token must be a non-empty string")
        env = kwargs.pop("env", None) or EnvironmentConfig()
        return cls(
            host=host or env.host,
            token=str(token).strip(),
            env=env,
            connection_pool_size=kwargs.pop("connection_pool_size", 10),
            **kwargs,
        )


# Blueprint + backward-compatible aliases
AuthManager = AuthProvider
AuthenticationResolver = AuthProvider

