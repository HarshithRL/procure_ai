"""Central logging control panel - single source of truth for all logging configuration.

This module defines:
- Log levels, directories, file paths
- Format strings (development vs production)
- Feature flags (diagnostics, backtraces)
- Namespace resolution (logger name -> app | agent_server | pdf_engine)
- Request-ID correlation (contextvar + loguru patcher)
- bootstrap() function (idempotent, call once at process startup)

Every logging path in this repo funnels through here:

    stdlib logging (flask, uvicorn, langchain, model_factory, web_app, ...)
        -> InterceptHandler on the stdlib ROOT logger
            -> loguru
                -> console sink   (colorized, profile-aware)
                -> app.log        (namespace == "app")
                -> agent.log      (namespace == "agent_server")
                -> engine.log     (namespace == "pdf_engine")
                -> all.log        (everything, cross-cutting debug view)

Usage:
    from shared_library.global_logger_hub.control_panel import bootstrap
    bootstrap()  # Idempotent - safe to call multiple times
"""

from __future__ import annotations

import os
import sys
import uuid
from contextvars import ContextVar
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
    "prod": "INFO",
}
LOG_LEVEL = os.environ.get("LOG_LEVEL", _LOG_LEVEL_DEFAULTS[ENV_PROFILE]).upper()

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
    # control_panel.py lives at <root>/shared_library/global_logger_hub/control_panel.py
    # Three parents up == repo root.
    LOG_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "logs"

# Per-namespace log files
LOG_FILE_AGENT = LOG_DIR / "agent.log"
LOG_FILE_APP = LOG_DIR / "app.log"
LOG_FILE_ENGINE = LOG_DIR / "engine.log"
LOG_FILE_ALL = LOG_DIR / "all.log"

# Rotation policy (shared across all file sinks)
LOG_ROTATION = os.environ.get("LOG_ROTATION", "10 MB")
LOG_RETENTION = int(os.environ.get("LOG_RETENTION", "10"))
LOG_COMPRESSION = os.environ.get("LOG_COMPRESSION", "zip") or None

# ============================================================================
# Namespace Resolution
# ============================================================================

#: Canonical namespaces. Each one owns a dedicated log file.
NAMESPACE_APP = "app"
NAMESPACE_AGENT = "agent_server"
NAMESPACE_ENGINE = "pdf_engine"
NAMESPACE_SYSTEM = "system"

#: Longest-prefix wins. Ordered most-specific first.
_NAMESPACE_PREFIXES: tuple[tuple[str, str], ...] = (
    # --- engine ---
    ("pdf_engine", NAMESPACE_ENGINE),
    ("pdfminer", NAMESPACE_ENGINE),
    ("pypdf", NAMESPACE_ENGINE),
    ("PIL", NAMESPACE_ENGINE),
    # --- agent side ---
    ("agent_server", NAMESPACE_AGENT),
    ("model_factory", NAMESPACE_AGENT),
    ("shared_library.model_factory", NAMESPACE_AGENT),
    ("databricks_connectors", NAMESPACE_AGENT),
    ("shared_library.databricks_connectors", NAMESPACE_AGENT),
    ("langchain", NAMESPACE_AGENT),
    ("langgraph", NAMESPACE_AGENT),
    ("deepagents", NAMESPACE_AGENT),
    ("anthropic", NAMESPACE_AGENT),
    ("openai", NAMESPACE_AGENT),
    ("databricks", NAMESPACE_AGENT),
    ("mlflow", NAMESPACE_AGENT),
    ("uvicorn", NAMESPACE_AGENT),
    ("fastapi", NAMESPACE_AGENT),
    ("starlette", NAMESPACE_AGENT),
    ("sse_starlette", NAMESPACE_AGENT),
    # --- web / app side ---
    ("web_app", NAMESPACE_APP),
    ("app", NAMESPACE_APP),
    ("wsgi", NAMESPACE_APP),
    ("flask", NAMESPACE_APP),
    ("werkzeug", NAMESPACE_APP),
    ("gunicorn", NAMESPACE_APP),
    ("waitress", NAMESPACE_APP),
    ("sqlalchemy", NAMESPACE_APP),
    # --- shared / ops ---
    ("shared_library", NAMESPACE_SYSTEM),
    ("ops", NAMESPACE_SYSTEM),
    ("launcher", NAMESPACE_SYSTEM),
    ("httpx", NAMESPACE_SYSTEM),
    ("httpcore", NAMESPACE_SYSTEM),
    ("urllib3", NAMESPACE_SYSTEM),
    ("requests", NAMESPACE_SYSTEM),
    ("asyncio", NAMESPACE_SYSTEM),
)

