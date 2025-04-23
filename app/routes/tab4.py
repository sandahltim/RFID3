from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db, cache
from ..models.db_models import Transaction, ItemMaster, RentalClassMapping, UserRentalClassMapping, HandCountedItems
from sqlalchemy import func, desc, or_
from time import time

tab4_bp = Blueprint('tab4', __name__)

@tab4_bp.route('/tab/4')
def tab4_view():
    current_app.logger.info("Entering tab4_view route")
    try:
        current_app.logger.info("Attempting to create database session")
        session = db.session()
        current_app.logger.info("Database session created successfully")

        # Define laundry-related categories
        laundry_categories = ['Rectangle Linen', 'Round Linen', 'Runners and Drapes']
        current_app.logger.info(f"Laundry categories defined: {laundry_categories}")

        # Fetch laundry contracts from id_item_master (contract numbers starting with 'L' or 'l')
        current_app.logger.info("Executing contracts query")
        contracts_query = session.query(
            ItemMaster.last_contract_num,
            func.count(ItemMaster.tag_id).label('total_items')
        ).filter(
            ItemMaster.status.in_(['On Rent', 'Delivered']),
            ItemMaster.last_contract_num != None,
            ItemMaster.last_contract_num != '00000',
            func.lower(ItemMaster.last_contract_num).like('[lL]%')
        ).group_by(
            ItemMaster.last_contract_num
        ).having(
            func.count(ItemMaster.tag_id) > 0
        ).all()

        current_app.logger.info(f"Raw laundry contracts query result: {[(c.last_contract_num, c.total_items) for c in contracts_query]}")

        contracts = []
        for contract_number, total_items in contracts_query:
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
            current_app.logger.debug(f"Contract {contract_number}: client_name={client_name}, scan_date={scan_date}")

            # Fetch rental class IDs for items in this contract
            rental_class_nums = session.query(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String)))
            ).filter(
                ItemMaster.last_contract_num == contract_number,
                ItemMaster.status.in_(['On Rent', 'Delivered'])
            ).distinct().all()
            rental_class_nums = [r[0] for r in rental_class_nums if r[0]]

            current_app.logger.debug(f"Laundry contract {contract_number}: rental_class_nums = {rental_class_nums}")

            # Map rental class IDs to categories, filtering for laundry categories
            base_mappings = session.query(RentalClassMapping).filter(
                RentalClassMapping.rental_class_id.in_(rental_class_nums),
                RentalClassMapping.category.in_(laundry_categories)
            ).all()
            user_mappings = session.query(UserRentalClassMapping).filter(
                UserRentalClassMapping.rental_class_id.in_(rental_class_nums),
                UserRentalClassMapping.category.in_(laundry_categories)
            ).all()

            mappings_dict = {m.rental_class_id: {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
            for um in user_mappings:
                mappings_dict[um.rental_class_id] = {'category': um.category, 'subcategory': um.subcategory}

            current_app.logger.debug(f"Laundry contract {contract_number}: mappings_dict = {mappings_dict}")

            categories = {}
            for rental_class_id in rental_class_nums:
                if rental_class_id in mappings_dict:
                    category = mappings_dict[rental_class_id]['category']
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(rental_class_id)

            current_app.logger.debug(f"Laundry contract {contract_number}: categories = {categories}")

            contract_categories = []
            for cat, rental_ids in categories.items():
                # Count items on this contract (already filtered by status)
                items_on_contract = session.query(func.count(ItemMaster.tag_id)).filter(
                    ItemMaster.last_contract_num == contract_number,
                    func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_ids),
                    ItemMaster.status.in_(['On Rent', 'Delivered'])
                ).scalar()

                # Total items in inventory for this category
                total_items_inventory = session.query(func.count(ItemMaster.tag_id)).filter(
                    func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_ids)
                ).scalar()

                contract_categories.append({
                    'category': cat,
                    'cat_id': contract_number + '_' + cat.lower().replace(' ', '_').replace('/', '_'),
                    'items_on_contract': items_on_contract or 0,
                    'total_items_inventory': total_items_inventory or 0
                })
                current_app.logger.debug(f"Laundry contract {contract_number}: category {cat} - items_on_contract={items_on_contract}, total_items_inventory={total_items_inventory}")

            contract_categories.sort(key=lambda x: x['category'])
            contracts.append({
                'contract_number': contract_number,
                'client_name': client_name,
                'scan_date': scan_date,
                'categories': contract_categories
            })

        contracts.sort(key=lambda x: x['contract_number'])
        current_app.logger.info(f"Fetched {len(contracts)} laundry contracts for tab4: {[c['contract_number'] for c in contracts]}")
        session.close()
        current_app.logger.info(f"Rendering tab4.html with contracts: {[c['contract_number'] for c in contracts]}")
        return render_template('tab4.html', contracts=contracts, cache_bust=int(time()))
    except Exception as e:
        current_app.logger.error(f"Error rendering Tab 4: {str(e)}", exc_info=True)
        if 'session' in locals():
            session.close()
        return render_template('tab4.html', contracts=[], cache_bust=int(time()))

