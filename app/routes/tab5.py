from flask import Blueprint, render_template, request, jsonify, current_app, Response
from .. import db, cache
from ..models.db_models import ItemMaster, Transaction, RentalClassMapping, UserRentalClassMapping
from ..services.api_client import APIClient
from sqlalchemy import func, desc, or_, asc, text
from time import time
from datetime import datetime, timedelta
import logging
import sys
from urllib.parse import unquote
import csv
from io import StringIO
import json

# Configure logging
logger = logging.getLogger('tab5')
logger.setLevel(logging.DEBUG)

# Remove existing handlers to avoid duplicates
logger.handlers = []

# File handler for rfid_dashboard.log
file_handler = logging.FileHandler('/home/tim/test_rfidpi/logs/rfid_dashboard.log')
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Secondary file handler for debug.log
debug_handler = logging.FileHandler('/home/tim/test_rfidpi/logs/debug.log')
debug_handler.setLevel(logging.DEBUG)
debug_handler.setFormatter(formatter)
logger.addHandler(debug_handler)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Also add logs to the root logger (which Gunicorn might capture)
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
    root_logger.addHandler(console_handler)

tab5_bp = Blueprint('tab5', __name__)

# Version marker
logger.info("Deployed tab5.py version: 2025-04-27-v22")

