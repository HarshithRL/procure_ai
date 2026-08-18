"""Shared production utilities (framework-agnostic).

Canonical implementations for reusable helpers used by agent_server, app,
and scripts. LangChain ``@tool`` wrappers live in ``agent_server.tools`` only.

Subpackages:
  - ``api`` — external HTTP clients (e.g. You.com search)
  - ``documents`` — markdown / chunk text operations
"""

from shared_libraries.utilities.exceptions import (
    DocumentTextError,
    UtilitiesError,
    YouSearchConfigError,
    YouSearchError,
    YouSearchHttpError,
    YouSearchTimeoutError,
)

__all__ = [
    "DocumentTextError",
    "UtilitiesError",
    "YouSearchConfigError",
    "YouSearchError",
    "YouSearchHttpError",
    "YouSearchTimeoutError",
]
