from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db
from ..models.db_models import ItemMaster, Transaction, RentalClassMapping, UserRentalClassMapping, SeedRentalClass
from ..services.api_client import APIClient
from sqlalchemy import text, func
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
import re

# Configure logging for Tab 3
logger = logging.getLogger('tab3')
logger.setLevel(logging.DEBUG)
logger.handlers = []

tab3_log_file = '/home/tim/test_rfidpi/logs/tab3.log'
try:
    if not os.path.exists(tab3_log_file):
        open(tab3_log_file, 'a').close()
    os.chmod(tab3_log_file, 0o666)
    os.chown(tab3_log_file, pwd.getpwnam('tim').pw_uid, grp.getgrnam('tim').gr_gid)
except Exception as e:
    print(f"ERROR: Failed to set up Tab 3 log file {tab3_log_file}: {str(e)}")
    sys.stderr.write(f"ERROR: Failed to set up Tab 3 log file {tab3_log_file}: {str(e)}\n")

file_handler = logging.FileHandler(tab3_log_file)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

tab3_bp = Blueprint('tab3', __name__)

SHARED_DIR = '/home/tim/test_rfidpi/shared'
CSV_FILE_PATH = os.path.join(SHARED_DIR, 'rfid_tags.csv')
LOCK_FILE_PATH = os.path.join(SHARED_DIR, 'rfid_tags.lock')

# Ensure shared directory exists with correct permissions
if not os.path.exists(SHARED_DIR):
    logger.info(f"Creating shared directory: {SHARED_DIR}")
    os.makedirs(SHARED_DIR, mode=0o770)
    os.chown(SHARED_DIR, pwd.getpwnam('tim').pw_uid, grp.getgrnam('tim').gr_gid)

# Log deployment version
logger.info("Deployed tab3.py version: 2025-05-28-v65")

# Helper function to normalize common_name by removing suffixes like (G1), (G2)
def normalize_common_name(name):
    if not name:
        return name
    # Remove suffixes like (G1), (G2), etc.
    return re.sub(r'\s*\(G[0-9]+\)$', '', name).strip()

