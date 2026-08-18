"""Identity translation, Full Metadata verification, and Concierge handoff."""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Mapping, Optional

from databricks.sdk import WorkspaceClient
from databricks.sdk.core import Config

from shared_library.databricks_connectors.utils.env_reader import EnvironmentConfig
from shared_library.databricks_connectors.utils.exceptions import AuthError, IdentityError

logger = logging.getLogger("databricks_connectors.identity")


@dataclass(frozen=True)
class WorkspaceUserMetadata:
    """Authoritative user + workspace profile (SCIM + routing context)."""

    user_id: Optional[str]
    user_name: Optional[str]
    display_name: Optional[str]
    emails: List[str] = field(default_factory=list)
    entitlements: List[str] = field(default_factory=list)
    groups: List[str] = field(default_factory=list)
    is_service_principal: bool = False
    active: bool = True
    workspace_id: Optional[str] = None
    workspace_host: Optional[str] = None
    environment: Optional[str] = None

    @property
    def id(self) -> Optional[str]:
        return self.user_id

    def has_entitlement(self, entitlement: str) -> bool:
        return entitlement in self.entitlements

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.user_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "display_name": self.display_name,
            "emails": list(self.emails),
            "entitlements": list(self.entitlements),
            "groups": list(self.groups),
            "is_service_principal": self.is_service_principal,
            "active": self.active,
            "workspace_id": self.workspace_id,
            "workspace_host": self.workspace_host,
            "environment": self.environment,
        }

    def to_dict(self) -> dict[str, Any]:
        return self.as_dict()


IdentitySnapshot = WorkspaceUserMetadata
UserIdentity = WorkspaceUserMetadata


def _values_from_attr_list(raw: Any) -> List[str]:
    out: List[str] = []
    if not raw:
        return out
    for item in raw:
        value = getattr(item, "value", None)
        if value is None and isinstance(item, str):
            value = item
        if value is not None:
            out.append(str(value))
    return out


def _display_from_groups(raw: Any) -> List[str]:
    out: List[str] = []
    if not raw:
        return out
    for item in raw:
        display = getattr(item, "display", None) or getattr(item, "value", None)
        if display is None and isinstance(item, str):
            display = item
        if display is not None:
            out.append(str(display))
    return out


def _is_service_principal(user_name: Optional[str]) -> bool:
    if not user_name:
        return False
    return "@" not in user_name


def _workspace_id_from_client(workspace_client: WorkspaceClient) -> Optional[str]:
    getter = getattr(workspace_client, "get_workspace_id", None)
    if callable(getter):
        try:
            value = getter()
            return str(value) if value is not None else None
        except Exception:  # noqa: BLE001
            logger.debug("get_workspace_id() failed", exc_info=True)
    return os.environ.get("DATABRICKS_WORKSPACE_ID")


def resolve_identity(
    workspace_client: WorkspaceClient,
    *,
    workspace_host: Optional[str] = None,
    workspace_id: Optional[str] = None,
    environment: Optional[str] = None,
) -> WorkspaceUserMetadata:
    """Full Metadata via ``current_user.me()``."""
    try:
        me_info = workspace_client.current_user.me()
    except Exception as exc:
        raise IdentityError(f"current_user.me() failed: {exc}") from exc

    user_name = getattr(me_info, "user_name", None)
    resolved_ws_id = workspace_id or _workspace_id_from_client(workspace_client)
    meta = WorkspaceUserMetadata(
        user_id=getattr(me_info, "id", None),
        user_name=user_name,
        display_name=getattr(me_info, "display_name", None),
        emails=_values_from_attr_list(getattr(me_info, "emails", None)),
        entitlements=_values_from_attr_list(getattr(me_info, "entitlements", None)),
        groups=_display_from_groups(getattr(me_info, "groups", None)),
        is_service_principal=_is_service_principal(user_name),
        active=bool(getattr(me_info, "active", True)),
        workspace_id=resolved_ws_id,
        workspace_host=workspace_host,
        environment=environment,
    )
    logger.info(
        "Resolved identity user_name=%s id=%s workspace_id=%s entitlements=%s",
        meta.user_name,
        meta.user_id,
        meta.workspace_id,
        len(meta.entitlements),
    )
    return meta


@dataclass(frozen=True)
class ConciergeContext:
    """Audit payload after OBO validation — hand long work to SP hub."""

    user: WorkspaceUserMetadata
    task_allowed: bool = True

    def audit_dict(self) -> Dict[str, Any]:
        payload = self.user.as_dict()
        payload["task_allowed"] = self.task_allowed
        return payload


