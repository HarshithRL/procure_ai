"""Log formatters for global logger hub.

Provides standard formatting for logs across pdf_engine, agent_server, and app modules.
"""

from __future__ import annotations

import logging

# Standard plain-text formatter (used for all modules)
STANDARD_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
STANDARD_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

STANDARD_FORMATTER = logging.Formatter(STANDARD_FORMAT, datefmt=STANDARD_DATE_FORMAT)

__all__ = ["STANDARD_FORMATTER", "STANDARD_FORMAT", "STANDARD_DATE_FORMAT"]
