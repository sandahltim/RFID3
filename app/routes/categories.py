# app/routes/categories.py
# categories.py version: 2025-06-26-v27
import logging
import sys
import json
from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db, cache
from ..models.db_models import RentalClassMapping, UserRentalClassMapping, SeedRentalClass
from ..services.api_client import APIClient
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime
from time import time

# Configure logging
logger = logging.getLogger('categories')
logger.setLevel(logging.INFO)
logger.handlers = []
file_handler = logging.FileHandler('/home/tim/test_rfidpi/logs/rfid_dashboard.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

categories_bp = Blueprint('categories', __name__)

logger.info(f"Deployed categories.py version: 2025-06-26-v27")

def normalize_rental_class_id(rental_class_id):
    """Normalize rental_class_id for consistent lookup."""
    if not rental_class_id:
        return 'N/A'
    return str(rental_class_id).strip().upper()

@categories_bp.route('/categories', methods=['GET', 'POST'])
def manage_categories():
    session = None
    try:
        session = db.session()
        logger.info("Starting new session for categories")
        current_app.logger.info("Starting new session for categories")

        # Fetch mappings
        cache_key = 'rental_class_mappings'
        mappings_dict_json = cache.get(cache_key)
        if mappings_dict_json is None:
            logger.debug("Cache miss for rental_class_mappings")
            base_mappings = session.query(RentalClassMapping).all()
            user_mappings = session.query(UserRentalClassMapping).all()
            mappings_dict = {normalize_rental_class_id(m.rental_class_id): {
                'category': m.category,
                'subcategory': m.subcategory,
                'short_common_name': m.short_common_name or 'N/A'
            } for m in base_mappings}
            for um in user_mappings:
                normalized_id = normalize_rental_class_id(um.rental_class_id)
                mappings_dict[normalized_id] = {
                    'category': um.category,
                    'subcategory': um.subcategory,
                    'short_common_name': um.short_common_name or 'N/A'
                }
            try:
                cache.set(cache_key, json.dumps(mappings_dict), ex=3600)
                logger.info("Cached rental_class_mappings as JSON")
            except Exception as e:
                logger.error(f"Error caching rental_class_mappings: {str(e)}. Data will be fetched on next request.", exc_info=True)
                current_app.logger.error(f"Error caching rental_class_mappings: {str(e)}. Data will be fetched on next request.", exc_info=True)
        else:
            mappings_dict = json.loads(mappings_dict_json)
            logger.debug("Retrieved rental_class_mappings from cache")

        # Fetch seed data
        cache_key_seed = 'seed_rental_classes'
        seed_data_json = cache.get(cache_key_seed)
        if seed_data_json is None:
            logger.debug("Cache miss for seed_rental_classes")
            seed_data = session.query(SeedRentalClass).all()
            if not seed_data:
                logger.info("No seed data in database, fetching from API")
                api_client = APIClient()
                seed_data_api = api_client.get_seed_data()
                for item in seed_data_api:
                    rental_class_id = item.get('rental_class_id')
                    if not rental_class_id:
                        logger.warning(f"Skipping seed item with missing rental_class_id: {item}")
                        continue
                    db_seed = SeedRentalClass(
                        rental_class_id=rental_class_id,
                        common_name=item.get('common_name', 'Unknown'),
                        bin_location=item.get('bin_location')
                    )
                    session.merge(db_seed)
                session.commit()
                seed_data = session.query(SeedRentalClass).all()
            seed_data_copy = [{
                'rental_class_id': item.rental_class_id,
                'common_name': item.common_name,
                'bin_location': item.bin_location
            } for item in seed_data]
            try:
                cache.set(cache_key_seed, json.dumps(seed_data_copy), ex=3600)
                logger.info("Cached seed_rental_classes as JSON")
            except Exception as e:
                logger.error(f"Error caching seed_data: {str(e)}. Data will be fetched on next request.", exc_info=True)
                current_app.logger.error(f"Error caching seed_data: {str(e)}. Data will be fetched on next request.", exc_info=True)
            common_name_dict = {item.rental_class_id: item.common_name for item in seed_data}
            logger.info(f"Built common_name_dict with {len(common_name_dict)} entries")
        else:
            seed_data_copy = json.loads(seed_data_json)
            common_name_dict = {item['rental_class_id']: item['common_name'] for item in seed_data_copy}
            logger.info(f"Retrieved seed_rental_classes from cache with {len(common_name_dict)} entries")

        if request.method == 'POST':
            data = request.get_json()
            action = data.get('action')
            rental_class_id = normalize_rental_class_id(data.get('rental_class_id'))
            category = data.get('category')
            subcategory = data.get('subcategory')
            short_common_name = data.get('short_common_name', '')

            if action == 'add':
                if not rental_class_id or not category or not subcategory:
                    logger.warning(f"Invalid input for add: {data}")
                    return jsonify({'error': 'Rental class ID, category, and subcategory are required'}), 400
                existing = session.query(UserRentalClassMapping).filter_by(rental_class_id=rental_class_id).first()
                if existing:
                    logger.warning(f"Mapping already exists for rental_class_id: {rental_class_id}")
                    return jsonify({'error': 'Mapping already exists for this rental class ID'}), 400
                new_mapping = UserRentalClassMapping(
                    rental_class_id=rental_class_id,
                    category=category,
                    subcategory=subcategory,
                    short_common_name=short_common_name,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(new_mapping)
                session.commit()
                cache.delete(cache_key)
                logger.info(f"Added new user mapping: {rental_class_id}")
                return jsonify({'message': 'Mapping added successfully'}), 200

            elif action == 'update':
                if not rental_class_id or not category or not subcategory:
                    logger.warning(f"Invalid input for update: {data}")
                    return jsonify({'error': 'Rental class ID, category, and subcategory are required'}), 400
                mapping = session.query(UserRentalClassMapping).filter_by(rental_class_id=rental_class_id).first()
                if not mapping:
                    logger.warning(f"No user mapping found for rental_class_id: {rental_class_id}")
                    return jsonify({'error': 'No user mapping found for this rental class ID'}), 404
                mapping.category = category
                mapping.subcategory = subcategory
                mapping.short_common_name = short_common_name
                mapping.updated_at = datetime.now()
                session.commit()
                cache.delete(cache_key)
                logger.info(f"Updated user mapping: {rental_class_id}")
                return jsonify({'message': 'Mapping updated successfully'}), 200

            elif action == 'delete':
                if not rental_class_id:
                    logger.warning(f"Invalid input for delete: {data}")
                    return jsonify({'error': 'Rental class ID is required'}), 400
                mapping = session.query(UserRentalClassMapping).filter_by(rental_class_id=rental_class_id).first()
                if not mapping:
                    logger.warning(f"No user mapping found for rental_class_id: {rental_class_id}")
                    return jsonify({'error': 'No user mapping found for this rental class ID'}), 404
                session.delete(mapping)
                session.commit()
                cache.delete(cache_key)
                logger.info(f"Deleted user mapping: {rental_class_id}")
                return jsonify({'message': 'Mapping deleted successfully'}), 200

            else:
                logger.warning(f"Invalid action: {action}")
                return jsonify({'error': 'Invalid action'}), 400

        # GET request
        mappings = []
        for rental_class_id, mapping in mappings_dict.items():
            common_name = common_name_dict.get(rental_class_id, 'Unknown')
            mappings.append({
                'rental_class_id': rental_class_id,
                'common_name': common_name,
                'category': mapping['category'],
                'subcategory': mapping['subcategory'],
                'short_common_name': mapping['short_common_name']
            })
        logger.info(f"Fetched {len(mappings)} category mappings")
        current_app.logger.info(f"Fetched {len(mappings)} category mappings")
        return render_template('categories.html', mappings=mappings, cache_bust=int(time()))

    except Exception as e:
        logger.error(f"Error in manage_categories: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error in manage_categories: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return render_template('categories.html', mappings=[], error=str(e))
    finally:
        if session:
            session.close()

@categories_bp.route('/categories/mappings', methods=['GET'])
def get_mappings():
    session = None
    try:
        session = db.session()
        logger.info(f"Fetching rental class mappings for API at {time.time()}")
        current_app.logger.info(f"Fetching rental class mappings for API at {time.time()}")

        cache_key = 'rental_class_mappings'
        mappings_dict_json = cache.get(cache_key)
        if mappings_dict_json is None:
            logger.debug("Cache miss for rental_class_mappings")
            base_mappings = session.query(RentalClassMapping).all()
            logger.info(f"Fetched {len(base_mappings)} base mappings from RentalClassMapping")
            user_mappings = session.query(UserRentalClassMapping).all()
            logger.info(f"Fetched {len(user_mappings)} user mappings from UserRentalClassMapping")
            mappings_dict = {normalize_rental_class_id(m.rental_class_id): {
                'category': m.category,
                'subcategory': m.subcategory,
                'short_common_name': m.short_common_name or 'N/A'
            } for m in base_mappings}
            for um in user_mappings:
                normalized_id = normalize_rental_class_id(um.rental_class_id)
                mappings_dict[normalized_id] = {
                    'category': um.category,
                    'subcategory': um.subcategory,
                    'short_common_name': um.short_common_name or 'N/A'
                }
            try:
                cache.set(cache_key, json.dumps(mappings_dict), ex=3600)
                logger.info("Cached rental_class_mappings as JSON")
            except Exception as e:
                logger.error(f"Error caching rental_class_mappings: {str(e)}. Data will be fetched on next request.", exc_info=True)
                current_app.logger.error(f"Error caching rental_class_mappings: {str(e)}. Data will be fetched on next request.", exc_info=True)
        else:
            mappings_dict = json.loads(mappings_dict_json)
            logger.debug("Retrieved rental_class_mappings from cache")

        cache_key_seed = 'seed_rental_classes'
        seed_data_json = cache.get(cache_key_seed)
        if seed_data_json is None:
            logger.info("Seed data not found in cache or cache failed, fetching from database")
            seed_data = session.query(SeedRentalClass).all()
            logger.info(f"Fetched {len(seed_data)} seed data records from database")
            if not seed_data:
                logger.info("No seed data in database, fetching from API")
                api_client = APIClient()
                seed_data_api = api_client.get_seed_data()
                for item in seed_data_api:
                    rental_class_id = item.get('rental_class_id')
                    if not rental_class_id:
                        logger.warning(f"Skipping seed item with missing rental_class_id: {item}")
                        continue
                    db_seed = SeedRentalClass(
                        rental_class_id=rental_class_id,
                        common_name=item.get('common_name', 'Unknown'),
                        bin_location=item.get('bin_location')
                    )
                    session.merge(db_seed)
                session.commit()
                seed_data = session.query(SeedRentalClass).all()
            seed_data_copy = [{
                'rental_class_id': item.rental_class_id,
                'common_name': item.common_name,
                'bin_location': item.bin_location
            } for item in seed_data]
            try:
                cache.set(cache_key_seed, json.dumps(seed_data_copy), ex=3600)
                logger.info("Cached seed_rental_classes as JSON")
            except Exception as e:
                logger.error(f"Error caching seed_data: {str(e)}. Data will be fetched on next request.", exc_info=True)
                current_app.logger.error(f"Error caching seed_data: {str(e)}. Data will be fetched on next request.", exc_info=True)
            common_name_dict = {item.rental_class_id: item.common_name for item in seed_data}
        else:
            seed_data_copy = json.loads(seed_data_json)
            common_name_dict = {item['rental_class_id']: item['common_name'] for item in seed_data_copy}
            logger.info(f"Retrieved seed_rental_classes from cache with {len(common_name_dict)} entries")

        mappings = []
        for rental_class_id, mapping in mappings_dict.items():
            common_name = common_name_dict.get(rental_class_id, 'Unknown')
            mappings.append({
                'rental_class_id': rental_class_id,
                'common_name': common_name,
                'category': mapping['category'],
                'subcategory': mapping['subcategory'],
                'short_common_name': mapping['short_common_name']
            })
        logger.info(f"Returning {len(mappings)} category mappings")
        current_app.logger.info(f"Returning {len(mappings)} category mappings")
        return jsonify(mappings)
    except Exception as e:
        logger.error(f"Error fetching mappings: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error fetching mappings: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@categories_bp.route('/categories/update', methods=['POST'])
def update_mappings():
    session = None
    try:
        session = db.session()
        logger.info(f"Starting new session for update_mappings at {time()}")
        current_app.logger.info(f"Starting new session for update_mappings at {time()}")

        new_mappings = request.get_json()
        logger.info(f"Received {len(new_mappings)} new mappings")
        current_app.logger.info(f"Received {len(new_mappings)} new mappings")

        if not isinstance(new_mappings, list):
            logger.error("Invalid data format received, expected a list")
            current_app.logger.error("Invalid data format received, expected a list")
            return jsonify({'error': 'Invalid data format, expected a list'}), 400

        for mapping in new_mappings:
            rental_class_id = mapping.get('rental_class_id')
            category = mapping.get('category')
            subcategory = mapping.get('subcategory', '')
            short_common_name = mapping.get('short_common_name', '')

            if not rental_class_id or not category:
                logger.warning(f"Skipping invalid mapping due to missing rental_class_id or category: {mapping}")
                current_app.logger.warning(f"Skipping invalid mapping due to missing rental_class_id or category: {mapping}")
                continue

            existing = session.query(UserRentalClassMapping).filter_by(rental_class_id=rental_class_id).first()
            if existing:
                existing.category = category
                existing.subcategory = subcategory
                existing.short_common_name = short_common_name
                existing.updated_at = datetime.now()
                logger.debug(f"Updated existing mapping: rental_class_id={rental_class_id}, category={category}, subcategory={subcategory}")
            else:
                user_mapping = UserRentalClassMapping(
                    rental_class_id=rental_class_id,
                    category=category,
                    subcategory=subcategory or '',
                    short_common_name=short_common_name or '',
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(user_mapping)
                logger.debug(f"Added new mapping: rental_class_id={rental_class_id}, category={category}, subcategory={subcategory}")

        session.commit()
        logger.info("Successfully committed rental class mappings")
        current_app.logger.info("Successfully committed rental class mappings")
        cache.delete('rental_class_mappings')
        return jsonify({'message': 'Mappings updated successfully'})
    except IntegrityError as e:
        logger.error(f"Database integrity error during update_mappings: {str(e)}", exc_info=True)
        current_app.logger.error(f"Database integrity error during update_mappings: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({'error': f'Database integrity error: {str(e)}'}), 400
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
        cache.delete('rental_class_mappings')
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