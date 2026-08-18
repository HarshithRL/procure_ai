"""Procure AI FastAPI server — agent orchestration + SSE streaming.

Direct port of PDF Parser's start_server.py.
Serves /api/v1/agents/* and /api/v1/identity/* endpoints.
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from shared_library.global_logger_hub import bootstrap, get_agent_logger, api_turn
from agent_server.agent import close_graph, get_agent_graph
from agent_server.core.config import get_config
from agent_server.schemas import AgentState, StreamEvent, StreamRequest

bootstrap()
logger = get_agent_logger(__name__)


async def _bootstrap_mlflow() -> None:
    """Bootstrap MLflow tracing and Prompt Registry sync."""
    try:
        import mlflow

        config = get_config()
        mlflow.set_tracking_uri(config.mlflow_tracking_uri)
        mlflow.set_experiment(config.mlflow_experiment)
        mlflow.langchain.autolog()

        logger.info(
            f"MLflow bootstrapped | uri={config.mlflow_tracking_uri} | exp={config.mlflow_experiment}"
        )
    except ImportError:
        logger.warning("MLflow not available; tracing disabled")
    except Exception as e:
        logger.warning(f"MLflow bootstrap error: {e}")


async def _warm_graph() -> None:
    """Warm up the agent graph on startup."""
    try:
        await get_agent_graph()
        logger.info("Agent graph warmed up")
    except Exception as e:
        logger.warning(f"Graph warm-up error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager — startup and shutdown."""
    logger.info("Starting Procure AI agent server...")

    # Startup
    await _bootstrap_mlflow()
    await _warm_graph()

    logger.info("Server startup complete")
    yield

    # Shutdown
    logger.info("Shutting down agent server...")
    await close_graph()
    logger.info("Server shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Procure AI Agent API",
    version="0.1.0",
    description="LangGraph + LangChain agent orchestration for procurement",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Routes
# ============================================================================


@app.get("/")
async def root() -> dict:
    """API index."""
    return {
        "service": "Procure AI Agent API",
        "version": "0.1.0",
        "endpoints": {
            "health": "GET /health",
            "stream": "POST /api/v1/agents/stream",
            "invoke": "POST /api/v1/agents/invoke",
            "threads": "GET /api/v1/agents/threads/{thread_id}",
            "identity": "GET /api/v1/identity/me",
        },
    }


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    try:
        graph = await get_agent_graph()
        graph_ready = graph is not None
    except Exception:
        graph_ready = False

    return {
        "status": "ok" if graph_ready else "starting",
        "graph_ready": graph_ready,
        "service": "Procure AI Agent API",
    }


@app.get("/api/v1/identity/me")
async def get_identity(request: Request) -> dict:
    """Return current user identity from X-Forwarded headers."""
    email = request.headers.get("X-Forwarded-Email", "unknown@example.com")
    user = request.headers.get("X-Forwarded-User", "unknown")
    preferred_username = request.headers.get("X-Forwarded-Preferred-Username", "unknown")

    return {
        "user_id": email.lower(),
        "email": email,
        "display_name": preferred_username or user,
    }


async def _stream_graph_events(
    thread_id: str,
    user_id: str,
    message: str,
    profile: str,
    model: str | None,
) -> AsyncGenerator[str, None]:
    """Stream agent events via SSE."""
    import uuid

    graph = await get_agent_graph()
    session_uuid = str(uuid.uuid4())

    # Build initial state
    from langchain_core.messages import HumanMessage

    state: AgentState = {
        "messages": [HumanMessage(content=message)],
        "thread_id": thread_id,
        "user_id": user_id,
        "session_id": session_uuid,
        # Drives per-request LLM selection in brain_node — this is what the
        # chat UI's model picker actually controls.
        "profile": profile,
        "model": model,
    }

    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_id": user_id,
        }
    }

    try:
        # MLflow trace ID (if available)
        trace_id = None
        try:
            import mlflow

            trace_id = mlflow.get_trace_id()
        except Exception:
            pass

        # Stream events
        async for event in graph.astream_events(state, config=config, version="v2"):
            event_type = event.get("event", "")
            data = event.get("data", {})

            # Emit StreamEvent as SSE data
            se = StreamEvent(
                event=event_type,
                data=data,
                trace_id=trace_id,
            )
            yield f"data: {json.dumps(se.model_dump(mode='json'))}\n\n"

        # Final complete event
        complete_event = StreamEvent(
            event="complete",
            data={"status": "success", "thread_id": thread_id},
            trace_id=trace_id,
        )
        yield f"data: {json.dumps(complete_event.model_dump(mode='json'))}\n\n"

    except Exception as e:
        logger.exception(f"Stream error: {e}")
        error_event = StreamEvent(
            event="error",
            data={"error": str(e)},
            trace_id=trace_id,
        )
        yield f"data: {json.dumps(error_event.model_dump(mode='json'))}\n\n"


