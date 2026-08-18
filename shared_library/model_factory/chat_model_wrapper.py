"""Constraint-aware chat model wrapper for Model Factory.

Wraps any ``BaseChatModel`` (or tool-bound Runnable) so message-shape
adaptation from CapabilityRegistry runs on every invoke / astream.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Iterator, List, Optional, Sequence

from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGenerationChunk, ChatResult
from langchain_core.runnables import Runnable, RunnableConfig
from pydantic import ConfigDict, Field

from agent_server.core.logging import get_logger

logger = get_logger("model_factory.chat_model_wrapper")

from shared_library.model_factory.family_adapter import (
    FamilyPolicy,
    adapt_messages_for_family,
    resolve_family_policy,
)
from shared_library.model_factory.message_constraints import MessageConstraints
from shared_library.model_factory.registry_loader import RegistryBundle


def _coerce_to_messages(value: Any) -> List[BaseMessage]:
    """Normalize LanguageModelInput-ish values into a message list."""
    if isinstance(value, list):
        return list(value)
    if isinstance(value, BaseMessage):
        return [value]
    if isinstance(value, str):
        from langchain_core.messages import HumanMessage

        return [HumanMessage(content=value)]
    if isinstance(value, dict) and "messages" in value:
        return list(value["messages"])
    raise TypeError(f"Unsupported chat model input type: {type(value)!r}")


def _adapt(
    messages: List[BaseMessage],
    *,
    constraints: MessageConstraints,
    policy: Optional[FamilyPolicy],
) -> List[BaseMessage]:
    if policy is not None:
        return adapt_messages_for_family(messages, policy, constraints)
    from shared_library.model_factory.message_constraints import (
        adapt_messages_for_invoke,
    )

    return adapt_messages_for_invoke(messages, constraints)


class ConstraintAwareBoundRunnable(Runnable[Any, Any]):
    """Wrap a tool-bound (or otherwise bound) chat Runnable with adaptation."""

    def __init__(
        self,
        bound: Runnable[Any, Any],
        *,
        constraints: MessageConstraints,
        model_key: str,
        family_policy: Optional[FamilyPolicy] = None,
    ) -> None:
        self._bound = bound
        self.constraints = constraints
        self.model_key = model_key
        self.family_policy = family_policy

    def invoke(
        self,
        input: Any,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> Any:
        adapted = _adapt(
            _coerce_to_messages(input),
            constraints=self.constraints,
            policy=self.family_policy,
        )
        return self._bound.invoke(adapted, config=config, **kwargs)

    async def ainvoke(
        self,
        input: Any,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> Any:
        adapted = _adapt(
            _coerce_to_messages(input),
            constraints=self.constraints,
            policy=self.family_policy,
        )
        return await self._bound.ainvoke(adapted, config=config, **kwargs)

    def stream(
        self,
        input: Any,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> Iterator[Any]:
        adapted = _adapt(
            _coerce_to_messages(input),
            constraints=self.constraints,
            policy=self.family_policy,
        )
        yield from self._bound.stream(adapted, config=config, **kwargs)

    async def astream(
        self,
        input: Any,
        config: Optional[RunnableConfig] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Any]:
        adapted = _adapt(
            _coerce_to_messages(input),
            constraints=self.constraints,
            policy=self.family_policy,
        )
        async for chunk in self._bound.astream(adapted, config=config, **kwargs):
            yield chunk

    def bind(self, **kwargs: Any) -> "ConstraintAwareBoundRunnable":
        return ConstraintAwareBoundRunnable(
            self._bound.bind(**kwargs),
            constraints=self.constraints,
            model_key=self.model_key,
            family_policy=self.family_policy,
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._bound, name)


class ConstraintAwareChatModel(BaseChatModel):
    """``BaseChatModel`` that adapts messages before delegating to ``inner``."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    inner: Any = Field(exclude=True)
    model_key: str = "unknown"
    constraints: MessageConstraints = Field(default_factory=MessageConstraints)
    family_policy: Optional[FamilyPolicy] = Field(default=None, exclude=True)

    @property
    def _llm_type(self) -> str:
        inner_type = getattr(self.inner, "_llm_type", None)
        if callable(inner_type):
            try:
                inner_type = inner_type()
            except Exception:  # noqa: BLE001
                inner_type = None
        if isinstance(inner_type, str) and inner_type:
            return f"constraint-aware:{inner_type}"
        return "constraint-aware"

    @property
    def _identifying_params(self) -> dict[str, Any]:
        params: dict[str, Any] = {"model_key": self.model_key}
        inner_params = getattr(self.inner, "_identifying_params", None)
        if isinstance(inner_params, dict):
            params.update(inner_params)
        return params

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        adapted = _adapt(
            messages, constraints=self.constraints, policy=self.family_policy
        )
        return self.inner._generate(
            adapted, stop=stop, run_manager=run_manager, **kwargs
        )

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        adapted = _adapt(
            messages, constraints=self.constraints, policy=self.family_policy
        )
        return await self.inner._agenerate(
            adapted, stop=stop, run_manager=run_manager, **kwargs
        )

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        adapted = _adapt(
            messages, constraints=self.constraints, policy=self.family_policy
        )
        stream_fn = getattr(self.inner, "_stream", None)
        if stream_fn is None:
            # Fallback: non-streaming generate
            result = self._generate(messages, stop=stop, run_manager=run_manager, **kwargs)
            for gen in result.generations:
                msg = gen.message if hasattr(gen, "message") else AIMessage(content=str(gen))
                yield ChatGenerationChunk(message=msg)  # type: ignore[arg-type]
            return
        # Pass through chunks; deduplication happens at install_usage_dedup_patch level
        yield from stream_fn(adapted, stop=stop, run_manager=run_manager, **kwargs)

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        adapted = _adapt(
            messages, constraints=self.constraints, policy=self.family_policy
        )
        stream_fn = getattr(self.inner, "_astream", None)
        if stream_fn is None:
            result = await self._agenerate(
                messages, stop=stop, run_manager=run_manager, **kwargs
            )
            for gen in result.generations:
                msg = gen.message if hasattr(gen, "message") else AIMessage(content=str(gen))
                yield ChatGenerationChunk(message=msg)  # type: ignore[arg-type]
            return
        # Pass through chunks; deduplication happens at install_usage_dedup_patch level
        async for chunk in stream_fn(
            adapted, stop=stop, run_manager=run_manager, **kwargs
        ):
            yield chunk

    def bind_tools(
        self,
        tools: Sequence[Any],
        *,
        tool_choice: Optional[str] = None,
        **kwargs: Any,
    ) -> Runnable[Any, AIMessage]:
        bound = self.inner.bind_tools(tools, tool_choice=tool_choice, **kwargs)
        return ConstraintAwareBoundRunnable(
            bound,
            constraints=self.constraints,
            model_key=self.model_key,
            family_policy=self.family_policy,
        )

    def bind(self, **kwargs: Any) -> Runnable[Any, Any]:
        bound = self.inner.bind(**kwargs)
        return ConstraintAwareBoundRunnable(
            bound,
            constraints=self.constraints,
            model_key=self.model_key,
            family_policy=self.family_policy,
        )

    def __getattr__(self, name: str) -> Any:
        # Delegate unknown attrs (e.g. model_name) to inner for tooling/telemetry
        if name.startswith("_") or name in {
            "inner",
            "model_key",
            "constraints",
            "family_policy",
            "model_config",
        }:
            raise AttributeError(name)
        return getattr(self.inner, name)


def wrap_with_message_constraints(
    chat: BaseChatModel,
    *,
    model_key: str,
    bundle: RegistryBundle,
) -> BaseChatModel:
    """Wrap a resolved chat model with registry message + family constraints."""
    from shared_library.model_factory.message_constraints import (
        get_message_constraints,
    )

    constraints = get_message_constraints(bundle, model_key)
    policy = resolve_family_policy(bundle, model_key)
    if isinstance(chat, ConstraintAwareChatModel):
        return chat
    return ConstraintAwareChatModel(
        inner=chat,
        model_key=model_key,
        constraints=constraints,
        family_policy=policy,
    )

