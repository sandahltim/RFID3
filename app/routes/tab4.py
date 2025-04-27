from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db, cache
from ..models.db_models import Transaction, ItemMaster, HandCountedItems
from sqlalchemy import func, desc, asc
from time import time
from datetime import datetime
import logging
import sys

# Configure logging
logger = logging.getLogger('tab4')
logger.setLevel(logging.DEBUG)  # Change to DEBUG for more detailed logging

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

tab4_bp = Blueprint('tab4', __name__)

# Version marker
logger.info("Deployed tab4.py version: 2025-04-27-v10")

@tab4_bp.route('/tab/4')
def tab4_view():
    logger.info("Route /tab/4 accessed")
    current_app.logger.info("Route /tab/4 accessed")
    try:
        logger.info("Attempting to create database session")
        current_app.logger.info("Attempting to create database session")
        session = db.session()
        logger.info("Database session created successfully")
        current_app.logger.info("Database session created successfully")

        # Verify database connection
        logger.info("Testing database connection")
        current_app.logger.info("Testing database connection")
        session.execute("SELECT 1")
        logger.info("Database connection test successful")
        current_app.logger.info("Database connection test successful")

        # Debug: Fetch all contract numbers to see what's in the database
        all_contracts = session.query(ItemMaster.last_contract_num).distinct().all()
        logger.debug(f"All distinct contract numbers in ItemMaster: {[c[0] for c in all_contracts]}")

        # Debug: Check all items to see their contract numbers and statuses
        all_items = session.query(ItemMaster).all()
        logger.debug(f"All items in ItemMaster: {len(all_items)} items")
        for item in all_items:
            logger.debug(f"Item: tag_id={item.tag_id}, last_contract_num='{item.last_contract_num}', status={item.status}")

        # Debug: Check items with 'L3' specifically
        l3_items = session.query(ItemMaster).filter(
            func.trim(ItemMaster.last_contract_num) == 'L3'
        ).all()
        logger.debug(f"Items with last_contract_num 'L3': {len(l3_items)}")
        for item in l3_items:
            logger.debug(f"Item with last_contract_num 'L3': tag_id={item.tag_id}, status={item.status}, last_contract_num='{item.last_contract_num}'")

        # Debug: Check items starting with 'L' or 'l' with status 'On Rent' or 'Delivered'
        laundry_items = session.query(ItemMaster).filter(
            func.lower(func.trim(ItemMaster.last_contract_num)).like('l%'),
            ItemMaster.status.in_(['On Rent', 'Delivered'])
        ).all()
        logger.debug(f"Items with last_contract_num starting with 'l' and status in ('On Rent', 'Delivered'): {len(laundry_items)}")
        for item in laundry_items:
            logger.debug(f"Laundry item: tag_id={item.tag_id}, last_contract_num='{item.last_contract_num}', status={item.status}")

        # Fetch laundry contracts from id_item_master (contract numbers starting with 'L' or 'l')
        logger.info("Executing contracts query")
        current_app.logger.info("Executing contracts query")
        contracts_query = session.query(
            ItemMaster.last_contract_num,
            func.count(ItemMaster.tag_id).label('total_items')
        ).filter(
            func.lower(func.trim(ItemMaster.last_contract_num)).like('l%'),
            ItemMaster.status.in_(['On Rent', 'Delivered']),
            ItemMaster.last_contract_num != None,
            ItemMaster.last_contract_num != '00000'
        ).group_by(
            ItemMaster.last_contract_num
        ).having(
            func.count(ItemMaster.tag_id) > 0
        ).all()

        logger.info(f"Raw laundry contracts query result: {[(c.last_contract_num, c.total_items) for c in contracts_query]}")
        current_app.logger.info(f"Raw laundry contracts query result: {[(c.last_contract_num, c.total_items) for c in contracts_query]}")

        # Debug: If no contracts found, try without status filter
        if not contracts_query:
            logger.warning("No contracts found with status in ('On Rent', 'Delivered'). Trying without status filter.")
            contracts_query = session.query(
                ItemMaster.last_contract_num,
                func.count(ItemMaster.tag_id).label('total_items')
            ).filter(
                func.lower(func.trim(ItemMaster.last_contract_num)).like('l%'),
                ItemMaster.last_contract_num != None,
                ItemMaster.last_contract_num != '00000'
            ).group_by(
                ItemMaster.last_contract_num
            ).having(
                func.count(ItemMaster.tag_id) > 0
            ).all()
            logger.info(f"Query result without status filter: {[(c.last_contract_num, c.total_items) for c in contracts_query]}")

        contracts = []
        for contract_number, total_items in contracts_query:
            logger.debug(f"Processing contract: {contract_number} with {total_items} items")
            current_app.logger.debug(f"Processing contract: {contract_number} with {total_items} items")

            # Fetch additional details from id_transactions for this contract
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
            logger.debug(f"Contract {contract_number}: client_name={client_name}, scan_date={scan_date}")
            current_app.logger.debug(f"Contract {contract_number}: client_name={client_name}, scan_date={scan_date}")

            # Count items on this contract
            items_on_contract = session.query(func.count(ItemMaster.tag_id)).filter(
                ItemMaster.last_contract_num == contract_number,
                ItemMaster.status.in_(['On Rent', 'Delivered'])
            ).scalar()

            # Total items in inventory for this contract
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
        logger.info(f"Fetched {len(contracts)} laundry contracts for tab4: {[c['contract_number'] for c in contracts]}")
        current_app.logger.info(f"Fetched {len(contracts)} laundry contracts for tab4: {[c['contract_number'] for c in contracts]}")
        session.close()
        logger.info(f"Rendering tab4.html with contracts: {[c['contract_number'] for c in contracts]}")
        current_app.logger.info(f"Rendering tab4.html with contracts: {[c['contract_number'] for c in contracts]}")
        return render_template('tab4.html', contracts=contracts, cache_bust=int(time()))
    except Exception as e:
        logger.error(f"Error rendering Tab 4: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error rendering Tab 4: {str(e)}", exc_info=True)
        if 'session' in locals():
            session.close()
        return render_template('tab4.html', contracts=[], cache_bust=int(time()))

