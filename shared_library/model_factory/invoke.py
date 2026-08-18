"""Standalone one-shot model invocation via the Model Factory resolver."""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional, Sequence, Union

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)

from shared_library.databricks_connectors import AuthProvider, ConnectorHub

from shared_library.model_factory.exceptions import ModelFactoryError
from shared_library.model_factory.resolver import resolve_chat_model

PromptInput = Union[str, BaseMessage, Sequence[Union[str, BaseMessage, dict]]]


def _coerce_messages(prompt: PromptInput) -> List[BaseMessage]:
    """Normalize str / message / OpenAI-style dicts into LangChain messages."""
    if isinstance(prompt, str):
        return [HumanMessage(content=prompt)]

    if isinstance(prompt, BaseMessage):
        return [prompt]

    if not isinstance(prompt, Sequence) or isinstance(prompt, (bytes, bytearray)):
        raise ModelFactoryError(
            f"Unsupported prompt type: {type(prompt).__name__}; "
            "expected str, BaseMessage, or a sequence of messages/dicts"
        )

    messages: List[BaseMessage] = []
    for item in prompt:
        if isinstance(item, str):
            messages.append(HumanMessage(content=item))
        elif isinstance(item, BaseMessage):
            messages.append(item)
        elif isinstance(item, dict):
            role = str(item.get("role", "user")).lower()
            content = item.get("content", "")
            if role in ("system", "developer"):
                messages.append(SystemMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
            else:
                messages.append(HumanMessage(content=content))
        else:
            raise ModelFactoryError(
                f"Unsupported message item type: {type(item).__name__}"
            )

    if not messages:
        raise ModelFactoryError("Prompt resolved to an empty message list")
    return messages


def _message_text(response: Any) -> str:
    if isinstance(response, str):
        return response
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
                continue
            if not isinstance(block, dict):
                continue
            block_type = str(block.get("type") or "")
            if block_type in {"reasoning", "thinking"}:
                continue
            if "text" in block and block["text"] is not None:
                parts.append(str(block["text"]))
            elif block_type in {"text", "output_text"} and block.get("content"):
                parts.append(str(block["content"]))
        return "".join(parts).strip() or str(content)
    return str(content)


import logging
import time

logger = logging.getLogger("model_factory.invoke")


def invoke_model(
    prompt: PromptInput,
    *,
    profile: str = "fast_chat",
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    max_retries: Optional[int] = None,
    timeout: Optional[Union[int, float]] = None,
    config_prefix: Optional[str] = None,
    registries_dir: Optional[Path | str] = None,
    hub: Optional[ConnectorHub] = None,
    provider: Optional[AuthProvider] = None,
) -> str:
    """Resolve via ``init_chat_model``, invoke once, return assistant text.

    Auth uses ``databricks_connectors`` WorkspaceClient credentials (CLI hub).
    Traffic goes to Unity AI Gateway OpenAI-compatible chat completions.
    """
    t0 = time.time()
    llm = resolve_chat_model(
        profile=profile,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        max_retries=max_retries,
        timeout=timeout,
        config_prefix=config_prefix,
        registries_dir=registries_dir,
        hub=hub,
        provider=provider,
    )
    messages = _coerce_messages(prompt)
    logger.info(
        "[MODEL-INVOKE] resolving model profile=%s model=%s msgs=%d",
        profile,
        model or "profile_default",
        len(messages),
    )

    try:
        result = llm.invoke(messages)
        elapsed_ms = int((time.time() - t0) * 1000)
        output_text = _message_text(result)
        logger.info(
            "[MODEL-INVOKE] complete profile=%s output_chars=%d duration_ms=%d",
            profile,
            len(output_text),
            elapsed_ms,
        )
        return output_text
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = int((time.time() - t0) * 1000)
        logger.error(
            "[MODEL-INVOKE] failed profile=%s error=%s duration_ms=%d",
            profile,
            exc,
            elapsed_ms,
        )
        raise ModelFactoryError(f"Model invocation failed: {exc}") from exc


