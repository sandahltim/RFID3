# app/__init__.py
# Version: 2025-07-08-v5
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_redis import FlaskRedis
from config import DB_CONFIG, REDIS_URL, LOG_FILE, APP_IP
from datetime import datetime
import re

# Initialize extensions
db = SQLAlchemy()
cache = FlaskRedis()

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder='/home/tim/test_rfidpi/static')

    # Configure logging
    log_dir = os.path.dirname(LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    handler = RotatingFileHandler(LOG_FILE, maxBytes=1000000, backupCount=5)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logging.getLogger('').handlers = []
    app.logger.handlers = []
    logging.getLogger('').addHandler(handler)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG)
    app.logger.propagate = False
    app.logger.info("Application starting up - logging initialized")
    app.logger.debug(f"Static folder path: {app.static_folder}")

    # Database configuration
    try:
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}&collation={DB_CONFIG['collation']}"
        )
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_timeout': 30,
            'pool_recycle': 1800,
        }
        app.config['REDIS_URL'] = REDIS_URL
        app.config['APP_IP'] = APP_IP
        app.logger.info("Database and Redis configuration set successfully")
    except Exception as e:
        app.logger.error(f"Failed to set database/Redis configuration: {str(e)}", exc_info=True)
        raise

    # Initialize extensions
    try:
        db.init_app(app)
        cache.init_app(app)
        app.logger.info("Extensions initialized successfully")
    except Exception as e:
        app.logger.error(f"Failed to initialize extensions: {str(e)}", exc_info=True)
        raise

    # Add custom Jinja2 filters
    def timestamp_filter(value):
        return int(datetime.now().timestamp())
    app.jinja_env.filters['timestamp'] = timestamp_filter

    def datetimeformat(value):
        if value is None:
            return 'N/A'
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return value
        return value.strftime('%Y-%m-%d %H:%M:%S')
    app.jinja_env.filters['datetimeformat'] = datetimeformat

    def regex_replace(value, pattern, replace):
        """Replace characters matching pattern with replace string."""
        if not value:
            return value
        return re.sub(pattern, replace, str(value))
    app.jinja_env.filters['regex_replace'] = regex_replace

    # Create database tables
    try:
        with app.app_context():
            app.logger.info("Creating database tables")
            db.create_all()
            app.logger.info("Database tables created")
    except Exception as e:
        app.logger.error(f"Failed to create database tables: {str(e)}", exc_info=True)
        raise

    # Import and register blueprints
    try:
        from app.routes.home import home_bp
        from app.routes.tab1 import tab1_bp
        from app.routes.tab2 import tab2_bp
        from app.routes.tab3 import tab3_bp
        from app.routes.tab4 import tab4_bp
        from app.routes.tab5 import tab5_bp
        from app.routes.categories import categories_bp
        from app.routes.health import health_bp
        from app.routes.tabs import tabs_bp
        from app.services.refresh import refresh_bp

        app.register_blueprint(home_bp)
        app.register_blueprint(tab1_bp)
        app.register_blueprint(tab2_bp)
        app.register_blueprint(tab3_bp)
        app.register_blueprint(tab4_bp)
        app.register_blueprint(tab5_bp)
        app.register_blueprint(categories_bp)
        app.register_blueprint(health_bp)
        app.register_blueprint(tabs_bp)
        app.register_blueprint(refresh_bp)
        app.logger.info("Blueprints registered successfully")
    except Exception as e:
        app.logger.error(f"Failed to register blueprints: {str(e)}", exc_info=True)
        raise

    # Initialize scheduler
    try:
        from app.services.scheduler import init_scheduler
        init_scheduler(app)
        app.logger.info("Scheduler initialized successfully")
    except Exception as e:
        app.logger.error(f"Failed to initialize scheduler: {str(e)}", exc_info=True)
        raise

    app.logger.info("Application startup completed successfully")
    return app