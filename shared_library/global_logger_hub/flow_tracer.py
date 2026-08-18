"""Flow tracing context managers - End-to-end lineage logging for development.

This module provides semantic context managers that emit [FLOW-TAG] log lines
to trace execution across layers (UI → HTTP → API → Graph → LLM → UI).

Each context manager:
1. Emits [ENTER] line on entry with metadata
2. Sets loguru.contextualize() so nested logs inherit thread_id + flow_stage
3. Measures elapsed time
4. Emits [EXIT] line on exit with duration_ms + result_summary
5. On exception: emits [FAIL] line with error class + message

Usage:
    # UI layer
    from shared_library.global_logger_hub.flow_tracer import ui_turn
    with ui_turn(thread_id="abc123", user="user1", prompt="hello"):
        logger.info("Inside the UI turn - automatically carries thread_id + flow_stage")
    
    # API layer
    from shared_library.global_logger_hub.flow_tracer import api_request
    with api_request(thread_id="abc123", endpoint="stream_agent"):
        logger.info("Inside API - has context")
    
    # Graph/Agent layer
    from shared_library.global_logger_hub.flow_tracer import graph_turn
    with graph_turn(thread_id="abc123", node="agent_node"):
        logger.info("Inside graph - has context")
"""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Generator, Any, Optional

from loguru import logger as _loguru

from shared_library.global_logger_hub.control_panel import bootstrap

# Bootstrap on import
bootstrap()

# ============================================================================
# UI Layer: ui_turn
# ============================================================================

@contextmanager
def ui_turn(
    *,
    thread_id: str,
    user: str = "anon",
    prompt: str = "",
) -> Generator[None, None, None]:
    """Context manager for a single user interaction in the UI layer.
    
    Logs the full lifecycle of a user's prompt from input to response display.
    
    Args:
        thread_id: Conversation thread ID (propagated to nested logs)
        user: User identifier (defaults to "anon")
        prompt: User's input text (logged for context)
    
    Effects:
        - Emits [UI-IN] line with prompt metadata
        - Sets contextualize(thread_id, user, flow_stage="ui")
        - Measures elapsed time
        - Emits [UI-OUT] line with duration_ms and result summary
        - On exception: emits [FAIL] with error class and message
    
    Example:
        logger = get_logger("app.home")
        with ui_turn(thread_id="abc123", user="user@example.com", prompt="What tables exist?"):
            for event in stream_chat(prompt):
                logger.debug("[UI-STRM] token received")
    """
    logger = _loguru.bind(namespace="app", component="app.flow.ui_turn")
    start_time = time.time()
    prompt_chars = len(prompt) if prompt else 0
    
    logger.info(
        "[UI-IN] prompt_received | user={} | prompt_chars={} | thread={}",
        user,
        prompt_chars,
        thread_id[:8] if thread_id else "unknown",
    )
    
    try:
        with _loguru.contextualize(
            thread_id=thread_id,
            user=user,
            flow_stage="ui",
        ):
            yield
    except Exception as exc:
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "[FAIL] ui_turn | user={} | duration_ms={} | error={} | msg={}",
            user,
            elapsed_ms,
            type(exc).__name__,
            str(exc)[:100],
        )
        raise
    finally:
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "[UI-OUT] prompt_processed | user={} | duration_ms={} | thread={}",
            user,
            elapsed_ms,
            thread_id[:8] if thread_id else "unknown",
        )


# ============================================================================
# HTTP/Client Layer: api_request (for use in chat_client.py)
# ============================================================================

@contextmanager
def api_request(
    *,
    thread_id: Optional[str] = None,
    endpoint: str = "stream",
    method: str = "POST",
) -> Generator[None, None, None]:
    """Context manager for HTTP requests from client to agent server.
    
    Traces outbound HTTP calls and their responses.
    
    Args:
        thread_id: Conversation thread ID (or None if new)
        endpoint: Endpoint name (e.g., "stream_agent", "invoke_agent")
        method: HTTP method (defaults to "POST")
    
    Effects:
        - Emits [HTTP-OUT] line before request
        - Sets contextualize(thread_id, flow_stage="http")
        - Measures elapsed time
        - Emits [HTTP-IN] line with response metadata
        - On exception: emits [FAIL] with error class
    
    Example:
        logger = get_logger("app.chat_client")
        with api_request(thread_id="abc123", endpoint="stream_agent"):
            for event in client.stream(url, ...):
                logger.debug("[HTTP-STREAM] event received")
    """
    logger = _loguru.bind(namespace="app", component="app.flow.api_request")
    start_time = time.time()
    thread_short = thread_id[:8] if thread_id else "new"
    
    logger.debug(
        "[HTTP-OUT] {} {} | thread={} | endpoint={}",
        method,
        endpoint,
        thread_short,
        endpoint,
    )
    
    try:
        with _loguru.contextualize(
            thread_id=thread_id or "unknown",
            flow_stage="http",
        ):
            yield
    except Exception as exc:
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "[FAIL] http_request | endpoint={} | duration_ms={} | error={} | msg={}",
            endpoint,
            elapsed_ms,
            type(exc).__name__,
            str(exc)[:100],
        )
        raise
    finally:
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.debug(
            "[HTTP-IN] response_received | endpoint={} | duration_ms={} | thread={}",
            endpoint,
            elapsed_ms,
            thread_short,
        )


# ============================================================================
# API Server Layer: api_turn (for use in router.py)
# ============================================================================

