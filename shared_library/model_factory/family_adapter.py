"""Family-aware request/response adaptation for Model Factory swaps.

Keeps a single OpenAI-compatible AI Gateway client while stripping
family-illegal params, building reasoning ``extra_body``, and flattening
Claude reasoning content blocks when the target family expects plain text.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from shared_library.model_factory.message_constraints import MessageConstraints
from shared_library.model_factory.registry_loader import RegistryBundle

_REASONING_BLOCK_TYPES = frozenset({"reasoning", "thinking"})


@dataclass(frozen=True)
class FamilyPolicy:
    """Resolved transport + request policy for one model family."""

    family: str = "claude"
    content_shape: str = "openai_multimodal"
    api_style: str = "openai_chat_completions"
    allow_params: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {"max_tokens", "temperature", "max_retries", "timeout", "stream"}
        )
    )
    strip_when_unsupported: frozenset[str] = field(default_factory=frozenset)
    multiturn: str = "recommended"
    parallel_tool_calls: bool = False
    max_tools: int = 32
    content_blocks: str = "reasoning_and_text"
    strip_reasoning_on_checkpoint: bool = True
    reasoning_extra_body: str = "none"  # none | thinking | reasoning_effort
    reasoning_mode: str = "none"  # from model meta


def _cap_doc(bundle: RegistryBundle, model_key: str) -> Dict[str, Any]:
    caps = bundle.capabilities.get(model_key)
    if isinstance(caps, dict):
        return caps
    for alias, meta in bundle.models.items():
        if isinstance(meta, dict) and meta.get("physical_model") == model_key:
            doc = bundle.capabilities.get(alias)
            if isinstance(doc, dict):
                return doc
    return {}


def _model_meta(bundle: RegistryBundle, model_key: str) -> Dict[str, Any]:
    meta = bundle.models.get(model_key)
    if isinstance(meta, dict):
        return meta
    for _alias, candidate in bundle.models.items():
        if isinstance(candidate, dict) and candidate.get("physical_model") == model_key:
            return candidate
    return {}


def resolve_family_policy(
    bundle: RegistryBundle,
    model_key: str,
) -> FamilyPolicy:
    """Load family defaults from CapabilityRegistry + model reasoning_mode."""
    model = _model_meta(bundle, model_key)
    caps = _cap_doc(bundle, model_key)
    family = str(
        model.get("family") or caps.get("family") or "claude"
    ).strip().lower()

    family_defaults = {}
    # CapabilityRegistry may store family_defaults at document root — loaded
    # via bundle.capabilities only contains the ``capabilities`` mapping.
    # Look up via loader-attached attrs if present.
    raw_family = getattr(bundle, "family_defaults", None)
    if isinstance(raw_family, dict):
        family_defaults = raw_family.get(family) or {}
    if not isinstance(family_defaults, dict):
        family_defaults = {}

    transport = family_defaults.get("transport") or {}
    req = family_defaults.get("request_param_policy") or {}
    tools = family_defaults.get("tool_policy") or {}
    resp = family_defaults.get("response_policy") or {}

    allow = req.get("allow") or [
        "max_tokens",
        "temperature",
        "max_retries",
        "timeout",
        "stream",
    ]
    strip = req.get("strip_when_unsupported") or []

    return FamilyPolicy(
        family=family,
        content_shape=str(transport.get("content_shape") or "openai_multimodal"),
        api_style=str(transport.get("api_style") or "openai_chat_completions"),
        allow_params=frozenset(str(x) for x in allow),
        strip_when_unsupported=frozenset(str(x) for x in strip),
        multiturn=str(tools.get("multiturn") or "recommended"),
        parallel_tool_calls=bool(tools.get("parallel_tool_calls", False)),
        max_tools=int(tools.get("max_tools") or 32),
        content_blocks=str(resp.get("content_blocks") or "text_only"),
        strip_reasoning_on_checkpoint=bool(
            resp.get("strip_reasoning_on_checkpoint", True)
        ),
        reasoning_extra_body=str(
            family_defaults.get("reasoning_extra_body") or "none"
        ),
        reasoning_mode=str(model.get("reasoning_mode") or "none"),
    )


def flatten_content_to_text(content: Any) -> str:
    """Flatten string or multimodal/reasoning content blocks to plain text."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return str(content)

    parts: list[str] = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
            continue
        if not isinstance(block, dict):
            parts.append(str(block))
            continue
        btype = str(block.get("type") or "").lower()
        if btype in _REASONING_BLOCK_TYPES:
            continue
        text = block.get("text")
        if isinstance(text, str):
            parts.append(text)
            continue
        # Claude reasoning summary shape
        summary = block.get("summary")
        if isinstance(summary, list):
            for item in summary:
                if isinstance(item, dict) and isinstance(item.get("text"), str):
                    # skip reasoning summaries when flattening for OSS
                    continue
        if "image_url" in block or btype in {"image_url", "input_image", "image"}:
            # Keep a placeholder so the turn is not empty
            parts.append("[image]")
            continue
        if text is not None:
            parts.append(str(text))
    return "".join(parts)