def get_category_data(session, filter_query='', sort='', status_filter='', bin_filter=''):
    # Check if data is in cache
    cache_key = f'tab5_view_data_{filter_query}_{sort}_{status_filter}_{bin_filter}'
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        logger.info("Serving Tab 5 data from cache")
        return json.loads(cached_data)

    # Fetch all rental class mappings from both tables
    base_mappings = session.query(RentalClassMapping).all()
    user_mappings = session.query(UserRentalClassMapping).all()
    logger.debug(f"Fetched {len(base_mappings)} base mappings and {len(user_mappings)} user mappings")

    # Merge mappings, prioritizing user mappings
    mappings_dict = {m.rental_class_id: {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
    for um in user_mappings:
        mappings_dict[um.rental_class_id] = {'category': um.category, 'subcategory': um.subcategory}

    if not mappings_dict:
        logger.warning("No rental class mappings found")
        return []

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

    # Calculate counts for each category
    category_data = []
    for cat, mappings in categories.items():
        if filter_query and filter_query not in cat.lower():
            continue
        rental_class_ids = [str(m['rental_class_id']).strip() for m in mappings]

        # Always filter by bin_location for Tab 5
        total_items_query = session.query(func.count(ItemMaster.tag_id)).filter(
            func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids),
            func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'sold', 'pack', 'burst'])
        )
        if status_filter:
            total_items_query = total_items_query.filter(func.lower(ItemMaster.status) == status_filter.lower())
        if bin_filter:
            total_items_query = total_items_query.filter(
                func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))) == bin_filter.lower()
            )
        total_items = total_items_query.scalar() or 0

        items_on_contracts_query = session.query(func.count(ItemMaster.tag_id)).filter(
            func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids),
            ItemMaster.status.in_(['On Rent', 'Delivered']),
            func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'sold', 'pack', 'burst'])
        )
        if status_filter:
            items_on_contracts_query = items_on_contracts_query.filter(func.lower(ItemMaster.status) == status_filter.lower())
        if bin_filter:
            items_on_contracts_query = items_on_contracts_query.filter(
                func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))) == bin_filter.lower()
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
            func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids),
            func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'sold', 'pack', 'burst']),
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
                func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))) == bin_filter.lower()
            )
        items_in_service = items_in_service_query.scalar() or 0

        items_available_query = session.query(func.count(ItemMaster.tag_id)).filter(
            func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids),
            ItemMaster.status == 'Ready to Rent',
            func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'sold', 'pack', 'burst'])
        )
        if status_filter:
            items_available_query = items_available_query.filter(func.lower(ItemMaster.status) == status_filter.lower())
        if bin_filter:
            items_available_query = items_available_query.filter(
                func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))) == bin_filter.lower()
            )
        items_available = items_available_query.scalar() or 0

        # Only include categories with items matching the bin_location filter
        if total_items == 0:
            continue

        category_data.append({
            'category': cat,
            'cat_id': cat.lower().replace(' ', '_').replace('/', '_'),
            'total_items': total_items,
            'items_on_contracts': items_on_contracts,
            'items_in_service': items_in_service,
            'items_available': items_available
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

    # Cache the data
    cache.set(cache_key, json.dumps(category_data), ex=60)
    logger.info("Cached Tab 5 data")
    return category_data

@tab5_bp.route('/tab/5')
def tab5_view():
    logger.info("Tab 5 route accessed")
    try:
        session = db.session()
        filter_query = request.args.get('filter', '').lower()
        sort = request.args.get('sort', '')
        status_filter = request.args.get('statusFilter', '').lower()
        bin_filter = request.args.get('binFilter', '').lower()

        category_data = get_category_data(session, filter_query, sort, status_filter, bin_filter)
        logger.info(f"Fetched {len(category_data)} categories for tab5")

        session.close()
        return render_template('tab5.html', categories=category_data, cache_bust=int(time()))
    except Exception as e:
        logger.error(f"Error rendering Tab 5: {str(e)}", exc_info=True)
        return render_template('tab5.html', categories=[], cache_bust=int(time()))

@tab5_bp.route('/tab/5/filter', methods=['POST'])
def tab5_filter():
    logger.info("Tab 5 filter route accessed")
    try:
        session = db.session()
        filter_query = request.form.get('category-filter', '').lower()
        sort = request.form.get('category-sort', '')
        status_filter = request.form.get('statusFilter', '').lower()
        bin_filter = request.form.get('binFilter', '').lower()

        category_data = get_category_data(session, filter_query, sort, status_filter, bin_filter)
        session.close()

        return jsonify(category_data)  # Return JSON data directly since we're not using _category_rows.html
    except Exception as e:
        logger.error(f"Error filtering Tab 5: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to filter categories'}), 500

@tab5_bp.route('/tab/5/subcat_data')
def tab5_subcat_data():
    category = unquote(request.args.get('category'))
    page = int(request.args.get('page', 1))
    per_page = 10
    filter_query = request.args.get('filter', '').lower()
    status_filter = request.args.get('statusFilter', '').lower()
    bin_filter = request.args.get('binFilter', '').lower()
    sort = request.args.get('sort', '')

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

        subcategory_data = []
        for subcat in paginated_subcats:
            rental_class_ids = subcategories[subcat]

            total_items_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids),
                func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'sold', 'pack', 'burst'])
            )
            if status_filter:
                total_items_query = total_items_query.filter(func.lower(ItemMaster.status) == status_filter.lower())
            if bin_filter:
                total_items_query = total_items_query.filter(
                    func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))) == bin_filter.lower()
                )
            total_items = total_items_query.scalar() or 0

            if total_items == 0:
                continue

            items_on_contracts_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids),
                ItemMaster.status.in_(['On Rent', 'Delivered']),
                func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'sold', 'pack', 'burst'])
            )
            if status_filter:
                items_on_contracts_query = items_on_contracts_query.filter(func.lower(ItemMaster.status) == status_filter.lower())
            if bin_filter:
                items_on_contracts_query = items_on_contracts_query.filter(
                    func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))) == bin_filter.lower()
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
                func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids),
                func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'sold', 'pack', 'burst']),
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
                    func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))) == bin_filter.lower()
                )
            items_in_service = items_in_service_query.scalar() or 0

            items_available_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids),
                ItemMaster.status == 'Ready to Rent',
                func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'sold', 'pack', 'burst'])
            )
            if status_filter:
                items_available_query = items_available_query.filter(func.lower(ItemMaster.status) == status_filter.lower())
            if bin_filter:
                items_available_query = items_available_query.filter(
                    func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))) == bin_filter.lower()
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
        return jsonify({
            'subcategories': subcategory_data,
            'total_subcats': total_subcats,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        logger.error(f"Error fetching subcategory data for category {category}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch subcategory data', 'details': str(e)}), 500

@tab5_bp.route('/tab/5/common_names')
def tab5_common_names():
    category = unquote(request.args.get('category'))
    subcategory = unquote(request.args.get('subcategory'))
    page = int(request.args.get('page', 1))
    per_page = 10
    filter_query = request.args.get('filter', '').lower()
    status_filter = request.args.get('statusFilter', '').lower()
    bin_filter = request.args.get('binFilter', '').lower()
    sort = request.args.get('sort', '')

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

        mappings_dict = {str(m.rental_class_id): {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[str(um.rental_class_id)] = {'category': um.category, 'subcategory': um.subcategory}

        rental_class_ids = list(mappings_dict.keys())

        common_names_query = session.query(
            ItemMaster.common_name,
            func.count(ItemMaster.tag_id).label('total_items')
        ).filter(
            func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids),
            func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'sold', 'pack', 'burst'])
        )
        if filter_query:
            common_names_query = common_names_query.filter(
                func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
            )
        if status_filter:
            common_names_query = common_names_query.filter(func.lower(ItemMaster.status) == status_filter.lower())
        if bin_filter:
            common_names_query = common_names_query.filter(
                func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))) == bin_filter.lower()
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
        common_names = []
        for name, total in common_names_all:
            if not name:
                continue

            items_on_contracts_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids),
                ItemMaster.common_name == name,
                ItemMaster.status.in_(['On Rent', 'Delivered']),
                func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'sold', 'pack', 'burst'])
            )
            if filter_query:
                items_on_contracts_query = items_on_contracts_query.filter(
                    func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
                )
            if status_filter:
                items_on_contracts_query = items_on_contracts_query.filter(func.lower(ItemMaster.status) == status_filter.lower())
            if bin_filter:
                items_on_contracts_query = items_on_contracts_query.filter(
                    func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))) == bin_filter.lower()
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
                func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids),
                ItemMaster.common_name == name,
                func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'sold', 'pack', 'burst']),
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
                    func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))) == bin_filter.lower()
                )
            items_in_service = items_in_service_query.scalar() or 0

            items_available_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids),
                ItemMaster.common_name == name,
                ItemMaster.status == 'Ready to Rent',
                func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'sold', 'pack', 'burst'])
            )
            if filter_query:
                items_available_query = items_available_query.filter(
                    func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
                )
            if status_filter:
                items_available_query = items_available_query.filter(func.lower(ItemMaster.status) == status_filter.lower())
            if bin_filter:
                items_available_query = items_available_query.filter(
                    func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))) == bin_filter.lower()
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

        session.close()
        return jsonify({
            'common_names': paginated_common_names,
            'total_common_names': total_common_names,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        logger.error(f"Error fetching common names for category {category}, subcategory {subcategory}: {str(e)}")
        return jsonify({'error': 'Failed to fetch common names'}), 500

@tab5_bp.route('/tab/5/data')
def tab5_data():
    category = unquote(request.args.get('category'))
    subcategory = unquote(request.args.get('subcategory'))
    common_name = unquote(request.args.get('common_name'))
    page = int(request.args.get('page', 1))
    per_page = 10
    filter_query = request.args.get('filter', '').lower()
    status_filter = request.args.get('statusFilter', '').lower()
    bin_filter = request.args.get('binFilter', '').lower()
    sort = request.args.get('sort', '')

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

        mappings_dict = {str(m.rental_class_id): {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[str(um.rental_class_id)] = {'category': um.category, 'subcategory': um.subcategory}

        rental_class_ids = list(mappings_dict.keys())

        query = session.query(ItemMaster).filter(
            func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids),
            ItemMaster.common_name == common_name,
            func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'sold', 'pack', 'burst'])
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
                func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))) == bin_filter.lower()
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
        logger.error(f"Error fetching items for category {category}, subcategory {subcategory}, common_name {common_name}: {str(e)}")
        return jsonify({'error': 'Failed to fetch items'}), 500

