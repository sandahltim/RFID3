from flask import Blueprint, render_template, current_app  # Add current_app import
from app.models.db_models import ItemMaster
from app import db, cache
from sqlalchemy import func
from time import time

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
@cache.cached(timeout=30)
def index():
    try:
        # Summary stats
        total_items = db.session.query(func.count(ItemMaster.tag_id)).scalar()
        status_counts = db.session.query(
            ItemMaster.status, func.count(ItemMaster.tag_id)
        ).group_by(ItemMaster.status).all()
        recent_scans = db.session.query(ItemMaster).order_by(
            ItemMaster.date_last_scanned.desc()
        ).limit(5).all()

        # Generate a timestamp for cache-busting
        cache_bust = int(time())

        return render_template(
            'home.html',
            total_items=total_items,
            status_counts=status_counts,
            recent_scans=recent_scans,
            cache_bust=cache_bust
        )
    except Exception as e:
        current_app.logger.error(f"Error loading home page: {str(e)}")  # Use current_app
        return render_template('home.html', error="Failed to load stats", cache_bust=int(time()))