@tab4_bp.route('/tab/4/common_names')
def tab4_common_names():
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

    try:
        session = db.session()

        # Fetch common names for items on this contract
        common_names_query = session.query(
            ItemMaster.common_name,
            func.count(ItemMaster.tag_id).label('on_contracts')
        ).filter(
            ItemMaster.last_contract_num == contract_number,
            ItemMaster.status.in_(['On Rent', 'Delivered'])
        ).group_by(
            ItemMaster.common_name
        )

        # Apply sorting
        if sort == 'name_asc':
            common_names_query = common_names_query.order_by(asc(func.lower(ItemMaster.common_name)))
        elif sort == 'name_desc':
            common_names_query = common_names_query.order_by(desc(func.lower(ItemMaster.common_name)))
        elif sort == 'on_contracts_asc':
            common_names_query = common_names_query.order_by(asc('on_contracts'))
        elif sort == 'on_contracts_desc':
            common_names_query = common_names_query.order_by(desc('on_contracts'))
        elif sort == 'total_items_inventory_asc':
            common_names_query = common_names_query.order_by(asc('total_items_inventory'))
        elif sort == 'total_items_inventory_desc':
            common_names_query = common_names_query.order_by(desc('total_items_inventory'))

        common_names_all = common_names_query.all()

        logger.debug(f"Common names for laundry contract {contract_number}: {[(name, count) for name, count in common_names_all]}")
        current_app.logger.debug(f"Common names for laundry contract {contract_number}: {[(name, count) for name, count in common_names_all]}")

        common_names = []
        for name, on_contracts in common_names_all:
            if not name:
                continue

            # Total items in inventory for this common name
            total_items_inventory = session.query(func.count(ItemMaster.tag_id)).filter(
                ItemMaster.common_name == name
            ).scalar()

            common_names.append({
                'name': name,
                'on_contracts': on_contracts or 0,
                'total_items_inventory': total_items_inventory or 0
            })

        # Apply sorting for computed fields if necessary
        if sort in ['total_items_inventory_asc', 'total_items_inventory_desc']:
            sort_field = sort.split('_')[0]
            sort_direction = sort.split('_')[-1]
            common_names.sort(
                key=lambda x: x[sort_field],
                reverse=(sort_direction == 'desc')
            )

        # Paginate common names
        total_common_names = len(common_names)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_common_names = common_names[start:end]

        session.close()
        logger.info(f"Returning {len(paginated_common_names)} common names for contract {contract_number}")
        current_app.logger.info(f"Returning {len(paginated_common_names)} common names for contract {contract_number}")
        return jsonify({
            'common_names': paginated_common_names,
            'total_common_names': total_common_names,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        logger.error(f"Error fetching common names for contract {contract_number}: {str(e)}")
        current_app.logger.error(f"Error fetching common names for contract {contract_number}: {str(e)}")
        if 'session' in locals():
            session.close()
        return jsonify({'error': 'Failed to fetch common names'}), 500

@tab4_bp.route('/tab/4/data')
def tab4_data():
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

    try:
        session = db.session()

        # Fetch items on this contract
        query = session.query(ItemMaster).filter(
            ItemMaster.last_contract_num == contract_number,
            ItemMaster.common_name == common_name,
            ItemMaster.status.in_(['On Rent', 'Delivered'])
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

        # Paginate items
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

        logger.debug(f"Items for laundry contract {contract_number}, common_name {common_name}: {len(items_data)} items")
        current_app.logger.debug(f"Items for laundry contract {contract_number}, common_name {common_name}: {len(items_data)} items")

        session.close()
        return jsonify({
            'items': items_data,
            'total_items': total_items,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        logger.error(f"Error fetching items for contract {contract_number}, common_name {common_name}: {str(e)}")
        current_app.logger.error(f"Error fetching items for contract {contract_number}, common_name {common_name}: {str(e)}")
        if 'session' in locals():
            session.close()
        return jsonify({'error': 'Failed to fetch items'}), 500

@tab4_bp.route('/tab/4/hand_counted_items')
def tab4_hand_counted_items():
    contract_number = request.args.get('contract_number')
    logger.info(f"Fetching hand-counted items for contract_number={contract_number}")
    current_app.logger.info(f"Fetching hand-counted items for contract_number={contract_number}")
    try:
        session = db.session()
        items = session.query(HandCountedItems).filter(
            HandCountedItems.contract_number == contract_number
        ).all()
        session.close()
        logger.info(f"Found {len(items)} hand-counted items for contract {contract_number}")
        current_app.logger.info(f"Found {len(items)} hand-counted items for contract {contract_number}")

        # Render HTML rows for HTMX to insert into the table
        html = ""
        if not items:
            html = '<tr><td colspan="6">No hand-counted items found.</td></tr>'
        else:
            for item in items:
                timestamp = item.timestamp.isoformat() if item.timestamp else 'N/A'
                html += f"""
                    <tr>
                        <td>{item.contract_number}</td>
                        <td>{item.item_name}</td>
                        <td>{item.quantity}</td>
                        <td>{item.action}</td>
                        <td>{timestamp}</td>
                        <td>{item.user}</td>
                    </tr>
                """
        return html
    except Exception as e:
        logger.error(f"Error fetching hand-counted items for contract {contract_number}: {str(e)}")
        current_app.logger.error(f"Error fetching hand-counted items for contract {contract_number}: {str(e)}")
        if 'session' in locals():
            session.close()
        return '<tr><td colspan="6">Error loading hand-counted items.</td></tr>'

@tab4_bp.route('/tab/4/add_hand_counted_item', methods=['POST'])
def add_hand_counted_item():
    data = request.get_json()
    contract_number = data.get('contract_number')
    item_name = data.get('item_name')
    quantity = data.get('quantity')
    action = data.get('action')
    employee_name = data.get('employee_name')

    logger.info(f"Adding hand-counted item: contract_number={contract_number}, item_name={item_name}, quantity={quantity}, action={action}, employee_name={employee_name}")
    current_app.logger.info(f"Adding hand-counted item: contract_number={contract_number}, item_name={item_name}, quantity={quantity}, action={action}, employee_name={employee_name}")

    if not all([contract_number, item_name, quantity, action, employee_name]):
        logger.error("Missing required fields for adding hand-counted item")
        current_app.logger.error("Missing required fields for adding hand-counted item")
        return jsonify({'error': 'All fields are required'}), 400

    try:
        session = db.session()
        hand_counted_item = HandCountedItems(
            contract_number=contract_number,
            item_name=item_name,
            quantity=quantity,
            action=action,
            user=employee_name,
            timestamp=datetime.now()
        )
        session.add(hand_counted_item)
        session.commit()
        session.close()
        logger.info(f"Successfully added hand-counted item for contract {contract_number}")
        current_app.logger.info(f"Successfully added hand-counted item for contract {contract_number}")
        return jsonify({'message': 'Item added successfully'})
    except Exception as e:
        logger.error(f"Error adding hand-counted item: {str(e)}")
        current_app.logger.error(f"Error adding hand-counted item: {str(e)}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return jsonify({'error': 'Failed to add item'}), 500

@tab4_bp.route('/tab/4/remove_hand_counted_item', methods=['POST'])
def remove_hand_counted_item():
    data = request.get_json()
    contract_number = data.get('contract_number')
    item_name = data.get('item_name')
    quantity = data.get('quantity')
    action = data.get('action')
    employee_name = data.get('employee_name')

    logger.info(f"Removing hand-counted item: contract_number={contract_number}, item_name={item_name}, quantity={quantity}, action={action}, employee_name={employee_name}")
    current_app.logger.info(f"Removing hand-counted item: contract_number={contract_number}, item_name={item_name}, quantity={quantity}, action={action}, employee_name={employee_name}")

    if not all([contract_number, item_name, quantity, action, employee_name]):
        logger.error("Missing required fields for removing hand-counted item")
        current_app.logger.error("Missing required fields for removing hand-counted item")
        return jsonify({'error': 'All fields are required'}), 400

    try:
        session = db.session()
        hand_counted_item = HandCountedItems(
            contract_number=contract_number,
            item_name=item_name,
            quantity=quantity,
            action=action,
            user=employee_name,
            timestamp=datetime.now()
        )
        session.add(hand_counted_item)
        session.commit()
        session.close()
        logger.info(f"Successfully removed hand-counted item for contract {contract_number}")
        current_app.logger.info(f"Successfully removed hand-counted item for contract {contract_number}")
        return jsonify({'message': 'Item removed successfully'})
    except Exception as e:
        logger.error(f"Error removing hand-counted item: {str(e)}")
        current_app.logger.error(f"Error removing hand-counted item: {str(e)}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return jsonify({'error': 'Failed to remove item'}), 500

@tab4_bp.route('/tab/4/full_items_by_rental_class')
def full_items_by_rental_class():
    contract_number = request.args.get('category')  # Using 'category' as contract_number for consistency with JS
    common_name = request.args.get('common_name')

    if not contract_number or not common_name:
        logger.error("Category (contract_number) and common name are required")
        current_app.logger.error("Category (contract_number) and common name are required")
        return jsonify({'error': 'Category (contract_number) and common name are required'}), 400

    try:
        session = db.session()

        # Fetch all items with the same contract_number and common_name
        items_query = session.query(ItemMaster).filter(
            ItemMaster.last_contract_num == contract_number,
            ItemMaster.common_name == common_name,
            ItemMaster.status.in_(['On Rent', 'Delivered'])
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

        session.close()
        return jsonify({
            'items': items_data,
            'total_items': len(items_data)
        })
    except Exception as e:
        logger.error(f"Error fetching full items for contract {contract_number}, common_name {common_name}: {str(e)}")
        current_app.logger.error(f"Error fetching full items for contract {contract_number}, common_name {common_name}: {str(e)}")
        return jsonify({'error': 'Failed to fetch full items'}), 500

@tab4_bp.route('/get_contract_date')
def get_contract_date():
    contract_number = request.args.get('contract_number')
    if not contract_number:
        logger.error("Missing required parameter: contract_number is required")
        current_app.logger.error("Missing required parameter: contract_number is required")
        return jsonify({'error': 'Contract number is required'}), 400

    try:
        session = db.session()
        latest_transaction = session.query(Transaction.scan_date).filter(
            Transaction.contract_number == contract_number,
            Transaction.scan_type == 'Rental'
        ).order_by(desc(Transaction.scan_date)).first()

        session.close()
        if latest_transaction and latest_transaction.scan_date:
            return jsonify({'date': latest_transaction.scan_date.isoformat()})
        return jsonify({'date': 'N/A'})
    except Exception as e:
        logger.error(f"Error fetching contract date for {contract_number}: {str(e)}")
        current_app.logger.error(f"Error fetching contract date for {contract_number}: {str(e)}")
        session.close()
        return jsonify({'error': 'Failed to fetch contract date'}), 500