from flask import Blueprint, render_template, request, jsonify, current_app, make_response
from .. import db, cache
from ..models.db_models import ItemMaster, Transaction, HandCountedItems, HandCountedCatalog, LaundryContractStatus
from sqlalchemy import func, desc, or_
from sqlalchemy.exc import ProgrammingError
from datetime import datetime
import logging
import sys
import time  # Ensure the time module is imported
import os
import config

# Configure logging for Tab 4
logger = logging.getLogger('tab4')
logger.setLevel(logging.INFO)

# Remove existing handlers to avoid duplicates
logger.handlers = []

# File handler for tab4.log
tab4_log_file = os.path.join(config.BASE_DIR, 'logs', 'tab4.log')
tab4_file_handler = logging.FileHandler(tab4_log_file)
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
main_file_handler = logging.FileHandler(config.LOG_FILE)
main_file_handler.setLevel(logging.INFO)
main_file_handler.setFormatter(formatter)
logger.addHandler(main_file_handler)

tab4_bp = Blueprint('tab4', __name__)

# Version marker
logger.info("Deployed tab4.py version: 2025-05-06-v36 at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@tab4_bp.route('/tab/4')
def tab4_view():
    session = None
    try:
        session = db.session()
        logger.info("Starting new session for tab4 at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.info("Starting new session for tab4 at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        # Step 1: Query ItemMaster for items with status 'On Rent' or 'Delivered' and contract starting with 'L'
        logger.info("Fetching items from id_item_master with status 'On Rent' or 'Delivered' and contract starting with 'L' at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
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

        logger.info(f"Contracts from ItemMaster: {[(c.contract_number, c.items_on_contract) for c in item_master_contracts]} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

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
        logger.info(f"Total items inventory for ItemMaster contracts: {total_items_inventory_dict} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        # Step 3: Fetch the latest transaction details for these contracts
        logger.info("Fetching latest transaction details for ItemMaster contracts at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
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
        logger.info(f"Latest transactions for ItemMaster contracts: {latest_transactions} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        # Step 4: Fetch hand-counted items for contracts starting with 'L'
        logger.info("Fetching hand-counted items for contracts starting with 'L' at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
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

        logger.info(f"Hand-counted contracts: {hand_counted_contracts} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

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
        # BUT: Keep contracts that have had hand-counted items added (even if net is 0)
        contracts = []
        for contract in contracts_dict.values():
            total_items_on_contract = contract['items_on_contract']
            total_items_inventory = contract['total_items_inventory']
            hand_counted_items = contract['hand_counted_items']
            
            # Check if contract has any history of hand-counted items (even if net is 0)
            contract_number = contract['contract_number']
            has_hand_counted_history = False
            if hand_counted_items == 0:
                # Check if there were any hand-counted items added historically
                hand_counted_history = session.query(HandCountedItems).filter(
                    HandCountedItems.contract_number == contract_number,
                    HandCountedItems.action == 'Added'
                ).first()
                has_hand_counted_history = hand_counted_history is not None
            
            # Skip only if no items AND no inventory AND no hand-counted history
            if total_items_on_contract == 0 and total_items_inventory == 0 and not has_hand_counted_history:
                logger.info(f"Skipping contract {contract['contract_number']}: No items, no inventory, no hand-counted history at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                continue
            contracts.append(contract)

        # Step 7: Add laundry contract status information and include completed contracts
        contract_numbers = [c['contract_number'] for c in contracts]
        
        # Also fetch contracts that are finalized/returned but might not have current items
        completed_status_records = session.query(LaundryContractStatus).filter(
            LaundryContractStatus.status.in_(['finalized', 'returned']),
            LaundryContractStatus.contract_number.like('L%')
        ).all()
        
        # Add completed contracts to the list if they're not already there
        existing_contract_numbers = set(contract_numbers)
        for status_record in completed_status_records:
            if status_record.contract_number not in existing_contract_numbers:
                # Get basic info for completed contract
                latest_transaction = session.query(
                    Transaction.client_name,
                    Transaction.scan_date
                ).filter(
                    Transaction.contract_number == status_record.contract_number,
                    Transaction.scan_type == 'Rental'
                ).order_by(desc(Transaction.scan_date)).first()
                
                # Get inventory count
                total_items_inventory = session.query(func.count(ItemMaster.tag_id)).filter(
                    ItemMaster.last_contract_num == status_record.contract_number
                ).scalar() or 0
                
                # Add the completed contract to the list
                contracts.append({
                    'contract_number': status_record.contract_number,
                    'client_name': latest_transaction.client_name if latest_transaction else 'N/A',
                    'scan_date': latest_transaction.scan_date.isoformat() if latest_transaction and latest_transaction.scan_date else 'N/A',
                    'items_on_contract': 0,  # No current items (completed)
                    'total_items_inventory': total_items_inventory,
                    'hand_counted_items': 0  # No current hand-counted items (completed)
                })
                contract_numbers.append(status_record.contract_number)
        
        # Now add status information to all contracts
        if contract_numbers:
            status_query = session.query(LaundryContractStatus).filter(
                LaundryContractStatus.contract_number.in_(contract_numbers)
            ).all()
            status_dict = {s.contract_number: s for s in status_query}
            
            # Add status information to each contract
            for contract in contracts:
                contract_number = contract['contract_number']
                status_info = status_dict.get(contract_number)
                if status_info:
                    contract['status'] = status_info.status
                    contract['finalized_date'] = status_info.finalized_date.isoformat() if status_info.finalized_date else None
                    contract['returned_date'] = status_info.returned_date.isoformat() if status_info.returned_date else None
                    contract['status_notes'] = status_info.notes
                else:
                    # Default status for new contracts
                    contract['status'] = 'active'
                    contract['finalized_date'] = None
                    contract['returned_date'] = None
                    contract['status_notes'] = None

        contracts.sort(key=lambda x: x['contract_number'])  # Default sort for initial load
        logger.info(f"Fetched {len(contracts)} contracts for tab4: {[c['contract_number'] for c in contracts]} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.info(f"Fetched {len(contracts)} contracts for tab4: {[c['contract_number'] for c in contracts]} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return render_template('tab4.html', contracts=contracts, cache_bust=int(time.time()))
    except Exception as e:
        logger.error(f"Error rendering Tab 4: {str(e)} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), exc_info=True)
        current_app.logger.error(f"Error rendering Tab 4: {str(e)} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), exc_info=True)
        return render_template('tab4.html', contracts=[], cache_bust=int(time.time()))
    finally:
        if session:
            session.close()

@tab4_bp.route('/tab/4/hand_counted_contracts', methods=['GET'])
def hand_counted_contracts():
    session = None
    try:
        session = db.session()
        # Fetch open laundry contracts from ItemMaster that currently have items
        contracts = session.query(
            ItemMaster.last_contract_num
        ).filter(
            ItemMaster.last_contract_num.isnot(None),
            ItemMaster.last_contract_num != '00000',
            ItemMaster.status.in_(['On Rent', 'Delivered']),
            func.upper(ItemMaster.last_contract_num).like('L%')
        ).group_by(
            ItemMaster.last_contract_num
        ).having(
            func.count(ItemMaster.tag_id) > 0
        ).order_by(
            ItemMaster.last_contract_num
        ).all()

        filtered_contracts = [c.last_contract_num for c in contracts]
        logger.info(
            f"Returned hand-counted contracts: {filtered_contracts} at %s",
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        return jsonify({'contracts': filtered_contracts})
    except Exception as e:
        logger.error(f"Error fetching hand-counted contracts: {str(e)} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab4_bp.route('/tab/4/hand_counted_items_by_contract', methods=['GET'])
def hand_counted_items_by_contract():
    contract_number = request.args.get('contract_number')
    session = None
    try:
        session = db.session()
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

        # Include all items with prior additions for removal options, even if net zero
        if not item_list and contract_number:
            added_items = session.query(HandCountedItems.item_name).filter(
                HandCountedItems.contract_number == contract_number,
                HandCountedItems.action == 'Added'
            ).distinct().all()
            for item in added_items:
                item_name = item.item_name
                added_qty = session.query(func.sum(HandCountedItems.quantity)).filter(
                    HandCountedItems.contract_number == contract_number,
                    HandCountedItems.item_name == item_name,
                    HandCountedItems.action == 'Added'
                ).scalar() or 0
                removed_qty = removed_dict.get(item_name, 0)
                net_qty = added_qty - removed_qty
                if added_qty > 0:  # Include items that have been added, even if fully removed
                    item_list.append({'item_name': item_name, 'quantity': net_qty})

        logger.info(f"Returned hand-counted items for contract {contract_number}: {item_list} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return jsonify({'items': item_list})
    except Exception as e:
        logger.error(f"Error fetching hand-counted items for contract {contract_number}: {str(e)} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab4_bp.route('/tab/4/hand_counted_catalog', methods=['GET'])
def hand_counted_catalog():
    session = None
    try:
        session = db.session()
        try:
            items = session.query(HandCountedCatalog.item_name, HandCountedCatalog.hand_counted_name).all()
        except ProgrammingError:
            session.rollback()
            logger.warning("hand_counted_catalog table missing; returning empty list")
            current_app.logger.warning("hand_counted_catalog table missing; returning empty list")
            items = []
        # Use hand_counted_name if available, otherwise fall back to item_name
        item_list = []
        for item in items:
            display_name = item.hand_counted_name if item.hand_counted_name else item.item_name
            item_list.append(display_name)
        logger.info(f"Returned hand-counted catalog items: {item_list} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return jsonify({'items': item_list})
    except Exception as e:
        logger.error(f"Error fetching hand-counted catalog: {str(e)} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab4_bp.route('/tab/4/hand_counted_catalog_categorized', methods=['GET'])
def hand_counted_catalog_categorized():
    """
    Get hand counted catalog items organized by categories for improved UX
    Returns items grouped by category and subcategory
    """
    session = None
    try:
        session = db.session()
        try:
            # Get items with their category information
            # Join HandCountedCatalog with UserRentalClassMapping via rental_class_id
            from ..models.db_models import UserRentalClassMapping, RentalClassMapping
            
            items_with_categories = session.query(
                HandCountedCatalog.item_name,
                HandCountedCatalog.hand_counted_name,
                UserRentalClassMapping.category,
                UserRentalClassMapping.subcategory
            ).outerjoin(
                UserRentalClassMapping, 
                HandCountedCatalog.rental_class_id == UserRentalClassMapping.rental_class_id
            ).all()
            
            # If no user mappings, try system mappings
            if not items_with_categories:
                items_with_categories = session.query(
                    HandCountedCatalog.item_name,
                    HandCountedCatalog.hand_counted_name,
                    RentalClassMapping.category,
                    RentalClassMapping.subcategory
                ).outerjoin(
                    RentalClassMapping,
                    HandCountedCatalog.rental_class_id == RentalClassMapping.rental_class_id
                ).all()
            
        except ProgrammingError:
            session.rollback()
            logger.warning("hand_counted_catalog table missing; returning empty categorized list")
            current_app.logger.warning("hand_counted_catalog table missing; returning empty categorized list")
            items_with_categories = []
        
        # Organize items by category
        categorized_items = {}
        uncategorized_items = []
        
        for item_name, hand_counted_name, category, subcategory in items_with_categories:
            # Use hand_counted_name if available, otherwise fall back to item_name
            display_name = hand_counted_name if hand_counted_name else item_name
            
            if category and subcategory:
                if category not in categorized_items:
                    categorized_items[category] = {}
                if subcategory not in categorized_items[category]:
                    categorized_items[category][subcategory] = []
                categorized_items[category][subcategory].append(display_name)
            else:
                uncategorized_items.append(display_name)
        
        # Add uncategorized items as a separate category
        if uncategorized_items:
            categorized_items['Uncategorized'] = {'General': uncategorized_items}
        
        logger.info(f"Returned categorized hand-counted catalog: {len(categorized_items)} categories")
        return jsonify({'categories': categorized_items})
        
    except Exception as e:
        logger.error(f"Error fetching categorized hand-counted catalog: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab4_bp.route('/tab/4/contract_items_count', methods=['GET'])
def contract_items_count():
    contract_number = request.args.get('contract_number')
    session = None
    try:
        session = db.session()
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

        logger.info(f"Returned contract items count for {contract_number}: {total_items} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return jsonify({'total_items': total_items})
    except Exception as e:
        logger.error(f"Error calculating items on contract for {contract_number}: {str(e)} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab4_bp.route('/tab/4/next_contract_number', methods=['GET'])
def next_contract_number():
    session = None
    try:
        session = db.session()
        latest_item = session.query(func.max(ItemMaster.last_contract_num)).filter(func.upper(ItemMaster.last_contract_num).like('L%')).scalar()
        latest_hand = session.query(func.max(HandCountedItems.contract_number)).filter(func.upper(HandCountedItems.contract_number).like('L%')).scalar()
        candidates = [c for c in [latest_item, latest_hand] if c]
        if candidates:
            latest = max(candidates)
            try:
                next_num = int(latest[1:]) + 1
            except ValueError:
                next_num = 1
        else:
            next_num = 1
        return jsonify({'next_contract_number': f'L{next_num}'})
    except Exception as e:
        logger.error(f"Error calculating next contract number: {str(e)} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab4_bp.route('/tab/4/hand_counted_entries', methods=['GET'])
def hand_counted_entries():
    contract_number = request.args.get('contract_number')
    session = None
    try:
        session = db.session()
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

        logger.info(f"Returned hand-counted entries for {contract_number}: {hand_counted_total} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return jsonify({'hand_counted_entries': hand_counted_total})
    except Exception as e:
        logger.error(f"Error calculating hand-counted entries for {contract_number}: {str(e)} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'), exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab4_bp.route('/tab/4/common_names')
def tab4_common_names():
    contract_number = request.args.get('contract_number')
    page = int(request.args.get('page', 1))
    per_page = 10
    sort = request.args.get('sort', '')
    fetch_all = request.args.get('all', 'false').lower() == 'true'

    logger.info(f"Fetching common names for contract_number={contract_number}, page={page}, sort={sort}, fetch_all={fetch_all} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    current_app.logger.info(f"Fetching common names for contract_number={contract_number}, page={page}, sort={sort}, fetch_all={fetch_all} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    if not contract_number:
        logger.error("Missing required parameter: contract_number is required at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.error("Missing required parameter: contract_number is required at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
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

        logger.info(f"Common names from id_item_master for contract {contract_number}: {[(name, count) for name, count in common_names_all]} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.info(f"Common names from id_item_master for contract {contract_number}: {[(name, count) for name, count in common_names_all]} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

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

        logger.info(f"Hand-counted items as common names for contract {contract_number}: {hand_counted_items} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.info(f"Hand-counted items as common names for contract {contract_number}: {hand_counted_items} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

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

        # Apply sorting
        if sort:
            try:
                field, direction = sort.rsplit('_', 1)
                reverse = direction == 'desc'
                if field in ['name', 'on_contracts', 'total_items_inventory']:
                    common_names_list.sort(
                        key=lambda x: (x[field].lower() if isinstance(x[field], str) else x[field]),
                        reverse=reverse
                    )
            except ValueError:
                logger.warning(f"Invalid sort parameter '{sort}'")
                current_app.logger.warning(f"Invalid sort parameter '{sort}'")
        else:
            common_names_list.sort(key=lambda x: x['name'].lower())

        # Handle pagination or fetch all
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

        logger.info(f"Returning {len(paginated_common_names)} common names for contract {contract_number} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.info(f"Returning {len(paginated_common_names)} common names for contract {contract_number} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return jsonify({
            'common_names': paginated_common_names,
            'total_common_names': total_common_names,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        logger.error(f"Error fetching common names for contract {contract_number}: {str(e)} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.error(f"Error fetching common names for contract {contract_number}: {str(e)} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return jsonify({'error': 'Failed to fetch common names'}), 500
    finally:
        if session:
            session.close()

@tab4_bp.route('/tab/4/data')
def tab4_data():
    contract_number = request.args.get('contract_number')
    common_name = request.args.get('common_name')
    page = int(request.args.get('page', 1))
    per_page = 10
    sort = request.args.get('sort', '')  # Keep for compatibility, but ignore

    logger.info(f"Fetching items for contract_number={contract_number}, common_name={common_name}, page={page}, sort={sort} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    current_app.logger.info(f"Fetching items for top level contract_number={contract_number}, common_name={common_name}, page={page}, sort={sort} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    if not contract_number or not common_name:
        logger.error("Missing required parameters: contract number and common name are required at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.error("Missing required parameters: contract number and common name are required at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
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

        logger.info(f"Items for contract {contract_number}, common_name {common_name}: {len(items_data)} items at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.info(f"Items for contract {contract_number}, common_name {common_name}: {len(items_data)} items at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        return jsonify({
            'items': items_data,
            'total_items': total_items,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        logger.error(f"Error fetching items for contract {contract_number}, common_name {common_name}: {str(e)} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.error(f"Error fetching items for contract {contract_number}, common_name {common_name}: {str(e)} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return jsonify({'error': 'Failed to fetch items'}), 500
    finally:
        if session:
            session.close()

@tab4_bp.route('/tab/4/contract_history_print')
def contract_history_print():
    """Generate comprehensive printable contract history report."""
    contract_number = request.args.get('contract_number')
    
    if not contract_number:
        return jsonify({'error': 'Contract number is required'}), 400
    
    session = None
    try:
        session = db.session()
        
        # Get contract overview from latest transaction
        contract_info = session.query(
            Transaction.contract_number,
            Transaction.client_name,
            func.min(Transaction.scan_date).label('start_date'),
            func.max(Transaction.scan_date).label('last_activity')
        ).filter(
            Transaction.contract_number == contract_number
        ).group_by(Transaction.contract_number, Transaction.client_name).first()
        
        if not contract_info:
            return jsonify({'error': f'Contract {contract_number} not found'}), 404
        
        # Get RFID items on contract
        rfid_items = session.query(ItemMaster).filter(
            ItemMaster.last_contract_num == contract_number,
            ItemMaster.status.in_(['On Rent', 'Delivered', 'Ready to Return'])
        ).all()
        
        # Get hand counted items history with custom names
        hand_counted_items = session.query(
            HandCountedItems,
            HandCountedCatalog.hand_counted_name
        ).outerjoin(
            HandCountedCatalog,
            HandCountedItems.item_name == HandCountedCatalog.item_name
        ).filter(
            HandCountedItems.contract_number == contract_number
        ).order_by(HandCountedItems.timestamp.desc()).all()
        
        # Get transaction history for timeline
        transactions = session.query(Transaction).filter(
            Transaction.contract_number == contract_number
        ).order_by(Transaction.scan_date.desc()).limit(50).all()
        
        # Calculate totals
        total_rfid_items = len(rfid_items)
        total_hand_counted = sum(item_tuple.HandCountedItems.quantity for item_tuple in hand_counted_items if item_tuple.HandCountedItems.action == 'Added')
        total_hand_counted -= sum(item_tuple.HandCountedItems.quantity for item_tuple in hand_counted_items if item_tuple.HandCountedItems.action == 'Removed')
        
        # Prepare data for template
        contract_data = {
            'contract_number': contract_number,
            'client_name': contract_info.client_name or 'N/A',
            'start_date': contract_info.start_date.strftime('%Y-%m-%d %H:%M') if contract_info.start_date else 'N/A',
            'last_activity': contract_info.last_activity.strftime('%Y-%m-%d %H:%M') if contract_info.last_activity else 'N/A',
            'total_rfid_items': total_rfid_items,
            'total_hand_counted': total_hand_counted,
            'total_items': total_rfid_items + total_hand_counted,
            'rfid_items': [{
                'tag_id': item.tag_id,
                'common_name': item.common_name or 'N/A',
                'status': item.status or 'N/A',
                'bin_location': item.bin_location or 'N/A',
                'quality': item.quality or 'N/A',
                'last_scanned': item.date_last_scanned.strftime('%Y-%m-%d %H:%M') if item.date_last_scanned else 'N/A',
                'notes': item.notes or ''
            } for item in rfid_items],
            'hand_counted_items': [{
                'item_name': item_tuple.HandCountedCatalog.hand_counted_name if item_tuple.HandCountedCatalog and item_tuple.HandCountedCatalog.hand_counted_name else item_tuple.HandCountedItems.item_name,
                'quantity': item_tuple.HandCountedItems.quantity,
                'action': item_tuple.HandCountedItems.action,
                'timestamp': item_tuple.HandCountedItems.timestamp.strftime('%Y-%m-%d %H:%M') if item_tuple.HandCountedItems.timestamp else 'N/A',
                'user': item_tuple.HandCountedItems.user or 'N/A'
            } for item_tuple in hand_counted_items],
            'recent_activity': [{
                'tag_id': t.tag_id or 'N/A',
                'scan_type': t.scan_type or 'N/A',
                'scan_date': t.scan_date.strftime('%Y-%m-%d %H:%M') if t.scan_date else 'N/A',
                'common_name': t.common_name or 'N/A',
                'status': t.status or 'N/A',
                'scan_by': t.scan_by or 'N/A'
            } for t in transactions[:10]]  # Latest 10 activities
        }
        
        # Add current date to data
        contract_data['current_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        html = render_template('contract_history_print.html', data=contract_data)
        response = make_response(html)
        response.headers['Content-Type'] = 'text/html'
        response.headers['Content-Disposition'] = f'inline; filename=contract_{contract_number}_history.html'
        return response
        
    except Exception as e:
        logger.error(f"Error generating contract history print: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab4_bp.route('/tab/4/hand_counted_history_print')
def hand_counted_history_print():
    """Generate printable hand counted items history by contract."""
    contract_number = request.args.get('contract_number')
    
    if not contract_number:
        return jsonify({'error': 'Contract number is required'}), 400
        
    session = None
    try:
        session = db.session()
        
        # Get contract basic info
        contract_info = session.query(
            Transaction.client_name
        ).filter(
            Transaction.contract_number == contract_number
        ).first()
        
        # Get all hand counted items for this contract with custom names
        hand_counted_items = session.query(
            HandCountedItems,
            HandCountedCatalog.hand_counted_name
        ).outerjoin(
            HandCountedCatalog,
            HandCountedItems.item_name == HandCountedCatalog.item_name
        ).filter(
            HandCountedItems.contract_number == contract_number
        ).order_by(HandCountedItems.timestamp.desc()).all()
        
        if not hand_counted_items:
            return jsonify({'error': f'No hand counted items found for contract {contract_number}'}), 404
        
        # Group by item name for summary (using custom names when available)
        item_summary = {}
        for item_tuple in hand_counted_items:
            item = item_tuple.HandCountedItems
            display_name = item_tuple.HandCountedCatalog.hand_counted_name if item_tuple.HandCountedCatalog and item_tuple.HandCountedCatalog.hand_counted_name else item.item_name
            
            if display_name not in item_summary:
                item_summary[display_name] = {'added': 0, 'removed': 0, 'net': 0, 'last_activity': None}
            
            if item.action == 'Added':
                item_summary[display_name]['added'] += item.quantity
            elif item.action == 'Removed':
                item_summary[display_name]['removed'] += item.quantity
                
            item_summary[display_name]['net'] = item_summary[display_name]['added'] - item_summary[display_name]['removed']
            
            if not item_summary[display_name]['last_activity'] or item.timestamp > item_summary[display_name]['last_activity']:
                item_summary[display_name]['last_activity'] = item.timestamp
        
        history_data = {
            'contract_number': contract_number,
            'client_name': contract_info.client_name if contract_info else 'N/A',
            'total_entries': len(hand_counted_items),
            'current_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'item_summary': [
                {
                    'item_name': name,
                    'total_added': summary['added'],
                    'total_removed': summary['removed'],
                    'net_quantity': summary['net'],
                    'last_activity': summary['last_activity'].strftime('%Y-%m-%d %H:%M') if summary['last_activity'] else 'N/A'
                }
                for name, summary in sorted(item_summary.items())
            ],
            'chronological_history': [{
                'item_name': item_tuple.HandCountedCatalog.hand_counted_name if item_tuple.HandCountedCatalog and item_tuple.HandCountedCatalog.hand_counted_name else item_tuple.HandCountedItems.item_name,
                'quantity': item_tuple.HandCountedItems.quantity,
                'action': item_tuple.HandCountedItems.action,
                'timestamp': item_tuple.HandCountedItems.timestamp.strftime('%Y-%m-%d %H:%M:%S') if item_tuple.HandCountedItems.timestamp else 'N/A',
                'user': item_tuple.HandCountedItems.user or 'N/A'
            } for item_tuple in hand_counted_items]
        }
        
        html = render_template('hand_counted_history_print.html', data=history_data)
        response = make_response(html)
        response.headers['Content-Type'] = 'text/html'
        response.headers['Content-Disposition'] = f'inline; filename=hand_counted_history_{contract_number}.html'
        return response
        
    except Exception as e:
        logger.error(f"Error generating hand counted history print: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab4_bp.route('/tab/4/contract_items_print')
def contract_items_print():
    """Generate professional printable contract items list."""
    contract_number = request.args.get('contract_number')
    
    if not contract_number:
        return jsonify({'error': 'Contract number is required'}), 400
    
    session = None
    try:
        session = db.session()
        
        # Get contract info
        try:
            contract_info = session.query(Transaction).filter(
                Transaction.contract_number == contract_number
            ).first()
            
            if not contract_info:
                return jsonify({'error': f'Contract {contract_number} not found'}), 404
            
            # Get date range
            date_info = session.query(
                func.min(Transaction.scan_date).label('start_date'),
                func.max(Transaction.scan_date).label('last_activity')
            ).filter(
                Transaction.contract_number == contract_number
            ).first()
            
        except Exception as e:
            logger.error(f"Error querying contract info: {str(e)}", exc_info=True)
            return jsonify({'error': 'Database error'}), 500
        
        # Try to get items from contract snapshots first (for historical accuracy)
        from ..models.db_models import ContractSnapshot
        snapshot_items = session.query(ContractSnapshot).filter(
            ContractSnapshot.contract_number == contract_number
        ).order_by(ContractSnapshot.common_name, ContractSnapshot.tag_id).all()
        
        if snapshot_items:
            # Use historical snapshot data
            items = snapshot_items
            logger.info(f"Using {len(snapshot_items)} snapshot items for contract {contract_number}")
        else:
            # Fallback to current ItemMaster data  
            items = session.query(ItemMaster).filter(
                ItemMaster.last_contract_num == contract_number
            ).order_by(ItemMaster.common_name, ItemMaster.tag_id).all()
            logger.info(f"Using {len(items)} current items for contract {contract_number} (no snapshots found)")
        
        # Prepare data for template
        items_data = {
            'contract_number': contract_number,
            'client_name': contract_info.client_name or 'N/A',
            'start_date': date_info.start_date.strftime('%Y-%m-%d') if date_info and date_info.start_date else 'N/A',
            'last_activity': date_info.last_activity.strftime('%Y-%m-%d') if date_info and date_info.last_activity else 'N/A',
            'total_items': len(items),
            'current_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'contract_items': items
        }
        
        html = render_template('contract_items_print.html', data=items_data)
        response = make_response(html)
        response.headers['Content-Type'] = 'text/html'
        response.headers['Content-Disposition'] = f'inline; filename=contract_items_{contract_number}.html'
        return response
        
    except Exception as e:
        logger.error(f"Error generating contract items print: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab4_bp.route('/tab/4/create_contract_snapshot', methods=['POST'])
def create_contract_snapshot():
    """Create a snapshot of all items on a contract for historical preservation."""
    from ..services.contract_snapshots import ContractSnapshotService
    
    data = request.get_json()
    contract_number = data.get('contract_number')
    snapshot_type = data.get('snapshot_type', 'manual')
    created_by = data.get('created_by', 'user')
    
    if not contract_number:
        return jsonify({'error': 'Contract number is required'}), 400
    
    try:
        snapshot_count = ContractSnapshotService.create_contract_snapshot(
            contract_number, snapshot_type, created_by
        )
        
        return jsonify({
            'success': True,
            'message': f'Created snapshot for contract {contract_number}',
            'items_count': snapshot_count
        })
        
    except Exception as e:
        logger.error(f"Error creating contract snapshot: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@tab4_bp.route('/tab/4/snapshot_status')
def snapshot_status():
    """Get status of automated snapshots and schedule info."""
    try:
        from ..services.scheduled_snapshots import ScheduledSnapshotService
        import json
        import os
        
        # Get schedule info
        schedule_info = ScheduledSnapshotService.get_snapshot_schedule_info()
        
        # Try to read last run summary
        last_run_file = os.path.join(config.BASE_DIR, 'logs', 'last_snapshot_run.json')
        last_run_info = None
        
        if os.path.exists(last_run_file):
            try:
                with open(last_run_file, 'r') as f:
                    last_run_info = json.load(f)
            except Exception as e:
                logger.warning(f"Could not read last run file: {str(e)}")
        
        return jsonify({
            'schedule_info': schedule_info,
            'last_run': last_run_info,
            'automation_enabled': True,
            'log_files': {
                'detailed_log': os.path.join(config.BASE_DIR, 'logs', 'snapshot_automation.log'),
                'cron_log': os.path.join(config.BASE_DIR, 'logs', 'snapshot_cron.log'),
                'status_summary': os.path.join(config.BASE_DIR, 'logs', 'last_snapshot_run.json')
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting snapshot status: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@tab4_bp.route('/tab/4/hand_counted_items')
def tab4_hand_counted_items():
    contract_number = request.args.get('contract_number', None)
    logger.info(f"Fetching hand-counted items for contract_number={contract_number} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    current_app.logger.info(f"Fetching hand-counted items for contract_number={contract_number} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    session = None
    try:
        session = db.session()
        query = session.query(HandCountedItems).order_by(HandCountedItems.timestamp.desc())
        if contract_number:
            query = query.filter(HandCountedItems.contract_number == contract_number)
        # Limit to the last 10 entries
        items = query.limit(10).all()
        logger.info(f"Found {len(items)} hand-counted items for contract {contract_number} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.info(f"Found {len(items)} hand-counted items for contract {contract_number} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

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
        logger.error(f"Error fetching hand-counted items for contract {contract_number}: {str(e)} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.error(f"Error fetching hand-counted items for contract {contract_number}: {str(e)} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return '<tr><td colspan="6">Error loading hand-counted items.</td></tr>'
    finally:
        if session:
            session.close()

@tab4_bp.route('/tab/4/add_hand_counted_item', methods=['POST'])
def add_hand_counted_item():
    data = request.get_json()
    contract_number = data.get('contract_number')
    item_name = data.get('item_name')
    quantity = data.get('quantity')
    action = data.get('action')
    employee_name = data.get('employee_name')

    logger.info(f"Adding hand-counted item: contract_number={contract_number}, item_name={item_name}, quantity={quantity}, action={action}, employee_name={employee_name} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    current_app.logger.info(f"Adding hand-counted item: contract_number={contract_number}, item_name={item_name}, quantity={quantity}, action={action}, employee_name={employee_name} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    if not all([contract_number, item_name, quantity, action, employee_name]):
        logger.error("Missing required fields for adding hand-counted item at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.error("Missing required fields for adding hand-counted item at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return jsonify({'error': 'All fields are required'}), 400

    # Validate quantity
    try:
        quantity = int(quantity)
        if quantity <= 0:
            logger.error("Quantity must be a positive integer at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            current_app.logger.error("Quantity must be a positive integer at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            return jsonify({'error': 'Quantity must be a positive integer'}), 400
    except ValueError:
        logger.error("Quantity must be a valid integer at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.error("Quantity must be a valid integer at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return jsonify({'error': 'Quantity must be a valid integer'}), 400

    session = None
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
        logger.info(f"Successfully added hand-counted item for contract {contract_number} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.info(f"Successfully added hand-counted item for contract {contract_number} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return jsonify({'message': f'Successfully added {quantity} {item_name} to {contract_number}'})
    except Exception as e:
        logger.error(f"Error adding hand-counted item: {str(e)} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.error(f"Error adding hand-counted item: {str(e)} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return jsonify({'error': 'Failed to add item'}), 500
    finally:
        if session:
            session.close()

@tab4_bp.route('/tab/4/remove_hand_counted_item', methods=['POST'])
def remove_hand_counted_item():
    data = request.get_json()
    contract_number = data.get('contract_number')
    item_name = data.get('item_name')
    quantity = data.get('quantity')
    action = data.get('action')
    employee_name = data.get('employee_name')

    logger.info(f"Removing hand-counted item: contract_number={contract_number}, item_name={item_name}, quantity={quantity}, action={action}, employee_name={employee_name} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    current_app.logger.info(f"Removing hand-counted item: contract_number={contract_number}, item_name={item_name}, quantity={quantity}, action={action}, employee_name={employee_name} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    if not all([contract_number, item_name, quantity, action, employee_name]):
        logger.error("Missing required fields for removing hand-counted item at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.error("Missing required fields for removing hand-counted item at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return jsonify({'error': 'All fields are required'}), 400

    # Validate quantity
    try:
        quantity = int(quantity)
        if quantity <= 0:
            logger.error("Quantity must be a positive integer at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            current_app.logger.error("Quantity must be a positive integer at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            return jsonify({'error': 'Quantity must be a positive integer'}), 400
    except ValueError:
        logger.error("Quantity must be a valid integer at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.error("Quantity must be a valid integer at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
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
        logger.info(f"Current quantity for {contract_number}/{item_name}: Added={added_quantity}, Removed={removed_quantity}, Net={current_quantity} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        # Check if removal is possible
        if current_quantity < quantity:
            logger.info(f"Cannot remove {quantity} items from {contract_number}/{item_name}: current_quantity={current_quantity} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            current_app.logger.info(f"Cannot remove {quantity} items from {contract_number}/{item_name}: current_quantity={current_quantity} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
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
        logger.info(f"Successfully removed {quantity} hand-counted items for contract {contract_number}, item {item_name} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.info(f"Successfully removed {quantity} hand-counted items for contract {contract_number}, item {item_name} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return jsonify({'message': f'Successfully removed {quantity} {item_name} from {contract_number}'})
    except Exception as e:
        logger.error(f"Error removing hand-counted item: {str(e)} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.error(f"Error removing hand-counted item: {str(e)} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return jsonify({'error': 'Failed to remove item'}), 500
    finally:
        if session:
            session.close()

@tab4_bp.route('/tab/4/full_items_by_rental_class')
def full_items_by_rental_class():
    contract_number = request.args.get('category')
    common_name = request.args.get('common_name')

    if not contract_number or not common_name:
        logger.error("Category (contract_number) and common name are required at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.error("Category (contract_number) and common name are required at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
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

        return jsonify({
            'items': items_data,
            'total_items': len(items_data)
        })
    except Exception as e:
        logger.error(f"Error fetching full items for contract {contract_number}, common_name {common_name}: {str(e)} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.error(f"Error fetching full items for contract {contract_number}, common_name {common_name}: {str(e)} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return jsonify({'error': 'Failed to fetch full items'}), 500
    finally:
        if session:
            session.close()

@tab4_bp.route('/get_contract_date')
def get_contract_date():
    contract_number = request.args.get('contract_number')
    if not contract_number:
        logger.error("Missing required parameter: contract_number is required at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.error("Missing required parameter: contract_number is required at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return jsonify({'error': 'Contract number is required'}), 400

    session = None
    try:
        session = db.session()
        latest_transaction = session.query(Transaction.scan_date).filter(
            Transaction.contract_number == contract_number,
            Transaction.scan_type == 'Rental'
        ).order_by(desc(Transaction.scan_date)).first()
        if latest_transaction and latest_transaction.scan_date:
            return jsonify({'date': latest_transaction.scan_date.isoformat()})
        return jsonify({'date': 'N/A'})
    except Exception as e:
        logger.error(f"Error fetching contract date for {contract_number}: {str(e)} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        current_app.logger.error(f"Error fetching contract date for {contract_number}: {str(e)} at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return jsonify({'error': 'Failed to fetch contract date'}), 500
    finally:
        if session:
            session.close()

@tab4_bp.route('/tab/4/finalize_contract', methods=['POST'])
def finalize_contract():
    """Mark a laundry contract as finalized (final count, picked up by cleaning service)"""
    data = request.get_json()
    contract_number = data.get('contract_number')
    user = data.get('user', 'user')
    notes = data.get('notes', '')
    
    if not contract_number:
        return jsonify({'error': 'Contract number is required'}), 400
    
    session = None
    try:
        session = db.session()
        
        # Check if status record already exists
        status_record = session.query(LaundryContractStatus).filter(
            LaundryContractStatus.contract_number == contract_number
        ).first()
        
        if status_record:
            # Update existing record
            status_record.status = 'finalized'
            status_record.finalized_date = datetime.now()
            status_record.finalized_by = user
            if notes:
                status_record.notes = notes
        else:
            # Create new record
            status_record = LaundryContractStatus(
                contract_number=contract_number,
                status='finalized',
                finalized_date=datetime.now(),
                finalized_by=user,
                notes=notes
            )
            session.add(status_record)
        
        session.commit()
        logger.info(f"Contract {contract_number} finalized by {user}")
        
        return jsonify({
            'success': True,
            'message': f'Contract {contract_number} has been finalized',
            'status': 'finalized',
            'finalized_date': status_record.finalized_date.isoformat()
        })
        
    except Exception as e:
        if session:
            session.rollback()
        logger.error(f"Error finalizing contract {contract_number}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab4_bp.route('/tab/4/mark_returned', methods=['POST'])
def mark_returned():
    """Mark a laundry contract as returned from cleaning service"""
    data = request.get_json()
    contract_number = data.get('contract_number')
    user = data.get('user', 'user')
    notes = data.get('notes', '')
    
    if not contract_number:
        return jsonify({'error': 'Contract number is required'}), 400
    
    session = None
    try:
        session = db.session()
        
        # Check if status record already exists
        status_record = session.query(LaundryContractStatus).filter(
            LaundryContractStatus.contract_number == contract_number
        ).first()
        
        if status_record:
            # Update existing record
            status_record.status = 'returned'
            status_record.returned_date = datetime.now()
            status_record.returned_by = user
            if notes:
                existing_notes = status_record.notes or ''
                status_record.notes = f"{existing_notes}\n{notes}" if existing_notes else notes
        else:
            # Create new record (shouldn't happen, but handle it)
            status_record = LaundryContractStatus(
                contract_number=contract_number,
                status='returned',
                returned_date=datetime.now(),
                returned_by=user,
                notes=notes
            )
            session.add(status_record)
        
        session.commit()
        logger.info(f"Contract {contract_number} marked as returned by {user}")
        
        return jsonify({
            'success': True,
            'message': f'Contract {contract_number} has been marked as returned',
            'status': 'returned',
            'returned_date': status_record.returned_date.isoformat()
        })
        
    except Exception as e:
        if session:
            session.rollback()
        logger.error(f"Error marking contract {contract_number} as returned: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab4_bp.route('/tab/4/reactivate_contract', methods=['POST'])
def reactivate_contract():
    """Reactivate a finalized or returned contract"""
    data = request.get_json()
    contract_number = data.get('contract_number')
    user = data.get('user', 'user')
    notes = data.get('notes', '')
    
    if not contract_number:
        return jsonify({'error': 'Contract number is required'}), 400
    
    session = None
    try:
        session = db.session()
        
        # Check if status record exists
        status_record = session.query(LaundryContractStatus).filter(
            LaundryContractStatus.contract_number == contract_number
        ).first()
        
        if status_record:
            # Update to active status
            status_record.status = 'active'
            # Clear finalized/returned dates if reactivating
            status_record.finalized_date = None
            status_record.finalized_by = None
            status_record.returned_date = None
            status_record.returned_by = None
            if notes:
                existing_notes = status_record.notes or ''
                status_record.notes = f"{existing_notes}\nReactivated by {user}: {notes}" if existing_notes else f"Reactivated by {user}: {notes}"
        else:
            # Create new active record
            status_record = LaundryContractStatus(
                contract_number=contract_number,
                status='active',
                notes=f"Reactivated by {user}: {notes}" if notes else f"Reactivated by {user}"
            )
            session.add(status_record)
        
        session.commit()
        logger.info(f"Contract {contract_number} reactivated by {user}")
        
        return jsonify({
            'success': True,
            'message': f'Contract {contract_number} has been reactivated',
            'status': 'active'
        })
        
    except Exception as e:
        if session:
            session.rollback()
        logger.error(f"Error reactivating contract {contract_number}: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()