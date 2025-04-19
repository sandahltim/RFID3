from flask import Blueprint, render_template, request, jsonify, current_app
from app.models.db_models import RentalClassMapping, SeedRentalClass
from app import db

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/categories', methods=['GET'])
def manage_categories():
    # Fetch all rental classes and their mappings
    rental_classes = db.session.query(SeedRentalClass.rental_class_id).distinct().all()
    rental_classes = [rc[0] for rc in rental_classes]
    
    mappings = RentalClassMapping.query.all()
    mapping_dict = {m.rental_class_id: {'category': m.category, 'subcategory': m.subcategory} for m in mappings}
    
    return render_template('categories.html', rental_classes=rental_classes, mappings=mapping_dict)

@categories_bp.route('/categories/update', methods=['POST'])
def update_category():
    try:
        rental_class_id = request.form.get('rental_class_id')
        category = request.form.get('category')
        subcategory = request.form.get('subcategory')
        
        if not all([rental_class_id, category, subcategory]):
            return jsonify({'status': 'error', 'message': 'All fields are required'}), 400
        
        mapping = RentalClassMapping.query.get(rental_class_id)
        if mapping:
            mapping.category = category
            mapping.subcategory = subcategory
        else:
            mapping = RentalClassMapping(
                rental_class_id=rental_class_id,
                category=category,
                subcategory=subcategory
            )
            db.session.add(mapping)
        
        db.session.commit()
        current_app.logger.info(f"Updated mapping for rental_class_id {rental_class_id}: {category}/{subcategory}")
        return jsonify({'status': 'success', 'message': 'Mapping updated'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating category mapping: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500