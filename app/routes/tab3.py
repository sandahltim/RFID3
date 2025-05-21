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
import sqlalchemy.exc
import fcntl
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests.exceptions

# Configure logging for Tab 3
logger = logging.getLogger('tab3')
logger.setLevel(logging.DEBUG)

# Remove existing handlers to avoid duplicates
logger.handlers = []

# File handler for rfid_dashboard.log
log_file_path = '/home/tim/test_rfidpi/logs/rfid_dashboard.log'
try:
    if not os.path.exists(log_file_path):
        open(log_file_path, 'a').close()
    os.chmod(log_file_path, 0o666)
    os.chown(log_file_path, pwd.getpwnam('tim').pw_uid, grp.getgrnam('tim').gr_gid)
except Exception as e:
    print(f"ERROR: Failed to set up log file {log_file_path}: {str(e)}")
    sys.stderr.write(f"ERROR: Failed to set up log file {log_file_path}: {str(e)}\n")

file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler for stdout
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Ensure logger propagates to root logger
logger.propagate = True

# Blueprint for Tab 3 routes
tab3_bp = Blueprint('tab3', __name__)

# Directory for shared CSV files
SHARED_DIR = '/home/tim/test_rfidpi/shared'
CSV_FILE_PATH = os.path.join(SHARED_DIR, 'rfid_tags.csv')
LOCK_FILE_PATH = os.path.join(SHARED_DIR, 'rfid_tags.lock')

# Ensure shared directory exists with correct permissions
if not os.path.exists(SHARED_DIR):
    print(f"DEBUG: Creating shared directory: {SHARED_DIR}")
    logger.info(f"Creating shared directory: {SHARED_DIR}")
    os.makedirs(SHARED_DIR, mode=0o770)
    os.chown(SHARED_DIR, pwd.getpwnam('tim').pw_uid, grp.getgrnam('tim').gr_gid)

# Version marker for deployment tracking
logger.info("Deployed tab3.py version: 2025-05-21-v50")

