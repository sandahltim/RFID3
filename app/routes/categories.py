from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db, cache
from ..models.db_models import RentalClassMapping, ItemMaster
from sqlalchemy import func, desc
from time import time

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/categories', methods=['GET'])
@cache.cached(timeout=0)  # Disable caching for this endpoint
def manage_categories():
    try:
        # Fetch all rental class mappings
        mappings = RentalClassMapping.query.order_by(RentalClassMapping.category, RentalClassMapping.rental_class_id).all()
        current_app.logger.info(f"Fetched {len(mappings)} mappings from database")
        
        # Subquery to find the most common common_name for each rental_class_num in ItemMaster
        subquery = db.session.query(
            func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).label('rental_class_num'),
            ItemMaster.common_name,
            func.count(ItemMaster.common_name).label('name_count')
        ).group_by(
            func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))), ItemMaster.common_name
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
        current_app.logger.debug(f"Common names dictionary: {common_name_dict}")

        # Prepare data for the template
        categories_data = []
        for mapping in mappings:
            # Normalize rental_class_id for matching
            normalized_rental_class_id = str(mapping.rental_class_id).strip().upper() if mapping.rental_class_id else ''
            common_name = common_name_dict.get(normalized_rental_class_id, 'N/A')
            
            # If common_name is 'N/A', try to fetch directly from ItemMaster for debugging
            if common_name == 'N/A':
                item = db.session.query(ItemMaster.common_name).filter(
                    func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))) == normalized_rental_class_id
                ).first()
                if item and item.common_name:
                    common_name = item.common_name
                    current_app.logger.info(f"Found common name {common_name} for rental_class_id {normalized_rental_class_id} via direct query")
                else:
                    current_app.logger.warning(f"No common name found for rental_class_id {normalized_rental_class_id}")

            categories_data.append({
                'rental_class_id': mapping.rental_class_id,
                'category': mapping.category,
                'subcategory': mapping.subcategory,
                'common_name': common_name
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
            func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).label('rental_class_num'),
            ItemMaster.common_name,
            func.count(ItemMaster.common_name).label('name_count')
        ).group_by(
            func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))), ItemMaster.common_name
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
        current_app.logger.debug(f"Common names dictionary (mapping): {common_name_dict}")

        data = []
        for m in mappings:
            normalized_rental_class_id = str(m.rental_class_id).strip().upper() if m.rental_class_id else ''
            common_name = common_name_dict.get(normalized_rental_class_id, 'N/A')
            
            # If common_name is 'N/A', try to fetch directly from ItemMaster for debugging
            if common_name == 'N/A':
                item = db.session.query(ItemMaster.common_name).filter(
                    func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))) == normalized_rental_class_id
                ).first()
                if item and item.common_name:
                    common_name = item.common_name
                    current_app.logger.info(f"Found common name {common_name} for rental_class_id {normalized_rental_class_id} via direct query (mapping)")
                else:
                    current_app.logger.warning(f"No common name found for rental_class_id {normalized_rental_class_id} (mapping)")

            data.append({
                'rental_class_id': m.rental_class_id,
                'category': m.category,
                'subcategory': m.subcategory,
                'common_name': common_name
            })
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

        # Deduplicate entries on the server side, keeping the last occurrence
        deduplicated_data = {}
        for item in data:
            rental_class_id = item.get('rental_class_id')
            if rental_class_id:
                deduplicated_data[rental_class_id] = item

        # Clear existing mappings
        deleted_count = RentalClassMapping.query.delete()
        current_app.logger.info(f"Deleted {deleted_count} existing mappings")

        # Add deduplicated mappings
        added_mappings = []
        for rental_class_id, item in deduplicated_data.items():
            mapping = RentalClassMapping(
                category=item.get('category'),
                subcategory=item.get('subcategory'),
                rental_class_id=rental_class_id
            )
            db.session.add(mapping)
            added_mappings.append({
                'rental_class_id': rental_class_id,
                'category': item.get('category'),
                'subcategory': item.get('subcategory')
            })

        db.session.commit()
        current_app.logger.info(f"Added {len(added_mappings)} mappings: {added_mappings}")

        # Verify the data in the database after commit
        mappings_after_commit = RentalClassMapping.query.all()
        current_app.logger.info(f"Mappings in database after commit: {len(mappings_after_commit)} entries")
        current_app.logger.debug(f"Database mappings: {[{ 'rental_class_id': m.rental_class_id, 'category': m.category, 'subcategory': m.subcategory } for m in mappings_after_commit]}")

        return jsonify({'message': 'Mappings updated successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating category mappings: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to update mappings'}), 500

@categories_bp.route('/categories/delete', methods=['POST'])
def delete_mapping():
    try:
        data = request.get_json()
        rental_class_id = data.get('rental_class_id')
        if not rental_class_id:
            return jsonify({'error': 'Rental Class ID is required'}), 400

        deleted = RentalClassMapping.query.filter_by(rental_class_id=rental_class_id).delete()
        db.session.commit()
        current_app.logger.info(f"Deleted mapping with rental_class_id {rental_class_id}, {deleted} rows affected")
        return jsonify({'message': 'Mapping deleted successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting category mapping with rental_class_id {rental_class_id}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to delete mapping'}), 500