@contextmanager
def api_turn(
    *,
    thread_id: str,
    endpoint: str = "unknown",
) -> Generator[None, None, None]:
    """Context manager for a single API request in the server (router.py).
    
    Traces server-side request processing.
    
    Args:
        thread_id: Conversation thread ID
        endpoint: API endpoint name (e.g., "stream_agent", "invoke_agent")
    
    Effects:
        - Emits [API-IN] line on entry
        - Sets contextualize(thread_id, flow_stage="api")
        - Measures elapsed time
        - Emits [API-OUT] line with duration_ms
        - On exception: emits [FAIL] with error details
    
    Example:
        logger = get_logger("agent_server.api.router")
        with api_turn(thread_id="abc123", endpoint="stream_agent"):
            async for event in graph.astream_events(...):
                logger.debug("[API-STREAM] event generated")
    """
    logger = _loguru.bind(namespace="agent_server", component="agent_server.flow.api_turn")
    start_time = time.time()
    
    logger.info(
        "[API-IN] {} | thread={} | endpoint={}",
        endpoint,
        thread_id[:8],
        endpoint,
    )
    
    try:
        with _loguru.contextualize(
            thread_id=thread_id,
            flow_stage="api",
        ):
            yield
    except Exception as exc:
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "[FAIL] api_turn | endpoint={} | duration_ms={} | error={} | msg={}",
            endpoint,
            elapsed_ms,
            type(exc).__name__,
            str(exc)[:100],
        )
        raise
    finally:
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "[API-OUT] {} | thread={} | duration_ms={}",
            endpoint,
            thread_id[:8],
            elapsed_ms,
        )


# ============================================================================
# Graph/Agent Layer: graph_turn
# ============================================================================

@contextmanager
def graph_turn(
    *,
    thread_id: str,
    node: str = "unknown",
) -> Generator[None, None, None]:
    """Context manager for a single graph node execution.
    
    Traces LangGraph node execution (agent_node, approval_node, etc.).
    
    Args:
        thread_id: Conversation thread ID
        node: Node name (e.g., "agent_node", "approval_node")
    
    Effects:
        - Emits [NODE] enter line
        - Sets contextualize(thread_id, node, flow_stage="graph")
        - Measures elapsed time
        - Emits [NODE] exit line with duration_ms
        - On exception: emits [FAIL] with error details
    
    Example:
        logger = get_logger("agent_server.agent")
        with graph_turn(thread_id="abc123", node="agent_node"):
            response = await agent.ainvoke(messages)
            logger.debug("[LLM-OUT] response received")
    """
    logger = _loguru.bind(namespace="agent_server", component="agent_server.flow.graph_turn")
    start_time = time.time()
    
    logger.debug(
        "[NODE] {} | entered | thread={}",
        node,
        thread_id[:8],
    )
    
    try:
        with _loguru.contextualize(
            thread_id=thread_id,
            node=node,
            flow_stage="graph",
        ):
            yield
    except Exception as exc:
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "[FAIL] graph_turn | node={} | duration_ms={} | error={} | msg={}",
            node,
            elapsed_ms,
            type(exc).__name__,
            str(exc)[:100],
        )
        raise
    finally:
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.debug(
            "[NODE] {} | exited | duration_ms={} | thread={}",
            node,
            elapsed_ms,
            thread_id[:8],
        )


# ============================================================================
# LLM Layer: llm_turn (for use in agent.py or harness)
# ============================================================================

@contextmanager
def llm_turn(
    *,
    thread_id: str,
    model: str = "unknown",
    message_count: int = 0,
) -> Generator[None, None, None]:
    """Context manager for LLM invocation within an agent node.
    
    Traces LLM calls (ainvoke, invoke, etc.) for latency and token tracking.
    
    Args:
        thread_id: Conversation thread ID
        model: Model name (e.g., "claude-3-opus", "gpt-4")
        message_count: Number of messages in prompt
    
    Effects:
        - Emits [LLM-OUT] call line
        - Sets contextualize(thread_id, model, flow_stage="llm")
        - Measures elapsed time
        - Emits [LLM-IN] response line with duration_ms
        - On exception: emits [FAIL] with error details
    
    Example:
        logger = get_logger("agent_server.agent")
        with llm_turn(thread_id="abc123", model="claude-3-opus", message_count=3):
            response = await agent.ainvoke(messages)
            logger.debug("[LLM-RESPONSE] content_chars={}", len(response.content))
    """
    logger = _loguru.bind(namespace="agent_server", component="agent_server.flow.llm_turn")
    start_time = time.time()
    
    logger.debug(
        "[LLM-OUT] ainvoke | model={} | msgs={} | thread={}",
        model,
        message_count,
        thread_id[:8],
    )
    
    try:
        with _loguru.contextualize(
            thread_id=thread_id,
            model=model,
            flow_stage="llm",
        ):
            yield
    except Exception as exc:
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.error(
            "[FAIL] llm_turn | model={} | duration_ms={} | error={} | msg={}",
            model,
            elapsed_ms,
            type(exc).__name__,
            str(exc)[:100],
        )
        raise
    finally:
        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.debug(
            "[LLM-IN] response_received | model={} | duration_ms={} | thread={}",
            model,
            elapsed_ms,
            thread_id[:8],
        )


# ============================================================================
# Public API
# ============================================================================

__all__ = [
    "ui_turn",
    "api_request",
    "api_turn",
    "graph_turn",
    "llm_turn",
]

