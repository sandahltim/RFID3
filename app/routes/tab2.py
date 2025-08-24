from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db, cache
from ..models.db_models import Transaction, ItemMaster
from ..services.api_client import APIClient
from sqlalchemy import func, desc, asc, text
from time import time
from datetime import datetime, timedelta, timezone
import logging
import sys

# Configure logging
logger = logging.getLogger('tab2')
logger.setLevel(logging.DEBUG)

# Remove existing handlers to avoid duplicates
logger.handlers = []

# File handler for rfid_dashboard.log
file_handler = logging.FileHandler('/home/tim/RFID3/logs/rfid_dashboard.log')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

tab2_bp = Blueprint('tab2', __name__)

# Version marker
logger.info("Deployed tab2.py version: 2025-05-29-v11")

@tab2_bp.route('/tab/2')
def tab2_view():
    session = None
    try:
        # Create a new session
        session = db.session()
        logger.info("Starting new session for tab2")
        current_app.logger.info("Starting new session for tab2")

        # Test database connection
        result = session.execute(text("SELECT 1")).fetchall()
        logger.info(f"Database connection test successful: {result}")

        # Debug: Fetch all contract numbers
        all_contracts = session.query(ItemMaster.last_contract_num).distinct().all()
        logger.debug(f"All distinct contract numbers in ItemMaster: {[c[0] for c in all_contracts]}")

        # Debug: Check statuses
        status_counts = session.query(
            ItemMaster.status,
            func.count(ItemMaster.tag_id)
        ).group_by(ItemMaster.status).all()
        logger.debug(f"Status counts in ItemMaster: {status_counts}")

        # Step 1: Base query without filters
        base_query = session.query(
            ItemMaster.last_contract_num,
            func.count(ItemMaster.tag_id).label('total_items')
        ).group_by(ItemMaster.last_contract_num)
        logger.debug(f"Base query SQL: {str(base_query)}")
        base_results = base_query.all()
        logger.debug(f"Base query results: {[(r.last_contract_num, r.total_items) for r in base_results]}")

        # Get and validate sort parameter (default to no sort for initial load)
        sort = request.args.get('sort', None)
        contracts_query = base_query.filter(
            func.lower(ItemMaster.status).in_(['on rent', 'delivered']),
            ItemMaster.last_contract_num.isnot(None),
            ItemMaster.last_contract_num != '00000',
            ~func.trim(ItemMaster.last_contract_num).op('REGEXP')('^L[0-9]+$')
        ).having(
            func.count(ItemMaster.tag_id) > 0
        )

        contracts_query_results = contracts_query.all()
        logger.info(f"Raw contracts query result: {[(c.last_contract_num, c.total_items) for c in contracts_query_results]}")
        current_app.logger.info(f"Raw contracts query result: {[(c.last_contract_num, c.total_items) for c in contracts_query_results]}")

        contracts = []
        now = datetime.now(timezone.utc)
        for contract_number, total_items in contracts_query_results:
            logger.debug(f"Processing contract: {contract_number}")
            latest_transaction = session.query(
                Transaction.client_name,
                Transaction.scan_date
            ).filter(
                Transaction.contract_number == contract_number,
                Transaction.scan_type == 'Rental'
            ).order_by(
                desc(Transaction.scan_date)
            ).first()

            client_name = latest_transaction.client_name if latest_transaction else 'N/A'
            scan_datetime = latest_transaction.scan_date if latest_transaction and latest_transaction.scan_date else None
            scan_date = scan_datetime.isoformat() if scan_datetime else 'N/A'
            # Make scan_datetime timezone-aware for comparison with timezone-aware 'now'
            if scan_datetime and scan_datetime.tzinfo is None:
                scan_datetime = scan_datetime.replace(tzinfo=timezone.utc)
            is_stale = True if not scan_datetime else (now - scan_datetime > timedelta(days=12))
            logger.debug(f"Contract {contract_number} - Client: {client_name}, Scan Date: {scan_date}, Stale: {is_stale}")

            items_on_contract = session.query(func.count(ItemMaster.tag_id)).filter(
                ItemMaster.last_contract_num == contract_number,
                func.lower(ItemMaster.status).in_(['on rent', 'delivered'])
            ).scalar()

            total_items_inventory = session.query(func.count(ItemMaster.tag_id)).filter(
                ItemMaster.last_contract_num == contract_number
            ).scalar()

            contracts.append({
                'contract_number': contract_number,
                'client_name': client_name,
                'scan_date': scan_date,
                'items_on_contract': items_on_contract or 0,
                'total_items_inventory': total_items_inventory or 0,
                'is_stale': is_stale
            })

        contracts.sort(key=lambda x: x['contract_number'])  # Default sort for initial load
        logger.info(f"Fetched {len(contracts)} contracts for tab2: {[c['contract_number'] for c in contracts]}")
        current_app.logger.info(f"Fetched {len(contracts)} contracts for tab2: {[c['contract_number'] for c in contracts]}")

        # Force flush logs
        for handler in logger.handlers:
            handler.flush()
        for handler in current_app.logger.handlers:
            handler.flush()

        return render_template('tab2.html', contracts=contracts, error=None, sort=None, cache_bust=int(time()))
    except Exception as e:
        logger.error(f"Error rendering Tab 2: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error rendering Tab 2: {str(e)}", exc_info=True)
        # Force flush logs
        for handler in logger.handlers:
            handler.flush()
        for handler in current_app.logger.handlers:
            handler.flush()
        return render_template('tab2.html', contracts=[], error=str(e), cache_bust=int(time()))
    finally:
        if session:
            try:
                session.rollback()
            except Exception as e:
                logger.warning(f"Session rollback failed: {str(e)}")
            session.close()
            logger.debug("Session closed for tab2_view")

