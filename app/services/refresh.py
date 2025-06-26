# app/services/refresh.py
# refresh.py version: 2025-06-26-v4
import logging
import traceback
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from .. import db
from ..models.db_models import ItemMaster, Transaction, SeedRentalClass, RefreshState
from ..services.api_client import APIClient
from flask import Blueprint, jsonify
from config import INCREMENTAL_LOOKBACK_SECONDS
import time
import os

logger = logging.getLogger(f'refresh_{os.getpid()}')
logger.setLevel(logging.INFO)
if not logger.handlers:
    file_handler = logging.FileHandler('/home/tim/test_rfidpi/logs/rfid_dashboard.log')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

refresh_bp = Blueprint('refresh', __name__)

api_client = APIClient()

def validate_date(date_str, field_name, tag_id):
    """Validate date string and return datetime object or None."""
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
    """Update the refresh_state table with the latest refresh timestamp."""
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

def update_item_master(session, items):
    logger.info(f"Updating {len(items)} items in id_item_master")
    skipped = 0
    batch_size = 100
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        try:
            with session.no_autoflush:  # Prevent autoflush to avoid deadlocks
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
        except Exception as e:
            logger.error(f"Error updating item batch {i//batch_size + 1}: {str(e)}", exc_info=True)
            session.rollback()
            raise
    logger.info(f"Skipped {skipped} items due to missing or invalid data")

def update_transactions(session, transactions):
    logger.info(f"Updating {len(transactions)} transactions in id_transactions")
    skipped = 0
    batch_size = 100
    for i in range(0, len(transactions), batch_size):
        batch = transactions[i:i + batch_size]
        try:
            with session.no_autoflush:
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
        except Exception as e:
            logger.error(f"Error updating transaction batch {i//batch_size + 1}: {str(e)}", exc_info=True)
            session.rollback()
            raise
    logger.info(f"Skipped {skipped} transactions due to missing or invalid data")

def update_seed_data(session, seed_data):
    logger.info(f"Updating {len(seed_data)} items in seed_rental_classes")
    skipped = 0
    batch_size = 100
    for i in range(0, len(seed_data), batch_size):
        batch = seed_data[i:i + batch_size]
        try:
            with session.no_autoflush:
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
        except Exception as e:
            logger.error(f"Error updating seed item batch {i//batch_size + 1}: {str(e)}", exc_info=True)
            session.rollback()
            raise
    logger.info(f"Skipped {skipped} seed items due to missing or invalid data")

def full_refresh():
    logger.info("Starting full refresh")
    session = db.session()
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with session.begin():
                deleted_items = session.query(ItemMaster).delete()
                deleted_transactions = session.query(Transaction).delete()
                deleted_seed = session.query(SeedRentalClass).delete()
                logger.info(f"Deleted {deleted_items} items from id_item_master")
                logger.info(f"Deleted {deleted_transactions} transactions from id_transactions")
                logger.info(f"Deleted {deleted_seed} items from seed_rental_classes")

                items = api_client.get_item_master(since_date=None)
                transactions = api_client.get_transactions(since_date=None)
                seed_data = api_client.get_seed_data()

                logger.info(f"Fetched {len(items)} items from item master")
                logger.info(f"Fetched {len(transactions)} transactions")
                logger.info(f"Fetched {len(seed_data)} items from seed data")

                if not items:
                    logger.warning("No items fetched from item master API")
                if not transactions:
                    logger.warning("No transactions fetched from transactions API")
                if not seed_data:
                    logger.warning("No seed data fetched from seed API")

                update_item_master(session, items)
                update_transactions(session, transactions)
                update_seed_data(session, seed_data)

            update_refresh_state('full_refresh', datetime.utcnow())
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

def incremental_refresh():
    logger.info("Starting incremental refresh")
    session = db.session()
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with session.no_autoflush:
                since_date = datetime.utcnow() - timedelta(seconds=INCREMENTAL_LOOKBACK_SECONDS)
                logger.info(f"Checking for updates since: {since_date.strftime('%Y-%m-%d %H:%M:%S')}")

                items = api_client.get_item_master(since_date=since_date)
                logger.info(f"Fetched {len(items)} items from item master")
                if not items:
                    logger.info("No new items fetched from item master API")

                transactions = api_client.get_transactions(since_date=since_date)
                logger.info(f"Fetched {len(transactions)} transactions")
                if not transactions:
                    logger.info("No new transactions fetched from transactions API")

                update_item_master(session, items)
                update_transactions(session, transactions)

                session.commit()
                update_refresh_state('incremental_refresh', datetime.utcnow())
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
    logger.info("Received request for full refresh via endpoint")
    session = db.session()
    try:
        full_refresh()
        logger.info("Full refresh completed successfully")
        return jsonify({'status': 'success', 'message': 'Full refresh completed successfully'})
    except OperationalError as e:
        logger.error(f"Database error during full refresh: {str(e)}", exc_info=True)
        session.rollback()
        return jsonify({'status': 'error', 'message': f"Database error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Full refresh failed: {str(e)}", exc_info=True)
        session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if session.is_active:
            session.rollback()
        session.close()

@refresh_bp.route('/refresh/incremental', methods=['POST'])
def incremental_refresh_endpoint():
    logger.info("Received request for incremental refresh via endpoint")
    session = db.session()
    try:
        incremental_refresh()
        logger.info("Incremental refresh completed successfully")
        return jsonify({'status': 'success', 'message': 'Incremental refresh completed successfully'})
    except OperationalError as e:
        logger.error(f"Database error during incremental refresh: {str(e)}", exc_info=True)
        session.rollback()
        return jsonify({'status': 'error', 'message': f"Database error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Incremental refresh failed: {str(e)}", exc_info=True)
        session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if session.is_active:
            session.rollback()
        session.close()

@refresh_bp.route('/clear_api_data', methods=['POST'])
def clear_api_data():
    logger.info("Received request for clear API data and refresh")
    session = db.session()
    try:
        full_refresh()
        logger.info("Clear API data and refresh completed successfully")
        return jsonify({'status': 'success', 'message': 'API data cleared and refreshed successfully'})
    except OperationalError as e:
        logger.error(f"Database error during clear API data: {str(e)}", exc_info=True)
        session.rollback()
        return jsonify({'status': 'error', 'message': f"Database error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Clear API data and refresh failed: {str(e)}", exc_info=True)
        session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500
    finally:
        if session.is_active:
            session.rollback()
        session.close()

@refresh_bp.route('/refresh/status', methods=['GET'])
def get_refresh_status():
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