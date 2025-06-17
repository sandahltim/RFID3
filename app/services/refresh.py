# refresh.py version: 2025-06-17-v2
import logging
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from app.models.db_models import ItemMaster, Transaction, SeedRentalClass, RefreshState, db
from app.services.api_client import APIClient
from flask import Blueprint, jsonify, current_app
from config import INCREMENTAL_LOOKBACK_SECONDS

logger = logging.getLogger('refresh')
logger.setLevel(logging.INFO)

# Remove existing handlers to avoid duplicates
logger.handlers = []

# File handler for rfid_dashboard.log
file_handler = logging.FileHandler('/home/tim/test_rfidpi/logs/rfid_dashboard.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

refresh_bp = Blueprint('refresh', __name__)

api_client = APIClient()

def validate_date(date_str, field_name, tag_id):
    """Validate date string and return datetime object or None."""
    if not date_str or date_str == '0000-00-00 00:00:00':
        logger.warning(f"Invalid {field_name} for tag_id {tag_id}: {date_str}. Setting to None.")
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError as e:
            logger.warning(f"Invalid {field_name} for tag_id {tag_id}: {date_str}. Error: {str(e)}. Setting to None.")
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
    for item in items:
        try:
            tag_id = item.get('tag_id')
            if not tag_id:
                logger.warning(f"Skipping item with missing tag_id: {item}")
                skipped += 1
                continue

            db_item = session.query(ItemMaster).filter_by(tag_id=tag_id).first()
            if not db_item:
                db_item = ItemMaster(tag_id=tag_id)

            db_item.serial_number = item.get('serial_number')
            db_item.rental_class_num = item.get('rental_class_num')
            db_item.client_name = item.get('client_name')
            db_item.common_name = item.get('common_name')
            db_item.quality = item.get('quality')
            db_item.bin_location = item.get('bin_location')
            raw_status = item.get('status')
            status = raw_status if raw_status else 'Unknown'
            db_item.status = status
            db_item.last_contract_num = item.get('last_contract_num')
            db_item.last_scanned_by = item.get('last_scanned_by')
            db_item.notes = item.get('notes')
            db_item.status_notes = item.get('status_notes')
            longitude = item.get('long')
            latitude = item.get('lat')
            db_item.longitude = float(longitude) if longitude and longitude.strip() else None
            db_item.latitude = float(latitude) if latitude and latitude.strip() else None
            db_item.date_last_scanned = validate_date(item.get('date_last_scanned'), 'date_last_scanned', tag_id)
            db_item.date_created = validate_date(item.get('date_created'), 'date_created', tag_id)
            db_item.date_updated = validate_date(item.get('date_updated'), 'date_updated', tag_id)

            session.merge(db_item)
        except Exception as e:
            logger.error(f"Error updating item {tag_id}: {str(e)}", exc_info=True)
            session.rollback()
            raise
    logger.info(f"Skipped {skipped} items due to missing or invalid data")

def update_transactions(session, transactions):
    logger.info(f"Updating {len(transactions)} transactions in id_transactions")
    skipped = 0
    for transaction in transactions:
        try:
            tag_id = transaction.get('tag_id')
            scan_date = transaction.get('scan_date')
            if not tag_id or not scan_date:
                logger.warning(f"Skipping transaction with missing tag_id or scan_date: {transaction}")
                skipped += 1
                continue

            scan_date_dt = validate_date(scan_date, 'scan_date', tag_id)
            if not scan_date_dt:
                skipped += 1
                continue

            db_transaction = session.query(Transaction).filter_by(
                tag_id=tag_id, scan_date=scan_date_dt
            ).first()
            if not db_transaction:
                db_transaction = Transaction(tag_id=tag_id, scan_date=scan_date_dt)

            db_transaction.scan_type = transaction.get('scan_type')
            db_transaction.contract_number = transaction.get('contract_number')
            db_transaction.client_name = transaction.get('client_name')
            db_transaction.notes = transaction.get('notes')
            db_transaction.rental_class_num = transaction.get('rental_class_id')
            db_transaction.common_name = transaction.get('common_name')
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
            longitude = transaction.get('long')
            latitude = transaction.get('lat')
            db_transaction.longitude = float(longitude) if longitude and longitude.strip() else None
            db_transaction.latitude = float(latitude) if latitude and latitude.strip() else None
            db_transaction.wet = to_bool(transaction.get('wet'))
            db_transaction.service_required = to_bool(transaction.get('service_required'))
            db_transaction.date_created = validate_date(transaction.get('date_created'), 'date_created', tag_id)
            db_transaction.date_updated = validate_date(transaction.get('date_updated'), 'date_updated', tag_id)

            session.merge(db_transaction)
        except Exception as e:
            logger.error(f"Error updating transaction {tag_id} at {scan_date}: {str(e)}", exc_info=True)
            logger.debug(f"Raw transaction data: {transaction}")
            session.rollback()
            raise
    logger.info(f"Skipped {skipped} transactions due to missing or invalid data")

def update_seed_data(session, seed_data):
    logger.info(f"Updating {len(seed_data)} items in seed_rental_classes")
    skipped = 0
    for item in seed_data:
        try:
            rental_class_id = item.get('rental_class_id')
            if not rental_class_id:
                logger.warning(f"Skipping seed item with missing rental_class_id: {item}")
                skipped += 1
                continue

            db_seed = session.query(SeedRentalClass).filter_by(rental_class_id=rental_class_id).first()
            if not db_seed:
                db_seed = SeedRentalClass(rental_class_id=rental_class_id)

            db_seed.common_name = item.get('common_name')
            db_seed.bin_location = item.get('bin_location')

            session.merge(db_seed)
        except Exception as e:
            logger.error(f"Error updating seed item {rental_class_id}: {str(e)}", exc_info=True)
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

                items = api_client.get_item_master()
                transactions = api_client.get_transactions()
                seed_data = api_client.get_seed_data()

                logger.info(f"Fetched {len(items)} items from item master")
                logger.info(f"Fetched {len(transactions)} transactions")
                logger.info(f"Fetched {len(seed_data)} items from seed data")
                logger.debug(f"Item master data sample: {items[:5] if items else 'No items'}")
                logger.debug(f"Transactions data sample: {transactions[:5] if transactions else 'No transactions'}")
                logger.debug(f"Seed data sample: {seed_data[:5] if seed_data else 'No seed data'}")

                if not items:
                    logger.warning("No items fetched from item master API. Check API endpoint or authentication.")
                if not transactions:
                    logger.warning("No transactions fetched from transactions API. Check API endpoint or authentication.")
                if not seed_data:
                    logger.warning("No seed data fetched from seed API. Check API endpoint or authentication.")

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
                    time.sleep(1)
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
    try:
        since_date = datetime.utcnow() - timedelta(seconds=INCREMENTAL_LOOKBACK_SECONDS)
        logger.info(f"Checking for updates since: {since_date.strftime('%Y-%m-%d %H:%M:%S')}")

        logger.info(f"Fetching item master data with since_date: {since_date}")
        items = api_client.get_item_master(since_date=since_date)
        logger.info(f"Fetched {len(items)} items from item master")
        logger.debug(f"Item master data sample: {items[:5] if items else 'No items'}")
        if not items:
            logger.info("No new items fetched from item master API.")

        logger.info(f"Fetching transactions data with since_date: {since_date}")
        transactions = api_client.get_transactions(since_date=since_date)
        logger.info(f"Fetched {len(transactions)} transactions")
        logger.debug(f"Transactions data sample: {transactions[:5] if transactions else 'No transactions'}")
        if not transactions:
            logger.info("No new transactions fetched from transactions API.")

        update_item_master(session, items)
        update_transactions(session, transactions)
        logger.info("Skipping seed data refresh (handled in full refresh)")

        session.commit()
        update_refresh_state('incremental_refresh', datetime.utcnow())
        logger.info("Incremental refresh completed successfully")
    except Exception as e:
        logger.error(f"Incremental refresh failed: {str(e)}", exc_info=True)
        session.rollback()
        raise
    finally:
        session.close()
        logger.debug("Incremental refresh session closed")

@refresh_bp.route('/refresh/full', methods=['POST'])
def full_refresh_endpoint():
    logger.info("Received request for full refresh via endpoint")
    session = db.session()
    try:
        logger.debug("Starting full refresh process")
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
        logger.debug("Full refresh endpoint session closed")

@refresh_bp.route('/refresh/incremental', methods=['POST'])
def incremental_refresh_endpoint():
    logger.info("Received request for incremental refresh via endpoint")
    session = db.session()
    try:
        logger.debug("Starting incremental refresh process")
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
        logger.debug("Incremental refresh endpoint session closed")

@refresh_bp.route('/clear_api_data', methods=['POST'])
def clear_api_data():
    logger.info("Received request for clear API data and refresh")
    session = db.session()
    try:
        logger.debug("Starting clear API data and refresh process")
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
        logger.debug("Clear API data endpoint session closed")