from flask import Blueprint, jsonify
from app.models.db_models import ItemMaster, Transaction, SeedRentalClass, RefreshState
from app.services.api_client import APIClient
from app import db, cache
from datetime import datetime

refresh_bp = Blueprint('refresh', __name__)

def update_item_master(items):
    current_app.logger.info(f"Updating {len(items)} items in id_item_master")
    for item in items:
        try:
            db.session.merge(ItemMaster(
                tag_id=item.get('tag_id'),
                uuid_accounts_fk=item.get('uuid_accounts_fk'),
                serial_number=item.get('serial_number'),
                client_name=item.get('client_name'),
                rental_class_num=item.get('rental_class_num'),
                common_name=item.get('common_name'),
                quality=item.get('quality'),
                bin_location=item.get('bin_location'),
                status=item.get('status'),
                last_contract_num=item.get('last_contract_num'),
                last_scanned_by=item.get('last_scanned_by'),
                notes=item.get('notes'),
                status_notes=item.get('status_notes'),
                longitude=item.get('longitude'),
                latitude=item.get('latitude'),
                date_last_scanned=item.get('date_last_scanned'),
                date_created=item.get('date_created'),
                date_updated=item.get('date_updated')
            ))
        except Exception as e:
            current_app.logger.error(f"Failed to update item {item.get('tag_id')}: {str(e)}")
    db.session.commit()

def update_transactions(transactions):
    current_app.logger.info(f"Updating {len(transactions)} transactions in id_transactions")
    for trans in transactions:
        try:
            db.session.merge(Transaction(
                contract_number=trans.get('contract_number'),
                tag_id=trans.get('tag_id'),
                scan_type=trans.get('scan_type'),
                scan_date=trans.get('scan_date'),
                client_name=trans.get('client_name'),
                common_name=trans.get('common_name'),
                bin_location=trans.get('bin_location'),
                status=trans.get('status'),
                scan_by=trans.get('scan_by'),
                location_of_repair=trans.get('location_of_repair'),
                quality=trans.get('quality'),
                dirty_or_mud=trans.get('dirty_or_mud'),
                leaves=trans.get('leaves'),
                oil=trans.get('oil'),
                mold=trans.get('mold'),
                stain=trans.get('stain'),
                oxidation=trans.get('oxidation'),
                other=trans.get('other'),
                rip_or_tear=trans.get('rip_or_tear'),
                sewing_repair_needed=trans.get('sewing_repair_needed'),
                grommet=trans.get('grommet'),
                rope=trans.get('rope'),
                buckle=trans.get('buckle'),
                date_created=trans.get('date_created'),
                date_updated=trans.get('date_updated'),
                uuid_accounts_fk=trans.get('uuid_accounts_fk'),
                serial_number=trans.get('serial_number'),
                rental_class_num=trans.get('rental_class_num'),
                longitude=trans.get('longitude'),
                latitude=trans.get('latitude'),
                wet=trans.get('wet'),
                service_required=trans.get('service_required'),
                notes=trans.get('notes')
            ))
        except Exception as e:
            current_app.logger.error(f"Failed to update transaction {trans.get('contract_number')}: {str(e)}")
    db.session.commit()

def update_seed_data(seeds):
    current_app.logger.info(f"Updating {len(seeds)} seeds in seed_rental_classes")
    for seed in seeds:
        try:
            db.session.merge(SeedRentalClass(
                rental_class_id=seed.get('rental_class_id'),
                common_name=seed.get('common_name'),
                bin_location=seed.get('bin_location')
            ))
        except Exception as e:
            current_app.logger.error(f"Failed to update seed {seed.get('rental_class_id')}: {str(e)}")
    db.session.commit()

@refresh_bp.route('/full_refresh', methods=['POST'])
def full_refresh():
    try:
        current_app.logger.info("Starting full refresh")
        client = APIClient()
        current_app.logger.info("Fetching item master data")
        items = client.get_item_master()
        current_app.logger.info("Fetching transactions data")
        transactions = client.get_transactions()
        current_app.logger.info("Fetching seed data")
        seeds = client.get_seed_data()
        
        current_app.logger.info("Updating database")
        with db.session.begin():
            update_item_master(items)
            update_transactions(transactions)
            update_seed_data(seeds)
            
            state = RefreshState.query.first()
            if not state:
                state = RefreshState(last_refresh=datetime.utcnow().isoformat())
                db.session.add(state)
            else:
                state.last_refresh = datetime.utcnow().isoformat()
        
        cache.clear()
        current_app.logger.info("Full refresh completed successfully")
        return jsonify({'status': 'success', 'message': 'Database refreshed'})
    except Exception as e:
        current_app.logger.error(f"Full refresh failed: {str(e)}")
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

def incremental_refresh():
    try:
        current_app.logger.info("Starting incremental refresh")
        state = RefreshState.query.first()
        since_date = state.last_refresh if state else None
        
        client = APIClient()
        items = client.get_item_master(since_date)
        transactions = client.get_transactions(since_date)
        seeds = client.get_seed_data(since_date)
        
        with db.session.begin():
            update_item_master(items)
            update_transactions(transactions)
            update_seed_data(seeds)
            
            if state:
                state.last_refresh = datetime.utcnow().isoformat()
            else:
                state = RefreshState(last_refresh=datetime.utcnow().isoformat())
                db.session.add(state)
        
        cache.clear()
        current_app.logger.info("Incremental refresh completed successfully")
    except Exception as e:
        current_app.logger.error(f"Incremental refresh failed: {str(e)}")
        db.session.rollback()