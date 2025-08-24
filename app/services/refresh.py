# app/services/refresh.py
# refresh.py version: 2025-06-27-v9
import logging
import traceback
from datetime import datetime, timedelta, timezone
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.sql import text
from .. import db
from ..models.db_models import (
    ItemMaster,
    Transaction,
    SeedRentalClass,
    RefreshState,
    UserRentalClassMapping,
)
from ..services.api_client import APIClient
from flask import Blueprint, jsonify
from config import INCREMENTAL_LOOKBACK_SECONDS, LOG_FILE
import time
import os
import csv
import json
from .logger import get_logger

# Configure logging
logger = get_logger(f'refresh_{os.getpid()}', level=logging.INFO, log_file=LOG_FILE)

refresh_bp = Blueprint('refresh', __name__)

api_client = APIClient()

def validate_date(date_str, field_name, tag_id):
    """Validate date string and return datetime object or None.
    
    Args:
        date_str (str): Date string to validate
        field_name (str): Name of the date field
        tag_id (str): Tag ID for logging context
    
    Returns:
        datetime: Parsed datetime object or None if invalid
    """
    if date_str is None or date_str == '0000-00-00 00:00:00':
        logger.debug(f"Null or invalid {field_name} for tag_id {tag_id}: {date_str}, returning None")
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError as e:
            if all(c in '0123456789ABCDEFabcdef' for c in date_str):
                logger.warning(f"Possible hexadecimal {field_name} for tag_id {tag_id}: {date_str}. Returning None.")
            else:
                logger.warning(f"Invalid {field_name} for tag_id {tag_id}: {date_str}. Error: {str(e)}. Returning None.")
            return None

def update_refresh_state(state_type, timestamp):
    """Update the refresh_state table with the latest refresh timestamp.
    
    Args:
        state_type (str): Type of refresh (full or incremental)
        timestamp (datetime): Timestamp of the refresh
    """
    session = db.session()
    try:
        refresh_state = session.query(RefreshState).first()
        if not refresh_state:
            refresh_state = RefreshState(last_refresh=timestamp.strftime('%Y-%m-%d %H:%M:%S'), state_type=state_type)
            session.add(refresh_state)
        else:
            refresh_state.last_refresh = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            refresh_state.state_type = state_type
        session.commit()
        logger.info(f"Updated refresh state: {state_type} at {timestamp}")
    except Exception as e:
        logger.error(f"Error updating refresh state: {str(e)}", exc_info=True)
        session.rollback()
    finally:
        session.close()

