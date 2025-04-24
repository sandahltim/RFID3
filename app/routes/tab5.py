from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db, cache
from ..models.db_models import ItemMaster, Transaction, RentalClassMapping, UserRentalClassMapping
from ..services.api_client import APIClient
from sqlalchemy import func, desc, or_
from time import time

tab5_bp = Blueprint('tab5', __name__)

@tab5_bp.route('/tab/5')
def tab5_view():
    try:
        # Check if data is in cache
        cache_key = 'tab5_view_data'
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            current_app.logger.info("Serving Tab 5 data from cache")
            return render_template('tab5.html', categories=cached_data, cache_bust=int(time()))

        session = db.session()
        current_app.logger.info("Starting new session for tab5")

        # Fetch all rental class mappings from both tables
        base_mappings = session.query(RentalClassMapping).all()
        user_mappings = session.query(UserRentalClassMapping).all()

        # Merge mappings, prioritizing user mappings
        mappings_dict = {m.rental_class_id: {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[um.rental_class_id] = {'category': um.category, 'subcategory': um.subcategory}

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

        # Calculate counts for each category, filtering for resale/pack items
        category_data = []
        for cat, mappings in categories.items():
            rental_class_ids = [m['rental_class_id'] for m in mappings]

            # Total items in this category with bin_location in ['resale', 'sold', 'pack', 'burst']
            total_items = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
                ItemMaster.bin_location.in_(['resale', 'sold', 'pack', 'burst'])
            ).scalar()

            # Only include categories with resale/pack items
            if total_items == 0:
                continue

            # Items on contracts (status = 'On Rent' or 'Delivered')
            items_on_contracts = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
                ItemMaster.status.in_(['On Rent', 'Delivered']),
                ItemMaster.bin_location.in_(['resale', 'sold', 'pack', 'burst'])
            ).scalar()

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

            items_in_service = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
                ItemMaster.bin_location.in_(['resale', 'sold', 'pack', 'burst']),
                or_(
                    ItemMaster.status.notin_(['Ready to Rent', 'On Rent', 'Delivered']),
                    ItemMaster.tag_id.in_(
                        session.query(subquery.c.tag_id).filter(
                            subquery.c.scan_date == session.query(func.max(Transaction.scan_date)).filter(Transaction.tag_id == subquery.c.tag_id).correlate(subquery).scalar_subquery(),
                            subquery.c.service_required == True
                        )
                    )
                )
            ).scalar()

            # Items available (status = 'Ready to Rent')
            items_available = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
                ItemMaster.status == 'Ready to Rent',
                ItemMaster.bin_location.in_(['resale', 'sold', 'pack', 'burst'])
            ).scalar()

            category_data.append({
                'category': cat,
                'cat_id': cat.lower().replace(' ', '_').replace('/', '_'),
                'total_items': total_items or 0,
                'items_on_contracts': items_on_contracts or 0,
                'items_in_service': items_in_service or 0,
                'items_available': items_available or 0
            })

        category_data.sort(key=lambda x: x['category'])
        current_app.logger.info(f"Fetched {len(category_data)} categories for tab5")

        # Cache the data
        cache.set(cache_key, category_data, timeout=60)
        current_app.logger.info("Cached Tab 5 data")

        session.close()
        return render_template('tab5.html', categories=category_data, cache_bust=int(time()))
    except Exception as e:
        current_app.logger.error(f"Error rendering Tab 5: {str(e)}", exc_info=True)
        return render_template('tab5.html', categories=[], cache_bust=int(time()))

