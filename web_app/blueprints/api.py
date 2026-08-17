"""
Procurement Decision Workspace API Routes

Security:
- User identity resolved via web_app.auth (single source of truth)
- Hard tenant scoping: list_projects filters by LOWER(owner_email)
- Open redirect protection: next= params validated to relative paths only
- Live workspace assets fetched via OBO token (x-forwarded-access-token)
"""

import logging
from flask import Blueprint, jsonify, redirect, request

from ..auth import get_current_user, get_forwarded_access_token
from ..database import get_session
from ..models import Project, User
from ..workspace_client import get_workspace_client_for_request

logger = logging.getLogger(__name__)
api_bp = Blueprint("api", __name__)


@api_bp.route("/projects", methods=["GET"])
def list_projects():
    """
    List projects owned by the current user.
    
    SECURITY: Hard tenant scope filters by LOWER(owner_email) = current_user.email.lower()
    This ensures users can only list and access their own projects, preventing unauthorized
    data exposure across tenant boundaries.
    
    Returns:
        JSON array of project dicts, ordered by most recent update
    """
    session = get_session()
    current_user = get_current_user()
    
    if not current_user:
        return jsonify({"error": "Not authenticated"}), 401
    
    # Hard tenant scope: only projects owned by current user
    projects = session.query(Project).filter(
        Project.owner_email == current_user.email.lower()
    ).order_by(Project.updated_at.desc()).all()
    
    return jsonify([p.to_dict() for p in projects])


@api_bp.route("/auth/profile", methods=["GET"])
def auth_profile():
    """
    Get the current authenticated user's profile enriched with live SCIM data.
    
    Returns the user from the database plus live workspace entitlements:
    - groups: from ws.current_user.me().groups (Databricks group memberships)
    - entitlements: from ws.current_user.me().entitlements (workspace entitlements)
    - roles: from ws.current_user.me().roles (if present)
    
    OBO token used: x-forwarded-access-token (inherits user's permissions).
    Falls back to DB data if SCIM fetch fails.
    
    Returns:
        JSON user object with all profile fields including live groups/entitlements
    """
    user = get_current_user()
    if not user:
        return jsonify({"error": "Not authenticated"}), 401
    
    profile = user.to_dict()
    
    # Enrich with live SCIM data (groups, entitlements, roles)
    try:
        ws = get_workspace_client_for_request(dict(request.headers))
        me = ws.current_user.me()
        
        # Extract groups from SCIM object (list of objects with "display" and "value")
        if hasattr(me, 'groups') and me.groups:
            profile['groups'] = [g.display if hasattr(g, 'display') else g.value for g in me.groups]
        
        # Extract entitlements (list of objects with "value" key)
        if hasattr(me, 'entitlements') and me.entitlements:
            profile['entitlements'] = [e.value if hasattr(e, 'value') else str(e) for e in me.entitlements]
        
        # Extract roles if present (list of objects with "value" key)
        if hasattr(me, 'roles') and me.roles:
            profile['roles'] = [r.value if hasattr(r, 'value') else str(r) for r in me.roles]
        
        # Optionally update name/timezone/locale from SCIM (more authoritative than headers)
        if hasattr(me, 'name') and me.name:
            if hasattr(me.name, 'formatted') and me.name.formatted:
                profile['display_name'] = me.name.formatted
        
        if hasattr(me, 'timezone') and me.timezone:
            profile['timezone'] = me.timezone
        
        if hasattr(me, 'locale') and me.locale:
            profile['locale'] = me.locale
        
        logger.info(f"Enriched profile for {user.email} with SCIM data")
    except Exception as e:
        logger.warning(f"Could not enrich profile with SCIM data for {user.email}: {e}")
        # Return DB data without SCIM enrichment on failure
    
    return jsonify(profile)


@api_bp.route("/profile/assets/<section>", methods=["GET"])
def profile_assets(section: str):
    """
    Get live Databricks workspace assets for a given section.
    
    Sections: compute, ai, data, apps
    Each section independently fetches from the WorkspaceClient using OBO token.
    On error, returns empty list with error message (graceful degradation).
    
    Args:
        section: One of "compute", "ai", "data", "apps"
    
    Returns:
        JSON dict with section-specific assets, or error flag if fetch failed
    """
    data = _get_live_asset_data(section)
    return jsonify(data)


def _get_live_asset_data(section: str) -> dict:
    """
    Fetch live Databricks workspace assets via OBO token (x-forwarded-access-token).
    
    Each section fetches independently and gracefully degrades on error.
    Uses try/except per section so one failure doesn't cascade.
    
    Args:
        section: "compute", "ai", "data", or "apps"
    
    Returns:
        Dict with section-specific data, or {"error": "..."} on failure
    """
    try:
        ws = get_workspace_client_for_request(dict(request.headers))
        
        if section == "compute":
            return _get_compute_assets(ws)
        elif section == "ai":
            return _get_ai_assets(ws)
        elif section == "data":
            return _get_data_assets(ws)
        elif section == "apps":
            return _get_apps_assets(ws)
        else:
            return {"error": f"Unknown section: {section}"}
    
    except Exception as e:
        logger.error(f"Failed to fetch {section} assets: {e}")
        return {"error": f"Could not load {section}: {str(e)}", "warehouses": [], "clusters": [], "serving_endpoints": [], "vector_search_endpoints": [], "catalogs": [], "apps": []}


