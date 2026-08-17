"""
Procure AI Flask application entrypoint.

This module exports the Flask app for gunicorn to run:
    gunicorn app:app -w 4 -b 0.0.0.0:$DATABRICKS_APP_PORT

Environment variables:
    FLASK_ENV: "development" or "production" (default: production)
    DATABRICKS_APP_PORT: Port to bind to (default: 8000 on Databricks Apps, 5000 local)
    DATABASE_URL: SQLAlchemy connection string (default: sqlite:////tmp/procure_ai.db)
    SECRET_KEY: Flask secret key for session signing (from Databricks Secret in prod)
    DATABRICKS_HOST: Workspace hostname for WorkspaceClient (e.g., https://adb-xxx.azuredatabricks.net)

Security:
    - Binds to DATABRICKS_APP_PORT (injected by Databricks Apps runtime)
    - Graceful SIGTERM handler (15-second shutdown window per platform constraints)
    - Session cookies configured with HttpOnly, SameSite=Lax, Secure (HTTPS in prod)
"""

import os
import signal
import sys
import logging

from web_app import create_app

# Configure logging early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app with environment-based config
flask_env = os.getenv("FLASK_ENV", "production")
app = create_app(config_name=flask_env)

# Graceful shutdown handler (15-second timeout per Databricks Apps constraints)
def handle_sigterm(signum, frame):
    """
    Handle SIGTERM signal for graceful shutdown.
    
    Databricks Apps runtime sends SIGTERM before SIGKILL with a strict 15-second window.
    This handler ensures:
    - Active database transactions complete or rollback
    - Scoped sessions are properly removed
    - Resources are cleaned up
    """
    logger.info("SIGTERM received. Initiating graceful shutdown...")
    try:
        # Close any pending database sessions
        from web_app.database import db_session
        if db_session:
            db_session.remove()
            logger.info("Database sessions closed")
    except Exception as e:
        logger.error(f"Error closing database sessions: {e}")
    
    logger.info("Shutdown complete. Exiting.")
    sys.exit(0)


# Register SIGTERM handler
signal.signal(signal.SIGTERM, handle_sigterm)

if __name__ == "__main__":
    # This runs only with `python app.py` (not gunicorn)
    # For local development, use: flask --app app run --debug --port 5000
    
    # Determine port: DATABRICKS_APP_PORT (Databricks Apps) or fallback to 5000 (local dev)
    port = int(os.getenv("DATABRICKS_APP_PORT", 5000))
    
    logger.info(f"Starting Flask app on 0.0.0.0:{port} (ENV={flask_env})")
    app.run(debug=(flask_env == "development"), host="0.0.0.0", port=port)
