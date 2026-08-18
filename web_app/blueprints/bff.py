"""BFF proxy blueprint — forward /bff/* requests to agent_server:8001.

Direct port of PDF Parser's blueprints/api_proxy/__init__.py.
Passes X-Forwarded-* headers through untouched for SSO auth.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Generator

import httpx
from flask import Blueprint, Response, request, stream_with_context

logger = logging.getLogger(__name__)

bff_bp = Blueprint("bff", __name__, url_prefix="/bff")

# Agent server base URL
AGENT_SERVER_URL = "http://127.0.0.1:8001"


def _build_request_headers() -> dict[str, str]:
    """Extract and pass through X-Forwarded-* headers from Flask request."""
    headers: dict[str, str] = {}

    # Copy all headers from the client
    for key, value in request.headers:
        # Whitelist critical headers
        if key.lower() in (
            "x-forwarded-email",
            "x-forwarded-user",
            "x-forwarded-preferred-username",
            "x-forwarded-access-token",
            "content-type",
            "accept",
            "user-agent",
        ):
            headers[key] = value

    return headers


def _stream_response(httpx_response: httpx.Response) -> Generator[bytes, None, None]:
    """Stream response body from httpx."""
    with httpx_response:
        for chunk in httpx_response.iter_bytes():
            yield chunk


@bff_bp.route("/agents/stream", methods=["POST"])
def stream_agent() -> Response:
    """POST /bff/agents/stream → agent_server /api/v1/agents/stream (SSE)."""
    data = request.get_json() or {}
    thread_id = data.get("thread_id", "unknown")
    user_id = request.headers.get("X-Forwarded-Email", "unknown@example.com")

    logger.info(f"[BFF] stream | thread={thread_id} | user={user_id}")

    headers = _build_request_headers()
    headers["Accept"] = "text/event-stream"

    try:
        with httpx.stream(
            "POST",
            f"{AGENT_SERVER_URL}/api/v1/agents/stream",
            json=data,
            headers=headers,
            timeout=600.0,  # 10 minute timeout for long streams
        ) as httpx_response:
            if httpx_response.status_code != 200:
                return Response(
                    json.dumps(
                        {
                            "error": "upstream_error",
                            "status": httpx_response.status_code,
                        }
                    ),
                    status=httpx_response.status_code,
                    mimetype="application/json",
                )

            return Response(
                stream_with_context(_stream_response(httpx_response)),
                mimetype="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                },
            )
    except Exception as e:
        logger.exception(f"[BFF] stream error: {e}")
        return Response(
            json.dumps({"error": str(e)}),
            status=500,
            mimetype="application/json",
        )


@bff_bp.route("/agents/invoke", methods=["POST"])
def invoke_agent() -> dict[str, Any]:
    """POST /bff/agents/invoke → agent_server /api/v1/agents/invoke."""
    data = request.get_json() or {}
    thread_id = data.get("thread_id", "unknown")
    user_id = request.headers.get("X-Forwarded-Email", "unknown@example.com")

    logger.info(f"[BFF] invoke | thread={thread_id} | user={user_id}")

    headers = _build_request_headers()

    try:
        httpx_response = httpx.post(
            f"{AGENT_SERVER_URL}/api/v1/agents/invoke",
            json=data,
            headers=headers,
            timeout=300.0,
        )
        return httpx_response.json()
    except Exception as e:
        logger.exception(f"[BFF] invoke error: {e}")
        return {"error": str(e), "status": 500}


@bff_bp.route("/agents/threads/<thread_id>", methods=["GET"])
def get_thread(thread_id: str) -> dict[str, Any]:
    """GET /bff/agents/threads/{thread_id} → agent_server /api/v1/agents/threads/{thread_id}."""
    user_id = request.headers.get("X-Forwarded-Email", "unknown@example.com")

    logger.info(f"[BFF] get_thread | thread={thread_id} | user={user_id}")

    headers = _build_request_headers()

    try:
        httpx_response = httpx.get(
            f"{AGENT_SERVER_URL}/api/v1/agents/threads/{thread_id}",
            headers=headers,
            timeout=30.0,
        )
        return httpx_response.json()
    except Exception as e:
        logger.exception(f"[BFF] get_thread error: {e}")
        return {"error": str(e), "status": 500}


@bff_bp.route("/agents/threads/<thread_id>", methods=["DELETE"])
def delete_thread(thread_id: str) -> dict[str, Any]:
    """DELETE /bff/agents/threads/{thread_id} → agent_server."""
    user_id = request.headers.get("X-Forwarded-Email", "unknown@example.com")

    logger.info(f"[BFF] delete_thread | thread={thread_id} | user={user_id}")

    headers = _build_request_headers()

    try:
        httpx_response = httpx.delete(
            f"{AGENT_SERVER_URL}/api/v1/agents/threads/{thread_id}",
            headers=headers,
            timeout=30.0,
        )
        return httpx_response.json()
    except Exception as e:
        logger.exception(f"[BFF] delete_thread error: {e}")
        return {"error": str(e), "status": 500}


@bff_bp.route("/identity/me", methods=["GET"])
def get_identity() -> dict[str, Any]:
    """GET /bff/identity/me → agent_server /api/v1/identity/me."""
    headers = _build_request_headers()

    try:
        httpx_response = httpx.get(
            f"{AGENT_SERVER_URL}/api/v1/identity/me",
            headers=headers,
            timeout=30.0,
        )
        return httpx_response.json()
    except Exception as e:
        logger.exception(f"[BFF] get_identity error: {e}")
        return {"error": str(e), "status": 500}


@bff_bp.route("/health", methods=["GET"])
def health() -> dict[str, Any]:
    """GET /bff/health → agent_server /health."""
    try:
        httpx_response = httpx.get(
            f"{AGENT_SERVER_URL}/health",
            timeout=5.0,
        )
        return httpx_response.json()
    except Exception as e:
        logger.exception(f"[BFF] health error: {e}")
        return {"status": "error", "error": str(e)}
