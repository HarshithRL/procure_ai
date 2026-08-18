"""State definitions for the Procure AI agent graph."""

from __future__ import annotations

from typing import Annotated, Optional

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import NotRequired, TypedDict


class AgentState(TypedDict):
    """Main graph state — shared by all nodes.

    Fields:
        messages: Conversation history (id-merged via add_messages reducer).
        thread_id: Unique session identifier (e.g., "{user_email}:{session_uuid}").
        user_id: User's Databricks email (from X-Forwarded headers).
        session_id: Unique session UUID.
    """

    messages: Annotated[list[BaseMessage], add_messages]
    thread_id: str
    user_id: NotRequired[Optional[str]]
    session_id: NotRequired[Optional[str]]
    pending_approval: NotRequired[Optional[dict]]  # HITL payload (Sprint 3)
