from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db
from ..models.db_models import ItemMaster, Transaction, RentalClassMapping, UserRentalClassMapping
from ..services.api_client import APIClient
from sqlalchemy import func, desc, asc, or_
from datetime import datetime
import logging
import sys

# Configure logging
logger = logging.getLogger('tab3')
logger.setLevel(logging.INFO)

# Remove existing handlers to avoid duplicates
logger.handlers = []

# File handler for rfid_dashboard.log
file_handler = logging.FileHandler('/home/tim/test_rfidpi/logs/rfid_dashboard.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

tab3_bp = Blueprint('tab3', __name__)

# Version marker
logger.info("Deployed tab3.py version: 2025-05-06-v7")

@tab3_bp.route('/tab/3')
def tab3_view():
    try:
        session = db.session()
        logger.info("Starting new session for tab3")
        current_app.logger.info("Starting new session for tab3")

        # Query parameters for filtering and sorting
        common_name_filter = request.args.get('common_name', '').lower()
        date_filter = request.args.get('date_last_scanned', '')
        sort = request.args.get('sort', 'date_last_scanned_desc')  # Default sort

        # Fetch all rental class mappings
        base_mappings = session.query(RentalClassMapping).all()
        user_mappings = session.query(UserRentalClassMapping).all()

        mappings_dict = {m.rental_class_id: {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[um.rental_class_id] = {'category': um.category, 'subcategory': um.subcategory}
        logger.info(f"Fetched {len(mappings_dict)} rental class mappings: {list(mappings_dict.keys())}")

        # Query items with service-related statuses, case-insensitive
        items_query = session.query(ItemMaster).filter(
            func.lower(func.trim(func.replace(func.coalesce(ItemMaster.status, ''), '\x00', ''))).in_(
                ['repair', 'needs to be inspected', 'staged', 'wash', 'wet']
            ),
            func.lower(func.trim(func.replace(func.coalesce(ItemMaster.status, ''), '\x00', ''))) != 'sold'
        )

        # Apply filters
        if common_name_filter:
            items_query = items_query.filter(
                func.lower(ItemMaster.common_name).like(f'%{common_name_filter}%')
            )
        if date_filter:
            try:
                date = datetime.strptime(date_filter, '%Y-%m-%d')
                items_query = items_query.filter(
                    func.date(ItemMaster.date_last_scanned) == date
                )
            except ValueError:
                logger.warning(f"Invalid date format for date_last_scanned filter: {date_filter}")

        # Apply sorting
        if sort == 'date_last_scanned_asc':
            items_query = items_query.order_by(
                asc(ItemMaster.date_last_scanned), asc(func.lower(ItemMaster.common_name))
            )
        elif sort == 'date_last_scanned_desc':
            items_query = items_query.order_by(
                desc(ItemMaster.date_last_scanned), asc(func.lower(ItemMaster.common_name))
            )
        else:
            # Default sorting
            items_query = items_query.order_by(
                desc(ItemMaster.date_last_scanned), asc(func.lower(ItemMaster.common_name))
            )

        items_in_service = items_query.all()
        logger.info(f"Query fetched {len(items_in_service)} items: {[item.tag_id + ': ' + item.status + ', rental_class_num=' + (item.rental_class_num or 'None') for item in items_in_service]}")

        # Fetch repair details for items with transactions
        tag_ids = [item.tag_id for item in items_in_service]
        transaction_data = {}
        if tag_ids:
            max_scan_date_subquery = session.query(
                Transaction.tag_id,
                func.max(Transaction.scan_date).label('max_scan_date')
            ).filter(
                Transaction.tag_id.in_(tag_ids)
            ).group_by(
                Transaction.tag_id
            ).subquery()

            transactions = session.query(
                Transaction.tag_id,
                Transaction.location_of_repair,
                Transaction.dirty_or_mud,
                Transaction.leaves,
                Transaction.oil,
                Transaction.mold,
                Transaction.stain,
                Transaction.oxidation,
                Transaction.rip_or_tear,
                Transaction.sewing_repair_needed,
                Transaction.grommet,
                Transaction.rope,
                Transaction.buckle,
                Transaction.wet,
                Transaction.other
            ).join(
                max_scan_date_subquery,
                (Transaction.tag_id == max_scan_date_subquery.c.tag_id) &
                (Transaction.scan_date == max_scan_date_subquery.c.max_scan_date)
            ).all()

            for t in transactions:
                repair_types = []
                if t.dirty_or_mud: repair_types.append("Dirty/Mud")
                if t.leaves: repair_types.append("Leaves")
                if t.oil: repair_types.append("Oil")
                if t.mold: repair_types.append("Mold")
                if t.stain: repair_types.append("Stain")
                if t.oxidation: repair_types.append("Oxidation")
                if t.rip_or_tear: repair_types.append("Rip/Tear")
                if t.sewing_repair_needed: repair_types.append("Sewing Repair Needed")
                if t.grommet: repair_types.append("Grommet")
                if t.rope: repair_types.append("Rope")
                if t.buckle: repair_types.append("Buckle")
                if t.wet: repair_types.append("Wet")
                if t.other: repair_types.append(f"Other: {t.other}")

                transaction_data[t.tag_id] = {
                    'location_of_repair': t.location_of_repair or 'N/A',
                    'repair_types': repair_types if repair_types else ['None']
                }

        # Group items by category
        crew_items = {}
        for item in items_in_service:
            rental_class_num = str(item.rental_class_num).strip().upper() if item.rental_class_num else None
            category = mappings_dict.get(rental_class_num, {}).get('category', 'Miscellaneous')

            if category not in crew_items:
                crew_items[category] = []

            t_data = transaction_data.get(item.tag_id, {'location_of_repair': 'N/A', 'repair_types': ['None']})

            crew_items[category].append({
                'tag_id': item.tag_id,
                'common_name': item.common_name,
                'status': item.status,
                'bin_location': item.bin_location or 'N/A',
                'last_contract_num': item.last_contract_num or 'N/A',
                'date_last_scanned': item.date_last_scanned.isoformat() if item.date_last_scanned else 'N/A',
                'location_of_repair': t_data['location_of_repair'],
                'repair_types': t_data['repair_types']
            })

        # Convert to list of crews for template
        crews = [
            {'name': category, 'items': items}
            for category, items in sorted(crew_items.items(), key=lambda x: x[0].lower())
        ]

        logger.info(f"Fetched {sum(len(c['items']) for c in crews)} total items across {len(crews)} crews")
        current_app.logger.info(f"Fetched {sum(len(c['items']) for c in crews)} total items across {len(crews)} crews")
        session.close()
        return render_template(
            'tab3.html',
            crews=crews,
            common_name_filter=common_name_filter,
            date_filter=date_filter,
            sort=sort,
            cache_bust=int(datetime.now().timestamp())
        )
    except Exception as e:
        logger.error(f"Error rendering Tab 3: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error rendering Tab 3: {str(e)}", exc_info=True)
        if 'session' in locals():
            session.close()
        return render_template(
            'tab3.html',
            crews=[],
            common_name_filter='',
            date_filter='',
            sort='date_last_scanned_desc',
            cache_bust=int(datetime.now().timestamp())
        )

@tab3_bp.route('/tab/3/update_status', methods=['POST'])
def update_status():
    try:
        data = request.get_json()
        tag_id = data.get('tag_id')
        new_status = data.get('status')

        if not tag_id or not new_status:
            return jsonify({'error': 'Tag ID and status are required'}), 400

        valid_statuses = ['Ready to Rent', 'Sold', 'Repair', 'Needs to be Inspected', 'Staged', 'Wash', 'Wet']
        if new_status not in valid_statuses:
            return jsonify({'error': f'Status must be one of {", ".join(valid_statuses)}'}), 400

        session = db.session()
        item = session.query(ItemMaster).filter_by(tag_id=tag_id).first()
        if not item:
            session.close()
            return jsonify({'error': 'Item not found'}), 404

        # Prevent updating to On Rent or Delivered manually
        if new_status in ['On Rent', 'Delivered']:
            session.close()
            return jsonify({'error': 'Status cannot be updated to "On Rent" or "Delivered" manually'}), 400

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