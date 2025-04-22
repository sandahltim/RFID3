import logging
from datetime import datetime, timedelta
from sqlalchemy.exc import SQLAlchemyError
from apscheduler.schedulers.background import BackgroundScheduler
from app.models.db_models import ItemMaster, Transaction, RentalClassMapping, db
from app.services.api_client import APIClient
from config import FULL_REFRESH_INTERVAL, INCREMENTAL_REFRESH_INTERVAL
from flask import Blueprint, jsonify, current_app

logger = logging.getLogger(__name__)

# Define the refresh blueprint
refresh_bp = Blueprint('refresh', __name__)

api_client = APIClient()

def update_item_master(session, items):
    logger.info(f"Updating {len(items)} items in id_item_master")
    for item in items:
        try:
            tag_id = item.get('tag_id')
            if not tag_id:
                logger.warning(f"Skipping item with missing tag_id: {item}")
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
            db_item.status = item.get('status')
            db_item.last_contract_num = item.get('last_contract_num')
            db_item.last_scanned_by = item.get('last_scanned_by')
            db_item.notes = item.get('notes')
            db_item.status_notes = item.get('status_notes')
            db_item.longitude = item.get('long')
            db_item.latitude = item.get('lat')
            db_item.date_last_scanned = item.get('date_last_scanned')

            session.merge(db_item)
        except Exception as e:
            logger.error(f"Error updating item {tag_id}: {str(e)}")
            session.rollback()
            raise

def update_transactions(session, transactions):
    logger.info(f"Updating {len(transactions)} transactions in id_transactions")
    for transaction in transactions:
        try:
            tag_id = transaction.get('tag_id')
            scan_date = transaction.get('scan_date')
            if not tag_id or not scan_date:
                logger.warning(f"Skipping transaction with missing tag_id or scan_date: {transaction}")
                continue

            db_transaction = session.query(Transaction).filter_by(
                tag_id=tag_id, scan_date=scan_date
            ).first()
            if not db_transaction:
                db_transaction = Transaction(tag_id=tag_id, scan_date=scan_date)

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
            db_transaction.dirty_or_mud = transaction.get('dirty_or_mud')
            db_transaction.leaves = transaction.get('leaves')
            db_transaction.oil = transaction.get('oil')
            db_transaction.mold = transaction.get('mold')
            db_transaction.stain = transaction.get('stain')
            db_transaction.oxidation = transaction.get('oxidation')
            db_transaction.other = transaction.get('other')
            db_transaction.rip_or_tear = transaction.get('rip_or_tear')
            db_transaction.sewing_repair_needed = transaction.get('sewing_repair_needed')
            db_transaction.grommet = transaction.get('grommet')
            db_transaction.rope = transaction.get('rope')
            db_transaction.buckle = transaction.get('buckle')
            db_transaction.longitude = transaction.get('long')
            db_transaction.latitude = transaction.get('lat')
            db_transaction.wet = transaction.get('wet')
            db_transaction.service_required = transaction.get('service_required')
            db_transaction.date_created = transaction.get('date_created')
            db_transaction.date_updated = transaction.get('date_updated')

            session.merge(db_transaction)
        except Exception as e:
            logger.error(f"Error updating transaction {tag_id} at {scan_date}: {str(e)}")
            session.rollback()
            raise

def update_seed_data(session, seeds):
    logger.info(f"Updating {len(seeds)} seeds in rental_class_mapping")
    for seed in seeds:
        try:
            rental_class_id = seed.get('rental_class_id')
            if not rental_class_id:
                logger.warning(f"Skipping seed with missing rental_class_id: {seed}")
                continue

            db_seed = session.query(RentalClassMapping).filter_by(rental_class_id=rental_class_id).first()
            if not db_seed:
                db_seed = RentalClassMapping(rental_class_id=rental_class_id)

            db_seed.category = seed.get('category', 'Unknown')  # Default to 'Unknown' if category is None
            db_seed.subcategory = seed.get('subcategory')
            db_seed.common_name = seed.get('common_name')
            db_seed.bin_location = seed.get('bin_location')

            session.merge(db_seed)
        except Exception as e:
            logger.error(f"Error updating seed {rental_class_id}: {str(e)}")
            session.rollback()
            raise

