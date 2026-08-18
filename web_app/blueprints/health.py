"""Health check and status endpoints."""

from __future__ import annotations

from flask import Blueprint, jsonify

from shared_library.global_logger_hub import bootstrap, get_app_logger
from shared_library.health_check import poll_agent_server

bootstrap()
logger = get_app_logger(__name__)

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Full system health check: Flask + agent server status.
    
    Returns JSON with:
        - service: Flask app name
        - flask_status: "ok"
        - agent_server: connectivity snapshot from poll
    """
    logger.debug("health_check | called")
    
    # One-shot poll (non-blocking, timeout 5s)
    agent_status = poll_agent_server(timeout=5.0)
    
    response = {
        "status": "ok",
        "service": "Procure AI Flask BFF",
        "flask": {"status": "ok"},
        "agent_server": {
            "online": agent_status.is_online,
            "graph_ready": agent_status.graph_ready,
            "status": agent_status.status,
            "response_time_ms": int(agent_status.response_time_ms),
        },
    }
    
    # Log result
    if agent_status.is_online:
        logger.info(
            "health_check | agent_ok | graph_ready={} | response_time={}ms",
            agent_status.graph_ready,
            int(agent_status.response_time_ms),
        )
    else:
        logger.warning(
            "health_check | agent_offline | error={} | response_time={}ms",
            agent_status.error,
            int(agent_status.response_time_ms),
        )
    
    return jsonify(response), 200


@health_bp.route("/ready", methods=["GET"])
def readiness():
    """Readiness probe: Flask is ready (but agent may still be starting).
    
    Returns 200 immediately. Agent status is informational.
    """
    agent_status = poll_agent_server(timeout=2.0)
    
    response = {
        "ready": True,
        "agent_ready": agent_status.is_online and agent_status.graph_ready,
    }
    
    return jsonify(response), 200


@health_bp.route("/live", methods=["GET"])
def liveness():
    """Liveness probe: Flask is alive and responding.
    
    Returns 200 immediately. Used by orchestrators (Kubernetes, Databricks Apps).
    """
    return jsonify({"alive": True}), 200


__all__ = ["health_bp"]