@app.post("/api/v1/agents/stream")
async def stream_agent(request: Request, body: StreamRequest) -> StreamingResponse:
    """Stream agent response via SSE."""
    # Extract user info from headers (X-Forwarded auth)
    user_id = request.headers.get("X-Forwarded-Email", body.user_id or "unknown@example.com")

    logger.info(
        f"Stream request | thread={body.thread_id} | user={user_id} | profile={body.profile}"
    )

    # Wrap streaming in api_turn flow tracer
    async def _wrapped_stream():
        with api_turn(thread_id=body.thread_id, endpoint="stream_agent"):
            async for chunk in _stream_graph_events(
                thread_id=body.thread_id,
                user_id=user_id,
                message=body.message,
                profile=body.profile,
                model=body.model,
            ):
                yield chunk

    return StreamingResponse(
        _wrapped_stream(),
        media_type="text/event-stream",
    )


@app.post("/api/v1/agents/invoke")
async def invoke_agent(request: Request, body: StreamRequest) -> dict:
    """Synchronous agent invocation (for testing; prefer /stream for production)."""
    user_id = request.headers.get("X-Forwarded-Email", body.user_id or "unknown@example.com")

    logger.info(
        f"Invoke request | thread={body.thread_id} | user={user_id} | profile={body.profile}"
    )

    graph = await get_agent_graph()

    from langchain_core.messages import HumanMessage

    state: AgentState = {
        "messages": [HumanMessage(content=body.message)],
        "thread_id": body.thread_id,
        "user_id": user_id,
        # Same per-request LLM selection as the streaming path.
        "profile": body.profile,
        "model": body.model,
    }

    config = {
        "configurable": {
            "thread_id": body.thread_id,
        }
    }

    try:
        result = await graph.ainvoke(state, config=config)
        messages = result.get("messages", [])
        return {
            "thread_id": body.thread_id,
            "messages": [m.dict() if hasattr(m, "dict") else str(m) for m in messages],
            "status": "success",
        }
    except Exception as e:
        logger.exception(f"Invoke error: {e}")
        return {
            "thread_id": body.thread_id,
            "messages": [],
            "status": "error",
            "error": str(e),
        }


@app.get("/api/v1/agents/threads/{thread_id}")
async def get_thread(thread_id: str, request: Request) -> dict:
    """Get thread state and history (placeholder for Sprint 2)."""
    user_id = request.headers.get("X-Forwarded-Email", "unknown@example.com")

    logger.info(f"Get thread | thread={thread_id} | user={user_id}")

    # Sprint 1: Return empty thread
    # Sprint 2: Load from checkpointer
    return {
        "thread_id": thread_id,
        "user_id": user_id,
        "messages": [],
        "status": "ok",
    }


@app.delete("/api/v1/agents/threads/{thread_id}")
async def delete_thread(thread_id: str, request: Request) -> dict:
    """Delete thread (placeholder for Sprint 2)."""
    user_id = request.headers.get("X-Forwarded-Email", "unknown@example.com")

    logger.info(f"Delete thread | thread={thread_id} | user={user_id}")

    # Sprint 2: Implement thread deletion
    return {
        "thread_id": thread_id,
        "status": "deleted",
    }


if __name__ == "__main__":
    # Development: run with `uv run uvicorn agent_server.start_server:app --reload --port 8001`
    config = get_config()
    uvicorn.run(
        "agent_server.start_server:app",
        host="0.0.0.0",
        port=8001,
        reload=False,
        log_level=config.log_level.lower(),
    )
