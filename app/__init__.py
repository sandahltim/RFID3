import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_redis import FlaskRedis
from config import DB_CONFIG, REDIS_URL, LOG_FILE

# Initialize extensions
db = SQLAlchemy()
cache = FlaskRedis()

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder='static')

    # Configure logging
    log_dir = os.path.dirname(LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    handler = RotatingFileHandler(LOG_FILE, maxBytes=1000000, backupCount=5)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    # Clear existing handlers to prevent duplicates
    logging.getLogger('').handlers = []
    app.logger.handlers = []
    # Add handler to root logger and app logger
    logging.getLogger('').addHandler(handler)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG)
    app.logger.propagate = False  # Prevent double logging
    app.logger.info("Application starting up - logging initialized")
    app.logger.debug(f"Static folder path: {app.static_folder}")

    # Database configuration with connection pooling
    try:
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}"
            f"&collation={DB_CONFIG['collation']}"
        )
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_timeout': 30,
            'pool_recycle': 1800,  # Recycle connections every 30 minutes
        }
        app.config['REDIS_URL'] = REDIS_URL
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
        from app.services.refresh import refresh_bp
        from app.routes.tabs import tabs_bp

        app.register_blueprint(home_bp)
        app.register_blueprint(tab1_bp)
        app.register_blueprint(tab2_bp)
        app.register_blueprint(tab3_bp)
        app.register_blueprint(tab4_bp)
        app.register_blueprint(tab5_bp)
        app.register_blueprint(categories_bp)
        app.register_blueprint(health_bp)
        app.register_blueprint(refresh_bp)
        app.register_blueprint(tabs_bp)
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