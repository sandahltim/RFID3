from flask import Blueprint, render_template
from app.models.db_models import ItemMaster
from app import db, cache
from sqlalchemy import func

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

        return render_template(
            'home.html',
            total_items=total_items,
            status_counts=status_counts,
            recent_scans=recent_scans
        )
    except Exception as e:
        app = home_bp.app
        app.logger.error(f"Error loading home page: {str(e)}")
        return render_template('home.html', error="Failed to load stats")