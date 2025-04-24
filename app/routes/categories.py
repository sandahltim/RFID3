from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db
from ..models.db_models import ItemMaster, RentalClassMapping, UserRentalClassMapping
from sqlalchemy import func, text
from time import time

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/categories')
def manage_categories():
    try:
        session = db.session()
        current_app.logger.info("Starting new session for manage_categories")

        # Fetch all rental class mappings from both tables
        base_mappings = session.query(RentalClassMapping).all()
        user_mappings = session.query(UserRentalClassMapping).all()

        # Merge mappings, prioritizing user mappings
        mappings_dict = {m.rental_class_id: {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[um.rental_class_id] = {'category': um.category, 'subcategory': um.subcategory}

        # Fetch common names for each rental class ID
        categories = []
        rental_class_ids = list(mappings_dict.keys())
        common_names_query = session.query(
            func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).label('rental_class_num'),
            ItemMaster.common_name
        ).filter(
            func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids)
        ).distinct().all()

        common_name_dict = {str(rental_class_num).strip().upper(): common_name for rental_class_num, common_name in common_names_query}

        for rental_class_id, mapping in mappings_dict.items():
            normalized_rental_class_id = str(rental_class_id).strip().upper()
            common_name = common_name_dict.get(normalized_rental_class_id, 'N/A')
            if common_name == 'N/A':
                current_app.logger.warning(f"No common name found for rental_class_id {normalized_rental_class_id}")
            categories.append({
                'category': mapping['category'],
                'subcategory': mapping['subcategory'],
                'rental_class_id': rental_class_id,
                'common_name': common_name
            })

        categories.sort(key=lambda x: (x['category'], x['subcategory'], x['rental_class_id']))
        current_app.logger.info(f"Fetched {len(categories)} category mappings")

        # Direct query to verify database state
        raw_base_mappings = session.execute(text("SELECT rental_class_id, category, subcategory FROM rental_class_mappings")).fetchall()
        raw_user_mappings = session.execute(text("SELECT rental_class_id, category, subcategory FROM user_rental_class_mappings")).fetchall()
        current_app.logger.info(f"Raw base mappings: {[(row[0], row[1], row[2]) for row in raw_base_mappings]}")
        current_app.logger.info(f"Raw user mappings: {[(row[0], row[1], row[2]) for row in raw_user_mappings]}")

        session.close()
        return render_template('categories.html', categories=categories, cache_bust=int(time()))
    except Exception as e:
        current_app.logger.error(f"Error rendering categories page: {str(e)}", exc_info=True)
        if 'session' in locals():
            session.close()
        return render_template('categories.html', categories=[])

@categories_bp.route('/categories/mapping', methods=['GET'])
def get_mappings():
    try:
        session = db.session()
        current_app.logger.info("Fetching rental class mappings for API")

        # Fetch all rental class mappings
        base_mappings = session.query(RentalClassMapping).all()
        user_mappings = session.query(UserRentalClassMapping).all()

        # Merge mappings, prioritizing user mappings
        mappings_dict = {m.rental_class_id: {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[um.rental_class_id] = {'category': um.category, 'subcategory': um.subcategory}

        # Fetch common names
        categories = []
        rental_class_ids = list(mappings_dict.keys())
        common_names_query = session.query(
            func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).label('rental_class_num'),
            ItemMaster.common_name
        ).filter(
            func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids)
        ).distinct().all()

        common_name_dict = {str(rental_class_num).strip().upper(): common_name for rental_class_num, common_name in common_names_query}

        for rental_class_id, mapping in mappings_dict.items():
            normalized_rental_class_id = str(rental_class_id).strip().upper()
            common_name = common_name_dict.get(normalized_rental_class_id, 'N/A')
            if common_name == 'N/A':
                current_app.logger.warning(f"No common name found for rental_class_id {normalized_rental_class_id} (mapping)")
            categories.append({
                'category': mapping['category'],
                'subcategory': mapping['subcategory'],
                'rental_class_id': rental_class_id,
                'common_name': common_name
            })

        categories.sort(key=lambda x: (x['category'], x['subcategory'], x['rental_class_id']))
        session.close()
        return jsonify(categories)
    except Exception as e:
        current_app.logger.error(f"Error fetching mappings: {str(e)}")
        if 'session' in locals():
            session.close()
        return jsonify({'error': 'Failed to fetch mappings'}), 500