@tab3_bp.route('/tab/3')
def tab3_view():
    # Log entry into endpoint
    logger.debug("Entering /tab/3 endpoint")
    session = None
    try:
        session = db.session()
        logger.info("Successfully created new session for tab3")

        # Test database connection
        session.execute(text("SELECT 1"))
        logger.info("Database connection test successful")

        # Debug: Check all statuses in id_item_master
        status_query = """
            SELECT DISTINCT status
            FROM id_item_master
            WHERE status IS NOT NULL
        """
        status_result = session.execute(text(status_query))
        statuses = [row[0] for row in status_result.fetchall()]
        logger.info(f"All statuses in id_item_master: {statuses}")

        # Debug: Count items by status
        count_query = """
            SELECT status, COUNT(*)
            FROM id_item_master
            WHERE TRIM(COALESCE(status, '')) IN ('Repair', 'Needs to be Inspected', 'Wash', 'Wet', 'On Rent', 'Ready to Rent')
            GROUP BY status
        """
        count_result = session.execute(text(count_query))
        status_counts = {row[0]: row[1] for row in count_result.fetchall()}
        logger.info(f"Status counts: {status_counts}")

        # Get query parameters
        common_name_filter = request.args.get('common_name', '').lower()
        date_filter = request.args.get('date_last_scanned', '')
        sort = request.args.get('sort', 'date_last_scanned_desc')
        page = int(request.args.get('page', 1))
        per_page = 20

        # Define in-service statuses (exact match to database)
        in_service_statuses = ['Repair', 'Needs to be Inspected', 'Wash', 'Wet']
        all_statuses = in_service_statuses + ['On Rent', 'Ready to Rent']

        # Construct IN clause manually to avoid tuple conversion issue
        in_service_statuses_sql = ', '.join([f"'{status}'" for status in in_service_statuses])
        all_statuses_sql = ', '.join([f"'{status}'" for status in all_statuses])

        # Query for summary data (parent layer)
        # Normalize common_name by removing suffixes like (G1), (G2)
        summary_query = f"""
            SELECT 
                COALESCE(rental_class_num, '') AS rental_class_id,
                REGEXP_REPLACE(common_name, '\s*\(G[0-9]+\)$', '') AS common_name,
                COUNT(CASE WHEN TRIM(COALESCE(status, '')) IN ({in_service_statuses_sql}) THEN 1 END) AS number_in_service,
                COUNT(CASE WHEN TRIM(COALESCE(status, '')) = 'On Rent' THEN 1 END) AS number_on_rent,
                COUNT(CASE WHEN TRIM(COALESCE(status, '')) = 'Ready to Rent' THEN 1 END) AS number_ready_to_rent,
                GROUP_CONCAT(DISTINCT CASE WHEN TRIM(COALESCE(status, '')) IN ({in_service_statuses_sql}) THEN status END) AS statuses
            FROM id_item_master
            WHERE TRIM(COALESCE(status, '')) IN ({all_statuses_sql})
        """
        params = {}
        
        if common_name_filter:
            summary_query += " AND LOWER(REGEXP_REPLACE(common_name, '\s*\(G[0-9]+\)$', '')) LIKE :common_name_filter"
            params['common_name_filter'] = f'%{common_name_filter}%'
        
        summary_query += " GROUP BY COALESCE(rental_class_num, ''), REGEXP_REPLACE(common_name, '\s*\(G[0-9]+\)$', '')"
        
        # Apply sorting for summary
        if sort == 'date_last_scanned_asc':
            summary_query += " ORDER BY MIN(date_last_scanned) ASC, REGEXP_REPLACE(common_name, '\s*\(G[0-9]+\)$', '') ASC"
        else:
            summary_query += " ORDER BY MIN(date_last_scanned) DESC, REGEXP_REPLACE(common_name, '\s*\(G[0-9]+\)$', '') ASC"

        summary_query += " LIMIT :limit OFFSET :offset"
        params['limit'] = per_page
        params['offset'] = (page - 1) * per_page

        logger.debug(f"Executing summary query: {summary_query} with params: {params}")
        summary_result = session.execute(text(summary_query), params)
        summary_rows = summary_result.fetchall()
        logger.info(f"Summary query returned {len(summary_rows)} groups: {[(row[0], row[1], row[2]) for row in summary_rows]}")

        # Structure summary groups
        summary_groups = []
        for row in summary_rows:
            summary_groups.append({
                'rental_class_id': row[0] or 'N/A',
                'common_name': row[1] or 'Unknown',
                'number_in_service': row[2] or 0,
                'number_on_rent': row[3] or 0,
                'number_ready_to_rent': row[4] or 0,
                'statuses': row[5].split(',') if row[5] else [],
                'item_list': []  # Renamed from 'items' to avoid conflict with dict.items()
            })

        # Query detailed items for in-service statuses
        detail_query = f"""
            SELECT 
                tag_id, 
                common_name, 
                status, 
                bin_location, 
                last_contract_num, 
                date_last_scanned, 
                rental_class_num, 
                notes
            FROM id_item_master
            WHERE TRIM(COALESCE(status, '')) IN ({in_service_statuses_sql})
        """
        detail_params = {}
        if common_name_filter:
            detail_query += " AND LOWER(REGEXP_REPLACE(common_name, '\s*\(G[0-9]+\)$', '')) LIKE :common_name_filter"
            detail_params['common_name_filter'] = f'%{common_name_filter}%'
        if date_filter:
            try:
                date = datetime.strptime(date_filter, '%Y-%m-%d')
                detail_query += " AND DATE(date_last_scanned) = :date_filter"
                detail_params['date_filter'] = date
            except ValueError:
                logger.warning(f"Invalid date format for date_last_scanned filter: {date_filter}")

        if sort == 'date_last_scanned_asc':
            detail_query += " ORDER BY date_last_scanned ASC, LOWER(REGEXP_REPLACE(common_name, '\s*\(G[0-9]+\)$', '')) ASC"
        else:
            detail_query += " ORDER BY date_last_scanned DESC, LOWER(REGEXP_REPLACE(common_name, '\s*\(G[0-9]+\)$', '')) ASC"

        logger.debug(f"Executing detail query: {detail_query} with params: {detail_params}")
        detail_result = session.execute(text(detail_query), detail_params)
        detail_rows = detail_result.fetchall()
        logger.info(f"Detailed query returned {len(detail_rows)} items: {[(row[0], row[1], row[2]) for row in detail_rows]}")

        # Structure detailed items
        items_in_service = [
            {
                'tag_id': row[0],
                'common_name': row[1],
                'common_name_normalized': normalize_common_name(row[1]),
                'status': row[2],
                'bin_location': row[3] or 'N/A',
                'last_contract_num': row[4] or 'N/A',
                'date_last_scanned': row[5].isoformat() if row[5] else 'N/A',
                'rental_class_num': str(row[6]).strip().upper() if row[6] else 'N/A',
                'notes': row[7] or ''
            }
            for row in detail_rows
        ]

        # Fetch transaction data
        tag_ids = [item['tag_id'] for item in items_in_service]
        transaction_data = {}
        if tag_ids:
            logger.debug(f"Fetching transactions for tag_ids: {tag_ids}")
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
            logger.info(f"Fetched {len(transactions)} transactions")

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

        # Assign detailed items to summary groups using normalized common_name
        unmatched_items = []
        for item in items_in_service:
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

            item_details = {
                'tag_id': item['tag_id'],
                'common_name': item['common_name'],
                'status': item['status'],
                'bin_location': item['bin_location'],
                'last_contract_num': item['last_contract_num'],
                'date_last_scanned': item['date_last_scanned'],
                'rental_class_id': item['rental_class_num'],
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
            }

            # Find matching summary group using normalized common_name
            matched = False
            for group in summary_groups:
                if group['rental_class_id'] == item['rental_class_num'] and normalize_common_name(group['common_name']) == item['common_name_normalized']:
                    group['item_list'].append(item_details)
                    # Increment number_in_service to reflect the actual count
                    group['number_in_service'] = len(group['item_list'])
                    # Update statuses
                    if item['status'] not in group['statuses']:
                        group['statuses'].append(item['status'])
                    matched = True
                    break
            if not matched:
                logger.debug(f"Unmatched item: tag_id={item['tag_id']}, common_name={item['common_name']}, rental_class_num={item['rental_class_num']}")
                unmatched_items.append(item)

        # Debug: Log groups after assignment but before filtering
        logger.debug(f"After assignment - Summary groups: {len(summary_groups)}")
        for group in summary_groups:
            logger.debug(f"Group: rental_class_id={group['rental_class_id']}, common_name={group['common_name']}, number_in_service={group['number_in_service']}, items={len(group['item_list'])}")

        # Filter out groups with no in-service items
        summary_groups = [g for g in summary_groups if g['number_in_service'] > 0]

        # Debug log data structure
        logger.debug(f"After filtering - Summary groups: {len(summary_groups)}")
        for group in summary_groups:
            logger.debug(f"Final group: rental_class_id={group['rental_class_id']}, common_name={group['common_name']}, items={len(group['item_list'])}, statuses={group['statuses']}")

        # Debug: Log unmatched items
        if unmatched_items:
            logger.debug(f"Unmatched items: {[(item['tag_id'], item['common_name'], item['rental_class_num']) for item in unmatched_items]}")

        session.commit()
        logger.info("Rendering Tab 3 template")
        return render_template(
            'tab3.html',
            summary_groups=summary_groups,
            common_name_filter=common_name_filter,
            date_filter=date_filter,
            sort=sort,
            cache_bust=int(datetime.now().timestamp())
        )
    except Exception as e:
        logger.error(f"Error rendering Tab 3: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return render_template(
            'tab3.html',
            summary_groups=[],
            common_name_filter='',
            date_filter='',
            sort='date_last_scanned_desc',
            cache_bust=int(datetime.now().timestamp())
        )
    finally:
        if session:
            session.close()

