from flask import Blueprint, render_template, request, jsonify, current_app
from app.models.db_models import ItemMaster, RentalClassMapping
from app import db, cache
from sqlalchemy import func
import re
from time import time  # Add this import for timestamp

tabs_bp = Blueprint('tabs', __name__)

def sanitize_id(text):
    """Sanitize text for use in HTML IDs."""
    return re.sub(r'[^\w-]', '_', text.replace('"', '').replace('.', '_').lower())

@tabs_bp.route('/tab/<int:tab_num>')
@cache.cached(timeout=30)
def tab(tab_num):
    try:
        current_app.logger.info(f"Loading tab {tab_num}")
        # Fetch categories from RentalClassMapping
        category_counts = db.session.query(
            RentalClassMapping.category,
            func.count(ItemMaster.tag_id).label('item_count')
        ).join(
            ItemMaster, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
        ).group_by(
            RentalClassMapping.category
        ).order_by(
            func.count(ItemMaster.tag_id).desc(),
            RentalClassMapping.category
        ).all()
        categories = [cat[0] for cat, _ in category_counts if cat[0]]
        
        # Fetch bin locations from ItemMaster
        bin_locations_query = db.session.query(
            ItemMaster.bin_location.distinct().label('bin_location')
        ).filter(ItemMaster.bin_location.isnot(None))
        bin_locations = bin_locations_query.all()
        current_app.logger.info(f"Fetched {len(categories)} categories")
        current_app.logger.info(f"Fetched {len(bin_locations)} bin locations")
        
        # Generate a timestamp for cache-busting
        cache_bust = int(time())
        
        return render_template(
            'tab.html',
            tab_num=tab_num,
            categories=categories,
            bin_locations=[b.bin_location for b in bin_locations],
            cache_bust=cache_bust  # Pass the timestamp to the template
        )
    except Exception as e:
        current_app.logger.error(f"Error loading tab {tab_num}: {str(e)}")
        return render_template('tab.html', tab_num=tab_num, error=f"Failed to load data: {str(e)}")

@tabs_bp.route('/tab/<int:tab_num>/subcat_data', methods=['GET'])
@cache.cached(timeout=30)
def subcat_data(tab_num):
    try:
        category = request.args.get('category')
        if not category:
            return jsonify({'error': 'Category required'}), 400
        
        # Fetch subcategories with item counts
        subcategory_counts = db.session.query(
            RentalClassMapping.subcategory,
            func.count(ItemMaster.tag_id).label('item_count')
        ).join(
            ItemMaster, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
        ).filter(
            RentalClassMapping.category.ilike(category)
        ).group_by(
            RentalClassMapping.subcategory
        ).order_by(
            func.count(ItemMaster.tag_id).desc(),
            RentalClassMapping.subcategory
        ).all()
        subcategories = [sub[0] for sub, _ in subcategory_counts if sub[0]]
        
        # Fetch common names for each subcategory
        result = []
        for sub in subcategories:
            common_name_counts = db.session.query(
                ItemMaster.common_name,
                func.count(ItemMaster.tag_id).label('item_count')
            ).join(
                RentalClassMapping, ItemMaster.rental_class_num == RentalClassMapping.rental_class_id
            ).filter(
                RentalClassMapping.category.ilike(category),
                RentalClassMapping.subcategory.ilike(sub)
            ).group_by(
                ItemMaster.common_name
            ).order_by(
                func.count(ItemMaster.tag_id).desc(),
                ItemMaster.common_name
            ).all()
            common_names = [cn[0] for cn, _ in common_name_counts if cn[0]]
            result.append({
                'subcategory': sub,
                'common_names': common_names
            })
        
        current_app.logger.info(f"Fetched {len(subcategories)} subcategories for category {category}")
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error fetching subcat data for tab {tab_num}: {str(e)}")
        return jsonify({'error': 'Failed to fetch subcategory data'}), 500

@tabs_bp.route('/tab/<int:tab_num>/data', methods=['GET'])
@cache.cached(timeout=30)
def tab_data(tab_num):
    try:
        category = request.args.get('category')
        subcategory = request.args.get('subcategory')
        common_name = request.args.get('common_name')
        
        query = db.session.query(ItemMaster)
        if category and subcategory:
            query = query.join(
                RentalClassMapping, ItemMaster.rental_class_num == RentalClassMapping.rental_class_id
            ).filter(
                RentalClassMapping.category.ilike(category),
                RentalClassMapping.subcategory.ilike(subcategory)
            )
        if common_name:
            query = query.filter(ItemMaster.common_name.ilike(common_name))
        
        items = query.all()
        current_app.logger.info(f"Fetched {len(items)} items for category={category}, subcategory={subcategory}, common_name={common_name}")
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