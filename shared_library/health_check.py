"""Agent server health check and connectivity poll.

Monitors the agent_server (FastAPI on port 8001) and logs connectivity status.

Usage:
    from shared_library.health_check import AgentServerPoller, poll_agent_server
    
    # One-shot check
    status = poll_agent_server()
    
    # Background polling with callback
    poller = AgentServerPoller(interval_seconds=30)
    poller.start()
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, asdict
from threading import Thread, Event
from typing import Callable, Optional

import httpx

from shared_library.global_logger_hub import bootstrap, get_app_logger

bootstrap()
logger = get_app_logger("health_check.agent_poller")

AGENT_SERVER_URL = "http://127.0.0.1:8001"
DEFAULT_POLL_INTERVAL = 30  # seconds


@dataclass
class AgentServerStatus:
    """Snapshot of agent server health."""

    timestamp: float  # time.time()
    is_online: bool  # can reach /health endpoint
    graph_ready: bool  # LLM graph compiled and ready
    status: str  # "ok" | "starting" | "error"
    error: Optional[str] = None  # error message if not online
    response_time_ms: float = 0.0  # HTTP round-trip
    details: Optional[dict] = None  # raw /health response


class AgentServerPoller:
    """Background poller that checks agent_server health on an interval.

    Usage:
        poller = AgentServerPoller(interval_seconds=30)
        poller.on_status(lambda s: print(f"Agent: {s.status}"))
        poller.start()
        # ... do work ...
        poller.stop()
    """

    def __init__(self, interval_seconds: int = DEFAULT_POLL_INTERVAL):
        self.interval = interval_seconds
        self._thread: Optional[Thread] = None
        self._stop_event = Event()
        self._last_status: Optional[AgentServerStatus] = None
        self._callbacks: list[Callable[[AgentServerStatus], None]] = []

    def on_status(self, callback: Callable[[AgentServerStatus], None]) -> None:
        """Register callback invoked after each poll."""
        self._callbacks.append(callback)

    def start(self) -> None:
        """Start background polling thread."""
        if self._thread is not None:
            logger.warning("poller | already_running")
            return

        self._stop_event.clear()
        self._thread = Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        logger.info(f"poller | started | interval={self.interval}s")

    def stop(self) -> None:
        """Stop background polling thread."""
        if self._thread is None:
            return

        self._stop_event.set()
        self._thread.join(timeout=5.0)
        self._thread = None
        logger.info("poller | stopped")

    def get_last_status(self) -> Optional[AgentServerStatus]:
        """Return the most recent poll result (or None if not polled yet)."""
        return self._last_status

    def _poll_loop(self) -> None:
        """Background loop: poll every interval, invoke callbacks."""
        while not self._stop_event.is_set():
            try:
                status = poll_agent_server()
                self._last_status = status

                # Log the result
                _log_status(status)

                # Invoke callbacks
                for cb in self._callbacks:
                    try:
                        cb(status)
                    except Exception as e:
                        logger.exception(f"poller | callback_error={type(e).__name__}")

            except Exception as e:
                logger.exception(f"poller | poll_error={type(e).__name__}")

            # Wait for interval, but allow early exit
            self._stop_event.wait(timeout=self.interval)


def poll_agent_server(timeout: float = 5.0) -> AgentServerStatus:
    """One-shot health check of agent_server.

    Args:
        timeout: HTTP timeout in seconds.

    Returns:
        AgentServerStatus snapshot.
    """
    start_time = time.time()
    url = f"{AGENT_SERVER_URL}/health"

    try:
        response = httpx.get(url, timeout=timeout)
        response_time = (time.time() - start_time) * 1000  # ms

        if response.status_code != 200:
            return AgentServerStatus(
                timestamp=start_time,
                is_online=False,
                graph_ready=False,
                status="error",
                error=f"HTTP {response.status_code}",
                response_time_ms=response_time,
                details=None,
            )

        data = response.json()
        return AgentServerStatus(
            timestamp=start_time,
            is_online=True,
            graph_ready=data.get("graph_ready", False),
            status=data.get("status", "unknown"),
            error=None,
            response_time_ms=response_time,
            details=data,
        )

    except httpx.ConnectError:
        response_time = (time.time() - start_time) * 1000
        return AgentServerStatus(
            timestamp=start_time,
            is_online=False,
            graph_ready=False,
            status="error",
            error="connection_refused",
            response_time_ms=response_time,
        )

    except httpx.TimeoutException:
        response_time = (time.time() - start_time) * 1000
        return AgentServerStatus(
            timestamp=start_time,
            is_online=False,
            graph_ready=False,
            status="error",
            error="timeout",
            response_time_ms=response_time,
        )

    except Exception as e:
        response_time = (time.time() - start_time) * 1000
        return AgentServerStatus(
            timestamp=start_time,
            is_online=False,
            graph_ready=False,
            status="error",
            error=f"{type(e).__name__}: {str(e)[:100]}",
            response_time_ms=response_time,
        )


def _log_status(status: AgentServerStatus) -> None:
    """Log a poll result with structured fields."""
    if status.is_online:
        logger.info(
            "poll | status={} | graph_ready={} | response_time={}ms",
            status.status,
            status.graph_ready,
            int(status.response_time_ms),
        )
    else:
        logger.warning(
            "poll | offline | error={} | response_time={}ms",
            status.error,
            int(status.response_time_ms),
        )


async def async_poll_agent_server(timeout: float = 5.0) -> AgentServerStatus:
    """Async version of poll_agent_server (for FastAPI endpoints)."""
    # For now, run sync version in executor
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, poll_agent_server, timeout)


__all__ = [
    "AgentServerStatus",
    "AgentServerPoller",
    "poll_agent_server",
    "async_poll_agent_server",
]
