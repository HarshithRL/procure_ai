"""Noise suppression for third-party loggers.

Silences or limits verbosity of external libraries based on module category.
"""

from __future__ import annotations

import logging

# PDF Engine related noise (libraries used by pdf_engine)
_PDF_ENGINE_NOISE = [
    "PIL",                    # Pillow warnings
    "pdfminer",               # PDFMiner debug output
    "pypdf",                  # PyPDF2 noise
    "pdf_inspector",          # Custom PDF tools
]

# Agent system noise (LangGraph, LangChain, LLM SDKs)
_AGENT_NOISE = [
    "langchain",              # LangChain (very chatty)
    "langchain_core",         # LangChain core
    "langgraph",              # LangGraph (deprecation warnings)
    "anthropic",              # Anthropic SDK
    "openai",                 # OpenAI SDK
    "databricks_langchain",   # Databricks LangChain integration
]

# HTTP & API noise
_HTTP_NOISE = [
    "httpx",                  # HTTPX client (request logs)
    "urllib3",                # urllib3 (connection pooling logs)
    "requests",               # Requests library
]

# Framework noise (web, async)
_FRAMEWORK_NOISE = [
    "uvicorn.access",         # Uvicorn access logs (per-request)
    "uvicorn.error",          # Uvicorn error logs
    "werkzeug",               # Flask/Werkzeug
    "streamlit",              # Streamlit framework
]

# Combined noise categories
_ALL_NOISE = _PDF_ENGINE_NOISE + _AGENT_NOISE + _HTTP_NOISE + _FRAMEWORK_NOISE


def _suppress_namespace(namespace: str, level: int = logging.WARNING) -> None:
    """Suppress or limit verbosity of a namespace.
    
    Args:
        namespace: Logger name (e.g., "langchain", "httpx")
        level: Minimum level to display (default: WARNING)
    """
    logger = logging.getLogger(namespace)
    logger.setLevel(level)


def suppress_pdf_engine_noise(level: int = logging.WARNING) -> None:
    """Suppress noise from PDF engine dependencies (Pillow, pdfminer, etc.).
    
    Args:
        level: Minimum level to display (default: WARNING)
    """
    for namespace in _PDF_ENGINE_NOISE:
        _suppress_namespace(namespace, level)


def suppress_agent_noise(level: int = logging.WARNING) -> None:
    """Suppress noise from agent system (LangChain, LangGraph, LLM SDKs).
    
    Args:
        level: Minimum level to display (default: WARNING)
    """
    for namespace in _AGENT_NOISE:
        _suppress_namespace(namespace, level)


def suppress_http_noise(level: int = logging.WARNING) -> None:
    """Suppress noise from HTTP clients and libraries.
    
    Args:
        level: Minimum level to display (default: WARNING)
    """
    for namespace in _HTTP_NOISE:
        _suppress_namespace(namespace, level)


def suppress_framework_noise(level: int = logging.WARNING) -> None:
    """Suppress noise from web frameworks (Uvicorn, Streamlit, Werkzeug).
    
    Args:
        level: Minimum level to display (default: WARNING)
    """
    for namespace in _FRAMEWORK_NOISE:
        _suppress_namespace(namespace, level)


def suppress_all_noise(level: int = logging.WARNING) -> None:
    """Suppress all known noisy namespaces at once.
    
    Args:
        level: Minimum level to display (default: WARNING)
    """
    for namespace in _ALL_NOISE:
        _suppress_namespace(namespace, level)


__all__ = [
    "suppress_pdf_engine_noise",
    "suppress_agent_noise",
    "suppress_http_noise",
    "suppress_framework_noise",
    "suppress_all_noise",
]
