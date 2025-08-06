# app/routes/home.py
# home.py version: 2025-07-10-v7
from flask import Blueprint, render_template, current_app
from .. import db, cache
from ..models.db_models import ItemMaster, Transaction, RefreshState
from sqlalchemy import func
from time import time
import logging
import sys       
from datetime import datetime
import os
import json

# Configure logging with process ID
logger = logging.getLogger(f'home_{os.getpid()}')
logger.setLevel(logging.INFO)
logger.handlers = []  # Clear existing handlers
file_handler = logging.FileHandler('/home/tim/RFID3/logs/rfid_dashboard.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

home_bp = Blueprint('home', __name__)

@home_bp.route('/', endpoint='home')
@home_bp.route('/home', endpoint='home_page')
def home():
    cache_key = 'home_page_cache'
    cached_data = cache.get(cache_key)
    if cached_data:
        logger.debug("Serving home page from cache")
        return render_template('home.html', **json.loads(cached_data), cache_bust=int(time()))

    try:
        session = db.session()
        logger.info("Starting new session for home")

        # Total items
        total_items = session.query(func.count(ItemMaster.tag_id)).scalar()
        logger.info(f'Total items details: {total_items}')
        logger.debug(f"Total items: {total_items}")

        # Status counts
        status_counts = session.query(
            ItemMaster.status,
            func.count(ItemMaster.tag_id).label('count')
        ).group_by(ItemMaster.status).all()
        logger.info(f'Status counts details: {[(status, count) for status, count in status_counts]}')
        logger.debug(f"Status counts in id_item_master: {[(status, count) for status, count in status_counts]}")

        # Items on rent
        items_on_rent = session.query(func.count(ItemMaster.tag_id)).filter(
            ItemMaster.status.in_(['On Rent', 'Delivered'])
        ).scalar()
        logger.info(f'Items on rent details: {items_on_rent}')
        logger.debug(f"Items on rent: {items_on_rent}")

        # Items in service
        subquery = session.query(
            Transaction.tag_id,
            Transaction.scan_date,
            Transaction.service_required
        ).filter(
            Transaction.tag_id == ItemMaster.tag_id
        ).order_by(
            Transaction.scan_date.desc()
        ).subquery()

        service_required_counts = session.query(
            subquery.c.service_required,
            func.count(subquery.c.tag_id).label('count')
        ).group_by(subquery.c.service_required).all()
        logger.info(f'Service required counts details: {[(sr, count) for sr, count in service_required_counts]}')
        logger.debug(f"Service required counts in id_transactions: {[(sr, count) for sr, count in service_required_counts]}")

        items_in_service = session.query(func.count(ItemMaster.tag_id)).filter(
            (ItemMaster.status.notin_(['Ready to Rent', 'On Rent', 'Delivered'])) |
            (ItemMaster.tag_id.in_(
                session.query(subquery.c.tag_id).filter(
                    subquery.c.scan_date == session.query(func.max(Transaction.scan_date)).filter(Transaction.tag_id == subquery.c.tag_id).correlate(subquery).scalar_subquery(),
                    subquery.c.service_required == True
                )
            ))
        ).scalar()
        logger.info(f'Items in service details: {items_in_service}')
        logger.debug(f"Items in service: {items_in_service}")

        # Items available
        items_available = session.query(func.count(ItemMaster.tag_id)).filter(
            ItemMaster.status == 'Ready to Rent'
        ).scalar()
        logger.info(f'Items available details: {items_available}')
        logger.debug(f"Items available: {items_available}")

        # Status breakdown
        status_breakdown = session.query(
            ItemMaster.status,
            func.count(ItemMaster.tag_id).label('count')
        ).group_by(ItemMaster.status).all()
        status_counts = [(status or 'Unknown', count) for status, count in status_breakdown]

        # Recent scans
        recent_scans = session.query(ItemMaster).filter(ItemMaster.date_last_scanned.isnot(None)).order_by(
            ItemMaster.date_last_scanned.desc()
        ).limit(10).all()
        logger.info(f'Recent scans details: {[(scan.tag_id, scan.common_name, scan.date_last_scanned) for scan in recent_scans]}')
        logger.debug(f"Recent scans sample: {[(item.tag_id, item.common_name, item.date_last_scanned) for item in recent_scans[:5]]}")

        # Last refresh state
        refresh_state = session.query(RefreshState).first()
        last_refresh = refresh_state.last_refresh.strftime('%Y-%m-%d %H:%M:%S') if refresh_state and refresh_state.last_refresh else 'N/A'
        refresh_type = refresh_state.state_type if refresh_state else 'N/A'
        logger.info(f'Last refresh details: {last_refresh}, Type: {refresh_type}')
        logger.debug(f"Last refresh: {last_refresh}, Type: {refresh_type}")

        # Cache the response
        render_data = {
            'total_items': total_items or 0,
            'items_on_rent': items_on_rent or 0,
            'items_in_service': items_in_service or 0,
            'items_available': items_available or 0,
            'status_counts': status_counts,
            'recent_scans': [(item.tag_id, item.common_name, item.date_last_scanned.isoformat() if item.date_last_scanned else None) for item in recent_scans],
            'last_refresh': last_refresh,
            'refresh_type': refresh_type
        }
        cache.set(cache_key, json.dumps(render_data), ex=60)  # Cache for 60 seconds

        session.close()
        return render_template('home.html', 
                              total_items=total_items or 0,
                              items_on_rent=items_on_rent or 0,
                              items_in_service=items_in_service or 0,
                              items_available=items_available or 0,
                              status_counts=status_counts,
                              recent_scans=recent_scans,
                              last_refresh=last_refresh,
                              refresh_type=refresh_type,
                              cache_bust=int(time()))
    except Exception as e:
        logger.error(f"Error rendering home page: {str(e)}", exc_info=True)
        if 'session' in locals():
            session.close()
        return render_template('home.html', 
                              total_items=0,
                              items_on_rent=0,
                              items_in_service=0,
                              items_available=0,
                              status_counts=[],
                              recent_scans=[],
                              last_refresh='N/A',
                              refresh_type='N/A',
                              cache_bust=int(time()))