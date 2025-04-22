from flask import Blueprint, render_template, jsonify, current_app, request
from .. import db, cache
from ..models.db_models import ItemMaster, RentalClassMapping
from sqlalchemy import func, case
from urllib.parse import quote
import re
import time

tab1_bp = Blueprint('tab1', __name__)

@tab1_bp.route('/tab/1')
@cache.cached(timeout=30)
def tab1_view():
    try:
        current_app.logger.info("Loading tab 1")

        categories_data = db.session.query(
            func.coalesce(RentalClassMapping.category, 'Unclassified').label('category'),
            func.count(ItemMaster.tag_id).label('total_items'),
            func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['on rent', 'delivered']), db.Integer)), 0).label('on_contracts'),
            func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['repair']), db.Integer)), 0).label('in_service')
        ).outerjoin(
            RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
        ).group_by(
            func.coalesce(RentalClassMapping.category, 'Unclassified')
        ).order_by(
            func.coalesce(RentalClassMapping.category, 'Unclassified')
        ).all()

        categories = [
            {
                'name': category,
                'total_items': total_items,
                'on_contracts': on_contracts,
                'in_service': in_service,
                'available': max(total_items - on_contracts - in_service, 0)
            }
            for category, total_items, on_contracts, in_service in categories_data
        ]
        current_app.logger.info(f"Fetched {len(categories)} categories")
        current_app.logger.debug(f"Raw category data: {categories_data}")

        bin_locations = db.session.query(
            ItemMaster.bin_location
        ).filter(
            ItemMaster.bin_location.isnot(None)
        ).distinct().order_by(
            ItemMaster.bin_location
        ).all()
        bin_locations = [loc[0] for loc in bin_locations]
        current_app.logger.info(f"Fetched {len(bin_locations)} bin locations")

        statuses = db.session.query(
            ItemMaster.status
        ).filter(
            ItemMaster.status.isnot(None)
        ).distinct().order_by(
            ItemMaster.status
        ).all()
        statuses = [status[0] for status in statuses]

        return render_template(
            'tab1.html',
            tab_num=1,
            categories=categories,
            bin_locations=bin_locations,
            statuses=statuses,
            cache_bust=int(time.time()),
            timestamp=lambda: int(time.time())
        )
    except Exception as e:
        current_app.logger.error(f"Error loading tab 1: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to load tab data'}), 500

@tab1_bp.route('/tab/1/categories')
def tab1_categories():
    try:
        categories_data = db.session.query(
            func.coalesce(RentalClassMapping.category, 'Unclassified').label('category'),
            func.count(ItemMaster.tag_id).label('total_items'),
            func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['on rent', 'delivered']), db.Integer)), 0).label('on_contracts'),
            func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['repair']), db.Integer)), 0).label('in_service')
        ).outerjoin(
            RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
        ).group_by(
            func.coalesce(RentalClassMapping.category, 'Unclassified')
        ).order_by(
            func.coalesce(RentalClassMapping.category, 'Unclassified')
        ).all()

        categories = [
            {
                'name': category,
                'total_items': total_items,
                'on_contracts': on_contracts,
                'in_service': in_service,
                'available': max(total_items - on_contracts - in_service, 0)
            }
            for category, total_items, on_contracts, in_service in categories_data
        ]

        html = ''
        for category in categories:
            cat_id = re.sub(r'[^a-z0-9-]', '_', category['name'].lower())
            encoded_category = quote(category['name']).replace("'", "\\'").replace('"', '\\"')
            current_app.logger.debug(f"Encoded category for onclick: {encoded_category}")
            html += f'''
                <tr>
                    <td>{category['name']}</td>
                    <td>{category['total_items']}</td>
                    <td>{category['on_contracts']}</td>
                    <td>{category['in_service']}</td>
                    <td>{category['available']}</td>
                    <td>
                        <button class="btn btn-sm btn-secondary" onclick="expandCategory('{encoded_category}', 'subcat-{cat_id}')">Expand</button>
                        <button class="btn btn-sm btn-info print-btn" data-print-level="Category" data-print-id="category-table">Print</button>
                        <div id="loading-{cat_id}" style="display:none;" class="loading">Loading...</div>
                    </td>
                </tr>
                <tr>
                    <td colspan="6">
                        <div id="subcat-{cat_id}" class="expandable collapsed"></div>
                    </td>
                </tr>
            '''
        return html
    except Exception as e:
        current_app.logger.error(f"Error fetching categories for tab 1: {str(e)}", exc_info=True)
        return '<tr><td colspan="6">Error loading categories</td></tr>'