def update_user_mappings(session, csv_file_path='/home/tim/RFID3/seeddata_20250425155406.csv'):
    """Populate user_rental_class_mappings from CSV, preserving existing user mappings.
    
    Creates a temporary table to back up user mappings, merges with CSV data
    (prioritizing user mappings), and repopulates user_rental_class_mappings.
    
    Args:
        session: SQLAlchemy session
        csv_file_path (str): Path to seed data CSV
    """
    logger.info("Updating user_rental_class_mappings from CSV while preserving user mappings")
    try:
        # Create temporary table for user mappings backup
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS temp_user_rental_class_mappings (
                rental_class_id VARCHAR(50) PRIMARY KEY,
                category VARCHAR(100) NOT NULL,
                subcategory VARCHAR(100) NOT NULL,
                short_common_name VARCHAR(50),
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """))
        session.commit()
        logger.debug("Created temporary table temp_user_rental_class_mappings")

        # Back up existing user mappings
        session.execute(text("""
            INSERT INTO temp_user_rental_class_mappings
            SELECT * FROM user_rental_class_mappings
        """))
        session.commit()
        logger.debug("Backed up user_rental_class_mappings to temporary table")

        # Read CSV and deduplicate mappings
        mappings_dict = {}
        row_count = 0
        if not os.path.exists(csv_file_path):
            logger.error(f"CSV file not found at: {csv_file_path}")
            return
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            logger.info("Reading CSV for user mappings")
            expected_columns = {'rental_class_id', 'Cat', 'SubCat'}
            if not expected_columns.issubset(reader.fieldnames):
                logger.error(f"CSV missing required columns. Expected: {expected_columns}, Found: {reader.fieldnames}")
                return
            for row in reader:
                row_count += 1
                try:
                    rental_class_id = row.get('rental_class_id', '').strip().upper()
                    category = row.get('Cat', '').strip()
                    subcategory = row.get('SubCat', '').strip()
                    if not rental_class_id or not category or not subcategory:
                        logger.debug(f"Skipping row {row_count} with missing data: {row}")
                        continue
                    if rental_class_id in mappings_dict:
                        logger.warning(f"Duplicate rental_class_id {rental_class_id} at row {row_count}, keeping first")
                        continue
                    mappings_dict[rental_class_id] = {
                        'rental_class_id': rental_class_id,
                        'category': category,
                        'subcategory': subcategory,
                        'short_common_name': row.get('short_common_name', '').strip() or 'N/A',
                        'created_at': datetime.now(timezone.utc),
                        'updated_at': datetime.now(timezone.utc)
                    }
                except Exception as e:
                    logger.error(f"Error processing CSV row {row_count}: {str(e)}", exc_info=True)
                    continue

        # Fetch existing user mappings from temporary table
        existing_mappings = session.execute(text("SELECT * FROM temp_user_rental_class_mappings")).fetchall()
        existing_mapping_dict = {}
        for row in existing_mappings:
            if hasattr(row, 'rental_class_id') and row.rental_class_id:
                existing_mapping_dict[row.rental_class_id] = {
                    'rental_class_id': row.rental_class_id,
                    'category': row.category,
                    'subcategory': row.subcategory,
                    'short_common_name': row.short_common_name or 'N/A',
                    'created_at': row.created_at,
                    'updated_at': row.updated_at
                }
            else:
                logger.warning(f"Skipping invalid row in temp_user_rental_class_mappings: {row}")

        # Merge mappings, prioritizing user mappings
        merged_mappings = {}
        for rental_class_id, mapping in existing_mapping_dict.items():
            merged_mappings[rental_class_id] = mapping
        for rental_class_id, mapping in mappings_dict.items():
            if rental_class_id not in merged_mappings:
                merged_mappings[rental_class_id] = mapping
            else:
                logger.debug(f"Preserving user mapping for rental_class_id {rental_class_id}")

        logger.info(f"Processed {row_count} CSV rows, {len(merged_mappings)} merged mappings (user mappings prioritized)")

        # NO DELETE - preserve all existing user mappings, only add new ones
        logger.info("Preserving all existing user mappings, only inserting new CSV mappings")

        # Use safe upsert approach - only insert new CSV mappings, preserve existing user ones
        inserted_count = 0
        skipped_count = 0
        
        # Get current rental_class_ids to avoid duplicates
        existing_ids = {row[0] for row in session.query(UserRentalClassMapping.rental_class_id).all()}
        
        for mapping in merged_mappings.values():
            try:
                if 'rental_class_id' not in mapping or not mapping['rental_class_id']:
                    logger.warning(f"Skipping mapping with missing rental_class_id: {mapping}")
                    continue
                    
                rental_class_id = mapping['rental_class_id']
                
                # Only insert if it doesn't already exist (preserve user mappings)
                if rental_class_id in existing_ids:
                    logger.debug(f"Preserving existing user mapping for {rental_class_id}")
                    skipped_count += 1
                    continue
                
                user_mapping = UserRentalClassMapping(
                    rental_class_id=mapping['rental_class_id'],
                    category=mapping['category'],
                    subcategory=mapping['subcategory'],
                    short_common_name=mapping.get('short_common_name', ''),
                    created_at=mapping.get('created_at', datetime.now(timezone.utc)),
                    updated_at=mapping.get('updated_at', datetime.now(timezone.utc))
                )
                session.add(user_mapping)
                inserted_count += 1
                logger.debug(f"Inserted new CSV mapping: {mapping['rental_class_id']}")
                
            except Exception as e:
                logger.error(f"Error processing mapping: {str(e)}", exc_info=True)
                continue

        session.commit()
        logger.info(f"Processed {len(merged_mappings)} mappings: {inserted_count} new CSV mappings inserted, {skipped_count} user mappings preserved")

        # Drop temporary table
        session.execute(text("DROP TABLE IF EXISTS temp_user_rental_class_mappings"))
        session.commit()
        logger.debug("Dropped temporary user mappings table")
    except Exception as e:
        logger.error(f"Error updating user mappings: {str(e)}", exc_info=True)
        session.rollback()
    finally:
        session.execute(text("DROP TABLE IF EXISTS temp_user_rental_class_mappings"))
        session.commit()
        session.close()

def update_item_master(session, items):
    """Update id_item_master with provided items.
    
    Args:
        session: SQLAlchemy session
        items: List of item dictionaries
    """
    if not items:
        logger.info("No items to update in id_item_master")
        return
    logger.info(f"Updating {len(items)} items in id_item_master")
    skipped = 0
    failed = 0
    batch_size = 500
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        try:
            for item in batch:
                tag_id = item.get('tag_id')
                if not tag_id:
                    logger.warning(f"Skipping item with missing tag_id: {item}")
                    skipped += 1
                    continue
                db_item = ItemMaster(tag_id=tag_id)
                db_item.serial_number = item.get('serial_number')
                db_item.rental_class_num = item.get('rental_class_num')
                db_item.client_name = item.get('client_name')
                db_item.common_name = item.get('common_name', 'Unknown')
                db_item.quality = item.get('quality')
                db_item.bin_location = item.get('bin_location')
                raw_status = item.get('status')
                db_item.status = raw_status if raw_status else 'Unknown'
                db_item.last_contract_num = item.get('last_contract_num')
                db_item.last_scanned_by = item.get('last_scanned_by')
                db_item.notes = item.get('notes')
                db_item.status_notes = item.get('status_notes')
                longitude = item.get('long')
                latitude = item.get('lat')
                db_item.longitude = float(longitude) if longitude and longitude.strip() else None
                db_item.latitude = float(latitude) if latitude and longitude.strip() else None
                db_item.date_last_scanned = validate_date(item.get('date_last_scanned'), 'date_last_scanned', tag_id)
                db_item.date_created = validate_date(item.get('date_created'), 'date_created', tag_id)
                db_item.date_updated = validate_date(item.get('date_updated'), 'date_updated', tag_id)
                session.merge(db_item)
            session.commit()
            logger.debug(f"Committed item batch {i//batch_size + 1}")
        except Exception as e:
            logger.error(f"Error updating item batch {i//batch_size + 1}: {str(e)}", exc_info=True)
            session.rollback()
            failed += len(batch)
    logger.info(f"Updated {len(items) - skipped - failed} items, skipped {skipped}, failed {failed}")

def update_transactions(session, transactions):
    """Update id_transactions with provided transactions.
    
    Args:
        session: SQLAlchemy session
        transactions: List of transaction dictionaries
    """
    if not transactions:
        logger.info("No transactions to update in id_transactions")
        return
    logger.info(f"Updating {len(transactions)} transactions in id_transactions")
    skipped = 0
    failed = 0
    batch_size = 500
    for i in range(0, len(transactions), batch_size):
        batch = transactions[i:i + batch_size]
        try:
            for transaction in batch:
                tag_id = transaction.get('tag_id')
                scan_date = transaction.get('scan_date')
                if not tag_id or not scan_date:
                    logger.warning(f"Skipping transaction with missing tag_id or scan_date: {transaction}")
                    skipped += 1
                    continue
                scan_date_dt = validate_date(scan_date, 'scan_date', tag_id)
                if not scan_date_dt:
                    logger.warning(f"Skipping transaction with invalid scan_date for tag_id {tag_id}: {scan_date}")
                    skipped += 1
                    continue
                db_transaction = Transaction(tag_id=tag_id, scan_date=scan_date_dt)
                db_transaction.scan_type = transaction.get('scan_type', 'Unknown')
                db_transaction.contract_number = transaction.get('contract_number')
                db_transaction.client_name = transaction.get('client_name')
                db_transaction.notes = transaction.get('notes')
                db_transaction.rental_class_num = transaction.get('rental_class_id')
                db_transaction.common_name = transaction.get('common_name', 'Unknown')
                db_transaction.serial_number = transaction.get('serial_number')
                db_transaction.location_of_repair = transaction.get('location_of_repair')
                db_transaction.quality = transaction.get('quality')
                db_transaction.bin_location = transaction.get('bin_location')
                db_transaction.status = transaction.get('status')
                db_transaction.scan_by = transaction.get('scan_by')
                def to_bool(value):
                    if isinstance(value, str):
                        return value.lower() == 'true'
                    return bool(value) if value is not None else None
                db_transaction.dirty_or_mud = to_bool(transaction.get('dirty_or_mud'))
                db_transaction.leaves = to_bool(transaction.get('leaves'))
                db_transaction.oil = to_bool(transaction.get('oil'))
                db_transaction.mold = to_bool(transaction.get('mold'))
                db_transaction.stain = to_bool(transaction.get('stain'))
                db_transaction.oxidation = to_bool(transaction.get('oxidation'))
                db_transaction.other = transaction.get('other')
                db_transaction.rip_or_tear = to_bool(transaction.get('rip_or_tear'))
                db_transaction.sewing_repair_needed = to_bool(transaction.get('sewing_repair_needed'))
                db_transaction.grommet = to_bool(transaction.get('grommet'))
                db_transaction.rope = to_bool(transaction.get('rope'))
                db_transaction.buckle = to_bool(transaction.get('buckle'))
                db_transaction.wet = to_bool(transaction.get('wet'))
                db_transaction.service_required = to_bool(transaction.get('service_required'))
                db_transaction.date_created = validate_date(transaction.get('date_created'), 'date_created', tag_id)
                db_transaction.date_updated = validate_date(transaction.get('date_updated'), 'date_updated', tag_id)
                session.merge(db_transaction)
            session.commit()
            logger.debug(f"Committed transaction batch {i//batch_size + 1}")
        except Exception as e:
            logger.error(f"Error updating transaction batch {i//batch_size + 1}: {str(e)}", exc_info=True)
            session.rollback()
            failed += len(batch)
    logger.info(f"Updated {len(transactions) - skipped - failed} transactions, skipped {skipped}, failed {failed}")

def update_seed_data(session, seed_data):
    """Update seed_rental_classes with provided seed data.
    
    Args:
        session: SQLAlchemy session
        seed_data: List of seed data dictionaries
    """
    if not seed_data:
        logger.info("No seed data to update in seed_rental_classes")
        return
    logger.info(f"Updating {len(seed_data)} items in seed_rental_classes")
    skipped = 0
    failed = 0
    batch_size = 500
    for i in range(0, len(seed_data), batch_size):
        batch = seed_data[i:i + batch_size]
        try:
            for item in batch:
                rental_class_id = item.get('rental_class_id')
                if not rental_class_id:
                    logger.warning(f"Skipping seed item with missing rental_class_id: {item}")
                    skipped += 1
                    continue
                db_seed = SeedRentalClass(rental_class_id=rental_class_id)
                db_seed.common_name = item.get('common_name', 'Unknown')
                db_seed.bin_location = item.get('bin_location')
                session.merge(db_seed)
            session.commit()
            logger.debug(f"Committed seed data batch {i//batch_size + 1}")
        except Exception as e:
            logger.error(f"Error updating seed item batch {i//batch_size + 1}: {str(e)}", exc_info=True)
            session.rollback()
            failed += len(batch)
    logger.info(f"Updated {len(seed_data) - skipped - failed} seed items, skipped {skipped}, failed {failed}")

def full_refresh():
    """Perform a full refresh of the database.

    Retrieves *all* available fields from the Item Master, Transactions,
    and Seed Rental Class APIs and replaces the corresponding tables in the
    local database.
    """
    logger.info("Starting full refresh of item master, transactions, and seed data")
    session = db.session()
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.debug("Clearing existing data")
            deleted_items = session.query(ItemMaster).delete()
            deleted_transactions = session.query(Transaction).delete()
            deleted_seed = session.query(SeedRentalClass).delete()
            session.commit()
            logger.info(f"Deleted {deleted_items} items from id_item_master")
            logger.info(f"Deleted {deleted_transactions} transactions from id_transactions")
            logger.info(f"Deleted {deleted_seed} items from seed_rental_classes")

            logger.debug("Fetching data from API")
            items = api_client.get_item_master(since_date=None, full_refresh=True)
            transactions = api_client.get_transactions(since_date=None, full_refresh=True)
            seed_data = api_client.get_seed_data()

            logger.info(f"Fetched {len(items)} item master records")
            logger.info(f"Fetched {len(transactions)} transaction records")
            logger.info(f"Fetched {len(seed_data)} seed rental class records")

            if not items:
                logger.warning("No items fetched from item master API")
            if not transactions:
                logger.warning("No transactions fetched from transactions API")
            if not seed_data:
                logger.warning("No seed data fetched from seed API")

            update_item_master(session, items)
            update_transactions(session, transactions)
            update_seed_data(session, seed_data)
            update_user_mappings(session)

            update_refresh_state('full_refresh', datetime.now(timezone.utc))
            logger.info("Full refresh completed successfully")
            break
        except OperationalError as e:
            if "Deadlock" in str(e):
                if attempt < max_retries - 1:
                    logger.warning(f"Deadlock detected, retrying ({attempt + 1}/{max_retries})")
                    session.rollback()
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.error(f"Max retries reached for deadlock: {str(e)}", exc_info=True)
                    raise
            else:
                logger.error(f"Database error: {str(e)}", exc_info=True)
                raise
        except Exception as e:
            logger.error(f"Full refresh failed: {str(e)}", exc_info=True)
            session.rollback()
            raise
        finally:
            if session.is_active:
                session.rollback()
            session.close()

def incremental_refresh():
    """Perform an incremental refresh of the database.

    Fetches all fields for updated Item Master and Transaction records since
    the configured lookback interval and applies them to the local database.
    """
    logger.info("Starting incremental refresh for item master and transactions")
    session = db.session()
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with session.no_autoflush:
                since_date = datetime.now(timezone.utc) - timedelta(seconds=INCREMENTAL_LOOKBACK_SECONDS)
                logger.info(
                    f"Checking for item master and transaction updates since: {since_date.strftime('%Y-%m-%d %H:%M:%S')}"
                )

                items = api_client.get_item_master(since_date=since_date, full_refresh=False)
                logger.info(f"Fetched {len(items)} item master records")
                if not items:
                    logger.info("No new items fetched from item master API")

                transactions = api_client.get_transactions(since_date=since_date, full_refresh=False)
                logger.info(f"Fetched {len(transactions)} transaction records")
                if not transactions:
                    logger.info("No new transactions fetched from transactions API")

                if not items and not transactions:
                    logger.info("No new item master or transaction data to process, skipping database updates")
                    session.commit()
                    update_refresh_state('incremental_refresh', datetime.now(timezone.utc))
                    break

                update_item_master(session, items)
                update_transactions(session, transactions)

                session.commit()
                update_refresh_state('incremental_refresh', datetime.now(timezone.utc))
                logger.info("Incremental refresh completed successfully")
                break
        except OperationalError as e:
            if "Lock wait timeout" in str(e) or "Deadlock" in str(e):
                if attempt < max_retries - 1:
                    logger.warning(f"Database lock/timeout detected, retrying ({attempt + 1}/{max_retries})")
                    session.rollback()
                    time.sleep(2 ** attempt)
                    continue
                else:
                    logger.error(f"Max retries reached for lock/timeout: {str(e)}", exc_info=True)
                    raise
            else:
                logger.error(f"Database error: {str(e)}", exc_info=True)
                raise
        except Exception as e:
            logger.error(f"Incremental refresh failed: {str(e)}", exc_info=True)
            session.rollback()
            raise
        finally:
            session.close()

@refresh_bp.route('/refresh/full', methods=['POST'])
def full_refresh_endpoint():
    """Endpoint for full refresh."""
    logger.info("Received request for full refresh via endpoint")
    try:
        full_refresh()
        logger.info("Full refresh completed successfully")
        return jsonify({'status': 'success', 'message': 'Full refresh completed successfully'})
    except OperationalError as e:
        logger.error(f"Database error during full refresh: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': f"Database error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Full refresh failed: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@refresh_bp.route('/refresh/incremental', methods=['POST'])
def incremental_refresh_endpoint():
    """Endpoint for incremental refresh."""
    logger.info("Received request for incremental refresh via endpoint")
    try:
        incremental_refresh()
        logger.info("Incremental refresh completed successfully")
        return jsonify({'status': 'success', 'message': 'Incremental refresh completed successfully'})
    except OperationalError as e:
        logger.error(f"Database error during incremental refresh: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': f"Database error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Incremental refresh failed: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@refresh_bp.route('/clear_api_data', methods=['POST'])
def clear_api_data():
    """Endpoint to clear API data and perform full refresh."""
    logger.info("Received request for clear API data and refresh")
    try:
        full_refresh()
        logger.info("Clear API data and refresh completed successfully")
        return jsonify({'status': 'success', 'message': 'API data cleared and refreshed successfully'})
    except OperationalError as e:
        logger.error(f"Database error during clear API data: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': f"Database error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Clear API data and refresh failed: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@refresh_bp.route('/refresh/status', methods=['GET'])
def get_refresh_status():
    """Endpoint to fetch refresh status."""
    logger.info("Fetching refresh status")
    session = db.session()
    try:
        refresh_state = session.query(RefreshState).first()
        if refresh_state:
            return jsonify({
                'status': 'success',
                'last_refresh': refresh_state.last_refresh,
                'refresh_type': refresh_state.state_type
            })
        else:
            logger.info("No refresh state found")
            return jsonify({
                'status': 'success',
                'last_refresh': 'N/A',
                'refresh_type': 'N/A'
            })
    except Exception as e:
        logger.error(f"Error fetching refresh status: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        session.close()