from flask import Blueprint, render_template, request, jsonify, current_app, Response
from .. import db, cache
from ..models.db_models import ItemMaster, Transaction, RentalClassMapping, UserRentalClassMapping
from ..services.api_client import APIClient
from sqlalchemy import func, desc, or_, asc, text
from time import time
import logging
import sys
from urllib.parse import unquote
import csv
from io import StringIO
import json  # Add import for JSON serialization

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
logger.info("Deployed tab5.py version: 2025-04-25-v14")

@tab5_bp.route('/tab/5')
def tab5_view():
    # Log using both logger and current_app.logger to ensure visibility
    logger.info("Tab 5 route accessed - Starting execution")
    current_app.logger.info("Tab 5 route accessed - Starting execution")
    
    try:
        # Check if data is in cache
        cache_key = 'tab5_view_data'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.info("Serving Tab 5 data from cache")
            current_app.logger.info("Serving Tab 5 data from cache")
            # Deserialize the cached data
            cached_data = json.loads(cached_data)
            return render_template('tab5.html', categories=cached_data, cache_bust=int(time()))

        session = db.session()
        logger.info("Starting new session for tab5")
        current_app.logger.info("Starting new session for tab5")

        # Fetch all rental class mappings from both tables
        base_mappings = session.query(RentalClassMapping).all()
        user_mappings = session.query(UserRentalClassMapping).all()
        logger.debug(f"Fetched {len(base_mappings)} base mappings and {len(user_mappings)} user mappings")
        current_app.logger.debug(f"Fetched {len(base_mappings)} base mappings and {len(user_mappings)} user mappings")
        for bm in base_mappings:
            logger.debug(f"Base mapping: rental_class_id={bm.rental_class_id}, category={bm.category}, subcategory={bm.subcategory}")
            current_app.logger.debug(f"Base mapping: rental_class_id={bm.rental_class_id}, category={bm.category}, subcategory={bm.subcategory}")
        for um in user_mappings:
            logger.debug(f"User mapping: rental_class_id={um.rental_class_id}, category={um.category}, subcategory={um.subcategory}")
            current_app.logger.debug(f"User mapping: rental_class_id={um.rental_class_id}, category={um.category}, subcategory={um.subcategory}")

        # Merge mappings, prioritizing user mappings
        mappings_dict = {m.rental_class_id: {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[um.rental_class_id] = {'category': um.category, 'subcategory': um.subcategory}

        # If no mappings exist, return an empty response with a warning
        if not mappings_dict:
            logger.warning("No rental class mappings found in either rental_class_mappings or user_rental_class_mappings")
            current_app.logger.warning("No rental class mappings found in either rental_class_mappings or user_rental_class_mappings")
            session.close()
            return render_template('tab5.html', categories=[], cache_bust=int(time()))

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
        logger.debug(f"Grouped categories: {list(categories.keys())}")
        current_app.logger.debug(f"Grouped categories: {list(categories.keys())}")

        # Calculate counts for each category, filtering for resale/pack items
        category_data = []
        filter_query = request.args.get('filter', '').lower()
        sort = request.args.get('sort', '')

        for cat, mappings in categories.items():
            rental_class_ids = [str(m['rental_class_id']).strip() for m in mappings]
            logger.debug(f"Processing category {cat} with rental_class_ids: {rental_class_ids}")
            current_app.logger.debug(f"Processing category {cat} with rental_class_ids: {rental_class_ids}")

            # Test the bin_location condition independently
            bin_location_test = session.query(func.count(ItemMaster.tag_id)).filter(
                func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'sold', 'pack', 'burst'])
            ).scalar()
            logger.debug(f"Total items with bin_location in ['resale', 'sold', 'pack', 'burst'] (no rental_class filter): {bin_location_test}")
            current_app.logger.debug(f"Total items with bin_location in ['resale', 'sold', 'pack', 'burst'] (no rental_class filter): {bin_location_test}")

            # Test the rental_class_num condition independently
            rental_class_test = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids)
            ).scalar()
            logger.debug(f"Total items with rental_class_num in {rental_class_ids} (no bin_location filter): {rental_class_test}")
            current_app.logger.debug(f"Total items with rental_class_num in {rental_class_ids} (no bin_location filter): {rental_class_test}")

            # Total items in this category with bin_location in ['resale', 'sold', 'pack', 'burst']
            total_items_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids),
                func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'sold', 'pack', 'burst'])
            )
            if filter_query:
                total_items_query = total_items_query.filter(
                    func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
                )
            total_items = total_items_query.scalar()
            logger.debug(f"Total items for category {cat}: {total_items}")
            current_app.logger.debug(f"Total items for category {cat}: {total_items}")

            # Debug: Fetch raw items for this category
            if total_items == 0:
                logger.debug(f"Skipping category {cat} due to zero total items")
                current_app.logger.debug(f"Skipping category {cat} due to zero total items")
                # Check total items without bin_location filter
                all_items = session.query(func.count(ItemMaster.tag_id)).filter(
                    func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids)
                ).scalar()
                logger.debug(f"Total items (without bin_location filter) for category {cat}: {all_items}")
                current_app.logger.debug(f"Total items (without bin_location filter) for category {cat}: {all_items}")
                if all_items > 0:
                    # Fetch raw items to inspect bin_location and rental_class_num
                    raw_items = session.query(ItemMaster.tag_id, ItemMaster.rental_class_num, ItemMaster.bin_location).filter(
                        func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids)
                    ).all()
                    for item in raw_items:
                        logger.debug(f"Item: tag_id={item.tag_id}, rental_class_num={item.rental_class_num}, bin_location={item.bin_location}")
                        current_app.logger.debug(f"Item: tag_id={item.tag_id}, rental_class_num={item.rental_class_num}, bin_location={item.bin_location}")
                    # Fetch distinct bin_locations
                    bin_locations = session.query(ItemMaster.bin_location).filter(
                        func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids)
                    ).distinct().all()
                    logger.debug(f"Bin locations for category {cat}: {[loc[0] for loc in bin_locations]}")
                    current_app.logger.debug(f"Bin locations for category {cat}: {[loc[0] for loc in bin_locations]}")
                    # Fetch distinct rental_class_num values
                    rental_class_nums = session.query(ItemMaster.rental_class_num).filter(
                        func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids)
                    ).distinct().all()
                    logger.debug(f"Rental class numbers for category {cat}: {[num[0] for num in rental_class_nums]}")
                    current_app.logger.debug(f"Rental class numbers for category {cat}: {[num[0] for num in rental_class_nums]}")
                continue

            # Items on contracts (status = 'On Rent' or 'Delivered')
            items_on_contracts_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids),
                ItemMaster.status.in_(['On Rent', 'Delivered']),
                func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'sold', 'pack', 'burst'])
            )
            if filter_query:
                items_on_contracts_query = items_on_contracts_query.filter(
                    func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
                )
            items_on_contracts = items_on_contracts_query.scalar()
            logger.debug(f"Items on contracts for category {cat}: {items_on_contracts}")
            current_app.logger.debug(f"Items on contracts for category {cat}: {items_on_contracts}")

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
            if filter_query:
                items_in_service_query = items_in_service_query.filter(
                    func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
                )
            items_in_service = items_in_service_query.scalar()
            logger.debug(f"Items in service for category {cat}: {items_in_service}")
            current_app.logger.debug(f"Items in service for category {cat}: {items_in_service}")

            # Items available (status = 'Ready to Rent')
            items_available_query = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids),
                ItemMaster.status == 'Ready to Rent',
                func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'sold', 'pack', 'burst'])
            )
            if filter_query:
                items_available_query = items_available_query.filter(
                    func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
                )
            items_available = items_available_query.scalar()
            logger.debug(f"Items available for category {cat}: {items_available}")
            current_app.logger.debug(f"Items available for category {cat}: {items_available}")

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

        logger.info(f"Fetched {len(category_data)} categories for tab5: {[cat['category'] for cat in category_data]}")
        current_app.logger.info(f"Fetched {len(category_data)} categories for tab5: {[cat['category'] for cat in category_data]}")

        # Cache the data with serialization
        cache.set(cache_key, json.dumps(category_data), ex=60)  # Serialize to JSON before caching
        logger.info("Cached Tab 5 data")
        current_app.logger.info("Cached Tab 5 data")

        session.close()
        return render_template('tab5.html', categories=category_data, cache_bust=int(time()))
    except Exception as e:
        logger.error(f"Error rendering Tab 5: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error rendering Tab 5: {str(e)}", exc_info=True)
        return render_template('tab5.html', categories=[], cache_bust=int(time()))

