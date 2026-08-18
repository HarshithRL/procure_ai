"""
Flask application configuration.

Environment-based config with hardened security defaults for Databricks Apps deployment.
See: https://flask.palletsprojects.com/en/3.0.x/config/
"""

import os


class DevelopmentConfig:
    DEBUG = True
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    # Local development uses a file-backed SQLite DB in the project root.
    #
    # Do NOT use "sqlite:///:memory:" here. SQLAlchemy backs in-memory SQLite
    # with SingletonThreadPool, so every worker thread gets its own EMPTY
    # database. create_all_tables() runs on the main thread, but the Flask dev
    # server is threaded, so request threads fail with "no such table: users"
    # as soon as get_current_user() runs.
    #
    # Override with the DATABASE_URL env var if needed.
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///procure_ai.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session cookie security (per auth.md: HttpOnly, SameSite=Lax)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False  # Local dev uses HTTP


class ProductionConfig:
    DEBUG = False
    # Secret key must be set via Databricks App secret binding in app.yaml.
    # If not set, Flask will use None and session signing will fail at runtime.
    # This is intentional: fail at first request, not at boot, to support config validation.
    SECRET_KEY = os.environ.get("SECRET_KEY")
    
    # Production (Databricks Apps) uses SQLite in /tmp (ephemeral)
    # Set DATABASE_URL env var in app.yaml for alternate storage (e.g., Lakebase PostgreSQL in Sprint 2)
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:////tmp/procure_ai.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session cookie security (per auth.md: HttpOnly, SameSite=Lax, Secure over HTTPS)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = True  # Databricks Apps enforces HTTPS via L7 proxy


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
