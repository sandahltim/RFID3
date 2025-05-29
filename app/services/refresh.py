import logging
import requests
from datetime import datetime
from flask import Blueprint, current_app
from .. import db, cache
from ..models.db_models import ItemMaster, Transaction, RefreshState
from .api_client import APIClient
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Configure logging
logger = logging.getLogger('app.services.refresh')
logger.setLevel(logging.DEBUG)

refresh_bp = Blueprint('refresh', __name__)

# API Client
api_client = APIClient()

def update_transactions(session, transactions):
    """Update or insert transactions and corresponding item master records."""
    logger.info(f"Updating {len(transactions)} transactions in id_transactions")
    
    for i, transaction in enumerate(transactions):
        try:
            # Extract transaction data
            scan_date = transaction.get('scan_date')
            if isinstance(scan_date, str):
                scan_date = datetime.strptime(scan_date, '%Y-%m-%d %H:%M:%S')
            
            # Check if transaction already exists
            existing_transaction = session.query(Transaction).filter(
                Transaction.tag_id == transaction['tag_id'],
                Transaction.scan_date == scan_date
            ).first()
            
            if not existing_transaction:
                # Create new transaction
                new_transaction = Transaction(
                    contract_number=transaction.get('contract_number'),
                    tag_id=transaction['tag_id'],
                    scan_type=transaction.get('scan_type'),
                    scan_date=scan_date,
                    client_name=transaction.get('client_name'),
                    common_name=transaction.get('common_name'),
                    bin_location=transaction.get('bin_location'),
                    status=transaction.get('status'),
                    scan_by=transaction.get('scan_by'),
                    location_of_repair=transaction.get('location_of_repair'),
                    quality=transaction.get('quality'),
                    dirty_or_mud=transaction.get('dirty_or_mud'),
                    leaves=transaction.get('leaves'),
                    oil=transaction.get('oil'),
                    mold=transaction.get('mold'),
                    stain=transaction.get('stain'),
                    oxidation=transaction.get('oxidation'),
                    other=transaction.get('other'),
                    rip_or_tear=transaction.get('rip_or_tear'),
                    sewing_repair_needed=transaction.get('sewing_repair_needed'),
                    grommet=transaction.get('grommet'),
                    rope=transaction.get('rope'),
                    buckle=transaction.get('buckle'),
                    date_created=transaction.get('date_created'),
                    date_updated=transaction.get('date_updated'),
                    uuid_accounts_fk=transaction.get('uuid_accounts_fk'),
                    serial_number=transaction.get('serial_number'),
                    rental_class_num=transaction.get('rental_class_id'),
                    longitude=float(transaction.get('long', 0.0)) if transaction.get('long') else None,
                    latitude=float(transaction.get('lat', 0.0)) if transaction.get('lat') else None,
                    wet=transaction.get('wet'),
                    service_required=transaction.get('service_required'),
                    notes=transaction.get('notes')
                )
                session.add(new_transaction)
            
            # Update or insert corresponding ItemMaster record
            with session.no_autoflush:  # Prevent premature flushing
                existing_item = session.query(ItemMaster).filter(
                    ItemMaster.tag_id == transaction['tag_id']
                ).first()
            
            if existing_item:
                # Update existing ItemMaster record
                logger.debug(f"Updating existing ItemMaster for tag_id {transaction['tag_id']}")
                existing_item.common_name = transaction.get('common_name')
                existing_item.rental_class_num = transaction.get('rental_class_id')
                existing_item.quality = transaction.get('quality')
                existing_item.bin_location = transaction.get('bin_location')
                existing_item.status = transaction.get('status')
                existing_item.last_contract_num = transaction.get('contract_number', '00000')
                existing_item.last_scanned_by = transaction.get('scan_by')
                existing_item.notes = transaction.get('notes')
                existing_item.date_last_scanned = scan_date
                existing_item.date_updated = datetime.now()
            else:
                # Create new ItemMaster record
                logger.debug(f"Creating new ItemMaster for tag_id {transaction['tag_id']}")
                new_item = ItemMaster(
                    tag_id=transaction['tag_id'],
                    uuid_accounts_fk=transaction.get('uuid_accounts_fk'),
                    serial_number=transaction.get('serial_number'),
                    client_name=transaction.get('client_name'),
                    rental_class_num=transaction.get('rental_class_id'),
                    common_name=transaction.get('common_name'),
                    quality=transaction.get('quality'),
                    bin_location=transaction.get('bin_location'),
                    status=transaction.get('status'),
                    last_contract_num=transaction.get('contract_number', '00000'),
                    last_scanned_by=transaction.get('scan_by'),
                    notes=transaction.get('notes'),
                    status_notes=None,
                    longitude=float(transaction.get('long', 0.0)) if transaction.get('long') else None,
                    latitude=float(transaction.get('lat', 0.0)) if transaction.get('lat') else None,
                    date_last_scanned=scan_date,
                    date_created=datetime.now(),
                    date_updated=datetime.now()
                )
                session.add(new_item)
                
        except Exception as e:
            logger.error(f"Error updating transaction {transaction['tag_id']} at {scan_date}: {str(e)}", exc_info=True)
            session.rollback()
            continue

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((requests.exceptions.RequestException,))
)
def fetch_transactions(last_refresh):
    """Fetch transactions from API since last refresh."""
    params = {
        'filter[gt]': f"date_updated,gt,'{last_refresh}'",
        'sort': 'date_updated,asc'
    }
    return api_client._make_request("14223767938169346196", params)