#: Fallback for unknown logger names.
DEFAULT_NAMESPACE = NAMESPACE_SYSTEM


def resolve_namespace(logger_name: str | None) -> str:
    """Map an arbitrary (stdlib) logger name to a hub namespace.

    Used by InterceptHandler so third-party and unbound stdlib records land in
    the right per-namespace log file instead of being dumped into one bucket.

    Args:
        logger_name: e.g. ``"web_app.blueprints.bff"``, ``"uvicorn.access"``.

    Returns:
        One of ``app`` | ``agent_server`` | ``pdf_engine`` | ``system``.
    """
    name = str(logger_name or "")
    if not name or name == "root":
        return DEFAULT_NAMESPACE

    best_ns = DEFAULT_NAMESPACE
    best_len = -1
    for prefix, namespace in _NAMESPACE_PREFIXES:
        if name == prefix or name.startswith(prefix + "."):
            if len(prefix) > best_len:
                best_ns = namespace
                best_len = len(prefix)
    return best_ns


# ============================================================================
# Request-ID Correlation
# ============================================================================

_request_id_var: ContextVar[str] = ContextVar("procure_request_id", default="-")


def new_request_id() -> str:
    """Generate a short, log-friendly correlation id."""
    return uuid.uuid4().hex[:12]


def set_request_id(request_id: str | None) -> str:
    """Bind ``request_id`` to the current context (thread / asyncio task).

    Every log line emitted afterwards in this context carries the id, which is
    what makes a browser click traceable across Flask -> BFF -> FastAPI -> LLM.

    Returns:
        The id that was actually set (a new one if ``request_id`` was falsy).
    """
    resolved = request_id or new_request_id()
    _request_id_var.set(resolved)
    return resolved


def get_request_id() -> str:
    """Return the correlation id bound to the current context (``-`` if unset)."""
    return _request_id_var.get()


def reset_request_id() -> None:
    """Clear the correlation id for the current context."""
    _request_id_var.set("-")


def _patch_record(record: dict[str, Any]) -> None:
    """Loguru patcher: guarantee ``component`` / ``namespace`` / ``request_id``.

    Without this, any log emitted through the raw ``loguru.logger`` (i.e. not
    via a wrapper's ``get_logger``) would raise ``KeyError`` against the
    console/file format strings.
    """
    extra = record["extra"]
    extra.setdefault("component", record.get("name") or "-")
    extra.setdefault("namespace", resolve_namespace(record.get("name")))
    # Always refresh request_id from the contextvar unless explicitly bound.
    if not extra.get("request_id") or extra.get("request_id") == "-":
        extra["request_id"] = _request_id_var.get()


# ============================================================================
# Format Strings (Console & Files)
# ============================================================================

# === DEVELOPMENT FORMAT ===
# Colorized, includes component + request id, optimized for reading flow logs
# 17:19:50.693 | INFO     | a1b2c3d4e5f6 | app.blueprints.bff  | [BFF] stream | ...
DEV_FORMAT = (
    "<green>{time:HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<magenta>{extra[request_id]:<12}</magenta> | "
    "<cyan>{extra[component]:<38}</cyan> | "
    "<level>{message}</level>"
)

# === TEST FORMAT ===
# Colorized but compact, single-line structured output
TEST_FORMAT = (
    "<green>{time:HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<magenta>{extra[request_id]}</magenta> | "
    "<cyan>{extra[component]}</cyan> | "
    "{message}"
)

# === PRODUCTION FORMAT ===
# No colors, ISO 8601 timestamp, minimal overhead for performance
PROD_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    "{level: <8} | "
    "{extra[request_id]} | "
    "{extra[component]} | "
    "{message}"
)

