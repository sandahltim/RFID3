from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db
from ..models.db_models import RentalClassMapping
from time import time

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/categories', methods=['GET'])
def manage_categories():
    try:
        return render_template(
            'categories.html',
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
        data = [{
            'id': m.rental_class_id,  # Changed from m.id to m.rental_class_id
            'category': m.category,
            'subcategory': m.subcategory,
            'rental_class_id': m.rental_class_id
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