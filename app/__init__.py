from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
import logging
from logging.handlers import RotatingFileHandler
from config import DB_CONFIG, REDIS_URL

db = SQLAlchemy()
cache = Cache()

def create_app():
    app = Flask(__name__)

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

    # Set up logging
    handler = RotatingFileHandler('/home/tim/test_rfidpi/logs/app.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    app.logger.addHandler(handler)

    # Create database tables
    with app.app_context():
        db.create_all()

    # Register blueprints
    from .routes import home, tabs, refresh, categories, health
    app.register_blueprint(home.home_bp)
    app.register_blueprint(tabs.tabs_bp)
    app.register_blueprint(refresh.refresh_bp)
    app.register_blueprint(categories.categories_bp)
    app.register_blueprint(health.health_bp)

    # Initialize scheduler
    from .scheduler import init_scheduler
    init_scheduler(app)

    return app