"""
Databricks WorkspaceClient Resolver

Implements dual-identity architecture per auth.md:
1. User Authorization (OBO): x-forwarded-access-token → U2M with UC permissions
2. App Authorization (SP): DATABRICKS_CLIENT_ID/SECRET → M2M system operations
3. Local Development: Interactive browser auth with caching

This module provides:
- get_workspace_client_for_request(): Resolves WorkspaceClient for a specific HTTP request
- get_app_client(): Module-level SP client singleton for background tasks
"""

import os
from functools import lru_cache
from typing import Optional

from databricks.sdk import WorkspaceClient


@lru_cache(maxsize=4)
def _get_cached_local_client(
    host: Optional[str] = None,
    profile: Optional[str] = None,
) -> WorkspaceClient:
    """
    Create a cached WorkspaceClient for local development.

    Resolution order:
      1. **CLI profile** — if `profile` is given (from DATABRICKS_CONFIG_PROFILE,
         or the `config_profile` key in ops/config/dev.yml), use the OAuth
         credentials already cached by `databricks auth login`. Non-interactive.
      2. **Interactive browser** — last resort; opens a browser tab the first
         time, then reuses ~/.databricks/token-cache.json.

    The @lru_cache decorator ensures repeated calls during local dev don't
    trigger multiple auth flows — the client is reused per (host, profile).

    Args:
        host: Databricks workspace hostname (e.g., https://adb-xxx.azuredatabricks.net/)
        profile: ~/.databrickscfg profile name, or None to skip profile auth

    Returns:
        WorkspaceClient: Authenticated client
    """
    if profile:
        # Let the SDK read host from the profile if none was supplied.
        kwargs = {"profile": profile}
        if host:
            kwargs["host"] = host
        return WorkspaceClient(**kwargs)

    return WorkspaceClient(host=host, auth_type="external-browser")


def _local_profile() -> Optional[str]:
    """
    Resolve the local-dev CLI profile name.

    Prefers the DATABRICKS_CONFIG_PROFILE env var, then falls back to the
    `databricks.config_profile` key in ops/config/{ENV_PROFILE}.yml so that a
    developer needs no exported env vars at all.

    Returns None if neither is set (caller then falls back to browser auth).
    """
    env_profile = os.getenv("DATABRICKS_CONFIG_PROFILE")
    if env_profile:
        return env_profile

    try:
        from shared_library.databricks_connectors.utils.env_reader import EnvironmentConfig

        return EnvironmentConfig().config_profile
    except Exception:
        # Config layer unavailable (e.g. trimmed deployment) — not fatal.
        return None


def _resolve_host() -> Optional[str]:
    """
    Resolve the Databricks workspace host.

    DATABRICKS_HOST (injected by Databricks Apps in production) wins; locally
    we fall back to ops/config/{ENV_PROFILE}.yml so no env var is required.
    Returning None lets the SDK resolve the host from the CLI profile itself.
    """
    env_host = os.getenv("DATABRICKS_HOST")
    if env_host:
        return env_host

    try:
        from shared_library.databricks_connectors.utils.env_reader import EnvironmentConfig

        return EnvironmentConfig().host
    except Exception:
        return None


def get_workspace_client_for_request(
    request_headers: Optional[dict] = None,
    host: Optional[str] = None,
) -> WorkspaceClient:
    """
    Dynamic WorkspaceClient resolver for HTTP request context.
    
    Implements the 3-tier identity resolution from auth.md:
    
    1. **User Authorization (On-Behalf-Of / OBO)**
       - Triggered: x-forwarded-access-token header present
       - Identity: Current end-user
       - Scope: Inherits user's Unity Catalog permissions & RLS/column masks
       - Use: Dynamic user queries, Genie AI agents, UC Volume access
    
    2. **App Authorization (Service Principal / M2M)**
       - Triggered: DATABRICKS_CLIENT_ID & DATABRICKS_CLIENT_SECRET in environment
       - Identity: Managed service principal (auto-injected on app deployment)
       - Scope: Static permissions granted to app SP
       - Use: Background maintenance, system logging, model serving ingestion
    
    3. **Local Development (Interactive U2M)**
       - Triggered: No headers, no SP credentials
       - Identity: Currently logged-in developer
       - Scope: Developer's workspace permissions
       - Use: Local testing, manual queries
       - Caching: @lru_cache prevents repeated browser auth prompts
    
    Args:
        request_headers: Dict of HTTP request headers (e.g., from Flask request.headers).
                        If None, skips OBO check (useful for background tasks).
        host: Databricks workspace hostname override. Defaults to DATABRICKS_HOST env var.
    
    Returns:
        WorkspaceClient: Authenticated client using the highest-priority available identity.
    
    Examples:
        # In a Flask route (use request context)
        from flask import request
        from .workspace_client import get_workspace_client_for_request
        
        @app.route('/api/query')
        def query():
            # Resolves to OBO if user is authenticated, SP if running as app, or local dev
            ws = get_workspace_client_for_request(dict(request.headers))
            # UC row-level filters & column masks apply automatically for user
            result = ws.statement_execution.execute_statement(...)
            return result
        
        # Background task (no request context)
        from .workspace_client import get_app_client
        
        @app.after_request
        def log_telemetry(response):
            # Always uses SP identity for logging; user context not needed
            ws = get_app_client()
            ws.jobs.list()  # System-level query
            return response
    """
    host = host or _resolve_host()

    # 1. User Authorization (On-Behalf-Of via forwarded header)
    if request_headers and "x-forwarded-access-token" in request_headers:
        token = request_headers["x-forwarded-access-token"]
        return WorkspaceClient(host=host, token=token, auth_type="pat")

    # 2. App Authorization (Service Principal M2M)
    if os.getenv("DATABRICKS_CLIENT_ID") and os.getenv("DATABRICKS_CLIENT_SECRET"):
        return WorkspaceClient(
            host=host,
            client_id=os.environ["DATABRICKS_CLIENT_ID"],
            client_secret=os.environ["DATABRICKS_CLIENT_SECRET"],
            auth_type="oauth-m2m",
        )

    # 3. Local Development (CLI profile U2M, else interactive browser; cached)
    return _get_cached_local_client(host, _local_profile())


_APP_CLIENT: Optional[WorkspaceClient] = None


def _init_app_client() -> WorkspaceClient:
    """Initialize the module-level service principal client."""
    host = _resolve_host()

    if os.getenv("DATABRICKS_CLIENT_ID") and os.getenv("DATABRICKS_CLIENT_SECRET"):
        return WorkspaceClient(
            host=host,
            client_id=os.environ["DATABRICKS_CLIENT_ID"],
            client_secret=os.environ["DATABRICKS_CLIENT_SECRET"],
            auth_type="oauth-m2m",
        )

    # Fallback to local dev (should not happen in production)
    return _get_cached_local_client(host, _local_profile())


def get_app_client() -> WorkspaceClient:
    """
    Module-level service principal WorkspaceClient singleton.
    
    Used for background tasks, system logging, telemetry, and other app-level operations
    that don't require user context. Always uses the service principal identity (M2M).
    
    This client is initialized once per app startup and reused across all requests.
    
    Returns:
        WorkspaceClient: App's service principal client
    
    Example:
        from .workspace_client import get_app_client
        
        ws = get_app_client()
        # Log to system table
        ws.statement_execution.execute_statement(
            warehouse_id=...,
            catalog="...",
            schema="...",
            statement="INSERT INTO audit_log ..."
        )
    """
    global _APP_CLIENT
    if _APP_CLIENT is None:
        _APP_CLIENT = _init_app_client()
    return _APP_CLIENT
