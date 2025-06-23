from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db, cache
from ..models.db_models import ItemMaster, Transaction, HandCountedItems
from sqlalchemy import func, desc, or_
from datetime import datetime
import logging
import sys
import time  # Ensure the time module is imported

# Configure logging for Tab 4
logger = logging.getLogger('tab4')
logger.setLevel(logging.INFO)

# Remove existing handlers to avoid duplicates
logger.handlers = []

# File handler for tab4.log
tab4_file_handler = logging.FileHandler('/home/tim/test_rfidpi/logs/tab4.log')
tab4_file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
tab4_file_handler.setFormatter(formatter)
logger.addHandler(tab4_file_handler)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Also log to the main rfid_dashboard.log
main_file_handler = logging.FileHandler('/home/tim/test_rfidpi/logs/rfid_dashboard.log')
main_file_handler.setLevel(logging.INFO)
main_file_handler.setFormatter(formatter)
logger.addHandler(main_file_handler)

tab4_bp = Blueprint('tab4', __name__)

# Version marker
logger.info("Deployed tab4.py version: 2025-05-06-v35")

@tab4_bp.route('/tab/4')
def tab4_view():
    try:
        session = db.session()
        logger.info("Starting new session for tab4")
        current_app.logger.info("Starting new session for tab4")

        # Step 1: Query ItemMaster for items with status 'On Rent' or 'Delivered' and contract starting with 'L'
        logger.info("Fetching items from id_item_master with status 'On Rent' or 'Delivered' and contract starting with 'L'")
        item_master_contracts = session.query(
            ItemMaster.last_contract_num.label('contract_number'),
            func.count(ItemMaster.tag_id).label('items_on_contract')
        ).filter(
            ItemMaster.last_contract_num != None,
            ItemMaster.last_contract_num != '00000',
            ItemMaster.status.in_(['On Rent', 'Delivered']),
            func.upper(ItemMaster.last_contract_num).like('L%')
        ).group_by(
            ItemMaster.last_contract_num
        ).having(
            func.count(ItemMaster.tag_id) > 0
        ).all()

        logger.info(f"Contracts from ItemMaster: {[(c.contract_number, c.items_on_contract) for c in item_master_contracts]}")

        # Step 2: Fetch total_items_inventory for these contracts
        contract_numbers_from_items = [c.contract_number for c in item_master_contracts]
        total_items_inventory_query = session.query(
            ItemMaster.last_contract_num.label('contract_number'),
            func.count(ItemMaster.tag_id).label('total_items_inventory')
        ).filter(
            ItemMaster.last_contract_num.in_(contract_numbers_from_items)
        ).group_by(
            ItemMaster.last_contract_num
        ).all()

        total_items_inventory_dict = {item.contract_number: item.total_items_inventory for item in total_items_inventory_query}
        logger.info(f"Total items inventory for ItemMaster contracts: {total_items_inventory_dict}")

        # Step 3: Fetch the latest transaction details for these contracts
        logger.info("Fetching latest transaction details for ItemMaster contracts")
        latest_transactions = {}
        if contract_numbers_from_items:
            transaction_query = session.query(
                Transaction.contract_number,
                Transaction.client_name,
                Transaction.scan_date
            ).filter(
                Transaction.contract_number.in_(contract_numbers_from_items),
                Transaction.scan_type == 'Rental'
            ).order_by(
                Transaction.contract_number,
                desc(Transaction.scan_date)
            ).distinct(
                Transaction.contract_number
            ).all()

            latest_transactions = {
                t.contract_number: {
                    'client_name': t.client_name if t.client_name else 'N/A',
                    'scan_date': t.scan_date.isoformat() if t.scan_date else 'N/A'
                } for t in transaction_query
            }
        logger.info(f"Latest transactions for ItemMaster contracts: {latest_transactions}")

        # Step 4: Fetch hand-counted items for contracts starting with 'L'
        logger.info("Fetching hand-counted items for contracts starting with 'L'")
        # Fetch all contracts starting with 'L' from HandCountedItems
        hand_counted_contract_numbers = session.query(
            HandCountedItems.contract_number
        ).filter(
            HandCountedItems.contract_number != None,
            func.upper(HandCountedItems.contract_number).like('L%')
        ).distinct().all()

        hand_counted_contract_numbers = [c.contract_number for c in hand_counted_contract_numbers]

        # Fetch "Added" quantities for these contracts
        added_quantities = session.query(
            HandCountedItems.contract_number,
            func.sum(HandCountedItems.quantity).label('added_quantity')
        ).filter(
            HandCountedItems.contract_number.in_(hand_counted_contract_numbers),
            HandCountedItems.action == 'Added'
        ).group_by(
            HandCountedItems.contract_number
        ).all()

        added_quantities_dict = {item.contract_number: item.added_quantity for item in added_quantities}

        # Fetch "Removed" quantities for these contracts
        removed_quantities = session.query(
            HandCountedItems.contract_number,
            func.sum(HandCountedItems.quantity).label('removed_quantity')
        ).filter(
            HandCountedItems.contract_number.in_(hand_counted_contract_numbers),
            HandCountedItems.action == 'Removed'
        ).group_by(
            HandCountedItems.contract_number
        ).all()

        removed_quantities_dict = {item.contract_number: item.removed_quantity for item in removed_quantities}

        # Calculate net hand-counted quantities
        hand_counted_contracts = []
        for contract_number in hand_counted_contract_numbers:
            added_qty = added_quantities_dict.get(contract_number, 0)
            removed_qty = removed_quantities_dict.get(contract_number, 0)
            net_qty = added_qty - removed_qty
            if net_qty > 0:
                hand_counted_contracts.append((contract_number, net_qty))

        logger.info(f"Hand-counted contracts: {hand_counted_contracts}")

        # Step 5: Combine ItemMaster and HandCountedItems data
        contracts_dict = {}

        # Process ItemMaster contracts
        for contract in item_master_contracts:
            contract_number = contract.contract_number
            transaction_info = latest_transactions.get(contract_number, {'client_name': 'N/A', 'scan_date': 'N/A'})
            contracts_dict[contract_number] = {
                'contract_number': contract_number,
                'client_name': transaction_info['client_name'],
                'scan_date': transaction_info['scan_date'],
                'items_on_contract': contract.items_on_contract or 0,
                'total_items_inventory': total_items_inventory_dict.get(contract_number, 0),
                'hand_counted_items': 0
            }

        # Add or update with HandCountedItems
        for contract_number, hand_counted_total in hand_counted_contracts:
            hand_counted_total = hand_counted_total or 0

            if contract_number in contracts_dict:
                # Contract already exists from ItemMaster, update hand-counted items
                contracts_dict[contract_number]['hand_counted_items'] = hand_counted_total
                contracts_dict[contract_number]['items_on_contract'] += hand_counted_total
            else:
                # New contract from HandCountedItems
                # Fetch total_items_inventory
                total_items_inventory = session.query(func.count(ItemMaster.tag_id)).filter(
                    ItemMaster.last_contract_num == contract_number
                ).scalar() or 0

                # Fetch latest transaction for this contract
                latest_transaction = session.query(
                    Transaction.client_name,
                    Transaction.scan_date
                ).filter(
                    Transaction.contract_number == contract_number,
                    Transaction.scan_type == 'Rental'
                ).order_by(
                    desc(Transaction.scan_date)
                ).first()

                contracts_dict[contract_number] = {
                    'contract_number': contract_number,
                    'client_name': latest_transaction.client_name if latest_transaction else 'N/A',
                    'scan_date': latest_transaction.scan_date.isoformat() if latest_transaction and latest_transaction.scan_date else 'N/A',
                    'items_on_contract': hand_counted_total,
                    'total_items_inventory': total_items_inventory,
                    'hand_counted_items': hand_counted_total
                }

        # Step 6: Filter out contracts with no items on contract and no inventory
        contracts = []
        for contract in contracts_dict.values():
            total_items_on_contract = contract['items_on_contract']
            total_items_inventory = contract['total_items_inventory']
            if total_items_on_contract == 0 and total_items_inventory == 0:
                logger.info(f"Skipping contract {contract['contract_number']}: No items on contract and no items in inventory")
                continue
            contracts.append(contract)

        contracts.sort(key=lambda x: x['contract_number'])  # Default sort for initial load
        logger.info(f"Fetched {len(contracts)} contracts for tab4: {[c['contract_number'] for c in contracts]}")
        current_app.logger.info(f"Fetched {len(contracts)} contracts for tab4: {[c['contract_number'] for c in contracts]}")
        session.close()
        return render_template('tab4.html', contracts=contracts, cache_bust=int(time.time()))
    except Exception as e:
        logger.error(f"Error rendering Tab 4: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error rendering Tab 4: {str(e)}", exc_info=True)
        if 'session' in locals():
            session.close()
        return render_template('tab4.html', contracts=[], cache_bust=int(time.time()))

