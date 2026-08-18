"""Request models for agent endpoints."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class AgentInvokeRequest(BaseModel):
    """Synchronous agent invocation request."""

    thread_id: str = Field(..., description="Session thread ID")
    user_id: Optional[str] = Field(None, description="User ID from X-Forwarded-Email")
    messages: list[dict] = Field(..., description="Conversation messages")
    model: Optional[str] = Field(None, description="Optional model override")
    profile: str = Field("balanced", description="Model profile (fast_chat, balanced, deep_reasoning)")


class StreamRequest(BaseModel):
    """Streaming agent invocation request (SSE)."""

    thread_id: str = Field(..., description="Session thread ID")
    user_id: Optional[str] = Field(None, description="User ID from X-Forwarded-Email")
    message: str = Field(..., description="User message text")
    model: Optional[str] = Field(None, description="Optional model override")
    profile: str = Field("balanced", description="Model profile")
