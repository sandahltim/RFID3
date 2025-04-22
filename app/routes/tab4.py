from flask import Blueprint, render_template, jsonify, current_app, request
from .. import db, cache
from ..models.db_models import ItemMaster, RentalClassMapping, Transaction, HandCountedItems
from sqlalchemy import func
from urllib.parse import quote
import re
import time
from datetime import datetime

# Blueprint for Tab 4 (Laundry Tab) - DO NOT MODIFY BLUEPRINT NAME
# Added on 2025-04-21 to display laundry contracts (starting with 'L')
tab4_bp = Blueprint('tab4', __name__)

@tab4_bp.route('/tab/4')
@cache.cached(timeout=30)
def tab4_view():
    # Route to render the main view for Tab 4
    # Displays a list of laundry contracts (starting with 'L') with status 'on rent' or 'delivered'
    try:
        current_app.logger.info("Loading tab 4 (Laundry)")

        # Query to fetch laundry contracts (starting with 'L') from ItemMaster
        # Filters by status 'on rent' or 'delivered', groups by last_contract_num
        # Includes customer name and most recent scanned date
        contract_data = db.session.query(
            ItemMaster.last_contract_num,
            func.count(ItemMaster.tag_id).label('tagged_items'),
            func.max(Transaction.client_name).label('customer_name'),
            func.max(ItemMaster.date_last_scanned).label('last_scanned_date')
        ).outerjoin(
            Transaction, Transaction.contract_number == ItemMaster.last_contract_num
        ).filter(
            func.lower(ItemMaster.status).in_(['on rent', 'delivered']),
            func.lower(ItemMaster.last_contract_num).like('l%')  # Only laundry contracts
        ).group_by(
            ItemMaster.last_contract_num
        ).order_by(
            ItemMaster.last_contract_num
        ).all()

        # Fetch hand-counted items to add to the counts
        hand_counted_data = db.session.query(
            HandCountedItems.contract_number,
            func.sum(HandCountedItems.quantity).label('hand_counted_total')
        ).filter(
            func.lower(HandCountedItems.contract_number).like('l%'),
            HandCountedItems.action == 'Added'
        ).group_by(
            HandCountedItems.contract_number
        ).all()

        hand_counted_dict = {row.contract_number: row.hand_counted_total for row in hand_counted_data}

        # Format the contract data for the template
        categories = []
        for contract_num, tagged_items, customer_name, last_scanned_date in contract_data:
            if contract_num is None:
                continue
            # Get hand-counted items for this contract
            hand_counted_items = hand_counted_dict.get(contract_num, 0)
            # Sum tagged items and hand-counted items
            total_items = tagged_items + hand_counted_items
            # Sanitize cat_id in Python
            cat_id = re.sub(r'[^a-z0-9-]', '_', contract_num.lower())
            # Format last_scanned_date to MM/DD/YYYY, h:mm:ss AM/PM
            formatted_date = last_scanned_date.strftime('%m/%d/%Y, %I:%M:%S %p') if last_scanned_date else 'N/A'
            categories.append({
                'name': contract_num,
                'cat_id': cat_id,
                'total_items': total_items,  # Total Items on Contract (tagged + hand-counted)
                'customer_name': customer_name or 'N/A',
                'last_scanned_date': formatted_date
            })
        current_app.logger.info(f"Fetched {len(categories)} laundry contracts")
        current_app.logger.debug(f"Raw contract data: {contract_data}")
        current_app.logger.debug(f"Hand-counted data: {hand_counted_dict}")
        current_app.logger.debug(f"Formatted categories for tab 4: {categories}")

        # Fetch bin locations for filtering (same as Tab 2)
        bin_locations = db.session.query(
            ItemMaster.bin_location
        ).filter(
            ItemMaster.bin_location.isnot(None)
        ).distinct().order_by(
            ItemMaster.bin_location
        ).all()
        bin_locations = [loc[0] for loc in bin_locations]
        current_app.logger.info(f"Fetched {len(bin_locations)} bin locations")

        # Fetch statuses for filtering (same as Tab 2)
        statuses = db.session.query(
            ItemMaster.status
        ).filter(
            ItemMaster.status.isnot(None)
        ).distinct().order_by(
            ItemMaster.status
        ).all()
        statuses = [status[0] for status in statuses]

        return render_template(
            'tab4.html',
            tab_num=4,
            categories=categories,
            bin_locations=bin_locations,
            statuses=statuses,
            cache_bust=int(time.time()),
            timestamp=lambda: int(time.time())
        )
    except Exception as e:
        current_app.logger.error(f"Error loading tab 4: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to load tab data'}), 500

@tab4_bp.route('/tab/4/subcat_data')
def tab4_subcat_data():
    # Route to fetch subcategory data for a specific laundry contract
    # Updated to fix Total Items in Inventory and Items on This Contract counts
    try:
        current_app.logger.info("Received request for /tab/4/subcat_data")
        contract_num = request.args.get('category')  # 'category' is the contract number
        page = int(request.args.get('page', 1))
        per_page = 20
        offset = (page - 1) * per_page

        if not contract_num:
            current_app.logger.error("Contract parameter is missing")
            return jsonify({'error': 'Contract parameter is required'}), 400

        # Fetch subcategories from ItemMaster (Items on This Contract)
        base_query = db.session.query(
            func.coalesce(RentalClassMapping.category, 'Unclassified').label('category'),
            func.count(ItemMaster.tag_id).label('items_on_contract')
        ).outerjoin(
            RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
        ).filter(
            func.lower(ItemMaster.status).in_(['on rent', 'delivered']),
            ItemMaster.last_contract_num == contract_num,
            func.lower(ItemMaster.last_contract_num).like('l%')
        ).group_by(
            func.coalesce(RentalClassMapping.category, 'Unclassified')
        )

        total_subcats = base_query.count()
        subcategories = base_query.order_by(
            func.coalesce(RentalClassMapping.category, 'Unclassified')
        ).offset(offset).limit(per_page).all()

        # Fetch total items in inventory for each subcategory (across all contracts, regardless of status)
        total_items_inventory = db.session.query(
            func.coalesce(RentalClassMapping.category, 'Unclassified').label('category'),
            func.count(ItemMaster.tag_id).label('total_items_inventory')
        ).outerjoin(
            RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
        ).group_by(
            func.coalesce(RentalClassMapping.category, 'Unclassified')
        ).all()

        total_items_dict = {cat: total for cat, total in total_items_inventory}

        # Fetch hand-counted items for this contract
        hand_counted_subcat_data = db.session.query(
            HandCountedItems.item_name.label('category'),
            func.sum(HandCountedItems.quantity).label('hand_counted_total')
        ).filter(
            HandCountedItems.contract_number == contract_num,
            HandCountedItems.action == 'Added'
        ).group_by(
            HandCountedItems.item_name
        ).all()

        # Convert subcategories to a dictionary for merging
        subcat_dict = {
            cat: {
                'items_on_contract': items_on_contract,
            }
            for cat, items_on_contract in subcategories
        }

        # Merge hand-counted items into the subcategories
        for h_cat, h_total in hand_counted_subcat_data:
            if h_cat in subcat_dict:
                # Add hand-counted items to existing subcategory
                subcat_dict[h_cat]['items_on_contract'] += h_total
            else:
                # Create new subcategory entry for hand-counted item
                subcat_dict[h_cat] = {
                    'items_on_contract': h_total,
                }

        # Add total items in inventory to each subcategory
        subcat_data = [
            {
                'subcategory': cat,
                'total_items_inventory': total_items_dict.get(cat, 0),
                'items_on_contract': data['items_on_contract'],
            }
            for cat, data in subcat_dict.items()
        ]

        current_app.logger.info(f"Fetched {len(subcat_data)} categories for contract {contract_num}")
        current_app.logger.debug(f"Subcategory data for contract {contract_num}: {subcat_data}")

        return jsonify({
            'subcategories': subcat_data,
            'total_subcats': total_subcats,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching categories for contract {contract_num}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch subcategory data'}), 500

@tab4_bp.route('/tab/4/common_names')
def tab4_common_names():
    try:
        contract_num = request.args.get('category')  # Contract number
        subcategory = request.args.get('subcategory')  # Subcategory under the contract
        page = int(request.args.get('page', 1))
        per_page = 20
        offset = (page - 1) * per_page

        if not contract_num or not subcategory:
            return jsonify({'error': 'Contract and subcategory parameters are required'}), 400

        current_app.logger.debug(f"Fetching common names for contract: {contract_num}, subcategory: {subcategory}")

        # Fetch common names for this contract and subcategory (Items on This Contract)
        if subcategory == 'Unclassified':
            base_query = db.session.query(
                func.trim(func.upper(ItemMaster.common_name)).label('common_name'),
                func.count(ItemMaster.tag_id).label('items_on_contract')
            ).outerjoin(
                RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
            ).filter(
                func.lower(ItemMaster.status).in_(['on rent', 'delivered']),
                ItemMaster.last_contract_num == contract_num,
                func.lower(ItemMaster.last_contract_num).like('l%'),
                RentalClassMapping.category.is_(None)
            ).group_by(
                func.trim(func.upper(ItemMaster.common_name))
            )
        else:
            base_query = db.session.query(
                func.trim(func.upper(ItemMaster.common_name)).label('common_name'),
                func.count(ItemMaster.tag_id).label('items_on_contract')
            ).join(
                RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
            ).filter(
                func.lower(ItemMaster.status).in_(['on rent', 'delivered']),
                ItemMaster.last_contract_num == contract_num,
                func.lower(ItemMaster.last_contract_num).like('l%'),
                func.lower(RentalClassMapping.category) == func.lower(subcategory)
            ).group_by(
                func.trim(func.upper(ItemMaster.common_name))
            )

        total_common_names = base_query.count()
        common_names = base_query.order_by(
            func.trim(func.upper(ItemMaster.common_name))
        ).offset(offset).limit(per_page).all()

        # Fetch total items in inventory for each common name (across all contracts, regardless of status)
        total_items_inventory = db.session.query(
            func.trim(func.upper(ItemMaster.common_name)).label('common_name'),
            func.count(ItemMaster.tag_id).label('total_items_inventory')
        ).group_by(
            func.trim(func.upper(ItemMaster.common_name))
        ).all()

        total_items_dict = {name: total for name, total in total_items_inventory if name is not None}

        # Include hand-counted items if they match the subcategory
        hand_counted_common_names = db.session.query(
            HandCountedItems.item_name.label('common_name'),
            func.sum(HandCountedItems.quantity).label('hand_counted_total')
        ).filter(
            HandCountedItems.contract_number == contract_num,
            HandCountedItems.item_name == subcategory,
            HandCountedItems.action == 'Added'
        ).group_by(
            HandCountedItems.item_name
        ).all()

        # Convert common names to a dictionary for merging
        common_dict = {
            name: {
                'items_on_contract': items_on_contract,
            }
            for name, items_on_contract in common_names
            if name is not None
        }

        # Merge hand-counted items into the common names
        for h_name, h_total in hand_counted_common_names:
            if h_name in common_dict:
                common_dict[h_name]['items_on_contract'] += h_total
            else:
                common_dict[h_name] = {
                    'items_on_contract': h_total,
                }

        # Add total items in inventory to each common name
        common_names_data = [
            {
                'name': name,
                'total_items_inventory': total_items_dict.get(name, 0),
                'items_on_contract': data['items_on_contract'],
            }
            for name, data in common_dict.items()
        ]

        current_app.logger.debug(f"Common names for contract {contract_num}, subcategory: {subcategory}: {common_names_data}")

        return jsonify({
            'common_names': common_names_data,
            'total_common_names': total_common_names,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching common names for contract {contract_num}, subcategory: {subcategory}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to fetch common names: {str(e)}'}), 500

@tab4_bp.route('/tab/4/data')
def tab4_data():
    try:
        contract_num = request.args.get('category')
        subcategory = request.args.get('subcategory')
        common_name = request.args.get('common_name')
        page = int(request.args.get('page', 1))
        per_page = 20
        offset = (page - 1) * per_page

        if not contract_num or not subcategory or not common_name:
            return jsonify({'error': 'Contract, subcategory, and common_name parameters are required'}), 400

        current_app.logger.debug(f"Fetching items for contract {contract_num}, subcategory {subcategory}, common_name {common_name}, page {page}")

        # Base query for items
        base_query = db.session.query(ItemMaster).outerjoin(
            RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
        ).filter(
            func.lower(ItemMaster.status).in_(['on rent', 'delivered']),
            ItemMaster.last_contract_num == contract_num,
            func.lower(ItemMaster.last_contract_num).like('l%'),
            func.trim(func.upper(ItemMaster.common_name)) == func.trim(func.upper(common_name))
        )

        if subcategory != 'Unclassified':
            base_query = base_query.filter(
                func.lower(RentalClassMapping.category) == func.lower(subcategory)
            )
        else:
            base_query = base_query.filter(
                RentalClassMapping.category.is_(None)
            )

        # Get total items for pagination
        total_items = base_query.count()

        # Apply pagination
        items = base_query.order_by(ItemMaster.tag_id).offset(offset).limit(per_page).all()

        current_app.logger.debug(f"Items for contract {contract_num}, subcategory {subcategory}, common_name {common_name}: {len(items)} items found (total {total_items})")

        items_data = [
            {
                'tag_id': item.tag_id,
                'common_name': item.common_name,
                'bin_location': item.bin_location,
                'status': item.status,
                'last_contract_num': item.last_contract_num,
                'last_scanned_date': item.date_last_scanned.strftime('%m/%d/%Y, %I:%M:%S %p') if item.date_last_scanned else 'N/A',
            }
            for item in items
        ]

        return jsonify({
            'items': items_data,
            'total_items': total_items,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching data for contract {contract_num}, subcategory {subcategory}, common_name {common_name}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to fetch data: {str(e)}'}), 500

@tab4_bp.route('/tab/4/add_hand_counted_item', methods=['POST'])
def add_hand_counted_item():
    try:
        data = request.get_json()
        contract_number = data.get('contract_number')
        item_name = data.get('item_name')
        quantity = data.get('quantity')
        action = data.get('action')
        employee_name = data.get('employee_name')

        if not all([contract_number, item_name, quantity, action, employee_name]):
            return jsonify({'error': 'Missing required fields'}), 400

        hand_counted_item = HandCountedItems(
            contract_number=contract_number,
            item_name=item_name,
            quantity=quantity,
            action=action,
            timestamp=datetime.utcnow(),
            user=employee_name
        )
        db.session.add(hand_counted_item)
        db.session.commit()

        current_app.logger.info(f"Added hand-counted item: {item_name} (Qty: {quantity}) to contract {contract_number} by {employee_name}")

        return jsonify({'message': 'Item added successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding hand-counted item: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to add item'}), 500

@tab4_bp.route('/tab/4/remove_hand_counted_item', methods=['POST'])
def remove_hand_counted_item():
    try:
        data = request.get_json()
        contract_number = data.get('contract_number')
        item_name = data.get('item_name')
        quantity = data.get('quantity')
        action = data.get('action')
        employee_name = data.get('employee_name')

        if not all([contract_number, item_name, quantity, action, employee_name]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Calculate the current total quantity for this contract and item
        current_total = db.session.query(
            func.sum(HandCountedItems.quantity).label('total')
        ).filter(
            HandCountedItems.contract_number == contract_number,
            HandCountedItems.item_name == item_name,
            HandCountedItems.action == 'Added'
        ).scalar() or 0

        removed_total = db.session.query(
            func.sum(HandCountedItems.quantity).label('total')
        ).filter(
            HandCountedItems.contract_number == contract_number,
            HandCountedItems.item_name == item_name,
            HandCountedItems.action == 'Removed'
        ).scalar() or 0

        net_quantity = current_total - removed_total
        if net_quantity < quantity:
            return jsonify({'error': f'Cannot remove {quantity} items. Only {net_quantity} items are available.'}), 400

        # Log the removal as a new entry
        hand_counted_item = HandCountedItems(
            contract_number=contract_number,
            item_name=item_name,
            quantity=quantity,
            action=action,
            timestamp=datetime.utcnow(),
            user=employee_name
        )
        db.session.add(hand_counted_item)
        db.session.commit()

        current_app.logger.info(f"Removed hand-counted item: {item_name} (Qty: {quantity}) from contract {contract_number} by {employee_name}")

        return jsonify({'message': 'Item removed successfully'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error removing hand-counted item: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to remove item'}), 500

@tab4_bp.route('/tab/4/hand_counted_items')
def get_hand_counted_items():
    try:
        items = db.session.query(HandCountedItems).order_by(HandCountedItems.timestamp.desc()).all()

        html = ''
        for item in items:
            # Format timestamp to MM/DD/YYYY, h:mm:ss AM/PM
            formatted_timestamp = item.timestamp.strftime('%m/%d/%Y, %I:%M:%S %p') if item.timestamp else 'N/A'
            html += f'''
                <tr>
                    <td>{item.contract_number}</td>
                    <td>{item.item_name}</td>
                    <td>{item.quantity}</td>
                    <td>{item.action}</td>
                    <td>{formatted_timestamp}</td>
                    <td>{item.user}</td>
                </tr>
            '''
        return html
    except Exception as e:
        current_app.logger.error(f"Error fetching hand-counted items: {str(e)}", exc_info=True)
        return '<tr><td colspan="6">Error loading hand-counted items</td></tr>'