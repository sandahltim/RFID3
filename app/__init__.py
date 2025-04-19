from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
import logging
from logging.handlers import TimedRotatingFileHandler
import os

db = SQLAlchemy()
cache = Cache()

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{os.environ.get('DB_USER', 'rfid_user')}:{os.environ.get('DB_PASSWORD', 'rfid_user_password')}@"
        f"localhost/rfid_inventory?charset=utf8mb4"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['CACHE_TYPE'] = 'redis'
    app.config['CACHE_REDIS_URL'] = 'redis://localhost:6379/0'

    # Initialize extensions
    db.init_app(app)
    cache.init_app(app)

    # Logging
    os.makedirs(os.path.join(app.root_path, '..', 'logs'), exist_ok=True)
    handler = TimedRotatingFileHandler(
        os.path.join(app.root_path, '..', 'logs', 'rfid_dashboard.log'),
        when='midnight',
        interval=1,
        backupCount=7
    )
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG)

    # Register blueprints with error handling
    try:
        from app.routes.home import home_bp
        app.register_blueprint(home_bp)
    except ImportError as e:
        app.logger.error(f"Failed to import home_bp: {str(e)}")
        raise

    try:
        from app.routes.tabs import tabs_bp
        app.register_blueprint(tabs_bp)
    except ImportError as e:
        app.logger.error(f"Failed to import tabs_bp: {str(e)}")
        raise

    try:
        from app.services.refresh import refresh_bp
        app.register_blueprint(refresh_bp)
    except ImportError as e:
        app.logger.error(f"Failed to import refresh_bp: {str(e)}")
        raise

    # Initialize scheduler
    try:
        from app.services.scheduler import init_scheduler
        with app.app_context():
            init_scheduler()
    except ImportError as e:
        app.logger.error(f"Failed to initialize scheduler: {str(e)}")
        raise

    return app