"""Agent logger wrapper implementation - Loguru-based with LangChain-aware defaults.

This module:
1. Calls bootstrap() once to initialize Loguru and stdlib bridge
2. Provides get_logger(name) bound to agent_server namespace
3. Provides agent_span context manager for request-scoped context
4. Provides @catch decorator and context manager for structured exception handling
"""

from __future__ import annotations

import sys
import traceback
from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from loguru import logger as _loguru

from shared_library.global_logger_hub.control_panel import (
    bootstrap,
    CATCH_RERAISE,
)

# Bootstrap on import (idempotent)
bootstrap()

T = TypeVar("T")


# ============================================================================
# Logger Factory
# ============================================================================

def get_logger(name: str):
    """Get a Loguru logger bound to the agent_server namespace.
    
    Args:
        name: Component or module name (e.g., "agent.harness.main_agent")
    
    Returns:
        Loguru logger with namespace="agent_server" and component=name
    
    Usage:
        logger = get_logger("agent_server.harness.main_agent")
        logger.info("Agent started")  # Includes namespace + component in extra
    """
    return _loguru.bind(namespace="agent_server", component=name)


# ============================================================================
# Context Manager: agent_span
# ============================================================================

@contextmanager
def agent_span(
    *,
    thread_id: str,
    user_id: str = "anon",
    node: str = "",
):
    """Context manager that adds request-scoped context to all logs within the block.
    
    Every log line emitted inside this block will include thread_id, user_id, node
    in the extra fields.
    
    Args:
        thread_id: LangGraph thread ID for this conversation
        user_id: User identifier (defaults to "anon" if not provided)
        node: Current graph node name (e.g., "agent_node", "approval_node")
    
    Usage:
        async def agent_node(state):
            with agent_span(thread_id=state["thread_id"], user_id="user123", node="agent_node"):
                logger.info("Processing message")  # auto includes thread_id, user_id, node
    """
    with _loguru.contextualize(thread_id=thread_id, user_id=user_id, node=node):
        yield


# ============================================================================
# Decorator + Context Manager: @catch
# ============================================================================

def catch(
    *,
    logger: Any | None = None,
    message: str = "Unhandled exception",
    reraise: bool | None = None,
    stage: str = "",
    doc_id: str = "",
) -> Callable:
    """Decorator and context manager for catching, logging, and optionally re-raising exceptions.
    
    When used as a decorator:
        @catch(stage="agent_invoke", reraise=False)
        async def my_function():
            ...
    
    When used as a context manager:
        with catch(stage="agent_invoke", doc_id="doc123"):
            response = await agent.ainvoke(messages)
    
    Args:
        logger: Loguru logger instance (defaults to _loguru)
        message: Base message for the log record
        reraise: Whether to re-raise the exception (defaults to CATCH_RERAISE from control_panel)
        stage: Stage/component name for context
        doc_id: Document ID for context
    
    Returns:
        Decorator function (when called as @catch(...))
        Context manager (when called as with catch(...))
    
    Behavior:
        - Logs the exception at ERROR level with full traceback
        - Includes stage, doc_id in the extra context
        - If reraise=True, re-raises after logging
        - If reraise=False, swallows and continues
    """
    _logger = logger or _loguru
    _reraise = reraise if reraise is not None else CATCH_RERAISE
    
    # ========================================================================
    # Decorator version: @catch(stage="...", reraise=False)
    # ========================================================================
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                _log_exception(
                    _logger,
                    exc,
                    message=message,
                    stage=stage,
                    doc_id=doc_id,
                )
                if _reraise:
                    raise
                return None
        
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                _log_exception(
                    _logger,
                    exc,
                    message=message,
                    stage=stage,
                    doc_id=doc_id,
                )
                if _reraise:
                    raise
                return None
        
        # Return the async or sync wrapper based on original function
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    # ========================================================================
    # Context manager version: with catch(stage="...", reraise=False):
    # ========================================================================
    @contextmanager
    def context_manager():
        try:
            yield
        except Exception as exc:
            _log_exception(
                _logger,
                exc,
                message=message,
                stage=stage,
                doc_id=doc_id,
            )
            if _reraise:
                raise
    
    # Return a context manager AND a decorator (Python's @contextmanager + decorator magic)
    # When used as @catch(...), this object is called with a function
    # When used as with catch(...), it's directly entered
    class CatchProxy:
        def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
            return decorator(func)
        
        def __enter__(self):
            # Keep the SAME generator context manager instance for __exit__.
            # Creating a fresh one in __exit__ makes contextlib advance an
            # un-started generator -> RuntimeError("generator didn't stop").
            self._cm = context_manager()
            return self._cm.__enter__()
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            return self._cm.__exit__(exc_type, exc_val, exc_tb)
        
        async def __aenter__(self):
            # For async context manager usage
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                _log_exception(
                    _logger,
                    exc_val,
                    message=message,
                    stage=stage,
                    doc_id=doc_id,
                )
                if _reraise:
                    return False  # Propagate exception
                return True  # Suppress exception
            return False
    
    return CatchProxy()


# ============================================================================
# Helper: _log_exception
# ============================================================================

def _log_exception(
    logger: Any,
    exc: BaseException,
    *,
    message: str = "Exception",
    stage: str = "",
    doc_id: str = "",
) -> None:
    """Log an exception with structured context.
    
    Args:
        logger: Loguru logger instance
        exc: Exception instance
        message: Base message
        stage: Stage/component context
        doc_id: Document ID context
    """
    # Build structured context
    context_parts = [message]
    if stage:
        context_parts.append(f"stage={stage}")
    if doc_id:
        context_parts.append(f"doc_id={doc_id}")
    
    exc_type = type(exc).__name__
    exc_msg = str(exc)
    
    # Log with exception context
    logger.error(
        "{} | {} | {}",
        " ".join(context_parts),
        exc_type,
        exc_msg,
        exc_info=exc,
    )


# ============================================================================
# Public API
# ============================================================================

__all__ = [
    "get_logger",
    "agent_span",
    "catch",
]

