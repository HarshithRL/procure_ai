"""Log handler factories for global logger hub.

Provides reusable console and file handler creation with proper cleanup,
and InterceptHandler for bridging stdlib logging → Loguru.
"""

from __future__ import annotations

import logging
import sys
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path

from shared_library.global_logger_hub.formatters import STANDARD_FORMATTER

# InterceptHandler is imported optionally (only if loguru is available)
try:
    from loguru import logger as _loguru

    class InterceptHandler(logging.Handler):
        """Handler that intercepts stdlib logging and routes to Loguru.

        This handler bridges Python's stdlib logging (used by LangChain, FastAPI, etc.)
        into Loguru, allowing all logs to be unified in the same output.
        """

        def emit(self, record: logging.LogRecord) -> None:
            level_name = record.levelname
            _loguru.log(level_name, record.getMessage())

    HAS_LOGURU = True
except ImportError:
    HAS_LOGURU = False
    InterceptHandler = None  # type: ignore

# Cache for file handlers to prevent duplicate file access
_file_handlers: dict[str, RotatingFileHandler] = {}
_handler_lock = threading.Lock()


class SafeRotatingFileHandler(RotatingFileHandler):
    """RotatingFileHandler that tolerates Windows file-lock races on rollover.

    On WinError 32 (file in use by another process/thread), defer rotation and
    keep writing to the current file instead of raising a Logging error.
    """

    def doRollover(self) -> None:  # noqa: N802
        try:
            super().doRollover()
        except PermissionError:
            # Defer rotation; keep writing to current file
            return


def make_console_handler(level: int = logging.INFO) -> logging.StreamHandler:
    """Create a console (stderr) handler with standard formatting."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(STANDARD_FORMATTER)
    return handler


def make_file_handler(
    log_path: Path,
    level: int = logging.INFO,
    max_bytes: int = 10_000_000,
    backup_count: int = 10,
) -> RotatingFileHandler:
    """Create a rotating file handler with caching to avoid multiple file access."""
    path_key = str(log_path.resolve())
    with _handler_lock:
        if path_key in _file_handlers:
            return _file_handlers[path_key]

        log_path.parent.mkdir(parents=True, exist_ok=True)

        handler = SafeRotatingFileHandler(
            str(log_path),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
            delay=False,
        )
        handler.setLevel(level)
        handler.setFormatter(STANDARD_FORMATTER)
        _file_handlers[path_key] = handler
        return handler


__all__ = ["make_console_handler", "make_file_handler", "SafeRotatingFileHandler"]

if HAS_LOGURU:
    __all__.append("InterceptHandler")

