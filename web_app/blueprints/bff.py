"""BFF proxy blueprint — forward /bff/* requests to agent_server:8001.

Direct port of PDF Parser's blueprints/api_proxy/__init__.py.
Passes X-Forwarded-* headers through untouched for SSO auth.
"""

from __future__ import annotations

import json
from typing import Any, Generator

import httpx
from flask import Blueprint, Response, request, stream_with_context

from shared_library.global_logger_hub import bootstrap, get_app_logger, set_request_id

bootstrap()
logger = get_app_logger(__name__)

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


def _stream_response(
    upstream: httpx.Response,
    client: httpx.Client,
) -> Generator[bytes, None, None]:
    """Relay the upstream SSE body, then release the connection.

    Both the response and its owning client are closed in a `finally` block so
    the connection is released even if the browser disconnects mid-stream
    (which raises GeneratorExit here).

    NOTE: do NOT use `with httpx.stream(...)` in the calling route. Flask
    evaluates this generator lazily, *after* the view returns, so the context
    manager would already have closed the connection by the time the first
    chunk is pulled. `httpx.Response` also has no context-manager protocol,
    so `with upstream:` raises TypeError.
    """
    try:
        for chunk in upstream.iter_bytes():
            yield chunk
    finally:
        upstream.close()
        client.close()


