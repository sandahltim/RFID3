from flask import Blueprint, render_template, current_app
from .. import db
from ..models.db_models import ItemMaster, Transaction
from sqlalchemy import func
from time import time

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def home():
    try:
        session = db.session()

        # Total items (all items in id_item_master)
        total_items = session.query(func.count(ItemMaster.tag_id)).scalar()

        # Items on rent (status = 'On Rent' or 'Delivered')
        items_on_rent = session.query(func.count(ItemMaster.tag_id)).filter(
            ItemMaster.status.in_(['On Rent', 'Delivered'])
        ).scalar()

        # Items in service logic:
        # 1. Status is not 'Ready to Rent', 'On Rent', or 'Delivered', OR
        # 2. Most recent transaction has service_required = true
        subquery = session.query(
            Transaction.tag_id,
            Transaction.scan_date,
            Transaction.service_required
        ).filter(
            Transaction.tag_id == ItemMaster.tag_id
        ).order_by(
            Transaction.scan_date.desc()
        ).subquery()

        items_in_service = session.query(func.count(ItemMaster.tag_id)).filter(
            (ItemMaster.status.notin_(['Ready to Rent', 'On Rent', 'Delivered'])) |
            (ItemMaster.tag_id.in_(
                session.query(subquery.c.tag_id).filter(
                    subquery.c.scan_date == session.query(func.max(Transaction.scan_date)).filter(Transaction.tag_id == subquery.c.tag_id).correlate(subquery).scalar_subquery(),
                    subquery.c.service_required == True
                )
            ))
        ).scalar()

        # Items available (status = 'Ready to Rent')
        items_available = session.query(func.count(ItemMaster.tag_id)).filter(
            ItemMaster.status == 'Ready to Rent'
        ).scalar()

        session.close()
        return render_template('home.html', 
                              total_items=total_items or 0,
                              items_on_rent=items_on_rent or 0,
                              items_in_service=items_in_service or 0,
                              items_available=items_available or 0,
                              cache_bust=int(time()))
    except Exception as e:
        current_app.logger.error(f"Error rendering home page: {str(e)}", exc_info=True)
        return render_template('home.html', 
                              total_items=0,
                              items_on_rent=0,
                              items_in_service=0,
                              items_available=0,
                              cache_bust=int(time()))