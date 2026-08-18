"""Agent system logger wrapper - Loguru-based with LangChain integration.

Provides:
- get_logger(name) - Returns Loguru logger bound to agent_server namespace
- agent_span(thread_id, user_id, node) - Context manager for request-scoped logging
- catch(stage, reraise) - Decorator + context manager for exception handling

Usage:
    from agent_server.core.logging import get_logger, agent_span, catch
    
    logger = get_logger("agent_server.agent")
    
    async def agent_node(state):
        with agent_span(thread_id=state["thread_id"], user_id="user123"):
            with catch(stage="agent_node", reraise=False):
                response = await agent.ainvoke(messages)
                logger.info("Agent responded", response_length=len(response.content))
"""

from .wrapper import get_logger, agent_span, catch
from ..flow_tracer import ui_turn, api_request, api_turn, graph_turn, llm_turn

__all__ = ["get_logger", "agent_span", "catch", "ui_turn", "api_request", "api_turn", "graph_turn", "llm_turn"]
