"""
User Authentication & SSO Identity Management

Handles extraction of user identity from Databricks SSO headers and provisioning.
Single source of truth for current user context (replaces duplicate logic in api.py).

Security Rules (per auth.md):
- x-forwarded-access-token is ephemeral; NEVER cache in session or DB
- X-Forwarded-* headers are injected by Databricks L7 proxy
- User auto-provisioning happens on first login
- All data operations filter by LOWER(owner_email) for tenant isolation

Identity resolution order:
1. Databricks SSO headers (X-Forwarded-Email / X-Forwarded-User) — production
2. Databricks CLI / local U2M identity via current_user.me() — local dev
3. First user in DB — last-resort fallback only if CLI auth is unavailable
"""

import os
import threading
from typing import Any, Optional

from flask import current_app, has_app_context, request
from sqlalchemy import select
from sqlalchemy.orm import scoped_session

from . import database
from .models import User

# Cached local-dev identity resolved from the Databricks CLI profile.
# current_user.me() is a network round-trip, so it must not run per request.
_CLI_IDENTITY: Optional[dict] = None
_CLI_IDENTITY_RESOLVED = False
_CLI_IDENTITY_LOCK = threading.Lock()


def _log(level: str, msg: str, *args: Any) -> None:
    """Log via Flask app logger when available, else stay silent."""
    if has_app_context():
        getattr(current_app.logger, level)(msg, *args)


def reset_cli_identity_cache() -> None:
    """Clear the cached CLI identity (used by tests and profile switches)."""
    global _CLI_IDENTITY, _CLI_IDENTITY_RESOLVED
    with _CLI_IDENTITY_LOCK:
        _CLI_IDENTITY = None
        _CLI_IDENTITY_RESOLVED = False


def _is_deployed() -> bool:
    """
    True when running inside Databricks Apps.

    In that environment the only non-header identity available is the app's
    service principal, which must NEVER be treated as the end user.
    """
    return bool(
        os.getenv("DATABRICKS_APP_NAME")
        or os.getenv("DATABRICKS_APP_URL")
        or (os.getenv("DATABRICKS_CLIENT_ID") and os.getenv("DATABRICKS_CLIENT_SECRET"))
    )


def _scim_values(raw: Any) -> list[str]:
    """Flatten a SCIM multi-valued attribute list to plain strings."""
    out: list[str] = []
    for item in raw or []:
        value = getattr(item, "display", None) or getattr(item, "value", None)
        if value is None and isinstance(item, str):
            value = item
        if value is not None:
            out.append(str(value))
    return out


def _identity_from_scim(me: Any) -> Optional[dict]:
    """
    Map a SCIM ``current_user.me()`` response to provisioning fields.

    Returns None for service principals (user_name has no ``@``), since an SP
    is an app identity, not a human user.
    """
    user_name = getattr(me, "user_name", None)
    if not user_name or "@" not in user_name:
        return None

    name = getattr(me, "name", None)
    given_name = getattr(name, "given_name", None) if name else None
    family_name = getattr(name, "family_name", None) if name else None
    display_name = (
        getattr(me, "display_name", None)
        or (getattr(name, "formatted", None) if name else None)
        or user_name.split("@")[0]
    )

    return {
        "email": user_name.lower(),
        "user_name": user_name.split("@")[0],
        "display_name": display_name,
        "given_name": given_name or display_name.split()[0],
        "family_name": family_name or "",
        "groups": _scim_values(getattr(me, "groups", None)),
        "entitlements": _scim_values(getattr(me, "entitlements", None)),
    }


def _resolve_cli_identity() -> Optional[dict]:
    """
    Resolve the developer's identity from local Databricks CLI credentials.

    Uses the same client resolver as the rest of the app (CLI profile from
    DATABRICKS_CONFIG_PROFILE / ops config, else interactive browser), then
    calls ``current_user.me()``.

    The result — including a negative result — is cached for the process so a
    broken or missing CLI login does not stall every request.
    """
    global _CLI_IDENTITY, _CLI_IDENTITY_RESOLVED

    if _CLI_IDENTITY_RESOLVED:
        return _CLI_IDENTITY

    with _CLI_IDENTITY_LOCK:
        if _CLI_IDENTITY_RESOLVED:
            return _CLI_IDENTITY

        identity: Optional[dict] = None
        if _is_deployed():
            _log("debug", "Deployed environment; skipping CLI identity fallback")
        else:
            try:
                from .workspace_client import get_workspace_client_for_request

                ws = get_workspace_client_for_request()
                identity = _identity_from_scim(ws.current_user.me())
                if identity is None:
                    _log(
                        "warning",
                        "CLI credentials resolve to a service principal; "
                        "not usable as a user identity",
                    )
                else:
                    _log(
                        "info",
                        "Resolved local dev identity from Databricks CLI: %s",
                        identity["email"],
                    )
            except Exception as exc:  # noqa: BLE001
                _log(
                    "warning",
                    "Databricks CLI identity resolution failed (%s). "
                    "Run 'databricks auth login' to authenticate locally.",
                    exc,
                )

        _CLI_IDENTITY = identity
        _CLI_IDENTITY_RESOLVED = True
        return _CLI_IDENTITY


