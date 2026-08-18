"""Unit tests for Model Factory message-constraint adaptation."""

from __future__ import annotations

from typing import Any, List, Optional
from unittest.mock import MagicMock

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import tool

from shared_library.model_factory.chat_model_wrapper import (
    ConstraintAwareBoundRunnable,
    ConstraintAwareChatModel,
    wrap_with_message_constraints,
)
from shared_library.model_factory.message_constraints import (
    MessageConstraints,
    adapt_messages_for_invoke,
    get_message_constraints,
)
from shared_library.model_factory.registry_loader import load_registries


def _text(content: Any) -> str:
    return content if isinstance(content, str) else str(content)


CLAUDE_CONSTRAINTS = MessageConstraints(
    requires_trailing_user_message=True,
    disallow_assistant_prefill=True,
    merge_system_messages=True,
)

PERMISSIVE_CONSTRAINTS = MessageConstraints(
    requires_trailing_user_message=False,
    disallow_assistant_prefill=False,
    merge_system_messages=True,
)


class _RecordingChatModel(BaseChatModel):
    """Minimal chat model that records the last messages it received."""

    last_messages: List[Any] = []

    @property
    def _llm_type(self) -> str:
        return "recording"

    def _generate(
        self,
        messages: List[Any],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        type(self).last_messages = list(messages)
        return ChatResult(
            generations=[
                ChatGeneration(message=AIMessage(content="ok")),
            ]
        )

    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
        bound = MagicMock(name="bound_tools")
        bound.invoke = MagicMock(
            side_effect=lambda msgs, config=None, **kw: AIMessage(content="tool-bound")
        )

        async def _ainvoke(msgs, config=None, **kw):
            return AIMessage(content="tool-bound")

        bound.ainvoke = _ainvoke
        bound._tools = tools
        return bound


def test_claude_upload_summarize_shape_ends_with_human():
    """Reproduce the failed MLflow turn: Human → AI status → System doc."""
    messages = [
        SystemMessage(content="# Agent system prompt"),
        HumanMessage(content="summarize the doc"),
        AIMessage(
            content=(
                "Parsed `Obsidian.pdf` — 4 page(s), "
                "status=repaired, document_id=abc."
            )
        ),
        SystemMessage(content="[Active PDF document]\nFull markdown here"),
    ]
    adapted = adapt_messages_for_invoke(messages, CLAUDE_CONSTRAINTS)

    assert adapted, "adapted messages must not be empty"
    assert isinstance(adapted[0], SystemMessage)
    assert "Agent system prompt" in adapted[0].content
    assert "Active PDF document" in adapted[0].content
    assert isinstance(adapted[-1], HumanMessage)
    assert "summarize the doc" in adapted[-1].content
    assert "Pipeline status" in adapted[-1].content
    assert not any(isinstance(m, AIMessage) for m in adapted)


def test_permissive_keeps_assistant_trailing_after_system_merge():
    messages = [
        SystemMessage(content="sys-a"),
        HumanMessage(content="hi"),
        AIMessage(content="Parsed ok"),
        SystemMessage(content="sys-b"),
    ]
    adapted = adapt_messages_for_invoke(messages, PERMISSIVE_CONSTRAINTS)
    assert isinstance(adapted[0], SystemMessage)
    assert "sys-a" in adapted[0].content and "sys-b" in adapted[0].content
    assert isinstance(adapted[1], HumanMessage)
    assert isinstance(adapted[2], AIMessage)
    assert adapted[-1].content == "Parsed ok"


def test_requires_trailing_user_appends_continue_prompt():
    messages = [
        SystemMessage(content="sys"),
        HumanMessage(content="hi"),
        AIMessage(content="hello"),
    ]
    constraints = MessageConstraints(
        requires_trailing_user_message=True,
        disallow_assistant_prefill=False,
        merge_system_messages=True,
    )
    adapted = adapt_messages_for_invoke(messages, constraints)
    assert isinstance(adapted[-1], HumanMessage)
    assert "continue" in adapted[-1].content.lower()


def test_tool_turn_not_folded():
    """ToolMessage after human must not be destroyed by prefill folding."""
    messages = [
        HumanMessage(content="search"),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "search_document",
                    "args": {},
                    "id": "1",
                    "type": "tool_call",
                }
            ],
        ),
        ToolMessage(content="hit", tool_call_id="1"),
    ]
    adapted = adapt_messages_for_invoke(messages, CLAUDE_CONSTRAINTS)
    assert any(isinstance(m, ToolMessage) for m in adapted)
    assert isinstance(adapted[-1], ToolMessage)
    assert not any(
        isinstance(m, HumanMessage) and "continue" in _text(m.content).lower()
        for m in adapted
    )


