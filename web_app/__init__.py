from flask import Flask, jsonify
from flask_cors import CORS

from .config import config
from .database import create_all_tables, get_session, init_engine
from .seed import seed_database


def create_app(config_name: str = "development") -> Flask:
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
    from .blueprints.views import views_bp

    app.register_blueprint(views_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.context_processor
    def inject_current_user():
        return {"current_user": get_current_user()}

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        get_session().remove()

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request", "message": str(e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error(f"Internal error: {e}")
        return jsonify({"error": "Internal server error"}), 500

    return app
