from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db, cache
from ..models.db_models import ItemMaster, RentalClassMapping
from sqlalchemy import func, distinct
from time import time

tabs_bp = Blueprint('tabs', __name__)

@tabs_bp.route('/tab/<int:tab_num>')
@cache.cached(timeout=30)
def tab_view(tab_num):
    try:
        current_app.logger.info(f"Loading tab {tab_num}")

        categories_data = db.session.query(
            RentalClassMapping.category,
            func.count(ItemMaster.tag_id).label('total_items'),
            func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['on rent', 'delivered']), db.Integer)), 0).label('on_contracts'),
            func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['repair']), db.Integer)), 0).label('in_service')
        ).outerjoin(
            ItemMaster, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
        ).group_by(
            RentalClassMapping.category
        ).order_by(
            RentalClassMapping.category
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
            'tab.html',
            tab_num=tab_num,
            categories=categories,
            bin_locations=bin_locations,
            statuses=statuses,
            cache_bust=int(time()),
            timestamp=lambda: int(time())
        )
    except Exception as e:
        current_app.logger.error(f"Error loading tab {tab_num}: {str(e)}")
        return jsonify({'error': 'Failed to load tab data'}), 500

@tabs_bp.route('/tab/<int:tab_num>/categories')
def tab_categories(tab_num):
    try:
        categories_data = db.session.query(
            RentalClassMapping.category,
            func.count(ItemMaster.tag_id).label('total_items'),
            func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['on rent', 'delivered']), db.Integer)), 0).label('on_contracts'),
            func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['repair']), db.Integer)), 0).label('in_service')
        ).outerjoin(
            ItemMaster, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
        ).group_by(
            RentalClassMapping.category
        ).order_by(
            RentalClassMapping.category
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
            cat_id = category['name'].lower().replace('[^a-z0-9-]', '_')
            html += f'''
                <tr>
                    <td>{category['name']}</td>
                    <td>{category['total_items']}</td>
                    <td>{category['on_contracts']}</td>
                    <td>{category['in_service']}</td>
                    <td>{category['available']}</td>
                    <td>
                        <button class="btn btn-sm btn-secondary" hx-get="/tab/{tab_num}/subcat_data?category={category['name']}" hx-target="#subcat-{cat_id}" hx-swap="innerHTML" onclick="showLoading('{cat_id}')">Expand</button>
                        <button class="btn btn-sm btn-info" onclick="printTable('Category', 'category-table')">Print</button>
                    </td>
                </tr>
            '''
        return html
    except Exception as e:
        current_app.logger.error(f"Error fetching categories for tab {tab_num}: {str(e)}")
        return '<tr><td colspan="6">Error loading categories</td></tr>'

@tabs_bp.route('/tab/<int:tab_num>/subcat_data')
def subcat_data(tab_num):
    try:
        category = request.args.get('category')
        if not category:
            return jsonify({'error': 'Category parameter is required'}), 400

        subcategories = db.session.query(
            RentalClassMapping.subcategory,
            func.count(ItemMaster.tag_id).label('total_items'),
            func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['on rent', 'delivered']), db.Integer)), 0).label('on_contracts'),
            func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['repair']), db.Integer)), 0).label('in_service')
        ).outerjoin(
            ItemMaster, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
        ).filter(
            RentalClassMapping.category == category
        ).group_by(
            RentalClassMapping.subcategory
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
        current_app.logger.error(f"Error fetching subcategories for category {category}: {str(e)}")
        return jsonify({'error': 'Failed to fetch subcategory data'}), 500

@tabs_bp.route('/tab/<int:tab_num>/common_names')
def common_names(tab_num):
    try:
        category = request.args.get('category')
        subcategory = request.args.get('subcategory')
        if not category or not subcategory:
            return jsonify({'error': 'Category and subcategory parameters are required'}), 400

        common_names = db.session.query(
            ItemMaster.common_name,
            func.count(ItemMaster.tag_id).label('total_items'),
            func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['on rent', 'delivered']), db.Integer)), 0).label('on_contracts'),
            func.coalesce(func.sum(func.cast(func.lower(ItemMaster.status).in_(['repair']), db.Integer)), 0).label('in_service')
        ).join(
            RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
        ).filter(
            RentalClassMapping.category == category,
            RentalClassMapping.subcategory == subcategory
        ).group_by(
            ItemMaster.common_name
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
        current_app.logger.error(f"Error fetching common names for category {category}, subcategory {subcategory}: {str(e)}")
        return jsonify({'error': 'Failed to fetch common names'}), 500

@tabs_bp.route('/tab/<int:tab_num>/data')
def tab_data(tab_num):
    try:
        category = request.args.get('category')
        subcategory = request.args.get('subcategory')
        common_name = request.args.get('common_name')
        if not category or not subcategory or not common_name:
            return jsonify({'error': 'Category, subcategory, and common_name parameters are required'}), 400

        items = db.session.query(
            ItemMaster
        ).join(
            RentalClassMapping, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
        ).filter(
            RentalClassMapping.category == category,
            RentalClassMapping.subcategory == subcategory,
            ItemMaster.common_name == common_name
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
        current_app.logger.error(f"Error fetching data for category {category}, subcategory {subcategory}, common_name {common_name}: {str(e)}")
        return jsonify({'error': 'Failed to fetch data'}), 500