def test_get_message_constraints_from_runtime_registry():
    bundle = load_registries()
    caps = get_message_constraints(bundle, "system.ai.claude-opus-4-8")
    assert caps.requires_trailing_user_message is True
    assert caps.disallow_assistant_prefill is True
    assert caps.merge_system_messages is True


def test_message_constraints_defaults_when_absent():
    caps = MessageConstraints.from_capability_doc({"features": {}})
    assert caps.requires_trailing_user_message is False
    assert caps.disallow_assistant_prefill is False
    assert caps.merge_system_messages is True


def test_wrap_returns_constraint_aware_model():
    bundle = load_registries()
    inner = _RecordingChatModel()
    wrapped = wrap_with_message_constraints(
        inner,
        model_key="system.ai.claude-opus-4-8",
        bundle=bundle,
    )
    assert isinstance(wrapped, ConstraintAwareChatModel)
    assert wrapped.constraints.disallow_assistant_prefill is True

    result = wrapped.invoke(
        [
            HumanMessage(content="summarize"),
            AIMessage(content="Parsed `x.pdf` — 1 page(s)."),
            SystemMessage(content="[Active PDF document] body"),
        ]
    )
    assert isinstance(result, AIMessage)
    last = _RecordingChatModel.last_messages
    assert isinstance(last[-1], HumanMessage)
    assert not any(isinstance(m, AIMessage) for m in last)


def test_bind_tools_preserves_constraints():
    bundle = load_registries()
    inner = _RecordingChatModel()
    wrapped = wrap_with_message_constraints(
        inner,
        model_key="system.ai.claude-haiku-4-5",
        bundle=bundle,
    )

    @tool
    def ping() -> str:
        """Ping tool."""
        return "pong"

    bound = wrapped.bind_tools([ping])
    assert isinstance(bound, ConstraintAwareBoundRunnable)
    assert bound.constraints.requires_trailing_user_message is True

    out = bound.invoke(
        [
            HumanMessage(content="summarize"),
            AIMessage(content="Parsed ok"),
        ]
    )
    assert isinstance(out, AIMessage)
    call_args = bound._bound.invoke.call_args
    adapted_msgs = call_args[0][0]
    assert isinstance(adapted_msgs[-1], HumanMessage)


def test_adapt_strips_message_name_field():
    """Verify .name field is stripped from all messages unconditionally.

    The deepagents framework tags subagent responses with a .name field,
    which Anthropic's Messages API does not support. This test ensures
    the field is removed before sending to the model endpoint.
    """
    messages = [
        SystemMessage(content="sys", name="system_agent"),
        HumanMessage(content="hi", name="user_agent"),
        AIMessage(content="hello", name="doc_parser"),
        AIMessage(content="status", name="status_agent"),
    ]

    # Test with permissive constraints (no adaptation needed)
    adapted = adapt_messages_for_invoke(messages, PERMISSIVE_CONSTRAINTS)
    for msg in adapted:
        assert getattr(msg, "name", None) is None, f"Message {type(msg).__name__} still has .name set"

    # Test with strict constraints (full adaptation runs)
    adapted = adapt_messages_for_invoke(messages, CLAUDE_CONSTRAINTS)
    for msg in adapted:
        assert getattr(msg, "name", None) is None, f"Message {type(msg).__name__} still has .name set"