@tab4_bp.route('/tab/4/hand_counted_contracts', methods=['GET'])
def hand_counted_contracts():
    session = db.session()
    try:
        # Fetch all contracts starting with 'L' from HandCountedItems
        contracts = session.query(
            HandCountedItems.contract_number
        ).filter(
            HandCountedItems.contract_number.ilike('L%')
        ).distinct().all()

        contract_list = [contract.contract_number for contract in contracts]

        # Fetch "Added" quantities for these contracts
        added_quantities = session.query(
            HandCountedItems.contract_number,
            func.sum(HandCountedItems.quantity).label('added_quantity')
        ).filter(
            HandCountedItems.contract_number.in_(contract_list),
            HandCountedItems.action == 'Added'
        ).group_by(
            HandCountedItems.contract_number
        ).all()

        added_quantities_dict = {item.contract_number: item.added_quantity for item in added_quantities}

        # Fetch "Removed" quantities for these contracts
        removed_quantities = session.query(
            HandCountedItems.contract_number,
            func.sum(HandCountedItems.quantity).label('removed_quantity')
        ).filter(
            HandCountedItems.contract_number.in_(contract_list),
            HandCountedItems.action == 'Removed'
        ).group_by(
            HandCountedItems.contract_number
        ).all()

        removed_quantities_dict = {item.contract_number: item.removed_quantity for item in removed_quantities}

        # Calculate net quantities and filter contracts with net quantity > 0
        filtered_contracts = []
        for contract_number in contract_list:
            added_qty = added_quantities_dict.get(contract_number, 0)
            removed_qty = removed_quantities_dict.get(contract_number, 0)
            net_qty = added_qty - removed_qty
            if net_qty > 0:
                filtered_contracts.append(contract_number)

        session.close()
        return jsonify({'contracts': filtered_contracts})
    except Exception as e:
        logger.error(f"Error fetching hand-counted contracts: {str(e)}", exc_info=True)
        session.close()
        return jsonify({'error': str(e)}), 500

