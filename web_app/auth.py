"""
User Authentication & SSO Identity Management

Handles extraction of user identity from Databricks SSO headers and provisioning.
Single source of truth for current user context (replaces duplicate logic in api.py).

Security Rules (per auth.md):
- x-forwarded-access-token is ephemeral; NEVER cache in session or DB
- X-Forwarded-* headers are injected by Databricks L7 proxy
- User auto-provisioning happens on first login
- All data operations filter by LOWER(owner_email) for tenant isolation
"""

from typing import Optional

from flask import current_app, request
from sqlalchemy import select
from sqlalchemy.orm import scoped_session

from . import database
from .models import User


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
    
    Fallback (local dev): Returns first user in DB if no SSO headers present.
    
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
        # Normalize to lowercase for case-insensitive email matching
        identifier_normalized = identifier.lower()
        existing = session.execute(
            select(User).where(User.email == identifier_normalized)
        ).scalar_one_or_none()
        if existing is not None:
            return existing

        # Auto-provision new user from SSO headers
        user_name = identifier.split("@")[0] if "@" in identifier else identifier
        display_name = preferred_username or user_name
        parts = display_name.split() if display_name else []
        given_name = parts[0] if parts else user_name
        family_name = parts[-1] if len(parts) > 1 else ""

        provisioned = User(
            user_name=user_name,
            email=identifier_normalized,  # Store normalized
            display_name=display_name,
            given_name=given_name,
            family_name=family_name,
            active=True,
            groups=[],
            entitlements=[],
        )
        session.add(provisioned)
        session.commit()
        current_app.logger.info(
            "Auto-provisioned user from SSO headers: %s", identifier_normalized
        )
        return provisioned

    # 3. Fallback (local dev): return first user in DB
    fallback = session.execute(select(User).order_by(User.id)).scalars().first()
    if fallback:
        current_app.logger.debug("No SSO headers; using fallback user: %s", fallback.email)
    return fallback
