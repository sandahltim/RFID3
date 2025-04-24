import os
import logging
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
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    app.logger.info(f"Static folder path: {app.static_folder}")

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['REDIS_URL'] = REDIS_URL

    # Initialize extensions
    db.init_app(app)
    cache.init_app(app)

    # Create database tables
    with app.app_context():
        app.logger.info("Creating database tables")
        db.create_all()
        app.logger.info("Database tables created")

    # Import and register blueprints
    from app.routes.home import home_bp
    from app.routes.tab1 import tab1_bp
    from app.routes.tab2 import tab2_bp
    from app.routes.tab3 import tab3_bp
    from app.routes.tab4 import tab4_bp
    from app.routes.tab5 import tab5_bp
    from app.routes.categories import categories_bp
    from app.routes.health import health_bp
    from app.routes.refresh import refresh_bp
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

    # Initialize scheduler
    from app.services.scheduler import init_scheduler
    init_scheduler(app)

    return app