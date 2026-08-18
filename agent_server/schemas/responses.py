"""Response models for agent endpoints."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class StreamEvent(BaseModel):
    """Single event in an SSE stream."""

    event: str = Field(..., description="Event type: on_chain_start, on_llm_stream, on_chain_end, etc.")
    data: Optional[dict[str, Any]] = Field(None, description="Event payload")
    trace_id: Optional[str] = Field(None, description="MLflow trace ID")


class InvokeResponse(BaseModel):
    """Synchronous invoke response."""

    thread_id: str
    messages: list[dict]
    trace_id: Optional[str] = None
    status: str = "success"


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="ok or starting")
    graph_ready: bool = Field(..., description="True if agent graph is compiled")
    mlflow_ready: bool = Field(False, description="True if MLflow is configured")
