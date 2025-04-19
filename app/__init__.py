from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
import logging
from logging.handlers import RotatingFileHandler

db = SQLAlchemy()
cache = Cache(config={'CACHE_TYPE': 'simple'})

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////home/tim/test_rfidpi/rfidpi.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key'
    
    # Initialize extensions
    db.init_app(app)
    cache.init_app(app)
    
    # Setup logging
    handler = RotatingFileHandler('/home/tim/test_rfidpi/logs/app.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Register blueprints
    from app.routes.home import home_bp
    from app.routes.tabs import tabs_bp
    from app.services.refresh import refresh_bp
    from app.routes.categories import categories_bp
    app.register_blueprint(home_bp)
    app.register_blueprint(tabs_bp)
    app.register_blueprint(refresh_bp)
    app.register_blueprint(categories_bp)
    
    return app

app = create_app()