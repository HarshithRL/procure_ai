"""Quick check that optional effort/fast aliases normalize to profiles."""

from agent_server.core.api.routers.agents.requests import normalize_profile_selection


def test_normalize_effort_and_fast() -> None:
    assert normalize_profile_selection(effort="high") == "deep_reasoning"
    assert normalize_profile_selection(effort="medium") == "balanced"
    assert normalize_profile_selection(effort="low") == "fast_chat"
    assert normalize_profile_selection(fast=True, effort="high") == "fast_chat"
    assert normalize_profile_selection(profile="vision_document") == "vision_document"
