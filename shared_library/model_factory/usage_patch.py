"""One-chunk lookahead deduplication of input_tokens in streamed responses.

The Databricks AI Gateway echoes full usage_metadata on every SSE chunk.
LangChain's AIMessageChunk.__add__ sums input_tokens across all chunks,
yielding inflated values (~52x the real prompt tokens). This module installs
a one-chunk lookahead filter on ChatOpenAI._stream and _astream that zeros
input_tokens and total_tokens on all but the final chunk, preserving the
correct sum while keeping output_tokens incremental deltas.

The filter is idempotent and survives init_chat_model, _ConfigurableModel,
and bind_tools because it patches ChatOpenAI at the module level.
"""

from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, Iterator, Optional

from agent_server.core.logging import get_logger

logger = get_logger("model_factory.usage_patch")

_PATCH_INSTALLED = False


def _zero_input_usage(chunk: Any) -> Any:
    """Return a copy of chunk with input_tokens and total_tokens zeroed.

    Args:
        chunk: A ChatGenerationChunk with a message attribute.

    Returns:
        A new ChatGenerationChunk with usage metadata filtered.
    """
    try:
        from langchain_core.outputs import ChatGenerationChunk

        msg = chunk.message
        if not hasattr(msg, "usage_metadata") or msg.usage_metadata is None:
            return chunk

        usage = dict(msg.usage_metadata)
        # Zero out prompt tokens; leave output_tokens so deltas stay correct
        usage.pop("input_tokens", None)
        usage.pop("total_tokens", None)

        # Use the message's copy method (if available) or dict() → new instance
        if hasattr(msg, "copy"):
            msg_copy = msg.copy(update={"usage_metadata": usage if usage else None})
        else:
            # Fallback: rebuild using model_construct to bypass pydantic validation
            msg_copy = type(msg).model_construct(
                **{**msg.dict(), "usage_metadata": usage if usage else None}
            )
        return ChatGenerationChunk(message=msg_copy)
    except Exception as e:
        logger.debug("Failed to zero usage on chunk (passthrough): {}", e)
        return chunk


def _stream_with_lookahead(
    original_stream_fn,
) -> Iterator[Any]:
    """Wrap _stream with one-chunk lookahead to filter usage on non-final chunks."""
    chunks_iter = original_stream_fn()
    previous_chunk = None

    for current_chunk in chunks_iter:
        if previous_chunk is not None:
            # Emit the previous chunk (now known not to be final) with zeroed usage
            yield _zero_input_usage(previous_chunk)
        previous_chunk = current_chunk

    # Emit the final chunk unmodified
    if previous_chunk is not None:
        yield previous_chunk


async def _astream_with_lookahead(
    original_astream_fn,
) -> AsyncIterator[Any]:
    """Wrap _astream with one-chunk lookahead to filter usage on non-final chunks."""
    chunks_iter = original_astream_fn()
    previous_chunk = None

    async for current_chunk in chunks_iter:
        if previous_chunk is not None:
            # Emit the previous chunk (now known not to be final) with zeroed usage
            yield _zero_input_usage(previous_chunk)
        previous_chunk = current_chunk

    # Emit the final chunk unmodified
    if previous_chunk is not None:
        yield previous_chunk


def install_usage_dedup_patch() -> None:
    """Install one-chunk lookahead filter on ChatOpenAI.

    Idempotent: subsequent calls are no-ops.
    Wrapped in try/except so a missing langchain_openai cannot break startup.
    """
    global _PATCH_INSTALLED

    if _PATCH_INSTALLED:
        return

    try:
        from langchain_openai import ChatOpenAI

        original_stream = ChatOpenAI._stream
        original_astream = ChatOpenAI._astream

        def patched_stream(self, *args, **kwargs):
            """Patched _stream with one-chunk lookahead."""
            def stream_gen():
                yield from original_stream(self, *args, **kwargs)

            yield from _stream_with_lookahead(stream_gen)

        async def patched_astream(self, *args, **kwargs):
            """Patched _astream with one-chunk lookahead."""
            async def astream_gen():
                async for chunk in original_astream(self, *args, **kwargs):
                    yield chunk

            async for chunk in _astream_with_lookahead(astream_gen):
                yield chunk

        ChatOpenAI._stream = patched_stream
        ChatOpenAI._astream = patched_astream

        _PATCH_INSTALLED = True
        logger.info("Installed usage deduplication patch on ChatOpenAI")

    except ImportError:
        logger.debug("langchain_openai not available; usage dedup patch skipped")
    except Exception as e:
        logger.warning("Failed to install usage dedup patch: {}", e)