# === FILE FORMAT ===
# Plain text, no colors, includes namespace + request id + source line
FILE_FORMAT = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
    "{level: <8} | "
    "{extra[request_id]} | "
    "{extra[namespace]} | "
    "{extra[component]} | "
    "{name}:{function}:{line} | "
    "{message}"
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
_DIAGNOSE_DEFAULTS = {"dev": "true", "test": "true", "prod": "false"}
ENABLE_DIAGNOSE = os.environ.get("LOG_DIAGNOSE", _DIAGNOSE_DEFAULTS[ENV_PROFILE]).lower() == "true"

# Whether to include the full exception backtrace in logs (OFF in prod for brevity)
_BACKTRACE_DEFAULTS = {"dev": "true", "test": "true", "prod": "false"}
ENABLE_BACKTRACE = os.environ.get("LOG_BACKTRACE", _BACKTRACE_DEFAULTS[ENV_PROFILE]).lower() == "true"

# Whether @catch decorator re-raises by default
_RERAISE_DEFAULTS = {"dev": "true", "test": "true", "prod": "true"}
CATCH_RERAISE = os.environ.get("LOG_CATCH_RERAISE", _RERAISE_DEFAULTS[ENV_PROFILE]).lower() == "true"

# Whether the all.log aggregate sink is enabled
ENABLE_ALL_LOG = os.environ.get("LOG_ALL_FILE", "true").lower() == "true"

# ============================================================================
# Global Bootstrap State
# ============================================================================

_BOOTSTRAP_CALLED = False


def _namespace_filter(namespace: str):
    """Build a loguru sink filter that only accepts one namespace."""

    def _filter(record: dict[str, Any]) -> bool:
        return record["extra"].get("namespace") == namespace

    return _filter


