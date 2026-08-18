"""FastAPI dependencies for Databricks OBO identity + Concierge SP handoff.

Soft-imports FastAPI so the shared library remains usable without it.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generator, List, Optional

from databricks.sdk import WorkspaceClient

from shared_library.databricks_connectors.core.auth import AuthProvider
from shared_library.databricks_connectors.core.identity import (
    IdentityManager,
    WorkspaceUserMetadata,
)
from shared_library.databricks_connectors.hub import get_hub
from shared_library.databricks_connectors.utils.env_reader import EnvironmentConfig
from shared_library.databricks_connectors.utils.exceptions import AuthError, IdentityError

logger = logging.getLogger("databricks_connectors.fastapi_deps")

try:
    from fastapi import Depends, Header, HTTPException, Request
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
except ImportError as _fastapi_exc:  # pragma: no cover
    Depends = None  # type: ignore[assignment]
    Header = None  # type: ignore[assignment]
    HTTPException = None  # type: ignore[assignment]
    Request = None  # type: ignore[assignment]
    HTTPAuthorizationCredentials = None  # type: ignore[assignment]
    HTTPBearer = None  # type: ignore[assignment]
    _FASTAPI_IMPORT_ERROR = _fastapi_exc
else:
    _FASTAPI_IMPORT_ERROR = None

if TYPE_CHECKING:
    from fastapi import Request as FastAPIRequest


def _require_fastapi() -> None:
    if _FASTAPI_IMPORT_ERROR is not None:
        raise ImportError(
            "fastapi is required for databricks_connectors.integrations.fastapi_deps. "
            "Install fastapi (already in agent_server requirements)."
        ) from _FASTAPI_IMPORT_ERROR


@dataclass
class AuthenticatedUser:
    """Request-scoped security envelope (Full Metadata + isolated client)."""

    identity: WorkspaceUserMetadata
    user_client: WorkspaceClient

    @property
    def email(self) -> Optional[str]:
        if self.identity.emails:
            return self.identity.emails[0]
        return self.identity.user_name

    @property
    def display_name(self) -> Optional[str]:
        return self.identity.display_name

    @property
    def user_id(self) -> Optional[str]:
        return self.identity.user_id

    @property
    def entitlements(self) -> List[str]:
        return list(self.identity.entitlements)

    def has_entitlement(self, entitlement: str) -> bool:
        return self.identity.has_entitlement(entitlement)

    def to_dict(self) -> dict[str, Any]:
        return self.identity.to_dict()


class DatabricksSecurityManager:
    """FastAPI-oriented security manager (local U2M + Apps OBO + Concierge)."""

    def __init__(self, env: Optional[EnvironmentConfig] = None) -> None:
        self.env = env or EnvironmentConfig()
        self.host = self.env.host
        self.timeout_seconds = self.env.http_timeout_seconds
        self.identity_manager = IdentityManager(host=self.host, env=self.env)
        self.auth = AuthProvider(env=self.env, http_timeout_seconds=self.timeout_seconds)
        self._bearer = HTTPBearer(auto_error=False) if HTTPBearer is not None else None

    @property
    def global_app_client(self) -> WorkspaceClient:
        """Long-lived SP / profile client for Concierge handoff."""
        return get_hub().workspace_client

    def extract_obo_token(
        self,
        request: Any,
        credentials: Optional[Any] = None,
    ) -> str:
        _require_fastapi()
        assert HTTPException is not None

        header_token = request.headers.get("x-forwarded-access-token") or request.headers.get(
            "X-Forwarded-Access-Token"
        )
        if header_token:
            if header_token.lower().startswith("bearer "):
                header_token = header_token[7:].strip()
            return header_token

        if credentials is not None and getattr(credentials, "credentials", None):
            return str(credentials.credentials)

        if self.env.is_local:
            try:
                from shared_library.databricks_connectors.utils.cli_token_cache import (
                    get_cached_cli_oauth_token,
                    peek_cached_cli_oauth_token,
                )

                access = peek_cached_cli_oauth_token(
                    host=self.host,
                    profile=self.env.config_profile or "DEFAULT",
                )
                if not access:
                    access = get_cached_cli_oauth_token(
                        host=self.host,
                        profile=self.env.config_profile or "DEFAULT",
                        http_timeout_seconds=self.timeout_seconds,
                        refresh_timeout_seconds=8.0,
                    )
                if access:
                    return access
            except Exception as exc:
                raise HTTPException(
                    status_code=401,
                    detail=f"Local CLI token resolution failed: {exc}. Run 'databricks auth login'.",
                ) from exc

        raise HTTPException(
            status_code=401,
            detail=(
                "Unauthorized: Missing On-Behalf-Of credentials in "
                "'X-Forwarded-Access-Token' or Authorization Bearer header."
            ),
        )

    def create_user_client(self, token: str) -> WorkspaceClient:
        if not self.host:
            raise AuthError("DATABRICKS_HOST required for OBO client")
        return self.auth.create_obo_client(self.host, token)

    def verify_user(self, user_client: WorkspaceClient) -> WorkspaceUserMetadata:
        return self.identity_manager.resolve_identity(user_client)

    def authorize_long_running_task(
        self,
        user: AuthenticatedUser,
        required_entitlement: Optional[str] = None,
    ) -> WorkspaceClient:
        """Concierge: validate entitlements, return SP client (drop OBO token)."""
        _require_fastapi()
        assert HTTPException is not None
        if required_entitlement and not user.has_entitlement(required_entitlement):
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Forbidden: User '{user.display_name}' lacks "
                    f"required entitlement '{required_entitlement}'."
                ),
            )
        logger.info(
            "User '%s' authorized; handing off to Service Principal / profile hub",
            user.identity.user_name,
        )
        return self.global_app_client


_security_manager: Optional[DatabricksSecurityManager] = None
_security_manager_error: Optional[tuple[float, Exception]] = None  # (timestamp, exception) for cooldown


def get_security_manager(*, cooldown_seconds: float = 30.0) -> DatabricksSecurityManager:
    """Get or build the security manager, with failure memoization."""
    global _security_manager, _security_manager_error
    import time
    
    # If we have a cached instance, return it
    if _security_manager is not None:
        return _security_manager
    
    # If we recently failed, re-raise within cooldown window
    if _security_manager_error is not None:
        error_time, error = _security_manager_error
        if time.time() - error_time < cooldown_seconds:
            raise error
        # Cooldown expired; forget the error and try again
        _security_manager_error = None
    
    try:
        _security_manager = DatabricksSecurityManager()
        return _security_manager
    except Exception as e:
        # Memoize the failure with a timestamp
        _security_manager_error = (time.time(), e)
        raise


def reset_security_manager() -> None:
    """Test helper."""
    global _security_manager, _security_manager_error
    _security_manager = None
    _security_manager_error = None


def get_obo_token(
    request: Any,
    x_forwarded_access_token: Optional[str] = None,
    credentials: Optional[Any] = None,
) -> str:
    """Extract OBO token (usable as FastAPI Depends with Header/Bearer)."""
    _require_fastapi()
    mgr = get_security_manager()
    # Prefer injected Header value when provided by FastAPI
    if x_forwarded_access_token:
        token = x_forwarded_access_token
        if token.lower().startswith("bearer "):
            token = token[7:].strip()
        return token
    return mgr.extract_obo_token(request, credentials)


def get_verified_user_context(
    request: Any = None,
    token: Optional[str] = None,
) -> Generator[AuthenticatedUser, None, None]:
    """
    Full Metadata validation dependency.

    Prefer wiring via::

        user: AuthenticatedUser = Depends(verified_user_dependency)
    """
    _require_fastapi()
    assert HTTPException is not None

    mgr = get_security_manager()
    if token is None:
        if request is None:
            raise HTTPException(status_code=401, detail="Missing request for OBO extraction")
        token = mgr.extract_obo_token(request)

    user_client = mgr.create_user_client(token)
    try:
        try:
            identity = mgr.verify_user(user_client)
        except (AuthError, IdentityError) as exc:
            logger.error("Control plane identity validation failed: %s", exc)
            raise HTTPException(
                status_code=401,
                detail="Unauthorized: Invalid, expired, or revoked access token.",
            ) from exc
        yield AuthenticatedUser(identity=identity, user_client=user_client)
    finally:
        session = getattr(getattr(user_client, "api_client", None), "_session", None)
        if session is not None:
            try:
                session.close()
            except Exception:  # noqa: BLE001
                logger.debug("OBO session close failed", exc_info=True)


def verified_user_dependency(
    request: Any,
    x_forwarded_access_token: Optional[str] = None,
) -> Generator[AuthenticatedUser, None, None]:
    """FastAPI-friendly Depends entrypoint."""
    _require_fastapi()
    token = get_obo_token(request, x_forwarded_access_token=x_forwarded_access_token)
    yield from get_verified_user_context(request=request, token=token)


def get_sp_client() -> WorkspaceClient:
    """Process SP / profile WorkspaceClient (Concierge marathon runner)."""
    return get_hub().workspace_client


# Bind Header defaults only when FastAPI is present (for route Depends)
if Header is not None and Depends is not None:

    def _verified_user_route_dep(
        request: Request,  # type: ignore[valid-type]
        x_forwarded_access_token: Optional[str] = Header(
            None, alias="X-Forwarded-Access-Token"
        ),
    ) -> Generator[AuthenticatedUser, None, None]:
        yield from verified_user_dependency(request, x_forwarded_access_token)

    verified_user = _verified_user_route_dep
else:  # pragma: no cover
    verified_user = verified_user_dependency  # type: ignore[assignment]

