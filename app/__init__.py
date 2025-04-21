import os
from flask import Flask, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
import logging
from logging.handlers import RotatingFileHandler
from config import DB_CONFIG, REDIS_URL

# Set up sync.log logging early
sync_handler = RotatingFileHandler('/home/tim/test_rfidpi/logs/sync.log', maxBytes=10000, backupCount=1)
sync_handler.setLevel(logging.DEBUG)
sync_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
sync_handler.setFormatter(sync_formatter)
logging.getLogger('').addHandler(sync_handler)
logging.getLogger('').setLevel(logging.DEBUG)

db = SQLAlchemy()
cache = Cache()

def create_app():
    # Define the project root directory (where static/ is located)
    project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    static_folder = os.path.join(project_root, 'static')

    app = Flask(__name__, static_folder=static_folder, static_url_path='/static')

    # Log the static folder path for debugging
    app.logger.info(f"Static folder path: {app.static_folder}")

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Caching configuration
    app.config['CACHE_TYPE'] = 'redis'
    app.config['CACHE_REDIS_URL'] = REDIS_URL

    # Initialize extensions
    db.init_app(app)
    cache.init_app(app)

    # Set up app.log logging
    handler = RotatingFileHandler('/home/tim/test_rfidpi/logs/app.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

    # Create database tables
    with app.app_context():
        app.logger.info("Creating database tables")
        db.create_all()
        app.logger.info("Database tables created")

    # Debug route to test static file serving
    @app.route('/debug/static/<path:filename>')
    def debug_static(filename):
        app.logger.info(f"Debug static file request: {filename}")
        return send_from_directory(app.static_folder, filename)

    # Register blueprints
    from app.routes.home import home_bp
    from app.routes.tabs import tabs_bp
    from app.routes.categories import categories_bp
    from app.routes.health import health_bp
    from app.services.refresh import refresh_bp
    app.register_blueprint(home_bp)
    app.register_blueprint(tabs_bp)
    app.register_blueprint(refresh_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(health_bp)

    # Initialize scheduler
    from app.services.scheduler import init_scheduler
    with app.app_context():
        app.logger.info("Initializing scheduler")
        init_scheduler(app)
        app.logger.info("Scheduler initialized")

    return app