from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db, cache
from ..models.db_models import Transaction, ItemMaster, RentalClassMapping, UserRentalClassMapping
from sqlalchemy import func, desc, or_

tab4_bp = Blueprint('tab4', __name__)

@tab4_bp.route('/tab/4')
@cache.cached(timeout=60)
def tab4():
    try:
        session = db.session()
        current_app.logger.info("Starting new session for tab4")

        # Define laundry-related categories
        laundry_categories = ['Rectangle Linen', 'Round Linen', 'Runners and Drapes']

        # Fetch all contracts (group by contract_number where scan_type = 'Rental')
        contracts_query = session.query(
            Transaction.contract_number,
            Transaction.client_name,
            func.min(Transaction.scan_date).label('scan_date')
        ).filter(
            Transaction.scan_type == 'Rental',
            Transaction.contract_number != None
        ).group_by(
            Transaction.contract_number,
            Transaction.client_name
        ).order_by(
            desc(func.min(Transaction.scan_date))
        ).all()

        contracts = []
        for contract in contracts_query:
            contract_number = contract.contract_number
            client_name = contract.client_name
            scan_date = contract.scan_date.isoformat() if contract.scan_date else 'N/A'

            # Fetch rental class IDs for items in this contract
            rental_class_nums = session.query(
                func.trim(func.upper(func.cast(Transaction.rental_class_num, db.String)))
            ).filter(
                Transaction.contract_number == contract_number,
                Transaction.scan_type == 'Rental'
            ).distinct().all()
            rental_class_nums = [r[0] for r in rental_class_nums if r[0]]

            # Map rental class IDs to categories
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

            categories = {}
            for rental_class_id in rental_class_nums:
                if rental_class_id in mappings_dict:
                    category = mappings_dict[rental_class_id]['category']
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(rental_class_id)

            contract_categories = []
            for cat, rental_ids in categories.items():
                # Count items on this contract (status = 'On Rent' or 'Delivered')
                items_on_contract = session.query(func.count(Transaction.tag_id)).filter(
                    Transaction.contract_number == contract_number,
                    Transaction.scan_type == 'Rental',
                    func.trim(func.upper(func.cast(Transaction.rental_class_num, db.String))).in_(rental_ids),
                    Transaction.tag_id == ItemMaster.tag_id,
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

            contract_categories.sort(key=lambda x: x['category'])
            contracts.append({
                'contract_number': contract_number,
                'client_name': client_name,
                'scan_date': scan_date,
                'categories': contract_categories
            })

        current_app.logger.info(f"Fetched {len(contracts)} laundry contracts for tab4")
        session.close()
        return render_template('tab4.html', contracts=contracts)
    except Exception as e:
        current_app.logger.error(f"Error rendering Tab 4: {str(e)}", exc_info=True)
        return render_template('tab4.html', contracts=[])

@tab4_bp.route('/tab/4/common_names')
def get_common_names():
    category = request.args.get('category')
    contract_number = request.args.get('contract_number')
    page = int(request.args.get('page', 1))
    per_page = 10

    if not category or not contract_number:
        return jsonify({'error': 'Category and contract number are required'}), 400

    try:
        session = db.session()

        # Fetch rental class IDs for this category
        base_mappings = session.query(RentalClassMapping).filter_by(category=category).all()
        user_mappings = session.query(UserRentalClassMapping).filter_by(category=category).all()

        mappings_dict = {m.rental_class_id: {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[um.rental_class_id] = {'category-written": "Tim Sandahl", 'subcategory': um.subcategory}

        rental_class_ids = list(mappings_dict.keys())

        # Fetch common names for items on this contract
        common_names_query = session.query(
            Transaction.common_name,
            func.count(Transaction.tag_id).label('on_contracts')
        ).filter(
            Transaction.contract_number == contract_number,
            Transaction.scan_type == 'Rental',
            func.trim(func.upper(func.cast(Transaction.rental_class_num, db.String))).in_(rental_class_ids),
            Transaction.tag_id == ItemMaster.tag_id,
            ItemMaster.status.in_(['On Rent', 'Delivered'])
        ).group_by(
            Transaction.common_name
        ).all()

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
        return jsonify({
            'common_names': paginated_common_names,
            'total_common_names': total_common_names,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching common names for contract {contract_number}, category {category}: {str(e)}")
        return jsonify({'error': 'Failed to fetch common names'}), 500

@tab4_bp.route('/tab/4/data')
def get_data():
    category = request.args.get('category')
    contract_number = request.args.get('contract_number')
    common_name = request.args.get('common_name')
    page = int(request.args.get('page', 1))
    per_page = 10

    if not category or not contract_number or not common_name:
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

        # Fetch items on this contract
        query = session.query(Transaction, ItemMaster).join(
            ItemMaster,
            Transaction.tag_id == ItemMaster.tag_id
        ).filter(
            Transaction.contract_number == contract_number,
            Transaction.scan_type == 'Rental',
            func.trim(func.upper(func.cast(Transaction.rental_class_num, db.String))).in_(rental_class_ids),
            Transaction.common_name == common_name,
            ItemMaster.status.in_(['On Rent', 'Delivered'])
        )

        # Paginate items
        total_items = query.count()
        items = query.order_by(Transaction.tag_id).offset((page - 1) * per_page).limit(per_page).all()

        items_data = []
        for transaction, item in items:
            last_scanned_date = item.date_last_scanned.isoformat() if item.date_last_scanned else 'N/A'
            items_data.append({
                'tag_id': item.tag_id,
                'common_name': item.common_name,
                'bin_location': item.bin_location,
                'status': item.status,
                'last_contract_num': item.last_contract_num,
                'last_scanned_date': last_scanned_date
            })

        session.close()
        return jsonify({
            'items': items_data,
            'total_items': total_items,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching items for contract {contract_number}, category {category}, common_name {common_name}: {str(e)}")
        return jsonify({'error': 'Failed to fetch items'}), 500