from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db
from ..models.db_models import ItemMaster, Transaction, RentalClassMapping, UserRentalClassMapping
from sqlalchemy import func, desc, or_, asc, text
from time import time
import logging
import sys

# Configure logging
logger = logging.getLogger('tab1')
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

tab1_bp = Blueprint('tab1', __name__)

# Version marker
logger.info("Deployed tab1.py version: 2025-04-25-v5")

@tab1_bp.route('/tab/1')
def tab1_view():
    try:
        session = db.session()
        logger.info("Starting new session for tab1")

        # Log raw contents of mapping tables
        raw_base_mappings = session.execute(text("SELECT rental_class_id, category, subcategory FROM rental_class_mappings")).fetchall()
        raw_user_mappings = session.execute(text("SELECT rental_class_id, category, subcategory FROM user_rental_class_mappings")).fetchall()
        logger.debug(f"Raw base mappings: {[(row[0], row[1], row[2]) for row in raw_base_mappings]}")
        logger.debug(f"Raw user mappings: {[(row[0], row[1], row[2]) for row in raw_user_mappings]}")

        # Fetch all rental class mappings from both tables
        base_mappings = session.query(RentalClassMapping).all()
        user_mappings = session.query(UserRentalClassMapping).all()
        logger.debug(f"Fetched {len(base_mappings)} base mappings")
        logger.debug(f"Fetched {len(user_mappings)} user mappings")

        # Merge mappings, prioritizing user mappings
        mappings_dict = {m.rental_class_id: {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[um.rental_class_id] = {'category': um.category, 'subcategory': um.subcategory}
        logger.debug(f"Merged mappings_dict has {len(mappings_dict)} entries")

        # Group by category
        categories = {}
        for rental_class_id, data in mappings_dict.items():
            category = data['category']
            if category not in categories:
                categories[category] = []
            categories[category].append({
                'rental_class_id': rental_class_id,
                'category': category,
                'subcategory': data['subcategory']
            })
        logger.debug(f"Grouped into {len(categories)} categories: {list(categories.keys())}")

        # Log rental_class_num values from id_item_master
        item_master_data = session.execute(text("SELECT tag_id, rental_class_num, status FROM id_item_master")).fetchall()
        logger.debug(f"Raw id_item_master data: {[(row[0], row[1], row[2]) for row in item_master_data]}")

        # Calculate counts for each category
        category_data = []
        filter_query = request.args.get('filter', '').lower()
        sort = request.args.get('sort', '')

        for cat, mappings in categories.items():
            rental_class_ids = [m['rental_class_id'] for m in mappings]
            logger.debug(f"Processing category {cat} with rental_class_ids: {rental_class_ids[:5]}...")

            # Total items in this category
            total_items_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids)
            )
            if filter_query:
                total_items_query = total_items_query.filter(
                    func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
                )
            total_items = total_items_query.scalar()
            logger.debug(f"Total items for category {cat}: {total_items}")

            # Items on contracts (status = 'On Rent' or 'Delivered')
            items_on_contracts_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
                ItemMaster.status.in_(['On Rent', 'Delivered'])
            )
            if filter_query:
                items_on_contracts_query = items_on_contracts_query.filter(
                    func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
                )
            items_on_contracts = items_on_contracts_query.scalar()
            logger.debug(f"Items on contracts for category {cat}: {items_on_contracts}")

            # Items in service logic
            subquery = session.query(
                Transaction.tag_id,
                Transaction.scan_date,
                Transaction.service_required
            ).filter(
                Transaction.tag_id == ItemMaster.tag_id
            ).order_by(
                Transaction.scan_date.desc()
            ).subquery()

            items_in_service_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
                or_(
                    ItemMaster.status.notin_(['Ready to Rent', 'On Rent', 'Delivered']),
                    ItemMaster.tag_id.in_(
                        session.query(subquery.c.tag_id).filter(
                            subquery.c.scan_date == session.query(func.max(Transaction.scan_date)).filter(Transaction.tag_id == subquery.c.tag_id).correlate(subquery).scalar_subquery(),
                            subquery.c.service_required == True
                        )
                    )
                )
            )
            if filter_query:
                items_in_service_query = items_in_service_query.filter(
                    func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
                )
            items_in_service = items_in_service_query.scalar()
            logger.debug(f"Items in service for category {cat}: {items_in_service}")

            # Items available (status = 'Ready to Rent')
            items_available_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
                ItemMaster.status == 'Ready to Rent'
            )
            if filter_query:
                items_available_query = items_available_query.filter(
                    func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
                )
            items_available = items_available_query.scalar()
            logger.debug(f"Items available for category {cat}: {items_available}")

            category_data.append({
                'category': cat,
                'cat_id': cat.lower().replace(' ', '_').replace('/', '_'),
                'total_items': total_items or 0,
                'items_on_contracts': items_on_contracts or 0,
                'items_in_service': items_in_service or 0,
                'items_available': items_available or 0
            })

        # Sort category data
        if sort == 'category_asc':
            category_data.sort(key=lambda x: x['category'].lower())
        elif sort == 'category_desc':
            category_data.sort(key=lambda x: x['category'].lower(), reverse=True)
        elif sort == 'total_items_asc':
            category_data.sort(key=lambda x: x['total_items'])
        elif sort == 'total_items_desc':
            category_data.sort(key=lambda x: x['total_items'], reverse=True)

        logger.info(f"Fetched {len(category_data)} categories for tab1")

        session.close()
        return render_template('tab1.html', categories=category_data, cache_bust=int(time()))
    except Exception as e:
        logger.error(f"Error rendering Tab 1: {str(e)}", exc_info=True)
        return render_template('tab1.html', categories=[], cache_bust=int(time()))

