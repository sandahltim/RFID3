from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db
from ..models.db_models import RentalClassMapping, ItemMaster
from sqlalchemy import func
from time import time

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/categories', methods=['GET'])
def manage_categories():
    try:
        # Fetch all rental class mappings
        mappings = RentalClassMapping.query.order_by(RentalClassMapping.category, RentalClassMapping.rental_class_id).all()
        
        # Fetch the most common 'common_name' for each rental_class_id from ItemMaster
        common_names = db.session.query(
            RentalClassMapping.rental_class_id,
            func.mode().within_group(ItemMaster.common_name).label('common_name')
        ).outerjoin(
            ItemMaster, ItemMaster.rental_class_num == RentalClassMapping.rental_class_id
        ).group_by(
            RentalClassMapping.rental_class_id
        ).all()
        
        common_name_dict = {rental_class_id: common_name for rental_class_id, common_name in common_names}

        # Prepare data for the template
        categories_data = []
        for mapping in mappings:
            categories_data.append({
                'id': mapping.id,
                'rental_class_id': mapping.rental_class_id,
                'category': mapping.category,
                'subcategory': mapping.subcategory,
                'common_name': common_name_dict.get(mapping.rental_class_id, 'N/A')
            })

        current_app.logger.info(f"Fetched {len(categories_data)} category mappings")
        current_app.logger.debug(f"Categories data: {categories_data}")

        return render_template(
            'categories.html',
            categories=categories_data,
            cache_bust=int(time()),
            timestamp=lambda: int(time())
        )
    except Exception as e:
        current_app.logger.error(f"Error rendering categories page: {str(e)}")
        return jsonify({'error': 'Failed to load categories page'}), 500

@categories_bp.route('/categories/mapping', methods=['GET'])
def get_mapping():
    try:
        mappings = RentalClassMapping.query.all()
        # Fetch the most common 'common_name' for each rental_class_id from ItemMaster
        common_names = db.session.query(
            RentalClassMapping.rental_class_id,
            func.mode().within_group(ItemMaster.common_name).label('common_name')
        ).outerjoin(
            ItemMaster, ItemMaster.rental_class_num == RentalClassMapping.rental_class_id
        ).group_by(
            RentalClassMapping.rental_class_id
        ).all()
        
        common_name_dict = {rental_class_id: common_name for rental_class_id, common_name in common_names}

        data = [{
            'id': m.id,  # Use m.id since we're rendering rows dynamically
            'category': m.category,
            'subcategory': m.subcategory,
            'rental_class_id': m.rental_class_id,
            'common_name': common_name_dict.get(m.rental_class_id, 'N/A')
        } for m in mappings]
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Error fetching category mappings: {str(e)}")
        return jsonify({'error': 'Failed to fetch mappings'}), 500

@categories_bp.route('/categories/update', methods=['POST'])
def update_mapping():
    try:
        data = request.get_json()
        if not isinstance(data, list):
            return jsonify({'error': 'Invalid data format'}), 400

        # Clear existing mappings
        RentalClassMapping.query.delete()

        # Add new mappings
        for item in data:
            mapping = RentalClassMapping(
                category=item.get('category'),
                subcategory=item.get('subcategory'),
                rental_class_id=item.get('rental_class_id')
            )
            db.session.add(mapping)

        db.session.commit()
        return jsonify({'message': 'Mappings updated successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating category mappings: {str(e)}")
        return jsonify({'error': 'Failed to update mappings'}), 500