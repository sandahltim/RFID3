from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db
from ..models.db_models import ItemMaster, Transaction, RentalClassMapping, UserRentalClassMapping
from sqlalchemy import func, desc, or_, asc
from time import time
import logging
import sys
from urllib.parse import unquote

# Configure logging
logger = logging.getLogger('tab1')
logger.setLevel(logging.DEBUG)  # DEBUG for detailed tracing

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
logger.info("Deployed tab1.py version: 2025-05-23-v20")

def get_category_data(session, filter_query='', sort='', status_filter='', bin_filter=''):
    logger.debug(f"get_category_data: filter_query={filter_query}, sort={sort}, status_filter={status_filter}, bin_filter={bin_filter}")
    base_mappings = session.query(RentalClassMapping).all()
    user_mappings = session.query(UserRentalClassMapping).all()
    logger.info(f"Fetched {len(base_mappings)} base mappings and {len(user_mappings)} user mappings")

    mappings_dict = {m.rental_class_id: {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
    for um in user_mappings:
        mappings_dict[um.rental_class_id] = {'category': um.category, 'subcategory': um.subcategory}

    if not mappings_dict:
        logger.warning("No rental class mappings found")
        return []

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

    category_data = []
    for cat, mappings in categories.items():
        if filter_query and filter_query not in cat.lower():
            continue
        rental_class_ids = [str(m['rental_class_id']) for m in mappings]
        logger.debug(f"Processing category {cat} with rental_class_ids: {rental_class_ids}")

        total_items_query = session.query(func.count(ItemMaster.tag_id)).filter(
            func.trim(func.cast(ItemMaster.rental_class_num, db.String)).in_(rental_class_ids)
        )
        if status_filter:
            total_items_query = total_items_query.filter(func.lower(ItemMaster.status) == status_filter.lower())
        if bin_filter:
            total_items_query = total_items_query.filter(
                func.lower(func.trim(func.coalesce(ItemMaster.bin_location, ''))) == bin_filter.lower()
            )
        total_items = total_items_query.scalar() or 0
        logger.debug(f"Category {cat}: total_items={total_items}")

        items_on_contracts_query = session.query(func.count(ItemMaster.tag_id)).filter(
            func.trim(func.cast(ItemMaster.rental_class_num, db.String)).in_(rental_class_ids),
            ItemMaster.status.in_(['On Rent', 'Delivered'])
        )
        if status_filter:
            items_on_contracts_query = items_on_contracts_query.filter(func.lower(ItemMaster.status) == status_filter.lower())
        if bin_filter:
            items_on_contracts_query = items_on_contracts_query.filter(
                func.lower(func.trim(func.coalesce(ItemMaster.bin_location, ''))) == bin_filter.lower()
            )
        items_on_contracts = items_on_contracts_query.scalar() or 0
        logger.debug(f"Category {cat}: items_on_contracts={items_on_contracts}")

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
            func.trim(func.cast(ItemMaster.rental_class_num, db.String)).in_(rental_class_ids),
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
        if status_filter:
            items_in_service_query = items_in_service_query.filter(func.lower(ItemMaster.status) == status_filter.lower())
        if bin_filter:
            items_in_service_query = items_in_service_query.filter(
                func.lower(func.trim(func.coalesce(ItemMaster.bin_location, ''))) == bin_filter.lower()
            )
        items_in_service = items_in_service_query.scalar() or 0
        logger.debug(f"Category {cat}: items_in_service={items_in_service}")

        items_available_query = session.query(func.count(ItemMaster.tag_id)).filter(
            func.trim(func.cast(ItemMaster.rental_class_num, db.String)).in_(rental_class_ids),
            ItemMaster.status == 'Ready to Rent'
        )
        if status_filter:
            items_available_query = items_available_query.filter(func.lower(ItemMaster.status) == status_filter.lower())
        if bin_filter:
            items_available_query = items_available_query.filter(
                func.lower(func.trim(func.coalesce(ItemMaster.bin_location, ''))) == bin_filter.lower()
            )
        items_available = items_available_query.scalar() or 0
        logger.debug(f"Category {cat}: items_available={items_available}")

        category_data.append({
            'category': cat,
            'cat_id': cat.lower().replace(' ', '_').replace('/', '_'),
            'total_items': total_items,
            'items_on_contracts': items_on_contracts,
            'items_in_service': items_in_service,
            'items_available': items_available
        })

    if not sort:
        sort = 'category_asc'

    if sort == 'category_asc':
        category_data.sort(key=lambda x: x['category'].lower())
    elif sort == 'category_desc':
        category_data.sort(key=lambda x: x['category'].lower(), reverse=True)
    elif sort == 'total_items_asc':
        category_data.sort(key=lambda x: x['total_items'])
    elif sort == 'total_items_desc':
        category_data.sort(key=lambda x: x['total_items'], reverse=True)

    logger.debug(f"Returning {len(category_data)} categories")
    return category_data

@tab1_bp.route('/tab/1')
def tab1_view():
    logger.debug("Tab 1 route accessed")
    current_app.logger.debug("Tab 1 route accessed")
    try:
        session = db.session()
        filter_query = request.args.get('filter', '').lower()
        sort = request.args.get('sort', '')
        status_filter = request.args.get('statusFilter', '').lower()
        bin_filter = request.args.get('binFilter', '').lower()
        logger.debug(f"Tab 1 parameters: filter_query={filter_query}, sort={sort}, status_filter={status_filter}, bin_filter={bin_filter}")

        category_data = get_category_data(session, filter_query, sort, status_filter, bin_filter)
        logger.info(f"Fetched {len(category_data)} categories for tab1")

        session.close()
        return render_template('common.html', categories=category_data, tab_num=1, cache_bust=int(time()))
    except Exception as e:
        logger.error(f"Error rendering Tab 1: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error rendering Tab 1: {str(e)}", exc_info=True)
        return render_template('common.html', categories=[], tab_num=1, cache_bust=int(time()))

@tab1_bp.route('/tab/1/filter', methods=['POST'])
def tab1_filter():
    logger.debug("Tab 1 filter route accessed")
    try:
        session = db.session()
        filter_query = request.form.get('category-filter', '').lower()
        sort = request.form.get('category-sort', '')
        status_filter = request.form.get('statusFilter', '').lower()
        bin_filter = request.form.get('binFilter', '').lower()
        logger.debug(f"Filter parameters: filter_query={filter_query}, sort={sort}, status_filter={status_filter}, bin_filter={bin_filter}")

        category_data = get_category_data(session, filter_query, sort, status_filter, bin_filter)
        session.close()

        return render_template('_category_rows.html', categories=category_data)
    except Exception as e:
        logger.error(f"Error filtering Tab 1: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to filter categories'}), 500

@tab1_bp.route('/tab/1/subcat_data')
def tab1_subcat_data():
    category = unquote(request.args.get('category'))
    page = int(request.args.get('page', 1))
    per_page = 10
    filter_query = request.args.get('filter', '').lower()
    sort = request.args.get('sort', '')
    status_filter = request.args.get('statusFilter', '').lower()
    bin_filter = request.args.get('binFilter', '').lower()
    logger.debug(f"subcat_data: category={category}, page={page}, per_page={per_page}, filter_query={filter_query}, sort={sort}, status_filter={status_filter}, bin_filter={bin_filter}")

    if not category:
        logger.error("Category parameter is missing in subcat_data request")
        return jsonify({'error': 'Category is required'}), 400

    logger.info(f"Fetching subcategories for category: {category}")
    try:
        session = db.session()

        base_mappings = session.query(RentalClassMapping).filter(
            func.lower(RentalClassMapping.category) == category.lower()
        ).all()
        user_mappings = session.query(UserRentalClassMapping).filter(
            func.lower(UserRentalClassMapping.category) == category.lower()
        ).all()
        logger.debug(f"Found {len(base_mappings)} base mappings and {len(user_mappings)} user mappings for category {category}")

        if not base_mappings and not user_mappings:
            logger.warning(f"No mappings found for category {category}")
            session.close()
            return jsonify({
                'subcategories': [],
                'total_subcats': 0,
                'page': page,
                'per_page': per_page,
                'message': f"No mappings found for category '{category}'. Please add mappings in the Categories tab."
            })

        mappings_dict = {str(m.rental_class_id): {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[str(um.rental_class_id)] = {'category': um.category, 'subcategory': um.subcategory}

        subcategories = {}
        for rental_class_id, data in mappings_dict.items():
            subcategory = data['subcategory']
            if not subcategory:
                continue
            if subcategory not in subcategories:
                subcategories[subcategory] = []
            subcategories[subcategory].append(rental_class_id)

        subcat_list = sorted(subcategories.keys())
        if filter_query:
            subcat_list = [s for s in subcat_list if filter_query in s.lower()]
        if sort == 'subcategory_asc':
            subcat_list.sort()
        elif sort == 'subcategory_desc':
            subcat_list.sort(reverse=True)

        total_subcats = len(subcat_list)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_subcats = subcat_list[start:end]
        logger.debug(f"Total subcategories: {total_subcats}, paginated: {paginated_subcats}")

        subcategory_data = []
        for subcat in paginated_subcats:
            rental_class_ids = subcategories[subcat]
            logger.debug(f"Processing subcategory {subcat} with rental_class_ids: {rental_class_ids}")

            total_items_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.cast(ItemMaster.rental_class_num, db.String)).in_(rental_class_ids)
            )
            if status_filter:
                total_items_query = total_items_query.filter(func.lower(ItemMaster.status) == status_filter.lower())
            if bin_filter:
                total_items_query = total_items_query.filter(
                    func.lower(func.trim(func.coalesce(ItemMaster.bin_location, ''))) == bin_filter.lower()
                )
            total_items = total_items_query.scalar() or 0

            items_on_contracts_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.cast(ItemMaster.rental_class_num, db.String)).in_(rental_class_ids),
                ItemMaster.status.in_(['On Rent', 'Delivered'])
            )
            if status_filter:
                items_on_contracts_query = items_on_contracts_query.filter(func.lower(ItemMaster.status) == status_filter.lower())
            if bin_filter:
                items_on_contracts_query = items_on_contracts_query.filter(
                    func.lower(func.trim(func.coalesce(ItemMaster.bin_location, ''))) == bin_filter.lower()
                )
            items_on_contracts = items_on_contracts_query.scalar() or 0

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
                func.trim(func.cast(ItemMaster.rental_class_num, db.String)).in_(rental_class_ids),
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
            if status_filter:
                items_in_service_query = items_in_service_query.filter(func.lower(ItemMaster.status) == status_filter.lower())
            if bin_filter:
                items_in_service_query = items_in_service_query.filter(
                    func.lower(func.trim(func.coalesce(ItemMaster.bin_location, ''))) == bin_filter.lower()
                )
            items_in_service = items_in_service_query.scalar() or 0

            items_available_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.cast(ItemMaster.rental_class_num, db.String)).in_(rental_class_ids),
                ItemMaster.status == 'Ready to Rent'
            )
            if status_filter:
                items_available_query = items_available_query.filter(func.lower(ItemMaster.status) == status_filter.lower())
            if bin_filter:
                items_available_query = items_available_query.filter(
                    func.lower(func.trim(func.coalesce(ItemMaster.bin_location, ''))) == bin_filter.lower()
                )
            items_available = items_available_query.scalar() or 0

            subcategory_data.append({
                'subcategory': subcat,
                'total_items': total_items,
                'items_on_contracts': items_on_contracts,
                'items_in_service': items_in_service,
                'items_available': items_available
            })

        if sort == 'total_items_asc':
            subcategory_data.sort(key=lambda x: x['total_items'])
        elif sort == 'total_items_desc':
            subcategory_data.sort(key=lambda x: x['total_items'], reverse=True)

        session.close()
        logger.debug(f"Returning subcategory_data: {subcategory_data}")
        return jsonify({
            'subcategories': subcategory_data,
            'total_subcats': total_subcats,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        logger.error(f"Error fetching subcategory data for category {category}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch subcategory data', 'details': str(e)}), 500

@tab1_bp.route('/tab/1/common_names')
def tab1_common_names():
    category = unquote(request.args.get('category'))
    subcategory = unquote(request.args.get('subcategory'))
    page = int(request.args.get('page', 1))
    per_page = 10
    filter_query = request.args.get('filter', '').lower()
    sort = request.args.get('sort', '')
    status_filter = request.args.get('statusFilter', '').lower()
    bin_filter = request.args.get('binFilter', '').lower()
    logger.debug(f"common_names: category={category}, subcategory={subcategory}, page={page}, per_page={per_page}, filter_query={filter_query}, sort={sort}, status_filter={status_filter}, bin_filter={bin_filter}")

    if not category or not subcategory:
        logger.error("Category and subcategory are required in common_names request")
        return jsonify({'error': 'Category and subcategory are required'}), 400

    try:
        session = db.session()

        base_mappings = session.query(RentalClassMapping).filter(
            func.lower(RentalClassMapping.category) == category.lower(),
            func.lower(RentalClassMapping.subcategory) == subcategory.lower()
        ).all()
        user_mappings = session.query(UserRentalClassMapping).filter(
            func.lower(UserRentalClassMapping.category) == category.lower(),
            func.lower(UserRentalClassMapping.subcategory) == subcategory.lower()
        ).all()
        logger.debug(f"Found {len(base_mappings)} base mappings and {len(user_mappings)} user mappings for category {category}, subcategory {subcategory}")

        mappings_dict = {str(m.rental_class_id): {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[str(um.rental_class_id)] = {'category': um.category, 'subcategory': um.subcategory}

        rental_class_ids = list(mappings_dict.keys())
        logger.debug(f"rental_class_ids: {rental_class_ids}")

        common_names_query = session.query(
            ItemMaster.common_name,
            func.count(ItemMaster.tag_id).label('total_items')
        ).filter(
            func.trim(func.cast(ItemMaster.rental_class_num, db.String)).in_(rental_class_ids)
        )
        if filter_query:
            common_names_query = common_names_query.filter(
                func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
            )
        if status_filter:
            common_names_query = common_names_query.filter(func.lower(ItemMaster.status) == status_filter.lower())
        if bin_filter:
            common_names_query = common_names_query.filter(
                func.lower(func.trim(func.coalesce(ItemMaster.bin_location, ''))) == bin_filter.lower()
            )
        common_names_query = common_names_query.group_by(ItemMaster.common_name)

        if sort == 'name_asc':
            common_names_query = common_names_query.order_by(asc(func.lower(ItemMaster.common_name)))
        elif sort == 'name_desc':
            common_names_query = common_names_query.order_by(desc(func.lower(ItemMaster.common_name)))
        elif sort == 'total_items_asc':
            common_names_query = common_names_query.order_by(asc('total_items'))
        elif sort == 'total_items_desc':
            common_names_query = common_names_query.order_by(desc('total_items'))

        common_names_all = common_names_query.all()
        logger.debug(f"Total common names fetched: {len(common_names_all)}")

        common_names = []
        for name, total in common_names_all:
            if not name:
                continue

            items_on_contracts_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.cast(ItemMaster.rental_class_num, db.String)).in_(rental_class_ids),
                ItemMaster.common_name == name,
                ItemMaster.status.in_(['On Rent', 'Delivered'])
            )
            if filter_query:
                items_on_contracts_query = items_on_contracts_query.filter(
                    func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
                )
            if status_filter:
                items_on_contracts_query = items_on_contracts_query.filter(func.lower(ItemMaster.status) == status_filter.lower())
            if bin_filter:
                items_on_contracts_query = items_on_contracts_query.filter(
                    func.lower(func.trim(func.coalesce(ItemMaster.bin_location, ''))) == bin_filter.lower()
                )
            items_on_contracts = items_on_contracts_query.scalar() or 0

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
                func.trim(func.cast(ItemMaster.rental_class_num, db.String)).in_(rental_class_ids),
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
            if status_filter:
                items_in_service_query = items_in_service_query.filter(func.lower(ItemMaster.status) == status_filter.lower())
            if bin_filter:
                items_in_service_query = items_in_service_query.filter(
                    func.lower(func.trim(func.coalesce(ItemMaster.bin_location, ''))) == bin_filter.lower()
                )
            items_in_service = items_in_service_query.scalar() or 0

            items_available_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.cast(ItemMaster.rental_class_num, db.String)).in_(rental_class_ids),
                ItemMaster.common_name == name,
                ItemMaster.status == 'Ready to Rent'
            )
            if filter_query:
                items_available_query = items_available_query.filter(
                    func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
                )
            if status_filter:
                items_available_query = items_available_query.filter(func.lower(ItemMaster.status) == status_filter.lower())
            if bin_filter:
                items_available_query = items_available_query.filter(
                    func.lower(func.trim(func.coalesce(ItemMaster.bin_location, ''))) == bin_filter.lower()
                )
            items_available = items_available_query.scalar() or 0

            common_names.append({
                'name': name,
                'total_items': total,
                'items_on_contracts': items_on_contracts,
                'items_in_service': items_in_service,
                'items_available': items_available
            })

        total_common_names = len(common_names)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_common_names = common_names[start:end]
        logger.debug(f"Returning {len(paginated_common_names)} paginated common names out of {total_common_names}")

        session.close()
        return jsonify({
            'common_names': paginated_common_names,
            'total_common_names': total_common_names,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        logger.error(f"Error fetching common names for category {category}, subcategory {subcategory}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch common names'}), 500

@tab1_bp.route('/tab/1/data')
def tab1_data():
    category = unquote(request.args.get('category'))
    subcategory = unquote(request.args.get('subcategory'))
    common_name = unquote(request.args.get('common_name'))
    page = int(request.args.get('page', 1))
    per_page = 10
    filter_query = request.args.get('filter', '').lower()
    sort = request.args.get('sort', '')
    status_filter = request.args.get('statusFilter', '').lower()
    bin_filter = request.args.get('binFilter', '').lower()
    logger.debug(f"data: category={category}, subcategory={subcategory}, common_name={common_name}, page={page}, per_page={per_page}, filter_query={filter_query}, sort={sort}, status_filter={status_filter}, bin_filter={bin_filter}")

    if not category or not subcategory or not common_name:
        logger.error("Category, subcategory, and common name are required in data request")
        return jsonify({'error': 'Category, subcategory, and common name are required'}), 400

    try:
        session = db.session()

        base_mappings = session.query(RentalClassMapping).filter(
            func.lower(RentalClassMapping.category) == category.lower(),
            func.lower(RentalClassMapping.subcategory) == subcategory.lower()
        ).all()
        user_mappings = session.query(UserRentalClassMapping).filter(
            func.lower(UserRentalClassMapping.category) == category.lower(),
            func.lower(UserRentalClassMapping.subcategory) == subcategory.lower()
        ).all()
        logger.debug(f"Found {len(base_mappings)} base mappings and {len(user_mappings)} user mappings for category {category}, subcategory {subcategory}")

        mappings_dict = {str(m.rental_class_id): {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[str(um.rental_class_id)] = {'category': um.category, 'subcategory': um.subcategory}

        rental_class_ids = list(mappings_dict.keys())
        logger.debug(f"rental_class_ids: {rental_class_ids}")

        query = session.query(ItemMaster).filter(
            func.trim(func.cast(ItemMaster.rental_class_num, db.String)).in_(rental_class_ids),
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
        if status_filter:
            query = query.filter(func.lower(ItemMaster.status) == status_filter.lower())
        if bin_filter:
            query = query.filter(
                func.lower(func.trim(func.coalesce(ItemMaster.bin_location, ''))) == bin_filter.lower()
            )

        if sort == 'tag_id_asc':
            query = query.order_by(asc(ItemMaster.tag_id))
        elif sort == 'tag_id_desc':
            query = query.order_by(desc(ItemMaster.tag_id))
        elif sort == 'last_scanned_date_asc':
            query = query.order_by(asc(ItemMaster.date_last_scanned))
        elif sort == 'last_scanned_date_desc':
            query = query.order_by(desc(ItemMaster.date_last_scanned))

        total_items = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        logger.debug(f"Fetched {len(items)} items out of {total_items} for common_name {common_name}")

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
        logger.debug(f"Returning items_data: {len(items_data)} items")
        return jsonify({
            'items': items_data,
            'total_items': total_items,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        logger.error(f"Error fetching items for category {category}, subcategory {subcategory}, common_name {common_name}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch items'}), 500

@tab1_bp.route('/tab/1/update_bin_location', methods=['POST'])
def update_bin_location():
    logger.debug("update_bin_location route accessed")
    try:
        session = db.session()
        data = request.get_json()
        tag_id = data.get('tag_id')
        bin_location = data.get('bin_location')
        logger.debug(f"update_bin_location: tag_id={tag_id}, bin_location={bin_location}")

        if not tag_id or not bin_location:
            logger.error("tag_id and bin_location are required")
            return jsonify({'error': 'tag_id and bin_location are required'}), 400

        item = session.query(ItemMaster).filter(ItemMaster.tag_id == tag_id).first()
        if not item:
            logger.warning(f"Item not found for tag_id {tag_id}")
            return jsonify({'error': 'Item not found'}), 404

        item.bin_location = bin_location
        item.date_updated = func.now()
        session.commit()
        logger.info(f"Updated bin_location for tag_id {tag_id} to {bin_location}")

        session.close()
        return jsonify({'message': 'Bin location updated successfully'})
    except Exception as e:
        logger.error(f"Error updating bin location: {str(e)}", exc_info=True)
        session.rollback()
        return jsonify({'error': 'Failed to update bin location'}), 500
    finally:
        session.close()

@tab1_bp.route('/tab/1/update_status', methods=['POST'])
def update_status():
    logger.debug("update_status route accessed")
    try:
        session = db.session()
        data = request.get_json()
        tag_id = data.get('tag_id')
        status = data.get('status')
        logger.debug(f"update_status: tag_id={tag_id}, status={status}")

        if not tag_id or not status:
            logger.error("tag_id and status are required")
            return jsonify({'error': 'tag_id and status are required'}), 400

        item = session.query(ItemMaster).filter(ItemMaster.tag_id == tag_id).first()
        if not item:
            logger.warning(f"Item not found for tag_id {tag_id}")
            return jsonify({'error': 'Item not found'}), 404

        if status == 'Ready to Rent' and item.status not in ['On Rent', 'Delivered']:
            logger.warning(f"Cannot set status to Ready to Rent for tag_id {tag_id}, current status: {item.status}")
            return jsonify({'error': 'Cannot set status to Ready to Rent unless current status is On Rent or Delivered'}), 400

        item.status = status
        item.date_updated = func.now()
        session.commit()
        logger.info(f"Updated status for tag_id {tag_id} to {status}")

        session.close()
        return jsonify({'message': 'Status updated successfully'})
    except Exception as e:
        logger.error(f"Error updating status: {str(e)}", exc_info=True)
        session.rollback()
        return jsonify({'error': 'Failed to update status'}), 500
    finally:
        session.close()

@tab1_bp.route('/tab/1/full_items_by_rental_class')
def full_items_by_rental_class():
    category = unquote(request.args.get('category'))
    subcategory = unquote(request.args.get('subcategory'))
    common_name = unquote(request.args.get('common_name'))
    logger.debug(f"full_items_by_rental_class: category={category}, subcategory={subcategory}, common_name={common_name}")

    if not category or not subcategory or not common_name:
        logger.error("Category, subcategory, and common name are required in full_items_by_rental_class request")
        return jsonify({'error': 'Category, subcategory, and common name are required'}), 400

    try:
        session = db.session()

        base_mappings = session.query(RentalClassMapping).filter(
            func.lower(RentalClassMapping.category) == category.lower(),
            func.lower(RentalClassMapping.subcategory) == subcategory.lower()
        ).all()
        user_mappings = session.query(UserRentalClassMapping).filter(
            func.lower(UserRentalClassMapping.category) == category.lower(),
            func.lower(UserRentalClassMapping.subcategory) == subcategory.lower()
        ).all()
        logger.debug(f"Found {len(base_mappings)} base mappings and {len(user_mappings)} user mappings for category {category}, subcategory {subcategory}")

        mappings_dict = {str(m.rental_class_id): {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[str(um.rental_class_id)] = {'category': um.category, 'subcategory': um.subcategory}

        rental_class_ids = list(mappings_dict.keys())
        logger.debug(f"rental_class_ids: {rental_class_ids}")

        items_query = session.query(ItemMaster).filter(
            func.trim(func.cast(ItemMaster.rental_class_num, db.String)).in_(rental_class_ids),
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

        logger.debug(f"Returning {len(items_data)} items for common_name {common_name}")
        session.close()
        return jsonify({
            'items': items_data,
            'total_items': len(items_data)
        })
    except Exception as e:
        logger.error(f"Error fetching full items for category {category}, subcategory {subcategory}, common_name {common_name}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch full items'}), 500