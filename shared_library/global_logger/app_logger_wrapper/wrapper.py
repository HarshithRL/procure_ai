"""App logger wrapper implementation - Loguru-based for Streamlit UI layer.

This module:
1. Calls bootstrap() once to initialize Loguru and stdlib bridge
2. Provides get_logger(name) bound to app namespace
3. Provides ui_event context manager for page-scoped context
4. Provides @catch decorator (never re-raises by default to keep UI alive)
"""

from __future__ import annotations

from contextlib import contextmanager
from functools import wraps
from typing import Any, Callable, TypeVar

from loguru import logger as _loguru

from shared_library.global_logger_hub.control_panel import bootstrap

# Bootstrap on import (idempotent)
bootstrap()

T = TypeVar("T")


# ============================================================================
# Logger Factory
# ============================================================================

def get_logger(name: str):
    """Get a Loguru logger bound to the app namespace.
    
    Args:
        name: Component or module name (e.g., "app.home", "app.sidebar")
    
    Returns:
        Loguru logger with namespace="app" and component=name
    
    Usage:
        logger = get_logger("app.home")
        logger.info("User uploaded file")  # Includes namespace + component
    """
    if not name.startswith("app."):
        name = f"app.{name}"
    return _loguru.bind(namespace="app", component=name)


# ============================================================================
# Context Manager: ui_event
# ============================================================================

@contextmanager
def ui_event(
    *,
    page: str,
    user: str = "anon",
    doc_id: str = "",
):
    """Context manager that adds page-scoped context to all logs within the block.
    
    Every log line emitted inside this block will include page, user, doc_id
    in the extra fields. Useful for correlating logs from a single user interaction.
    
    Args:
        page: Streamlit page name (e.g., "Home", "Agent Chat")
        user: User identifier (defaults to "anon" if not provided)
        doc_id: Document ID for context (optional)
    
    Usage:
        def handle_upload(uploaded_file):
            with ui_event(page="Home", user=st.session_state.user_id):
                logger.info("User started upload")
                result = ingest_pdf(uploaded_file)
    """
    with _loguru.contextualize(page=page, user=user, doc_id=doc_id):
        yield


# ============================================================================
# Decorator + Context Manager: @catch
# ============================================================================

def catch(
    *,
    logger: Any | None = None,
    message: str = "UI error",
    reraise: bool = False,
    page: str = "",
    doc_id: str = "",
) -> Callable:
    """Decorator and context manager for catching and logging exceptions in the UI layer.
    
    **Important:** App-layer @catch never re-raises by default (reraise=False).
    This keeps the Streamlit UI alive even when errors occur. Errors are logged
    but the UI continues running.
    
    When used as a decorator:
        @catch(page="Home", reraise=False)
        def handle_upload(uploaded_file):
            ...
    
    When used as a context manager:
        with catch(page="Home", doc_id="doc123"):
            response = agent.invoke(messages)
    
    Args:
        logger: Loguru logger instance (defaults to _loguru)
        message: Base message for the log record
        reraise: Whether to re-raise the exception (defaults to False for app layer)
        page: Page name for context
        doc_id: Document ID for context
    
    Returns:
        Decorator function (when called as @catch(...))
        Context manager (when called as with catch(...))
    
    Behavior:
        - Logs the exception at ERROR level with full traceback
        - Includes page, doc_id in the extra context
        - Never re-raises by default (keeps UI alive)
        - If reraise=True explicitly set, will re-raise (not recommended in production)
    """
    _logger = logger or _loguru
    
    # ========================================================================
    # Decorator version: @catch(page="...", reraise=False)
    # ========================================================================
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T | None:
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                _log_exception(
                    _logger,
                    exc,
                    message=message,
                    page=page,
                    doc_id=doc_id,
                )
                if reraise:
                    raise
                return None
        
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T | None:
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                _log_exception(
                    _logger,
                    exc,
                    message=message,
                    page=page,
                    doc_id=doc_id,
                )
                if reraise:
                    raise
                return None
        
        # Return the async or sync wrapper based on original function
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    # ========================================================================
    # Context manager version: with catch(page="...", reraise=False):
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
                page=page,
                doc_id=doc_id,
            )
            if reraise:
                raise
    
    # Return a context manager AND a decorator
    class CatchProxy:
        def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
            return decorator(func)
        
        def __enter__(self):
            return context_manager().__enter__()
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            return context_manager().__exit__(exc_type, exc_val, exc_tb)
        
        async def __aenter__(self):
            return self
        
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                _log_exception(
                    _logger,
                    exc_val,
                    message=message,
                    page=page,
                    doc_id=doc_id,
                )
                if reraise:
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
    page: str = "",
    doc_id: str = "",
) -> None:
    """Log an exception with structured context.
    
    Args:
        logger: Loguru logger instance
        exc: Exception instance
        message: Base message
        page: Page context
        doc_id: Document ID context
    """
    # Build structured context
    context_parts = [message]
    if page:
        context_parts.append(f"page={page}")
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
    "ui_event",
    "catch",
]

