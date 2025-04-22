from flask import Blueprint, render_template, jsonify, current_app, request
from .. import db, cache
from ..models.db_models import ItemMaster, RentalClassMapping
from sqlalchemy import func, case
from urllib.parse import quote
import re
import time
from datetime import datetime

# Blueprint for Tab 3 (Service) - DO NOT MODIFY BLUEPRINT NAME
tab3_bp = Blueprint('tab3', __name__)

@tab3_bp.route('/tab/3')
@cache.cached(timeout=30)
def tab3_view():
    # Route to render the main view for Tab 3
    # Displays items in 'in service' status
    try:
        current_app.logger.info("Loading tab 3 (Service)")

        # Fetch categories for items in 'in service' status
        categories = db.session.query(
            func.coalesce(RentalClassMapping.category, 'Unclassified').label('category'),
            func.count(ItemMaster.tag_id).label('total_items'),
            func.count(case(
                [(func.lower(ItemMaster.status).in_(['on rent', 'delivered']), ItemMaster.tag_id)], else_=None
            )).label('on_contracts'),
            func.count(case(
                [(func.lower(ItemMaster.status) == 'in service', ItemMaster.tag_id)], else_=None
            )).label('in_service'),
            func.count(case(
                [(func.lower(ItemMaster.status) == 'available', ItemMaster.tag_id)], else_=None
            )).label('available')
        ).outerjoin(
            RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
        ).group_by(
            func.coalesce(RentalClassMapping.category, 'Unclassified')
        ).order_by(
            func.coalesce(RentalClassMapping.category, 'Unclassified')
        ).all()

        # Format the category data for the template
        formatted_categories = []
        for cat, total, on_contracts, in_service, available in categories:
            cat_id = re.sub(r'[^a-z0-9-]', '_', cat.lower())
            formatted_categories.append({
                'name': cat,
                'cat_id': cat_id,
                'total_items': total,
                'on_contracts': on_contracts or 0,
                'in_service': in_service or 0,
                'available': available or 0
            })
        current_app.logger.info(f"Fetched {len(formatted_categories)} categories for Tab 3")
        current_app.logger.debug(f"Formatted categories for tab 3: {formatted_categories}")

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
            'tab3.html',
            tab_num=3,
            categories=formatted_categories,
            bin_locations=bin_locations,
            statuses=statuses,
            cache_bust=int(time.time()),
            timestamp=lambda: int(time.time())
        )
    except Exception as e:
        current_app.logger.error(f"Error loading tab 3: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to load tab data'}), 500

@tab3_bp.route('/tab/3/subcat_data')
def tab3_subcat_data():
    # Route to fetch subcategory data for a specific category
    try:
        current_app.logger.info("Received request for /tab/3/subcat_data")
        category = request.args.get('category')
        page = int(request.args.get('page', 1))
        per_page = 20
        offset = (page - 1) * per_page

        if not category:
            current_app.logger.error("Category parameter is missing")
            return jsonify({'error': 'Category parameter is required'}), 400

        # Fetch subcategories for items in 'in service' status
        base_query = db.session.query(
            func.coalesce(RentalClassMapping.subcategory, 'Unclassified').label('subcategory'),
            func.count(ItemMaster.tag_id).label('total_items'),
            func.count(case(
                [(func.lower(ItemMaster.status).in_(['on rent', 'delivered']), ItemMaster.tag_id)], else_=None
            )).label('on_contracts'),
            func.count(case(
                [(func.lower(ItemMaster.status) == 'in service', ItemMaster.tag_id)], else_=None
            )).label('in_service'),
            func.count(case(
                [(func.lower(ItemMaster.status) == 'available', ItemMaster.tag_id)], else_=None
            )).label('available')
        ).outerjoin(
            RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
        ).filter(
            func.lower(ItemMaster.status) == 'in service'
        )

        if category != 'Unclassified':
            base_query = base_query.filter(
                func.lower(RentalClassMapping.category) == func.lower(category)
            )
        else:
            base_query = base_query.filter(
                RentalClassMapping.category.is_(None)
            )

        base_query = base_query.group_by(
            func.coalesce(RentalClassMapping.subcategory, 'Unclassified')
        )

        total_subcats = base_query.count()
        subcategories = base_query.order_by(
            func.coalesce(RentalClassMapping.subcategory, 'Unclassified')
        ).offset(offset).limit(per_page).all()

        # If no subcategories are found, check if there are items for this category
        if not subcategories:
            # Check if there are any items in this category
            item_count = db.session.query(
                func.count(ItemMaster.tag_id)
            ).outerjoin(
                RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
            ).filter(
                func.lower(ItemMaster.status) == 'in service'
            )
            if category != 'Unclassified':
                item_count = item_count.filter(
                    func.lower(RentalClassMapping.category) == func.lower(category)
                )
            else:
                item_count = item_count.filter(
                    RentalClassMapping.category.is_(None)
                )
            item_count = item_count.scalar()

            if item_count > 0:
                # If there are items but no subcategories, treat it as a single "Unclassified" subcategory
                subcategories = [(
                    'Unclassified',
                    item_count,
                    db.session.query(
                        func.count(ItemMaster.tag_id)
                    ).outerjoin(
                        RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
                    ).filter(
                        func.lower(ItemMaster.status).in_(['on rent', 'delivered'])
                    ).filter(
                        func.lower(RentalClassMapping.category) == func.lower(category) if category != 'Unclassified' else RentalClassMapping.category.is_(None)
                    ).scalar() or 0,
                    db.session.query(
                        func.count(ItemMaster.tag_id)
                    ).outerjoin(
                        RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
                    ).filter(
                        func.lower(ItemMaster.status) == 'in service'
                    ).filter(
                        func.lower(RentalClassMapping.category) == func.lower(category) if category != 'Unclassified' else RentalClassMapping.category.is_(None)
                    ).scalar() or 0,
                    db.session.query(
                        func.count(ItemMaster.tag_id)
                    ).outerjoin(
                        RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
                    ).filter(
                        func.lower(ItemMaster.status) == 'available'
                    ).filter(
                        func.lower(RentalClassMapping.category) == func.lower(category) if category != 'Unclassified' else RentalClassMapping.category.is_(None)
                    ).scalar() or 0
                )]
                total_subcats = 1

        subcat_data = [
            {
                'subcategory': subcat,
                'total_items': total,
                'on_contracts': on_contracts or 0,
                'in_service': in_service or 0,
                'available': available or 0
            }
            for subcat, total, on_contracts, in_service, available in subcategories
        ]

        current_app.logger.info(f"Fetched {len(subcat_data)} subcategories for category {category}")
        current_app.logger.debug(f"Subcategory data for category {category}: {subcat_data}")

        return jsonify({
            'subcategories': subcat_data,
            'total_subcats': total_subcats,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching subcategories for category {category}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch subcategory data'}), 500

@tab3_bp.route('/tab/3/common_names')
def tab3_common_names():
    try:
        category = request.args.get('category')
        subcategory = request.args.get('subcategory')
        page = int(request.args.get('page', 1))
        per_page = 20
        offset = (page - 1) * per_page

        if not category or not subcategory:
            return jsonify({'error': 'Category and subcategory parameters are required'}), 400

        current_app.logger.debug(f"Fetching common names for category: {category}, subcategory: {subcategory}")

        # Fetch common names for items in 'in service' status
        if subcategory == 'Unclassified':
            base_query = db.session.query(
                func.trim(func.upper(ItemMaster.common_name)).label('common_name'),
                func.count(ItemMaster.tag_id).label('total_items'),
                func.count(case(
                    [(func.lower(ItemMaster.status).in_(['on rent', 'delivered']), ItemMaster.tag_id)], else_=None
                )).label('on_contracts'),
                func.count(case(
                    [(func.lower(ItemMaster.status) == 'in service', ItemMaster.tag_id)], else_=None
                )).label('in_service'),
                func.count(case(
                    [(func.lower(ItemMaster.status) == 'available', ItemMaster.tag_id)], else_=None
                )).label('available')
            ).outerjoin(
                RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
            ).filter(
                func.lower(ItemMaster.status) == 'in service',
                RentalClassMapping.subcategory.is_(None)
            )
            if category != 'Unclassified':
                base_query = base_query.filter(
                    func.lower(RentalClassMapping.category) == func.lower(category)
                )
            else:
                base_query = base_query.filter(
                    RentalClassMapping.category.is_(None)
                )
        else:
            base_query = db.session.query(
                func.trim(func.upper(ItemMaster.common_name)).label('common_name'),
                func.count(ItemMaster.tag_id).label('total_items'),
                func.count(case(
                    [(func.lower(ItemMaster.status).in_(['on rent', 'delivered']), ItemMaster.tag_id)], else_=None
                )).label('on_contracts'),
                func.count(case(
                    [(func.lower(ItemMaster.status) == 'in service', ItemMaster.tag_id)], else_=None
                )).label('in_service'),
                func.count(case(
                    [(func.lower(ItemMaster.status) == 'available', ItemMaster.tag_id)], else_=None
                )).label('available')
            ).join(
                RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
            ).filter(
                func.lower(ItemMaster.status) == 'in service',
                func.lower(RentalClassMapping.subcategory) == func.lower(subcategory)
            )
            if category != 'Unclassified':
                base_query = base_query.filter(
                    func.lower(RentalClassMapping.category) == func.lower(category)
                )

        base_query = base_query.group_by(
            func.trim(func.upper(ItemMaster.common_name))
        )

        total_common_names = base_query.count()
        common_names = base_query.order_by(
            func.trim(func.upper(ItemMaster.common_name))
        ).offset(offset).limit(per_page).all()

        common_names_data = [
            {
                'name': name,
                'total_items': total,
                'on_contracts': on_contracts or 0,
                'in_service': in_service or 0,
                'available': available or 0
            }
            for name, total, on_contracts, in_service, available in common_names
            if name is not None
        ]

        current_app.logger.debug(f"Common names for category {category}, subcategory: {subcategory}: {common_names_data}")

        return jsonify({
            'common_names': common_names_data,
            'total_common_names': total_common_names,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching common names for category {category}, subcategory: {subcategory}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to fetch common names: {str(e)}'}), 500

@tab3_bp.route('/tab/3/data')
def tab3_data():
    try:
        category = request.args.get('category')
        subcategory = request.args.get('subcategory')
        common_name = request.args.get('common_name')
        page = int(request.args.get('page', 1))
        per_page = 20
        offset = (page - 1) * per_page

        if not category or not subcategory or not common_name:
            return jsonify({'error': 'Category, subcategory, and common_name parameters are required'}), 400

        current_app.logger.debug(f"Fetching items for category {category}, subcategory {subcategory}, common_name {common_name}, page {page}")

        # Base query for items
        base_query = db.session.query(ItemMaster).outerjoin(
            RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
        ).filter(
            func.lower(ItemMaster.status) == 'in service',
            func.trim(func.upper(ItemMaster.common_name)) == func.trim(func.upper(common_name))
        )

        if category != 'Unclassified':
            base_query = base_query.filter(
                func.lower(RentalClassMapping.category) == func.lower(category)
            )
        else:
            base_query = base_query.filter(
                RentalClassMapping.category.is_(None)
            )

        if subcategory != 'Unclassified':
            base_query = base_query.filter(
                func.lower(RentalClassMapping.subcategory) == func.lower(subcategory)
            )
        else:
            base_query = base_query.filter(
                RentalClassMapping.subcategory.is_(None)
            )

        # Get total items for pagination
        total_items = base_query.count()

        # Apply pagination
        items = base_query.order_by(ItemMaster.tag_id).offset(offset).limit(per_page).all()

        current_app.logger.debug(f"Items for category {category}, subcategory {subcategory}, common_name {common_name}: {len(items)} items found (total {total_items})")

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

        return jsonify({
            'items': items_data,
            'total_items': total_items,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        current_app.logger.error(f"Error fetching data for category {category}, subcategory {subcategory}, common_name {common_name}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to fetch data: {str(e)}'}), 500