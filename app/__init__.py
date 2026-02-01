"""
Grocery Store Management System - Flask Application Factory
"""
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name=None):
    """Create and configure the Flask application."""
    flask_app = Flask(__name__, template_folder="templates", static_folder="static")

    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    if config_name == "production":
        flask_app.config.from_object("app.config.ProductionConfig")
    elif config_name == "testing":
        flask_app.config.from_object("app.config.TestingConfig")
    else:
        flask_app.config.from_object("app.config.DevelopmentConfig")

    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    csrf.init_app(flask_app)
    login_manager.init_app(flask_app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    from app.models.user import User
    import app.models  # noqa: F401 - register all models with SQLAlchemy

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.inventory import inventory_bp
    from app.routes.pos import pos_bp
    from app.routes.analytics import analytics_bp
    from app.routes.users import users_bp
    from app.routes.customers import customers_bp
    from app.routes.main import main_bp

    flask_app.register_blueprint(main_bp)
    flask_app.register_blueprint(auth_bp, url_prefix="/auth")
    flask_app.register_blueprint(inventory_bp, url_prefix="/inventory")
    flask_app.register_blueprint(pos_bp, url_prefix="/pos")
    flask_app.register_blueprint(analytics_bp, url_prefix="/analytics")
    flask_app.register_blueprint(users_bp, url_prefix="/users")
    flask_app.register_blueprint(customers_bp, url_prefix="/customers")

    # Register error handlers
    @flask_app.errorhandler(404)
    def not_found(e):
        return {"error": "Not found"}, 404

    @flask_app.errorhandler(500)
    def server_error(e):
        return {"error": "Internal server error"}, 500

    return flask_app
