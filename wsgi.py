"""WSGI entry point for Gunicorn — Procure AI Flask application.

This is the canonical entry point for production deployment:
    gunicorn "wsgi:app" -w 4 -b 0.0.0.0:8000

Or locally with flask CLI:
    flask --app wsgi run --debug --port 5000

Handles:
- Logging configuration (shared with agent_server)
- MLflow tracing bootstrap
- Flask app factory initialization
- Graceful SIGTERM shutdown (Databricks Apps constraint: 15-second window)

Environment variables:
    FLASK_ENV: "development" or "production" (default: production)
    DATABRICKS_APP_PORT: Port to bind to (default: 8000 on Databricks Apps, 5000 local)
    DATABASE_URL: SQLAlchemy connection string (default: sqlite:////tmp/procure_ai.db)
    SECRET_KEY: Flask secret key for session signing (from Databricks Secret in prod)
    DATABRICKS_HOST: Workspace hostname for WorkspaceClient (e.g., https://adb-xxx.azuredatabricks.net)
    MLFLOW_TRACKING_URI: MLflow tracking server URI (optional)
    MLFLOW_EXPERIMENT: MLflow experiment name (optional)

IMPORTANT: This is paired with agent_server/start_server.py (FastAPI on port 8001).
For local development, use ops/deployment/run_app.py to launch both:
    uv run python ops/deployment/run_app.py
"""

import logging
import os
import signal
import sys

# Configure logging FIRST, before any imports that use logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bootstrap MLflow tracing (if available)
try:
    import mlflow
    from shared_library.global_logger_hub import configure_root_logging

    configure_root_logging()

    # Default MLflow URI: if DATABRICKS_HOST is set, use databricks://.
    # Otherwise, use explicit MLFLOW_TRACKING_URI or skip tracing.
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI")
    if not mlflow_uri and os.getenv("DATABRICKS_HOST"):
        mlflow_uri = "databricks"
    
    mlflow_exp = os.getenv("MLFLOW_EXPERIMENT", "procure_ai")
    
    if mlflow_uri:
        mlflow.set_tracking_uri(mlflow_uri)
        mlflow.set_experiment(mlflow_exp)
        mlflow.langchain.autolog()
        logger.info(f"MLflow tracing bootstrapped | uri={mlflow_uri} | exp={mlflow_exp}")
    else:
        logger.info("MLflow tracing disabled (no MLFLOW_TRACKING_URI or DATABRICKS_HOST)")
except ImportError:
    logger.warning("MLflow not available; tracing disabled")
except Exception as e:
    logger.warning(f"MLflow bootstrap error: {e}; continuing without tracing")

# Create Flask app using the factory pattern
from web_app.config import config as config_dict
from web_app import create_app

flask_env = os.getenv("FLASK_ENV", "production").lower()

# Normalize env name; default to production if invalid
if flask_env not in config_dict:
    logger.warning(f"Invalid FLASK_ENV={flask_env}; defaulting to production")
    flask_env = "production"

app = create_app(config_name=flask_env)

logger.info(f"Flask app created | env={flask_env} | debug={app.debug}")

# NOTE: SIGTERM handling is managed by ops/deployment/run_app.py (launcher process).
# Do NOT register signal handlers at module level in gunicorn workers —
# it overwrites gunicorn's built-in graceful-drain mechanism.
# Each worker should allow gunicorn to orchestrate shutdown per its lifecycle.

if __name__ == "__main__":
    # This runs when invoked as `python wsgi.py` (not gunicorn)
    # For production, use: gunicorn "wsgi:app" -w 4 -b 0.0.0.0:8000
    # For local dev, use: flask --app wsgi run --debug --port 5000
    
    port = int(os.getenv("DATABRICKS_APP_PORT", 5000))
    debug = flask_env == "development"
    
    logger.info(f"Starting Flask app on 0.0.0.0:{port} (debug={debug})")
    logger.info("Note: Agent server not started. Run ops/deployment/run_app.py for dual-server mode.")
    
    app.run(debug=debug, host="0.0.0.0", port=port)