@tab5_bp.route('/tab/5/update_bin_location', methods=['POST'])
def update_bin_location():
    try:
        data = request.get_json()
        tag_id = data.get('tag_id')
        new_bin_location = data.get('bin_location')

        if not tag_id or not new_bin_location:
            return jsonify({'error': 'Tag ID and bin location are required'}), 400

        if new_bin_location not in ['resale', 'sold', 'pack', 'burst']:
            return jsonify({'error': 'Invalid bin location'}), 400

        session = db.session()
        item = session.query(ItemMaster).filter_by(tag_id=tag_id).first()
        if not item:
            session.close()
            return jsonify({'error': 'Item not found'}), 404

        # Update local database
        current_time = datetime.now()
        item.bin_location = new_bin_location
        item.date_last_scanned = current_time
        session.commit()

        # Update external API
        api_client = APIClient()
        api_client.update_bin_location(tag_id, new_bin_location)

        session.close()
        logger.info(f"Updated bin_location for tag_id {tag_id} to {new_bin_location} and date_last_scanned to {current_time}")
        return jsonify({'message': 'Bin location updated successfully'})
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating bin location for tag {tag_id}: {str(e)}")
        session.close()
        return jsonify({'error': str(e)}), 500

@tab5_bp.route('/tab/5/update_status', methods=['POST'])
def update_status():
    try:
        data = request.get_json()
        tag_id = data.get('tag_id')
        new_status = data.get('status')

        if not tag_id or not new_status:
            return jsonify({'error': 'Tag ID and status are required'}), 400

        if new_status not in ['Ready to Rent', 'Sold']:
            return jsonify({'error': 'Status can only be updated to "Ready to Rent" or "Sold"'}), 400

        session = db.session()
        item = session.query(ItemMaster).filter_by(tag_id=tag_id).first()
        if not item:
            session.close()
            return jsonify({'error': 'Item not found'}), 404

        # For "Ready to Rent", only allow update from "On Rent", "Delivered", or "Sold"
        if new_status == 'Ready to Rent' and item.status not in ['On Rent', 'Delivered', 'Sold']:
            session.close()
            return jsonify({'error': 'Status can only be updated to "Ready to Rent" from "On Rent", "Delivered", or "Sold"'}), 400

        # Update local database
        current_time = datetime.now()
        item.status = new_status
        item.date_last_scanned = current_time
        session.commit()

        # Update external API
        api_client = APIClient()
        api_client.update_status(tag_id, new_status)

        session.close()
        logger.info(f"Updated status for tag_id {tag_id} to {new_status} and date_last_scanned to {current_time}")
        return jsonify({'message': 'Status updated successfully'})
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating status for tag {tag_id}: {str(e)}")
        session.close()
        return jsonify({'error': str(e)}), 500

