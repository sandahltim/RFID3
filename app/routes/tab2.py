from flask import Blueprint, render_template, jsonify, current_app, request
from .. import db, cache
from ..models.db_models import ItemMaster, RentalClassMapping, Transaction
from sqlalchemy import func
from urllib.parse import quote
import re
import time

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

        # Format the contract data for the template
        # Fixed on 2025-04-21 to ensure 'on_contracts' is a count, not a date
        categories = [
            {
                'name': contract_num,
                'total_items': total_items,
                'on_contracts': total_items,  # Count of items on contract (status 'on rent' or 'delivered')
                'in_service': 0,  # Placeholder, not used
                'available': 0,   # Placeholder, not used
                'customer_name': customer_name or 'N/A',
                'last_scanned_date': last_scanned_date.isoformat().replace('T', ' ') if last_scanned_date else 'N/A'
            }
            for contract_num, total_items, customer_name, last_scanned_date in contract_data
            if contract_num is not None
        ]
        current_app.logger.info(f"Fetched {len(categories)} rental contracts")
        current_app.logger.debug(f"Raw contract data: {contract_data}")
        # Added on 2025-04-21 to debug display issues
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

@tab2_bp.route('/tab/2/categories')
def tab2_categories():
    # Route to render the categories table for Tab 2
    # Shows all open contracts with columns: Contract Number, Customer Name, Items on Contracts, Last Scanned Date, Actions
    # Hides columns: Total Items, Items in Service, Items Available
    # Fixed on 2025-04-21 to ensure correct column data and visibility
    try:
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

        categories = [
            {
                'name': contract_num,
                'total_items': total_items,
                'on_contracts': total_items,
                'in_service': 0,
                'available': 0,
                'customer_name': customer_name or 'N/A',
                'last_scanned_date': last_scanned_date.isoformat().replace('T', ' ') if last_scanned_date else 'N/A'
            }
            for contract_num, total_items, customer_name, last_scanned_date in contract_data
            if contract_num is not None
        ]
        # Added on 2025-04-21 to debug display issues
        current_app.logger.debug(f"Categories for tab 2 rendering: {categories}")

        # Generate HTML for the table rows with correct column alignment
        html = ''
        for category in categories:
            cat_id = re.sub(r'[^a-z0-9-]', '_', category['name'].lower())
            encoded_category = quote(category['name']).replace("'", "\\'").replace('"', '\\"')
            current_app.logger.debug(f"Encoded category for onclick: {encoded_category}")
            html += f'''
                <tr>
                    <td>{category['name']}</td>
                    <td>{category['customer_name']}</td>
                    <td class="hidden">{category['total_items']}</td>
                    <td>{category['on_contracts']}</td>
                    <td class="hidden">{category['in_service']}</td>
                    <td class="hidden">{category['available']}</td>
                    <td>{category['last_scanned_date']}</td>
                    <td>
                        <button class="btn btn-sm btn-secondary" onclick="expandCategory('{encoded_category}', 'subcat-{cat_id}')">Expand</button>
                        <button class="btn btn-sm btn-info print-btn" data-print-level="Contract" data-print-id="category-table">Print</button>
                        <div id="loading-{cat_id}" style="display:none;" class="loading">Loading...</div>
                    </td>
                </tr>
                <tr>
                    <td colspan="8">
                        <div id="subcat-{cat_id}" class="expandable collapsed"></div>
                    </td>
                </tr>
            '''
        return html
    except Exception as e:
        current_app.logger.error(f"Error fetching contracts for tab 2: {str(e)}", exc_info=True)
        return '<tr><td colspan="8">Error loading contracts</td></tr>'

@tab2_bp.route('/tab/2/subcat_data')
def tab2_subcat_data():
    # Route to fetch subcategory data for a specific contract
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

        current_app.logger.debug(f"Raw category counts for contract {contract_num}: {subcategories}")

        subcat_data = [
            {
                'subcategory': cat,
                'total_items': total_items,
                'on_contracts': on_contracts,
                'in_service': in_service,
                'available': 0
            }
            for cat, total_items, on_contracts, in_service in subcategories
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

        current_app.logger.debug(f"Common names for contract {contract_num}, category: {category}: {common_names}")

        common_names_data = [
            {
                'name': name,
                'total_items': total_items,
                'on_contracts': on_contracts,
                'in_service': in_service,
                'available': 0
            }
            for name, total_items, on_contracts, in_service in common_names
            if name is not None
        ]

        current_app.logger.debug(f"Common names data: {common_names_data}")

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

        current_app.logger.debug(f"Items for contract {contract_num}, category {category}, common_name {common_name}: {len(items)} items found")

        items_data = [
            {
                'tag_id': item.tag_id,
                'common_name': item.common_name,
                'bin_location': item.bin_location,
                'status': item.status,
                'last_contract_num': item.last_contract_num,
                'last_scanned_date': item.date_last_scanned.isoformat().replace('T', ' ') if item.date_last_scanned else None,
                'quality': item.quality,
                'notes': item.notes
            }
            for item in items
        ]

        return jsonify(items_data)
    except Exception as e:
        current_app.logger.error(f"Error fetching data for contract {contract_num}, category {category}, common_name {common_name}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to fetch data: {str(e)}'}), 500