@tab1_bp.route('/tab/1/subcat_data')
def tab1_subcat_data():
    try:
        current_app.logger.info("Received request for /tab/1/subcat_data")
        category = request.args.get('category')
        if not category:
            current_app.logger.error("Category parameter is missing")
            return jsonify({'error': 'Category parameter is required'}), 400

        # Handle the default "Unclassified" category
        if category == 'Unclassified':
            subcategories = db.session.query(
                func.coalesce(RentalClassMapping.subcategory, 'Uncategorized').label('subcategory'),
                func.count(ItemMaster.tag_id).label('total_items'),
                func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['on rent', 'delivered']), db.Integer)), 0).label('on_contracts'),
                func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['repair']), db.Integer)), 0).label('in_service')
            ).outerjoin(
                RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
            ).filter(
                RentalClassMapping.category.is_(None)  # Items without a category mapping
            ).group_by(
                func.coalesce(RentalClassMapping.subcategory, 'Uncategorized')
            ).all()
        else:
            subcategories = db.session.query(
                func.coalesce(RentalClassMapping.subcategory, 'Uncategorized').label('subcategory'),
                func.count(ItemMaster.tag_id).label('total_items'),
                func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['on rent', 'delivered']), db.Integer)), 0).label('on_contracts'),
                func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['repair']), db.Integer)), 0).label('in_service')
            ).outerjoin(
                RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
            ).filter(
                RentalClassMapping.category == category
            ).group_by(
                func.coalesce(RentalClassMapping.subcategory, 'Uncategorized')
            ).all()

        current_app.logger.debug(f"Raw subcategory counts for category {category}: {subcategories}")

        subcat_data = [
            {
                'subcategory': subcategory,
                'total_items': total_items,
                'on_contracts': on_contracts,
                'in_service': in_service,
                'available': max(total_items - on_contracts - in_service, 0)
            }
            for subcategory, total_items, on_contracts, in_service in subcategories
        ]

        current_app.logger.info(f"Fetched {len(subcat_data)} subcategories for category {category}")
        current_app.logger.debug(f"Subcategory data for category {category}: {subcat_data}")

        return jsonify(subcat_data)
    except Exception as e:
        current_app.logger.error(f"Error fetching subcategories for category {category}: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to fetch subcategory data'}), 500

@tab1_bp.route('/tab/1/common_names')
def tab1_common_names():
    try:
        category = request.args.get('category')
        subcategory = request.args.get('subcategory')
        if not category or not subcategory:
            return jsonify({'error': 'Category and subcategory parameters are required'}), 400

        current_app.logger.debug(f"Fetching common names for category: {category}, subcategory: {subcategory}")

        # Handle the default "Unclassified" category and "Uncategorized" subcategory
        if category == 'Unclassified' and subcategory == 'Uncategorized':
            common_names = db.session.query(
                func.trim(func.upper(ItemMaster.common_name)).label('common_name'),
                func.count(ItemMaster.tag_id).label('total_items'),
                func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['on rent', 'delivered']), db.Integer)), 0).label('on_contracts'),
                func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['repair']), db.Integer)), 0).label('in_service')
            ).outerjoin(
                RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
            ).filter(
                RentalClassMapping.category.is_(None),
                RentalClassMapping.subcategory.is_(None)
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
                func.lower(RentalClassMapping.category) == func.lower(category),
                func.lower(RentalClassMapping.subcategory) == func.lower(subcategory)
            ).group_by(
                func.trim(func.upper(ItemMaster.common_name))
            ).all()

        current_app.logger.debug(f"Common names for category {category}, subcategory {subcategory}: {common_names}")

        common_names_data = [
            {
                'name': name,
                'total_items': total_items,
                'on_contracts': on_contracts,
                'in_service': in_service,
                'available': max(total_items - on_contracts - in_service, 0)
            }
            for name, total_items, on_contracts, in_service in common_names
            if name is not None
        ]

        current_app.logger.debug(f"Common names data: {common_names_data}")

        return jsonify({'common_names': common_names_data})
    except Exception as e:
        current_app.logger.error(f"Error fetching common names for category {category}, subcategory {subcategory}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to fetch common names: {str(e)}'}), 500

@tab1_bp.route('/tab/1/data')
def tab1_data():
    try:
        category = request.args.get('category')
        subcategory = request.args.get('subcategory')
        common_name = request.args.get('common_name')
        if not category or not subcategory or not common_name:
            return jsonify({'error': 'Category, subcategory, and common_name parameters are required'}), 400

        current_app.logger.debug(f"Fetching items for category {category}, subcategory {subcategory}, common_name {common_name}")

        # Handle the default "Unclassified" category and "Uncategorized" subcategory
        if category == 'Unclassified' and subcategory == 'Uncategorized':
            items = db.session.query(
                ItemMaster
            ).outerjoin(
                RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
            ).filter(
                RentalClassMapping.category.is_(None),
                RentalClassMapping.subcategory.is_(None),
                func.trim(func.upper(ItemMaster.common_name)) == func.trim(func.upper(common_name))
            ).all()
        else:
            items = db.session.query(
                ItemMaster
            ).join(
                RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
            ).filter(
                func.lower(RentalClassMapping.category) == func.lower(category),
                func.lower(RentalClassMapping.subcategory) == func.lower(subcategory),
                func.trim(func.upper(ItemMaster.common_name)) == func.trim(func.upper(common_name))
            ).all()

        current_app.logger.debug(f"Items for category {category}, subcategory {subcategory}, common_name {common_name}: {len(items)} items found")

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
        current_app.logger.error(f"Error fetching data for category {category}, subcategory {subcategory}, common_name {common_name}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to fetch data: {str(e)}'}), 500