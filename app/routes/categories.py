# app/routes/categories.py
# categories.py version: 2025-06-20-v24
from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db, cache
from ..models.db_models import RentalClassMapping, UserRentalClassMapping, SeedRentalClass
from ..services.api_client import APIClient
from sqlalchemy.exc import SQLAlchemyError
from time import time
import logging
import sys
import copy

# Configure logging
logger = logging.getLogger('categories')
logger.setLevel(logging.INFO)

# Remove existing handlers to avoid duplicates
logger.handlers = []

# File handler for rfid_dashboard.log
file_handler = logging.FileHandler('/home/tim/test_rfidpi/logs/rfid_dashboard.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Secondary file handler for debug.log
debug_handler = logging.FileHandler('/home/tim/test_rfidpi/logs/debug.log')
debug_handler.setLevel(logging.INFO)
debug_handler.setFormatter(formatter)
logger.addHandler(debug_handler)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Also add logs to the root logger (which Gunicorn might capture)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
    root_logger.addHandler(console_handler)

categories_bp = Blueprint('categories', __name__)

# Version check to ensure correct deployment
logger.info("Deployed categories.py version: 2025-06-20-v24")

def build_common_name_dict(seed_data):
    """Build a dictionary mapping rental_class_id to common_name from seed_data."""
    common_name_dict = {}
    if not seed_data:
        logger.warning("Seed data is empty or None")
        return common_name_dict
    for item in seed_data:
        try:
            rental_class_id = item.get('rental_class_id')
            common_name = item.get('common_name', 'Unknown')
            bin_location = item.get('bin_location')
            if rental_class_id:
                normalized_key = str(rental_class_id).strip()
                common_name_dict[normalized_key] = common_name
                logger.debug(f"Seed item - rental_class_id: {normalized_key}, common_name: {common_name}, bin_location: {bin_location}")
            else:
                logger.debug(f"Skipping item due to missing rental_class_id: {item}")
        except Exception as comp_error:
            logger.error(f"Error processing item for common_name_dict: {str(comp_error)}", exc_info=True)
            current_app.logger.error(f"Error processing item for common_name_dict: {str(comp_error)}", exc_info=True)
    logger.info(f"Built common_name_dict with {len(common_name_dict)} entries")
    return common_name_dict

@categories_bp.route('/categories')
def manage_categories():
    session = None
    try:
        session = db.session()
        logger.info("Starting new session for manage_categories")
        current_app.logger.info("Starting new session for manage_categories")

        # Fetch all rental class mappings from both tables
        logger.debug("Fetching rental class mappings")
        try:
            base_mappings = session.query(RentalClassMapping).all()
            logger.info(f"Fetched {len(base_mappings)} base mappings from RentalClassMapping")
        except Exception as db_error:
            logger.error(f"Failed to fetch base_mappings from RentalClassMapping: {str(db_error)}", exc_info=True)
            current_app.logger.error(f"Failed to fetch base_mappings from RentalClassMapping: {str(db_error)}", exc_info=True)
            base_mappings = []

        try:
            user_mappings = session.query(UserRentalClassMapping).all()
            logger.info(f"Fetched {len(user_mappings)} user mappings from UserRentalClassMapping")
        except Exception as db_error:
            logger.error(f"Failed to fetch user_mappings from UserRentalClassMapping: {str(db_error)}", exc_info=True)
            current_app.logger.error(f"Failed to fetch user_mappings from UserRentalClassMapping: {str(db_error)}", exc_info=True)
            user_mappings = []

        # Merge mappings, prioritizing user mappings
        mappings_dict = {
            m.rental_class_id: {
                'category': m.category,
                'subcategory': m.subcategory,
                'short_common_name': m.short_common_name or 'N/A'
            } for m in base_mappings
        }
        for um in user_mappings:
            mappings_dict[um.rental_class_id] = {
                'category': um.category,
                'subcategory': um.subcategory,
                'short_common_name': um.short_common_name or 'N/A'
            }
        logger.debug(f"Merged mappings into dictionary with {len(mappings_dict)} entries")

        # Fetch seed data from cache or database
        cache_key = 'seed_rental_classes'
        logger.debug(f"Checking cache for key: {cache_key}")
        try:
            seed_data = cache.get(cache_key)
        except Exception as cache_error:
            logger.error(f"Cache error for key {cache_key}: {str(cache_error)}. Bypassing cache.", exc_info=True)
            current_app.logger.error(f"Cache error for key {cache_key}: {str(cache_error)}. Bypassing cache.", exc_info=True)
            seed_data = None

        if seed_data is None:
            logger.info("Seed data not found in cache or cache failed, fetching from database")
            try:
                seed_data = session.query(SeedRentalClass).all()
                seed_data = [{'rental_class_id': s.rental_class_id, 'common_name': s.common_name or 'Unknown', 'bin_location': s.bin_location} for s in seed_data]
                logger.info(f"Fetched {len(seed_data)} seed data records from database")
            except Exception as db_error:
                logger.error(f"Failed to fetch seed data from database: {str(db_error)}", exc_info=True)
                current_app.logger.error(f"Failed to fetch seed data from database: {str(db_error)}", exc_info=True)
                seed_data = []

            # Fallback to API if database is empty
            if not seed_data:
                logger.info("No seed data in database, fetching from API")
                try:
                    api_client = APIClient()
                    seed_data = api_client.get_seed_data()
                    if isinstance(seed_data, dict) and 'data' in seed_data:
                        seed_data = seed_data['data']
                    logger.debug(f"Fetched seed data from API: {len(seed_data)} records")
                except Exception as api_error:
                    logger.error(f"Failed to fetch seed data from API: {str(api_error)}", exc_info=True)
                    current_app.logger.error(f"Failed to fetch seed data from API: {str(api_error)}", exc_info=True)
                    seed_data = []

        # Create a mapping of rental_class_id to common_name
        try:
            common_name_dict = build_common_name_dict(seed_data)
        except Exception as dict_error:
            logger.error(f"Error creating common_name_dict from seed_data: {str(dict_error)}", exc_info=True)
            current_app.logger.error(f"Error creating common_name_dict from seed_data: {str(dict_error)}", exc_info=True)
            common_name_dict = {}

        # Build categories list
        categories = []
        for rental_class_id, mapping in mappings_dict.items():
            normalized_rental_class_id = str(rental_class_id).strip()
            common_name = common_name_dict.get(normalized_rental_class_id, 'N/A')
            categories.append({
                'category': mapping['category'],
                'subcategory': mapping['subcategory'],
                'rental_class_id': rental_class_id,
                'common_name': common_name,
                'short_common_name': mapping['short_common_name']
            })
        logger.debug(f"Built categories list with {len(categories)} entries")

        # Cache the seed_data after lookup
        if seed_data:
            try:
                seed_data_copy = copy.deepcopy(seed_data)
                cache.set(cache_key, seed_data_copy, ex=3600)  # Cache for 1 hour
                logger.info("Fetched seed data and cached")
                current_app.logger.info("Fetched seed data and cached")
            except Exception as cache_error:
                logger.error(f"Error caching seed data: {str(cache_error)}. Data will be fetched on next request.", exc_info=True)
                current_app.logger.error(f"Error caching seed data: {str(cache_error)}. Data will be fetched on next request.", exc_info=True)

        categories.sort(key=lambda x: (x['category'] or '', x['subcategory'] or '', x['rental_class_id'] or ''))
        logger.info(f"Fetched {len(categories)} category mappings")
        current_app.logger.info(f"Fetched {len(categories)} category mappings")

        session.close()
        return render_template('categories.html', categories=categories, cache_bust=int(time()))
    except Exception as e:
        logger.error(f"Error rendering categories page: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error rendering categories page: {str(e)}", exc_info=True)
        if 'session' in locals():
            session.close()
        return render_template('categories.html', categories=[])

@categories_bp.route('/categories/mapping', methods=['GET'])
def get_mappings():
    session = None
    try:
        session = db.session()
        logger.info("Fetching rental class mappings for API")
        current_app.logger.info("Fetching rental class mappings for API")

        # Fetch all rental class mappings
        logger.debug("Querying rental_class_mappings")
        try:
            base_mappings = session.query(RentalClassMapping).all()
            logger.info(f"Fetched {len(base_mappings)} base mappings from RentalClassMapping")
        except Exception as db_error:
            logger.error(f"Failed to fetch base_mappings from RentalClassMapping: {str(db_error)}", exc_info=True)
            current_app.logger.error(f"Failed to fetch base_mappings from RentalClassMapping: {str(db_error)}", exc_info=True)
            base_mappings = []

        logger.debug("Querying user_rental_class_mappings")
        try:
            user_mappings = session.query(UserRentalClassMapping).all()
            logger.info(f"Fetched {len(user_mappings)} user mappings from UserRentalClassMapping")
        except Exception as db_error:
            logger.error(f"Failed to fetch user_mappings from UserRentalClassMapping: {str(db_error)}", exc_info=True)
            current_app.logger.error(f"Failed to fetch user_mappings from UserRentalClassMapping: {str(db_error)}", exc_info=True)
            user_mappings = []

        # Merge mappings, prioritizing user mappings
        mappings_dict = {
            m.rental_class_id: {
                'category': m.category,
                'subcategory': m.subcategory,
                'short_common_name': m.short_common_name or 'N/A'
            } for m in base_mappings
        }
        for um in user_mappings:
            mappings_dict[um.rental_class_id] = {
                'category': um.category,
                'subcategory': um.subcategory,
                'short_common_name': um.short_common_name or 'N/A'
            }
        logger.debug(f"Merged mappings into dictionary with {len(mappings_dict)} entries")

        # Fetch seed data from cache or database
        cache_key = 'seed_rental_classes'
        logger.debug(f"Checking cache for key: {cache_key}")
        try:
            seed_data = cache.get(cache_key)
        except Exception as cache_error:
            logger.error(f"Cache error for key {cache_key}: {str(cache_error)}. Bypassing cache.", exc_info=True)
            current_app.logger.error(f"Cache error for key {cache_key}: {str(cache_error)}. Bypassing cache.", exc_info=True)
            seed_data = None

        if seed_data is None:
            logger.info("Seed data not found in cache or cache failed, fetching from database")
            try:
                seed_data = session.query(SeedRentalClass).all()
                seed_data = [{'rental_class_id': s.rental_class_id, 'common_name': s.common_name or 'Unknown', 'bin_location': s.bin_location} for s in seed_data]
                logger.info(f"Fetched {len(seed_data)} seed data records from database")
            except Exception as db_error:
                logger.error(f"Failed to fetch seed data from database: {str(db_error)}", exc_info=True)
                current_app.logger.error(f"Failed to fetch seed data from database: {str(db_error)}", exc_info=True)
                seed_data = []

            # Fallback to API if database is empty
            if not seed_data:
                logger.info("No seed data in database, fetching from API")
                try:
                    api_client = APIClient()
                    seed_data = api_client.get_seed_data()
                    if isinstance(seed_data, dict) and 'data' in seed_data:
                        seed_data = seed_data['data']
                    logger.debug(f"Fetched seed data from API: {len(seed_data)} records")
                except Exception as api_error:
                    logger.error(f"Failed to fetch seed data from API: {str(api_error)}", exc_info=True)
                    current_app.logger.error(f"Failed to fetch seed data from API: {str(api_error)}", exc_info=True)
                    seed_data = []

        # Create a mapping of rental_class_id to common_name
        try:
            common_name_dict = build_common_name_dict(seed_data)
        except Exception as dict_error:
            logger.error(f"Error creating common_name_dict from seed_data: {str(dict_error)}", exc_info=True)
            current_app.logger.error(f"Error creating common_name_dict from seed_data: {str(dict_error)}", exc_info=True)
            common_name_dict = {}

        # Build categories list
        categories = []
        for rental_class_id, mapping in mappings_dict.items():
            normalized_rental_class_id = str(rental_class_id).strip()
            common_name = common_name_dict.get(normalized_rental_class_id, 'N/A')
            categories.append({
                'category': mapping['category'],
                'subcategory': mapping['subcategory'],
                'rental_class_id': rental_class_id,
                'common_name': common_name,
                'short_common_name': mapping['short_common_name']
            })
        logger.debug(f"Built categories list with {len(categories)} entries")

        # Cache the seed_data after lookup
        if seed_data:
            try:
                seed_data_copy = copy.deepcopy(seed_data)
                cache.set(cache_key, seed_data_copy, ex=3600)  # Cache for 1 hour
                logger.info("Fetched seed data and cached")
                current_app.logger.info("Fetched seed data and cached")
            except Exception as cache_error:
                logger.error(f"Error caching seed_data: {str(cache_error)}. Data will be fetched on next request.", exc_info=True)
                current_app.logger.error(f"Error caching seed_data: {str(cache_error)}. Data will be fetched on next request.", exc_info=True)

        categories.sort(key=lambda x: (x['category'] or '', x['subcategory'] or '', x['rental_class_id'] or ''))
        logger.info(f"Returning {len(categories)} category mappings")
        session.close()
        return jsonify(categories)
    except Exception as e:
        logger.error(f"Error fetching mappings: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error fetching mappings: {str(e)}", exc_info=True)
        if 'session' in locals():
            session.close()
        return jsonify({'error': f'Failed to fetch mappings: {str(e)}'}), 500

@categories_bp.route('/categories/update', methods=['POST'])
def update_mappings():
    session = None
    try:
        session = db.session()
        logger.info("Starting new session for update_mappings")
        current_app.logger.info("Starting new session for update_mappings")

        new_mappings = request.get_json()
        logger.info(f"Received {len(new_mappings)} new mappings")
        current_app.logger.info(f"Received {len(new_mappings)} new mappings")

        if not isinstance(new_mappings, list):
            logger.error("Invalid data format received, expected a list")
            current_app.logger.error("Invalid data format received, expected a list")
            return jsonify({'error': 'Invalid data format, expected a list'}), 400

        # Clear existing user mappings
        logger.debug("Deleting existing user mappings")
        deleted_count = session.query(UserRentalClassMapping).delete()
        logger.info(f"Deleted {deleted_count} existing user mappings")
        current_app.logger.info(f"Deleted {deleted_count} existing user mappings")

        # Add new user mappings
        for mapping in new_mappings:
            rental_class_id = mapping.get('rental_class_id')
            category = mapping.get('category')
            subcategory = mapping.get('subcategory', '')
            short_common_name = mapping.get('short_common_name', '')

            if not rental_class_id or not category:
                logger.warning(f"Skipping invalid mapping due to missing rental_class_id or category: {mapping}")
                current_app.logger.warning(f"Skipping invalid mapping due to missing rental_class_id or category: {mapping}")
                continue

            user_mapping = UserRentalClassMapping(
                rental_class_id=rental_class_id,
                category=category,
                subcategory=subcategory or '',
                short_common_name=short_common_name or ''
            )
            session.add(user_mapping)

        session.commit()
        logger.info("Successfully committed rental class mappings")
        current_app.logger.info("Successfully committed rental class mappings")

        return jsonify({'message': 'Mappings updated successfully'})
    except SQLAlchemyError as e:
        logger.error(f"Database error during update_mappings: {str(e)}", exc_info=True)
        current_app.logger.error(f"Database error during update_mappings: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Unexpected error during update_mappings: {str(e)}", exc_info=True)
        current_app.logger.error(f"Unexpected error during update_mappings: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
    finally:
        if session:
            session.close()
            logger.info("Database session closed for update_mappings")
            current_app.logger.info("Database session closed for update_mappings")

@categories_bp.route('/categories/delete', methods=['POST'])
def delete_mapping():
    session = None
    try:
        session = db.session()
        data = request.get_json()
        rental_class_id = data.get('rental_class_id')

        if not rental_class_id:
            logger.error("Missing rental_class_id in delete request")
            current_app.logger.error("Missing rental_class_id in delete request")
            return jsonify({'error': 'Rental class ID is required'}), 400

        logger.info(f"Deleting mapping for rental_class_id: {rental_class_id}")
        current_app.logger.info(f"Deleting mapping for rental_class_id: {rental_class_id}")
        deleted_count = session.query(UserRentalClassMapping).filter_by(rental_class_id=rental_class_id).delete()
        session.commit()
        logger.info(f"Deleted {deleted_count} user mappings for rental_class_id: {rental_class_id}")
        current_app.logger.info(f"Deleted {deleted_count} user mappings for rental_class_id: {rental_class_id}")

        return jsonify({'message': 'Mapping deleted successfully'})
    except SQLAlchemyError as e:
        logger.error(f"Database error during delete_mapping: {str(e)}", exc_info=True)
        current_app.logger.error(f"Database error during delete_mapping: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"Unexpected error during delete_mapping: {str(e)}", exc_info=True)
        current_app.logger.error(f"Unexpected error during delete_mapping: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
    finally:
        if session:
            session.close()
            logger.info("Database session closed for delete_mapping")
            current_app.logger.info("Database session closed for delete_mapping")