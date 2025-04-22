from flask import Blueprint, render_template, jsonify, current_app, request
from .. import db, cache
from ..models.db_models import ItemMaster, RentalClassMapping, Transaction, HandCountedItems
from sqlalchemy import func
from urllib.parse import quote
import re
import time
from datetime import datetime

# Blueprint for Tab 2 (Open Contracts) - DO NOT MODIFY BLUEPRINT NAME
# Added on 2025-04-21 to display all open contracts
tab2_bp = Blueprint('tab2', __name__)

@tab2_bp.route('/tab/2')
@cache.cached(timeout=30)
def tab2_view():
    # Route to render the main view for Tab 2
    # Displays a list of all open contracts with status 'on rent' or 'delivered'
    try:
        current_app.logger.info("Loading tab 2")

        # Query to fetch all open contracts from ItemMaster
        # Filters by status 'on rent' or 'delivered', groups by last_contract_num
        # Includes customer name and most recent scanned date
        contract_data = db.session.query(
            ItemMaster.last_contract_num,
            func.count(ItemMaster.tag_id).label('total_items'),
            func.max(Transaction.client_name).label('customer_name'),
            func.max(ItemMaster.date_last_scanned).label('last_scanned_date')
        ).outerjoin(
            Transaction, Transaction.contract_number == ItemMaster.last_contract_num
        ).filter(
            func.lower(ItemMaster.status).in_(['on rent', 'delivered'])
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
            HandCountedItems.action == 'Added'
        ).group_by(
            HandCountedItems.contract_number
        ).all()

        hand_counted_dict = {row.contract_number: row.hand_counted_total for row in hand_counted_data}

        # Format the contract data for the template
        # Include hand-counted items in the total under the same contract
        categories = []
        for contract_num, total_items, customer_name, last_scanned_date in contract_data:
            if contract_num is None:
                continue
            hand_counted_items = hand_counted_dict.get(contract_num, 0)
            total_with_hand_counted = total_items + hand_counted_items
            # Sanitize cat_id in Python
            cat_id = re.sub(r'[^a-z0-9-]', '_', contract_num.lower())
            # Format last_scanned_date to MM/DD/YYYY, h:mm:ss AM/PM
            formatted_date = last_scanned_date.strftime('%m/%d/%Y, %I:%M:%S %p') if last_scanned_date else 'N/A'
            categories.append({
                'name': contract_num,
                'cat_id': cat_id,  # Add sanitized cat_id
                'total_items': total_with_hand_counted,
                'on_contracts': total_with_hand_counted,  # Count includes hand-counted items
                'in_service': 0,  # Placeholder, not used
                'available': 0,   # Placeholder, not used
                'customer_name': customer_name or 'N/A',
                'last_scanned_date': formatted_date
            })
        current_app.logger.info(f"Fetched {len(categories)} rental contracts")
        current_app.logger.debug(f"Raw contract data: {contract_data}")
        current_app.logger.debug(f"Hand-counted data: {hand_counted_dict}")
        current_app.logger.debug(f"Formatted categories for tab 2: {categories}")

        # Fetch bin locations for filtering
        bin_locations = db.session.query(
            ItemMaster.bin_location
        ).filter(
            ItemMaster.bin_location.isnot(None)
        ).distinct().order_by(
            ItemMaster.bin_location
        ).all()
        bin_locations = [loc[0] for loc in bin_locations]
        current_app.logger.info(f"Fetched {len(bin_locations)} bin locations")

        # Fetch statuses for filtering
        statuses = db.session.query(
            ItemMaster.status
        ).filter(
            ItemMaster.status.isnot(None)
        ).distinct().order_by(
            ItemMaster.status
        ).all()
        statuses = [status[0] for status in statuses]

        return render_template(
            'tab2.html',
            tab_num=2,
            categories=categories,
            bin_locations=bin_locations,
            statuses=statuses,
            cache_bust=int(time.time()),
            timestamp=lambda: int(time.time())
        )
    except Exception as e:
        current_app.logger.error(f"Error loading tab 2: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to load tab data'}), 500

@tab2_bp.route('/tab/2/subcat_data')
def tab2_subcat_data():
    # Route to fetch subcategory data for a specific contract
    # Updated on 2025-04-21 to combine hand-counted items under the same contract
    try:
        current_app.logger.info("Received request for /tab/2/subcat_data")
        contract_num = request.args.get('category')  # For Tab 2, 'category' is the contract number
        if not contract_num:
            current_app.logger.error("Contract parameter is missing")
            return jsonify({'error': 'Contract parameter is required'}), 400

        subcategories = db.session.query(
            func.coalesce(RentalClassMapping.category, 'Unclassified').label('category'),
            func.count(ItemMaster.tag_id).label('total_items'),
            func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['on rent', 'delivered']), db.Integer)), 0).label('on_contracts'),
            func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['repair']), db.Integer)), 0).label('in_service')
        ).outerjoin(
            RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
        ).filter(
            func.lower(ItemMaster.status).in_(['on rent', 'delivered']),
            ItemMaster.last_contract_num == contract_num
        ).group_by(
            func.coalesce(RentalClassMapping.category, 'Unclassified')
        ).all()

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
                'total_items': total_items,
                'on_contracts': on_contracts,
                'in_service': in_service,
                'available': 0
            }
            for cat, total_items, on_contracts, in_service in subcategories
        }

        # Merge hand-counted items into the subcategories
        for h_cat, h_total in hand_counted_subcat_data:
            if h_cat in subcat_dict:
                # Add hand-counted items to existing subcategory
                subcat_dict[h_cat]['total_items'] += h_total
                subcat_dict[h_cat]['on_contracts'] += h_total
            else:
                # Create new subcategory entry for hand-counted item
                subcat_dict[h_cat] = {
                    'total_items': h_total,
                    'on_contracts': h_total,
                    'in_service': 0,
                    'available': 0
                }

        subcat_data = [
            {
                'subcategory': cat,
                'total_items': data['total_items'],
                'on_contracts': data['on_contracts'],
                'in_service': data['in_service'],
                'available': data['available']
            }
            for cat, data in subcat_dict.items()
        ]

        current_app.logger.info(f"Fetched {len(subcat_data)} categories for contract {contract_num}")
        current_app.logger.debug(f"Subcategory data for contract {contract_num}: {subcat_data}")

        return jsonify(subcat_data)
    except Exception as e:
        current_app.logger.error(f"Error fetching categories for contract {contract_num}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch subcategory data'}), 500

@tab2_bp.route('/tab/2/common_names')
def tab2_common_names():
    try:
        contract_num = request.args.get('category')  # Contract number
        category = request.args.get('subcategory')  # Category under the contract
        if not contract_num or not category:
            return jsonify({'error': 'Contract and category parameters are required'}), 400

        current_app.logger.debug(f"Fetching common names for contract: {contract_num}, category: {category}")

        if category == 'Unclassified':
            common_names = db.session.query(
                func.trim(func.upper(ItemMaster.common_name)).label('common_name'),
                func.count(ItemMaster.tag_id).label('total_items'),
                func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['on rent', 'delivered']), db.Integer)), 0).label('on_contracts'),
                func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['repair']), db.Integer)), 0).label('in_service')
            ).outerjoin(
                RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
            ).filter(
                func.lower(ItemMaster.status).in_(['on rent', 'delivered']),
                ItemMaster.last_contract_num == contract_num,
                RentalClassMapping.category.is_(None)
            ).group_by(
                func.trim(func.upper(ItemMaster.common_name))
            ).all()
        else:
            common_names = db.session.query(
                func.trim(func.upper(ItemMaster.common_name)).label('common_name'),
                func.count(ItemMaster.tag_id).label('total_items'),
                func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['on rent', 'delivered']), db.Integer)), 0).label('on_contracts'),
                func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['repair']), db.Integer)), 0).label('in_service')
            ).join(
                RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
            ).filter(
                func.lower(ItemMaster.status).in_(['on rent', 'delivered']),
                ItemMaster.last_contract_num == contract_num,
                func.lower(RentalClassMapping.category) == func.lower(category)
            ).group_by(
                func.trim(func.upper(ItemMaster.common_name))
            ).all()

        # Include hand-counted items if they match the category
        hand_counted_common_names = db.session.query(
            HandCountedItems.item_name.label('common_name'),
            func.sum(HandCountedItems.quantity).label('hand_counted_total')
        ).filter(
            HandCountedItems.contract_number == contract_num,
            HandCountedItems.item_name == category,
            HandCountedItems.action == 'Added'
        ).group_by(
            HandCountedItems.item_name
        ).all()

        # Convert common names to a dictionary for merging
        common_dict = {
            name: {
                'total_items': total_items,
                'on_contracts': on_contracts,
                'in_service': in_service,
                'available': 0
            }
            for name, total_items, on_contracts, in_service in common_names
            if name is not None
        }

        # Merge hand-counted items into the common names
        for h_name, h_total in hand_counted_common_names:
            if h_name in common_dict:
                common_dict[h_name]['total_items'] += h_total
                common_dict[h_name]['on_contracts'] += h_total
            else:
                common_dict[h_name] = {
                    'total_items': h_total,
                    'on_contracts': h_total,
                    'in_service': 0,
                    'available': 0
                }

        common_names_data = [
            {
                'name': name,
                'total_items': data['total_items'],
                'on_contracts': data['on_contracts'],
                'in_service': data['in_service'],
                'available': data['available']
            }
            for name, data in common_dict.items()
        ]

        current_app.logger.debug(f"Common names for contract {contract_num}, category: {category}: {common_names_data}")

        return jsonify({'common_names': common_names_data})
    except Exception as e:
        current_app.logger.error(f"Error fetching common names for contract {contract_num}, category: {category}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to fetch common names: {str(e)}'}), 500

@tab2_bp.route('/tab/2/data')
def tab2_data():
    try:
        contract_num = request.args.get('category')
        category = request.args.get('subcategory')
        common_name = request.args.get('common_name')
        if not contract_num or not category or not common_name:
            return jsonify({'error': 'Contract, category, and common_name parameters are required'}), 400

        current_app.logger.debug(f"Fetching items for contract {contract_num}, category {category}, common_name {common_name}")

        if category == 'Unclassified':
            items = db.session.query(
                ItemMaster
            ).outerjoin(
                RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
            ).filter(
                func.lower(ItemMaster.status).in_(['on rent', 'delivered']),
                ItemMaster.last_contract_num == contract_num,
                RentalClassMapping.category.is_(None),
                func.trim(func.upper(ItemMaster.common_name)) == func.trim(func.upper(common_name))
            ).all()
        else:
            items = db.session.query(
                ItemMaster
            ).join(
                RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
            ).filter(
                func.lower(ItemMaster.status).in_(['on rent', 'delivered']),
                ItemMaster.last_contract_num == contract_num,
                func.lower(RentalClassMapping.category) == func.lower(category),
                func.trim(func.upper(ItemMaster.common_name)) == func.trim(func.upper(common_name))
            ).all()

        # Hand-counted items don't have individual item details, so they won't appear here
        # They are already included in the counts at the subcategory and common name levels

        current_app.logger.debug(f"Items for contract {contract_num}, category {category}, common_name {common_name}: {len(items)} items found")

        items_data = [
            {
                'tag_id': item.tag_id,
                'common_name': item.common_name,
                'bin_location': item.bin_location,
                'status': item.status,
                'last_contract_num': item.last_contract_num,
                'last_scanned_date': item.date_last_scanned.strftime('%m/%d/%Y, %I:%M:%S %p') if item.date_last_scanned else 'N/A',
                'quality': item.quality,
                'notes': item.notes
            }
            for item in items
        ]

        return jsonify(items_data)
    except Exception as e:
        current_app.logger.error(f"Error fetching data for contract {contract_num}, category {category}, common_name {common_name}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to fetch data: {str(e)}'}), 500