class IdentityManager:
    """Request-scoped identity extraction and verification."""

    def __init__(
        self,
        host: Optional[str] = None,
        *,
        env: Optional[EnvironmentConfig] = None,
        timeout_seconds: Optional[int] = None,
    ) -> None:
        self.env = env or EnvironmentConfig()
        self.host = (host or self.env.host or "").rstrip("/")
        self.timeout_seconds = (
            timeout_seconds if timeout_seconds is not None else self.env.http_timeout_seconds
        )
        self._identity_cache: Dict[str, WorkspaceUserMetadata] = {}

    def extract_token_from_headers(self, headers: Mapping[str, str]) -> str:
        return self.extract_obo_token_from_headers(headers)

    def extract_obo_token_from_headers(self, headers: Mapping[str, str]) -> str:
        normalized = {str(k).lower(): v for k, v in headers.items()}
        token = normalized.get("x-forwarded-access-token")
        if not token:
            raise AuthError(
                "Missing 'X-Forwarded-Access-Token'. "
                "Enable User Authorization (OBO) in Databricks Apps settings."
            )
        if token.lower().startswith("bearer "):
            token = token[7:].strip()
        if not token:
            raise AuthError("Empty OBO access token in forwarded headers")
        return token

    def resolve_active_token(self, headers: Optional[Mapping[str, str]] = None) -> str:
        """Local U2M via Config token cache; Apps via forwarded header."""
        if self.env.is_local:
            if headers:
                normalized = {str(k).lower(): v for k, v in headers.items()}
                if normalized.get("x-forwarded-access-token"):
                    return self.extract_obo_token_from_headers(headers)
            try:
                from shared_library.databricks_connectors.utils.cli_token_cache import (
                    get_cached_cli_oauth_token,
                )

                access = get_cached_cli_oauth_token(
                    host=self.host or None,
                    profile=self.env.config_profile,
                    http_timeout_seconds=self.timeout_seconds,
                )
                if access:
                    return access
            except Exception as exc:
                raise AuthError(
                    f"Local CLI credential resolution failed: {exc}. "
                    "Run 'databricks auth login'."
                ) from exc
            raise AuthError("Local CLI credential resolution returned no access_token")

        if not headers:
            raise AuthError("Deployed OBO requires request headers")
        return self.extract_obo_token_from_headers(headers)

    def create_user_client(self, token: str) -> WorkspaceClient:
        """Isolated request-scoped client — never writes DATABRICKS_TOKEN to env."""
        return self.create_user_scoped_client(token)

    def create_user_scoped_client(self, token: str) -> WorkspaceClient:
        if not self.host:
            raise AuthError("DATABRICKS_HOST / ops host required for OBO client")
        config = Config(
            host=self.host,
            token=token,
            http_timeout_seconds=self.timeout_seconds,
            connection_pool_size=10,
        )
        return WorkspaceClient(config=config)

    def fetch_verified_identity(
        self,
        client: WorkspaceClient,
        *,
        force_refresh: bool = False,
    ) -> WorkspaceUserMetadata:
        return self.resolve_identity(client, force_refresh=force_refresh)

    def resolve_identity(
        self,
        client: WorkspaceClient,
        force_refresh: bool = False,
    ) -> WorkspaceUserMetadata:
        cache_key = getattr(getattr(client, "config", None), "token", None)
        if cache_key and cache_key in self._identity_cache and not force_refresh:
            return self._identity_cache[cache_key]

        identity = resolve_identity(
            client,
            workspace_host=self.host or None,
            workspace_id=self.env.workspace_id,
            environment=self.env.env_profile,
        )
        if cache_key:
            self._identity_cache[cache_key] = identity
        return identity

    def authorize_long_running_task(
        self,
        client: WorkspaceClient,
        required_entitlement: Optional[str] = None,
    ) -> WorkspaceUserMetadata:
        """Concierge validation: verify OBO user before SP handoff."""
        identity = self.resolve_identity(client)
        if required_entitlement and not identity.has_entitlement(required_entitlement):
            raise PermissionError(
                f"User '{identity.user_name}' is not authorized. "
                f"Missing entitlement '{required_entitlement}'."
            )
        logger.info(
            "OBO caller '%s' validated for long-running task handoff",
            identity.user_name,
        )
        return identity

    @contextmanager
    def user_session(
        self,
        token: str,
    ) -> Iterator[tuple[WorkspaceClient, WorkspaceUserMetadata]]:
        """Request-scoped client + Full Metadata; closes session on exit."""
        client = self.create_user_scoped_client(token)
        try:
            identity = self.resolve_identity(client)
            yield client, identity
        finally:
            session = getattr(getattr(client, "api_client", None), "_session", None)
            if session is not None:
                try:
                    session.close()
                except Exception:  # noqa: BLE001
                    logger.debug("user_session session close failed", exc_info=True)

    def build_concierge_context(
        self,
        token: str,
        *,
        required_entitlements: Optional[List[str]] = None,
    ) -> ConciergeContext:
        """Validate OBO user then return audit payload for SP handoff."""
        with self.user_session(token) as (_client, identity):
            allowed = True
            if required_entitlements:
                allowed = all(identity.has_entitlement(e) for e in required_entitlements)
            return ConciergeContext(user=identity, task_allowed=allowed)


def get_verified_user_from_headers(
    headers: Mapping[str, str],
    *,
    host: Optional[str] = None,
) -> WorkspaceUserMetadata:
    """Convenience Full Metadata gate from Apps proxy headers."""
    manager = IdentityManager(host=host)
    token = manager.extract_obo_token_from_headers(headers)
    with manager.user_session(token) as (_client, identity):
        return identity