def bootstrap(*, force: bool = False) -> None:
    """Initialize Loguru, the stdlib->Loguru bridge, and log file handlers.

    This function is idempotent: calling it multiple times is safe. The second
    and subsequent calls are no-ops unless force=True.

    Args:
        force: If True, reconfigure even if already bootstrapped.

    Effects:
        - Removes Loguru's default sink (stderr)
        - Installs a patcher guaranteeing component/namespace/request_id fields
        - Adds console sink with profile-specific format (DEV/TEST/PROD)
        - Adds rotating file sinks: agent.log, app.log, engine.log, all.log
        - Installs InterceptHandler into the stdlib ROOT logger
        - Resets every pre-existing stdlib handler so nothing double-prints
        - Applies third-party noise suppression
    """
    global _BOOTSTRAP_CALLED

    if _BOOTSTRAP_CALLED and not force:
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Remove Loguru's default stderr sink and any sinks from a prior bootstrap
    _loguru.remove()

    # Global defaults + patcher so format fields never KeyError for unbound loggers
    _loguru.configure(
        extra={"component": "-", "namespace": NAMESPACE_SYSTEM, "request_id": "-"},
        patcher=_patch_record,
    )

    # ------------------------------------------------------------------
    # Console sink
    # ------------------------------------------------------------------
    _loguru.add(
        sys.stderr,
        format=CONSOLE_FORMAT,
        level=LOG_LEVEL,
        colorize=ENV_PROFILE != "prod",
        backtrace=ENABLE_BACKTRACE,
        diagnose=ENABLE_DIAGNOSE,
        enqueue=False,
    )

    # ------------------------------------------------------------------
    # Per-namespace rotating file sinks
    # ------------------------------------------------------------------
    _file_sinks = (
        (LOG_FILE_AGENT, _namespace_filter(NAMESPACE_AGENT)),
        (LOG_FILE_APP, _namespace_filter(NAMESPACE_APP)),
        (LOG_FILE_ENGINE, _namespace_filter(NAMESPACE_ENGINE)),
    )
    for path, sink_filter in _file_sinks:
        _loguru.add(
            str(path),
            format=FILE_FORMAT,
            level=LOG_LEVEL,
            rotation=LOG_ROTATION,
            retention=LOG_RETENTION,
            compression=LOG_COMPRESSION,
            filter=sink_filter,
            backtrace=ENABLE_BACKTRACE,
            diagnose=ENABLE_DIAGNOSE,
            encoding="utf-8",
            enqueue=False,
        )

    # Aggregate sink: every namespace, one chronological file.
    # This is the file to read when tracing a request end-to-end.
    if ENABLE_ALL_LOG:
        _loguru.add(
            str(LOG_FILE_ALL),
            format=FILE_FORMAT,
            level=LOG_LEVEL,
            rotation=LOG_ROTATION,
            retention=LOG_RETENTION,
            compression=LOG_COMPRESSION,
            backtrace=ENABLE_BACKTRACE,
            diagnose=ENABLE_DIAGNOSE,
            encoding="utf-8",
            enqueue=False,
        )

    # ------------------------------------------------------------------
    # Stdlib bridge: InterceptHandler routes stdlib logging -> Loguru
    # ------------------------------------------------------------------
    import logging

    class InterceptHandler(logging.Handler):
        """Route stdlib ``logging`` records into Loguru, namespace-aware."""

        def emit(self, record: logging.LogRecord) -> None:
            # Map stdlib level -> loguru level, falling back to the numeric level.
            try:
                level: str | int = _loguru.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # Walk out of the logging machinery so {name}:{function}:{line}
            # points at the real call site instead of logging/__init__.py.
            frame, depth = sys._getframe(6), 6
            while frame and frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            name = record.name or "root"
            (
                _loguru.bind(
                    component=name,
                    namespace=resolve_namespace(name),
                    request_id=_request_id_var.get(),
                )
                .opt(depth=depth, exception=record.exc_info)
                .log(level, record.getMessage())
            )

    # Wipe every pre-existing stdlib handler (basicConfig, gunicorn, uvicorn,
    # flask) so records reach loguru exactly once.
    for existing in list(logging.root.handlers):
        logging.root.removeHandler(existing)
    logging.root.addHandler(InterceptHandler())
    logging.root.setLevel(logging.DEBUG)

    # Detach handlers from known chatty loggers and force propagation so the
    # root InterceptHandler is the single exit point.
    for orphan in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "gunicorn.error",
        "gunicorn.access",
        "werkzeug",
        "flask.app",
        "sqlalchemy",
        "sqlalchemy.engine",
        "mlflow",
        "httpx",
        "asyncio",
    ):
        orphan_logger = logging.getLogger(orphan)
        orphan_logger.handlers = []
        orphan_logger.propagate = True

    # ------------------------------------------------------------------
    # Third-party noise suppression
    # ------------------------------------------------------------------
    try:
        from shared_library.global_logger_hub.noise_filters import suppress_all_noise

        suppress_all_noise()
    except Exception:  # pragma: no cover - never let logging setup kill the app
        pass

    _BOOTSTRAP_CALLED = True

    bootstrap_logger = _loguru.bind(
        component="global_logger_hub.control_panel", namespace=NAMESPACE_SYSTEM
    )
    bootstrap_logger.info(
        "logging.bootstrapped | profile={} | level={} | sample_rate={} | "
        "diagnose={} | backtrace={} | reraise={} | log_dir={}",
        ENV_PROFILE.upper(),
        LOG_LEVEL,
        LOG_STREAM_SAMPLE_RATE,
        ENABLE_DIAGNOSE,
        ENABLE_BACKTRACE,
        CATCH_RERAISE,
        str(LOG_DIR),
    )


def is_bootstrapped() -> bool:
    """Return True once :func:`bootstrap` has run in this process."""
    return _BOOTSTRAP_CALLED


# ============================================================================
# Public API
# ============================================================================

__all__ = [
    "bootstrap",
    "is_bootstrapped",
    "resolve_namespace",
    "new_request_id",
    "set_request_id",
    "get_request_id",
    "reset_request_id",
    "ENV_PROFILE",
    "LOG_LEVEL",
    "LOG_STREAM_SAMPLE_RATE",
    "LOG_DIR",
    "LOG_FILE_AGENT",
    "LOG_FILE_APP",
    "LOG_FILE_ENGINE",
    "LOG_FILE_ALL",
    "NAMESPACE_APP",
    "NAMESPACE_AGENT",
    "NAMESPACE_ENGINE",
    "NAMESPACE_SYSTEM",
    "DEV_FORMAT",
    "TEST_FORMAT",
    "PROD_FORMAT",
    "FILE_FORMAT",
    "CONSOLE_FORMAT",
    "ENABLE_DIAGNOSE",
    "ENABLE_BACKTRACE",
    "CATCH_RERAISE",
]