@tab1_bp.route('/tab/1/subcat_data')
def tab1_subcat_data():
    category = request.args.get('category')
    page = int(request.args.get('page', 1))
    per_page = 10
    filter_query = request.args.get('filter', '').lower()
    sort = request.args.get('sort', '')

    if not category:
        logger.error("Category parameter is missing in subcat_data request")
        return jsonify({'error': 'Category is required'}), 400

    logger.info(f"Fetching subcategories for category: {category}")
    try:
        session = db.session()

        # Log raw contents of mapping tables for this category
        raw_base_mappings = session.execute(
            text("SELECT rental_class_id, category, subcategory FROM rental_class_mappings WHERE LOWER(category) = :category"),
            {"category": category.lower()}
        ).fetchall()
        raw_user_mappings = session.execute(
            text("SELECT rental_class_id, category, subcategory FROM user_rental_class_mappings WHERE LOWER(category) = :category"),
            {"category": category.lower()}
        ).fetchall()
        logger.debug(f"Raw base mappings for category {category}: {[(row[0], row[1], row[2]) for row in raw_base_mappings]}")
        logger.debug(f"Raw user mappings for category {category}: {[(row[0], row[1], row[2]) for row in raw_user_mappings]}")

        # Fetch mappings for this category (case-insensitive)
        base_mappings = session.query(RentalClassMapping).filter(
            func.lower(RentalClassMapping.category) == category.lower()
        ).all()
        user_mappings = session.query(UserRentalClassMapping).filter(
            func.lower(UserRentalClassMapping.category) == category.lower()
        ).all()
        logger.debug(f"Fetched {len(base_mappings)} base mappings for category {category}")
        logger.debug(f"Fetched {len(user_mappings)} user mappings for category {category}")

        mappings_dict = {m.rental_class_id: {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[um.rental_class_id] = {'category': um.category, 'subcategory': um.subcategory}
        logger.debug(f"Merged mappings_dict has {len(mappings_dict)} entries: {list(mappings_dict.items())[:5]}")

        # Group by subcategory
        subcategories = {}
        for rental_class_id, data in mappings_dict.items():
            subcategory = data['subcategory']
            if subcategory not in subcategories:
                subcategories[subcategory] = []
            subcategories[subcategory].append(rental_class_id)
        logger.debug(f"Found {len(subcategories)} subcategories: {list(subcategories.keys())}")

        # Apply filter and sort
        subcat_list = sorted(subcategories.keys())
        if filter_query:
            subcat_list = [s for s in subcat_list if filter_query in s.lower()]
        if sort == 'subcategory_asc':
            subcat_list.sort()
        elif sort == 'subcategory_desc':
            subcat_list.sort(reverse=True)

        # Paginate subcategories
        total_subcats = len(subcat_list)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_subcats = subcat_list[start:end]
        logger.debug(f"Paginated subcategories (page {page}): {paginated_subcats}")

        subcategory_data = []
        for subcat in paginated_subcats:
            rental_class_ids = subcategories[subcat]
            logger.debug(f"Processing subcategory {subcat} with rental_class_ids: {rental_class_ids}")

            # Total items in this subcategory
            total_items_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids)
            )
            if filter_query:
                total_items_query = total_items_query.filter(
                    func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
                )
            total_items = total_items_query.scalar()
            logger.debug(f"Total items for subcategory {subcat}: {total_items}")

            # Items on contracts (status = 'On Rent' or 'Delivered')
            items_on_contracts_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
                ItemMaster.status.in_(['On Rent', 'Delivered'])
            )
            if filter_query:
                items_on_contracts_query = items_on_contracts_query.filter(
                    func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
                )
            items_on_contracts = items_on_contracts_query.scalar()
            logger.debug(f"Items on contracts for subcategory {subcat}: {items_on_contracts}")

            # Items in service
            subquery = session.query(
                Transaction.tag_id,
                Transaction.scan_date,
                Transaction.service_required
            ).filter(
                Transaction.tag_id == ItemMaster.tag_id
            ).order_by(
                Transaction.scan_date.desc()
            ).subquery()

            items_in_service_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
                or_(
                    ItemMaster.status.notin_(['Ready to Rent', 'On Rent', 'Delivered']),
                    ItemMaster.tag_id.in_(
                        session.query(subquery.c.tag_id).filter(
                            subquery.c.scan_date == session.query(func.max(Transaction.scan_date)).filter(Transaction.tag_id == subquery.c.tag_id).correlate(subquery).scalar_subquery(),
                            subquery.c.service_required == True
                        )
                    )
                )
            )
            if filter_query:
                items_in_service_query = items_in_service_query.filter(
                    func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
                )
            items_in_service = items_in_service_query.scalar()
            logger.debug(f"Items in service for subcategory {subcat}: {items_in_service}")

            # Items available (status = 'Ready to Rent')
            items_available_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
                ItemMaster.status == 'Ready to Rent'
            )
            if filter_query:
                items_available_query = items_available_query.filter(
                    func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
                )
            items_available = items_available_query.scalar()
            logger.debug(f"Items available for subcategory {subcat}: {items_available}")

            subcategory_data.append({
                'subcategory': subcat,
                'total_items': total_items or 0,
                'items_on_contracts': items_on_contracts or 0,
                'items_in_service': items_in_service or 0,
                'items_available': items_available or 0
            })

            # Sort subcategory data if needed
            if sort == 'total_items_asc':
                subcategory_data.sort(key=lambda x: x['total_items'])
            elif sort == 'total_items_desc':
                subcategory_data.sort(key=lambda x: x['total_items'], reverse=True)

        session.close()
        logger.info(f"Returning {len(subcategory_data)} subcategories for category {category}")
        return jsonify({
            'subcategories': subcategory_data,
            'total_subcats': total_subcats,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        logger.error(f"Error fetching subcategory data for category {category}: {str(e)}")
        return jsonify({'error': 'Failed to fetch subcategory data'}), 500

@tab1_bp.route('/tab/1/common_names')
def tab1_common_names():
    category = request.args.get('category')
    subcategory = request.args.get('subcategory')
    page = int(request.args.get('page', 1))
    per_page = 10
    filter_query = request.args.get('filter', '').lower()
    sort = request.args.get('sort', '')

    if not category or not subcategory:
        return jsonify({'error': 'Category and subcategory are required'}), 400

    try:
        session = db.session()

        # Fetch rental class IDs for this category and subcategory
        base_mappings = session.query(RentalClassMapping).filter(
            func.lower(RentalClassMapping.category) == category.lower(),
            func.lower(RentalClassMapping.subcategory) == subcategory.lower()
        ).all()
        user_mappings = session.query(UserRentalClassMapping).filter(
            func.lower(UserRentalClassMapping.category) == category.lower(),
            func.lower(UserRentalClassMapping.subcategory) == subcategory.lower()
        ).all()

        mappings_dict = {m.rental_class_id: {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[um.rental_class_id] = {'category': um.category, 'subcategory': um.subcategory}

        rental_class_ids = list(mappings_dict.keys())

        # Group items by common name
        common_names_query = session.query(
            ItemMaster.common_name,
            func.count(ItemMaster.tag_id).label('total_items')
        ).filter(
            func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids)
        )
        if filter_query:
            common_names_query = common_names_query.filter(
                func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
            )
        common_names_query = common_names_query.group_by(ItemMaster.common_name)

        # Apply sorting
        if sort == 'name_asc':
            common_names_query = common_names_query.order_by(asc(func.lower(ItemMaster.common_name)))
        elif sort == 'name_desc':
            common_names_query = common_names_query.order_by(desc(func.lower(ItemMaster.common_name)))
        elif sort == 'total_items_asc':
            common_names_query = common_names_query.order_by(asc('total_items'))
        elif sort == 'total_items_desc':
            common_names_query = common_names_query.order_by(desc('total_items'))

        # Fetch all common names to calculate total before pagination
        common_names_all = common_names_query.all()
        common_names = []
        for name, total in common_names_all:
            if not name:  # Skip items with no common name
                continue

            # Items on contracts (status = 'On Rent' or 'Delivered')
            items_on_contracts_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
                ItemMaster.common_name == name,
                ItemMaster.status.in_(['On Rent', 'Delivered'])
            )
            if filter_query:
                items_on_contracts_query = items_on_contracts_query.filter(
                    func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
                )
            items_on_contracts = items_on_contracts_query.scalar()

            # Items in service
            subquery = session.query(
                Transaction.tag_id,
                Transaction.scan_date,
                Transaction.service_required
            ).filter(
                Transaction.tag_id == ItemMaster.tag_id
            ).order_by(
                Transaction.scan_date.desc()
            ).subquery()

            items_in_service_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
                ItemMaster.common_name == name,
                or_(
                    ItemMaster.status.notin_(['Ready to Rent', 'On Rent', 'Delivered']),
                    ItemMaster.tag_id.in_(
                        session.query(subquery.c.tag_id).filter(
                            subquery.c.scan_date == session.query(func.max(Transaction.scan_date)).filter(Transaction.tag_id == subquery.c.tag_id).correlate(subquery).scalar_subquery(),
                            subquery.c.service_required == True
                        )
                    )
                )
            )
            if filter_query:
                items_in_service_query = items_in_service_query.filter(
                    func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
                )
            items_in_service = items_in_service_query.scalar()

            # Items available (status = 'Ready to Rent')
            items_available_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
                ItemMaster.common_name == name,
                ItemMaster.status == 'Ready to Rent'
            )
            if filter_query:
                items_available_query = items_available_query.filter(
                    func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
                )
            items_available = items_available_query.scalar()

            common_names.append({
                'name': name,
                'total_items': total or 0,
                'items_on_contracts': items_on_contracts or 0,
                'items_in_service': items_in_service or 0,
                'items_available': items_available or 0
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
        current_app.logger.error(f"Error fetching common names for category {category}, subcategory {subcategory}: {str(e)}")
        return jsonify({'error': 'Failed to fetch common names'}), 500

@tab1_bp.route('/tab/1/data')
def tab1_data():
    category = request.args.get('category')
    subcategory = request.args.get('subcategory')
    common_name = request.args.get('common_name')
    page = int(request.args.get('page', 1))
    per_page = 10
    filter_query = request.args.get('filter', '').lower()
    sort = request.args.get('sort', '')

    if not category or not subcategory or not common_name:
        return jsonify({'error': 'Category, subcategory, and common name are required'}), 400

    try:
        session = db.session()

        # Fetch rental class IDs for this category and subcategory
        base_mappings = session.query(RentalClassMapping).filter(
            func.lower(RentalClassMapping.category) == category.lower(),
            func.lower(RentalClassMapping.subcategory) == subcategory.lower()
        ).all()
        user_mappings = session.query(UserRentalClassMapping).filter(
            func.lower(UserRentalClassMapping.category) == category.lower(),
            func.lower(UserRentalClassMapping.subcategory) == subcategory.lower()
        ).all()

        mappings_dict = {m.rental_class_id: {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[um.rental_class_id] = {'category': um.category, 'subcategory': um.subcategory}

        rental_class_ids = list(mappings_dict.keys())

        # Fetch items
        query = session.query(ItemMaster).filter(
            func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
            ItemMaster.common_name == common_name
        )
        if filter_query:
            query = query.filter(
                or_(
                    func.lower(ItemMaster.tag_id).like(f'%{filter_query}%'),
                    func.lower(ItemMaster.bin_location).like(f'%{filter_query}%'),
                    func.lower(ItemMaster.status).like(f'%{filter_query}%'),
                    func.lower(ItemMaster.last_contract_num).like(f'%{filter_query}%')
                )
            )

        # Apply sorting
        if sort == 'tag_id_asc':
            query = query.order_by(asc(ItemMaster.tag_id))
        elif sort == 'tag_id_desc':
            query = query.order_by(desc(ItemMaster.tag_id))
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
                'last_scanned_date': last_scanned_date,
                'quality': item.quality,
                'notes': item.notes
            })

        session.close()
        return jsonify({
            'items': items_data,
            'total_items': total_items,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching items for category {category}, subcategory {subcategory}, common_name {common_name}: {str(e)}")
        return jsonify({'error': 'Failed to fetch items'}), 500

@tab1_bp.route('/tab/1/full_items_by_rental_class')
def full_items_by_rental_class():
    category = request.args.get('category')
    subcategory = request.args.get('subcategory')
    common_name = request.args.get('common_name')

    if not category or not subcategory or not common_name:
        return jsonify({'error': 'Category, subcategory, and common name are required'}), 400

    try:
        session = db.session()

        # Fetch rental class IDs for this category and subcategory
        base_mappings = session.query(RentalClassMapping).filter(
            func.lower(RentalClassMapping.category) == category.lower(),
            func.lower(RentalClassMapping.subcategory) == subcategory.lower()
        ).all()
        user_mappings = session.query(UserRentalClassMapping).filter(
            func.lower(UserRentalClassMapping.category) == category.lower(),
            func.lower(UserRentalClassMapping.subcategory) == subcategory.lower()
        ).all()

        mappings_dict = {m.rental_class_id: {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[um.rental_class_id] = {'category': um.category, 'subcategory': um.subcategory}

        rental_class_ids = list(mappings_dict.keys())

        # Fetch all items with the same rental_class_num and common_name
        items_query = session.query(ItemMaster).filter(
            func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
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

        session.close()
        return jsonify({
            'items': items_data,
            'total_items': len(items_data)
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching full items for category {category}, subcategory {subcategory}, common_name {common_name}: {str(e)}")
        return jsonify({'error': 'Failed to fetch full items'}), 500