@tab2_bp.route('/tab/2/sort_contracts')
def sort_contracts():
    session = None
    try:
        session = db.session()
        logger.info("Starting new session for sort_contracts")

        # Get and validate sort parameter
        sort = request.args.get('sort', 'contract_number_asc')
        sort_parts = sort.split('_')
        if len(sort_parts) != 2 or sort_parts[1] not in ['asc', 'desc']:
            sort_column, sort_direction = 'contract_number', 'asc'
        else:
            sort_column, sort_direction = sort_parts[0], sort_parts[1]
        sort_direction = asc if sort_direction == 'asc' else desc

        # Step 1: Base query
        base_query = session.query(
            ItemMaster.last_contract_num,
            func.count(ItemMaster.tag_id).label('total_items')
        ).group_by(ItemMaster.last_contract_num)

        # Apply filters
        contracts_query = base_query.join(
            Transaction, ItemMaster.last_contract_num == Transaction.contract_number
        ).filter(
            func.lower(ItemMaster.status).in_(['on rent', 'delivered']),
            ItemMaster.last_contract_num.isnot(None),
            ItemMaster.last_contract_num != '00000',
            ~func.trim(ItemMaster.last_contract_num).op('REGEXP')('^L[0-9]+$')
        ).having(
            func.count(ItemMaster.tag_id) > 0
        )

        # Apply sorting only to top layer
        if sort_column == 'contract_number':
            contracts_query = contracts_query.order_by(sort_direction(ItemMaster.last_contract_num))
        elif sort_column == 'client_name':
            contracts_query = contracts_query.order_by(sort_direction(Transaction.client_name))
        elif sort_column == 'scan_date':
            contracts_query = contracts_query.order_by(sort_direction(func.max(Transaction.scan_date)))

        contracts_query_results = contracts_query.all()
        logger.info(f"Sorted contracts query result: {[(c.last_contract_num, c.total_items) for c in contracts_query_results]}")
        current_app.logger.info(f"Sorted contracts query result: {[(c.last_contract_num, c.total_items) for c in contracts_query_results]}")

        contracts = []
        now = datetime.now(timezone.utc)
        for contract_number, total_items in contracts_query_results:
            logger.debug(f"Processing contract: {contract_number}")
            latest_transaction = session.query(
                Transaction.client_name,
                Transaction.scan_date
            ).filter(
                Transaction.contract_number == contract_number,
                Transaction.scan_type == 'Rental'
            ).order_by(
                desc(Transaction.scan_date)
            ).first()

            client_name = latest_transaction.client_name if latest_transaction else 'N/A'
            scan_datetime = latest_transaction.scan_date if latest_transaction and latest_transaction.scan_date else None
            scan_date = scan_datetime.isoformat() if scan_datetime else 'N/A'
            # Make scan_datetime timezone-aware for comparison with timezone-aware 'now'
            if scan_datetime and scan_datetime.tzinfo is None:
                scan_datetime = scan_datetime.replace(tzinfo=timezone.utc)
            is_stale = True if not scan_datetime else (now - scan_datetime > timedelta(days=12))
            logger.debug(f"Contract {contract_number} - Client: {client_name}, Scan Date: {scan_date}, Stale: {is_stale}")

            items_on_contract = session.query(func.count(ItemMaster.tag_id)).filter(
                ItemMaster.last_contract_num == contract_number,
                func.lower(ItemMaster.status).in_(['on rent', 'delivered'])
            ).scalar()

            total_items_inventory = session.query(func.count(ItemMaster.tag_id)).filter(
                ItemMaster.last_contract_num == contract_number
            ).scalar()

            contracts.append({
                'contract_number': contract_number,
                'client_name': client_name,
                'scan_date': scan_date,
                'items_on_contract': items_on_contract or 0,
                'total_items_inventory': total_items_inventory or 0,
                'is_stale': is_stale
            })

        logger.info(f"Returned {len(contracts)} sorted contracts for tab2")
        return jsonify({'contracts': contracts, 'sort': sort})
    except Exception as e:
        logger.error(f"Error sorting contracts: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error sorting contracts: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            try:
                session.rollback()
            except Exception as e:
                logger.warning(f"Session rollback failed: {str(e)}")
            session.close()
            logger.debug("Session closed for sort_contracts")

@tab2_bp.route('/tab/2/common_names')
def tab2_common_names():
    contract_number = request.args.get('contract_number')
    page = int(request.args.get('page', 1))
    per_page = 10
    sort = request.args.get('sort', '')

    logger.info(f"Fetching common names for contract_number={contract_number}, page={page}, sort={sort}")
    current_app.logger.info(f"Fetching common names for contract_number={contract_number}, page={page}, sort={sort}")

    if not contract_number:
        logger.error("Missing required parameter: contract_number is required")
        current_app.logger.error("Missing required parameter: contract_number is required")
        return jsonify({'error': 'Contract number is required'}), 400

    session = None
    try:
        session = db.session()
        logger.info("Successfully created session for tab2_common_names")

        # Test database connection
        session.execute(text("SELECT 1"))
        logger.info("Database connection test successful in tab2_common_names")

        # Define the query with the on_contracts alias
        on_contracts = func.count(ItemMaster.tag_id).label('on_contracts')
        common_names_query = session.query(
            ItemMaster.common_name,
            on_contracts
        ).filter(
            ItemMaster.last_contract_num == contract_number,
            func.lower(ItemMaster.status).in_(['on rent', 'delivered'])
        ).group_by(
            ItemMaster.common_name
        )

        # Apply sorting (unchanged for nested layers)
        if sort == 'name_asc':
            common_names_query = common_names_query.order_by(asc(func.lower(ItemMaster.common_name)))
        elif sort == 'name_desc':
            common_names_query = common_names_query.order_by(desc(func.lower(ItemMaster.common_name)))
        elif sort == 'on_contracts_asc':
            common_names_query = common_names_query.order_by(asc(on_contracts))
        elif sort == 'on_contracts_desc':
            common_names_query = common_names_query.order_by(desc(on_contracts))
        elif sort == 'total_items_inventory_asc':
            common_names_query = common_names_query.order_by(asc('total_items_inventory'))
        elif sort == 'total_items_inventory_desc':
            common_names_query = common_names_query.order_by(desc('total_items_inventory'))

        logger.debug(f"Common names query: {str(common_names_query)}")
        common_names_all = common_names_query.all()

        logger.debug(f"Common names for contract {contract_number}: {[(name, count) for name, count in common_names_all]}")
        current_app.logger.debug(f"Common names for contract {contract_number}: {[(name, count) for name, count in common_names_all]}")

        common_names = []
        for name, on_contracts_count in common_names_all:
            if not name:
                continue

            total_items_inventory = session.query(func.count(ItemMaster.tag_id)).filter(
                ItemMaster.common_name == name
            ).scalar()

            common_names.append({
                'name': name,
                'on_contracts': on_contracts_count or 0,
                'total_items_inventory': total_items_inventory or 0
            })

        # Apply sorting for computed fields
        if sort in ['total_items_inventory_asc', 'total_items_inventory_desc']:
            sort_field = sort.split('_')[0]
            sort_direction = sort.split('_')[-1]
            common_names.sort(
                key=lambda x: x[sort_field],
                reverse=(sort_direction == 'desc')
            )

        total_common_names = len(common_names)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_common_names = common_names[start:end]

        logger.info(f"Returning {len(paginated_common_names)} common names for contract {contract_number}")
        current_app.logger.info(f"Returning {len(paginated_common_names)} common names for contract {contract_number}")
        return jsonify({
            'common_names': paginated_common_names,
            'total_common_names': total_common_names,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        logger.error(f"Error fetching common names for contract {contract_number}: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error fetching common names for contract {contract_number}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to fetch common names: {str(e)}'}), 500
    finally:
        if session:
            session.rollback()
            session.close()


@tab2_bp.route('/tab/2/update_status', methods=['POST'])
def update_status():
    session = None
    try:
        data = request.get_json()
        tag_id = data.get('tag_id')
        new_status = data.get('status')

        if not tag_id or not new_status:
            return jsonify({'error': 'Tag ID and status are required'}), 400

        valid_statuses = ['Ready to Rent', 'Sold', 'Repair', 'Needs to be Inspected', 'Wash', 'Wet']
        if new_status not in valid_statuses:
            return jsonify({'error': f'Status must be one of {", ".join(valid_statuses)}'}), 400

        session = db.session()
        item = session.query(ItemMaster).filter_by(tag_id=tag_id).first()
        if not item:
            return jsonify({'error': 'Item not found'}), 404

        if new_status in ['On Rent', 'Delivered']:
            return jsonify({'error': 'Status cannot be updated to "On Rent" or "Delivered" manually'}), 400

        current_time = datetime.now(timezone.utc)
        item.status = new_status
        item.date_last_scanned = current_time
        session.commit()

        try:
            api_client = APIClient()
            api_client.update_status(tag_id, new_status)
        except Exception as e:
            logger.error(f"Failed to update API status for tag_id {tag_id}: {str(e)}", exc_info=True)
            return jsonify({'error': f'Failed to update API: {str(e)}', 'local_update': 'success'}), 200

        return jsonify({'message': 'Status updated successfully'})
    except Exception as e:
        if session:
            session.rollback()
        logger.error(f"Error updating status for tag {tag_id if 'tag_id' in locals() else ''}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to update status'}), 500
    finally:
        if session:
            session.close()


@tab2_bp.route('/tab/2/bulk_update_status', methods=['POST'])
def bulk_update_status():
    session = None
    try:
        data = request.get_json()
        contract_number = data.get('contract_number')
        new_status = data.get('status')

        if not contract_number or not new_status:
            return jsonify({'error': 'Contract number and status are required'}), 400

        valid_statuses = ['Ready to Rent', 'Sold', 'Repair', 'Needs to be Inspected', 'Wash', 'Wet']
        if new_status not in valid_statuses:
            return jsonify({'error': f'Status must be one of {", ".join(valid_statuses)}'}), 400

        session = db.session()
        items = session.query(ItemMaster).filter(
            ItemMaster.last_contract_num == contract_number,
            func.lower(ItemMaster.status).in_(['on rent', 'delivered'])
        ).all()

        if not items:
            return jsonify({'error': 'No items found for the given contract'}), 404

        current_time = datetime.now(timezone.utc)
        api_client = APIClient()
        updated = 0
        for item in items:
            item.status = new_status
            item.date_last_scanned = current_time
            try:
                api_client.update_status(item.tag_id, new_status)
                updated += 1
            except Exception as e:
                logger.error(f"Failed to update API status for tag_id {item.tag_id}: {str(e)}", exc_info=True)

        session.commit()
        return jsonify({'message': f'Updated {updated} items'})
    except Exception as e:
        if session:
            session.rollback()
        logger.error(f"Error bulk updating status for contract {contract_number if 'contract_number' in locals() else ''}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to bulk update status'}), 500
    finally:
        if session:
            session.close()

@tab2_bp.route('/tab/2/data')
def tab2_data():
    contract_number = request.args.get('contract_number')
    common_name = request.args.get('common_name')
    page = int(request.args.get('page', 1))
    per_page = 10
    sort = request.args.get('sort', '')

    logger.info(f"Fetching items for contract_number={contract_number}, common_name={common_name}, page={page}, sort={sort}")
    current_app.logger.info(f"Fetching items for contract_number={contract_number}, common_name={common_name}, page={page}, sort={sort}")

    if not contract_number or not common_name:
        logger.error("Missing required parameters: contract number and common name are required")
        current_app.logger.error("Missing required parameters: contract number and common name are required")
        return jsonify({'error': 'Contract number and common name are required'}), 400

    session = None
    try:
        session = db.session()
        logger.info("Successfully created session for tab2_data")

        query = session.query(ItemMaster).filter(
            ItemMaster.last_contract_num == contract_number,
            ItemMaster.common_name == common_name,
            func.lower(ItemMaster.status).in_(['on rent', 'delivered'])
        )

        # Apply sorting (unchanged for nested layers)
        if sort == 'tag_id_asc':
            query = query.order_by(asc(ItemMaster.tag_id))
        elif sort == 'tag_id_desc':
            query = query.order_by(desc(ItemMaster.tag_id))
        elif sort == 'common_name_asc':
            query = query.order_by(asc(func.lower(ItemMaster.common_name)))
        elif sort == 'common_name_desc':
            query = query.order_by(desc(func.lower(ItemMaster.common_name)))
        elif sort == 'bin_location_asc':
            query = query.order_by(asc(func.lower(func.coalesce(ItemMaster.bin_location, ''))))
        elif sort == 'bin_location_desc':
            query = query.order_by(desc(func.lower(func.coalesce(ItemMaster.bin_location, ''))))
        elif sort == 'status_asc':
            query = query.order_by(asc(func.lower(ItemMaster.status)))
        elif sort == 'status_desc':
            query = query.order_by(desc(func.lower(ItemMaster.status)))
        elif sort == 'last_contract_asc':
            query = query.order_by(asc(func.lower(func.coalesce(ItemMaster.last_contract_num, ''))))
        elif sort == 'last_contract_desc':
            query = query.order_by(desc(func.lower(func.coalesce(ItemMaster.last_contract_num, ''))))
        elif sort == 'last_scanned_date_asc':
            query = query.order_by(asc(ItemMaster.date_last_scanned))
        elif sort == 'last_scanned_date_desc':
            query = query.order_by(desc(ItemMaster.date_last_scanned))

        total_items = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()

        items_data = []
        for item in items:
            last_scanned_date = item.date_last_scanned.isoformat() if item.date_last_scanned else 'N/A'
            items_data.append({
                'tag_id': item.tag_id,
                'common_name': item.common_name,
                'bin_location': item.bin_location,
                'status': item.status,
                'last_contract_num': item.last_contract_num,
                'last_scanned_date': last_scanned_date
            })

        logger.debug(f"Items for contract {contract_number}, common_name {common_name}: {len(items_data)} items")
        current_app.logger.debug(f"Items for contract {contract_number}, common_name {common_name}: {len(items_data)} items")

        return jsonify({
            'items': items_data,
            'total_items': total_items,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        logger.error(f"Error fetching items for contract {contract_number}, common_name {common_name}: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error fetching items for contract {contract_number}, common_name {common_name}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch items'}), 500
    finally:
        if session:
            session.rollback()
            session.close()

@tab2_bp.route('/tab/2/full_items_by_rental_class')
def full_items_by_rental_class():
    contract_number = request.args.get('category')
    common_name = request.args.get('common_name')

    if not contract_number or not common_name:
        logger.error("Category (contract_number) and common name are required")
        current_app.logger.error("Category (contract_number) and common name are required")
        return jsonify({'error': 'Category (contract_number) and common name are required'}), 400

    session = None
    try:
        session = db.session()
        logger.info("Successfully created session for full_items_by_rental_class")

        items_query = session.query(ItemMaster).filter(
            ItemMaster.last_contract_num == contract_number,
            ItemMaster.common_name == common_name
        ).order_by(ItemMaster.tag_id)

        items = items_query.all()
        items_data = []
        for item in items:
            last_scanned_date = item.date_last_scanned.isoformat() if item.date_last_scanned else 'N/A'
            items_data.append({
                'tag_id': item.tag_id,
                'common_name': item.common_name,
                'rental_class_num': item.rental_class_num,
                'bin_location': item.bin_location,
                'status': item.status,
                'last_contract_num': item.last_contract_num,
                'last_scanned_date': last_scanned_date,
                'quality': item.quality,
                'notes': item.notes
            })

        return jsonify({
            'items': items_data,
            'total_items': len(items_data)
        })
    except Exception as e:
        logger.error(f"Error fetching full items for contract {contract_number}, common_name {common_name}: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error fetching full items for contract {contract_number}, common_name {common_name}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch full items'}), 500
    finally:
        if session:
            session.rollback()
            session.close()
            