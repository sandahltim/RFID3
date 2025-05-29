from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db, cache
from ..models.db_models import Transaction, ItemMaster
from sqlalchemy import func, desc, asc
from time import time
import logging
import sys

# Configure logging
logger = logging.getLogger('tab2')
logger.setLevel(logging.DEBUG)

# Remove existing handlers to avoid duplicates
logger.handlers = []

# File handler for rfid_dashboard.log
file_handler = logging.FileHandler('/home/tim/test_rfidpi/logs/rfid_dashboard.log')
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
logger.info("Deployed tab2.py version: 2025-05-29-v6")

@tab2_bp.route('/tab/2')
def tab2_view():
    session = None
    try:
        session = db.session()
        logger.info("Starting new session for tab2")
        current_app.logger.info("Starting new session for tab2")

        # Test database connection
        session.execute("SELECT 1")
        logger.info("Database connection test successful")

        # Debug: Fetch all contract numbers
        all_contracts = session.query(ItemMaster.last_contract_num).distinct().all()
        logger.debug(f"All distinct contract numbers in ItemMaster: {[c[0] for c in all_contracts]}")

        # Break down query for debugging
        contracts_query = session.query(
            ItemMaster.last_contract_num,
            func.count(ItemMaster.tag_id).label('total_items')
        ).filter(
            func.lower(ItemMaster.status).in_(['on rent', 'delivered']),  # Case-insensitive
            ItemMaster.last_contract_num.isnot(None),
            ItemMaster.last_contract_num != '00000',
            ~func.trim(ItemMaster.last_contract_num).op('REGEXP')('^L[0-9]+$')
        ).group_by(
            ItemMaster.last_contract_num
        ).having(
            func.count(ItemMaster.tag_id) > 0
        )

        logger.debug(f"Contracts query SQL: {str(contracts_query)}")
        contracts_query = contracts_query.all()
        logger.info(f"Raw contracts query result: {[(c.last_contract_num, c.total_items) for c in contracts_query]}")
        current_app.logger.info(f"Raw contracts query result: {[(c.last_contract_num, c.total_items) for c in contracts_query]}")

        contracts = []
        for contract_number, total_items in contracts_query:
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
            scan_date = latest_transaction.scan_date.isoformat() if latest_transaction and latest_transaction.scan_date else 'N/A'

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
                'total_items_inventory': total_items_inventory or 0
            })

        contracts.sort(key=lambda x: x['contract_number'])
        logger.info(f"Fetched {len(contracts)} contracts for tab2: {[c['contract_number'] for c in contracts]}")
        current_app.logger.info(f"Fetched {len(contracts)} contracts for tab2: {[c['contract_number'] for c in contracts]}")
        return render_template('tab2.html', contracts=contracts, cache_bust=int(time()))
    except Exception as e:
        logger.error(f"Error rendering Tab 2: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error rendering Tab 2: {str(e)}", exc_info=True)
        return render_template('tab2.html', contracts=[], error=str(e), cache_bust=int(time()))
    finally:
        if session:
            session.close()

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
        session.execute("SELECT 1")
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

        # Apply sorting
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

        # Apply sorting
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
            session.close()