def adapt_messages_for_family(
    messages: Sequence[BaseMessage],
    policy: FamilyPolicy,
    constraints: MessageConstraints,
) -> List[BaseMessage]:
    """Apply family content_shape then message_constraints."""
    from shared_library.model_factory.message_constraints import (
        adapt_messages_for_invoke,
    )

    shaped: list[BaseMessage] = list(messages)
    if policy.content_shape == "text_string" or policy.strip_reasoning_on_checkpoint:
        shaped = [_flatten_message_content(m, policy) for m in shaped]

    return adapt_messages_for_invoke(shaped, constraints)


def _flatten_message_content(msg: BaseMessage, policy: FamilyPolicy) -> BaseMessage:
    if isinstance(msg, (HumanMessage, SystemMessage)):
        if policy.content_shape == "text_string" and not isinstance(msg.content, str):
            return type(msg)(content=flatten_content_to_text(msg.content))
        return msg
    if isinstance(msg, AIMessage):
        # Preserve tool_calls; flatten content when needed
        content = msg.content
        if policy.content_shape == "text_string" or (
            policy.strip_reasoning_on_checkpoint and not isinstance(content, str)
        ):
            content = flatten_content_to_text(content)
        return AIMessage(
            content=content,
            tool_calls=getattr(msg, "tool_calls", None) or [],
            additional_kwargs=dict(getattr(msg, "additional_kwargs", None) or {}),
            id=getattr(msg, "id", None),
            name=getattr(msg, "name", None),
        )
    return msg


def build_request_params(
    *,
    policy: FamilyPolicy,
    temperature_supported: bool,
    merged_hyperparams: Dict[str, Any],
    enable_thinking: bool = False,
    reasoning_effort: Optional[str] = None,
) -> Dict[str, Any]:
    """Filter hyperparams + optional family ``extra_body`` for init_chat_model."""
    out: Dict[str, Any] = {}
    for key, value in merged_hyperparams.items():
        if value is None:
            continue
        if key not in policy.allow_params and key not in {
            "max_tokens",
            "temperature",
            "max_retries",
            "timeout",
        }:
            continue
        if key == "temperature" and (
            not temperature_supported or "temperature" in policy.strip_when_unsupported
        ):
            continue
        if key == "temperature" and not temperature_supported:
            continue
        out[key] = value

    if not temperature_supported:
        out.pop("temperature", None)

    # Databricks FM: never advertise parallel tool calls
    out.pop("parallel_tool_calls", None)

    extra_body: Dict[str, Any] = {}
    mode = policy.reasoning_extra_body
    if mode == "thinking" and enable_thinking:
        budget = 8000
        max_tok = out.get("max_tokens")
        if isinstance(max_tok, int) and max_tok > 1:
            budget = min(8000, max_tok - 1)
        extra_body["thinking"] = {"type": "enabled", "budget_tokens": budget}
    elif mode == "reasoning_effort":
        effort = reasoning_effort or "low"
        if effort not in {"low", "medium", "high", "minimal"}:
            effort = "low"
        extra_body["reasoning_effort"] = effort

    if extra_body:
        out["extra_body"] = extra_body
    return out


def is_chat_routable(model_meta: Dict[str, Any]) -> bool:
    """Return False for embeddings / non-routable models."""
    if model_meta.get("routable") is False:
        return False
    if model_meta.get("routable_as_chat") is False:
        return False
    task = str(model_meta.get("task") or "llm/v1/chat")
    if "embed" in task.lower():
        return False
    status = str(model_meta.get("status") or "").lower()
    if status in {"deprecated", "retired"}:
        return False
    return True

