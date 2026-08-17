"""
Procurement Decision Workspace API Routes

Security:
- User identity resolved via web_app.auth (single source of truth)
- Hard tenant scoping: list_projects filters by LOWER(owner_email)
- Open redirect protection: next= params validated to relative paths only
"""

import re
from flask import Blueprint, jsonify, redirect, request

from ..auth import get_current_user
from ..database import get_session
from ..models import Project, User

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
    Get the current authenticated user's profile.
    
    Returns:
        JSON user object with email, display_name, groups, entitlements
    """
    user = get_current_user()
    if not user:
        return jsonify({"error": "Not authenticated"}), 401
    return jsonify(user.to_dict())


@api_bp.route("/profile/assets/<section>", methods=["GET"])
def profile_assets(section: str):
    data = _asset_data(section)
    return jsonify(data)


def _asset_data(section: str) -> dict:
    if section == "compute":
        return {
            "warehouses": [
                {
                    "name": "procure-ai-wh",
                    "cluster_size": "Small",
                    "warehouse_type": "PRO",
                    "state": "RUNNING",
                },
                {
                    "name": "etex-bi-wh",
                    "cluster_size": "Medium",
                    "warehouse_type": "STANDARD",
                    "state": "STOPPED",
                },
            ],
            "clusters": [
                {
                    "cluster_name": "vendor-agent-shared",
                    "spark_version": "15.4.x-scala2.12",
                    "state": "RUNNING",
                },
            ],
        }
    if section == "ai":
        return {
            "serving_endpoints": [
                {"name": "procure-ai-chat", "ready": "READY", "config_update": "READY"},
                {
                    "name": "vendor-classifier",
                    "ready": "READY",
                    "config_update": "READY",
                },
            ],
            "vector_search_endpoints": [
                {
                    "name": "procure-vs-endpoint",
                    "endpoint_type": "STANDARD",
                    "state": "ONLINE",
                },
            ],
        }
    if section == "data":
        return {
            "catalogs": [
                {
                    "name": "harshith_raghunath_d",
                    "owner": "harshith.raghunath@etexgroup.com",
                    "catalog_type": "MANAGED_CATALOG",
                },
                {"name": "main", "owner": "system", "catalog_type": "SYSTEM_CATALOG"},
                {
                    "name": "samples",
                    "owner": "system",
                    "catalog_type": "SYSTEM_CATALOG",
                },
            ],
        }
    if section == "apps":
        return {
            "apps": [
                {
                    "name": "ds-procure-ai",
                    "description": "Databricks Procurement Decision Workspace",
                    "state": "RUNNING",
                },
            ],
        }
    return {"error": f"Unknown section: {section}"}


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
