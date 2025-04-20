from flask import Blueprint, jsonify, request, current_app, render_template
from .. import db, cache
from ..models.db_models import ItemMaster, RentalClassMapping
from sqlalchemy import func
from time import time  # Add this import

tabs_bp = Blueprint('tabs', __name__)

@tabs_bp.route('/tab/<int:tab_num>', methods=['GET'])
@cache.cached(timeout=30)
def tab_view(tab_num):
    try:
        current_app.logger.info(f"Loading tab {tab_num}")
        categories_data = db.session.query(
            RentalClassMapping.category,
            func.count(ItemMaster.tag_id).label('total_items'),
            func.coalesce(func.sum(func.cast(ItemMaster.status.in_(['On Rent', 'Delivered']), db.Integer)), 0).label('on_contracts'),
            func.coalesce(func.sum(func.cast(ItemMaster.status.in_(['Repair']), db.Integer)), 0).label('in_service')
        ).outerjoin(
            ItemMaster, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
        ).group_by(
            RentalClassMapping.category
        ).order_by(
            RentalClassMapping.category
        ).all()
        current_app.logger.debug(f"Raw category data: {categories_data}")
        categories = []
        for cat in categories_data:
            if cat[0]:
                total_items = cat[1] or 0
                on_contracts = cat[2] or 0
                in_service = cat[3] or 0
                available = total_items - on_contracts - in_service
                categories.append({
                    'name': cat[0],
                    'total_items': total_items,
                    'on_contracts': on_contracts,
                    'in_service': in_service,
                    'available': available
                })
        current_app.logger.info(f"Fetched {len(categories)} categories")

        bin_locations = db.session.query(ItemMaster.bin_location).distinct().order_by(ItemMaster.bin_location).all()
        bin_locations = [loc[0] for loc in bin_locations if loc[0]]
        current_app.logger.info(f"Fetched {len(bin_locations)} bin locations")

        statuses = db.session.query(ItemMaster.status).distinct().order_by(ItemMaster.status).all()
        statuses = [status[0] for status in statuses if status[0]]

        # Add cache_bust parameter
        cache_bust = int(time())

        return render_template('tab.html', tab_num=tab_num, categories=categories, statuses=statuses, bin_locations=bin_locations, cache_bust=cache_bust)
    except Exception as e:
        current_app.logger.error(f"Error loading tab {tab_num}: {str(e)}")
        return jsonify({'error': 'Failed to load tab'}), 500

@tabs_bp.route('/tab/<int:tab_num>/subcat_data', methods=['GET'])
def subcat_data(tab_num):
    try:
        category = request.args.get('category')
        if not category:
            return jsonify({'error': 'Category is required'}), 400

        subcategory_counts = db.session.query(
            RentalClassMapping.subcategory,
            func.count(ItemMaster.tag_id).label('total_items'),
            func.coalesce(func.sum(func.cast(ItemMaster.status.in_(['On Rent', 'Delivered']), db.Integer)), 0).label('on_contracts'),
            func.coalesce(func.sum(func.cast(ItemMaster.status.in_(['Repair']), db.Integer)), 0).label('in_service')
        ).outerjoin(
            ItemMaster, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num
        ).filter(
            RentalClassMapping.category.ilike(category)
        ).group_by(
            RentalClassMapping.subcategory
        ).order_by(
            func.count(ItemMaster.tag_id).desc(),
            RentalClassMapping.subcategory
        ).all()

        current_app.logger.debug(f"Raw subcategory counts for category {category}: {subcategory_counts}")
        data = []
        for sub, total_items, on_contracts, in_service in subcategory_counts:
            if sub:
                total_items = total_items or 0
                on_contracts = on_contracts or 0
                in_service = in_service or 0
                available = total_items - on_contracts - in_service
                data.append({
                    'subcategory': sub,
                    'total_items': total_items,
                    'on_contracts': on_contracts,
                    'in_service': in_service,
                    'available': available
                })

        current_app.logger.info(f"Fetched {len(data)} subcategories for category {category}")
        current_app.logger.debug(f"Subcategory data for category {category}: {data}")
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Error fetching subcategories for tab {tab_num}: {str(e)}")
        return jsonify({'error': 'Failed to fetch subcategories'}), 500

@tabs_bp.route('/tab/<int:tab_num>/common_names', methods=['GET'])
def common_names(tab_num):
    try:
        category = request.args.get('category')
        subcategory = request.args.get('subcategory')
        if not category or not subcategory:
            return jsonify({'error': 'Category and subcategory are required'}), 400

        common_names_data = db.session.query(
            ItemMaster.common_name,
            func.count(ItemMaster.tag_id).label('total_items'),
            func.coalesce(func.sum(func.cast(ItemMaster.status.in_(['On Rent', 'Delivered']), db.Integer)), 0).label('on_contracts'),
            func.coalesce(func.sum(func.cast(ItemMaster.status.in_(['Repair']), db.Integer)), 0).label('in_service')
        ).join(
            RentalClassMapping, ItemMaster.rental_class_num == RentalClassMapping.rental_class_id
        ).filter(
            RentalClassMapping.category.ilike(category),
            RentalClassMapping.subcategory.ilike(subcategory)
        ).group_by(
            ItemMaster.common_name
        ).order_by(
            ItemMaster.common_name
        ).all()

        current_app.logger.debug(f"Raw common names data for category {category}, subcategory {subcategory}: {common_names_data}")
        common_names = []
        for cn, total_items, on_contracts, in_service in common_names_data:
            if cn:
                total_items = total_items or 0
                on_contracts = on_contracts or 0
                in_service = in_service or 0
                available = total_items - on_contracts - in_service
                common_names.append({
                    'name': cn,
                    'total_items': total_items,
                    'on_contracts': on_contracts,
                    'in_service': in_service,
                    'available': available
                })

        current_app.logger.debug(f"Common names for category {category}, subcategory {subcategory}: {common_names}")
        return jsonify({'common_names': common_names})
    except Exception as e:
        current_app.logger.error(f"Error fetching common names for tab {tab_num}: {str(e)}")
        return jsonify({'error': 'Failed to fetch common names'}), 500

@tabs_bp.route('/tab/<int:tab_num>/data', methods=['GET'])
def tab_data(tab_num):
    try:
        category = request.args.get('category')
        subcategory = request.args.get('subcategory')
        common_name = request.args.get('common_name')

        current_app.logger.debug(f"Received request for tab {tab_num} data: category={category}, subcategory={subcategory}, common_name={common_name}")

        query = db.session.query(ItemMaster)
        if category and subcategory:
            query = query.join(
                RentalClassMapping, ItemMaster.rental_class_num == RentalClassMapping.rental_class_id
            ).filter(
                RentalClassMapping.category.ilike(category),
                RentalClassMapping.subcategory.ilike(subcategory)
            )
        if common_name:
            query = query.filter(ItemMaster.common_name.ilike(common_name))

        items = query.all()
        current_app.logger.info(f"Fetched {len(items)} items for category={category}, subcategory={subcategory}, common_name={common_name}")
        data = [{
            'tag_id': item.tag_id,
            'common_name': item.common_name,
            'bin_location': item.bin_location,
            'status': item.status,
            'last_contract_num': item.last_contract_num,
            'last_scanned_date': item.date_last_scanned.isoformat() if item.date_last_scanned else None,
            'quality': item.quality,
            'notes': item.notes
        } for item in items]
        current_app.logger.debug(f"Returning item data: {data}")
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Error fetching tab {tab_num} data: {str(e)}")
        return jsonify({'error': 'Failed to fetch data'}), 500