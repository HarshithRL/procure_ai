"""Enterprise ConnectorHub — hybrid SDK delegation + typo-safe ``.rest()``."""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, Optional

from databricks.sdk import AccountClient, WorkspaceClient
from databricks.sdk.core import DatabricksError

from shared_library.databricks_connectors.core.auth import AuthProvider, AuthenticationResolver
from shared_library.databricks_connectors.core.identity import (
    IdentityManager,
    WorkspaceUserMetadata,
    resolve_identity,
)
from shared_library.databricks_connectors.utils.env_reader import EnvironmentConfig
from shared_library.databricks_connectors.utils.exceptions import AuthError, IdentityError, RestError
from shared_library.databricks_connectors.utils.retry import execute_with_full_jitter

logger = logging.getLogger("databricks_connectors.hub")

_HUB_LOCK = threading.Lock()
_DEFAULT_HUB: Optional["ConnectorHub"] = None
_HUB_ERROR: Optional[tuple[float, Exception]] = None  # (timestamp, exception) for cooldown


class ConnectorHub:
    """Unified Databricks gateway: auth, identity, SDK services, explicit REST."""

    def __init__(
        self,
        provider: Optional[AuthProvider] = None,
        resolver: Optional[AuthProvider] = None,
        *,
        host: Optional[str] = None,
        profile: Optional[str] = None,
        token: Optional[str] = None,
        account_id: Optional[str] = None,
        env: Optional[EnvironmentConfig] = None,
        apply_ops: bool = True,
        is_obo: bool = False,
        **kwargs: Any,
    ) -> None:
        # apply_ops retained for API compatibility; EnvironmentConfig reads YAML directly
        _ = apply_ops
        auth = provider or resolver
        if auth is not None:
            self._auth = auth
        else:
            self._auth = AuthProvider(
                host=host,
                profile=profile,
                token=token,
                account_id=account_id,
                env=env,
                **kwargs,
            )

        self.env = self._auth.env
        self.config = self._auth.get_config()
        try:
            self._workspace = WorkspaceClient(config=self.config)
        except Exception as exc:
            raise AuthError(f"WorkspaceClient init failed: {exc}") from exc

        self._account: Optional[AccountClient] = None
        if getattr(self.config, "account_id", None):
            try:
                self._account = AccountClient(config=self.config)
            except Exception as exc:
                logger.warning("AccountClient unavailable: %s", exc)
                self._account = None

        self._identity_cache: Optional[WorkspaceUserMetadata] = None
        self._is_obo = bool(is_obo or token is not None or self._auth._is_obo)
        self.identity_manager = IdentityManager(
            host=getattr(self.config, "host", None) or self.env.host,
            env=self.env,
        )

        logger.info(
            "ConnectorHub bound host=%s obo=%s account=%s",
            getattr(self.config, "host", None),
            self._is_obo,
            self._account is not None,
        )

    @property
    def workspace_client(self) -> WorkspaceClient:
        return self._workspace

    @property
    def w(self) -> WorkspaceClient:
        return self._workspace

    @property
    def a(self) -> Optional[AccountClient]:
        return self._account

    def get_auth_headers(self) -> Dict[str, str]:
        return self._auth.get_auth_headers()

    def get_sync_httpx_client(self):
        return self._auth.get_sync_httpx_client()

    def get_async_httpx_client(self):
        return self._auth.get_async_httpx_client()

    def get_current_identity(self, force_refresh: bool = False) -> WorkspaceUserMetadata:
        if self._identity_cache is not None and not force_refresh:
            return self._identity_cache
        try:
            self._identity_cache = resolve_identity(
                self._workspace,
                workspace_host=getattr(self.config, "host", None),
                workspace_id=self.env.workspace_id,
                environment=self.env.env_profile,
            )
        except IdentityError:
            raise
        except Exception as exc:
            raise IdentityError(f"Failed to resolve session identity: {exc}") from exc
        return self._identity_cache

    def rest(
        self,
        method: str,
        path: str,
        *,
        body: Optional[Dict[str, Any]] = None,
        query: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        raw: bool = False,
        max_retries: int = 5,
    ) -> Any:
        """Explicit REST gateway (typo-safe — not used by ``__getattr__``)."""
        normalized = path if path.startswith("/") else f"/{path}"

        def _do() -> Any:
            try:
                return self._workspace.api_client.do(
                    method=method,
                    path=normalized,
                    headers=headers,
                    body=body,
                    query=query,
                    raw=raw,
                )
            except DatabricksError as exc:
                raise RestError(f"REST {method} {normalized} failed: {exc}") from exc

        return execute_with_full_jitter(_do, max_retries=max_retries)

    def __getattr__(self, name: str) -> Any:
        """Delegate to WorkspaceClient, then AccountClient. Never invent REST paths."""
        if name.startswith("_"):
            raise AttributeError(name)
        if hasattr(self._workspace, name):
            return getattr(self._workspace, name)
        if self._account is not None and hasattr(self._account, name):
            return getattr(self._account, name)
        raise AttributeError(
            f"'{type(self).__name__}' has no attribute '{name}'. "
            "Use hub.rest(method, path, ...) for unmapped/preview REST endpoints."
        )

    @classmethod
    def from_obo_token(
        cls,
        token: str,
        host: Optional[str] = None,
        **kwargs: Any,
    ) -> "ConnectorHub":
        provider = AuthProvider.from_obo_token(token, host=host, **kwargs)
        return cls(provider=provider, is_obo=True)

    as_obo = from_obo_token


def get_hub(*, force_new: bool = False, cooldown_seconds: float = 30.0, **kwargs: Any) -> ConnectorHub:
    """Process-level default hub (profile / Apps SP). Not used for OBO.

    Pass ``http_timeout_seconds`` / ``connection_pool_size`` / ``env`` through
    to ``AuthProvider`` when (re)building the singleton after ``reset_default_hub``.
    
    On construction failure, memoizes the error with a cooldown so repeated calls
    within ``cooldown_seconds`` re-raise immediately instead of retrying.
    """
    global _DEFAULT_HUB, _HUB_ERROR
    import time
    
    if force_new:
        return ConnectorHub(**kwargs)

    with _HUB_LOCK:
        # If we have a cached instance, return it
        if _DEFAULT_HUB is not None:
            return _DEFAULT_HUB
        
        # If we recently failed, re-raise within cooldown window
        if _HUB_ERROR is not None:
            error_time, error = _HUB_ERROR
            if time.time() - error_time < cooldown_seconds:
                raise error
            # Cooldown expired; forget the error and try again
            _HUB_ERROR = None
        
        try:
            _DEFAULT_HUB = ConnectorHub(**kwargs)
            return _DEFAULT_HUB
        except Exception as e:
            # Memoize the failure with a timestamp
            _HUB_ERROR = (time.time(), e)
            raise


def get_current_identity(force_refresh: bool = False) -> WorkspaceUserMetadata:
    return get_hub().get_current_identity(force_refresh=force_refresh)


def hub_identity_ready() -> bool:
    """True when the process hub has a cached identity from prewarm / prior me()."""
    hub = _DEFAULT_HUB
    if hub is None:
        return False
    return getattr(hub, "_identity_cache", None) is not None


def reset_default_hub() -> None:
    global _DEFAULT_HUB, _HUB_ERROR
    with _HUB_LOCK:
        _DEFAULT_HUB = None
        _HUB_ERROR = None


# Re-export alias used by older call sites
AuthenticationResolver = AuthProvider