@bff_bp.route("/agents/stream", methods=["POST"])
def stream_agent() -> Response:
    """POST /bff/agents/stream → agent_server /api/v1/agents/stream (SSE)."""
    data = request.get_json() or {}
    thread_id = data.get("thread_id", "unknown")
    user_id = request.headers.get("X-Forwarded-Email", "unknown@example.com")
    set_request_id(thread_id)

    logger.info(f"stream | thread={thread_id} | user={user_id}")

    headers = _build_request_headers()
    headers["Accept"] = "text/event-stream"

    # The client must outlive this view function: Flask pulls from the
    # generator only after the view returns. Ownership is handed to
    # _stream_response(), which closes both in its finally block.
    client = httpx.Client(timeout=600.0)  # 10 minute timeout for long streams
    try:
        upstream = client.send(
            client.build_request(
                "POST",
                f"{AGENT_SERVER_URL}/api/v1/agents/stream",
                json=data,
                headers=headers,
            ),
            stream=True,
        )
    except Exception as e:
        client.close()
        logger.exception(f"stream | error={type(e).__name__}")
        return Response(
            json.dumps({"error": str(e)}),
            status=500,
            mimetype="application/json",
        )

    if upstream.status_code != 200:
        # Drain the body so the error detail is not lost, then release both.
        try:
            upstream.read()
            detail = upstream.text[:500]
        except Exception:
            detail = ""
        finally:
            upstream.close()
            client.close()

        logger.error(
            "stream | upstream_error | status=%s | detail=%s",
            upstream.status_code,
            detail,
        )
        return Response(
            json.dumps(
                {
                    "error": "upstream_error",
                    "status": upstream.status_code,
                    "detail": detail,
                }
            ),
            status=upstream.status_code,
            mimetype="application/json",
        )

    return Response(
        stream_with_context(_stream_response(upstream, client)),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@bff_bp.route("/agents/invoke", methods=["POST"])
def invoke_agent() -> dict[str, Any]:
    """POST /bff/agents/invoke → agent_server /api/v1/agents/invoke."""
    data = request.get_json() or {}
    thread_id = data.get("thread_id", "unknown")
    user_id = request.headers.get("X-Forwarded-Email", "unknown@example.com")
    set_request_id(thread_id)

    logger.info(f"invoke | thread={thread_id} | user={user_id}")

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
        logger.exception(f"invoke | error={type(e).__name__}")
        return {"error": str(e), "status": 500}


@bff_bp.route("/agents/threads/<thread_id>", methods=["GET"])
def get_thread(thread_id: str) -> dict[str, Any]:
    """GET /bff/agents/threads/{thread_id} → agent_server /api/v1/agents/threads/{thread_id}."""
    user_id = request.headers.get("X-Forwarded-Email", "unknown@example.com")
    set_request_id(thread_id)

    logger.info(f"get_thread | thread={thread_id} | user={user_id}")

    headers = _build_request_headers()

    try:
        httpx_response = httpx.get(
            f"{AGENT_SERVER_URL}/api/v1/agents/threads/{thread_id}",
            headers=headers,
            timeout=30.0,
        )
        return httpx_response.json()
    except Exception as e:
        logger.exception(f"get_thread | error={type(e).__name__}")
        return {"error": str(e), "status": 500}


@bff_bp.route("/agents/threads/<thread_id>", methods=["DELETE"])
def delete_thread(thread_id: str) -> dict[str, Any]:
    """DELETE /bff/agents/threads/{thread_id} → agent_server."""
    user_id = request.headers.get("X-Forwarded-Email", "unknown@example.com")
    set_request_id(thread_id)

    logger.info(f"delete_thread | thread={thread_id} | user={user_id}")

    headers = _build_request_headers()

    try:
        httpx_response = httpx.delete(
            f"{AGENT_SERVER_URL}/api/v1/agents/threads/{thread_id}",
            headers=headers,
            timeout=30.0,
        )
        return httpx_response.json()
    except Exception as e:
        logger.exception(f"delete_thread | error={type(e).__name__}")
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


@bff_bp.route("/model-catalog", methods=["GET"])
def get_model_catalog() -> dict[str, Any]:
    """GET /bff/model-catalog → expose model/profile catalog for the UI model picker.
    
    Returns the combined profile + model + effort metadata from shared_library.model_factory.catalog.
    The model picker uses this to populate the searchable list.
    
    Query params:
    - surface: "chat" (default) | "power_user" | "all" — filter models by surface.
    
    Response shape (from catalog.py:240-260):
    {
      "schema_version": 3,
      "surface": "chat",
      "defaults": { "profile": "fast_chat", "effort": "low", "fast": false },
      "effort_map": { "low": "fast_chat", "medium": "balanced", "high": "deep_reasoning" },
      "fast_profile": "fast_chat",
      "profiles": [
        { "id": "fast_chat", "label": "Fast", "description": "...", "effort": "low", ... },
        ...
      ],
      "models": [
        { "id": "system.ai.claude-haiku...", "label": "...", "short_name": "...", 
          "badges": [...], "swap_safe_for_agent": true, ... },
        ...
      ]
    }
    """
    try:
        from shared_library.model_factory.catalog import get_model_catalog
        
        surface = request.args.get("surface", "chat")
        catalog = get_model_catalog(surface=surface)
        return catalog
    except Exception as e:
        logger.exception(f"get_model_catalog | error={type(e).__name__}")
        return {
            "error": str(e),
            "status": 500,
        }


@bff_bp.route("/health", methods=["GET"])
def health() -> dict[str, Any]:
    """GET /bff/health → agent_server /health.
    
    Checks if the FastAPI agent server is running and responsive.
    Returns {"status": "ok", "graph_ready": true/false} if agent is running.
    Returns {"status": "error", "error": "reason"} if agent is unreachable.
    
    Troubleshooting:
    - If status is "error" with "Connection refused", start agent_server:
        uv run uvicorn agent_server.start_server:app --reload --port 8001
    - Or use dual-server launcher:
        uv run python ops/deployment/run_app.py
    """
    agent_url = f"{AGENT_SERVER_URL}/health"
    
    try:
        logger.debug(f"health | agent={agent_url}")
        httpx_response = httpx.get(agent_url, timeout=5.0)
        
        if httpx_response.status_code != 200:
            logger.warning(f"health | status={httpx_response.status_code}")
            return {
                "status": "error",
                "error": f"agent_server returned {httpx_response.status_code}",
                "agent_url": agent_url,
            }
        
        result = httpx_response.json()
        logger.info(f"health | graph_ready={result.get('graph_ready', 'unknown')}")
        return result
        
    except httpx.ConnectError as e:
        logger.warning(f"health | connect_error | agent={agent_url}")
        return {
            "status": "error",
            "error": "agent_server unreachable (connection refused)",
            "agent_url": agent_url,
        }
    except httpx.TimeoutException:
        logger.warning(f"health | timeout | agent={agent_url}")
        return {
            "status": "error",
            "error": "agent_server timeout (no response in 5s)",
            "agent_url": agent_url,
        }
    except Exception as e:
        logger.exception(f"health | error={type(e).__name__}")
        return {
            "status": "error",
            "error": str(e),
            "agent_url": agent_url,
        }