@tab5_bp.route('/tab/5/update_resale_pack_to_sold', methods=['POST'])
def update_resale_pack_to_sold():
    """
    Update items in ItemMaster with bin_location 'resale' or 'pack', status 'On Rent' or 'Delivered',
    and date_last_scanned more than 4 days ago to status 'Sold' via API PATCH.
    """
    try:
        session = db.session()
        current_time = datetime.now()
        four_days_ago = current_time - timedelta(days=4)

        # Query items matching the criteria
        items_to_update = session.query(ItemMaster).filter(
            func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'pack']),
            ItemMaster.status.in_(['On Rent', 'Delivered']),
            ItemMaster.date_last_scanned < four_days_ago
        ).all()

        if not items_to_update:
            session.close()
            return jsonify({'status': 'success', 'message': 'No items found to update'})

        api_client = APIClient()
        updated_items = 0

        for item in items_to_update:
            try:
                # Update status to 'Sold' via API
                api_client.update_status(item.tag_id, 'Sold')
                # Update local database
                item.status = 'Sold'
                item.date_last_scanned = current_time
                updated_items += 1
            except Exception as e:
                logger.error(f"Failed to update tag_id {item.tag_id}: {str(e)}")
                continue

        session.commit()
        session.close()
        logger.info(f"Updated {updated_items} items from resale/pack to Sold status")
        return jsonify({'status': 'success', 'message': f'Updated {updated_items} items to Sold status'})
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating resale/pack items to Sold: {str(e)}")
        session.close()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@tab5_bp.route('/tab/5/export_sold_burst_csv')
def export_sold_burst_csv():
    try:
        session = db.session()

        items = session.query(ItemMaster).filter(
            func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['sold', 'burst'])
        ).all()

        output = StringIO()
        writer = csv.writer(output)

        headers = ['Tag ID', 'Common Name', 'Bin Location', 'Status', 'Last Scanned Date', 'Quality', 'Notes']
        writer.writerow(headers)

        for item in items:
            last_scanned_date = item.date_last_scanned.isoformat() if item.date_last_scanned else 'N/A'
            writer.writerow([
                item.tag_id,
                item.common_name,
                item.bin_location,
                item.status,
                last_scanned_date,
                item.quality or 'N/A',
                item.notes or 'N/A'
            ])

        session.close()

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=sold_burst_items.csv'}
        )
    except Exception as e:
        logger.error(f"Error exporting sold/burst items to CSV: {str(e)}")
        return jsonify({'error': 'Failed to export CSV'}), 500

@tab5_bp.route('/tab/5/full_items_by_rental_class')
def full_items_by_rental_class():
    category = unquote(request.args.get('category'))
    subcategory = unquote(request.args.get('subcategory'))
    common_name = unquote(request.args.get('common_name'))

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

        mappings_dict = {str(m.rental_class_id): {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[str(um.rental_class_id)] = {'category': um.category, 'subcategory': um.subcategory}

        rental_class_ids = list(mappings_dict.keys())

        items_query = session.query(ItemMaster).filter(
            func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids),
            ItemMaster.common_name == common_name,
            func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'sold', 'pack', 'burst'])
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
        logger.error(f"Error fetching full items for category {category}, subcategory {subcategory}, common_name {common_name}: {str(e)}")
        return jsonify({'error': 'Failed to fetch full items'}), 500