def _get_compute_assets(ws) -> dict:
    """Fetch warehouses and clusters (live)."""
    try:
        warehouses = []
        for w in ws.warehouses.list():
            warehouses.append({
                "name": w.name,
                "cluster_size": w.cluster_size or "—",
                "warehouse_type": str(w.warehouse_type) if w.warehouse_type else "—",
                "state": str(w.state) if w.state else "UNKNOWN",
            })
    except Exception as e:
        logger.warning(f"Failed to list warehouses: {e}")
        warehouses = []
    
    try:
        clusters = []
        for c in ws.clusters.list():
            clusters.append({
                "cluster_name": c.cluster_name or c.cluster_id,
                "spark_version": c.spark_version or "—",
                "state": str(c.state) if c.state else "UNKNOWN",
            })
    except Exception as e:
        logger.warning(f"Failed to list clusters: {e}")
        clusters = []
    
    return {"warehouses": warehouses, "clusters": clusters}


def _get_ai_assets(ws) -> dict:
    """Fetch serving endpoints and vector search endpoints (live)."""
    try:
        serving_endpoints = []
        for e in ws.serving_endpoints.list():
            serving_endpoints.append({
                "name": e.name,
                "ready": str(e.state.ready) if e.state and e.state.ready else "UNKNOWN",
                "config_update": str(e.state.config_update) if e.state and e.state.config_update else "UNKNOWN",
            })
    except Exception as e:
        logger.warning(f"Failed to list serving endpoints: {e}")
        serving_endpoints = []
    
    try:
        vector_search_endpoints = []
        vs_list = ws.vector_search_endpoints.list_endpoints()
        if vs_list and hasattr(vs_list, 'endpoints') and vs_list.endpoints:
            for e in vs_list.endpoints:
                vector_search_endpoints.append({
                    "name": e.name,
                    "endpoint_type": str(e.endpoint_type) if e.endpoint_type else "STANDARD",
                    "state": str(e.endpoint_status.state) if e.endpoint_status and e.endpoint_status.state else "UNKNOWN",
                })
    except Exception as e:
        logger.warning(f"Failed to list vector search endpoints: {e}")
        vector_search_endpoints = []
    
    return {"serving_endpoints": serving_endpoints, "vector_search_endpoints": vector_search_endpoints}


def _get_data_assets(ws) -> dict:
    """Fetch Unity Catalog catalogs (live)."""
    try:
        catalogs = []
        for c in ws.catalogs.list():
            catalogs.append({
                "name": c.name,
                "owner": c.owner or "—",
                "catalog_type": str(c.catalog_type) if c.catalog_type else "—",
            })
    except Exception as e:
        logger.warning(f"Failed to list catalogs: {e}")
        catalogs = []
    
    return {"catalogs": catalogs}


def _get_apps_assets(ws) -> dict:
    """Fetch Databricks Apps (live)."""
    try:
        apps = []
        for a in ws.apps.list():
            state = "UNKNOWN"
            if hasattr(a, 'app_status') and a.app_status and hasattr(a.app_status, 'state'):
                state = str(a.app_status.state)
            
            apps.append({
                "name": a.name,
                "description": a.description or "—",
                "state": state,
            })
    except Exception as e:
        logger.warning(f"Failed to list apps: {e}")
        apps = []
    
    return {"apps": apps}


@api_bp.route("/logs", methods=["POST"])
def logs():
    """
    Telemetry endpoint for client-side logging.
    
    POST body expected: { "level": "info|warn|error", "message": "...", "context": {...} }
    """
    return jsonify({"ok": True})


def _validate_redirect_url(url: str) -> bool:
    """
    Validate that a redirect URL is safe (relative path only).
    
    SECURITY: Open redirect protection per auth.md.
    Only allows relative paths without double slashes (//) to prevent
    redirect to external hosts (e.g., evil.com via //evil.com/path).
    
    Args:
        url: URL to validate
    
    Returns:
        bool: True if safe to redirect, False otherwise
    """
    # Must not contain :// (prevents protocol-relative redirects)
    # Must not start with // (prevents //evil.com redirects)
    # Must start with / (relative path only)
    if not url:
        return False
    return url.startswith("/") and "://" not in url and not url.startswith("//")


@api_bp.route("/auth/logout", methods=["GET"])
def auth_logout():
    """
    Logout endpoint. Redirects to login page.
    
    SECURITY: Validates next= param to prevent open redirects.
    """
    next_url = request.args.get("next", "/login")
    
    # Validate redirect URL (prevent open redirect attacks)
    if not _validate_redirect_url(next_url):
        next_url = "/login"
    
    return redirect(next_url)


@api_bp.route("/auth/login", methods=["GET"])
def auth_login():
    """
    Login endpoint. Redirects to home.
    
    In production (Databricks Apps), SSO is handled by the L7 proxy
    before requests reach this app. This route exists for consistency.
    """
    return redirect("/")
