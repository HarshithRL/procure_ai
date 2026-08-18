"""Brain agent — LangChain create_agent harness.

Direct port of PDF Parser's harness/main_agent.py.
Ported to procurement domain with minimal tools (Sprint 1).
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from typing_extensions import NotRequired, TypedDict

from agent_server.core.context import get_brain_system_prompt
from agent_server.core.models.mock import MockChatModel
from shared_library.model_factory import resolve_chat_model
from shared_library.databricks_connectors.utils.exceptions import AuthError
from shared_library.model_factory.exceptions import AuthBridgeError

logger = logging.getLogger(__name__)

BRAIN_AGENT_ID = "brain"


class BrainAgentState(TypedDict):
    """Brain agent private state (subgraph)."""

    messages: list[Any]
    thread_id: NotRequired[str]
    user_id: NotRequired[Optional[str]]
    session_id: NotRequired[Optional[str]]


def build_brain_agent(model: Optional[BaseChatModel] = None) -> Any:
    """Build and compile the Brain agent using LangChain create_agent.

    Args:
        model: Chat model. Defaults to model_factory resolution of "balanced" profile.
               If Databricks auth unavailable, falls back to MockChatModel.

    Returns:
        Compiled agent graph (CompiledStateGraph).
    """
    if model is None:
        try:
            model = resolve_chat_model(profile="balanced")
            logger.info("Brain agent resolved model via model_factory (profile=balanced)")
        except (AuthError, AuthBridgeError, ValueError) as exc:
            # Databricks auth unavailable. In local dev, this is expected without credentials.
            # Options to fix:
            # 1. Local dev (recommended): 
            #    - Run: databricks auth login
            #    - Or set: DATABRICKS_HOST + DATABRICKS_TOKEN env vars
            # 2. For testing without auth: Use MockChatModel (dev only)
            # 3. Deployed on Databricks Apps: Service principal auto-injected, no action needed
            
            import os
            if os.getenv("USE_MOCK_MODEL", "false").lower() == "true":
                # Explicitly requested mock model (for testing)
                logger.warning(
                    f"Databricks auth failed ({type(exc).__name__}), "
                    "but USE_MOCK_MODEL=true. Using MockChatModel."
                )
                model = MockChatModel()
            else:
                # Default: require real auth. User must set up credentials.
                logger.error(
                    f"Databricks auth failed: {type(exc).__name__}\n\n"
                    f"To authenticate locally:\n"
                    f"  1. Run: databricks auth login\n"
                    f"  2. Or set env vars:\n"
                    f"     - DATABRICKS_HOST=https://adb-7181820732839861.1.azuredatabricks.net\n"
                    f"     - DATABRICKS_TOKEN=<your-token>\n\n"
                    f"For testing without auth, set: USE_MOCK_MODEL=true\n\n"
                    f"Original error:\n{exc}"
                )
                raise
        except Exception as exc:
            # Other exceptions are unexpected; re-raise
            logger.error(f"Failed to resolve model (unexpected error): {exc}")
            raise

    # Load system prompt
    system_prompt = get_brain_system_prompt(prefer_registry=True)

    # Sprint 1: No tools. Tools added in Sprint 2 (memory lookup, web search stub).
    tools: list[Any] = []

    # Create and compile the agent graph using create_agent
    # Returns: CompiledStateGraph[AgentState, None, InputAgentState, OutputAgentState]
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        name=BRAIN_AGENT_ID,
    )

    logger.info(f"Brain agent compiled | tools={len(tools)} | model_type={type(model).__name__}")
    return agent


# Singleton with cooldown (follows PDF Parser pattern)
_brain_instance: Optional[Any] = None
_brain_error: Optional[tuple[float, Exception]] = None


def get_brain(force_new: bool = False) -> Any:
    """Get or create singleton brain agent.

    On first construction failure, memoizes the error for 30 seconds
    so repeated calls re-raise immediately rather than retrying.

    Args:
        force_new: Ignore singleton; build a new instance.

    Returns:
        Compiled brain agent graph.
    """
    global _brain_instance, _brain_error
    import time

    if force_new:
        return build_brain_agent()

    if _brain_instance is not None:
        return _brain_instance

    # If we recently failed, re-raise within cooldown
    if _brain_error is not None:
        error_time, error = _brain_error
        if time.time() - error_time < 30.0:
            raise error
        # Cooldown expired; forget and try again
        _brain_error = None

    try:
        _brain_instance = build_brain_agent()
        return _brain_instance
    except Exception as e:
        # Memoize failure with timestamp
        _brain_error = (time.time(), e)
        raise


def reset_brain() -> None:
    """Reset brain singleton (for testing)."""
    global _brain_instance, _brain_error
    _brain_instance = None
    _brain_error = None
