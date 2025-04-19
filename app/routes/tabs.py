from flask import Blueprint, render_template, jsonify, request, current_app
from app.models.db_models import ItemMaster
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
        current_app.logger.info(f"Loading tab {tab_num}")
        # Fetch rental class numbers (group by rental_class_num from id_item_master)
        rental_classes_query = db.session.query(
            ItemMaster.rental_class_num.distinct().label('rental_class_num')
        ).filter(ItemMaster.rental_class_num.isnot(None))
        rental_classes = rental_classes_query.all()
        current_app.logger.info(f"Fetched {len(rental_classes)} rental classes")
        
        # Fetch bin locations from ItemMaster
        bin_locations_query = db.session.query(
            ItemMaster.bin_location.distinct().label('bin_location')
        ).filter(ItemMaster.bin_location.isnot(None))
        bin_locations = bin_locations_query.all()
        current_app.logger.info(f"Fetched {len(bin_locations)} bin locations")
        
        return render_template(
            'tab.html',
            tab_num=tab_num,
            categories=[c.rental_class_num for c in rental_classes],
            bin_locations=[b.bin_location for b in bin_locations]
        )
    except Exception as e:
        current_app.logger.error(f"Error loading tab {tab_num}: {str(e)}")
        return render_template('tab.html', tab_num=tab_num, error=f"Failed to load data: {str(e)}")

@tabs_bp.route('/tab/<int:tab_num>/data', methods=['GET'])
@cache.cached(timeout=30)
def tab_data(tab_num):
    try:
        category = request.args.get('category')  # rental_class_num
        subcategory = request.args.get('subcategory')  # bin_location
        common_name = request.args.get('common_name')
        
        query = db.session.query(ItemMaster)
        if category:
            query = query.filter(ItemMaster.rental_class_num.ilike(category))
        if subcategory:
            query = query.filter(ItemMaster.bin_location.ilike(subcategory))
        if common_name:
            query = query.filter(ItemMaster.common_name.ilike(common_name))
        
        items = query.all()
        current_app.logger.info(f"Fetched {len(items)} items for tab {tab_num}")
        data = [{
            'tag_id': item.tag_id,
            'common_name': item.common_name,
            'bin_location': item.bin_location,
            'status': item.status,
            'last_contract_num': item.last_contract_num
        } for item in items]
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Error fetching tab {tab_num} data: {str(e)}")
        return jsonify({'error': 'Failed to fetch data'}), 500

@tabs_bp.route('/tab/<int:tab_num>/subcat_data', methods=['GET'])
@cache.cached(timeout=30)
def subcat_data(tab_num):
    try:
        category = request.args.get('category')  # rental_class_num
        if not category:
            return jsonify({'error': 'Rental class required'}), 400
        
        # Fetch subcategories (bin_location) for the rental class
        subcategories = db.session.query(
            ItemMaster.bin_location.distinct().label('subcategory')
        ).filter(ItemMaster.rental_class_num.ilike(category)).all()
        current_app.logger.info(f"Fetched {len(subcategories)} subcategories for rental class {category}")
        
        # Fetch common names for each subcategory
        result = []
        for sub in subcategories:
            common_names = db.session.query(
                ItemMaster.common_name.distinct().label('common_name')
            ).filter(
                ItemMaster.rental_class_num.ilike(category),
                ItemMaster.bin_location.ilike(sub.subcategory)
            ).all()
            result.append({
                'subcategory': sub.subcategory,
                'common_names': [cn.common_name for cn in common_names]
            })
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error fetching subcat data for tab {tab_num}: {str(e)}")
        return jsonify({'error': 'Failed to fetch subcategory data'}), 500