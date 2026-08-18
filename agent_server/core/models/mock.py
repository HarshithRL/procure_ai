"""Mock ChatModel for local development when Databricks auth is unavailable."""

import logging
from typing import Any, Optional

from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.outputs.chat_generation import ChatGeneration
from langchain_core.outputs.llm_result import LLMResult

logger = logging.getLogger(__name__)


class MockChatModel(BaseChatModel):
    """
    A mock LLM that echoes user messages back for local development.
    
    Used when Databricks authentication is unavailable. Allows full stack testing
    locally without cloud credentials. Logs a warning on first use.
    
    Behavior:
    - Returns "Mock response: {user_message}" for any input
    - Logs warning on first instantiation
    - Implements LangChain BaseChatModel interface
    """

    _warned: bool = False

    def __init__(self, **kwargs: Any) -> None:
        """Initialize MockChatModel and emit warning once."""
        super().__init__(**kwargs)
        if not MockChatModel._warned:
            logger.warning(
                "[WARN] Using MockChatModel for local development. "
                "No Databricks credentials found. Real model will activate on deployment."
            )
            MockChatModel._warned = True

    @property
    def _llm_type(self) -> str:
        """Return LLM type identifier."""
        return "mock-chat"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """
        Generate a mock response by echoing the last user message.
        
        Args:
            messages: List of messages in conversation
            stop: Stop sequences (ignored)
            run_manager: Callback manager (ignored)
            **kwargs: Additional kwargs (ignored)
            
        Returns:
            LLMResult with a single mock message
        """
        # Extract the last user message
        last_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                last_message = msg.content
                break

        if last_message is None:
            last_message = "(empty)"

        # Generate mock response
        response_text = f"Mock response: {last_message}"

        # Wrap in AIMessage and LLMResult
        message = AIMessage(content=response_text)
        generation = ChatGeneration(message=message)

        return LLMResult(generations=[[generation]])

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """
        Async version of _generate (same behavior, no actual async work).
        
        Args:
            messages: List of messages in conversation
            stop: Stop sequences (ignored)
            run_manager: Callback manager (ignored)
            **kwargs: Additional kwargs (ignored)
            
        Returns:
            LLMResult with a single mock message
        """
        # For mock, no actual async work needed; just call sync version
        return self._generate(messages, stop, run_manager, **kwargs)
