"""Logging facade for agent_server."""

from __future__ import annotations

import logging
from typing import Optional

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)
