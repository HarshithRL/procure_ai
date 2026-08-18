"""Logger namespace registry and configuration.

Provides a centralized registry of logger namespaces with their configurations,
enabling runtime extension without modifying core logging code.
"""

from __future__ import annotations

import logging
from typing import Any

# Namespace configuration dictionary
# Format: namespace -> {level, handlers, propagate, description}
NAMESPACE_CONFIG: dict[str, dict[str, Any]] = {
    "pdf_engine": {
        "level": logging.INFO,
        "handlers": ["console", "file"],
        "propagate": False,
        "description": "PDF parsing engine and related tools",
    },
    "agent_server": {
        "level": logging.INFO,
        "handlers": ["console", "file"],
        "propagate": False,
        "description": "Agent system (LangGraph, LangChain, FastAPI)",
    },
    "app": {
        "level": logging.WARNING,
        "handlers": ["console"],
        "propagate": False,
        "description": "Flask BFF / UI layer",
    },
}


def register_namespace(
    name: str,
    level: int = logging.INFO,
    handlers: list[str] | None = None,
    propagate: bool = False,
    description: str = "",
) -> None:
    """Register a new logger namespace at runtime.
    
    Args:
        name: Namespace name (e.g., "my_module")
        level: Log level (default: INFO)
        handlers: List of handler names (default: ["console", "file"])
        propagate: Whether to propagate to parent logger (default: False)
        description: Human-readable description of namespace
    """
    if handlers is None:
        handlers = ["console", "file"]
    
    NAMESPACE_CONFIG[name] = {
        "level": level,
        "handlers": handlers,
        "propagate": propagate,
        "description": description,
    }


def get_namespace_config(name: str) -> dict[str, Any] | None:
    """Get configuration for a specific namespace.
    
    Args:
        name: Namespace name
        
    Returns:
        Configuration dict or None if not found
    """
    return NAMESPACE_CONFIG.get(name)


def list_namespaces() -> dict[str, str]:
    """List all registered namespaces with descriptions.
    
    Returns:
        Dict mapping namespace name to description
    """
    return {name: config.get("description", "") for name, config in NAMESPACE_CONFIG.items()}


__all__ = ["NAMESPACE_CONFIG", "register_namespace", "get_namespace_config", "list_namespaces"]
