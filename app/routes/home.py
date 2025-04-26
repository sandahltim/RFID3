from flask import Blueprint, render_template, current_app
from .. import db
from ..models.db_models import ItemMaster, Transaction
from sqlalchemy import func, text
from time import time
import logging
import sys

# Configure logging
logger = logging.getLogger('home')
logger.setLevel(logging.INFO)

# Remove existing handlers to avoid duplicates
logger.handlers = []

# File handler for rfid_dashboard.log
file_handler = logging.FileHandler('/home/tim/test_rfidpi/logs/rfid_dashboard.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

home_bp = Blueprint('home', __name__)

# Version marker
logger.info("Deployed home.py version: 2025-04-25-v1")

@home_bp.route('/', endpoint='home')
def home():
    try:
        session = db.session()
        logger.info("Starting new session for home")
        current_app.logger.info("Starting new session for home")

        # Total items (all items in id_item_master)
        total_items = session.query(func.count(ItemMaster.tag_id)).scalar()
        logger.info(f"Total items: {total_items}")
        current_app.logger.info(f"Total items: {total_items}")

        # Log distinct status values to debug
        status_counts = session.query(
            ItemMaster.status,
            func.count(ItemMaster.tag_id).label('count')
        ).group_by(ItemMaster.status).all()
        logger.info(f"Status counts in id_item_master: {[(status, count) for status, count in status_counts]}")
        current_app.logger.info(f"Status counts in id_item_master: {[(status, count) for status, count in status_counts]}")

        # Items on rent (status = 'On Rent' or 'Delivered')
        items_on_rent = session.query(func.count(ItemMaster.tag_id)).filter(
            ItemMaster.status.in_(['On Rent', 'Delivered'])
        ).scalar()
        logger.info(f"Items on rent: {items_on_rent}")
        current_app.logger.info(f"Items on rent: {items_on_rent}")

        # Items in service logic
        subquery = session.query(
            Transaction.tag_id,
            Transaction.scan_date,
            Transaction.service_required
        ).filter(
            Transaction.tag_id == ItemMaster.tag_id
        ).order_by(
            Transaction.scan_date.desc()
        ).subquery()

        # Log service_required counts to debug
        service_required_counts = session.query(
            subquery.c.service_required,
            func.count(subquery.c.tag_id).label('count')
        ).group_by(subquery.c.service_required).all()
        logger.info(f"Service required counts in id_transactions: {[(sr, count) for sr, count in service_required_counts]}")
        current_app.logger.info(f"Service required counts in id_transactions: {[(sr, count) for sr, count in service_required_counts]}")

        items_in_service = session.query(func.count(ItemMaster.tag_id)).filter(
            (ItemMaster.status.notin_(['Ready to Rent', 'On Rent', 'Delivered'])) |
            (ItemMaster.tag_id.in_(
                session.query(subquery.c.tag_id).filter(
                    subquery.c.scan_date == session.query(func.max(Transaction.scan_date)).filter(Transaction.tag_id == subquery.c.tag_id).correlate(subquery).scalar_subquery(),
                    subquery.c.service_required == True
                )
            ))
        ).scalar()
        logger.info(f"Items in service: {items_in_service}")
        current_app.logger.info(f"Items in service: {items_in_service}")

        # Items available (status = 'Ready to Rent')
        items_available = session.query(func.count(ItemMaster.tag_id)).filter(
            ItemMaster.status == 'Ready to Rent'
        ).scalar()
        logger.info(f"Items available: {items_available}")
        current_app.logger.info(f"Items available: {items_available}")

        # Fetch status breakdown for template
        status_breakdown = session.query(
            ItemMaster.status,
            func.count(ItemMaster.tag_id).label('count')
        ).group_by(ItemMaster.status).all()
        status_counts = [(status or 'Unknown', count) for status, count in status_breakdown]

        # Fetch recent scans for template
        recent_scans = session.query(ItemMaster).order_by(
            ItemMaster.date_last_scanned.desc()
        ).limit(10).all()
        logger.info(f"Recent scans sample: {[(item.tag_id, item.common_name, item.date_last_scanned) for item in recent_scans[:5]]}")
        current_app.logger.info(f"Recent scans sample: {[(item.tag_id, item.common_name, item.date_last_scanned) for item in recent_scans[:5]]}")

        session.close()
        return render_template('home.html', 
                              total_items=total_items or 0,
                              items_on_rent=items_on_rent or 0,
                              items_in_service=items_in_service or 0,
                              items_available=items_available or 0,
                              status_counts=status_counts,
                              recent_scans=recent_scans,
                              cache_bust=int(time()))
    except Exception as e:
        logger.error(f"Error rendering home page: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error rendering home page: {str(e)}", exc_info=True)
        session.close()
        return render_template('home.html', 
                              total_items=0,
                              items_on_rent=0,
                              items_in_service=0,
                              items_available=0,
                              status_counts=[],
                              recent_scans=[],
                              cache_bust=int(time()))