@tab5_bp.route('/tab/5/subcat_data')
def tab5_subcat_data():
    # Decode the category parameter to handle URL-encoded values
    category = unquote(request.args.get('category'))
    page = int(request.args.get('page', 1))
    per_page = 10
    filter_query = request.args.get('filter', '').lower()
    sort = request.args.get('sort', '')

    if not category:
        logger.error("Category parameter is missing in subcat_data request")
        current_app.logger.error("Category parameter is missing in subcat_data request")
        return jsonify({'error': 'Category is required'}), 400

    logger.info(f"Fetching subcategories for category: {category}")
    current_app.logger.info(f"Fetching subcategories for category: {category}")
    try:
        session = db.session()

        # Fetch mappings for this category (case-insensitive)
        base_mappings = session.query(RentalClassMapping).filter(
            func.lower(RentalClassMapping.category) == category.lower()
        ).all()
        user_mappings = session.query(UserRentalClassMapping).filter(
            func.lower(UserRentalClassMapping.category) == category.lower()
        ).all()
        logger.debug(f"Fetched {len(base_mappings)} base mappings and {len(user_mappings)} user mappings for category {category}")
        current_app.logger.debug(f"Fetched {len(base_mappings)} base mappings and {len(user_mappings)} user mappings for category {category}")

        # Log the mappings for debugging
        if base_mappings:
            logger.debug("Base mappings: " + ", ".join([f"{m.rental_class_id}: {m.category} - {m.subcategory}" for m in base_mappings]))
            current_app.logger.debug("Base mappings: " + ", ".join([f"{m.rental_class_id}: {m.category} - {m.subcategory}" for m in base_mappings]))
        if user_mappings:
            logger.debug("User mappings: " + ", ".join([f"{m.rental_class_id}: {m.category} - {m.subcategory}" for m in user_mappings]))
            current_app.logger.debug("User mappings: " + ", ".join([f"{m.rental_class_id}: {m.category} - {m.subcategory}" for m in user_mappings]))

        # If no mappings exist, return an empty response with a warning
        if not base_mappings and not user_mappings:
            logger.warning(f"No mappings found for category {category} in either rental_class_mappings or user_rental_class_mappings")
            current_app.logger.warning(f"No mappings found for category {category} in either rental_class_mappings or user_rental_class_mappings")
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

        # Group by subcategory
        subcategories = {}
        for rental_class_id, data in mappings_dict.items():
            subcategory = data['subcategory']
            if subcategory not in subcategories:
                subcategories[subcategory] = []
            subcategories[subcategory].append(rental_class_id)

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

        subcategory_data = []
        for subcat in paginated_subcats:
            rental_class_ids = subcategories[subcat]
            logger.debug(f"Processing subcategory {subcat} with rental_class_ids: {rental_class_ids}")
            current_app.logger.debug(f"Processing subcategory {subcat} with rental_class_ids: {rental_class_ids}")

            try:
                # Total items in this subcategory with bin_location in ['resale', 'sold', 'pack', 'burst']
                total_items_query = session.query(func.count(ItemMaster.tag_id)).filter(
                    func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids),
                    func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'sold', 'pack', 'burst'])
                )
                if filter_query:
                    total_items_query = total_items_query.filter(
                        func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
                    )
                total_items = total_items_query.scalar() or 0
                logger.debug(f"Total items for subcategory {subcat}: {total_items}")
                current_app.logger.debug(f"Total items for subcategory {subcat}: {total_items}")

                # Only include subcategories with resale/pack items
                if total_items == 0:
                    logger.debug(f"Skipping subcategory {subcat} due to zero total items")
                    current_app.logger.debug(f"Skipping subcategory {subcat} due to zero total items")
                    # Debug: Check if there are any items with these rental_class_ids
                    all_items = session.query(func.count(ItemMaster.tag_id)).filter(
                        func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids)
                    ).scalar()
                    logger.debug(f"Total items (without bin_location filter) for subcategory {subcat}: {all_items}")
                    current_app.logger.debug(f"Total items (without bin_location filter) for subcategory {subcat}: {all_items}")
                    if all_items > 0:
                        bin_locations = session.query(ItemMaster.bin_location).filter(
                            func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids)
                        ).distinct().all()
                        logger.debug(f"Bin locations for subcategory {subcat}: {[loc[0] for loc in bin_locations]}")
                        current_app.logger.debug(f"Bin locations for subcategory {subcat}: {[loc[0] for loc in bin_locations]}")
                    continue

                # Items on contracts (status = 'On Rent' or 'Delivered')
                items_on_contracts_query = session.query(func.count(ItemMaster.tag_id)).filter(
                    func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids),
                    ItemMaster.status.in_(['On Rent', 'Delivered']),
                    func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'sold', 'pack', 'burst'])
                )
                if filter_query:
                    items_on_contracts_query = items_on_contracts_query.filter(
                        func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
                    )
                items_on_contracts = items_on_contracts_query.scalar() or 0
                logger.debug(f"Items on contracts for subcategory {subcat}: {items_on_contracts}")
                current_app.logger.debug(f"Items on contracts for subcategory {subcat}: {items_on_contracts}")

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
                if filter_query:
                    items_in_service_query = items_in_service_query.filter(
                        func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
                    )
                items_in_service = items_in_service_query.scalar() or 0
                logger.debug(f"Items in service for subcategory {subcat}: {items_in_service}")
                current_app.logger.debug(f"Items in service for subcategory {subcat}: {items_in_service}")

                # Items available (status = 'Ready to Rent')
                items_available_query = session.query(func.count(ItemMaster.tag_id)).filter(
                    func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids),
                    ItemMaster.status == 'Ready to Rent',
                    func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'sold', 'pack', 'burst'])
                )
                if filter_query:
                    items_available_query = items_available_query.filter(
                        func.lower(ItemMaster.common_name).like(f'%{filter_query}%')
                    )
                items_available = items_available_query.scalar() or 0
                logger.debug(f"Items available for subcategory {subcat}: {items_available}")
                current_app.logger.debug(f"Items available for subcategory {subcat}: {items_available}")

                subcategory_data.append({
                    'subcategory': subcat,
                    'total_items': total_items,
                    'items_on_contracts': items_on_contracts,
                    'items_in_service': items_in_service,
                    'items_available': items_available
                })
            except Exception as e:
                logger.error(f"Error calculating counts for subcategory {subcat} in category {category}: {str(e)}", exc_info=True)
                current_app.logger.error(f"Error calculating counts for subcategory {subcat} in category {category}: {str(e)}", exc_info=True)
                continue  # Skip this subcategory and continue with others

        # Sort subcategory data if needed
        if sort == 'total_items_asc':
            subcategory_data.sort(key=lambda x: x['total_items'])
        elif sort == 'total_items_desc':
            subcategory_data.sort(key=lambda x: x['total_items'], reverse=True)

        session.close()
        logger.info(f"Returning {len(subcategory_data)} subcategories for category {category}")
        current_app.logger.info(f"Returning {len(subcategory_data)} subcategories for category {category}")
        return jsonify({
            'subcategories': subcategory_data,
            'total_subcats': total_subcats,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        logger.error(f"Error fetching subcategory data for category {category}: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error fetching subcategory data for category {category}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch subcategory data', 'details': str(e)}), 500

@tab5_bp.route('/tab/5/common_names')
def tab5_common_names():
    category = unquote(request.args.get('category'))
    subcategory = unquote(request.args.get('subcategory'))
    page = int(request.args.get('page', 1))
    per_page = 10
    filter_query = request.args.get('filter', '').lower()
    sort = request.args.get('sort', '')

    if not category or not subcategory:
        logger.error("Category and subcategory are required in common_names request")
        current_app.logger.error("Category and subcategory are required in common_names request")
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

        mappings_dict = {str(m.rental_class_id): {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[str(um.rental_class_id)] = {'category': um.category, 'subcategory': um.subcategory}

        rental_class_ids = list(mappings_dict.keys())

        # Group items by common name
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
                func.trim(func.cast(func.replace(ItemMaster.rental_class_num, '\x00', ''), db.String)).in_(rental_class_ids),
                ItemMaster.common_name == name,
                ItemMaster.status.in_(['On Rent', 'Delivered']),
                func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['resale', 'sold', 'pack', 'burst'])
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
            items_in_service = items_in_service_query.scalar()

            # Items available (status = 'Ready to Rent')
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
        logger.error(f"Error fetching common names for category {category}, subcategory {subcategory}: {str(e)}")
        current_app.logger.error(f"Error fetching common names for category {category}, subcategory {subcategory}: {str(e)}")
        return jsonify({'error': 'Failed to fetch common names'}), 500

@tab5_bp.route('/tab/5/data')
def tab5_data():
    category = unquote(request.args.get('category'))
    subcategory = unquote(request.args.get('subcategory'))
    common_name = unquote(request.args.get('common_name'))
    page = int(request.args.get('page', 1))
    per_page = 10
    filter_query = request.args.get('filter', '').lower()
    sort = request.args.get('sort', '')

    if not category or not subcategory or not common_name:
        logger.error("Category, subcategory, and common name are required in data request")
        current_app.logger.error("Category, subcategory, and common name are required in data request")
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

        mappings_dict = {str(m.rental_class_id): {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[str(um.rental_class_id)] = {'category': um.category, 'subcategory': um.subcategory}

        rental_class_ids = list(mappings_dict.keys())

        # Fetch items
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
        logger.error(f"Error fetching items for category {category}, subcategory {subcategory}, common_name {common_name}: {str(e)}")
        current_app.logger.error(f"Error fetching items for category {category}, subcategory {subcategory}, common_name {common_name}: {str(e)}")
        return jsonify({'error': 'Failed to fetch items'}), 500

@tab5_bp.route('/tab/5/update_bin_location', methods=['POST'])
def update_bin_location():
    # Note: This endpoint is Tab 5 specific
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
        item.bin_location = new_bin_location
        session.commit()

        # Update external API
        api_client = APIClient()
        api_client.update_bin_location(tag_id, new_bin_location)

        session.close()
        logger.info(f"Updated bin_location for tag_id {tag_id} to {new_bin_location}")
        current_app.logger.info(f"Updated bin_location for tag_id {tag_id} to {new_bin_location}")
        return jsonify({'message': 'Bin location updated successfully'})
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating bin location for tag {tag_id}: {str(e)}")
        current_app.logger.error(f"Error updating bin location for tag {tag_id}: {str(e)}")
        session.close()
        return jsonify({'error': str(e)}), 500

@tab5_bp.route('/tab/5/update_status', methods=['POST'])
def update_status():
    # Note: This endpoint is Tab 5 specific
    try:
        data = request.get_json()
        tag_id = data.get('tag_id')
        new_status = data.get('status')

        if not tag_id or not new_status:
            return jsonify({'error': 'Tag ID and status are required'}), 400

        # Allow updating from 'On Rent' or 'Delivered' to 'Ready to Rent' only
        if new_status != 'Ready to Rent':
            return jsonify({'error': 'Status can only be updated to "Ready to Rent"'}), 400

        session = db.session()
        item = session.query(ItemMaster).filter_by(tag_id=tag_id).first()
        if not item:
            session.close()
            return jsonify({'error': 'Item not found'}), 404

        # Check current status
        if item.status not in ['On Rent', 'Delivered']:
            session.close()
            return jsonify({'error': 'Status can only be updated from "On Rent" or "Delivered"'}), 400

        # Update local database
        item.status = new_status
        session.commit()

        # Update external API (assuming APIClient has a method for status updates)
        api_client = APIClient()
        api_client.update_status(tag_id, new_status)

        session.close()
        logger.info(f"Updated status for tag_id {tag_id} to {new_status}")
        current_app.logger.info(f"Updated status for tag_id {tag_id} to {new_status}")
        return jsonify({'message': 'Status updated successfully'})
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating status for tag {tag_id}: {str(e)}")
        current_app.logger.error(f"Error updating status for tag {tag_id}: {str(e)}")
        session.close()
        return jsonify({'error': str(e)}), 500

@tab5_bp.route('/tab/5/export_sold_burst_csv')
def export_sold_burst_csv():
    # Note: This endpoint is Tab 5 specific
    try:
        session = db.session()

        # Fetch all items with bin_location in ['sold', 'burst']
        items = session.query(ItemMaster).filter(
            func.lower(func.trim(func.replace(func.coalesce(ItemMaster.bin_location, ''), '\x00', ''))).in_(['sold', 'burst'])
        ).all()

        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        
        # Write CSV headers
        headers = ['Tag ID', 'Common Name', 'Bin Location', 'Status', 'Last Scanned Date', 'Quality', 'Notes']
        writer.writerow(headers)

        # Write CSV rows
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

        # Prepare response
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=sold_burst_items.csv'}
        )
    except Exception as e:
        logger.error(f"Error exporting sold/burst items to CSV: {str(e)}")
        current_app.logger.error(f"Error exporting sold/burst items to CSV: {str(e)}")
        return jsonify({'error': 'Failed to export CSV'}), 500

@tab5_bp.route('/tab/5/full_items_by_rental_class')
def full_items_by_rental_class():
    category = unquote(request.args.get('category'))
    subcategory = unquote(request.args.get('subcategory'))
    common_name = unquote(request.args.get('common_name'))

    if not category or not subcategory or not common_name:
        logger.error("Category, subcategory, and common name are required in full_items_by_rental_class request")
        current_app.logger.error("Category, subcategory, and common name are required in full_items_by_rental_class request")
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

        mappings_dict = {str(m.rental_class_id): {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[str(um.rental_class_id)] = {'category': um.category, 'subcategory': um.subcategory}

        rental_class_ids = list(mappings_dict.keys())

        # Fetch all items with the same rental_class_num and common_name
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
        current_app.logger.error(f"Error fetching full items for category {category}, subcategory {subcategory}, common_name {common_name}: {str(e)}")
        return jsonify({'error': 'Failed to fetch full items'}), 500