"""
Flask application configuration.

Environment-based config with hardened security defaults for Databricks Apps deployment.
See: https://flask.palletsprojects.com/en/3.0.x/config/
"""

import os

class DevelopmentConfig:
    DEBUG = True
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    # Local development uses in-memory SQLite (avoids filesystem issues with uv on Windows)
    # Override with DATABASE_URL env var if needed
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///:memory:")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session cookie security (per auth.md: HttpOnly, SameSite=Lax)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False  # Local dev uses HTTP


class ProductionConfig:
    DEBUG = False
    SECRET_KEY = os.environ.get("SECRET_KEY")  # MUST be set via environment (Databricks Secret)
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
