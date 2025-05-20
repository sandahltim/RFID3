from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db
from ..models.db_models import ItemMaster, Transaction, RentalClassMapping, UserRentalClassMapping, SeedRentalClass
from ..services.api_client import APIClient
from sqlalchemy import text, func, desc, asc
from datetime import datetime
import logging
import sys
import csv
import os
import pwd
import grp

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

# Directory for shared CSV files
SHARED_DIR = '/home/tim/test_rfidpi/shared'
CSV_FILE_PATH = os.path.join(SHARED_DIR, 'rfid_tags.csv')

# Ensure shared directory exists with correct permissions
if not os.path.exists(SHARED_DIR):
    print(f"DEBUG: Creating shared directory: {SHARED_DIR}")
    logger.info(f"Creating shared directory: {SHARED_DIR}")
    os.makedirs(SHARED_DIR, mode=0o770)
    os.chown(SHARED_DIR, pwd.getpwnam('tim').pw_uid, grp.getgrnam('tim').gr_gid)

# Version marker
logger.info("Deployed tab3.py version: 2025-05-20-v29")

@tab3_bp.route('/tab/3')
def tab3_view():
    session = None
    try:
        session = db.session()
        print("DEBUG: Starting new session for tab3")
        logger.info("Starting new session for tab3")
        current_app.logger.info("Starting new session for tab3")

        # Test database connection
        session.execute(text("SELECT 1"))
        print("DEBUG: Database connection test successful")
        logger.info("Database connection test successful")

        # Query parameters for filtering and sorting
        common_name_filter = request.args.get('common_name', '').lower()
        date_filter = request.args.get('date_last_scanned', '')
        sort = request.args.get('sort', 'date_last_scanned_desc')
        page = int(request.args.get('page', 1))
        per_page = 20

        # Fetch all rental class mappings
        base_mappings = session.query(RentalClassMapping).all()
        user_mappings = session.query(UserRentalClassMapping).all()

        mappings_dict = {str(m.rental_class_id).strip().upper(): {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[str(um.rental_class_id).strip().upper()] = {'category': um.category, 'subcategory': um.subcategory}
        print(f"DEBUG: Fetched {len(mappings_dict)} rental class mappings: {list(mappings_dict.keys())}")
        logger.info(f"Fetched {len(mappings_dict)} rental class mappings: {list(mappings_dict.keys())}")

        # Raw SQL query to fetch items with service-related statuses
        sql_query = """
            SELECT tag_id, common_name, status, bin_location, last_contract_num, date_last_scanned, rental_class_num
            FROM id_item_master
            WHERE LOWER(TRIM(REPLACE(COALESCE(status, ''), '\0', ''))) IN ('repair', 'needs to be inspected', 'staged', 'wash', 'wet')
            AND LOWER(TRIM(REPLACE(COALESCE(status, ''), '\0', ''))) != 'sold'
        """
        params = {}
        if common_name_filter:
            sql_query += " AND LOWER(common_name) LIKE :common_name_filter"
            params['common_name_filter'] = f'%{common_name_filter}%'
        if date_filter:
            try:
                date = datetime.strptime(date_filter, '%Y-%m-%d')
                sql_query += " AND DATE(date_last_scanned) = :date_filter"
                params['date_filter'] = date
            except ValueError:
                print(f"DEBUG: Invalid date format for date_last_scanned filter: {date_filter}")
                logger.warning(f"Invalid date format for date_last_scanned filter: {date_filter}")

        # Apply sorting
        if sort == 'date_last_scanned_asc':
            sql_query += " ORDER BY date_last_scanned ASC, LOWER(common_name) ASC"
        else:
            sql_query += " ORDER BY date_last_scanned DESC, LOWER(common_name) ASC"

        # Add pagination
        sql_query += " LIMIT :limit OFFSET :offset"
        params['limit'] = per_page
        params['offset'] = (page - 1) * per_page

        print(f"DEBUG: Executing raw SQL query: {sql_query} with params: {params}")
        logger.info(f"Executing raw SQL query: {sql_query} with params: {params}")
        result = session.execute(text(sql_query), params)
        rows = result.fetchall()
        print(f"DEBUG: Raw query returned {len(rows)} rows")
        logger.info(f"Raw query returned {len(rows)} rows")

        items_in_service = [
            {
                'tag_id': row[0],
                'common_name': row[1],
                'status': row[2],
                'bin_location': row[3] or 'N/A',
                'last_contract_num': row[4] or 'N/A',
                'date_last_scanned': row[5].isoformat() if row[5] else 'N/A',
                'rental_class_num': str(row[6]).strip().upper() if row[6] else None
            }
            for row in rows
        ]
        print(f"DEBUG: Processed {len(items_in_service)} items: {[item['tag_id'] + ': ' + item['status'] + ', rental_class_num=' + (item['rental_class_num'] or 'None') for item in items_in_service]}")
        logger.info(f"Processed {len(items_in_service)} items: {[item['tag_id'] + ': ' + item['status'] + ', rental_class_num=' + (item['rental_class_num'] or 'None') for item in items_in_service]}")

        # Fetch total count for pagination
        count_query = """
            SELECT COUNT(*) 
            FROM id_item_master
            WHERE LOWER(TRIM(REPLACE(COALESCE(status, ''), '\0', ''))) IN ('repair', 'needs to be inspected', 'staged', 'wash', 'wet')
            AND LOWER(TRIM(REPLACE(COALESCE(status, ''), '\0', ''))) != 'sold'
        """
        count_params = {}
        if common_name_filter:
            count_query += " AND LOWER(common_name) LIKE :common_name_filter"
            count_params['common_name_filter'] = f'%{common_name_filter}%'
        if date_filter:
            try:
                date = datetime.strptime(date_filter, '%Y-%m-%d')
                count_query += " AND DATE(date_last_scanned) = :date_filter"
                count_params['date_filter'] = date
            except ValueError:
                pass

        total_items = session.execute(text(count_query), count_params).scalar()

        # Fetch repair details for items with transactions
        tag_ids = [item['tag_id'] for item in items_in_service]
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
            rental_class_num = item['rental_class_num']
            category = mappings_dict.get(rental_class_num, {}).get('category', 'Miscellaneous')
            print(f"DEBUG: Item {item['tag_id']}: rental_class_num={rental_class_num}, mapped to category={category}")
            logger.info(f"Item {item['tag_id']}: rental_class_num={rental_class_num}, mapped to category={category}")

            if category not in crew_items:
                crew_items[category] = []

            t_data = transaction_data.get(item['tag_id'], {'location_of_repair': 'N/A', 'repair_types': ['None']})

            crew_items[category].append({
                'tag_id': item['tag_id'],
                'common_name': item['common_name'],
                'status': item['status'],
                'bin_location': item['bin_location'],
                'last_contract_num': item['last_contract_num'],
                'date_last_scanned': item['date_last_scanned'],
                'location_of_repair': t_data['location_of_repair'],
                'repair_types': t_data['repair_types']
            })

        # Convert to list of crews for template
        crews = [
            {
                'name': category,
                'item_list': item_list[:20],  # Limit to 20 items initially
                'total_items': len(item_list)  # Store total for pagination
            }
            for category, item_list in sorted(crew_items.items(), key=lambda x: x[0].lower())
        ]
        print(f"DEBUG: Final crews structure: {[{c['name']: len(c['item_list'])} for c in crews]}")
        logger.info(f"Final crews structure: {[{c['name']: len(c['item_list'])} for c in crews]}")
        print(f"DEBUG: Fetched {sum(len(c['item_list']) for c in crews)} total items across {len(crews)} crews")
        logger.info(f"Fetched {sum(len(c['item_list']) for c in crews)} total items across {len(crews)} crews")
        current_app.logger.info(f"Fetched {sum(len(c['item_list']) for c in crews)} total items across {len(crews)} crews")

        session.commit()
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
        print(f"DEBUG: Error rendering Tab 3: {str(e)}")
        logger.error(f"Error rendering Tab 3: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error rendering Tab 3: {str(e)}", exc_info=True)
        if session:
            session.rollback()
            session.close()
        return render_template(
            'tab3.html',
            crews=[],
            common_name_filter='',
            date_filter='',
            sort='date_last_scanned_desc',
            cache_bust=int(datetime.now().timestamp())
        )

@tab3_bp.route('/tab/3/crew_items', methods=['GET'])
def crew_items():
    """
    Fetch paginated items for a specific crew.
    """
    session = None
    try:
        session = db.session()
        crew_id = request.args.get('crew_id')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        common_name_filter = request.args.get('common_name', '').lower()
        date_filter = request.args.get('date_last_scanned', '')
        sort = request.args.get('sort', 'date_last_scanned_desc')

        # Fetch rental class mappings
        base_mappings = session.query(RentalClassMapping).all()
        user_mappings = session.query(UserRentalClassMapping).all()
        mappings_dict = {str(m.rental_class_id).strip().upper(): {'category': m.category, 'subcategory': m.subcategory} for m in base_mappings}
        for um in user_mappings:
            mappings_dict[str(um.rental_class_id).strip().upper()] = {'category': um.category, 'subcategory': um.subcategory}

        # Find rental class numbers for the crew
        rental_class_nums = [rcn for rcn, mapping in mappings_dict.items() if mapping['category'].lower().replace(' ', '-') == crew_id]

        if not rental_class_nums:
            return jsonify({'items': [], 'total_items': 0}), 200

        # Build query
        sql_query = """
            SELECT tag_id, common_name, status, bin_location, last_contract_num, date_last_scanned, rental_class_num
            FROM id_item_master
            WHERE LOWER(TRIM(REPLACE(COALESCE(status, ''), '\0', ''))) IN ('repair', 'needs to be inspected', 'staged', 'wash', 'wet')
            AND LOWER(TRIM(REPLACE(COALESCE(status, ''), '\0', ''))) != 'sold'
            AND rental_class_num IN :rental_class_nums
        """
        params = {'rental_class_nums': tuple(rental_class_nums)}
        if common_name_filter:
            sql_query += " AND LOWER(common_name) LIKE :common_name_filter"
            params['common_name_filter'] = f'%{common_name_filter}%'
        if date_filter:
            try:
                date = datetime.strptime(date_filter, '%Y-%m-%d')
                sql_query += " AND DATE(date_last_scanned) = :date_filter"
                params['date_filter'] = date
            except ValueError:
                pass

        # Apply sorting
        if sort == 'date_last_scanned_asc':
            sql_query += " ORDER BY date_last_scanned ASC, LOWER(common_name) ASC"
        else:
            sql_query += " ORDER BY date_last_scanned DESC, LOWER(common_name) ASC"

        # Add pagination
        sql_query += " LIMIT :limit OFFSET :offset"
        params['limit'] = per_page
        params['offset'] = (page - 1) * per_page

        result = session.execute(text(sql_query), params)
        rows = result.fetchall()

        items = [
            {
                'tag_id': row[0],
                'common_name': row[1],
                'status': row[2],
                'bin_location': row[3] or 'N/A',
                'last_contract_num': row[4] or 'N/A',
                'date_last_scanned': row[5].isoformat() if row[5] else 'N/A',
                'rental_class_num': str(row[6]).strip().upper() if row[6] else None
            }
            for row in rows
        ]

        # Fetch total count
        count_query = """
            SELECT COUNT(*)
            FROM id_item_master
            WHERE LOWER(TRIM(REPLACE(COALESCE(status, ''), '\0', ''))) IN ('repair', 'needs to be inspected', 'staged', 'wash', 'wet')
            AND LOWER(TRIM(REPLACE(COALESCE(status, ''), '\0', ''))) != 'sold'
            AND rental_class_num IN :rental_class_nums
        """
        count_params = {'rental_class_nums': tuple(rental_class_nums)}
        if common_name_filter:
            count_query += " AND LOWER(common_name) LIKE :common_name_filter"
            count_params['common_name_filter'] = f'%{common_name_filter}%'
        if date_filter:
            try:
                date = datetime.strptime(date_filter, '%Y-%m-%d')
                count_query += " AND DATE(date_last_scanned) = :date_filter"
                count_params['date_filter'] = date
            except ValueError:
                pass

        total_items = session.execute(text(count_query), count_params).scalar()

        # Fetch repair details
        tag_ids = [item['tag_id'] for item in items]
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

        # Add repair details to items
        for item in items:
            t_data = transaction_data.get(item['tag_id'], {'location_of_repair': 'N/A', 'repair_types': ['None']})
            item['location_of_repair'] = t_data['location_of_repair']
            item['repair_types'] = t_data['repair_types']

        session.commit()
        return jsonify({'items': items, 'total_items': total_items}), 200
    except Exception as e:
        logger.error(f"Error fetching crew items: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab3_bp.route('/tab/3/pack_resale_common_names', methods=['GET'])
def get_pack_resale_common_names():
    """
    Fetch distinct common names for items with bin_location 'pack' or 'resale' from SeedRentalClass.
    """
    try:
        common_names = db.session.query(SeedRentalClass.common_name)\
            .filter(SeedRentalClass.bin_location.in_(['pack', 'resale']))\
            .distinct()\
            .all()
        common_names = [name[0] for name in common_names if name[0]]
        print(f"DEBUG: Fetched {len(common_names)} common names from SeedRentalClass for pack/resale: {common_names}")
        logger.info(f"Fetched {len(common_names)} common names from SeedRentalClass for pack/resale: {common_names}")
        return jsonify({'common_names': sorted(common_names)}), 200
    except Exception as e:
        print(f"DEBUG: Error fetching pack/resale common names from SeedRentalClass: {str(e)}")
        logger.error(f"Error fetching pack/resale common names from SeedRentalClass: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@tab3_bp.route('/tab/3/sync_to_pc', methods=['POST'])
def sync_to_pc():
    """
    Sync selected items to a CSV file for printing RFID tags.
    Creates exactly the requested number of unique entries, overwriting the existing CSV file.
    If no items exist in ItemMaster, create new entries based on SeedRentalClass.
    Ensure new tag IDs are unique across ItemMaster and new items.
    """
    session = None
    try:
        session = db.session()
        print("DEBUG: Entering /tab/3/sync_to_pc route")

        data = request.get_json()
        print(f"DEBUG: Received request data: {data}")

        common_name = data.get('common_name')
        quantity = data.get('quantity')

        print(f"DEBUG: Sync request data: common_name={common_name}, quantity={quantity}")

        if not common_name or not isinstance(quantity, int) or quantity <= 0:
            print(f"DEBUG: Invalid input: common_name={common_name}, quantity={quantity}")
            logger.warning(f"Invalid input: common_name={common_name}, quantity={quantity}")
            return jsonify({'error': 'Invalid common name or quantity'}), 400

        # Ensure shared directory is writable
        if not os.path.exists(SHARED_DIR):
            print(f"DEBUG: Creating shared directory: {SHARED_DIR}")
            logger.info(f"Creating shared directory: {SHARED_DIR}")
            os.makedirs(SHARED_DIR, mode=0o770)
            os.chown(SHARED_DIR, pwd.getpwnam('tim').pw_uid, grp.getgrnam('tim').gr_gid)
        if not os.access(SHARED_DIR, os.W_OK):
            print(f"DEBUG: Shared directory {SHARED_DIR} is not writable")
            logger.error(f"Shared directory {SHARED_DIR} is not writable")
            return jsonify({'error': f"Shared directory {SHARED_DIR} is not writable"}), 500

        # Query items matching the common name and bin location from ItemMaster
        print("DEBUG: Querying ItemMaster for existing items")
        items = session.query(ItemMaster)\
            .filter(ItemMaster.common_name == common_name,
                    ItemMaster.bin_location.in_(['pack', 'resale']))\
            .order_by(ItemMaster.status.asc())\
            .limit(quantity)\
            .all()
        print(f"DEBUG: Found {len(items)} items in ItemMaster for common_name={common_name} and bin_location in ['pack', 'resale']")
        logger.info(f"Found {len(items)} items in ItemMaster for common_name={common_name} and bin_location in ['pack', 'resale']")

        # Prepare items to sync
        synced_items = []
        new_items = []
        new_tag_ids = set()
        existing_tag_ids = set(item.tag_id for item in items)
        remaining_quantity = quantity - len(items)

        if remaining_quantity > 0:
            print(f"DEBUG: Not enough items found in ItemMaster. Need to create {remaining_quantity} new items for common_name={common_name}")
            logger.info(f"Not enough items found in ItemMaster. Need to create {remaining_quantity} new items for common_name={common_name}")

            # Fetch rental_class_id and bin_location from SeedRentalClass
            print(f"DEBUG: Querying SeedRentalClass for common_name={common_name}")
            seed_entry = session.query(SeedRentalClass)\
                .filter(SeedRentalClass.common_name == common_name,
                        SeedRentalClass.bin_location.in_(['pack', 'resale']))\
                .first()
            print(f"DEBUG: SeedRentalClass query result: {seed_entry}")
            logger.info(f"SeedRentalClass query result: {seed_entry}")

            if not seed_entry:
                print(f"DEBUG: No SeedRentalClass entry found for common_name={common_name} and bin_location in ['pack', 'resale']")
                logger.warning(f"No SeedRentalClass entry found for common_name={common_name} and bin_location in ['pack', 'resale']")
                return jsonify({'error': f"No SeedRentalClass entry found for common name '{common_name}'"}), 404

            rental_class_num = seed_entry.rental_class_id
            bin_location = seed_entry.bin_location
            print(f"DEBUG: SeedRentalClass entry found: rental_class_id={rental_class_num}, bin_location={bin_location}")
            logger.info(f"SeedRentalClass entry found: rental_class_id={rental_class_num}, bin_location={bin_location}")

            # Generate new tag IDs
            for i in range(remaining_quantity):
                print(f"DEBUG: Generating new tag ID {i+1}/{remaining_quantity}")
                max_tag_id = session.query(func.max(ItemMaster.tag_id))\
                    .filter(ItemMaster.tag_id.startswith('425445'))\
                    .scalar()
                print(f"DEBUG: Max tag_id from ItemMaster: {max_tag_id}")
                logger.info(f"Max tag_id from ItemMaster: {max_tag_id}")
                
                if max_tag_id and len(max_tag_id) == 24 and max_tag_id.startswith('425445'):
                    try:
                        incremental_part = int(max_tag_id[6:], 16)
                        new_num = incremental_part + 1
                    except ValueError:
                        print(f"DEBUG: Invalid incremental part in max_tag_id: {max_tag_id}, starting from 1")
                        logger.warning(f"Invalid incremental part in max_tag_id: {max_tag_id}, starting from 1")
                        new_num = 1
                else:
                    new_num = 1

                # Ensure unique tag_id
                while True:
                    incremental_hex = format(new_num, 'x').zfill(18)
                    tag_id = f"425445{incremental_hex}"
                    if tag_id not in existing_tag_ids and tag_id not in new_tag_ids:
                        break
                    new_num += 1
                    print(f"DEBUG: Tag ID {tag_id} already exists, incrementing to {new_num}")

                if len(tag_id) != 24:
                    print(f"DEBUG: Generated tag_id {tag_id} is not 24 characters long (length={len(tag_id)})")
                    logger.error(f"Generated tag_id {tag_id} is not 24 characters long (length={len(tag_id)})")
                    raise ValueError(f"Generated tag_id {tag_id} must be 24 characters long")

                synced_items.append({
                    'tag_id': tag_id,
                    'common_name': common_name,
                    'subcategory': 'Unknown',
                    'short_common_name': common_name,
                    'status': 'Ready to Rent',
                    'bin_location': bin_location,
                    'rental_class_num': rental_class_num,
                    'is_new': True
                })
                new_tag_ids.add(tag_id)
                print(f"DEBUG: Added to synced_items: tag_id={tag_id}, common_name={common_name}")
                logger.info(f"Added to synced_items: tag_id={tag_id}, common_name={common_name}")

                new_item = ItemMaster(
                    tag_id=tag_id,
                    common_name=common_name,
                    rental_class_num=rental_class_num,
                    bin_location=bin_location,
                    status='Ready to Rent',
                    date_created=datetime.now(),
                    date_updated=datetime.now(),
                    uuid_accounts_fk=None,
                    serial_number=None,
                    client_name=None,
                    quality=None,
                    last_contract_num=None,
                    last_scanned_by=None,
                    notes=None,
                    status_notes=None,
                    longitude=None,
                    latitude=None,
                    date_last_scanned=None
                )
                session.add(new_item)
                new_items.append(new_item)
                print(f"DEBUG: Created new ItemMaster entry: tag_id={tag_id}, common_name={common_name}, rental_class_num={rental_class_num}")
                logger.info(f"Created new ItemMaster entry: tag_id={tag_id}, common_name={common_name}, rental_class_num={rental_class_num}")

        # Add existing items to synced_items
        for item in items:
            tag_id = item.tag_id
            if tag_id.startswith('425445'):
                new_tag_ids.add(tag_id)
            print(f"DEBUG: Using tag_id {tag_id} for item with common_name={item.common_name}")
            logger.info(f"Using tag_id {tag_id} for item with common_name={item.common_name}")

            synced_items.append({
                'tag_id': tag_id,
                'common_name': item.common_name,
                'subcategory': 'Unknown',
                'short_common_name': item.common_name,
                'status': item.status,
                'bin_location': item.bin_location,
                'rental_class_num': item.rental_class_num,
                'is_new': False
            })
            print(f"DEBUG: Added to synced_items: tag_id={tag_id}, common_name={item.common_name}")
            logger.info(f"Added to synced_items: tag_id={tag_id}, common_name={item.common_name}")

        # Fetch rental class mappings
        print("DEBUG: Fetching rental class mappings")
        base_mappings = session.query(RentalClassMapping).all()
        user_mappings = session.query(UserRentalClassMapping).all()
        mappings_dict = {str(m.rental_class_id).strip().upper(): {
            'category': m.category,
            'subcategory': m.subcategory,
            'short_common_name': m.short_common_name if hasattr(m, 'short_common_name') else None
        } for m in base_mappings}
        for um in user_mappings:
            mappings_dict[str(um.rental_class_id).strip().upper()] = {
                'category': um.category,
                'subcategory': um.subcategory,
                'short_common_name': um.short_common_name if hasattr(um, 'short_common_name') else None
            }
        print(f"DEBUG: Fetched {len(mappings_dict)} rental class mappings")
        logger.info(f"Fetched {len(mappings_dict)} rental class mappings")

        # Update synced_items with mapping data
        for item in synced_items:
            mapping = mappings_dict.get(str(item['rental_class_num']).strip().upper() if item['rental_class_num'] else '', {})
            item['subcategory'] = mapping.get('subcategory', 'Unknown')
            item['short_common_name'] = mapping.get('short_common_name', item['common_name'])
            print(f"DEBUG: Updated synced_item with mappings: {item}")
            logger.info(f"Updated synced_item with mappings: {item}")

        # Overwrite the CSV file
        print("DEBUG: Writing to CSV file")
        try:
            with open(CSV_FILE_PATH, 'w', newline='') as csvfile:
                fieldnames = ['tag_id', 'common_name', 'subcategory', 'short_common_name', 'status', 'bin_location']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                print("DEBUG: Wrote CSV header row")
                logger.info("Wrote CSV header row")
                for item in synced_items:
                    writer.writerow({
                        'tag_id': item['tag_id'],
                        'common_name': item['common_name'],
                        'subcategory': item['subcategory'],
                        'short_common_name': item['short_common_name'],
                        'status': item['status'],
                        'bin_location': item['bin_location']
                    })
                    print(f"DEBUG: Wrote CSV row: {item}")
                    logger.info(f"Wrote CSV row: {item}")
        except Exception as e:
            print(f"DEBUG: Failed to write to CSV file {CSV_FILE_PATH}: {str(e)}")
            logger.error(f"Failed to write to CSV file {CSV_FILE_PATH}: {str(e)}", exc_info=True)
            return jsonify({'error': f"Failed to write to CSV file: {str(e)}"}), 500

        # Commit new ItemMaster entries
        if new_items:
            print("DEBUG: Committing session after CSV write")
            try:
                session.flush()
                print(f"DEBUG: Session flushed successfully after CSV write")
                logger.info(f"Session flushed successfully after CSV write")
                session.commit()
                print(f"DEBUG: Successfully committed {len(new_items)} new ItemMaster entries")
                logger.info(f"Successfully committed {len(new_items)} new ItemMaster entries")
            except Exception as e:
                print(f"DEBUG: Failed to commit session after CSV write: {str(e)}")
                logger.error(f"Failed to commit session after CSV write: {str(e)}", exc_info=True)
                session.rollback()
                print("DEBUG: Returning success response despite commit failure (CSV write completed)")
                logger.warning("Returning success response despite commit failure (CSV write completed)")
                return jsonify({'synced_items': len(synced_items)}), 200

        print(f"DEBUG: Successfully synced {len(synced_items)} items to CSV")
        logger.info(f"Successfully synced {len(synced_items)} items to CSV")
        return jsonify({'synced_items': len(synced_items)}), 200
    except Exception as e:
        print(f"DEBUG: Uncaught exception in sync_to_pc: {str(e)}")
        logger.error(f"Error in sync_to_pc: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()
            print("DEBUG: Session closed")

@tab3_bp.route('/tab/3/update_synced_status', methods=['POST'])
def update_synced_status():
    """
    Update the status of items in the CSV file to 'Ready to Rent' and clear the CSV file.
    Inserts new tag_id entries into the API via POST and updates existing ones via PATCH.
    """
    session = None
    try:
        session = db.session()
        print("DEBUG: Entering /tab/3/update_synced_status route")
        logger.info("Received request for /tab/3/update_synced_status")

        if not os.path.exists(CSV_FILE_PATH):
            print("DEBUG: No synced items found in CSV file")
            logger.info("No synced items found in CSV file")
            return jsonify({'error': 'No synced items found'}), 404

        if os.path.getsize(CSV_FILE_PATH) == 0:
            print("DEBUG: CSV file is empty")
            logger.info("CSV file is empty")
            return jsonify({'error': 'No items found in CSV file'}), 404

        print("DEBUG: Reading items from CSV file")
        items_to_update = []
        try:
            with open(CSV_FILE_PATH, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                required_fields = ['tag_id', 'common_name', 'bin_location', 'status']
                if not all(field in reader.fieldnames for field in required_fields):
                    missing = [field for field in required_fields if field not in reader.fieldnames]
                    print(f"DEBUG: CSV file missing required fields: {missing}")
                    logger.error(f"CSV file missing required fields: {missing}")
                    return jsonify({'error': f"CSV file missing required fields: {missing}"}), 400

                for row in reader:
                    try:
                        items_to_update.append({
                            'tag_id': row['tag_id'],
                            'common_name': row['common_name'],
                            'bin_location': row['bin_location'],
                            'status': row['status']
                        })
                        print(f"DEBUG: Read CSV row: {row}")
                    except KeyError as ke:
                        print(f"DEBUG: Missing required field in CSV row: {ke}, row: {row}")
                        logger.error(f"Missing required field in CSV row: {ke}, row: {row}")
                        return jsonify({'error': f"Missing required field in CSV row: {ke}"}), 400
        except Exception as e:
            print(f"DEBUG: Error reading CSV file: {str(e)}")
            logger.error(f"Error reading CSV file: {str(e)}", exc_info=True)
            return jsonify({'error': f"Error reading CSV file: {str(e)}"}), 500

        if not items_to_update:
            print("DEBUG: No items found in CSV file to update")
            logger.info("No items found in CSV file to update")
            return jsonify({'error': 'No items found in CSV file'}), 404

        tag_ids = [item['tag_id'] for item in items_to_update]
        print(f"DEBUG: Found {len(tag_ids)} items to update: {tag_ids}")
        logger.info(f"Found {len(tag_ids)} items to update: {tag_ids}")

        print("DEBUG: Fetching rental_class_num from ItemMaster")
        try:
            items_in_db = session.query(ItemMaster.tag_id, ItemMaster.rental_class_num, ItemMaster.common_name, ItemMaster.bin_location)\
                .filter(ItemMaster.tag_id.in_(tag_ids))\
                .all()
            item_dict = {item.tag_id: {
                'rental_class_num': item.rental_class_num,
                'common_name': item.common_name,
                'bin_location': item.bin_location
            } for item in items_in_db}
            print(f"DEBUG: Fetched {len(item_dict)} items from ItemMaster for tag_ids: {list(item_dict.keys())}")
            logger.debug(f"Fetched {len(item_dict)} items from ItemMaster for tag_ids: {list(item_dict.keys())}")
        except Exception as e:
            print(f"DEBUG: Error querying ItemMaster for tag_ids: {str(e)}")
            logger.error(f"Error querying ItemMaster for tag_ids: {str(e)}", exc_info=True)
            return jsonify({'error': f"Error querying ItemMaster: {str(e)}"}), 500

        print("DEBUG: Updating ItemMaster status to 'Ready to Rent'")
        try:
            updated_items = ItemMaster.query\
                .filter(ItemMaster.tag_id.in_(tag_ids))\
                .update({ItemMaster.status: 'Ready to Rent'}, synchronize_session='fetch')
            print(f"DEBUG: Updated {updated_items} items in ItemMaster to 'Ready to Rent'")
            logger.info(f"Updated {updated_items} items in ItemMaster to 'Ready to Rent'")
        except Exception as e:
            print(f"DEBUG: Error updating ItemMaster status: {str(e)}")
            logger.error(f"Error updating ItemMaster status: {str(e)}", exc_info=True)
            return jsonify({'error': f"Error updating ItemMaster: {str(e)}"}), 500

        print("DEBUG: Updating items via API")
        api_client = APIClient()
        for item in items_to_update:
            tag_id = item['tag_id']
            db_item = item_dict.get(tag_id, {})
            print(f"DEBUG: Processing tag_id {tag_id}: db_item={db_item}")
            logger.debug(f"Processing tag_id {tag_id}: db_item={db_item}")
            try:
                params = {'filter[eq]': f"tag_id,eq,'{tag_id}'"}
                existing_items = api_client._make_request("14223767938169344381", params)
                print(f"DEBUG: API check for tag_id {tag_id}: found {len(existing_items)} items")
                logger.debug(f"API check for tag_id {tag_id}: found {len(existing_items)} items")
                if existing_items:
                    api_client.update_status(tag_id, 'Ready to Rent')
                    print(f"DEBUG: Updated existing tag_id {tag_id} via API PATCH")
                    logger.info(f"Updated existing tag_id {tag_id} via API PATCH")
                else:
                    new_item = {
                        'tag_id': tag_id,
                        'common_name': db_item.get('common_name', item['common_name']),
                        'bin_location': db_item.get('bin_location', item['bin_location']),
                        'status': 'Ready to Rent',
                        'date_last_scanned': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'rental_class_num': db_item.get('rental_class_num', '')
                    }
                    api_client.insert_item(new_item)
                    print(f"DEBUG: Inserted new tag_id {tag_id} via API POST with data: {new_item}")
                    logger.info(f"Inserted new tag_id {tag_id} via API POST with data: {new_item}")
            except Exception as api_error:
                print(f"DEBUG: Error updating/inserting tag_id {tag_id} in API: {str(api_error)}")
                logger.error(f"Error updating/inserting tag_id {tag_id} in API: {str(api_error)}", exc_info=True)
                return jsonify({'error': f"Failed to update/insert tag_id {tag_id} in API: {str(api_error)}"}), 500

        print("DEBUG: Clearing CSV file")
        try:
            with open(CSV_FILE_PATH, 'w', newline='') as csvfile:
                fieldnames = ['tag_id', 'common_name', 'subcategory', 'short_common_name', 'status', 'bin_location']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
            print("DEBUG: Cleared CSV file")
            logger.info("Cleared CSV file")
        except Exception as e:
            print(f"DEBUG: Error clearing CSV file: {str(e)}")
            logger.error(f"Error clearing CSV file: {str(e)}", exc_info=True)
            return jsonify({'error': f"Error clearing CSV file: {str(e)}"}), 500

        print("DEBUG: Committing session after API updates")
        session.commit()
        print(f"DEBUG: Updated status for {updated_items} items and cleared CSV file")
        logger.info(f"Updated status for {updated_items} items and cleared CSV file")
        return jsonify({'updated_items': updated_items}), 200
    except Exception as e:
        print(f"DEBUG: Uncaught exception in update_synced_status: {str(e)}")
        logger.error(f"Error in update_synced_status: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()
            print("DEBUG: Session closed")

@tab3_bp.route('/tab/3/update_status', methods=['POST'])
def update_status():
    session = None
    try:
        session = db.session()
        print("DEBUG: Entering /tab/3/update_status route")
        data = request.get_json()
        tag_id = data.get('tag_id')
        new_status = data.get('status')

        if not tag_id or not new_status:
            print(f"DEBUG: Invalid input in update_status: tag_id={tag_id}, new_status={new_status}")
            logger.warning(f"Invalid input in update_status: tag_id={tag_id}, new_status={new_status}")
            return jsonify({'error': 'Tag ID and status are required'}), 400

        valid_statuses = ['Ready to Rent', 'Sold', 'Repair', 'Needs to be Inspected', 'Staged', 'Wash', 'Wet']
        if new_status not in valid_statuses:
            print(f"DEBUG: Invalid status value: {new_status}")
            logger.warning(f"Invalid status value: {new_status}")
            return jsonify({'error': f'Status must be one of {", ".join(valid_statuses)}'}), 400

        print(f"DEBUG: Querying ItemMaster for tag_id={tag_id}")
        item = session.query(ItemMaster).filter_by(tag_id=tag_id).first()
        if not item:
            session.close()
            print(f"DEBUG: Item not found for tag_id {tag_id}")
            logger.info(f"Item not found for tag_id {tag_id}")
            return jsonify({'error': 'Item not found'}), 404

        if new_status in ['On Rent', 'Delivered']:
            session.close()
            print(f"DEBUG: Attempted manual update to restricted status {new_status} for tag_id {tag_id}")
            logger.warning(f"Attempted manual update to restricted status {new_status} for tag_id {tag_id}")
            return jsonify({'error': 'Status cannot be updated to "On Rent" or "Delivered" manually'}), 400

        print(f"DEBUG: Updating ItemMaster status for tag_id={tag_id} to {new_status}")
        current_time = datetime.now()
        item.status = new_status
        item.date_last_scanned = current_time
        session.commit()

        print(f"DEBUG: Updating external API for tag_id={tag_id}")
        api_client = APIClient()
        api_client.update_status(tag_id, new_status)

        session.close()
        print(f"DEBUG: Updated status for tag_id {tag_id} to {new_status} and date_last_scanned to {current_time}")
        logger.info(f"Updated status for tag_id {tag_id} to {new_status} and date_last_scanned to {current_time}")
        return jsonify({'message': 'Status updated successfully'})
    except Exception as e:
        print(f"DEBUG: Uncaught exception in update_status: {str(e)}")
        logger.error(f"Error updating status for tag {tag_id}: {str(e)}", exc_info=True)
        if session:
            session.rollback()
            session.close()
        return jsonify({'error': str(e)}), 500