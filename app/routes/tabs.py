from flask import Blueprint, jsonify, request, current_app
from .. import db, cache
from ..db_models import ItemMaster, RentalClassMapping  # Updated import
from sqlalchemy import func

tabs_bp = Blueprint('tabs', __name__)

@tabs_bp.route('/tab/<int:tab_num>', methods=['GET'])
@cache.cached(timeout=30)
def tab_view(tab_num):
    try:
        current_app.logger.info(f"Loading tab {tab_num}")
        categories = db.session.query(RentalClassMapping.category).distinct().order_by(RentalClassMapping.category).all()
        categories = [cat[0] for cat in categories if cat[0]]
        current_app.logger.info(f"Fetched {len(categories)} categories")

        bin_locations = db.session.query(ItemMaster.bin_location).distinct().order_by(ItemMaster.bin_location).all()
        bin_locations = [loc[0] for loc in bin_locations if loc[0]]
        current_app.logger.info(f"Fetched {len(bin_locations)} bin locations")

        statuses = db.session.query(ItemMaster.status).distinct().order_by(ItemMaster.status).all()
        statuses = [status[0] for status in statuses if status[0]]

        return render_template('tab.html', tab_num=tab_num, categories=categories, statuses=statuses, bin_locations=bin_locations)
    except Exception as e:
        current_app.logger.error(f"Error loading tab {tab_num}: {str(e)}")
        return jsonify({'error': 'Failed to load tab'}), 500

@tabs_bp.route('/tab/<int:tab_num>/subcat_data', methods=['GET'])
# @cache.cached(timeout=30)  # Temporarily disabled caching
def subcat_data(tab_num):
    try:
        category = request.args.get('category')
        if not category:
            return jsonify({'error': 'Category is required'}), 400

        subcategory_counts = db.session.query(
            RentalClassMapping.subcategory,
            func.count(ItemMaster.tag_id).label('item_count')
        ).join(
            ItemMaster, RentalClassMapping.rental_class_id == ItemMaster.rental_class_num, isouter=True
        ).filter(
            RentalClassMapping.category.ilike(category)
        ).group_by(
            RentalClassMapping.subcategory
        ).order_by(
            func.count(ItemMaster.tag_id).desc(),
            RentalClassMapping.subcategory
        ).all()

        subcategories = [sub[0] for sub, _ in subcategory_counts if sub[0]]
        current_app.logger.info(f"Fetched {len(subcategories)} subcategories for category {category}")

        data = []
        for subcategory in subcategories:
            common_names = db.session.query(
                ItemMaster.common_name
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
            common_names = [cn[0] for cn in common_names if cn[0]]
            data.append({
                'subcategory': subcategory,
                'common_names': common_names
            })

        current_app.logger.debug(f"Subcategory data for category {category}: {data}")
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Error fetching subcategories for tab {tab_num}: {str(e)}")
        return jsonify({'error': 'Failed to fetch subcategories'}), 500

@tabs_bp.route('/tab/<int:tab_num>/data', methods=['GET'])
# @cache.cached(timeout=30)  # Temporarily disabled caching
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
            'last_contract_num': item.last_contract_num
        } for item in items]
        current_app.logger.debug(f"Returning item data: {data}")
        return jsonify(data)
    except Exception as e:
        current_app.logger.error(f"Error fetching tab {tab_num} data: {str(e)}")
        return jsonify({'error': 'Failed to fetch data'}), 500