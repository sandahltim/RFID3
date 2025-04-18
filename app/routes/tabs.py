from flask import Blueprint, render_template, jsonify
from app.models.db_models import ItemMaster, SeedRentalClass
from app import db, cache
import re

tabs_bp = Blueprint('tabs', __name__)

def sanitize_id(text):
    """Sanitize text for use in HTML IDs."""
    return re.sub(r'[^\w-]', '_', text.replace('"', '').replace('.', '_'))

@tabs_bp.route('/tab/<int:tab_num>')
@cache.cached(timeout=30)
def tab(tab_num):
    try:
        # Fetch categories (example: group by rental_class_num)
        categories = db.session.query(
            SeedRentalClass.rental_class_id,
            SeedRentalClass.common_name
        ).all()
        return render_template(
            'tab.html',
            tab_num=tab_num,
            categories=categories
        )
    except Exception as e:
        app = tabs_bp.app
        app.logger.error(f"Error loading tab {tab_num}: {str(e)}")
        return render_template('tab.html', tab_num=tab_num, error="Failed to load data")

@tabs_bp.route('/tab/<int:tab_num>/data', methods=['GET'])
@cache.cached(timeout=30)
def tab_data(tab_num):
    try:
        # Example: Fetch items for the tab
        items = db.session.query(ItemMaster).all()
        data = [{
            'tag_id': item.tag_id,
            'common_name': item.common_name,
            'bin_location': item.bin_location,
            'status': item.status,
            'last_contract_num': item.last_contract_num
        } for item in items]
        return jsonify(data)
    except Exception as e:
        app = tabs_bp.app
        app.logger.error(f"Error fetching tab {tab_num} data: {str(e)}")
        return jsonify({'error': 'Failed to fetch data'}), 500