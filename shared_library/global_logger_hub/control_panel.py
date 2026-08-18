"""Central logging control panel - single source of truth for all logging configuration.

This module defines:
- Log levels, directories, file paths
- Format strings (development vs production)
- Feature flags (diagnostics, backtraces)
- bootstrap() function (idempotent, call once at process startup)

All wrapper modules (agent_logger_wrapper, app_logger_wrapper, and legacy pdf_engine.logger)
import and call bootstrap() to initialize Loguru and the stdlib→Loguru bridge.

Usage:
    from shared_library.global_logger_hub.control_panel import bootstrap
    bootstrap()  # Idempotent - safe to call multiple times
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from loguru import logger as _loguru

# ============================================================================
# Environment Profile (dev, test, prod)
# ============================================================================

ENV_PROFILE = os.environ.get("ENV_PROFILE", "dev").lower()
if ENV_PROFILE not in ("dev", "test", "prod"):
    ENV_PROFILE = "dev"

# ============================================================================
# Configuration (read from environment or defaults)
# ============================================================================

# Log level for console and files
# Defaults: dev=DEBUG, test=INFO, prod=WARNING
_LOG_LEVEL_DEFAULTS = {
    "dev": "DEBUG",
    "test": "INFO",
    "prod": "WARNING",
}
LOG_LEVEL = os.environ.get("LOG_LEVEL", _LOG_LEVEL_DEFAULTS[ENV_PROFILE])

# Log stream sample rate: log every Nth token in SSE streams
# Defaults: dev=1 (every token), test=10 (every 10th), prod=0 (disabled)
_SAMPLE_RATE_DEFAULTS = {
    "dev": "1",      # Every token (verbose)
    "test": "10",    # Every 10th token (moderate)
    "prod": "0",     # No token logs (quiet)
}
LOG_STREAM_SAMPLE_RATE = int(os.environ.get("LOG_STREAM_SAMPLE_RATE", _SAMPLE_RATE_DEFAULTS[ENV_PROFILE]))

# Log directory (defaults to data/logs in project root)
_LOG_DIR_ENV = os.environ.get("LOG_DIR")
if _LOG_DIR_ENV:
    LOG_DIR = Path(_LOG_DIR_ENV)
else:
    # Project root: control_panel.py is under shared_libraries/global_logger_hub/
    # Two levels up from here to reach the component root
    LOG_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "logs"

# Per-namespace log files
LOG_FILE_AGENT = LOG_DIR / "agent.log"
LOG_FILE_APP = LOG_DIR / "app.log"
LOG_FILE_ENGINE = LOG_DIR / "engine.log"

# ============================================================================
# Format Strings (Console & Files)
# ============================================================================

# === DEVELOPMENT FORMAT ===
# Colorized, includes component names, optimized for reading flow logs
# Example: 17:19:50.693 | INFO     | app.flow.ui_turn                  | [UI-IN] prompt_received | ...
DEV_FORMAT = (
    "<green>{time:HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{extra[component]:<40}</cyan> | "
    "{message}"
)

# === TEST FORMAT ===
# Colorized but more compact, single-line structured output
# Example: 17:19:50.693 | INFO | app.flow.ui_turn | [UI-IN] prompt_received | user=test | thread=abc12345
TEST_FORMAT = (
    "<green>{time:HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan> | "
    "{message}"
)

# === PRODUCTION FORMAT ===
# No colors, ISO 8601 timestamp, minimal overhead for performance
# Example: 2026-08-09 17:19:50.693 | INFO     | app.flow.ui_turn | [UI-IN] prompt_received | ...
PROD_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    "<level>{level: <8}</level> | "
    "{name} | "
    "{message}"
)

# === FILE FORMAT ===
# Plain text, no colors, includes module path and line number for debugging
FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    "{level: <8} | "
    "{name}:{line} | "
    "{message}"
)

# === EXCEPTION FORMAT ===
# Full traceback with locals when LOG_DIAGNOSE=true
EXCEPTION_FORMAT = (
    "<red>{time:YYYY-MM-DD HH:mm:ss}</red> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}:{line}</cyan> | "
    "{message}\n"
    "{extra[exception_brief]}"
)

# Select console format based on environment profile
_CONSOLE_FORMAT_MAP = {
    "dev": DEV_FORMAT,
    "test": TEST_FORMAT,
    "prod": PROD_FORMAT,
}
CONSOLE_FORMAT = _CONSOLE_FORMAT_MAP[ENV_PROFILE]

# ============================================================================
# Feature Flags (Environment-Aware Defaults)
# ============================================================================

# Whether to show local variable values in tracebacks (OFF in prod for security)
# Defaults: dev=true, test=true, prod=false
_DIAGNOSE_DEFAULTS = {
    "dev": "true",
    "test": "true",
    "prod": "false",
}
ENABLE_DIAGNOSE = os.environ.get("LOG_DIAGNOSE", _DIAGNOSE_DEFAULTS[ENV_PROFILE]).lower() == "true"

# Whether to include the full exception backtrace in logs (OFF in prod for brevity)
# Defaults: dev=true, test=true, prod=false
_BACKTRACE_DEFAULTS = {
    "dev": "true",
    "test": "true",
    "prod": "false",
}
ENABLE_BACKTRACE = os.environ.get("LOG_BACKTRACE", _BACKTRACE_DEFAULTS[ENV_PROFILE]).lower() == "true"

# Whether @catch decorator re-raises by default
# Defaults: dev=true, test=true, prod=true (reraise in production for reliability)
_RERAISE_DEFAULTS = {
    "dev": "true",
    "test": "true",
    "prod": "true",
}
CATCH_RERAISE = os.environ.get("LOG_CATCH_RERAISE", _RERAISE_DEFAULTS[ENV_PROFILE]).lower() == "true"

# ============================================================================
# Global Bootstrap State
# ============================================================================

_BOOTSTRAP_CALLED = False


def bootstrap(*, force: bool = False) -> None:
    """Initialize Loguru, the stdlib→Loguru bridge, and log file handlers.
    
    This function is idempotent: calling it multiple times is safe. The second
    and subsequent calls are no-ops unless force=True.
    
    Args:
        force: If True, reconfigure even if already bootstrapped.
    
    Effects:
        - Removes Loguru's default sink (stderr)
        - Adds console sink with profile-specific format (DEV/TEST/PROD)
        - Adds rotating file sinks (one per namespace: agent.log, app.log, engine.log)
        - Installs InterceptHandler into stdlib root logger (bridges stdlib → Loguru)
        - Sets ENABLE_DIAGNOSE and ENABLE_BACKTRACE on the logger based on profile
        - Emits bootstrap message showing active profile and settings
    """
    global _BOOTSTRAP_CALLED
    
    if _BOOTSTRAP_CALLED and not force:
        return
    
    # Ensure log directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    # Remove Loguru's default stderr sink
    _loguru.remove()
    
    # Global defaults so format fields never KeyError for unbound loggers
    _loguru.configure(extra={"component": "-", "namespace": "system"})
    
    # ========================================================================
    # Console Sink (Format & Verbosity Based on Environment Profile)
    # ========================================================================
    _loguru.add(
        sys.stderr,
        format=CONSOLE_FORMAT,
        level=LOG_LEVEL,
        colorize=True,
        backtrace=ENABLE_BACKTRACE,
        diagnose=ENABLE_DIAGNOSE,
    )
    
    # ========================================================================
    # File Sinks (Per-Namespace Rotating Files)
    # ========================================================================
    
    # Agent logger file (filter by namespace="agent_server")
    _loguru.add(
        str(LOG_FILE_AGENT),
        format=FILE_FORMAT,
        level=LOG_LEVEL,
        rotation="10 MB",
        retention=10,
        compression="zip",
        filter=lambda record: record["extra"].get("namespace") == "agent_server",
        backtrace=ENABLE_BACKTRACE,
        diagnose=ENABLE_DIAGNOSE,
    )
    
    # App logger file (filter by namespace="app")
    _loguru.add(
        str(LOG_FILE_APP),
        format=FILE_FORMAT,
        level=LOG_LEVEL,
        rotation="10 MB",
        retention=10,
        compression="zip",
        filter=lambda record: record["extra"].get("namespace") == "app",
        backtrace=ENABLE_BACKTRACE,
        diagnose=ENABLE_DIAGNOSE,
    )
    
    # Engine logger file (filter by namespace="pdf_engine")
    _loguru.add(
        str(LOG_FILE_ENGINE),
        format=FILE_FORMAT,
        level=LOG_LEVEL,
        rotation="10 MB",
        retention=10,
        compression="zip",
        filter=lambda record: record["extra"].get("namespace") == "pdf_engine",
        backtrace=ENABLE_BACKTRACE,
        diagnose=ENABLE_DIAGNOSE,
    )
    
    # ========================================================================
    # Stdlib Bridge: InterceptHandler routes stdlib logging → Loguru
    # ========================================================================
    import logging
    
    class InterceptHandler(logging.Handler):
        """Handler that intercepts stdlib logging and routes to Loguru."""
        
        def emit(self, record: logging.LogRecord) -> None:
            # Get the stdlib level name directly (already a string)
            level_name = record.levelname
            
            # Route through Loguru at the same level.
            # Bind component/namespace so DEV_FORMAT ({extra[component]}) never
            # raises KeyError for stdlib-originated records.
            # Map logger name → Loguru namespace so engine/app/agent file sinks work
            name = str(record.name or "")
            if name.startswith("pdf_engine") or ".pdf_engine" in name:
                ns = "pdf_engine"
            elif name.startswith("agent_server") or name.startswith("agent") or name.startswith("model_factory") or name.startswith("databricks_connectors"):
                ns = "agent_server"
            elif name.startswith("web_app") or name.startswith("app"):
                ns = "app"
            else:
                ns = "agent_server"
            bound = _loguru.bind(component=record.name, namespace=ns)
            try:
                bound.log(level_name, record.getMessage())
            except ValueError:
                # Unknown custom stdlib level - fall back to INFO
                bound.info(record.getMessage())
    
    # Remove any existing handlers from stdlib root logger
    logging.root.handlers = []
    
    # Add the intercept handler
    logging.root.addHandler(InterceptHandler())
    logging.root.setLevel(logging.DEBUG)
    
    # Log bootstrap event with profile info (use .bind to ensure component field exists for DEV format)
    bootstrap_logger = _loguru.bind(component="control_panel", namespace="system")
    bootstrap_logger.info(
        "✓ Logging bootstrapped: ENV_PROFILE={} | "
        "LOG_LEVEL={} | SAMPLE_RATE={} | "
        "DIAGNOSE={} | BACKTRACE={} | RERAISE={} | "
        "console_format={} | log_dir={}",
        ENV_PROFILE.upper(),
        LOG_LEVEL,
        LOG_STREAM_SAMPLE_RATE,
        ENABLE_DIAGNOSE,
        ENABLE_BACKTRACE,
        CATCH_RERAISE,
        "DEV" if ENV_PROFILE == "dev" else "TEST" if ENV_PROFILE == "test" else "PROD",
        str(LOG_DIR),
    )
    
    _BOOTSTRAP_CALLED = True


# ============================================================================
# Public API
# ============================================================================

__all__ = [
    "bootstrap",
    "ENV_PROFILE",
    "LOG_LEVEL",
    "LOG_STREAM_SAMPLE_RATE",
    "LOG_DIR",
    "LOG_FILE_AGENT",
    "LOG_FILE_APP",
    "LOG_FILE_ENGINE",
    "DEV_FORMAT",
    "TEST_FORMAT",
    "PROD_FORMAT",
    "FILE_FORMAT",
    "CONSOLE_FORMAT",
    "ENABLE_DIAGNOSE",
    "ENABLE_BACKTRACE",
    "CATCH_RERAISE",
]

