from flask import Blueprint, render_template, current_app, jsonify, request
from .. import db, cache
from ..models.db_models import ItemMaster, Transaction
from sqlalchemy import func
from time import time

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
@cache.cached(timeout=30)
def index():
    try:
        # Clear cache to ensure fresh data
        cache.clear()
        current_app.logger.info("Cleared cache for homepage")

        # Use DISTINCT to avoid counting duplicate tag_ids, exclude suspicious tag_ids
        total_items = db.session.query(func.count(func.distinct(ItemMaster.tag_id))).filter(
            ItemMaster.tag_id.notlike('7070%')  # Exclude suspicious tag_ids
        ).scalar() or 0
        current_app.logger.debug(f"Total distinct items: {total_items}")

        status_counts = db.session.query(
            func.coalesce(ItemMaster.status, 'Unknown').label('status'),
            func.count(func.distinct(ItemMaster.tag_id)).label('count')
        ).filter(
            ItemMaster.tag_id.notlike('7070%')  # Exclude suspicious tag_ids
        ).group_by(
            func.coalesce(ItemMaster.status, 'Unknown')
        ).all()
        current_app.logger.debug(f"Status counts: {status_counts}")

        status_breakdown = {status: count for status, count in status_counts}

        # Fetch recent scans, ensuring distinct tag_ids and excluding suspicious patterns
        recent_scans = db.session.query(ItemMaster).filter(
            ItemMaster.tag_id.notlike('7070%')  # Exclude suspicious tag_ids
        ).order_by(
            ItemMaster.date_last_scanned.desc()
        ).limit(5).all()
        recent_scans = [
            {
                'tag_id': item.tag_id,
                'common_name': item.common_name,
                'date_last_scanned': item.date_last_scanned.strftime('%m/%d/%Y, %I:%M:%S %p') if item.date_last_scanned else 'N/A'
            }
            for item in recent_scans
        ]
        current_app.logger.debug(f"Recent scans: {recent_scans}")

        return render_template(
            'home.html',
            total_items=total_items,
            status_counts=status_counts,
            recent_scans=recent_scans,
            cache_bust=int(time()),
            timestamp=lambda: int(time())
        )
    except Exception as e:
        current_app.logger.error(f"Error loading home page: {str(e)}", exc_info=True)
        return render_template('home.html', error="Failed to load dashboard data")

@home_bp.route('/get_contract_date')
def get_contract_date():
    try:
        contract_number = request.args.get('contract_number')
        if not contract_number:
            return jsonify({'error': 'Contract number is required'}), 400

        # Fetch the earliest transaction date for this contract
        transaction = db.session.query(
            func.min(Transaction.date).label('date')
        ).filter(
            Transaction.contract_number == contract_number
        ).first()

        return jsonify({'date': transaction.date.isoformat() if transaction.date else None})
    except Exception as e:
        current_app.logger.error(f"Error fetching contract date: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch contract date'}), 500