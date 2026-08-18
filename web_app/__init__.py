from flask import Flask, jsonify, g
from flask_cors import CORS

from shared_library.global_logger_hub import bootstrap, get_app_logger, set_request_id, reset_request_id, new_request_id
from shared_library.health_check import AgentServerPoller, poll_agent_server
from .config import config
from .database import create_all_tables, get_session, init_engine
from .seed import seed_database

# Bootstrap logging once at import time
bootstrap()
logger = get_app_logger(__name__)

# Global agent server poller (started on app init)
_agent_poller: AgentServerPoller | None = None


def create_app(config_name: str = "development") -> Flask:
    global _agent_poller
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    CORS(app)
    init_engine(app.config["SQLALCHEMY_DATABASE_URI"])
    create_all_tables()

    session = get_session()
    try:
        seed_database(session)
    finally:
        session.remove()

    from .auth import get_current_user
    from .blueprints.api import api_bp
    from .blueprints.bff import bff_bp
    from .blueprints.views import views_bp
    from .blueprints.health import health_bp

    # Start agent server poller (30s interval, logs connectivity)
    _agent_poller = AgentServerPoller(interval_seconds=30)
    _agent_poller.start()
    logger.info("agent_poller | started")

    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(bff_bp)
    app.register_blueprint(health_bp)

    @app.before_request
    def before_request():
        """Bind request ID + user info to request context."""
        g.request_id = set_request_id(None)
        g.logger = get_app_logger(f"web_app.request.{new_request_id()}")

    @app.after_request
    def after_request(response):
        """Clean up request context."""
        reset_request_id()
        return response

    @app.context_processor
    def inject_current_user():
        return {"current_user": get_current_user()}

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        get_session().remove()

    @app.teardown_appcontext
    def shutdown_poller(exception=None):
        """Stop agent poller on app teardown."""
        global _agent_poller
        if _agent_poller is not None:
            _agent_poller.stop()
            _agent_poller = None

    @app.errorhandler(400)
    def bad_request(e):
        logger.warning(f"Bad request: {e}")
        return jsonify({"error": "Bad request", "message": str(e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        logger.debug(f"Not found: {e}")
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"Internal error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

    return app
