"""Registry-driven message-shape adaptation for Model Factory chat models.

Constraints come from CapabilityRegistry.message_constraints — never from
hardcoded model-name checks. Adaptation runs only at the invoke boundary so
checkpoint / UI message history stays unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Sequence

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from shared_library.model_factory.registry_loader import RegistryBundle

_PIPELINE_STATUS_PREFIX = "[Pipeline status]\n"
_CONTINUE_PROMPT = "Please continue based on the context above."


@dataclass(frozen=True)
class MessageConstraints:
    """Provider-agnostic chat message shape rules for a resolved model."""

    requires_trailing_user_message: bool = False
    disallow_assistant_prefill: bool = False
    merge_system_messages: bool = True

    @classmethod
    def from_capability_doc(cls, doc: Optional[dict[str, Any]]) -> "MessageConstraints":
        """Load constraints from a CapabilityRegistry model entry."""
        if not isinstance(doc, dict):
            return cls()
        raw = doc.get("message_constraints")
        if not isinstance(raw, dict):
            return cls()
        return cls(
            requires_trailing_user_message=bool(
                raw.get("requires_trailing_user_message", False)
            ),
            disallow_assistant_prefill=bool(
                raw.get("disallow_assistant_prefill", False)
            ),
            merge_system_messages=bool(raw.get("merge_system_messages", True)),
        )

    @property
    def needs_adaptation(self) -> bool:
        return (
            self.requires_trailing_user_message
            or self.disallow_assistant_prefill
            or self.merge_system_messages
        )


def get_message_constraints(
    bundle: RegistryBundle,
    model_key: str,
) -> MessageConstraints:
    """Resolve message constraints for a logical or physical model key."""
    caps = bundle.capabilities.get(model_key)
    if isinstance(caps, dict):
        return MessageConstraints.from_capability_doc(caps)

    # Allow lookup by physical_model alias used as capability key elsewhere
    for alias, meta in bundle.models.items():
        if not isinstance(meta, dict):
            continue
        if meta.get("physical_model") == model_key:
            caps = bundle.capabilities.get(alias)
            if isinstance(caps, dict):
                return MessageConstraints.from_capability_doc(caps)
            break

    return MessageConstraints()


def _content_to_str(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                text = block.get("text")
                if isinstance(text, str):
                    parts.append(text)
                else:
                    parts.append(str(block))
            else:
                parts.append(str(block))
        return "".join(parts)
    return str(content)


def _merge_system_contents(systems: Sequence[SystemMessage]) -> Optional[SystemMessage]:
    if not systems:
        return None
    if len(systems) == 1:
        return systems[0]
    parts = [_content_to_str(m.content).strip() for m in systems]
    parts = [p for p in parts if p]
    return SystemMessage(content="\n\n".join(parts))


def _fold_status_into_human(
    human: HumanMessage,
    status_ais: Sequence[AIMessage],
) -> HumanMessage:
    status_parts = [
        _content_to_str(m.content).strip() for m in status_ais if _content_to_str(m.content).strip()
    ]
    if not status_parts:
        return human
    status_block = _PIPELINE_STATUS_PREFIX + "\n\n".join(status_parts)
    user_text = _content_to_str(human.content).strip()
    if user_text:
        merged = f"{user_text}\n\n{status_block}"
    else:
        merged = status_block
    return HumanMessage(content=merged)


def _strip_name(msg: BaseMessage) -> BaseMessage:
    if getattr(msg, "name", None) is None:
        return msg
    return msg.model_copy(update={"name": None})


def adapt_messages_for_invoke(
    messages: Sequence[BaseMessage],
    constraints: MessageConstraints,
) -> List[BaseMessage]:
    """Normalize message list for a model according to registry constraints.

    Steps:
    1. Strip `.name` field from all messages (subagent framework internal labels).
    2. Optionally lift + merge all SystemMessages into one leading block.
    3. Keep Human/AI/Tool conversation order.
    4. If disallow_assistant_prefill: fold trailing AIMessages after the last
       HumanMessage into that human turn (pipeline status injection).
    5. If requires_trailing_user_message and last non-system is not Human:
       append a short continue prompt.
    """
    stripped = [_strip_name(m) for m in messages]

    if not stripped:
        if constraints.requires_trailing_user_message:
            return [HumanMessage(content=_CONTINUE_PROMPT)]
        return []

    if not constraints.needs_adaptation:
        return stripped

    systems: list[SystemMessage] = []
    conversation: list[BaseMessage] = []
    for msg in stripped:
        if isinstance(msg, SystemMessage):
            systems.append(msg)
        else:
            conversation.append(msg)

    if constraints.merge_system_messages:
        leading_system = _merge_system_contents(systems)
        systems_out: list[BaseMessage] = [leading_system] if leading_system else []
    else:
        systems_out = list(systems)

    # Fold trailing assistant prefill into the last human turn
    if constraints.disallow_assistant_prefill and conversation:
        last_human_idx: Optional[int] = None
        for i, msg in enumerate(conversation):
            if isinstance(msg, HumanMessage):
                last_human_idx = i

        if last_human_idx is not None:
            trailing = conversation[last_human_idx + 1 :]
            # Only fold pure trailing AIMessages (status injects). Keep tool
            # turns intact — if ToolMessage appears, do not rewrite.
            if trailing and all(isinstance(m, AIMessage) for m in trailing):
                folded = _fold_status_into_human(
                    conversation[last_human_idx],  # type: ignore[arg-type]
                    trailing,  # type: ignore[arg-type]
                )
                conversation = conversation[:last_human_idx] + [folded]
            elif trailing and not any(isinstance(m, (HumanMessage, ToolMessage)) for m in trailing):
                # Mixed trailing that is only AI + unknown → fold AIs, drop empties
                ais = [m for m in trailing if isinstance(m, AIMessage)]
                others = [m for m in trailing if not isinstance(m, AIMessage)]
                if ais and not others:
                    folded = _fold_status_into_human(
                        conversation[last_human_idx],  # type: ignore[arg-type]
                        ais,
                    )
                    conversation = conversation[:last_human_idx] + [folded]

    result: list[BaseMessage] = systems_out + conversation

    if constraints.requires_trailing_user_message:
        # Find last non-system message
        last_non_system: Optional[BaseMessage] = None
        for msg in reversed(result):
            if not isinstance(msg, SystemMessage):
                last_non_system = msg
                break
        if last_non_system is None:
            result.append(HumanMessage(content=_CONTINUE_PROMPT))
        elif isinstance(last_non_system, HumanMessage):
            pass
        elif isinstance(last_non_system, ToolMessage):
            # Valid mid tool-call loop — do not inject a synthetic user turn
            pass
        elif isinstance(last_non_system, AIMessage) and getattr(
            last_non_system, "tool_calls", None
        ):
            # Model requested tools; next turn supplies ToolMessage(s)
            pass
        else:
            result.append(HumanMessage(content=_CONTINUE_PROMPT))

    return result

