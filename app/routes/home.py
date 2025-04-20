from flask import Blueprint, render_template, current_app
from .. import db, cache
from ..models.db_models import ItemMaster
from sqlalchemy import func
from time import time

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
@cache.cached(timeout=30)
def index():
    try:
        total_items = db.session.query(func.count(ItemMaster.tag_id)).scalar() or 0
        status_counts = db.session.query(
            ItemMaster.status,
            func.count(ItemMaster.tag_id).label('count')
        ).group_by(ItemMaster.status).all()
        status_breakdown = {status: count for status, count in status_counts}

        recent_scans = db.session.query(ItemMaster).order_by(
            ItemMaster.date_last_scanned.desc()
        ).limit(5).all()
        recent_scans = [
            {
                'tag_id': item.tag_id,
                'common_name': item.common_name,
                'date_last_scanned': item.date_last_scanned.isoformat() if item.date_last_scanned else None
            } for item in recent_scans
        ]

        return render_template(
            'home.html',
            total_items=total_items,
            status_breakdown=status_breakdown,
            recent_scans=recent_scans,
            cache_bust=int(time()),
            timestamp=lambda: int(time())
        )
    except Exception as e:
        current_app.logger.error(f"Error loading home page: {str(e)}")
        return render_template('home.html', error="Failed to load dashboard data")