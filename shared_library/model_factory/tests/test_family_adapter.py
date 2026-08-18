"""Unit tests for Model Factory family adapters, catalog, and registry load."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

from shared_library.model_factory.catalog import (
    get_model_catalog,
    list_models,
    peek_resolved_model_key,
    peek_resolved_model_label,
)
from shared_library.model_factory.family_adapter import (
    adapt_messages_for_family,
    build_request_params,
    flatten_content_to_text,
    is_chat_routable,
    resolve_family_policy,
)
from shared_library.model_factory.message_constraints import MessageConstraints
from shared_library.model_factory.registry_loader import load_registries
from shared_library.model_factory.resolver import ModelFactoryResolver


def test_registries_load_without_opus_5() -> None:
    bundle = load_registries()
    assert "system.ai.claude-opus-5" not in bundle.models
    assert "system.ai.claude-opus-4-7" in bundle.models
    assert "system.ai.claude-sonnet-4-6" in bundle.models
    assert "system.ai.gpt-oss-120b" in bundle.models
    assert "system.ai.gte-large-en" in bundle.models
    assert bundle.profiles["deep_reasoning"]["default_model"] == (
        "system.ai.claude-opus-4-7"
    )
    assert bundle.profiles["balanced"]["default_model"] == (
        "system.ai.claude-sonnet-4-6"
    )
    assert "claude" in bundle.family_defaults
    assert "gpt_oss" in bundle.family_defaults


def test_catalog_enriched_and_filters_embeddings_flag() -> None:
    catalog = get_model_catalog(surface="chat")
    assert catalog["schema_version"] == 3
    assert catalog["surface"] == "chat"
    assert catalog["effort_map"]["high"] == "deep_reasoning"
    assert catalog["fast_profile"] == "fast_chat"

    ids = {m["id"] for m in catalog["models"]}
    assert "system.ai.claude-opus-5" not in ids
    assert "system.ai.claude-haiku-4-5" in ids
    assert "system.ai.gte-large-en" not in ids
    assert "system.ai.claude-opus-4-5" not in ids

    profile_ids = {p["id"] for p in catalog["profiles"]}
    assert profile_ids == {"fast_chat", "balanced", "deep_reasoning"}
    assert "intent_router" not in profile_ids
    assert "guardrail" not in profile_ids

    haiku = next(m for m in catalog["models"] if "haiku" in m["id"])
    assert "Fast" in haiku["badges"]
    assert haiku["family"] == "claude"
    assert haiku["short_name"] == "Claude Haiku 4.5"
    assert haiku["chat_eligible"] is True

    full = get_model_catalog(surface="all")
    full_ids = {m["id"] for m in full["models"]}
    assert "system.ai.gte-large-en" in full_ids
    embed = next(m for m in full["models"] if "gte-large" in m["id"])
    assert embed["task"] == "llm/v1/embeddings"
    assert embed["swap_safe_for_agent"] is False
    assert embed["routable"] is False
    assert embed["chat_eligible"] is False


def test_build_request_params_strips_temperature_for_opus() -> None:
    """Opus 4.7 uses ADAPTIVE thinking, not the legacy budgeted form.

    The gateway rejects {"type": "enabled", "budget_tokens": N} for this model:
      '"thinking.type.enabled" is not supported for this model. Use
       "thinking.type.adaptive" and "output_config.effort"'
    """
    bundle = load_registries()
    policy = resolve_family_policy(bundle, "system.ai.claude-opus-4-7")
    params = build_request_params(
        policy=policy,
        temperature_supported=False,
        merged_hyperparams={"temperature": 0.7, "max_tokens": 2048},
        enable_thinking=True,
    )
    assert "temperature" not in params
    assert params["max_tokens"] == 2048
    assert "extra_body" in params
    assert params["extra_body"]["thinking"] == {"type": "adaptive"}
    assert params["extra_body"]["output_config"]["effort"] == "high"
    # The rejected legacy key must not be present.
    assert "budget_tokens" not in params["extra_body"]["thinking"]


def test_build_request_params_legacy_thinking_for_older_claude() -> None:
    """Models still on `reasoning_mode: thinking` keep the budgeted form."""
    bundle = load_registries()
    policy = resolve_family_policy(bundle, "system.ai.claude-sonnet-4-6")
    params = build_request_params(
        policy=policy,
        temperature_supported=False,
        merged_hyperparams={"max_tokens": 4096},
        enable_thinking=True,
    )
    thinking = params["extra_body"]["thinking"]
    assert thinking["type"] == "enabled"
    assert thinking["budget_tokens"] == 4095
    assert "output_config" not in params["extra_body"]


def test_build_request_params_reasoning_effort_for_gpt_oss() -> None:
    bundle = load_registries()
    policy = resolve_family_policy(bundle, "system.ai.gpt-oss-20b")
    params = build_request_params(
        policy=policy,
        temperature_supported=True,
        merged_hyperparams={"temperature": 0.0, "max_tokens": 256},
        reasoning_effort="low",
    )
    assert params["extra_body"]["reasoning_effort"] == "low"
    assert "thinking" not in params.get("extra_body", {})


def test_flatten_reasoning_blocks_for_llama_swap() -> None:
    content = [
        {"type": "reasoning", "summary": [{"type": "summary_text", "text": "think"}]},
        {"type": "text", "text": "final answer"},
    ]
    assert flatten_content_to_text(content) == "final answer"

    bundle = load_registries()
    policy = resolve_family_policy(bundle, "system.ai.meta-llama-3-3-70b-instruct")
    constraints = MessageConstraints(
        requires_trailing_user_message=False,
        disallow_assistant_prefill=False,
        merge_system_messages=True,
    )
    msgs = adapt_messages_for_family(
        [
            HumanMessage(content="hi"),
            AIMessage(content=content),
            HumanMessage(content="again"),
        ],
        policy,
        constraints,
    )
    ai = next(m for m in msgs if isinstance(m, AIMessage))
    assert ai.content == "final answer"


def test_embedding_not_chat_routable() -> None:
    bundle = load_registries()
    meta = bundle.models["system.ai.gte-large-en"]
    assert is_chat_routable(meta) is False


def test_resolver_refuses_embedding_override() -> None:
    from shared_library.model_factory.exceptions import ResolveError

    resolver = ModelFactoryResolver()
    try:
        resolver.resolve("fast_chat", model="system.ai.gte-large-en")
        raise AssertionError("expected ResolveError")
    except ResolveError as exc:
        assert "chat" in str(exc).lower() or "routable" in str(exc).lower()


def test_list_models_has_display_names() -> None:
    models = list_models()
    assert all("display_name" in m for m in models)
    assert all("swap_safe_for_agent" in m for m in models)


def test_peek_resolved_model_uses_profile_default() -> None:
    assert peek_resolved_model_key("fast_chat") == "system.ai.claude-haiku-4-5"
    assert peek_resolved_model_label("fast_chat") == "Claude Haiku 4.5"
    assert (
        peek_resolved_model_key(
            "fast_chat", "system.ai.claude-sonnet-4-6"
        )
        == "system.ai.claude-sonnet-4-6"
    )