@tab3_bp.route('/tab/3')
def tab3_view():
    """Render Tab 3 view with items grouped by common_name and status."""
    logger.debug("Entering /tab/3 endpoint")
    session = None
    try:
        logger.debug("Attempting to create new database session")
        session = db.session()
        logger.info("Successfully created new session for tab3")
        current_app.logger.info("Successfully created new session for tab3")

        # Test database connection
        logger.debug("Testing database connection with SELECT 1")
        session.execute(text("SELECT 1"))
        logger.info("Database connection test successful")

        # Log distinct status values in id_item_master for debugging
        status_query = """
            SELECT DISTINCT status
            FROM id_item_master
            WHERE status IS NOT NULL
        """
        logger.debug(f"Executing status query: {status_query}")
        status_result = session.execute(text(status_query))
        statuses = [row[0] for row in status_result.fetchall()]
        logger.info(f"Distinct statuses in id_item_master: {statuses}")

        # Query parameters for filtering and sorting
        common_name_filter = request.args.get('common_name', '').lower()
        date_filter = request.args.get('date_last_scanned', '')
        sort = request.args.get('sort', 'date_last_scanned_desc')
        page = int(request.args.get('page', 1))
        per_page = 20
        logger.debug(f"Query parameters - common_name_filter: {common_name_filter}, date_filter: {date_filter}, sort: {sort}, page: {page}, per_page: {per_page}")

        # Simplified query with direct IN clause for status matching
        sql_query = """
            SELECT tag_id, common_name, status, bin_location, last_contract_num, date_last_scanned, rental_class_num, notes
            FROM id_item_master
            WHERE TRIM(COALESCE(status, '')) IN ('Repair', 'Needs to be Inspected', 'Staged', 'Wash', 'Wet')
              AND TRIM(COALESCE(status, '')) != 'Sold'
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

        logger.debug(f"Executing raw SQL query: {sql_query} with params: {params}")
        result = session.execute(text(sql_query), params)
        rows = result.fetchall()
        logger.info(f"Raw query returned {len(rows)} rows")

        # Log the raw rows for debugging
        raw_data = [
            {
                'tag_id': row[0],
                'common_name': row[1],
                'status': row[2],
                'bin_location': row[3],
                'last_contract_num': row[4],
                'date_last_scanned': row[5],
                'rental_class_num': row[6],
                'notes': row[7]
            }
            for row in rows
        ]
        logger.info(f"Raw rows: {raw_data}")

        items_in_service = [
            {
                'tag_id': row[0],
                'common_name': row[1],
                'status': row[2],
                'bin_location': row[3] or 'N/A',
                'last_contract_num': row[4] or 'N/A',
                'date_last_scanned': row[5].isoformat() if row[5] else 'N/A',
                'rental_class_num': str(row[6]).strip().upper() if row[6] else None,
                'notes': row[7] or ''
            }
            for row in rows
        ]
        logger.info(f"Processed {len(items_in_service)} items: {[item['tag_id'] + ': ' + item['status'] for item in items_in_service]}")

        # Fetch total count for pagination
        count_query = """
            SELECT COUNT(*) 
            FROM id_item_master
            WHERE TRIM(COALESCE(status, '')) IN ('Repair', 'Needs to be Inspected', 'Staged', 'Wash', 'Wet')
              AND TRIM(COALESCE(status, '')) != 'Sold'
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

        logger.debug(f"Executing count query: {count_query} with params: {count_params}")
        total_items = session.execute(text(count_query), count_params).scalar()
        logger.info(f"Total items matching query: {total_items}")

        # Fetch repair details and additional transaction fields
        tag_ids = [item['tag_id'] for item in items_in_service]
        transaction_data = {}
        if tag_ids:
            logger.debug(f"Fetching transactions for {len(tag_ids)} tag_ids")
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
                Transaction.other,
                Transaction.service_required,
                Transaction.longitude,
                Transaction.latitude,
                Transaction.scan_date
            ).join(
                max_scan_date_subquery,
                (Transaction.tag_id == max_scan_date_subquery.c.tag_id) &
                (Transaction.scan_date == max_scan_date_subquery.c.max_scan_date)
            ).all()

            logger.info(f"Fetched {len(transactions)} transactions for {len(tag_ids)} tag_ids")

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
                if t.service_required: repair_types.append("Service Required")

                transaction_data[t.tag_id] = {
                    'location_of_repair': t.location_of_repair or 'N/A',
                    'repair_types': repair_types if repair_types else ['None'],
                    'dirty_or_mud': t.dirty_or_mud,
                    'leaves': t.leaves,
                    'oil': t.oil,
                    'mold': t.mold,
                    'stain': t.stain,
                    'oxidation': t.oxidation,
                    'rip_or_tear': t.rip_or_tear,
                    'sewing_repair_needed': t.sewing_repair_needed,
                    'grommet': t.grommet,
                    'rope': t.rope,
                    'buckle': t.buckle,
                    'wet': t.wet,
                    'other': t.other or 'N/A',
                    'service_required': t.service_required,
                    'longitude': float(t.longitude) if t.longitude is not None else None,
                    'latitude': float(t.latitude) if t.latitude is not None else None,
                    'last_transaction_scan_date': t.scan_date.strftime('%Y-%m-%d %H:%M:%S') if t.scan_date else 'N/A'
                }
                logger.debug(f"Transaction data for tag_id {t.tag_id}: {transaction_data[t.tag_id]}")

        # Group items by common_name and status
        items_by_common_name = {}
        for item in items_in_service:
            common_name = item['common_name']
            status = item['status']
            if common_name not in items_by_common_name:
                items_by_common_name[common_name] = {}
            if status not in items_by_common_name[common_name]:
                items_by_common_name[common_name][status] = []
            
            t_data = transaction_data.get(item['tag_id'], {
                'location_of_repair': 'N/A',
                'repair_types': ['None'],
                'dirty_or_mud': False,
                'leaves': False,
                'oil': False,
                'mold': False,
                'stain': False,
                'oxidation': False,
                'rip_or_tear': False,
                'sewing_repair_needed': False,
                'grommet': False,
                'rope': False,
                'buckle': False,
                'wet': False,
                'other': 'N/A',
                'service_required': False,
                'longitude': None,
                'latitude': None,
                'last_transaction_scan_date': 'N/A'
            })

            items_by_common_name[common_name][status].append({
                'tag_id': item['tag_id'],
                'common_name': item['common_name'],
                'status': item['status'],
                'bin_location': item['bin_location'],
                'last_contract_num': item['last_contract_num'],
                'date_last_scanned': item['date_last_scanned'],
                'location_of_repair': t_data['location_of_repair'],
                'repair_types': t_data['repair_types'],
                'notes': item['notes'],
                'dirty_or_mud': t_data['dirty_or_mud'],
                'leaves': t_data['leaves'],
                'oil': t_data['oil'],
                'mold': t_data['mold'],
                'stain': t_data['stain'],
                'oxidation': t_data['oxidation'],
                'rip_or_tear': t_data['rip_or_tear'],
                'sewing_repair_needed': t_data['sewing_repair_needed'],
                'grommet': t_data['grommet'],
                'rope': t_data['rope'],
                'buckle': t_data['buckle'],
                'wet': t_data['wet'],
                'other': t_data['other'],
                'service_required': t_data['service_required'],
                'longitude': t_data['longitude'],
                'latitude': t_data['latitude'],
                'last_transaction_scan_date': t_data['last_transaction_scan_date']
            })

        # Define status priority order
        status_priority = {
            'Repair': 1,
            'Wash': 2,
            'Wet': 3,
            'Staged': 4,
            'Needs to be Inspected': 5
        }

        # Structure data for template: list of common names, each with a list of status groups
        common_name_groups = []
        for common_name, statuses in sorted(items_by_common_name.items()):
            status_groups = []
            for status in sorted(statuses.keys(), key=lambda s: status_priority.get(s, 6)):
                status_groups.append({
                    'status': status,
                    'items': statuses[status],
                    'total_items': len(statuses[status])
                })
            common_name_groups.append({
                'common_name': common_name,
                'status_groups': status_groups,
                'total_items': sum(len(statuses[s]) for s in statuses)
            })

        logger.info(f"Final common_name_groups structure: {[{'common_name': c['common_name'], 'total_items': c['total_items'], 'status_groups': [{s['status']: s['total_items']} for s in c['status_groups']]} for c in common_name_groups]}")
        logger.info(f"Total items fetched: {sum(c['total_items'] for c in common_name_groups)}")

        session.commit()
        session.close()
        logger.debug("Rendering tab3.html with common_name_groups")
        return render_template(
            'tab3.html',
            common_name_groups=common_name_groups,
            common_name_filter=common_name_filter,
            date_filter=date_filter,
            sort=sort,
            cache_bust=int(datetime.now().timestamp())
        )
    except Exception as e:
        logger.error(f"Error rendering Tab 3: {str(e)}", exc_info=True)
        current_app.logger.error(f"Error rendering Tab 3: {str(e)}", exc_info=True)
        if session:
            session.rollback()
            session.close()
        logger.debug("Rendering tab3.html with empty common_name_groups due to error")
        return render_template(
            'tab3.html',
            common_name_groups=[],
            common_name_filter='',
            date_filter='',
            sort='date_last_scanned_desc',
            cache_bust=int(datetime.now().timestamp())
        )