@tab5_bp.route('/tab/5/bulk_update_common_name', methods=['POST'])
def bulk_update_common_name():
    try:
        data = request.get_json()
        category = data.get('category')
        subcategory = data.get('subcategory')
        common_name = data.get('common_name')
        new_bin_location = data.get('bin_location')
        new_status = data.get('status')

        if not category or not subcategory or not common_name:
            return jsonify({'error': 'Category, subcategory, and common name are required'}), 400

        if not new_bin_location and not new_status:
            return jsonify({'error': 'At least one of bin_location or status must be provided'}), 400

        session = db.session()

        # Get rental class IDs for the category and subcategory
        base_mappings = session.query(RentalClassMapping).filter(
            func.lower(RentalClassMapping.category) == category.lower(),
            func.lower(RentalClassMapping.subcategory) == subcategory.lower()
        ).all()
        user_mappings = session.query(UserRentalClassMapping).filter(
            func.lower(UserRentalClassMapping.category) == category.lower(),
            func.lower(UserRentalClassMapping.subcategory) == subcategory.lower()
        ).all()

        mappings_dict = {str(m.rental_class_id): {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[str(um.rental_class_id)] = {'category': um.category, 'subcategory': um.subcategory}

        rental_class_ids = list(mappings_dict.keys())

        # Query items matching the criteria
        query = session.query(ItemMaster).filter(
            func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids),
            ItemMaster.common_name == common_name,
            func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'sold', 'pack', 'burst'])
        )

        items = query.all()
        if not items:
            session.close()
            return jsonify({'error': 'No items found for the given criteria'}), 404

        api_client = APIClient()
        updated_items = 0
        current_time = datetime.now()

        for item in items:
            if new_bin_location and new_bin_location in ['resale', 'sold', 'pack', 'burst']:
                item.bin_location = new_bin_location
                item.date_last_scanned = current_time
                api_client.update_bin_location(item.tag_id, new_bin_location)
                updated_items += 1

            if new_status:
                if new_status not in ['Ready to Rent', 'Sold']:
                    session.close()
                    return jsonify({'error': 'Status can only be updated to "Ready to Rent" or "Sold"'}), 400
                if new_status == 'Ready to Rent' and item.status not in ['On Rent', 'Delivered', 'Sold']:
                    continue  # Skip items that can't be updated to "Ready to Rent"
                item.status = new_status
                item.date_last_scanned = current_time
                api_client.update_status(item.tag_id, new_status)
                updated_items += 1

        session.commit()
        session.close()

        logger.info(f"Bulk updated {updated_items} items for category {category}, subcategory {subcategory}, common_name {common_name}")
        return jsonify({'message': f'Bulk update successful, updated {updated_items} items'})
    except Exception as e:
        session.rollback()
        logger.error(f"Error in bulk update for common name {common_name}: {str(e)}")
        session.close()
        return jsonify({'error': str(e)}), 500

@tab5_bp.route('/tab/5/bulk_update_items', methods=['POST'])
def bulk_update_items():
    try:
        data = request.get_json()
        tag_ids = data.get('tag_ids', [])
        new_bin_location = data.get('bin_location')
        new_status = data.get('status')

        if not tag_ids:
            return jsonify({'error': 'Tag IDs are required'}), 400

        if not new_bin_location and not new_status:
            return jsonify({'error': 'At least one of bin_location or status must be provided'}), 400

        session = db.session()
        items = session.query(ItemMaster).filter(ItemMaster.tag_id.in_(tag_ids)).all()

        if not items:
            session.close()
            return jsonify({'error': 'No items found for the given tag IDs'}), 404

        api_client = APIClient()
        updated_items = 0
        current_time = datetime.now()

        for item in items:
            if new_bin_location and new_bin_location in ['resale', 'sold', 'pack', 'burst']:
                item.bin_location = new_bin_location
                item.date_last_scanned = current_time
                api_client.update_bin_location(item.tag_id, new_bin_location)
                updated_items += 1

            if new_status:
                if new_status not in ['Ready to Rent', 'Sold']:
                    session.close()
                    return jsonify({'error': 'Status can only be updated to "Ready to Rent" or "Sold"'}), 400
                if new_status == 'Ready to Rent' and item.status not in ['On Rent', 'Delivered', 'Sold']:
                    continue  # Skip items that can't be updated to "Ready to Rent"
                item.status = new_status
                item.date_last_scanned = current_time
                api_client.update_status(item.tag_id, new_status)
                updated_items += 1

        session.commit()
        session.close()

        logger.info(f"Bulk updated {updated_items} items for tag_ids {tag_ids}")
        return jsonify({'message': f'Bulk update successful, updated {updated_items} items'})
    except Exception as e:
        session.rollback()
        logger.error(f"Error in bulk update for tag_ids {tag_ids}: {str(e)}")
        session.close()
        return jsonify({'error': str(e)}), 500