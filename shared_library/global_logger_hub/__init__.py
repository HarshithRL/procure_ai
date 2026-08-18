"""Global logging hub — the single logging entry point for the whole repo.

Everything (Flask ``web_app``, FastAPI ``agent_server``, ``model_factory``,
``databricks_connectors``, third-party libraries) funnels through one Loguru
pipeline configured in :mod:`shared_library.global_logger_hub.control_panel`.

Architecture
------------
::

    stdlib logging.getLogger(...)         loguru-bound wrappers
              |                                    |
              v                                    v
      InterceptHandler on ROOT  ------------>   loguru core
                                                   |
              +------------------+-----------------+-----------------+
              |                  |                 |                 |
           console            app.log          agent.log         engine.log
        (profile fmt)     namespace=app   namespace=agent_server  namespace=pdf_engine
                                                   |
                                                all.log (everything)

Quick start
-----------
::

    # 1. Once, at process startup (wsgi.py / start_server.py / run_app.py)
    from shared_library.global_logger_hub import bootstrap
    bootstrap()

    # 2. In web / Flask modules
    from shared_library.global_logger_hub import get_app_logger
    logger = get_app_logger("web_app.blueprints.bff")

    # 3. In agent / model modules
    from shared_library.global_logger_hub import get_agent_logger
    logger = get_agent_logger("agent_server.agent")

    # 4. Plain stdlib still works — it is bridged automatically
    import logging
    logging.getLogger(__name__).info("bridged into loguru")

Correlation
-----------
``set_request_id()`` binds a short id to the current thread / asyncio task.
Every subsequent log line — including third-party stdlib records — carries it,
so a single browser click is greppable across Flask -> BFF -> FastAPI -> LLM::

    grep a1b2c3d4e5f6 data/logs/all.log
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

from shared_library.global_logger_hub.control_panel import (
    ENV_PROFILE,
    LOG_DIR,
    LOG_FILE_AGENT,
    LOG_FILE_ALL,
    LOG_FILE_APP,
    LOG_FILE_ENGINE,
    LOG_LEVEL,
    LOG_STREAM_SAMPLE_RATE,
    NAMESPACE_AGENT,
    NAMESPACE_APP,
    NAMESPACE_ENGINE,
    NAMESPACE_SYSTEM,
    bootstrap,
    get_request_id,
    is_bootstrapped,
    new_request_id,
    reset_request_id,
    resolve_namespace,
    set_request_id,
)

# Backwards-compatible aliases (older code imported these names)
DEFAULT_LOG_DIR = LOG_DIR
DEFAULT_LOG_FILE = LOG_FILE_APP


# ============================================================================
# Utility Functions
# ============================================================================


def step(n: int, total: int, event: str) -> str:
    """Format a fixed pipeline milestone: ``[step 3/5] ingest.store_ok``."""
    return f"[step {n}/{total}] {event}"


def detail(obj: Any) -> str:
    """Serialize ``obj`` for logs with full field detail (no truncation).

    Raw ``bytes`` / ``bytearray`` are never dumped; instead length + sha256
    are recorded so binary payloads stay out of the log file.
    """

    def _normalize(value: Any) -> Any:
        if value is None or isinstance(value, (bool, int, float, str)):
            return value
        if isinstance(value, (bytes, bytearray)):
            return {
                "_type": "bytes",
                "len": len(value),
                "sha256": hashlib.sha256(value).hexdigest(),
            }
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, dict):
            return {str(k): _normalize(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [_normalize(v) for v in value]
        if hasattr(value, "keys") and hasattr(value, "__getitem__"):
            try:
                return {str(k): _normalize(value[k]) for k in value.keys()}
            except Exception:
                return str(value)
        return str(value)

    return json.dumps(_normalize(obj), ensure_ascii=False, default=str, indent=None)


def preview(text: Any, limit: int = 200) -> str:
    """Return a single-line, length-capped preview of ``text`` for log lines."""
    s = str(text).replace("\n", "\\n")
    if len(s) <= limit:
        return s
    return f"{s[:limit]}...(+{len(s) - limit} chars)"


# ============================================================================
# Configuration Entry Points
# ============================================================================


def configure_root_logging(
    level: str | int | None = None,
    *,
    log_dir: str | Path | None = None,
    force: bool = False,
) -> logging.Logger:
    """Compatibility shim — delegates to :func:`bootstrap`.

    Historically this configured a *second*, stdlib-only logging tree with its
    own handlers on the ``pdf_engine`` / ``agent_server`` / ``app`` loggers.
    Running it alongside :func:`bootstrap` produced duplicated console output
    and orphaned log files, because those namespace loggers had
    ``propagate=False`` and therefore never reached the Loguru bridge.

    There is now exactly one pipeline. ``level`` and ``log_dir`` are honoured by
    exporting ``LOG_LEVEL`` / ``LOG_DIR`` *before* the first bootstrap; passing
    them here after bootstrap has run is a no-op.

    Returns:
        The stdlib root logger (which carries the InterceptHandler).
    """
    if level is not None and not is_bootstrapped():
        os.environ.setdefault(
            "LOG_LEVEL",
            logging.getLevelName(level) if isinstance(level, int) else str(level).upper(),
        )
    if log_dir is not None and not is_bootstrapped():
        os.environ.setdefault("LOG_DIR", str(log_dir))

    bootstrap(force=force)
    return logging.getLogger()


def get_logger(name: str) -> logging.Logger:
    """Return a stdlib logger that is bridged into the Loguru pipeline.

    Prefer :func:`get_app_logger` / :func:`get_agent_logger` in new code — they
    return Loguru loggers with brace-style formatting and pre-bound namespaces.
    This function exists so that plain ``logging``-based modules keep working.

    Args:
        name: Fully-qualified module name, e.g. ``"web_app.blueprints.api"``.
    """
    bootstrap()
    return logging.getLogger(name)


# ============================================================================
# Namespace-bound Loguru factories (re-exported from the wrappers)
# ============================================================================

from shared_library.global_logger_hub.agent_logger_wrapper.wrapper import (  # noqa: E402
    agent_span,
)
from shared_library.global_logger_hub.agent_logger_wrapper.wrapper import (  # noqa: E402
    catch as agent_catch,
)
from shared_library.global_logger_hub.agent_logger_wrapper.wrapper import (  # noqa: E402
    get_logger as get_agent_logger,
)
from shared_library.global_logger_hub.app_logger_wrapper.wrapper import (  # noqa: E402
    catch as app_catch,
)
from shared_library.global_logger_hub.app_logger_wrapper.wrapper import (  # noqa: E402
    get_logger as get_app_logger,
)
from shared_library.global_logger_hub.app_logger_wrapper.wrapper import (  # noqa: E402
    ui_event,
)
from shared_library.global_logger_hub.flow_tracer import (  # noqa: E402
    api_request,
    api_turn,
    graph_turn,
    llm_turn,
    ui_turn,
)

__all__ = [
    # bootstrap / config
    "bootstrap",
    "configure_root_logging",
    "is_bootstrapped",
    "resolve_namespace",
    # logger factories
    "get_logger",
    "get_app_logger",
    "get_agent_logger",
    # correlation
    "new_request_id",
    "set_request_id",
    "get_request_id",
    "reset_request_id",
    # spans / tracers
    "ui_event",
    "ui_turn",
    "api_request",
    "api_turn",
    "graph_turn",
    "llm_turn",
    "agent_span",
    "agent_catch",
    "app_catch",
    # helpers
    "detail",
    "step",
    "preview",
    # constants
    "ENV_PROFILE",
    "LOG_LEVEL",
    "LOG_STREAM_SAMPLE_RATE",
    "LOG_DIR",
    "LOG_FILE_APP",
    "LOG_FILE_AGENT",
    "LOG_FILE_ENGINE",
    "LOG_FILE_ALL",
    "NAMESPACE_APP",
    "NAMESPACE_AGENT",
    "NAMESPACE_ENGINE",
    "NAMESPACE_SYSTEM",
    "DEFAULT_LOG_DIR",
    "DEFAULT_LOG_FILE",
]