@tab3_bp.route('/tab/3/csv_contents', methods=['GET'])
def get_csv_contents():
    """Fetch the contents of rfid_tags.csv for display in the UI."""
    try:
        logger.debug("Entering /tab/3/csv_contents endpoint")
        if not os.path.exists(CSV_FILE_PATH):
            logger.info("CSV file does not exist")
            return jsonify({'items': [], 'count': 0}), 200

        items = []
        with open(CSV_FILE_PATH, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            required_fields = ['tag_id', 'common_name', 'subcategory', 'short_common_name', 'status', 'bin_location']
            if not all(field in reader.fieldnames for field in required_fields):
                logger.warning("CSV file missing required fields")
                return jsonify({'error': 'CSV file missing required fields'}), 400

            for row in reader:
                items.append({
                    'tag_id': row['tag_id'],
                    'common_name': row['common_name'],
                    'subcategory': row['subcategory'],
                    'short_common_name': row['short_common_name'],
                    'status': row['status'],
                    'bin_location': row['bin_location']
                })

        logger.info(f"Fetched {len(items)} items from CSV")
        return jsonify({'items': items, 'count': len(items)}), 200
    except Exception as e:
        logger.error(f"Error reading CSV file: {str(e)}", exc_info=True)
        return jsonify({'error': f"Error reading CSV file: {str(e)}"}), 500

@tab3_bp.route('/tab/3/remove_csv_item', methods=['POST'])
def remove_csv_item():
    """Remove a specific item from rfid_tags.csv based on tag_id."""
    lock_file = None
    try:
        logger.debug("Entering /tab/3/remove_csv_item endpoint")
        # Acquire lock to prevent concurrent CSV modifications
        lock_file = open(LOCK_FILE_PATH, 'w')
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        logger.debug("Acquired lock for remove_csv_item")

        data = request.get_json()
        tag_id = data.get('tag_id')

        if not tag_id:
            logger.warning("tag_id is required")
            return jsonify({'error': 'tag_id is required'}), 400

        if not os.path.exists(CSV_FILE_PATH):
            logger.info("CSV file does not exist")
            return jsonify({'error': 'CSV file does not exist'}), 404

        # Read existing items
        items = []
        with open(CSV_FILE_PATH, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames
            for row in reader:
                if row['tag_id'] != tag_id:
                    items.append(row)

        # Write back items excluding the removed one
        with open(CSV_FILE_PATH, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for item in items:
                writer.writerow(item)

        logger.info(f"Removed item with tag_id {tag_id} from CSV")
        return jsonify({'message': f"Removed item with tag_id {tag_id}"}), 200
    except Exception as e:
        logger.error(f"Error removing item from CSV: {str(e)}", exc_info=True)
        return jsonify({'error': f"Error removing item from CSV: {str(e)}"}), 500
    finally:
        if lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
            lock_file.close()
            logger.debug("Released lock for remove_csv_item")

@tab3_bp.route('/tab/3/sync_to_pc', methods=['POST'])
def sync_to_pc():
    """
    Sync selected items to rfid_tags.csv for printing RFID tags.
    Appends exactly 'quantity' unique entries to the CSV, using existing ItemMaster tags
    (prioritizing 'Sold', then others) and generating new tags if needed.
    Added file-based lock to prevent concurrent CSV writes and duplicates.
    """
    session = None
    lock_file = None
    try:
        logger.debug("Entering /tab/3/sync_to_pc endpoint")
        session = db.session()
        logger.info("Entering /tab/3/sync_to_pc route")

        # Acquire lock to prevent concurrent CSV modifications
        lock_file = open(LOCK_FILE_PATH, 'w')
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            logger.debug("Acquired lock for sync_to_pc")
        except BlockingIOError:
            logger.warning("Another sync_to_pc operation is in progress")
            return jsonify({'error': 'Another sync operation is in progress'}), 429

        data = request.get_json()
        logger.debug(f"Received request data: {data}")

        common_name = data.get('common_name')
        quantity = data.get('quantity')

        logger.info(f"Sync request: common_name={common_name}, quantity={quantity}")

        # Validate input
        if not common_name or not isinstance(quantity, int) or quantity <= 0:
            logger.warning(f"Invalid input: common_name={common_name}, quantity={quantity}")
            return jsonify({'error': 'Invalid common name or quantity'}), 400

        # Ensure shared directory is writable
        if not os.path.exists(SHARED_DIR):
            logger.info(f"Creating shared directory: {SHARED_DIR}")
            os.makedirs(SHARED_DIR, mode=0o770)
            os.chown(SHARED_DIR, pwd.getpwnam('tim').pw_uid, grp.getgrnam('tim').gr_gid)
        if not os.access(SHARED_DIR, os.W_OK):
            logger.error(f"Shared directory {SHARED_DIR} is not writable")
            return jsonify({'error': f"Shared directory {SHARED_DIR} is not writable"}), 500

        # Read existing tag_ids from CSV and remove duplicates
        logger.debug("Reading existing tag_ids from CSV")
        csv_tag_ids = set()
        existing_items = []
        needs_header = not os.path.exists(CSV_FILE_PATH)
        if os.path.exists(CSV_FILE_PATH):
            try:
                with open(CSV_FILE_PATH, 'r') as csvfile:
                    first_line = csvfile.readline().strip()
                    if not first_line:
                        needs_header = True
                    else:
                        csvfile.seek(0)
                        reader = csv.DictReader(csvfile)
                        required_fields = ['tag_id', 'common_name', 'subcategory', 'short_common_name', 'status', 'bin_location']
                        if not all(field in reader.fieldnames for field in required_fields):
                            logger.warning("CSV file exists but lacks valid headers. Rewriting with headers.")
                            needs_header = True
                        else:
                            for row in reader:
                                if 'tag_id' in row and row['tag_id'] not in csv_tag_ids:
                                    csv_tag_ids.add(row['tag_id'])
                                    existing_items.append(row)
            except Exception as e:
                logger.error(f"Error reading existing CSV file: {str(e)}", exc_info=True)
                return jsonify({'error': f"Failed to read existing CSV file: {str(e)}"}), 500

        logger.info(f"Found {len(csv_tag_ids)} unique tag_ids in CSV before sync")

        # Initialize synced items and tracking set
        synced_items = []
        existing_tag_ids = csv_tag_ids.copy()

        # Step 1: Query ItemMaster for existing items
        logger.debug("Querying ItemMaster for existing items")
        try:
            # Get 'Sold' items first, up to quantity
            sold_items = session.query(ItemMaster)\
                .filter(ItemMaster.common_name == common_name,
                        ItemMaster.bin_location.in_(['pack', 'resale']),
                        ItemMaster.status == 'Sold')\
                .order_by(ItemMaster.date_updated.asc())\
                .all()
            logger.debug(f"Found {len(sold_items)} 'Sold' items in ItemMaster for common_name={common_name}")

            for item in sold_items:
                if len(synced_items) >= quantity:
                    break
                if item.tag_id in existing_tag_ids:
                    logger.debug(f"Skipping tag_id {item.tag_id} as it’s already in use")
                    continue
                synced_items.append({
                    'tag_id': item.tag_id,
                    'common_name': item.common_name,
                    'subcategory': 'Unknown',
                    'short_common_name': item.common_name,
                    'status': item.status,
                    'bin_location': item.bin_location,
                    'rental_class_num': item.rental_class_num,
                    'is_new': False
                })
                existing_tag_ids.add(item.tag_id)
                logger.info(f"Added to synced_items: tag_id={item.tag_id}, common_name={item.common_name}, status={item.status}")

            # Get non-'Sold' items if needed, up to remaining quantity
            if len(synced_items) < quantity:
                remaining_quantity = quantity - len(synced_items)
                other_items = session.query(ItemMaster)\
                    .filter(ItemMaster.common_name == common_name,
                            ItemMaster.bin_location.in_(['pack', 'resale']),
                            ItemMaster.status != 'Sold')\
                    .order_by(ItemMaster.status.asc())\
                    .all()
                logger.debug(f"Found {len(other_items)} non-'Sold' items in ItemMaster")

                for item in other_items:
                    if len(synced_items) >= quantity:
                        break
                    if item.tag_id in existing_tag_ids:
                        logger.debug(f"Skipping tag_id {item.tag_id} as it’s already in use")
                        continue
                    synced_items.append({
                        'tag_id': item.tag_id,
                        'common_name': item.common_name,
                        'subcategory': 'Unknown',
                        'short_common_name': item.common_name,
                        'status': item.status,
                        'bin_location': item.bin_location,
                        'rental_class_num': item.rental_class_num,
                        'is_new': False
                    })
                    existing_tag_ids.add(item.tag_id)
                    logger.info(f"Added to synced_items: tag_id={item.tag_id}, common_name={item.common_name}, status={item.status}")

                remaining_quantity = quantity - len(synced_items)
                logger.debug(f"After non-Sold items, remaining_quantity={remaining_quantity}")
        except sqlalchemy.exc.DatabaseError as e:
            logger.error(f"Database error querying ItemMaster: {str(e)}", exc_info=True)
            return jsonify({'error': f"Database error querying ItemMaster: {str(e)}"}), 500

        # Step 2: Generate new tags if needed
        new_items = []
        if len(synced_items) < quantity:
            remaining_quantity = quantity - len(synced_items)
            logger.info(f"Generating {remaining_quantity} new items for common_name={common_name}")

            # Fetch rental_class_id and bin_location from SeedRentalClass
            logger.debug(f"Querying SeedRentalClass for common_name={common_name}")
            try:
                seed_entry = session.query(SeedRentalClass)\
                    .filter(SeedRentalClass.common_name == common_name,
                            SeedRentalClass.bin_location.in_(['pack', 'resale']))\
                    .first()
                logger.debug(f"SeedRentalClass query result: {seed_entry}")
            except sqlalchemy.exc.DatabaseError as e:
                logger.error(f"Database error querying SeedRentalClass: {str(e)}", exc_info=True)
                return jsonify({'error': f"Database error querying SeedRentalClass: {str(e)}"}), 500

            if not seed_entry:
                logger.warning(f"No SeedRentalClass entry found for common_name={common_name} and bin_location in ['pack', 'resale']")
                return jsonify({'error': f"No SeedRentalClass entry found for common name '{common_name}'"}), 404

            rental_class_num = seed_entry.rental_class_id
            bin_location = seed_entry.bin_location
            logger.info(f"SeedRentalClass entry: rental_class_id={rental_class_num}, bin_location={bin_location}")

            # Generate new tag IDs
            for i in range(remaining_quantity):
                logger.debug(f"Generating new tag ID {i+1}/{remaining_quantity}")
                try:
                    max_tag_id = session.query(func.max(ItemMaster.tag_id))\
                        .filter(ItemMaster.tag_id.startswith('425445'))\
                        .scalar()
                    logger.debug(f"Max tag_id from ItemMaster: {max_tag_id}")
                except sqlalchemy.exc.DatabaseError as e:
                    logger.error(f"Database error querying max tag_id: {str(e)}", exc_info=True)
                    return jsonify({'error': f"Database error querying max tag_id: {str(e)}"}), 500

                new_num = 1
                if max_tag_id and len(max_tag_id) == 24 and max_tag_id.startswith('425445'):
                    try:
                        incremental_part = int(max_tag_id[6:], 16)
                        new_num = incremental_part + 1
                    except ValueError:
                        logger.warning(f"Invalid incremental part in max_tag_id: {max_tag_id}, starting from 1")

                # Ensure unique tag_id
                while True:
                    incremental_hex = format(new_num, 'x').zfill(18)
                    tag_id = f"425445{incremental_hex}"
                    if tag_id not in existing_tag_ids:
                        break
                    new_num += 1
                    logger.debug(f"Tag ID {tag_id} already exists, incrementing to {new_num}")

                if len(tag_id) != 24:
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
                existing_tag_ids.add(tag_id)
                logger.info(f"Added to synced_items: tag_id={tag_id}, common_name={common_name}, status=Ready to Rent")

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
                logger.info(f"Created new ItemMaster entry: tag_id={tag_id}, common_name={common_name}, rental_class_num={rental_class_num}")

        # Ensure exactly the requested quantity before CSV write
        if len(synced_items) > quantity:
            synced_items = synced_items[:quantity]
            logger.info(f"Truncated synced_items to {quantity} items before CSV write")
        elif len(synced_items) < quantity:
            logger.warning(f"Only {len(synced_items)} items synced, requested {quantity}")

        # Log final synced items for debugging
        logger.info(f"Final synced_items ({len(synced_items)}): {[item['tag_id'] for item in synced_items]}")

        # Fetch rental class mappings
        logger.debug("Fetching rental class mappings")
        try:
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
            logger.info(f"Fetched {len(mappings_dict)} rental class mappings")
        except sqlalchemy.exc.DatabaseError as e:
            logger.error(f"Database error fetching rental class mappings: {str(e)}", exc_info=True)
            return jsonify({'error': f"Database error fetching rental class mappings: {str(e)}"}), 500

        # Update synced_items with mapping data
        for item in synced_items:
            mapping = mappings_dict.get(str(item['rental_class_num']).strip().upper() if item['rental_class_num'] else '', {})
            item['subcategory'] = mapping.get('subcategory', 'Unknown')
            item['short_common_name'] = mapping.get('short_common_name', item['common_name'])
            logger.debug(f"Updated synced_item with mappings: {item}")

        # Write to CSV, preserving existing non-duplicate items
        logger.debug("Writing to CSV file")
        try:
            # Combine existing items (minus duplicates) with new synced items
            all_items = [item for item in existing_items if item['tag_id'] not in {i['tag_id'] for i in synced_items}]
            all_items.extend(synced_items)
            logger.info(f"Total items to write to CSV: {len(all_items)}")

            with open(CSV_FILE_PATH, 'w', newline='') as csvfile:
                fieldnames = ['tag_id', 'common_name', 'subcategory', 'short_common_name', 'status', 'bin_location']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for item in all_items:
                    writer.writerow({
                        'tag_id': item['tag_id'],
                        'common_name': item['common_name'],
                        'subcategory': item['subcategory'],
                        'short_common_name': item['short_common_name'],
                        'status': item['status'],
                        'bin_location': item['bin_location']
                    })
                    logger.info(f"Wrote CSV row: {item}")
        except Exception as e:
            logger.error(f"Failed to write to CSV file {CSV_FILE_PATH}: {str(e)}", exc_info=True)
            return jsonify({'error': f"Failed to write to CSV file: {str(e)}"}), 500

        # Commit new ItemMaster entries
        if new_items:
            logger.debug("Committing session after CSV write")
            try:
                session.flush()
                logger.info("Session flushed successfully after CSV write")
                session.commit()
                logger.info(f"Successfully committed {len(new_items)} new ItemMaster entries")
            except sqlalchemy.exc.DatabaseError as e:
                logger.error(f"Database error committing session: {str(e)}", exc_info=True)
                session.rollback()
                return jsonify({'error': f"Database error committing session: {str(e)}"}), 500

        logger.info(f"Successfully synced {len(synced_items)} items to CSV")
        return jsonify({'synced_items': len(synced_items)}), 200
    except Exception as e:
        logger.error(f"Uncaught exception in sync_to_pc: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
            lock_file.close()
            logger.debug("Released lock for sync_to_pc")
        if session:
            session.close()
            logger.debug("Session closed")

@tab3_bp.route('/tab/3/update_synced_status', methods=['POST'])
def update_synced_status():
    """
    Update the status of items in rfid_tags.csv to 'Ready to Rent', sync to API,
    and clear the CSV file.
    Added retry logic and timeout handling to prevent API timeouts.
    """
    session = None
    lock_file = None
    try:
        logger.debug("Entering /tab/3/update_synced_status endpoint")
        session = db.session()
        logger.info("Received request for /tab/3/update_synced_status")

        # Acquire lock to prevent concurrent CSV modifications
        lock_file = open(LOCK_FILE_PATH, 'w')
        try:
            fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            logger.debug("Acquired lock for update_synced_status")
        except BlockingIOError:
            logger.warning("Another update_synced_status operation is in progress")
            return jsonify({'error': 'Another update operation is in progress'}), 429

        if not os.path.exists(CSV_FILE_PATH):
            logger.info("No synced items found in CSV file")
            return jsonify({'error': 'No synced items found'}), 404

        if os.path.getsize(CSV_FILE_PATH) == 0:
            logger.info("CSV file is empty")
            return jsonify({'error': 'No items found in CSV file'}), 404

        logger.debug("Reading items from CSV file")
        items_to_update = []
        try:
            with open(CSV_FILE_PATH, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                required_fields = ['tag_id', 'common_name', 'bin_location', 'status']
                if not all(field in reader.fieldnames for field in required_fields):
                    missing = [field for field in required_fields if field not in reader.fieldnames]
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
                        logger.debug(f"Read CSV row: {row}")
                    except KeyError as ke:
                        logger.error(f"Missing required field in CSV row: {ke}, row: {row}")
                        return jsonify({'error': f"Missing required field in CSV row: {ke}"}), 400
        except Exception as e:
            logger.error(f"Error reading CSV file: {str(e)}", exc_info=True)
            return jsonify({'error': f"Error reading CSV file: {str(e)}"}), 500

        if not items_to_update:
            logger.info("No items found in CSV file to update")
            return jsonify({'error': 'No items found in CSV file'}), 404

        tag_ids = [item['tag_id'] for item in items_to_update]
        logger.info(f"Found {len(tag_ids)} items to update: {tag_ids}")

        logger.debug("Fetching rental_class_num from ItemMaster")
        try:
            items_in_db = session.query(ItemMaster.tag_id, ItemMaster.rental_class_num, ItemMaster.common_name, ItemMaster.bin_location)\
                .filter(ItemMaster.tag_id.in_(tag_ids))\
                .all()
            item_dict = {item.tag_id: {
                'rental_class_num': item.rental_class_num,
                'common_name': item.common_name,
                'bin_location': item.bin_location
            } for item in items_in_db}
            logger.debug(f"Fetched {len(item_dict)} items from ItemMaster for tag_ids: {list(item_dict.keys())}")
        except sqlalchemy.exc.DatabaseError as e:
            logger.error(f"Database error querying ItemMaster for tag_ids: {str(e)}", exc_info=True)
            return jsonify({'error': f"Database error querying ItemMaster: {str(e)}"}), 500

        logger.debug("Updating ItemMaster status to 'Ready to Rent'")
        try:
            updated_items = ItemMaster.query\
                .filter(ItemMaster.tag_id.in_(tag_ids))\
                .update({ItemMaster.status: 'Ready to Rent'}, synchronize_session='fetch')
            logger.info(f"Updated {updated_items} items in ItemMaster to 'Ready to Rent'")
        except sqlalchemy.exc.DatabaseError as e:
            logger.error(f"Database error updating ItemMaster status: {str(e)}", exc_info=True)
            return jsonify({'error': f"Database error updating ItemMaster: {str(e)}"}), 500

        logger.debug("Updating items via API")
        api_client = APIClient()

        # Retry decorator for API calls with exponential backoff
        @retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=4, max=10),
            retry=retry_if_exception_type((requests.exceptions.RequestException,))
        )
        def make_api_request(url, params, headers):
            return api_client._make_request(url, params=params, headers=headers)

        failed_items = []
        for item in items_to_update:
            tag_id = item['tag_id']
            db_item = item_dict.get(tag_id, {})
            logger.debug(f"Processing tag_id {tag_id}: db_item={db_item}")
            try:
                params = {'filter[eq]': f"tag_id,eq,'{tag_id}'"}
                headers = api_client.get_headers()
                existing_items = make_api_request("14223767938169344381", params, headers)
                logger.debug(f"API check for tag_id {tag_id}: found {len(existing_items)} items")
                if existing_items:
                    api_client.update_status(tag_id, 'Ready to Rent')
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
                    logger.info(f"Inserted new tag_id {tag_id} via API POST with data: {new_item}")
            except Exception as api_error:
                logger.error(f"Error updating/inserting tag_id {tag_id} in API: {str(api_error)}", exc_info=True)
                failed_items.append(tag_id)

        if failed_items:
            logger.warning(f"Failed to update {len(failed_items)} items in API: {failed_items}")
            return jsonify({'error': f"Failed to update {len(failed_items)} items in API", 'failed_items': failed_items}), 500

        logger.debug("Clearing CSV file")
        try:
            with open(CSV_FILE_PATH, 'w', newline='') as csvfile:
                fieldnames = ['tag_id', 'common_name', 'subcategory', 'short_common_name', 'status', 'bin_location']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
            logger.info("Cleared CSV file")
        except Exception as e:
            logger.error(f"Error clearing CSV file: {str(e)}", exc_info=True)
            return jsonify({'error': f"Error clearing CSV file: {str(e)}"}), 500

        logger.debug("Committing session after API updates")
        try:
            session.commit()
        except sqlalchemy.exc.DatabaseError as e:
            logger.error(f"Database error committing session: {str(e)}", exc_info=True)
            return jsonify({'error': f"Database error committing session: {str(e)}"}), 500

        logger.info(f"Updated status for {updated_items} items and cleared CSV file")
        return jsonify({'updated_items': updated_items}), 200
    except Exception as e:
        logger.error(f"Uncaught exception in update_synced_status: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
            lock_file.close()
            logger.debug("Released lock for update_synced_status")
        if session:
            session.close()
            logger.debug("Session closed")

@tab3_bp.route('/tab/3/update_status', methods=['POST'])
def update_status():
    """Update an item's status in ItemMaster and sync to API."""
    session = None
    try:
        logger.debug("Entering /tab/3/update_status endpoint")
        session = db.session()
        logger.info("Entering /tab/3/update_status route")
        data = request.get_json()
        tag_id = data.get('tag_id')
        new_status = data.get('status')

        if not tag_id or not new_status:
            logger.warning(f"Invalid input in update_status: tag_id={tag_id}, new_status={new_status}")
            return jsonify({'error': 'Tag ID and status are required'}), 400

        valid_statuses = ['Ready to Rent', 'Sold', 'Repair', 'Needs to be Inspected', 'Staged', 'Wash', 'Wet']
        if new_status not in valid_statuses:
            logger.warning(f"Invalid status value: {new_status}")
            return jsonify({'error': f'Status must be one of {", ".join(valid_statuses)}'}), 400

        logger.debug(f"Querying ItemMaster for tag_id={tag_id}")
        item = session.query(ItemMaster).filter_by(tag_id=tag_id).first()
        if not item:
            session.close()
            logger.info(f"Item not found for tag_id {tag_id}")
            return jsonify({'error': 'Item not found'}), 404

        if new_status in ['On Rent', 'Delivered']:
            session.close()
            logger.warning(f"Attempted manual update to restricted status {new_status} for tag_id {tag_id}")
            return jsonify({'error': 'Status cannot be updated to "On Rent" or "Delivered" manually'}), 400

        logger.debug(f"Updating ItemMaster status for tag_id={tag_id} to {new_status}")
        current_time = datetime.now()
        item.status = new_status
        item.date_last_scanned = current_time
        try:
            session.commit()
        except sqlalchemy.exc.DatabaseError as e:
            logger.error(f"Database error updating ItemMaster status: {str(e)}", exc_info=True)
            session.rollback()
            return jsonify({'error': f"Database error updating status: {str(e)}"}), 500

        logger.debug(f"Updating external API for tag_id={tag_id}")
        try:
            api_client = APIClient()
            api_client.update_status(tag_id, new_status)
            logger.info(f"Successfully updated API status for tag_id {tag_id}")
        except Exception as e:
            logger.error(f"Failed to update API status for tag_id {tag_id}: {str(e)}", exc_info=True)

        session.close()
        logger.info(f"Updated status for tag_id {tag_id} to {new_status} and date_last_scanned to {current_time}")
        return jsonify({'message': 'Status updated successfully'})
    except Exception as e:
        logger.error(f"Uncaught exception in update_status: {str(e)}", exc_info=True)
        if session:
            session.rollback()
            session.close()
        return jsonify({'error': str(e)}), 500

@tab3_bp.route('/tab/3/update_notes', methods=['POST'])
def update_notes():
    """Update an item's notes in ItemMaster and sync to API."""
    session = None
    try:
        logger.debug("Entering /tab/3/update_notes endpoint")
        session = db.session()
        logger.info("Entering /tab/3/update_notes route")
        data = request.get_json()
        tag_id = data.get('tag_id')
        new_notes = data.get('notes')

        if not tag_id:
            logger.warning(f"Invalid input in update_notes: tag_id={tag_id}")
            return jsonify({'error': 'Tag ID is required'}), 400

        logger.debug(f"Querying ItemMaster for tag_id={tag_id}")
        item = session.query(ItemMaster).filter_by(tag_id=tag_id).first()
        if not item:
            session.close()
            logger.info(f"Item not found for tag_id {tag_id}")
            return jsonify({'error': 'Item not found'}), 404

        logger.debug(f"Updating ItemMaster notes for tag_id={tag_id}")
        current_time = datetime.now()
        item.notes = new_notes if new_notes else None
        item.date_updated = current_time
        try:
            session.commit()
        except sqlalchemy.exc.DatabaseError as e:
            logger.error(f"Database error updating ItemMaster notes: {str(e)}", exc_info=True)
            session.rollback()
            return jsonify({'error': f"Database error updating notes: {str(e)}"}), 500

        logger.debug(f"Updating external API notes for tag_id={tag_id}")
        try:
            api_client = APIClient()
            api_client.update_notes(tag_id, new_notes if new_notes else '')
            logger.info(f"Successfully updated API notes for tag_id {tag_id}")
        except Exception as e:
            logger.error(f"Failed to update API notes for tag_id {tag_id}: {str(e)}", exc_info=True)

        session.close()
        logger.info(f"Updated notes for tag_id {tag_id} to '{new_notes}' and date_updated to {current_time}")
        return jsonify({'message': 'Notes updated successfully'})
    except Exception as e:
        logger.error(f"Uncaught exception in update_notes: {str(e)}", exc_info=True)
        if session:
            session.rollback()
            session.close()
        return jsonify({'error': str(e)}), 500

@tab3_bp.route('/tab/3/pack_resale_common_names', methods=['GET'])
def get_pack_resale_common_names():
    """Fetch distinct common names from SeedRentalClass for pack/resale bin locations."""
    try:
        logger.debug("Entering /tab/3/pack_resale_common_names endpoint")
        common_names = db.session.query(SeedRentalClass.common_name)\
            .filter(SeedRentalClass.bin_location.in_(['pack', 'resale']))\
            .distinct()\
            .all()
        common_names = [name[0] for name in common_names if name[0]]
        logger.info(f"Fetched {len(common_names)} common names from SeedRentalClass for pack/resale: {common_names}")
        return jsonify({'common_names': sorted(common_names)}), 200
    except sqlalchemy.exc.DatabaseError as e:
        logger.error(f"Database error fetching pack/resale common names: {str(e)}", exc_info=True)
        return jsonify({'error': f"Database error: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Error fetching pack/resale common names from SeedRentalClass: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500