from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db, cache
from ..models.db_models import RentalClassMapping, UserRentalClassMapping
from ..services.api_client import APIClient
from sqlalchemy import func, text
from sqlalchemy.exc import SQLAlchemyError
from time import time
import logging

# Ensure logs go to both file and console
logger = logging.getLogger('categories')
if not logger.handlers:
    logger.setLevel(logging.DEBUG)
    file_handler = logging.FileHandler('/home/tim/test_rfidpi/logs/rfid_dashboard.log')
    file_handler.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/categories')
def manage_categories():
    logger.info("TEST: Entering manage_categories endpoint")
    try:
        session = db.session()
        logger.info("Starting new session for manage_categories")

        # Fetch all rental class mappings from both tables
        base_mappings = session.query(RentalClassMapping).all()
        user_mappings = session.query(UserRentalClassMapping).all()

        # Merge mappings, prioritizing user mappings
        mappings_dict = {m.rental_class_id: {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[um.rental_class_id] = {'category': um.category, 'subcategory': um.subcategory}

        # Fetch seed data from cache or API
        cache_key = 'seed_rental_classes'
        seed_data = cache.get(cache_key)
        common_name_dict = {}
        if seed_data is None:
            try:
                api_client = APIClient()
                seed_data = api_client.get_seed_data()
                # Check if response is nested under 'data' key
                if isinstance(seed_data, dict) and 'data' in seed_data:
                    logger.debug("API response contains 'data' key, extracting nested data")
                    seed_data = seed_data['data']
                logger.debug(f"Seed data fetched from API (first 5 items): {seed_data[:5] if seed_data else 'Empty'}")
                cache.set(cache_key, seed_data, timeout=3600)  # Cache for 1 hour
                logger.info("Fetched seed data from API and cached")
            except Exception as api_error:
                logger.error(f"Failed to fetch seed data from API: {str(api_error)}", exc_info=True)
                seed_data = []  # Fallback to empty list
        else:
            logger.info("Using cached seed data")
            logger.debug(f"Cached seed data (first 5 items): {seed_data[:5] if seed_data else 'Empty'}")

        # Create a mapping of rental_class_id to common_name
        try:
            common_name_dict = {
                str(item['rental_class_id']).strip().upper(): item['common_name']
                for item in seed_data
                if 'rental_class_id' in item and 'common_name' in item
            }
            logger.debug(f"Created common_name_dict with {len(common_name_dict)} entries")
            # Log a sample of common_name_dict to verify contents
            sample_common_names = dict(list(common_name_dict.items())[:5])
            logger.debug(f"Sample of common_name_dict: {sample_common_names}")
        except Exception as dict_error:
            logger.error(f"Error creating common_name_dict from seed_data: {str(dict_error)}", exc_info=True)
            common_name_dict = {}

        # Build categories list
        categories = []
        # Log a sample of rental_class_ids from mappings_dict for comparison
        sample_rental_class_ids = list(mappings_dict.keys())[:5]
        logger.debug(f"Sample rental_class_ids from mappings: {sample_rental_class_ids}")
        for rental_class_id, mapping in mappings_dict.items():
            normalized_rental_class_id = str(rental_class_id).strip().upper()
            common_name = common_name_dict.get(normalized_rental_class_id, 'N/A')
            if common_name == 'N/A':
                logger.warning(f"No common name found for rental_class_id {normalized_rental_class_id}")
            categories.append({
                'category': mapping['category'],
                'subcategory': mapping['subcategory'],
                'rental_class_id': rental_class_id,
                'common_name': common_name
            })

        categories.sort(key=lambda x: (x['category'], x['subcategory'], x['rental_class_id']))
        logger.info(f"Fetched {len(categories)} category mappings")

        # Direct query to verify database state
        raw_base_mappings = session.execute(text("SELECT rental_class_id, category, subcategory FROM rental_class_mappings")).fetchall()
        raw_user_mappings = session.execute(text("SELECT rental_class_id, category, subcategory FROM user_rental_class_mappings")).fetchall()
        logger.info(f"Raw base mappings: {[(row[0], row[1], row[2]) for row in raw_base_mappings]}")
        logger.info(f"Raw user mappings: {[(row[0], row[1], row[2]) for row in raw_user_mappings]}")

        session.close()
        return render_template('categories.html', categories=categories, cache_bust=int(time()))
    except Exception as e:
        logger.error(f"Error rendering categories page: {str(e)}", exc_info=True)
        if 'session' in locals():
            session.close()
        return render_template('categories.html', categories=[])

@categories_bp.route('/categories/mapping', methods=['GET'])
def get_mappings():
    logger.info("TEST: Entering get_mappings endpoint")
    try:
        session = db.session()
        logger.info("Fetching rental class mappings for API")

        # Fetch all rental class mappings
        base_mappings = session.query(RentalClassMapping).all()
        user_mappings = session.query(UserRentalClassMapping).all()

        # Merge mappings, prioritizing user mappings
        mappings_dict = {m.rental_class_id: {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[um.rental_class_id] = {'category': um.category, 'subcategory': um.subcategory}

        # Fetch seed data from cache or API
        cache_key = 'seed_rental_classes'
        # Temporarily clear cache to force a fresh API call for debugging
        cache.delete(cache_key)
        logger.info("Cleared seed_rental_classes cache to force fresh API call")
        seed_data = cache.get(cache_key)
        common_name_dict = {}
        if seed_data is None:
            try:
                api_client = APIClient()
                seed_data = api_client.get_seed_data()
                # Check if response is nested under 'data' key
                if isinstance(seed_data, dict) and 'data' in seed_data:
                    logger.debug("API response contains 'data' key, extracting nested data")
                    seed_data = seed_data['data']
                logger.debug(f"Seed data fetched from API (first 5 items): {seed_data[:5] if seed_data else 'Empty'}")
                cache.set(cache_key, seed_data, timeout=3600)  # Cache for 1 hour
                logger.info("Fetched seed data from API and cached")
            except Exception as api_error:
                logger.error(f"Failed to fetch seed data from API: {str(api_error)}", exc_info=True)
                seed_data = []  # Fallback to empty list
        else:
            logger.info("Using cached seed data")
            logger.debug(f"Cached seed data (first 5 items): {seed_data[:5] if seed_data else 'Empty'}")

        # Create a mapping of rental_class_id to common_name
        try:
            common_name_dict = {
                str(item['rental_class_id']).strip().upper(): item['common_name']
                for item in seed_data
                if 'rental_class_id' in item and 'common_name' in item
            }
            logger.debug(f"Created common_name_dict with {len(common_name_dict)} entries")
            # Log a sample of common_name_dict to verify contents
            sample_common_names = dict(list(common_name_dict.items())[:5])
            logger.debug(f"Sample of common_name_dict: {sample_common_names}")
        except Exception as dict_error:
            logger.error(f"Error creating common_name_dict from seed_data: {str(dict_error)}", exc_info=True)
            common_name_dict = {}

        # Build categories list
        categories = []
        # Log a sample of rental_class_ids from mappings_dict for comparison
        sample_rental_class_ids = list(mappings_dict.keys())[:5]
        logger.debug(f"Sample rental_class_ids from mappings: {sample_rental_class_ids}")
        for rental_class_id, mapping in mappings_dict.items():
            normalized_rental_class_id = str(rental_class_id).strip().upper()
            common_name = common_name_dict.get(normalized_rental_class_id, 'N/A')
            if common_name == 'N/A':
                logger.warning(f"No common name found for rental_class_id {normalized_rental_class_id} (mapping)")
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
        logger.error(f"Error fetching mappings: {str(e)}")
        if 'session' in locals():
            session.close()
        return jsonify({'error': 'Failed to fetch mappings'}), 500

@categories_bp.route('/categories/update', methods=['POST'])
def update_mappings():
    session = None
    try:
        # Start a new session for this request
        session = db.session()
        logger.info("Starting new session for update_mappings")

        # Get the new mappings from the request
        new_mappings = request.get_json()
        logger.info(f"Received {len(new_mappings)} new mappings: {new_mappings}")

        if not isinstance(new_mappings, list):
            logger.error("Invalid data format received, expected a list")
            return jsonify({'error': 'Invalid data format, expected a list'}), 400

        # Clear existing user mappings
        deleted_count = session.query(UserRentalClassMapping).delete()
        logger.info(f"Deleted {deleted_count} existing user mappings")

        # Add new user mappings
        for mapping in new_mappings:
            rental_class_id = mapping.get('rental_class_id')
            category = mapping.get('category')
            subcategory = mapping.get('subcategory', '')

            if not rental_class_id or not category:
                logger.warning(f"Skipping invalid mapping due to missing rental_class_id or category: {mapping}")
                continue

            user_mapping = UserRentalClassMapping(
                rental_class_id=rental_class_id,
                category=category,
                subcategory=subcategory or ''
            )
            session.add(user_mapping)
            logger.debug(f"Added mapping: rental_class_id={rental_class_id}, category={category}, subcategory={subcategory}")

        # Commit the changes
        session.commit()
        logger.info("Successfully committed rental class mappings")

        # Verify the mappings were saved
        saved_mappings = session.query(UserRentalClassMapping).all()
        logger.info(f"Saved mappings after commit: {[(m.rental_class_id, m.category, m.subcategory) for m in saved_mappings]}")

        # Direct query to verify database state
        raw_user_mappings = session.execute(text("SELECT rental_class_id, category, subcategory FROM user_rental_class_mappings")).fetchall()
        logger.info(f"Raw user mappings after commit: {[(row[0], row[1], row[2]) for row in raw_user_mappings]}")

        return jsonify({'message': 'Mappings updated successfully'})
    except SQLAlchemyError as e:
        logger.error(f"Database error during update_mappings: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Unexpected error during update_mappings: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
    finally:
        if session:
            session.close()
            logger.info("Database session closed for update_mappings")

@categories_bp.route('/categories/delete', methods=['POST'])
def delete_mapping():
    session = None
    try:
        session = db.session()
        data = request.get_json()
        rental_class_id = data.get('rental_class_id')

        if not rental_class_id:
            logger.error("Missing rental_class_id in delete request")
            return jsonify({'error': 'Rental class ID is required'}), 400

        logger.info(f"Deleting mapping for rental_class_id: {rental_class_id}")
        deleted_count = session.query(UserRentalClassMapping).filter_by(rental_class_id=rental_class_id).delete()
        session.commit()
        logger.info(f"Deleted {deleted_count} user mappings for rental_class_id: {rental_class_id}")

        # Verify the deletion
        remaining_mappings = session.query(UserRentalClassMapping).all()
        logger.info(f"Remaining user mappings after deletion: {[(m.rental_class_id, m.category, m.subcategory) for m in remaining_mappings]}")

        return jsonify({'message': 'Mapping deleted successfully'})
    except SQLAlchemyError as e:
        logger.error(f"Database error during delete_mapping: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Unexpected error during delete_mapping: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
    finally:
        if session:
            session.close()
            logger.info("Database session closed for delete_mapping")