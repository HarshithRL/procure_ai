"""Brain agent — LangChain create_agent harness.

Direct port of PDF Parser's harness/main_agent.py.
Ported to procurement domain with minimal tools (Sprint 1).
"""

from __future__ import annotations

from typing import Any, Optional

from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from typing_extensions import NotRequired, TypedDict

from shared_library.global_logger_hub import bootstrap, get_agent_logger
from agent_server.core.context import get_brain_system_prompt
from agent_server.core.models.mock import MockChatModel
from shared_library.model_factory import resolve_chat_model
from shared_library.databricks_connectors.utils.exceptions import AuthError
from shared_library.model_factory.exceptions import AuthBridgeError

bootstrap()
logger = get_agent_logger(__name__)

BRAIN_AGENT_ID = "brain"

#: Profile used when the caller supplies nothing. Must exist in
#: shared_library/model_factory/registries/ProfileRegistry.yaml.
DEFAULT_PROFILE = "balanced"

#: Profiles the chat UI is allowed to select (model_picker.html mode chips).
#: Anything else falls back to DEFAULT_PROFILE rather than erroring, so a stale
#: or tampered client cannot take the agent down.
ALLOWED_PROFILES = frozenset({"fast_chat", "balanced", "deep_reasoning"})


def normalize_profile(profile: Optional[str]) -> str:
    """Clamp a client-supplied profile name to a known, allowed profile."""
    if not profile:
        return DEFAULT_PROFILE
    candidate = str(profile).strip().lower()
    if candidate in ALLOWED_PROFILES:
        return candidate
    logger.warning(
        "Unknown model profile %r requested; falling back to %r",
        profile,
        DEFAULT_PROFILE,
    )
    return DEFAULT_PROFILE


class BrainAgentState(TypedDict):
    """Brain agent private state (subgraph)."""

    messages: list[Any]
    thread_id: NotRequired[str]
    user_id: NotRequired[Optional[str]]
    session_id: NotRequired[Optional[str]]


def build_brain_agent(
    model: Optional[BaseChatModel] = None,
    profile: Optional[str] = None,
    model_id: Optional[str] = None,
) -> Any:
    """Build and compile the Brain agent using LangChain create_agent.

    Args:
        model: Explicit chat model object. If given, `profile` and `model_id` are ignored.
        profile: model_factory profile name (fast_chat | balanced |
                 deep_reasoning). Defaults to DEFAULT_PROFILE. This is what the
                 chat UI's model picker selects.
        model_id: Optional model override ID (e.g., "system.ai.claude-opus-4-7").
                 If provided, resolves to that specific model instead of the 
                 profile default.
                 If Databricks auth unavailable, falls back to MockChatModel.

    Returns:
        Compiled agent graph (CompiledStateGraph).
    """
    resolved_profile = normalize_profile(profile)

    if model is None:
        try:
            # If model_id is specified, use it as the override; else resolve by profile
            model = resolve_chat_model(profile=resolved_profile, model=model_id)
            logger.info(
                "Brain agent resolved model via model_factory (profile=%s, model_id=%s)",
                resolved_profile,
                model_id or "(default)",
            )
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

    # Sprint 1: Register analysis tools (query_kg, search_evidence, generate_excel)
    try:
        from agent_server.tools.toolkit import make_analysis_tools
        tools = make_analysis_tools()
    except ImportError as e:
        logger.warning(
            "Failed to load analysis tools: %s. Falling back to empty tools list.",
            e,
        )
        tools: list[Any] = []

    # Create and compile the agent graph using create_agent
    # Returns: CompiledStateGraph[AgentState, None, InputAgentState, OutputAgentState]
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        name=BRAIN_AGENT_ID,
    )

    logger.info(
        "Brain agent compiled | profile=%s | tools=%d | model_type=%s",
        resolved_profile,
        len(tools),
        type(model).__name__,
    )
    return agent


# Per-profile instance cache with per-profile error cooldown.
# Keyed by profile so the chat UI's model picker actually switches models
# instead of every request reusing one hardcoded singleton.
_brain_instances: dict[str, Any] = {}
_brain_errors: dict[str, tuple[float, Exception]] = {}


def get_brain(profile: Optional[str] = None, model_id: Optional[str] = None, force_new: bool = False) -> Any:
    """Get or create the brain agent for a given model profile and optional override.

    On construction failure, memoizes the error for 30 seconds *for that
    profile+model_id key only*, so repeated calls re-raise immediately rather than
    hammering Databricks auth — while a healthy profile stays usable.

    Args:
        profile: model_factory profile name. Defaults to DEFAULT_PROFILE.
        model_id: Optional model override (e.g., "system.ai.claude-opus-4-7").
                 If provided, the cache key includes it so a different override
                 is built as a fresh instance.
        force_new: Ignore the cache; build a fresh instance.

    Returns:
        Compiled brain agent graph.
    """
    import time

    resolved_profile = normalize_profile(profile)
    # Include model_id in cache key so different overrides don't share instances
    cache_key = (resolved_profile, model_id or "")

    if force_new:
        return build_brain_agent(profile=resolved_profile, model_id=model_id)

    cached = _brain_instances.get(cache_key)
    if cached is not None:
        return cached

    # If we recently failed for this profile+model_id, re-raise within cooldown
    failure = _brain_errors.get(cache_key)
    if failure is not None:
        error_time, error = failure
        if time.time() - error_time < 30.0:
            raise error
        # Cooldown expired; forget and try again
        _brain_errors.pop(cache_key, None)

    try:
        instance = build_brain_agent(profile=resolved_profile, model_id=model_id)
        _brain_instances[cache_key] = instance
        return instance
    except Exception as e:
        # Memoize failure with timestamp, scoped to this profile+model_id
        _brain_errors[cache_key] = (time.time(), e)
        raise


def reset_brain() -> None:
    """Reset the brain cache (for testing)."""
    _brain_instances.clear()
    _brain_errors.clear()
