"""
Procurement Decision Workspace API Routes

Security:
- User identity resolved via web_app.auth (single source of truth)
- Hard tenant scoping: list_projects filters by LOWER(owner_email)
- Open redirect protection: next= params validated to relative paths only
- Live workspace assets fetched via OBO token (x-forwarded-access-token)
"""

from shared_library.global_logger_hub import bootstrap, get_app_logger

bootstrap()
import uuid
from datetime import datetime, timezone
from flask import Blueprint, jsonify, redirect, request

from ..auth import get_current_user, get_forwarded_access_token
from ..database import get_session
from ..models import Project, User
from ..workspace_client import get_workspace_client_for_request

logger = get_app_logger(__name__)
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


# ─────────────────────────────────────────────────────────────────────────────
# Chat API — Sprint 1 stubs (no DB; replaced by real persistence in Sprint 2)
# ─────────────────────────────────────────────────────────────────────────────

def _utcnow_iso() -> str:
    """ISO-8601 timestamp with Z suffix — matches project model convention."""
    return datetime.now(timezone.utc).isoformat() + "Z"


# Synthetic stub data — replaced by DB in Sprint 2
_STUB_SESSIONS: list[dict] = [
    {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "title": "Packaging supplier shortlist review",
        "created_at": "2026-08-15T09:12:00.000000Z",
        "message_count": 6,
        "last_message": "Which vendors have ISO 14001 certification?",
    },
    {
        "id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "title": "Logistics RFQ cost analysis",
        "created_at": "2026-08-16T14:30:00.000000Z",
        "message_count": 4,
        "last_message": "Compare total landed cost across 3 vendors.",
    },
    {
        "id": "c3d4e5f6-a7b8-9012-cdef-123456789012",
        "title": "EMEA raw materials benchmark",
        "created_at": "2026-08-18T08:00:00.000000Z",
        "message_count": 1,
        "last_message": "Summarise price variance for Q3 2026.",
    },
]

_STUB_MESSAGES: dict[str, list[dict]] = {
    "a1b2c3d4-e5f6-7890-abcd-ef1234567890": [
        {
            "id": "msg-001",
            "role": "user",
            "content": "List all suppliers with active ISO 14001 certification.",
            "timestamp": "2026-08-15T09:12:00.000000Z",
        },
        {
            "id": "msg-002",
            "role": "assistant",
            "content": "Based on the uploaded vendor documents, three suppliers hold active ISO 14001 certification: **Vendor A** (valid until 2027-06), **Vendor B** (valid until 2026-12), and **Vendor C** (valid until 2028-03).",
            "timestamp": "2026-08-15T09:12:04.000000Z",
        },
        {
            "id": "msg-003",
            "role": "user",
            "content": "Which vendors have ISO 14001 certification?",
            "timestamp": "2026-08-15T10:45:00.000000Z",
        },
        {
            "id": "msg-004",
            "role": "assistant",
            "content": "How are you?",
            "timestamp": "2026-08-15T10:45:01.000000Z",
        },
    ],
    "b2c3d4e5-f6a7-8901-bcde-f12345678901": [
        {
            "id": "msg-101",
            "role": "user",
            "content": "Compare total landed cost across 3 vendors.",
            "timestamp": "2026-08-16T14:30:00.000000Z",
        },
        {
            "id": "msg-102",
            "role": "assistant",
            "content": "How are you?",
            "timestamp": "2026-08-16T14:30:02.000000Z",
        },
    ],
    "c3d4e5f6-a7b8-9012-cdef-123456789012": [
        {
            "id": "msg-201",
            "role": "user",
            "content": "Summarise price variance for Q3 2026.",
            "timestamp": "2026-08-18T08:00:00.000000Z",
        },
        {
            "id": "msg-202",
            "role": "assistant",
            "content": "How are you?",
            "timestamp": "2026-08-18T08:00:03.000000Z",
        },
    ],
}


@api_bp.route("/chat/sessions", methods=["GET"])
def list_chat_sessions():
    """
    List chat sessions for the current user.

    Sprint 1: Returns hardcoded synthetic sessions (no DB).
    Sprint 2: Replace with DB query filtered by current_user.email.

    Returns:
        JSON array: [{id, title, created_at, message_count, last_message}]
    """
    return jsonify(_STUB_SESSIONS)


@api_bp.route("/chat/sessions/<session_id>", methods=["GET"])
def get_chat_session(session_id: str):
    """
    Get all messages for a chat session.

    Sprint 1: Returns hardcoded synthetic messages for known stub session IDs.
    Unknown session IDs return 404.

    Args:
        session_id: UUID string of the session

    Returns:
        JSON: {session_id, title, messages: [{id, role, content, timestamp}]}
    """
    # Look up session metadata from stub list
    session_meta = next(
        (s for s in _STUB_SESSIONS if s["id"] == session_id), None
    )
    if session_meta is None:
        return jsonify({"error": "Session not found"}), 404

    messages = _STUB_MESSAGES.get(session_id, [])
    return jsonify({
        "session_id": session_id,
        "title": session_meta["title"],
        "messages": messages,
    })


@api_bp.route("/chat/sessions/<session_id>/message", methods=["POST"])
def send_chat_message(session_id: str):
    """
    Send a user message and receive an assistant reply.

    Sprint 1: Always replies "How are you?" (fixed stub).
    Sprint 2: Wire to LangChain agent with session memory.

    Request body: {"content": "<user message>"}
    Returns:
        JSON: {id, role, content, timestamp}
        400 if content is missing or empty
        404 if session_id is not a known stub session
    """
    # Validate session exists
    session_meta = next(
        (s for s in _STUB_SESSIONS if s["id"] == session_id), None
    )
    if session_meta is None:
        return jsonify({"error": "Session not found"}), 404

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"error": "content is required and must be non-empty"}), 400

    logger.info("Chat message received for session %s (stub reply)", session_id)

    reply = {
        "id": str(uuid.uuid4()),
        "role": "assistant",
        "content": "How are you?",
        "timestamp": _utcnow_iso(),
    }
    return jsonify(reply), 200


@api_bp.route("/chat/sessions", methods=["POST"])
def create_chat_session():
    """
    Create a new chat session.

    Sprint 1: Returns a synthetic session with a generated UUID (no DB).
    Sprint 2: Persist to ChatSession table with owner_email = current_user.email.

    Request body: {"title": "<optional title>"}
    Returns:
        JSON: {id, title, created_at, message_count}
        201 Created
    """
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip() or "New conversation"

    new_session = {
        "id": str(uuid.uuid4()),
        "title": title,
        "created_at": _utcnow_iso(),
        "message_count": 0,
    }
    logger.info("Created stub chat session: %s — '%s'", new_session["id"], title)
    return jsonify(new_session), 201