def full_refresh():
    logger.info("Starting full refresh")
    session = db.session()
    try:
        # Clear existing data
        deleted_items = session.query(ItemMaster).delete()
        deleted_transactions = session.query(Transaction).delete()
        deleted_mappings = session.query(RentalClassMapping).delete()
        logger.info(f"Deleted {deleted_items} items from id_item_master")
        logger.info(f"Deleted {deleted_transactions} transactions from id_transactions")
        logger.info(f"Deleted {deleted_mappings} mappings from rental_class_mappings")

        # Fetch all data without since_date
        items = api_client.get_item_master()
        transactions = api_client.get_transactions()
        seeds = api_client.get_seed_data()

        logger.info(f"Fetched {len(items)} items from item master")
        logger.info(f"Fetched {len(transactions)} transactions")
        logger.info(f"Fetched {len(seeds)} seeds")
        logger.debug(f"Item master data sample: {items[:5] if items else 'No items'}")
        logger.debug(f"Transactions data sample: {transactions[:5] if transactions else 'No transactions'}")
        logger.debug(f"Seed data sample: {seeds[:5] if seeds else 'No seeds'}")

        if not items:
            logger.warning("No items fetched from item master API. Check API endpoint or authentication.")
        if not transactions:
            logger.warning("No transactions fetched from transactions API. Check API endpoint or authentication.")
        if not seeds:
            logger.warning("No seeds fetched from seed API. Check API endpoint or authentication.")

        # Update database
        update_item_master(session, items)
        update_transactions(session, transactions)
        update_seed_data(session, seeds)

        session.commit()
        logger.info("Clear API data and full refresh completed successfully")
    except Exception as e:
        logger.error(f"Full refresh failed: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()
        logger.debug("Full refresh session closed")

def incremental_refresh():
    logger.info("Starting incremental refresh")
    session = db.session()
    try:
        # Use a since_date for incremental updates (last 30 days for testing)
        since_date = datetime.utcnow() - timedelta(days=30)  # Adjusted to 30 days for testing
        logger.info(f"Fetching item master data with since_date: {since_date}")
        items = api_client.get_item_master(since_date=since_date)
        logger.info(f"Fetched {len(items)} items from item master")
        logger.debug(f"Item master data sample: {items[:5] if items else 'No items'}")
        if not items:
            logger.warning("No items fetched from item master API. Check API endpoint or authentication.")

        logger.info(f"Fetching transactions data with since_date: {since_date}")
        transactions = api_client.get_transactions(since_date=since_date)
        logger.info(f"Fetched {len(transactions)} transactions")
        logger.debug(f"Transactions data sample: {transactions[:5] if transactions else 'No transactions'}")
        if not transactions:
            logger.warning("No transactions fetched from transactions API. Check API endpoint or authentication.")

        logger.info("Fetching seed data")
        seeds = api_client.get_seed_data()  # Removed since_date as seed data doesn't support filtering
        logger.info(f"Fetched {len(seeds)} seeds")
        logger.debug(f"Seed data sample: {seeds[:5] if seeds else 'No seeds'}")
        if not seeds:
            logger.warning("No seeds fetched from seed API. Check API endpoint or authentication.")

        update_item_master(session, items)
        update_transactions(session, transactions)
        update_seed_data(session, seeds)

        session.commit()
        logger.info("Incremental refresh completed successfully")
    except Exception as e:
        logger.error(f"Incremental refresh failed: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()
        logger.debug("Incremental refresh session closed")

def init_scheduler(app):
    scheduler = BackgroundScheduler()

    def run_with_context():
        with app.app_context():
            incremental_refresh()

    scheduler.add_job(
        run_with_context,
        'interval',
        seconds=INCREMENTAL_REFRESH_INTERVAL,
        id='incremental_refresh'
    )

    scheduler.add_job(
        full_refresh,
        'interval',
        seconds=FULL_REFRESH_INTERVAL,
        id='full_refresh'
    )

    scheduler.start()
    logger.info("Scheduler started with incremental and full refresh jobs")

    return scheduler

# Define the route for clearing API data and refreshing
@refresh_bp.route('/clear_api_data', methods=['POST'])
def clear_api_data():
    try:
        current_app.logger.info("Starting clear API data and refresh")
        full_refresh()
        current_app.logger.info("Clear API data and refresh completed successfully")
        return jsonify({'status': 'success', 'message': 'API data cleared and refreshed successfully'})
    except Exception as e:
        current_app.logger.error(f"Clear API data and refresh failed: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500