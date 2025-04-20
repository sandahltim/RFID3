from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
import logging
from logging.handlers import RotatingFileHandler
from flask_wtf.csrf import CSRFProtect
# Adjust import path to point to the root directory
from ..config import DB_CONFIG, REDIS_CONFIG

db = SQLAlchemy()
cache = Cache()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mariadb+mariadbconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Caching configuration
    app.config['CACHE_TYPE'] = 'redis'
    app.config['CACHE_REDIS_HOST'] = REDIS_CONFIG['host']
    app.config['CACHE_REDIS_PORT'] = REDIS_CONFIG['port']
    app.config['CACHE_REDIS_DB'] = REDIS_CONFIG['db']

    # Secret key for CSRF protection
    app.config['SECRET_KEY'] = 'your-secret-key-here'  # Replace with a secure key

    # Initialize extensions
    db.init_app(app)
    cache.init_app(app)
    csrf.init_app(app)

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