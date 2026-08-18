"""Profile normalization for client-supplied model-picker selections.

This previously imported `agent_server.core.api.routers.agents.requests`,
a module that does not exist in this repo (leftover from the PDF Parser
port), so the whole test session failed at collection.

It now covers `agent_server.core.sub_agents.brain.normalize_profile`, which
clamps the `profile` field sent by the chat UI's model picker before it is
used to resolve an LLM.
"""

import pytest

from agent_server.core.sub_agents.brain import (
    ALLOWED_PROFILES,
    DEFAULT_PROFILE,
    normalize_profile,
)


@pytest.mark.parametrize("profile", sorted(ALLOWED_PROFILES))
def test_allowed_profiles_pass_through(profile: str) -> None:
    assert normalize_profile(profile) == profile


@pytest.mark.parametrize(
    "raw",
    ["  balanced  ", "BALANCED", "Balanced"],
)
def test_normalization_trims_and_lowercases(raw: str) -> None:
    assert normalize_profile(raw) == "balanced"


@pytest.mark.parametrize("empty", [None, "", "   "])
def test_missing_profile_falls_back_to_default(empty) -> None:
    assert normalize_profile(empty) == DEFAULT_PROFILE


@pytest.mark.parametrize(
    "unknown",
    [
        "not_a_profile",
        "vision_document",  # a real registry profile, but not chat-selectable
        "intent_router",
        "guardrail",
        "../../etc/passwd",
    ],
)
def test_unknown_or_non_chat_profiles_fall_back(unknown: str) -> None:
    """A stale or tampered client must never take the agent down."""
    assert normalize_profile(unknown) == DEFAULT_PROFILE


def test_default_profile_is_itself_allowed() -> None:
    assert DEFAULT_PROFILE in ALLOWED_PROFILES