def _get_or_provision(session: scoped_session, fields: dict, source: str) -> Optional[User]:
    """
    Look up a user by normalized email, auto-provisioning on first sight.

    Args:
        session: active scoped session
        fields: output of _identity_from_scim or the SSO-header equivalent
        source: label for logs ("SSO headers" / "Databricks CLI")
    """
    email = fields["email"]
    existing = session.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    provisioned = User(
        user_name=fields.get("user_name"),
        email=email,
        display_name=fields.get("display_name"),
        given_name=fields.get("given_name"),
        family_name=fields.get("family_name") or "",
        active=True,
        groups=fields.get("groups") or [],
        entitlements=fields.get("entitlements") or [],
    )
    session.add(provisioned)
    try:
        session.commit()
    except Exception:  # noqa: BLE001 — concurrent insert on the unique email
        session.rollback()
        return session.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

    _log("info", "Auto-provisioned user from %s: %s", source, email)
    return provisioned


def get_forwarded_access_token() -> Optional[str]:
    """
    Extract the current user's OAuth token from x-forwarded-access-token header.
    
    This token is injected by Databricks L7 proxy and enables "on-behalf-of" (OBO)
    WorkspaceClient operations that inherit the user's Unity Catalog permissions.
    
    SECURITY: This token is request-scoped and ephemeral. NEVER cache in session
    cookies or database. Always extract from headers for each request that needs it.
    
    Returns:
        str | None: OAuth token if present in request, None otherwise (e.g., local dev)
    """
    return request.headers.get("x-forwarded-access-token")


def get_current_user() -> Optional[User]:
    """
    Resolve the current authenticated user from Databricks SSO headers.
    
    Single source of truth for user identity. Automatically provisions new users
    on first login based on X-Forwarded-* headers injected by Databricks L7 proxy.
    
    Fallback (local dev): resolves the developer's identity from the Databricks
    CLI (``current_user.me()`` over the cached CLI/U2M credentials) and
    provisions that user, so local dev runs as the logged-in developer rather
    than an arbitrary seeded row.

    Returns:
        User | None: Authenticated user object, or None if no context available
    """
    session: Optional[scoped_session] = database.db_session
    if session is None:
        return None

    # 1. Extract identity from SSO headers (injected by Databricks L7 proxy)
    forwarded_email = request.headers.get("X-Forwarded-Email")
    forwarded_user = request.headers.get("X-Forwarded-User")
    preferred_username = request.headers.get("X-Forwarded-Preferred-Username")

    identifier = forwarded_email or forwarded_user

    # 2. If headers present, check for existing user or auto-provision
    if identifier:
        user_name = identifier.split("@")[0] if "@" in identifier else identifier
        display_name = preferred_username or user_name
        parts = display_name.split() if display_name else []
        return _get_or_provision(
            session,
            {
                "email": identifier.lower(),  # Normalized for case-insensitive match
                "user_name": user_name,
                "display_name": display_name,
                "given_name": parts[0] if parts else user_name,
                "family_name": parts[-1] if len(parts) > 1 else "",
                "groups": [],
                "entitlements": [],
            },
            "SSO headers",
        )

    # 3. Local dev: fall back to Databricks CLI auth identity.
    # Never reached in Databricks Apps — SSO headers are always injected there,
    # and _resolve_cli_identity() refuses service-principal identities anyway.
    cli_identity = _resolve_cli_identity()
    if cli_identity:
        return _get_or_provision(session, cli_identity, "Databricks CLI")

    # 4. Last resort: first user in DB (CLI auth unavailable, e.g. offline dev).
    fallback = session.execute(select(User).order_by(User.id)).scalars().first()
    if fallback:
        current_app.logger.warning(
            "No SSO headers and no CLI identity; using first DB user: %s. "
            "Run 'databricks auth login' to run as yourself.",
            fallback.email,
        )
    else:
        current_app.logger.debug(
            "No SSO headers, no CLI identity, and no users in DB"
        )
    return fallback