@tab4_bp.route('/tab/4/common_names')
def tab4_common_names():
    category = request.args.get('category')
    contract_number = request.args.get('contract_number')
    page = int(request.args.get('page', 1))
    per_page = 10

    current_app.logger.info(f"Fetching common names for category={category}, contract_number={contract_number}, page={page}")

    if not category or not contract_number:
        current_app.logger.error("Missing required parameters: category and contract_number are required")
        return jsonify({'error': 'Category and contract number are required'}), 400

    try:
        session = db.session()

        # Fetch rental class IDs for this category
        base_mappings = session.query(RentalClassMapping).filter_by(category=category).all()
        user_mappings = session.query(UserRentalClassMapping).filter_by(category=category).all()

        mappings_dict = {m.rental_class_id: {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[um.rental_class_id] = {'category': um.category, 'subcategory': um.subcategory}

        rental_class_ids = list(mappings_dict.keys())
        current_app.logger.debug(f"Common names for contract {contract_number}, category {category}: rental_class_ids = {rental_class_ids}")

        # Fetch common names for items on this contract
        common_names_query = session.query(
            ItemMaster.common_name,
            func.count(ItemMaster.tag_id).label('on_contracts')
        ).filter(
            ItemMaster.last_contract_num == contract_number,
            func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
            ItemMaster.status.in_(['On Rent', 'Delivered'])
        ).group_by(
            ItemMaster.common_name
        ).all()

        current_app.logger.debug(f"Common names for laundry contract {contract_number}, category {category}: {[(name, count) for name, count in common_names_query]}")

        common_names = []
        for name, on_contracts in common_names_query:
            if not name:
                continue

            # Total items in inventory for this common name
            total_items_inventory = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
                ItemMaster.common_name == name
            ).scalar()

            common_names.append({
                'name': name,
                'on_contracts': on_contracts or 0,
                'total_items_inventory': total_items_inventory or 0
            })

        # Paginate common names
        total_common_names = len(common_names)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_common_names = common_names[start:end]

        session.close()
        current_app.logger.info(f"Returning {len(paginated_common_names)} common names for contract {contract_number}, category {category}")
        return jsonify({
            'common_names': paginated_common_names,
            'total_common_names': total_common_names,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching common names for contract {contract_number}, category {category}: {str(e)}")
        session.close()
        return jsonify({'error': 'Failed to fetch common names'}), 500

@tab4_bp.route('/tab/4/data')
def tab4_data():
    category = request.args.get('category')
    contract_number = request.args.get('contract_number')
    common_name = request.args.get('common_name')
    page = int(request.args.get('page', 1))
    per_page = 10

    current_app.logger.info(f"Fetching items for category={category}, contract_number={contract_number}, common_name={common_name}, page={page}")

    if not category or not contract_number or not common_name:
        current_app.logger.error("Missing required parameters: category, contract number, and common name are required")
        return jsonify({'error': 'Category, contract number, and common name are required'}), 400

    try:
        session = db.session()

        # Fetch rental class IDs for this category
        base_mappings = session.query(RentalClassMapping).filter_by(category=category).all()
        user_mappings = session.query(UserRentalClassMapping).filter_by(category=category).all()

        mappings_dict = {m.rental_class_id: {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[um.rental_class_id] = {'category': um.category, 'subcategory': um.subcategory}

        rental_class_ids = list(mappings_dict.keys())
        current_app.logger.debug(f"Items for contract {contract_number}, category {category}: rental_class_ids = {rental_class_ids}")

        # Fetch items on this contract
        query = session.query(ItemMaster).filter(
            ItemMaster.last_contract_num == contract_number,
            func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
            ItemMaster.common_name == common_name,
            ItemMaster.status.in_(['On Rent', 'Delivered'])
        )

        # Paginate items
        total_items = query.count()
        items = query.order_by(ItemMaster.tag_id).offset((page - 1) * per_page).limit(per_page).all()

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

        current_app.logger.debug(f"Items for laundry contract {contract_number}, category {category}, common_name {common_name}: {len(items_data)} items")

        session.close()
        return jsonify({
            'items': items_data,
            'total_items': total_items,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching items for contract {contract_number}, category {category}, common_name {common_name}: {str(e)}")
        session.close()
        return jsonify({'error': 'Failed to fetch items'}), 500

@tab4_bp.route('/tab/4/hand_counted_items')
def tab4_hand_counted_items():
    contract_number = request.args.get('contract_number')
    current_app.logger.info(f"Fetching hand-counted items for contract_number={contract_number}")
    try:
        session = db.session()
        items = session.query(HandCountedItems).filter(
            HandCountedItems.contract_number == contract_number
        ).all()
        session.close()
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
        current_app.logger.error(f"Error fetching hand-counted items for contract {contract_number}: {str(e)}")
        session.close()
        return '<tr><td colspan="6">Error loading hand-counted items.</td></tr>'