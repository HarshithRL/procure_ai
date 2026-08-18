"""Development entry point for Procure AI Flask application.

This file provides a convenient way to run Flask locally:
    python app.py                           (uses werkzeug dev server)
    flask --app app run --debug --port 5000 (uses flask CLI)

For production, use wsgi.py instead:
    gunicorn "wsgi:app" -w 4 -b 0.0.0.0:8000

For dual-server development (Flask + FastAPI agent server):
    uv run python ops/deployment/run_app.py

This file delegates all logging, tracing, and shutdown handling to wsgi.py.
If you run this directly, the agent server (FastAPI on 8001) is not started.
Agent status will show "offline" until you start it separately.
"""

import os

# Use wsgi.py's app directly (avoids code duplication)
from wsgi import app

if __name__ == "__main__":
    flask_env = os.getenv("FLASK_ENV", "development")
    port = int(os.getenv("DATABRICKS_APP_PORT", 5000))
    
    print(f"Starting Flask app on 0.0.0.0:{port}")
    print("Note: Agent server not started. Run 'uv run python ops/deployment/run_app.py' for full setup.")
    
    app.run(debug=(flask_env == "development"), host="0.0.0.0", port=port)
