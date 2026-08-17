"""
Procure AI Flask application entrypoint.

This module exports the Flask app for gunicorn to run:
    gunicorn app:app

Environment variables:
    FLASK_ENV: "development" or "production" (default: production)
    DATABASE_URL: SQLAlchemy connection string (default: sqlite:////tmp/procure_ai.db)
    SECRET_KEY: Flask secret key for session signing (auto-generated if unset)
"""

import os
from web_app import create_app

# Create Flask app with environment-based config
flask_env = os.getenv("FLASK_ENV", "production")
app = create_app(config_name=flask_env)

if __name__ == "__main__":
    # This runs only with `python app.py` (not gunicorn)
    # For local development, use: flask --app app run --debug --port 5000
    app.run(debug=(flask_env == "development"), port=5000)