@tab3_bp.route('/tab/3/csv_contents', methods=['GET'])
def get_csv_contents():
    # Fetch and return CSV contents
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
    # Remove an item from the CSV
    lock_file = None
    try:
        logger.debug("Entering /tab/3/remove_csv_item endpoint")
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

        items = []
        with open(CSV_FILE_PATH, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames
            for row in reader:
                if row['tag_id'] != tag_id:
                    items.append(row)

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
    # Sync items to CSV for printing
    session = None
    lock_file = None
    try:
        logger.debug("Entering /tab/3/sync_to_pc endpoint")
        session = db.session()
        logger.info("Entering /tab/3/sync_to_pc route")

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

        # Read existing CSV
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

        synced_items = []
        existing_tag_ids = csv_tag_ids.copy()

        # Query ItemMaster for items
        logger.debug("Querying ItemMaster for existing items")
        try:
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

        # Generate new items if needed
        new_items = []
        if len(synced_items) < quantity:
            remaining_quantity = quantity - len(synced_items)
            logger.info(f"Generating {remaining_quantity} new items for common_name={common_name}")

            seed_entry = session.query(SeedRentalClass)\
                .filter(SeedRentalClass.common_name == common_name,
                        SeedRentalClass.bin_location.in_(['pack', 'resale']))\
                .first()
            if not seed_entry:
                logger.warning(f"No SeedRentalClass entry found for common_name={common_name} and bin_location in ['pack', 'resale']")
                return jsonify({'error': f"No SeedRentalClass entry found for common name '{common_name}'"}), 404

            rental_class_num = seed_entry.rental_class_id
            bin_location = seed_entry.bin_location

            for i in range(remaining_quantity):
                max_tag_id = session.query(func.max(ItemMaster.tag_id))\
                    .filter(ItemMaster.tag_id.startswith('425445'))\
                    .scalar()

                new_num = 1
                if max_tag_id and len(max_tag_id) == 24 and max_tag_id.startswith('425445'):
                    try:
                        incremental_part = int(max_tag_id[6:], 16)
                        new_num = incremental_part + 1
                    except ValueError:
                        logger.warning(f"Invalid incremental part in max_tag_id: {max_tag_id}, starting from 1")

                while True:
                    incremental_hex = format(new_num, 'x').zfill(18)
                    tag_id = f"425445{incremental_hex}"
                    if tag_id not in existing_tag_ids:
                        break
                    new_num += 1

                if len(tag_id) != 24:
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

                new_item = ItemMaster(
                    tag_id=tag_id,
                    common_name=common_name,
                    rental_class_num=rental_class_num,
                    bin_location=bin_location,
                    status='Ready to Rent',
                    date_created=datetime.now(),
                    date_updated=datetime.now()
                )
                session.add(new_item)
                new_items.append(new_item)

        if len(synced_items) > quantity:
            synced_items = synced_items[:quantity]

        # Map rental class details
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

        for item in synced_items:
            mapping = mappings_dict.get(str(item['rental_class_num']).strip().upper() if item['rental_class_num'] else '', {})
            item['subcategory'] = mapping.get('subcategory', 'Unknown')
            item['short_common_name'] = mapping.get('short_common_name', item['common_name'])

        # Write to CSV
        all_items = [item for item in existing_items if item['tag_id'] not in {i['tag_id'] for i in synced_items}]
        all_items.extend(synced_items)

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

        if new_items:
            session.flush()
            session.commit()

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
        if session:
            session.close()

@tab3_bp.route('/tab/3/update_synced_status', methods=['POST'])
def update_synced_status():
    # Update synced items' status to Ready to Rent
    session = None
    lock_file = None
    try:
        logger.debug("Entering /tab/3/update_synced_status endpoint")
        session = db.session()
        logger.info("Received request for /tab/3/update_synced_status")

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

        logger.debug("Checking CSV file permissions")
        if not os.access(CSV_FILE_PATH, os.R_OK | os.W_OK):
            logger.error(f"CSV file {CSV_FILE_PATH} is not readable/writable")
            return jsonify({'error': f"CSV file {CSV_FILE_PATH} is not readable/writable"}), 500

        # Read CSV items
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

        # Fetch ItemMaster data
        logger.debug("Fetching items from ItemMaster")
        items_in_db = session.query(ItemMaster.tag_id, ItemMaster.rental_class_num, ItemMaster.common_name, ItemMaster.bin_location)\
            .filter(ItemMaster.tag_id.in_(tag_ids))\
            .all()
        item_dict = {item.tag_id: {
            'rental_class_num': item.rental_class_num,
            'common_name': item.common_name,
            'bin_location': item.bin_location
        } for item in items_in_db}

        # Update ItemMaster status
        logger.debug("Updating ItemMaster status to 'Ready to Rent'")
        updated_items = ItemMaster.query\
            .filter(ItemMaster.tag_id.in_(tag_ids))\
            .update({ItemMaster.status: 'Ready to Rent'}, synchronize_session='fetch')
        session.flush()
        logger.info(f"Updated {updated_items} items in ItemMaster")

        # Update API
        api_client = APIClient()
        failed_items = []
        for item in items_to_update:
            tag_id = item['tag_id']
            db_item = item_dict.get(tag_id, {})
            try:
                params = {'filter[eq]': f"tag_id,eq,'{tag_id}'"}
                existing_items = api_client._make_request("14223767938169344381", params)
                if existing_items:
                    api_client.update_status(tag_id, 'Ready to Rent')
                    logger.debug(f"Updated status for tag_id {tag_id} in API")
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
                    logger.debug(f"Inserted new item for tag_id {tag_id} in API")
            except Exception as api_error:
                logger.error(f"Error updating/inserting tag_id {tag_id} in API: {str(api_error)}", exc_info=True)
                failed_items.append(tag_id)

        if failed_items:
            logger.warning(f"Failed to update {len(failed_items)} items in API: {failed_items}")
            session.rollback()
            return jsonify({'error': f"Failed to update {len(failed_items)} items in API", 'failed_items': failed_items}), 500

        # Clear CSV
        logger.debug("Clearing CSV file")
        try:
            with open(CSV_FILE_PATH, 'w', newline='') as csvfile:
                fieldnames = ['tag_id', 'common_name', 'subcategory', 'short_common_name', 'status', 'bin_location']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
            logger.info("CSV file cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing CSV file: {str(e)}", exc_info=True)
            session.rollback()
            return jsonify({'error': f"Error clearing CSV file: {str(e)}"}), 500

        session.commit()
        logger.info(f"Completed update_synced_status: Updated {updated_items} items and cleared CSV file")
        return jsonify({'updated_items': updated_items, 'message': 'Status updated successfully'}), 200
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

@tab3_bp.route('/tab/3/update_status', methods=['POST'])
def update_status():
    # Update individual item status
    session = None
    try:
        logger.debug("Entering /tab/3/update_status endpoint")
        session = db.session()
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

        item = session.query(ItemMaster).filter_by(tag_id=tag_id).first()
        if not item:
            logger.info(f"Item not found for tag_id {tag_id}")
            return jsonify({'error': 'Item not found'}), 404

        if new_status in ['On Rent', 'Delivered']:
            logger.warning(f"Attempted manual update to restricted status {new_status} for tag_id {tag_id}")
            return jsonify({'error': 'Status cannot be updated to "On Rent" or "Delivered" manually'}), 400

        item.status = new_status
        item.date_last_scanned = datetime.now()
        session.commit()

        try:
            api_client = APIClient()
            api_client.update_status(tag_id, new_status)
        except Exception as e:
            logger.error(f"Failed to update API status for tag_id {tag_id}: {str(e)}", exc_info=True)

        return jsonify({'message': 'Status updated successfully'})
    except Exception as e:
        logger.error(f"Uncaught exception in update_status: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab3_bp.route('/tab/3/update_notes', methods=['POST'])
def update_notes():
    # Update individual item notes
    session = None
    try:
        logger.debug("Entering /tab/3/update_notes endpoint")
        session = db.session()
        data = request.get_json()
        tag_id = data.get('tag_id')
        new_notes = data.get('notes')

        if not tag_id:
            logger.warning(f"Invalid input in update_notes: tag_id={tag_id}")
            return jsonify({'error': 'Tag ID is required'}), 400

        item = session.query(ItemMaster).filter_by(tag_id=tag_id).first()
        if not item:
            logger.info(f"Item not found for tag_id {tag_id}")
            return jsonify({'error': 'Item not found'}), 404

        item.notes = new_notes if new_notes else ''
        item.date_updated = datetime.now()
        session.commit()

        try:
            api_client = APIClient()
            api_client.update_notes(tag_id, new_notes if new_notes else '')
        except Exception as e:
            logger.error(f"Failed to update API notes for tag_id {tag_id}: {str(e)}", exc_info=True)

        return jsonify({'message': 'Notes updated successfully'})
    except Exception as e:
        logger.error(f"Uncaught exception in update_notes: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab3_bp.route('/tab/3/pack_resale_common_names', methods=['GET'])
def get_pack_resale_common_names():
    # Fetch common names for pack/resale
    session = None
    try:
        logger.debug("Entering /tab/3/pack_resale_common_names endpoint")
        session = db.session()
        common_names = session.query(SeedRentalClass.common_name)\
            .filter(SeedRentalClass.bin_location.in_(['pack', 'resale']))\
            .distinct()\
            .order_by(SeedRentalClass.common_name.asc())\
            .all()
        common_names = [name[0] for name in common_names if name[0]]
        logger.info(f"Fetched {len(common_names)} common names from SeedRentalClass for pack/resale")
        return jsonify({'common_names': common_names}), 200
    except Exception as e:
        logger.error(f"Error fetching common names: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()