@tab4_bp.route('/tab/4/hand_counted_items_by_contract', methods=['GET'])
def hand_counted_items_by_contract():
    contract_number = request.args.get('contract_number')
    session = db.session()
    try:
        # Fetch "Added" quantities
        items = session.query(
            HandCountedItems.item_name,
            func.sum(HandCountedItems.quantity).label('total_quantity')
        ).filter(
            HandCountedItems.contract_number == contract_number,
            HandCountedItems.action == 'Added'
        ).group_by(
            HandCountedItems.item_name
        ).all()

        # Fetch "Removed" quantities
        removed_items = session.query(
            HandCountedItems.item_name,
            func.sum(HandCountedItems.quantity).label('total_quantity')
        ).filter(
            HandCountedItems.contract_number == contract_number,
            HandCountedItems.action == 'Removed'
        ).group_by(
            HandCountedItems.item_name
        ).all()
        removed_dict = {item.item_name: item.total_quantity for item in removed_items}

        # Calculate net quantities
        item_list = []
        for item in items:
            removed_qty = removed_dict.get(item.item_name, 0)
            total_qty = item.total_quantity - removed_qty
            if total_qty > 0:
                item_list.append({'item_name': item.item_name, 'quantity': total_qty})

        session.close()
        return jsonify({'items': item_list})
    except Exception as e:
        logger.error(f"Error fetching hand-counted items for contract {contract_number}: {str(e)}", exc_info=True)
        session.close()
        return jsonify({'error': str(e)}), 500

@tab4_bp.route('/tab/4/contract_items_count', methods=['GET'])
def contract_items_count():
    contract_number = request.args.get('contract_number')
    session = db.session()
    try:
        # Count items on contract (On Rent or Delivered)
        items_on_contract = session.query(
            func.count(ItemMaster.tag_id)
        ).filter(
            ItemMaster.last_contract_num == contract_number,
            ItemMaster.status.in_(['On Rent', 'Delivered'])
        ).scalar() or 0

        # Count hand-counted items
        hand_counted_added = session.query(
            func.sum(HandCountedItems.quantity)
        ).filter(
            HandCountedItems.contract_number == contract_number,
            HandCountedItems.action == 'Added'
        ).scalar() or 0

        hand_counted_removed = session.query(
            func.sum(HandCountedItems.quantity)
        ).filter(
            HandCountedItems.contract_number == contract_number,
            HandCountedItems.action == 'Removed'
        ).scalar() or 0

        hand_counted_total = max(hand_counted_added - hand_counted_removed, 0)
        total_items = items_on_contract + hand_counted_total

        session.close()
        return jsonify({'total_items': total_items})
    except Exception as e:
        logger.error(f"Error calculating items on contract for {contract_number}: {str(e)}", exc_info=True)
        session.close()
        return jsonify({'error': str(e)}), 500

