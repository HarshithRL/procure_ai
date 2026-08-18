"""App layer logger wrapper - Loguru-based for UI / Flask web_app.

Provides:
- get_logger(name) - Returns Loguru logger bound to app namespace
- ui_event(page, user, doc_id) - Context manager for page-scoped logging
- catch(page, reraise) - Decorator + context manager (never re-raises by default for UI stability)

Usage:
    from shared_library.global_logger_hub.app_logger_wrapper import get_logger, ui_event, catch
    
    logger = get_logger("web_app.home")
    
    def handle_upload(uploaded_file):
        with ui_event(page="Home", user=user_id):
            with catch(page="Home", reraise=False):
                result = ingest_pdf(uploaded_file)
                logger.info("Upload successful")
"""

from .wrapper import get_logger, ui_event, catch
from ..flow_tracer import ui_turn, api_request, api_turn, graph_turn, llm_turn

__all__ = ["get_logger", "ui_event", "catch", "ui_turn", "api_request", "api_turn", "graph_turn", "llm_turn"]