def full_refresh():
    """Perform a full refresh of item master and transactions."""
    logger.info("Starting full refresh")
    session = None
    try:
        session = db.session()
        
        # Clear existing data
        session.query(Transaction).delete()
        session.query(ItemMaster).delete()
        session.commit()
        
        # Fetch all items
        items = api_client._make_request("14223767938169344381")
        logger.info(f"Fetched {len(items)} items for full refresh")
        
        for item in items:
            date_last_scanned = item.get('date_last_scanned')
            if isinstance(date_last_scanned, str):
                date_last_scanned = datetime.strptime(date_last_scanned, '%Y-%m-%d %H:%M:%S')
                
            new_item = ItemMaster(
                tag_id=item['tag_id'],
                uuid_accounts_fk=item.get('uuid_accounts_fk'),
                serial_number=item.get('serial_number'),
                client_name=item.get('client_name'),
                rental_class_num=item.get('rental_class_num'),
                common_name=item.get('common_name'),
                quality=item.get('quality'),
                bin_location=item.get('bin_location'),
                status=item.get('status'),
                last_contract_num=item.get('last_contract_num', '00000'),
                last_scanned_by=item.get('last_scanned_by'),
                notes=item.get('notes'),
                status_notes=item.get('status_notes'),
                longitude=float(item.get('longitude', 0.0)) if item.get('longitude') else None,
                latitude=float(item.get('latitude', 0.0)) if item.get('latitude') else None,
                date_last_scanned=date_last_scanned,
                date_created=item.get('date_created'),
                date_updated=item.get('date_updated')
            )
            session.add(new_item)
        
        # Fetch all transactions
        transactions = api_client._make_request("14223767938169346196")
        update_transactions(session, transactions)
        
        # Update refresh state
        refresh_state = session.query(RefreshState).first()
        if not refresh_state:
            refresh_state = RefreshState(last_refresh=datetime.now().isoformat())
            session.add(refresh_state)
        else:
            refresh_state.last_refresh = datetime.now().isoformat()
        
        session.commit()
        logger.info("Full refresh completed successfully")
        
    except Exception as e:
        logger.error(f"Full refresh failed: {str(e)}", exc_info=True)
        if session:
            session.rollback()
    finally:
        if session:
            session.close()

def incremental_refresh():
    """Perform an incremental refresh of transactions."""
    logger.info("Starting incremental refresh")
    session = None
    try:
        session = db.session()
        
        # Get last refresh time
        refresh_state = session.query(RefreshState).first()
        last_refresh = refresh_state.last_refresh if refresh_state else '2023-01-01 00:00:00'
        
        # Fetch new transactions
        transactions = fetch_transactions(last_refresh)
        logger.info(f"Fetched {len(transactions)} new transactions for incremental refresh")
        
        # Update transactions
        update_transactions(session, transactions)
        
        # Update refresh state
        if not refresh_state:
            refresh_state = RefreshState(last_refresh=datetime.now().isoformat())
            session.add(refresh_state)
        else:
            refresh_state.last_refresh = datetime.now().isoformat()
        
        session.commit()
        logger.info("Incremental refresh completed successfully")
        
    except Exception as e:
        logger.error(f"Incremental refresh failed: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        raise
    finally:
        if session:
            session.close()
        logger.debug("Incremental refresh session closed")

@refresh_bp.route('/refresh/full', methods=['POST'])
def trigger_full_refresh():
    """Trigger a full refresh."""
    try:
        full_refresh()
        return {'status': 'Full refresh triggered successfully'}, 200
    except Exception as e:
        logger.error(f"Full refresh endpoint failed: {str(e)}", exc_info=True)
        return {'error': str(e)}, 500

@refresh_bp.route('/refresh/incremental', methods=['POST'])
def trigger_incremental_refresh():
    """Trigger an incremental refresh."""
    try:
        incremental_refresh()
        return {'status': 'Incremental refresh triggered successfully'}, 200
    except Exception as e:
        logger.error(f"Incremental refresh endpoint failed: {str(e)}", exc_info=True)
        return {'error': str(e)}, 500