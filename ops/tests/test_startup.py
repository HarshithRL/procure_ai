"""
Smoke test for production startup paths.

Ensures the WSGI entry point and Flask app can be imported and initialized
without errors in both development and production configurations.

Run locally:
  FLASK_ENV=production SECRET_KEY=test uv run python -m pytest ops/tests/test_startup.py -v
  FLASK_ENV=development uv run python -m pytest ops/tests/test_startup.py -v

Run as pre-deploy gate:
  FLASK_ENV=production SECRET_KEY=test python -c "import sys; sys.path.insert(0, '.'); import wsgi; print('PASS: wsgi import')"
"""

import os
import sys
from pathlib import Path

import pytest

# Add project root to path so wsgi can be imported
_PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))


@pytest.fixture
def setup_env_production():
    """Set up environment for production config."""
    os.environ["FLASK_ENV"] = "production"
    os.environ["SECRET_KEY"] = "test-secret-key-for-smoke-test"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    
    # Clear module cache
    for mod in list(sys.modules.keys()):
        if mod.startswith("wsgi") or mod.startswith("web_app"):
            del sys.modules[mod]
    
    yield
    # Cleanup
    os.environ.pop("FLASK_ENV", None)
    os.environ.pop("SECRET_KEY", None)
    os.environ.pop("DATABASE_URL", None)


@pytest.fixture
def setup_env_development():
    """Set up environment for development config."""
    os.environ["FLASK_ENV"] = "development"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    
    # Clear module cache
    for mod in list(sys.modules.keys()):
        if mod.startswith("wsgi") or mod.startswith("web_app"):
            del sys.modules[mod]
    
    yield
    os.environ.pop("FLASK_ENV", None)
    os.environ.pop("DATABASE_URL", None)


def test_wsgi_import_production(setup_env_production):
    """Test that wsgi module can be imported in production without errors."""
    # This import simulates what gunicorn does: `gunicorn wsgi:app`
    import wsgi
    assert wsgi.app is not None
    assert hasattr(wsgi.app, "config")
    # Verify the config was applied
    assert wsgi.app.debug is False  # production = DEBUG=False


def test_wsgi_import_development(setup_env_development):
    """Test that wsgi module can be imported in development without errors."""
    import wsgi
    assert wsgi.app is not None
    assert hasattr(wsgi.app, "config")
    # Verify the config was applied
    assert wsgi.app.debug is True  # development = DEBUG=True


def test_flask_app_factory_production(setup_env_production):
    """Test Flask app factory with production config."""
    from web_app import create_app
    app = create_app(config_name="production")
    assert app is not None
    assert app.debug is False
    assert app.config["DEBUG"] is False


def test_flask_app_factory_development(setup_env_development):
    """Test Flask app factory with development config."""
    from web_app import create_app
    app = create_app(config_name="development")
    assert app is not None
    assert app.debug is True
    assert app.config["DEBUG"] is True


def test_invalid_flask_env_defaults_to_production():
    """Test that invalid FLASK_ENV defaults to production gracefully."""
    os.environ["FLASK_ENV"] = "invalid-env-name"
    os.environ["SECRET_KEY"] = "test"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"  # Use in-memory DB for test
    
    import importlib
    
    # Clear module cache to force re-import
    for mod in list(sys.modules.keys()):
        if mod.startswith("wsgi") or mod.startswith("web_app"):
            del sys.modules[mod]
    
    import wsgi
    assert wsgi.app is not None
    assert wsgi.app.debug is False  # Should default to production (DEBUG=False)
    
    os.environ.pop("FLASK_ENV", None)
    os.environ.pop("SECRET_KEY", None)
    os.environ.pop("DATABASE_URL", None)


def test_production_config_with_missing_secret_key():
    """Test that ProductionConfig allows missing SECRET_KEY (deferred validation)."""
    os.environ.pop("SECRET_KEY", None)
    
    import sys
    if "web_app.config" in sys.modules:
        del sys.modules["web_app.config"]
    
    from web_app.config import ProductionConfig
    # Should not raise during import; SECRET_KEY is None but allowed at class level
    assert ProductionConfig.SECRET_KEY is None


def test_app_has_required_blueprints(setup_env_development):
    """Test that Flask app registers all required blueprints."""
    # The fixture clears module cache
    import wsgi
    
    # Extract blueprint names from the app's blueprints
    blueprint_names = {bp for bp in wsgi.app.blueprints.keys()}
    
    # Verify required blueprints are registered (using their registered names)
    expected_blueprints = {"views", "api", "bff"}
    assert expected_blueprints.issubset(blueprint_names), (
        f"Missing blueprints. Expected {expected_blueprints}, got {blueprint_names}"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
