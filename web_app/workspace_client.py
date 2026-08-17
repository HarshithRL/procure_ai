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
def _get_cached_local_client(host: str) -> WorkspaceClient:
    """
    Create a cached WorkspaceClient for local development using interactive browser auth.
    
    The @lru_cache decorator ensures that repeated calls to get_workspace_client_for_request()
    during local dev don't trigger multiple browser auth flows — the client is reused.
    
    Args:
        host: Databricks workspace hostname (e.g., https://adb-xxx.azuredatabricks.net/)
    
    Returns:
        WorkspaceClient: Authenticated client using external-browser auth
    """
    return WorkspaceClient(host=host, auth_type="external-browser")


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
    host = host or os.getenv("DATABRICKS_HOST")

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

    # 3. Local Development (Interactive U2M with caching)
    return _get_cached_local_client(host)


_APP_CLIENT: Optional[WorkspaceClient] = None


def _init_app_client() -> WorkspaceClient:
    """Initialize the module-level service principal client."""
    host = os.getenv("DATABRICKS_HOST")
    
    if os.getenv("DATABRICKS_CLIENT_ID") and os.getenv("DATABRICKS_CLIENT_SECRET"):
        return WorkspaceClient(
            host=host,
            client_id=os.environ["DATABRICKS_CLIENT_ID"],
            client_secret=os.environ["DATABRICKS_CLIENT_SECRET"],
            auth_type="oauth-m2m",
        )
    
    # Fallback to local dev (should not happen in production)
    return _get_cached_local_client(host)


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