@tab5_bp.route('/tab/5/subcat_data')
def tab5_subcat_data():
    category = request.args.get('category')
    page = int(request.args.get('page', 1))
    per_page = 10

    if not category:
        return jsonify({'error': 'Category is required'}), 400

    try:
        session = db.session()

        # Fetch mappings for this category
        base_mappings = session.query(RentalClassMapping).filter_by(category=category).all()
        user_mappings = session.query(UserRentalClassMapping).filter_by(category=category).all()

        mappings_dict = {m.rental_class_id: {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[um.rental_class_id] = {'category': um.category, 'subcategory': um.subcategory}

        # Group by subcategory
        subcategories = {}
        for rental_class_id, data in mappings_dict.items():
            subcategory = data['subcategory']
            if subcategory not in subcategories:
                subcategories[subcategory] = []
            subcategories[subcategory].append(rental_class_id)

        # Paginate subcategories
        subcat_list = sorted(subcategories.keys())
        total_subcats = len(subcat_list)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_subcats = subcat_list[start:end]

        subcategory_data = []
        for subcat in paginated_subcats:
            rental_class_ids = subcategories[subcat]

            # Total items in this subcategory
            total_items = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
                ItemMaster.bin_location.in_(['resale', 'sold', 'pack', 'burst'])
            ).scalar()

            # Only include subcategories with resale/pack items
            if total_items == 0:
                continue

            # Items on contracts (status = 'On Rent' or 'Delivered')
            items_on_contracts = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
                ItemMaster.status.in_(['On Rent', 'Delivered']),
                ItemMaster.bin_location.in_(['resale', 'sold', 'pack', 'burst'])
            ).scalar()

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

            items_in_service = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
                ItemMaster.bin_location.in_(['resale', 'sold', 'pack', 'burst']),
                or_(
                    ItemMaster.status.notin_(['Ready to Rent', 'On Rent', 'Delivered']),
                    ItemMaster.tag_id.in_(
                        session.query(subquery.c.tag_id).filter(
                            subquery.c.scan_date == session.query(func.max(Transaction.scan_date)).filter(Transaction.tag_id == subquery.c.tag_id).correlate(subquery).scalar_subquery(),
                            subquery.c.service_required == True
                        )
                    )
                )
            ).scalar()

            # Items available (status = 'Ready to Rent')
            items_available = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
                ItemMaster.status == 'Ready to Rent',
                ItemMaster.bin_location.in_(['resale', 'sold', 'pack', 'burst'])
            ).scalar()

            subcategory_data.append({
                'subcategory': subcat,
                'total_items': total_items or 0,
                'on_contracts': items_on_contracts or 0,
                'in_service': items_in_service or 0,
                'available': items_available or 0
            })

        session.close()
        return jsonify({
            'subcategories': subcategory_data,
            'total_subcats': total_subcats,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching subcategory data for category {category}: {str(e)}")
        return jsonify({'error': 'Failed to fetch subcategory data'}), 500

@tab5_bp.route('/tab/5/common_names')
def tab5_common_names():
    category = request.args.get('category')
    subcategory = request.args.get('subcategory')
    page = int(request.args.get('page', 1))
    per_page = 10

    if not category or not subcategory:
        return jsonify({'error': 'Category and subcategory are required'}), 400

    try:
        session = db.session()

        # Fetch rental class IDs for this category and subcategory
        base_mappings = session.query(RentalClassMapping).filter_by(category=category, subcategory=subcategory).all()
        user_mappings = session.query(UserRentalClassMapping).filter_by(category=category, subcategory=subcategory).all()

        mappings_dict = {m.rental_class_id: {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[um.rental_class_id] = {'category': um.category, 'subcategory': um.subcategory}

        rental_class_ids = list(mappings_dict.keys())

        # Group items by common name
        common_names_query = session.query(
            ItemMaster.common_name,
            func.count(ItemMaster.tag_id).label('total_items')
        ).filter(
            func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
            ItemMaster.bin_location.in_(['resale', 'sold', 'pack', 'burst'])
        ).group_by(
            ItemMaster.common_name
        ).all()

        common_names = []
        for name, total in common_names_query:
            if not name:  # Skip items with no common name
                continue

            # Items on contracts (status = 'On Rent' or 'Delivered')
            items_on_contracts = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
                ItemMaster.common_name == name,
                ItemMaster.status.in_(['On Rent', 'Delivered']),
                ItemMaster.bin_location.in_(['resale', 'sold', 'pack', 'burst'])
            ).scalar()

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

            items_in_service = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
                ItemMaster.common_name == name,
                ItemMaster.bin_location.in_(['resale', 'sold', 'pack', 'burst']),
                or_(
                    ItemMaster.status.notin_(['Ready to Rent', 'On Rent', 'Delivered']),
                    ItemMaster.tag_id.in_(
                        session.query(subquery.c.tag_id).filter(
                            subquery.c.scan_date == session.query(func.max(Transaction.scan_date)).filter(Transaction.tag_id == subquery.c.tag_id).correlate(subquery).scalar_subquery(),
                            subquery.c.service_required == True
                        )
                    )
                )
            ).scalar()

            # Items available (status = 'Ready to Rent')
            items_available = session.query(func.count(ItemMaster.tag_id)).filter(
                func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
                ItemMaster.common_name == name,
                ItemMaster.status == 'Ready to Rent',
                ItemMaster.bin_location.in_(['resale', 'sold', 'pack', 'burst'])
            ).scalar()

            common_names.append({
                'name': name,
                'total_items': total or 0,
                'items_on_contracts': items_on_contracts or 0,
                'in_service': items_in_service or 0,
                'available': items_available or 0
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

@tab5_bp.route('/tab/5/data')
def tab5_data():
    category = request.args.get('category')
    subcategory = request.args.get('subcategory')
    common_name = request.args.get('common_name')
    page = int(request.args.get('page', 1))
    per_page = 10

    if not category or not subcategory or not common_name:
        return jsonify({'error': 'Category, subcategory, and common name are required'}), 400

    try:
        session = db.session()

        # Fetch rental class IDs for this category and subcategory
        base_mappings = session.query(RentalClassMapping).filter_by(category=category, subcategory=subcategory).all()
        user_mappings = session.query(UserRentalClassMapping).filter_by(category=category, subcategory=subcategory).all()

        mappings_dict = {m.rental_class_id: {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[um.rental_class_id] = {'category': um.category, 'subcategory': um.subcategory}

        rental_class_ids = list(mappings_dict.keys())

        # Fetch items
        query = session.query(ItemMaster).filter(
            func.trim(func.upper(func.cast(ItemMaster.rental_class_num, db.String))).in_(rental_class_ids),
            ItemMaster.common_name == common_name,
            ItemMaster.bin_location.in_(['resale', 'sold', 'pack', 'burst'])
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
        item.bin_location = new_bin_location
        session.commit()

        # Update external API
        api_client = APIClient()
        api_client.update_bin_location(tag_id, new_bin_location)

        session.close()
        current_app.logger.info(f"Updated bin_location for tag_id {tag_id} to {new_bin_location}")
        return jsonify({'message': 'Bin location updated successfully'})
    except Exception as e:
        session.rollback()
        current_app.logger.error(f"Error updating bin location for tag {tag_id}: {str(e)}")
        session.close()
        return jsonify({'error': str(e)}), 500