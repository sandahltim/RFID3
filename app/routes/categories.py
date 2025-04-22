from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db
from ..models.db_models import RentalClassMapping, ItemMaster
from sqlalchemy import func, desc
from time import time

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/categories', methods=['GET'])
def manage_categories():
    try:
        # Fetch all rental class mappings
        mappings = RentalClassMapping.query.order_by(RentalClassMapping.category, RentalClassMapping.rental_class_id).all()
        
        # Subquery to find the most common common_name for each rental_class_num in ItemMaster
        subquery = db.session.query(
            ItemMaster.rental_class_num,
            ItemMaster.common_name,
            func.count(ItemMaster.common_name).label('name_count')
        ).group_by(
            ItemMaster.rental_class_num, ItemMaster.common_name
        ).subquery()

        # Main query to get the most common common_name per rental_class_num
        common_names = db.session.query(
            subquery.c.rental_class_num,
            subquery.c.common_name
        ).order_by(
            subquery.c.rental_class_num, desc(subquery.c.name_count)
        ).group_by(
            subquery.c.rental_class_num
        ).all()

        common_name_dict = {rental_class_num: common_name for rental_class_num, common_name in common_names}

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
        current_app.logger.error(f"Error rendering categories page: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to load categories page'}), 500

@categories_bp.route('/categories/mapping', methods=['GET'])
def get_mapping():
    try:
        mappings = RentalClassMapping.query.all()
        # Subquery to find the most common common_name for each rental_class_num in ItemMaster
        subquery = db.session.query(
            ItemMaster.rental_class_num,
            ItemMaster.common_name,
            func.count(ItemMaster.common_name).label('name_count')
        ).group_by(
            ItemMaster.rental_class_num, ItemMaster.common_name
        ).subquery()

        # Main query to get the most common common_name per rental_class_num
        common_names = db.session.query(
            subquery.c.rental_class_num,
            subquery.c.common_name
        ).order_by(
            subquery.c.rental_class_num, desc(subquery.c.name_count)
        ).group_by(
            subquery.c.rental_class_num
        ).all()
        
        common_name_dict = {rental_class_num: common_name for rental_class_num, common_name in common_names}

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