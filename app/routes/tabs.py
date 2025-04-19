from flask import Blueprint, render_template, jsonify, request
from app.models.db_models import ItemMaster, SeedRentalClass
from app import db, cache
import re

tabs_bp = Blueprint('tabs', __name__)

def sanitize_id(text):
    """Sanitize text for use in HTML IDs."""
    return re.sub(r'[^\w-]', '_', text.replace('"', '').replace('.', '_').lower())

@tabs_bp.route('/tab/<int:tab_num>')
@cache.cached(timeout=30)
def tab(tab_num):
    try:
        # Fetch categories (group by category from id_rfidtag)
        categories = db.session.query(
            ItemMaster.category.distinct().label('category')
        ).filter(ItemMaster.category.isnot(None)).all()
        # Fetch bin locations
        bin_locations = db.session.query(
            ItemMaster.bin_location.distinct().label('bin_location')
        ).filter(ItemMaster.bin_location.isnot(None)).all()
        return render_template(
            'tab.html',
            tab_num=tab_num,
            categories=[c.category for c in categories],
            bin_locations=[b.bin_location for b in bin_locations]
        )
    except Exception as e:
        app = tabs_bp.app
        app.logger.error(f"Error loading tab {tab_num}: {str(e)}")
        return render_template('tab.html', tab_num=tab_num, error="Failed to load data")

@tabs_bp.route('/tab/<int:tab_num>/data', methods=['GET'])
@cache.cached(timeout=30)
def tab_data(tab_num):
    try:
        category = request.args.get('category')
        subcategory = request.args.get('subcategory')
        common_name = request.args.get('common_name')
        
        query = db.session.query(ItemMaster)
        if category:
            query = query.filter(ItemMaster.category.ilike(category))
        if subcategory:
            query = query.filter(ItemMaster.bin_location.ilike(subcategory))
        if common_name:
            query = query.filter(ItemMaster.common_name.ilike(common_name))
        
        items = query.all()
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

@tabs_bp.route('/tab/<int:tab_num>/subcat_data', methods=['GET'])
@cache.cached(timeout=30)
def subcat_data(tab_num):
    try:
        category = request.args.get('category')
        if not category:
            return jsonify({'error': 'Category required'}), 400
        
        # Fetch subcategories (bin_location) for the category
        subcategories = db.session.query(
            ItemMaster.bin_location.distinct().label('subcategory')
        ).filter(ItemMaster.category.ilike(category)).all()
        
        # Fetch common names for each subcategory
        result = []
        for sub in subcategories:
            common_names = db.session.query(
                ItemMaster.common_name.distinct().label('common_name')
            ).filter(
                ItemMaster.category.ilike(category),
                ItemMaster.bin_location.ilike(sub.subcategory)
            ).all()
            result.append({
                'subcategory': sub.subcategory,
                'common_names': [cn.common_name for cn in common_names]
            })
        
        return jsonify(result)
    except Exception as e:
        app = tabs_bp.app
        app.logger.error(f"Error fetching subcat data for tab {tab_num}: {str(e)}")
        return jsonify({'error': 'Failed to fetch subcategory data'}), 500