@tab4_bp.route('/tab/4/hand_counted_entries', methods=['GET'])
def hand_counted_entries():
    contract_number = request.args.get('contract_number')
    session = db.session()
    try:
        # Count hand-counted items (net quantity: Added - Removed)
        hand_counted_added = session.query(
            func.sum(HandCountedItems.quantity)
        ).filter(
            HandCountedItems.contract_number == contract_number,
            HandCountedItems.action == 'Added'
        ).scalar() or 0

        hand_counted_removed = session.query(
            func.sum(HandCountedItems.quantity)
        ).filter(
            HandCountedItems.contract_number == contract_number,
            HandCountedItems.action == 'Removed'
        ).scalar() or 0

        hand_counted_total = max(hand_counted_added - hand_counted_removed, 0)

        session.close()
        return jsonify({'hand_counted_entries': hand_counted_total})
    except Exception as e:
        logger.error(f"Error calculating hand-counted entries for {contract_number}: {str(e)}", exc_info=True)
        session.close()
        return jsonify({'error': str(e)}), 500

@tab4_bp.route('/tab/4/common_names')
def tab4_common_names():
    contract_number = request.args.get('contract_number')
    page = int(request.args.get('page', 1))
    per_page = 10
    sort = request.args.get('sort', '')  # Keep for compatibility, but ignore unless explicitly needed
    fetch_all = request.args.get('all', 'false').lower() == 'true'

    logger.info(f"Fetching common names for contract_number={contract_number}, page={page}, sort={sort}, fetch_all={fetch_all}")
    current_app.logger.info(f"Fetching common names for contract_number={contract_number}, page={page}, sort={sort}, fetch_all={fetch_all}")

    if not contract_number:
        logger.error("Missing required parameter: contract_number is required")
        current_app.logger.error("Missing required parameter: contract_number is required")
        return jsonify({'error': 'Contract number is required'}), 400

    try:
        session = db.session()

        # Fetch common names for items on this contract from id_item_master
        common_names_query = session.query(
            ItemMaster.common_name,
            func.count(ItemMaster.tag_id).label('on_contracts')
        ).filter(
            ItemMaster.last_contract_num == contract_number,
            ItemMaster.status.in_(['On Rent', 'Delivered'])
        ).group_by(
            ItemMaster.common_name
        )

        common_names_all = common_names_query.all()

        logger.info(f"Common names from id_item_master for contract {contract_number}: {[(name, count) for name, count in common_names_all]}")
        current_app.logger.info(f"Common names from id_item_master for contract {contract_number}: {[(name, count) for name, count in common_names_all]}")

        # Fetch hand-counted items to include as "common names"
        # Fetch "Added" quantities
        hand_counted_added = session.query(
            HandCountedItems.item_name.label('common_name'),
            func.sum(HandCountedItems.quantity).label('added_quantity')
        ).filter(
            HandCountedItems.contract_number == contract_number,
            HandCountedItems.action == 'Added'
        ).group_by(
            HandCountedItems.item_name
        ).all()

        # Fetch "Removed" quantities
        hand_counted_removed = session.query(
            HandCountedItems.item_name.label('common_name'),
            func.sum(HandCountedItems.quantity).label('removed_quantity')
        ).filter(
            HandCountedItems.contract_number == contract_number,
            HandCountedItems.action == 'Removed'
        ).group_by(
            HandCountedItems.item_name
        ).all()

        # Create a dictionary of removed quantities
        removed_dict = {item.common_name: item.removed_quantity for item in hand_counted_removed}

        # Calculate net quantities for hand-counted items
        hand_counted_items = []
        for item in hand_counted_added:
            removed_qty = removed_dict.get(item.common_name, 0)
            net_qty = item.added_quantity - removed_qty
            if net_qty > 0:
                hand_counted_items.append((item.common_name, net_qty))

        logger.info(f"Hand-counted items as common names for contract {contract_number}: {hand_counted_items}")
        current_app.logger.info(f"Hand-counted items as common names for contract {contract_number}: {hand_counted_items}")

        # Combine common names from id_item_master and hand_counted_items
        common_names = {}
        for name, on_contracts in common_names_all:
            if not name:
                continue
            total_items_inventory = session.query(func.count(ItemMaster.tag_id)).filter(
                ItemMaster.common_name == name
            ).scalar()
            common_names[name] = {
                'name': name,
                'on_contracts': on_contracts or 0,
                'total_items_inventory': total_items_inventory or 0,
                'is_hand_counted': False
            }

        for name, on_contracts in hand_counted_items:
            if not name:
                continue
            if name in common_names:
                common_names[name]['on_contracts'] += on_contracts or 0
            else:
                common_names[name] = {
                    'name': name,
                    'on_contracts': on_contracts or 0,
                    'total_items_inventory': 0,
                    'is_hand_counted': True
                }

        common_names_list = list(common_names.values())

        # Handle pagination or fetch all (no sorting applied)
        if fetch_all:
            paginated_common_names = common_names_list
            total_common_names = len(common_names_list)
            page = 1
            per_page = total_common_names
        else:
            total_common_names = len(common_names_list)
            start = (page - 1) * per_page
            end = start + per_page
            paginated_common_names = common_names_list[start:end]

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
    sort = request.args.get('sort', '')  # Keep for compatibility, but ignore

    logger.info(f"Fetching items for contract_number={contract_number}, common_name={common_name}, page={page}, sort={sort}")
    current_app.logger.info(f"Fetching items for top level contract_number={contract_number}, common_name={common_name}, page={page}, sort={sort}")

    if not contract_number or not common_name:
        logger.error("Missing required parameters: contract number and common name are required")
        current_app.logger.error("Missing required parameters: contract number and common name are required")
        return jsonify({'error': 'Contract number and common name are required'}), 400

    try:
        session = db.session()

        # Check if this common_name exists in HandCountedItems
        is_hand_counted = session.query(HandCountedItems).filter(
            HandCountedItems.contract_number == contract_number,
            HandCountedItems.item_name == common_name,
            HandCountedItems.action == 'Added'
        ).first() is not None

        items_data = []
        total_items = 0

        if is_hand_counted:
            # Fetch hand-counted items
            query = session.query(HandCountedItems).filter(
                HandCountedItems.contract_number == contract_number,
                HandCountedItems.item_name == common_name,
                HandCountedItems.action == 'Added'
            )

            total_items = query.count()
            items = query.offset((page - 1) * per_page).limit(per_page).all()

            for item in items:
                items_data.append({
                    'tag_id': f"HC-{item.id}",
                    'common_name': item.item_name,
                    'bin_location': 'N/A',
                    'status': 'Hand-Counted',
                    'last_contract_num': item.contract_number,
                    'last_scanned_date': item.timestamp.isoformat() if item.timestamp else 'N/A'
                })
        else:
            # Fetch items from id_item_master
            query = session.query(ItemMaster).filter(
                ItemMaster.last_contract_num == contract_number,
                ItemMaster.common_name == common_name,
                ItemMaster.status.in_(['On Rent', 'Delivered'])
            )

            total_items = query.count()
            items = query.offset((page - 1) * per_page).limit(per_page).all()

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

        logger.info(f"Items for contract {contract_number}, common_name {common_name}: {len(items_data)} items")
        current_app.logger.info(f"Items for contract {contract_number}, common_name {common_name}: {len(items_data)} items")

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
    contract_number = request.args.get('contract_number', None)
    logger.info(f"Fetching hand-counted items for contract_number={contract_number}")
    current_app.logger.info(f"Fetching hand-counted items for contract_number={contract_number}")
    try:
        session = db.session()
        query = session.query(HandCountedItems).order_by(HandCountedItems.timestamp.desc())
        if contract_number:
            query = query.filter(HandCountedItems.contract_number == contract_number)
        # Limit to the last 10 entries
        items = query.limit(10).all()
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

    # Validate quantity
    try:
        quantity = int(quantity)
        if quantity <= 0:
            logger.error("Quantity must be a positive integer")
            current_app.logger.error("Quantity must be a positive integer")
            return jsonify({'error': 'Quantity must be a positive integer'}), 400
    except ValueError:
        logger.error("Quantity must be a valid integer")
        current_app.logger.error("Quantity must be a valid integer")
        return jsonify({'error': 'Quantity must be a valid integer'}), 400

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
        return jsonify({'message': f'Successfully added {quantity} {item_name} to {contract_number}'})
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

    # Validate quantity
    try:
        quantity = int(quantity)
        if quantity <= 0:
            logger.error("Quantity must be a positive integer")
            current_app.logger.error("Quantity must be a positive integer")
            return jsonify({'error': 'Quantity must be a positive integer'}), 400
    except ValueError:
        logger.error("Quantity must be a valid integer")
        current_app.logger.error("Quantity must be a valid integer")
        return jsonify({'error': 'Quantity must be a valid integer'}), 400

    try:
        session = db.session()

        # Calculate the current total quantity of "Added" items for this contract_number and item_name
        added_quantity = session.query(
            func.sum(HandCountedItems.quantity)
        ).filter(
            HandCountedItems.contract_number == contract_number,
            HandCountedItems.item_name == item_name,
            HandCountedItems.action == 'Added'
        ).scalar() or 0

        # Calculate the current total quantity of "Removed" items
        removed_quantity = session.query(
            func.sum(HandCountedItems.quantity)
        ).filter(
            HandCountedItems.contract_number == contract_number,
            HandCountedItems.item_name == item_name,
            HandCountedItems.action == 'Removed'
        ).scalar() or 0

        # Calculate the net quantity (Added - Removed)
        current_quantity = added_quantity - removed_quantity
        logger.info(f"Current quantity for {contract_number}/{item_name}: Added={added_quantity}, Removed={removed_quantity}, Net={current_quantity}")

        # Check if removal is possible
        if current_quantity < quantity:
            session.close()
            logger.info(f"Cannot remove {quantity} items from {contract_number}/{item_name}: current_quantity={current_quantity}")
            current_app.logger.info(f"Cannot remove {quantity} items from {contract_number}/{item_name}: current_quantity={current_quantity}")
            return jsonify({'error': f'Cannot remove {quantity} items from {contract_number}/{item_name}. Quantity would be negative.'}), 400

        # Log the removal as a new entry with action="Removed"
        hand_counted_item = HandCountedItems(
            contract_number=contract_number,
            item_name=item_name,
            quantity=quantity,
            action='Removed',
            user=employee_name,
            timestamp=datetime.now()
        )
        session.add(hand_counted_item)
        session.commit()
        session.close()
        logger.info(f"Successfully removed {quantity} hand-counted items for contract {contract_number}, item {item_name}")
        current_app.logger.info(f"Successfully removed {quantity} hand-counted items for contract {contract_number}, item {item_name}")
        return jsonify({'message': f'Successfully removed {quantity} {item_name} from {contract_number}'})
    except Exception as e:
        logger.error(f"Error removing hand-counted item: {str(e)}")
        current_app.logger.error(f"Error removing hand-counted item: {str(e)}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return jsonify({'error': 'Failed to remove item'}), 500

@tab4_bp.route('/tab/4/full_items_by_rental_class')
def full_items_by_rental_class():
    contract_number = request.args.get('category')
    common_name = request.args.get('common_name')

    if not contract_number or not common_name:
        logger.error("Category (contract_number) and common name are required")
        current_app.logger.error("Category (contract_number) and common name are required")
        return jsonify({'error': 'Category (contract_number) and common name are required'}), 400

    try:
        session = db.session()

        # Check if this common_name exists in HandCountedItems
        is_hand_counted = session.query(HandCountedItems).filter(
            HandCountedItems.contract_number == contract_number,
            HandCountedItems.item_name == common_name,
            HandCountedItems.action == 'Added'
        ).first() is not None

        items_data = []

        if is_hand_counted:
            # Fetch all hand-counted items with the same contract_number and item_name
            items_query = session.query(HandCountedItems).filter(
                HandCountedItems.contract_number == contract_number,
                HandCountedItems.item_name == common_name,
                HandCountedItems.action == 'Added'
            ).order_by(HandCountedItems.id)

            items = items_query.all()
            for item in items:
                last_scanned_date = item.timestamp.isoformat() if item.timestamp else 'N/A'
                items_data.append({
                    'tag_id': f"HC-{item.id}",
                    'common_name': item.item_name,
                    'rental_class_num': 'N/A',
                    'bin_location': 'N/A',
                    'status': 'Hand-Counted',
                    'last_contract_num': item.contract_number,
                    'last_scanned_date': last_scanned_date,
                    'quality': 'N/A',
                    'notes': 'N/A'
                })
        else:
            # Fetch all items with the same contract_number and common_name from id_item_master
            items_query = session.query(ItemMaster).filter(
                ItemMaster.last_contract_num == contract_number,
                ItemMaster.common_name == common_name,
                ItemMaster.status.in_(['On Rent', 'Delivered'])
            ).order_by(ItemMaster.tag_id)

            items = items_query.all()
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