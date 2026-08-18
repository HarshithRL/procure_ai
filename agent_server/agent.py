"""Procure AI LangGraph orchestrator — Brain agent + routing.

Direct port of PDF Parser's agent.py with procurement domain.
Sprint 1: Single brain node (future: intake, clarification, document nodes).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, StateGraph

from shared_library.global_logger_hub import bootstrap, get_agent_logger, graph_turn
from agent_server.core.sub_agents.brain import (
    DEFAULT_PROFILE,
    get_brain,
    normalize_profile,
)
from agent_server.schemas import AgentState

bootstrap()
logger = get_agent_logger(__name__)

GRAPH_ID = "procure_orchestrator"
BRAIN_AGENT_ID = "brain"


async def brain_node(state: AgentState, config: Any = None) -> dict[str, Any]:
    """Brain agent node — primary conversational intelligence.

    Selects the LLM per request from `state["profile"]` (set by the chat UI's
    model picker), then delegates to the matching compiled brain subgraph.

    This node MUST stay registered as the graph's brain node. Registering the
    compiled brain directly (``graph.add_node(BRAIN_AGENT_ID, get_brain())``)
    binds one hardcoded model for the process lifetime and silently ignores the
    user's model selection.

    Astream_events propagation: we call `astream_events()` on the inner agent 
    with version="v2", so token-level `on_chat_model_stream` events bubble up 
    to the SSE endpoint and are relayed to the UI in real time.
    """
    profile = normalize_profile(state.get("profile"))
    model_id = state.get("model")  # Optional model override from user
    thread_id = state.get("thread_id", "unknown")
    
    with graph_turn(thread_id=thread_id, node="brain_node"):
        logger.info(f"brain | profile={profile} | model_id={model_id or '(default)'}")
        try:
            brain = get_brain(profile=profile, model_id=model_id)

            inner_config = {
                "configurable": {
                    "thread_id": thread_id,
                    "user_id": state.get("user_id"),
                }
            }

            # Use astream_events v2 to capture token-level on_chat_model_stream.
            # Collect the final messages from the stream.
            final_messages = state.get("messages", [])
            async for event in brain.astream_events(
                {"messages": state.get("messages", [])},
                config=inner_config,
                version="v2",
            ):
                # Relay events upstream through the outer graph's SSE handler.
                # The outer graph (start_server.py) will serialize and yield them.
                # We just forward the final messages after the stream completes.
                if event.get("event") == "on_chat_model_end":
                    # Extract the assistant message from the end event
                    msg = event.get("data", {}).get("output", {}).get("content")
                    if msg:
                        from langchain_core.messages import AIMessage
                        final_messages = list(state.get("messages", [])) + [AIMessage(content=msg)]
            
            message_count = len(final_messages)
            logger.info(f"brain | complete | message_count={message_count}")
            return {"messages": final_messages}
        except Exception as exc:
            logger.exception(f"brain | failed | {exc}")
            from langchain_core.messages import AIMessage

            return {
                "messages": [
                    AIMessage(
                        content=f"Brain agent error: {type(exc).__name__}: {exc}"
                    )
                ]
            }


def route_after_start(state: AgentState) -> Literal["brain", END]:
    """Route logic after START.

    Sprint 1: Always route to brain.
    Sprint 2+: Could route to intake, clarification, etc. based on intent.
    """
    return BRAIN_AGENT_ID


async def build_agent_graph(
    db_path: str | None = None,
    *,
    executive_graph: Any = None,
) -> Any:
    """Build and compile the agent graph with AsyncSqliteSaver.

    Args:
        db_path: Path to SQLite checkpoint database. Defaults to agent_server/checkpoints.db.

    Returns:
        Compiled StateGraph.
    """
    if db_path is None:
        db_path = str(Path(__file__).resolve().parent / "checkpoints.db")

    # Set up AsyncSqliteSaver
    conn = await aiosqlite.connect(db_path)
    checkpointer = AsyncSqliteSaver(conn)
    await checkpointer.setup()

    # Register brain_node (a per-request dispatcher), NOT a pre-built brain.
    # Tests may still inject a compiled graph via executive_graph.
    inner = executive_graph if executive_graph is not None else brain_node

    if executive_graph is None:
        # Warm the default profile so /health's graph_ready still proves that
        # Databricks auth + model resolution actually work. Failures propagate,
        # matching the previous build-time behaviour.
        get_brain(profile=DEFAULT_PROFILE)

    # Build the graph
    graph = StateGraph(AgentState)
    graph.add_node(BRAIN_AGENT_ID, inner)
    graph.add_conditional_edges(
        START,
        route_after_start,
        {BRAIN_AGENT_ID: BRAIN_AGENT_ID, "end": END},
    )
    graph.add_edge(BRAIN_AGENT_ID, END)

    compiled = graph.compile(checkpointer=checkpointer, name=GRAPH_ID)
    # Store connection for cleanup on shutdown
    compiled._async_sqlite_conn = conn  # noqa: SLF001

    logger.info(f"Graph built | id={GRAPH_ID} | db={db_path}")
    return compiled


# Singleton instance
_graph_instance: Any = None


async def get_agent_graph() -> Any:
    """Get or create singleton agent graph."""
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = await build_agent_graph()
    return _graph_instance


async def get_graph() -> Any:
    """Alias for get_agent_graph()."""
    return await get_agent_graph()


async def close_graph() -> None:
    """Close the graph's database connection."""
    global _graph_instance
    if _graph_instance is not None:
        try:
            conn = getattr(_graph_instance, "_async_sqlite_conn", None)
            if conn is not None:
                await conn.close()
                logger.info("Graph database connection closed")
        except Exception as e:
            logger.warning(f"Error closing graph connection: {e}")
        finally:
            _graph_instance = None
