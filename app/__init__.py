# app/__init__.py
# Version: 2025-07-08-v5
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_redis import FlaskRedis
from config import (
    DB_CONFIG,
    REDIS_URL,
    LOG_FILE,
    APP_IP,
    BASE_DIR,
    STATIC_DIR,
    validate_config,
)
from datetime import datetime
import re

# Initialize extensions
db = SQLAlchemy()
cache = FlaskRedis()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder=str(STATIC_DIR))

    # Configure logging using centralized system
    from app.services.logger import setup_app_logging

    setup_app_logging(app)
    app.logger.info("Application starting up - logging initialized")
    app.logger.debug(f"Static folder path: {app.static_folder}")

    # Validate configuration
    try:
        validate_config()
        app.logger.info("Configuration validation passed")
    except ValueError as e:
        app.logger.error(f"Configuration validation failed: {str(e)}")
        raise

    # Database configuration
    try:
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}&collation={DB_CONFIG['collation']}"
        )
        app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_timeout": 30,
            "pool_recycle": 1800,
        }
        app.config["REDIS_URL"] = REDIS_URL
        app.config["APP_IP"] = APP_IP
        app.logger.info("Database and Redis configuration set successfully")
    except (KeyError, TypeError) as e:
        app.logger.error(
            f"Failed to set database/Redis configuration: {str(e)}", exc_info=True
        )
        raise

    # Initialize extensions
    try:
        db.init_app(app)
        cache.init_app(app)
        app.logger.info("Extensions initialized successfully")
    except (ImportError, AttributeError, RuntimeError) as e:
        app.logger.error(f"Failed to initialize extensions: {str(e)}", exc_info=True)
        raise

    # Add custom Jinja2 filters
    def timestamp_filter(value):
        return int(datetime.now().timestamp())

    app.jinja_env.filters["timestamp"] = timestamp_filter

    def datetimeformat(value):
        if value is None:
            return "N/A"
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return value
        return value.strftime("%Y-%m-%d %H:%M:%S")

    app.jinja_env.filters["datetimeformat"] = datetimeformat

    def regex_replace(value, pattern, replace):
        """Replace characters matching pattern with replace string."""
        if not value:
            return value
        return re.sub(pattern, replace, str(value))

    app.jinja_env.filters["regex_replace"] = regex_replace

    # Note: Database table creation should be handled explicitly via migration scripts
    # or administrative commands, not automatically on every application startup

    # Import and register blueprints
    try:
        from app.routes.home import home_bp
        from app.routes.tab1 import tab1_bp
        from app.routes.tab2 import tab2_bp
        from app.routes.tab3 import tab3_bp
        from app.routes.tab4 import tab4_bp
        from app.routes.tab5 import tab5_bp
        from app.routes.tab7 import tab7_bp
        from app.routes.categories import categories_bp
        from app.routes.health import health_bp
        from app.routes.tabs import tabs_bp
        from app.routes.inventory_analytics import inventory_analytics_bp
        from app.routes.enhanced_analytics_api import enhanced_analytics_bp
        from app.routes.bi_dashboard import bi_bp
        from app.routes.performance import performance_bp
        from app.services.refresh import refresh_bp
        from app.routes.correlation_routes import correlation_bp
        from app.routes.pos_routes import pos_bp
        from app.routes.predictive_analytics_api import predictive_bp
        from app.routes.predictive_analytics_routes import predictive_routes_bp
        from app.routes.configuration_routes import config_bp, config_redirect_bp
        from app.routes.feedback_api import feedback_bp
        from app.routes.feedback_dashboard_route import feedback_dashboard_bp
        from app.routes.manual_import_routes import manual_import_bp

        app.register_blueprint(home_bp)
        app.register_blueprint(tab1_bp)
        app.register_blueprint(tab2_bp)
        app.register_blueprint(tab3_bp)
        app.register_blueprint(tab4_bp)
        app.register_blueprint(tab5_bp)
        app.register_blueprint(tab7_bp)
        app.register_blueprint(categories_bp)
        app.register_blueprint(inventory_analytics_bp)
        app.register_blueprint(enhanced_analytics_bp)
        app.register_blueprint(bi_bp)
        app.register_blueprint(health_bp)
        app.register_blueprint(tabs_bp)
        app.register_blueprint(performance_bp)
        app.register_blueprint(refresh_bp)
        app.register_blueprint(correlation_bp)
        app.register_blueprint(pos_bp)
        app.register_blueprint(predictive_bp)
        app.register_blueprint(predictive_routes_bp)
        app.register_blueprint(config_bp)
        app.register_blueprint(config_redirect_bp)
        app.register_blueprint(feedback_bp)
        app.register_blueprint(feedback_dashboard_bp)
        app.register_blueprint(manual_import_bp)
        app.logger.info("Blueprints registered successfully")

        # Set up performance monitoring middleware
        from app.routes.performance import track_request_performance

        before_request, after_request = track_request_performance()
        app.before_request(before_request)
        app.after_request(after_request)
    except (ImportError, AttributeError) as e:
        app.logger.error(f"Failed to register blueprints: {str(e)}", exc_info=True)
        raise

    # Initialize scheduler
    try:
        from app.services.scheduler import init_scheduler

        init_scheduler(app)
        app.logger.info("Scheduler initialized successfully")
    except (ImportError, RuntimeError) as e:
        app.logger.error(f"Failed to initialize scheduler: {str(e)}", exc_info=True)
        raise

    app.logger.info("Application startup completed successfully")
    return app
