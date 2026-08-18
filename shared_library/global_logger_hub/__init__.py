"""Global logging hub for PDF Parser application.

This module provides a unified logging setup for pdf_engine, agent_server, and app modules,
with automatic noise suppression for third-party libraries.

Configured hierarchy:
    root (WARNING)
    ├─ pdf_engine (INFO/DEBUG) → console + rotating file
    ├─ agent_server (INFO/DEBUG) → console + rotating file
    └─ app (WARNING) → console only

Usage:
    from global_logger_hub import configure_root_logging, get_logger
    
    # Bootstrap at app startup
    configure_root_logging()
    
    # In modules
    logger = get_logger("pdf_engine.core.ingestion_gate")  # → pdf_engine logger
    logger = get_logger("agent_server.harness.main_agent")  # → agent_server logger
    logger = get_logger("app.chat")  # → app logger
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from shared_library.global_logger_hub.formatters import STANDARD_FORMATTER
from shared_library.global_logger_hub.handlers import make_console_handler, make_file_handler
from shared_library.global_logger_hub.noise_filters import suppress_all_noise
from shared_library.global_logger_hub.registry import NAMESPACE_CONFIG
from shared_library.global_logger_hub.control_panel import bootstrap
from logging.handlers import RotatingFileHandler

# Resolve log directory from env or use default
_LOG_DIR_ENV = os.environ.get("LOG_DIR")
if _LOG_DIR_ENV:
    DEFAULT_LOG_DIR = Path(_LOG_DIR_ENV)
else:
    # Project root: control_panel and __init__ are under shared_libraries/global_logger_hub/
    # Three levels up from here to reach the component root
    DEFAULT_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "logs"

DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "app.log"

_CONFIGURED = False


# ============================================================================
# Utility Functions
# ============================================================================

def step(n: int, total: int, event: str) -> str:
    """Format a fixed pipeline milestone: ``[step 3/5] ingest.store_ok``."""
    return f"[step {n}/{total}] {event}"


def detail(obj: Any) -> str:
    """Serialize ``obj`` for logs with full field detail (no truncation).

    Raw ``bytes`` / ``bytearray`` are never dumped; instead length + sha256
    are recorded so PDF payloads stay out of the log file.
    """

    def _normalize(value: Any) -> Any:
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, (bytes, bytearray)):
            digest = hashlib.sha256(value).hexdigest()
            return {"_type": "bytes", "len": len(value), "sha256": digest}
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, dict):
            return {str(k): _normalize(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [_normalize(v) for v in value]
        if hasattr(value, "keys") and hasattr(value, "__getitem__"):
            # sqlite3.Row and similar mappings
            try:
                return {str(k): _normalize(value[k]) for k in value.keys()}
            except Exception:
                return str(value)
        return str(value)

    return json.dumps(_normalize(obj), ensure_ascii=False, default=str, indent=None)


def _resolve_level(level: str | int | None) -> int:
    """Resolve log level from string, int, or environment variable."""
    if level is None:
        raw = os.environ.get("LOG_LEVEL", "INFO")
    elif isinstance(level, int):
        return level
    else:
        raw = str(level)
    return getattr(logging, raw.upper(), logging.INFO)


# ============================================================================
# Global Logger Configuration
# ============================================================================

def configure_root_logging(
    level: str | int | None = None,
    *,
    log_dir: str | Path | None = None,
    force: bool = False,
) -> logging.Logger:
    """Configure global logging with separate loggers for each module namespace.

    Args:
        level: Log level name or int. Defaults to env ``LOG_LEVEL`` or ``INFO``.
        log_dir: Directory for the rotating log file. Defaults to env ``LOG_DIR`` or ``data/logs/``.
        force: Reconfigure handlers even if already configured.

    Returns:
        The configured root logger.
    """
    global _CONFIGURED

    if _CONFIGURED and not force:
        return logging.getLogger()

    resolved = _resolve_level(level)

    # Configure root logger (minimal)
    root = logging.getLogger()
    root.setLevel(logging.WARNING)

    # Set up log directory
    directory = Path(log_dir) if log_dir is not None else DEFAULT_LOG_DIR
    directory.mkdir(parents=True, exist_ok=True)
    log_path = directory / "app.log"

    # Drop stale RotatingFileHandlers before re-attach (Streamlit script reruns)
    from shared_library.global_logger_hub import handlers as _handlers_mod

    for namespace in NAMESPACE_CONFIG:
        ns_logger = logging.getLogger(namespace)
        for h in list(ns_logger.handlers):
            if isinstance(h, RotatingFileHandler):
                ns_logger.removeHandler(h)
                try:
                    base = getattr(h, "baseFilename", None)
                    if base:
                        _handlers_mod._file_handlers.pop(str(Path(base).resolve()), None)
                    h.close()
                except Exception:
                    pass

    # Create handlers (will be cached internally)
    console = make_console_handler(level=resolved)
    file_handler = make_file_handler(log_path, level=resolved)

    # Configure loggers for each namespace
    for namespace, config in NAMESPACE_CONFIG.items():
        logger = logging.getLogger(namespace)
        ns_level = config.get("level", resolved)
        logger.setLevel(ns_level)
        logger.propagate = config.get("propagate", False)

        # Add handlers based on config (avoid duplicates on rerun)
        handlers = config.get("handlers", ["console", "file"])
        if "console" in handlers and console not in logger.handlers:
            logger.addHandler(console)
        if "file" in handlers and file_handler not in logger.handlers:
            logger.addHandler(file_handler)

    # Suppress noise from third-party libraries
    suppress_all_noise()

    _CONFIGURED = True
    root_logger = logging.getLogger("pdf_engine")
    root_logger.info(
        "logging.configured path=%s level=%s max_bytes=%s backups=%s",
        log_path,
        logging.getLevelName(resolved),
        10_000_000,
        10,
    )
    return root


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger instance.

    This function supports fully-qualified names that are auto-prefixed with
    a module namespace based on their content.

    Args:
        name: Logger name. Examples:
            - "pdf_engine.core.ingestion_gate" -> pdf_engine.core.ingestion_gate
            - "agent_server.harness.main_agent" -> agent_server.harness.main_agent
            - "app.chat" -> app.chat
            - "ingestion_gate" -> pdf_engine.ingestion_gate (legacy auto-prefix)

    Returns:
        A logging.Logger instance.
    """
    # Ensure logging is configured
    if not _CONFIGURED:
        configure_root_logging()

    # Handle legacy short names (auto-prefix with pdf_engine for backward compatibility)
    if not any(prefix in name for prefix in ("pdf_engine", "agent_server", "app")):
        name = f"pdf_engine.{name}"

    return logging.getLogger(name)


__all__ = [
    "configure_root_logging",
    "get_logger",
    "detail",
    "step",
    "DEFAULT_LOG_DIR",
    "DEFAULT_LOG_FILE",
    "bootstrap",  # New control panel bootstrap
]