@categories_bp.route('/categories/update', methods=['POST'])
def update_mappings():
    try:
        # Start a new session for this request
        session = db.session()
        current_app.logger.info("Starting new session for update_mappings")

        # Get the new mappings from the request
        new_mappings = request.get_json()
        current_app.logger.debug(f"Received new mappings: {new_mappings}")

        if not isinstance(new_mappings, list):
            session.close()
            return jsonify({'error': 'Invalid data format, expected a list'}), 400

        # Clear existing user mappings
        deleted_count = session.query(UserRentalClassMapping).delete()
        current_app.logger.info(f"Deleted {deleted_count} existing user mappings")

        # Add new user mappings
        for mapping in new_mappings:
            rental_class_id = mapping.get('rental_class_id')
            category = mapping.get('category')
            subcategory = mapping.get('subcategory', '')

            if not rental_class_id or not category:
                current_app.logger.warning(f"Skipping invalid mapping: {mapping}")
                continue

            user_mapping = UserRentalClassMapping(
                rental_class_id=rental_class_id,
                category=category,
                subcategory=subcategory
            )
            session.add(user_mapping)
            current_app.logger.debug(f"Added mapping: rental_class_id={rental_class_id}, category={category}, subcategory={subcategory}")

        # Commit the changes
        session.commit()
        current_app.logger.info("Successfully committed rental class mappings")

        # Verify the mappings were saved
        saved_mappings = session.query(UserRentalClassMapping).all()
        current_app.logger.info(f"Saved mappings after commit: {[(m.rental_class_id, m.category, m.subcategory) for m in saved_mappings]}")

        # Direct query to verify database state
        raw_user_mappings = session.execute(text("SELECT rental_class_id, category, subcategory FROM user_rental_class_mappings")).fetchall()
        current_app.logger.info(f"Raw user mappings after commit: {[(row[0], row[1], row[2]) for row in raw_user_mappings]}")

        session.close()
        return jsonify({'message': 'Mappings updated successfully'})
    except Exception as e:
        current_app.logger.error(f"Error updating mappings: {str(e)}", exc_info=True)
        if 'session' in locals():
            session.rollback()
            session.close()
        return jsonify({'error': 'Failed to update mappings'}), 500

@categories_bp.route('/categories/delete', methods=['POST'])
def delete_mapping():
    try:
        session = db.session()
        data = request.get_json()
        rental_class_id = data.get('rental_class_id')

        if not rental_class_id:
            current_app.logger.error("Missing rental_class_id in delete request")
            session.close()
            return jsonify({'error': 'Rental class ID is required'}), 400

        current_app.logger.info(f"Deleting mapping for rental_class_id: {rental_class_id}")
        deleted_count = session.query(UserRentalClassMapping).filter_by(rental_class_id=rental_class_id).delete()
        session.commit()
        current_app.logger.info(f"Deleted {deleted_count} user mappings for rental_class_id: {rental_class_id}")

        # Verify the deletion
        remaining_mappings = session.query(UserRentalClassMapping).all()
        current_app.logger.info(f"Remaining user mappings after deletion: {[(m.rental_class_id, m.category, m.subcategory) for m in remaining_mappings]}")

        session.close()
        return jsonify({'message': 'Mapping deleted successfully'})
    except Exception as e:
        current_app.logger.error(f"Error deleting mapping: {str(e)}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return jsonify({'error': 'Failed to delete mapping'}), 500