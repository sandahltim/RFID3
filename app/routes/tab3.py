# app/routes/tab3.py
# tab3.py version: 2025-07-10-v87
from flask import Blueprint, render_template, request, jsonify, current_app, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from .. import db, cache
from ..models.db_models import ItemMaster, Transaction, RentalClassMapping, UserRentalClassMapping, SeedRentalClass
from ..services.api_client import APIClient
from sqlalchemy import text, func, or_
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
import json
from urllib.parse import unquote

# Configure logging for Tab 3
logger = logging.getLogger('tab3')
logger.setLevel(logging.INFO)
logger.handlers = []

tab3_log_file = '/home/tim/RFID3/logs/rfid_dashboard.log'
try:
    if not os.path.exists(tab3_log_file):
        open(tab3_log_file, 'a').close()
    os.chmod(tab3_log_file, 0o666)
    os.chown(tab3_log_file, pwd.getpwnam('tim').pw_uid, grp.getgrnam('tim').gr_gid)
except Exception as e:
    print(f"ERROR: Failed to set up Tab 3 log file {tab3_log_file}: {str(e)}")
    sys.stderr.write(f"ERROR: Failed to set up Tab 3 log file {tab3_log_file}: {str(e)}\n")

file_handler = logging.FileHandler(tab3_log_file)
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

tab3_bp = Blueprint('tab3', __name__)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

SHARED_DIR = '/home/tim/RFID3/shared'
CSV_FILE_PATH = os.path.join(SHARED_DIR, 'rfid_tags.csv')
LOCK_FILE_PATH = os.path.join(SHARED_DIR, 'rfid_tags.lock')

# Ensure shared directory exists with correct permissions
if not os.path.exists(SHARED_DIR):
    logger.info(f"Creating shared directory: {SHARED_DIR}")
    os.makedirs(SHARED_DIR, mode=0o770)
    os.chown(SHARED_DIR, pwd.getpwnam('tim').pw_uid, grp.getgrnam('tim').gr_gid)

# Log deployment version
logger.info("Deployed tab3.py version: 2025-07-10-v87")

# Define crew categories
TENT_CATEGORIES = ['Frame Tent Tops', 'Pole Tent Tops', 'Tent Crates', 'Sidewall']
LINEN_CATEGORIES = ['Napkins', 'Rectangle Linen', 'Round Linen', 'Skirt', 'Spandex']
SERVICE_DEPT_CATEGORIES = ['Other']

# Valid values for quality
VALID_QUALITIES = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', '']

# Helper function to normalize common_name
def normalize_common_name(name):
    """Normalize common name by removing trailing (GXXX) pattern."""
    if not name:
        return name
    return re.sub(r'\s*\(G[0-9]+\)$', '', name).strip()

# Helper function to normalize rental_class_id
def normalize_rental_class_id(rental_class_id):
    """Normalize rental class ID to uppercase and strip whitespace."""
    if not rental_class_id:
        return 'N/A'
    return str(rental_class_id).strip().upper()

# Helper function to determine crew based on category
def get_crew_for_category(category):
    """Assign crew based on category."""
    if category in TENT_CATEGORIES:
        return 'Tent Crew'
    elif category in LINEN_CATEGORIES:
        return 'Linen Crew'
    else:
        return 'Service Dept'

# Manual Redis caching functions
def cache_get(key):
    """Retrieve cached data from Redis."""
    try:
        cached_data = cache.get(key)
        if cached_data:
            logger.debug(f"Cache hit for key: {key}")
            return json.loads(cached_data)
        logger.debug(f"Cache miss for key: {key}")
        return None
    except Exception as e:
        logger.error(f"Error accessing Redis cache for key {key}: {str(e)}", exc_info=True)
        return None

def cache_set(key, value, timeout=60):
    """Store data in Redis cache with expiration."""
    try:
        cache.set(key, json.dumps(value), ex=timeout)
        logger.debug(f"Cache set for key: {key}, timeout: {timeout}s")
    except Exception as e:
        logger.error(f"Error setting Redis cache for key {key}: {str(e)}", exc_info=True)

@tab3_bp.route('/tab/3')
def tab3_view():
    """Render Tab 3 view with items in service."""
    logger.debug("Entering /tab/3 endpoint at %s", datetime.now())
    session = None
    try:
        session = db.session()
        logger.info("Successfully created new session for tab3")

        # Test database connection
        session.execute(text("SELECT 1"))
        logger.debug("Database connection test successful")

        # Debug: Check all statuses in id_item_master
        status_query = """
            SELECT DISTINCT COALESCE(status, 'NULL') AS status
            FROM id_item_master
        """
        status_result = session.execute(text(status_query))
        statuses = [row[0] for row in status_result.fetchall()]
        logger.debug(f"All statuses in id_item_master: {statuses}")

        # Debug: Check all qualities in id_item_master
        quality_query = """
            SELECT DISTINCT COALESCE(quality, 'NULL') AS quality
            FROM id_item_master
        """
        quality_result = session.execute(text(quality_query))
        qualities = [row[0] for row in quality_result.fetchall()]
        logger.debug(f"All qualities in id_item_master: {qualities}")

        # Get query parameters
        common_name_filter = request.args.get('common_name', '').lower()
        date_filter = request.args.get('date_last_scanned', '')
        sort = request.args.get('sort', 'date_last_scanned_desc')
        page = int(request.args.get('page', 1))
        per_page = 20
        crew_filter = request.args.get('crew', '')

        # Define in-service statuses
        in_service_statuses = ['Repair', 'Needs to be Inspected', 'Wash', 'Wet']
        all_statuses = in_service_statuses + ['On Rent', 'Ready to Rent']
        in_service_statuses_sql = ', '.join([f"'{status}'" for status in in_service_statuses])
        all_statuses_sql = ', '.join([f"'{status}'" for status in all_statuses])

        # Cache key for mappings
        cache_key = 'rental_class_mappings'
        mappings_dict = cache_get(cache_key)
        if mappings_dict is None:
            base_mappings = session.query(RentalClassMapping).all()
            user_mappings = session.query(UserRentalClassMapping).all()
            mappings_dict = {normalize_rental_class_id(m.rental_class_id): {
                'category': m.category,
                'subcategory': m.subcategory,
                'short_common_name': m.short_common_name or 'N/A'
            } for m in base_mappings}
            for um in user_mappings:
                normalized_id = normalize_rental_class_id(um.rental_class_id)
                mappings_dict[normalized_id] = {
                    'category': um.category,
                    'subcategory': um.subcategory,
                    'short_common_name': um.short_common_name or 'N/A'
                }
            cache_set(cache_key, mappings_dict, timeout=3600)
            logger.debug("Cached rental_class_mappings")

        # Fetch all rental_class_num values for in-service items
        rental_class_query = f"""
            SELECT DISTINCT COALESCE(rental_class_num, '') AS rental_class_id
            FROM id_item_master
            WHERE LOWER(TRIM(COALESCE(status, ''))) IN ({', '.join([f"'{status.lower()}'" for status in in_service_statuses])})
        """
        rental_class_result = session.execute(text(rental_class_query))
        in_service_rental_classes = [row[0] for row in rental_class_result.fetchall()]
        logger.debug(f"In-service rental_class_num values: {in_service_rental_classes}")

        # Summary query with crew grouping
        summary_query = f"""
            SELECT 
                COALESCE(i.rental_class_num, '') AS rental_class_id,
                REGEXP_REPLACE(i.common_name, '\s*\(G[0-9]+\)$', '') AS common_name,
                COUNT(CASE WHEN LOWER(TRIM(COALESCE(i.status, ''))) IN ({', '.join([f"'{status.lower()}'" for status in in_service_statuses])}) THEN 1 END) AS number_in_service,
                COUNT(CASE WHEN LOWER(TRIM(COALESCE(i.status, ''))) = 'on rent' THEN 1 END) AS number_on_rent,
                COUNT(CASE WHEN LOWER(TRIM(COALESCE(i.status, ''))) = 'ready to rent' THEN 1 END) AS number_ready_to_rent,
                GROUP_CONCAT(DISTINCT CASE WHEN LOWER(TRIM(COALESCE(i.status, ''))) IN ({', '.join([f"'{status.lower()}'" for status in in_service_statuses])}) THEN i.status END) AS statuses,
                COALESCE(u.category, r.category, 'Other') AS category
            FROM id_item_master i
            LEFT JOIN user_rental_class_mappings u ON i.rental_class_num = u.rental_class_id
            LEFT JOIN rental_class_mappings r ON i.rental_class_num = r.rental_class_id
            WHERE LOWER(TRIM(COALESCE(i.status, ''))) IN ({', '.join([f"'{status.lower()}'" for status in all_statuses])})
        """
        params = {}
        if common_name_filter:
            summary_query += " AND LOWER(REGEXP_REPLACE(i.common_name, '\s*\(G[0-9]+\)$', '')) LIKE :common_name_filter"
            params['common_name_filter'] = f'%{common_name_filter}%'
        if crew_filter:
            crew_categories = TENT_CATEGORIES if crew_filter == 'Tent Crew' else LINEN_CATEGORIES if crew_filter == 'Linen Crew' else SERVICE_DEPT_CATEGORIES
            if crew_filter == 'Service Dept':
                summary_query += " AND (COALESCE(u.category, r.category, 'Other') NOT IN :tent_categories AND COALESCE(u.category, r.category, 'Other') NOT IN :linen_categories)"
                params['tent_categories'] = tuple(TENT_CATEGORIES)
                params['linen_categories'] = tuple(LINEN_CATEGORIES)
            else:
                summary_query += " AND COALESCE(u.category, r.category, 'Other') IN :crew_categories"
                params['crew_categories'] = tuple(crew_categories)
        summary_query += " GROUP BY COALESCE(i.rental_class_num, ''), REGEXP_REPLACE(i.common_name, '\s*\(G[0-9]+\)$', ''), COALESCE(u.category, r.category, 'Other')"
        summary_query += " ORDER BY MIN(i.date_last_scanned) DESC, REGEXP_REPLACE(i.common_name, '\s*\(G[0-9]+\)$', '') ASC"
        logger.debug(f"Executing summary query: {summary_query} with params: {params}")
        summary_result = session.execute(text(summary_query), params)
        summary_rows = summary_result.fetchall()
        logger.info(f"Summary query returned {len(summary_rows)} groups")

        # Structure summary groups by crew
        crew_groups = {
            'Tent Crew': [],
            'Linen Crew': [],
            'Service Dept': []
        }
        rental_class_to_group = {}
        for row in summary_rows:
            category = row[6] or 'Other'
            crew = get_crew_for_category(category)
            group = {
                'rental_class_id': row[0] or 'N/A',
                'common_name': row[1] or 'Unknown',
                'number_in_service': row[2] or 0,
                'number_on_rent': row[3] or 0,
                'number_ready_to_rent': row[4] or 0,
                'statuses': row[5].split(',') if row[5] else [],
                'item_list': [],
                'category': category,
                'crew': crew
            }
            crew_groups[crew].append(group)
            rental_class_to_group[group['rental_class_id']] = group

        # Detail query
        detail_query = f"""
            SELECT 
                i.tag_id, 
                i.common_name, 
                i.status, 
                i.bin_location, 
                i.last_contract_num, 
                i.date_last_scanned, 
                i.rental_class_num, 
                i.notes, 
                COALESCE(u.category, r.category, 'Other') AS category,
                i.quality
            FROM id_item_master i
            LEFT JOIN user_rental_class_mappings u ON i.rental_class_num = u.rental_class_id
            LEFT JOIN rental_class_mappings r ON i.rental_class_num = r.rental_class_id
            WHERE LOWER(TRIM(COALESCE(i.status, ''))) IN ({', '.join([f"'{status.lower()}'" for status in in_service_statuses])})
        """
        detail_params = {}
        if common_name_filter:
            detail_query += " AND LOWER(REGEXP_REPLACE(i.common_name, '\s*\(G[0-9]+\)$', '')) LIKE :common_name_filter"
            detail_params['common_name_filter'] = f'%{common_name_filter}%'
        if crew_filter:
            if crew_filter == 'Service Dept':
                detail_query += " AND (COALESCE(u.category, r.category, 'Other') NOT IN :tent_categories AND COALESCE(u.category, r.category, 'Other') NOT IN :linen_categories)"
                detail_params['tent_categories'] = tuple(TENT_CATEGORIES)
                detail_params['linen_categories'] = tuple(LINEN_CATEGORIES)
            else:
                detail_query += " AND COALESCE(u.category, r.category, 'Other') IN :crew_categories"
                detail_params['crew_categories'] = tuple(crew_categories)
        if date_filter:
            try:
                date = datetime.strptime(date_filter, '%Y-%m-%d')
                detail_query += " AND DATE(i.date_last_scanned) = :date_filter"
                detail_params['date_filter'] = date
            except ValueError:
                logger.warning(f"Invalid date format: {date_filter}")
        detail_query += f" ORDER BY i.date_last_scanned {'ASC' if sort == 'date_last_scanned_asc' else 'DESC'}, LOWER(REGEXP_REPLACE(i.common_name, '\s*\(G[0-9]+\)$', '')) ASC"
        detail_query += " LIMIT :limit OFFSET :offset"
        detail_params['limit'] = per_page
        detail_params['offset'] = (page - 1) * per_page
        logger.debug(f"Executing detail query: {detail_query} with params: {detail_params}")
        detail_result = session.execute(text(detail_query), detail_params)
        detail_rows = detail_result.fetchall()
        logger.info(f"Detailed query returned {len(detail_rows)} items")

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
                'rental_class_num': normalize_rental_class_id(row[6]),
                'notes': row[7] or '',
                'category': row[8] or 'Other',
                'quality': row[9] or 'N/A'
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
            logger.debug(f"Fetched {len(transactions)} transactions")

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
                    'last_transaction_scan_date': t.scan_date.isoformat() if t.scan_date else 'N/A'
                }

        # Assign detailed items to summary groups
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
                'quality': item['quality'],
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

            group = rental_class_to_group.get(item['rental_class_num'])
            if group:
                group['item_list'].append(item_details)
                if item['status'] not in group['statuses']:
                    group['statuses'].append(item['status'])
                logger.debug(f"Updated existing group: rental_class_id={item['rental_class_num']}, common_name={item['common_name']}")
            else:
                unmatched_items.append(item_details)
                logger.debug(f"Unmatched item: tag_id={item['tag_id']}, common_name={item['common_name']}")

        # Add unmatched items to Service Dept
        for item in unmatched_items:
            crew = get_crew_for_category(item['category'])
            new_group = {
                'rental_class_id': item['rental_class_id'],
                'common_name': item['common_name'],
                'number_in_service': 1,
                'number_on_rent': 0,
                'number_ready_to_rent': 0,
                'statuses': [item['status']],
                'item_list': [item],
                'category': item['category'],
                'crew': crew
            }
            crew_groups[crew].append(new_group)
            rental_class_to_group[item['rental_class_id']] = new_group
            logger.debug(f"Created new group for unmatched item: rental_class_id={item['rental_class_id']}, common_name={item['common_name']}, crew={crew}")

        # Filter out groups with no in-service items
        for crew in crew_groups:
            crew_groups[crew] = [g for g in crew_groups[crew] if g['number_in_service'] > 0]

        # Apply pagination after filtering
        all_groups = []
        for crew in ['Tent Crew', 'Linen Crew', 'Service Dept']:
            all_groups.extend(crew_groups[crew])
        total_groups = len(all_groups)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        summary_groups = all_groups[start_idx:end_idx]

        # Debug log data structure
        logger.debug(f"After filtering and pagination - Total groups: {total_groups}")
        for crew, groups in crew_groups.items():
            logger.debug(f"{crew}: {len(groups)} groups")
            for group in groups:
                logger.debug(f"Group: rental_class_id={group['rental_class_id']}, common_name={group['common_name']}, items={len(group['item_list'])}, statuses={group['statuses']}, crew={group['crew']}")

        # Fetch common names for dropdown
        common_names = session.query(SeedRentalClass.common_name)\
            .filter(SeedRentalClass.bin_location.in_(['pack', 'resale']))\
            .distinct()\
            .order_by(SeedRentalClass.common_name.asc())\
            .all()
        common_names = [name[0] for name in common_names if name[0]]

        session.commit()
        logger.info("Rendering Tab 3 template")
        return render_template(
            'tab3.html',
            crew_groups=crew_groups,
            common_name_filter=common_name_filter,
            date_filter=date_filter,
            sort=sort,
            crew_filter=crew_filter,
            total_groups=total_groups,
            current_page=page,
            per_page=per_page,
            common_names=common_names,
            cache_bust=int(datetime.now().timestamp())
        )
    except Exception as e:
        logger.error(f"Error rendering Tab 3: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return render_template(
            'tab3.html',
            crew_groups={'Tent Crew': [], 'Linen Crew': [], 'Service Dept': []},
            common_name_filter='',
            date_filter='',
            sort='date_last_scanned_desc',
            crew_filter='',
            total_groups=0,
            current_page=1,
            per_page=20,
            common_names=[],
            cache_bust=int(datetime.now().timestamp())
        )
    finally:
        if session:
            session.close()

@tab3_bp.route('/tab/3/common_names')
def tab3_common_names():
    """Fetch common names for a rental class with manual Redis caching."""
    logger.debug("Entering /tab/3/common_names endpoint at %s", datetime.now())
    session = None
    try:
        session = db.session()
        rental_class_id = request.args.get('rental_class_id', '')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))

        if not rental_class_id:
            logger.warning("Missing rental_class_id parameter")
            return jsonify({'error': 'rental_class_id is required'}), 400

        # Validate rental_class_id
        normalized_rental_class_id = normalize_rental_class_id(rental_class_id)
        logger.debug(f"Normalized rental_class_id: {normalized_rental_class_id}")

        # Check cache
        cache_key = f"tab3_common_names_{normalized_rental_class_id}_{page}_{per_page}"
        cached_data = cache_get(cache_key)
        if cached_data:
            logger.info(f"Returning cached data for {cache_key}")
            return jsonify(cached_data), 200

        # Query for common names under the rental class
        query = """
            SELECT 
                REGEXP_REPLACE(i.common_name, '\s*\(G[0-9]+\)$', '') AS name,
                COUNT(*) AS on_contracts,
                COUNT(*) AS total_items_inventory
            FROM id_item_master i
            WHERE COALESCE(i.rental_class_num, '') = :rental_class_id
            AND LOWER(TRIM(COALESCE(i.status, ''))) IN ('repair', 'needs to be inspected', 'wash', 'wet')
            GROUP BY REGEXP_REPLACE(i.common_name, '\s*\(G[0-9]+\)$', '')
            ORDER BY name ASC
            LIMIT :limit OFFSET :offset
        """
        params = {
            'rental_class_id': normalized_rental_class_id,
            'limit': per_page,
            'offset': (page - 1) * per_page
        }

        result = session.execute(text(query), params)
        common_names = [
            {
                'name': row[0],
                'on_contracts': row[1],
                'total_items_inventory': row[2],
                'is_hand_counted': False
            } for row in result.fetchall()
        ]

        # Get total count for pagination
        count_query = """
            SELECT COUNT(DISTINCT REGEXP_REPLACE(i.common_name, '\s*\(G[0-9]+\)$', ''))
            FROM id_item_master i
            WHERE COALESCE(i.rental_class_num, '') = :rental_class_id
            AND LOWER(TRIM(COALESCE(i.status, ''))) IN ('repair', 'needs to be inspected', 'wash', 'wet')
        """
        total_items = session.execute(text(count_query), {'rental_class_id': normalized_rental_class_id}).scalar() or 0

        response = {
            'common_names': common_names,
            'total_items': total_items,
            'page': page,
            'per_page': per_page
        }

        # Cache response
        cache_set(cache_key, response, timeout=60)
        logger.info(f"Fetched and cached {len(common_names)} common names for rental_class_id {normalized_rental_class_id}, total: {total_items}")
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error fetching common names: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab3_bp.route('/tab/3/data')
def tab3_data():
    """Fetch individual items for a rental class and common name."""
    logger.debug("Entering /tab/3/data endpoint at %s", datetime.now())
    session = None
    try:
        session = db.session()
        rental_class_id = unquote(request.args.get('rental_class_id', ''))
        common_name = unquote(request.args.get('common_name', ''))
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        if not rental_class_id or not common_name:
            logger.warning(f"Missing parameters: rental_class_id={rental_class_id}, common_name={common_name}")
            return jsonify({'error': 'rental_class_id and common_name are required'}), 400

        # Validate rental_class_id
        normalized_rental_class_id = normalize_rental_class_id(rental_class_id)
        logger.debug(f"Normalized rental_class_id: {normalized_rental_class_id}, common_name: {common_name}")

        # Check cache
        cache_key = f"tab3_items_{normalized_rental_class_id}_{common_name}_{page}_{per_page}"
        cached_data = cache_get(cache_key)
        if cached_data:
            logger.info(f"Returning cached data for {cache_key}")
            return jsonify(cached_data), 200

        # Query for items, including notes
        query = session.query(
            ItemMaster.tag_id,
            ItemMaster.common_name,
            ItemMaster.status,
            ItemMaster.bin_location,
            ItemMaster.last_contract_num,
            ItemMaster.date_last_scanned,
            ItemMaster.rental_class_num,
            ItemMaster.notes,
            ItemMaster.quality
        ).filter(
            ItemMaster.rental_class_num == normalized_rental_class_id,
            ItemMaster.common_name == common_name,
            or_(
                ItemMaster.status.in_(['Repair', 'Needs to be Inspected', 'Wash', 'Wet']),
                ItemMaster.tag_id.in_(
                    session.query(Transaction.tag_id).filter(
                        Transaction.tag_id == ItemMaster.tag_id,
                        Transaction.scan_date == session.query(func.max(Transaction.scan_date)).filter(Transaction.tag_id == ItemMaster.tag_id).correlate(Transaction).scalar_subquery(),
                        Transaction.service_required == True
                    )
                )
            )
        ).order_by(ItemMaster.date_last_scanned.desc())

        total_items = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()

        items_data = [
            {
                'tag_id': item.tag_id,
                'common_name': item.common_name,
                'status': item.status or 'N/A',
                'bin_location': item.bin_location or 'N/A',
                'last_contract_num': item.last_contract_num or 'N/A',
                'date_last_scanned': item.date_last_scanned.isoformat() if item.date_last_scanned else 'N/A',
                'quality': item.quality or 'N/A',
                'notes': item.notes or ''
            } for item in items
        ]

        response = {
            'items': items_data,
            'total_items': total_items,
            'page': page,
            'per_page': per_page
        }

        # Cache response
        cache_set(cache_key, response, timeout=60)
        logger.info(f"Fetched and cached {len(items_data)} items for rental_class_id {normalized_rental_class_id}, common_name {common_name}, total: {total_items}")
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error fetching items: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab3_bp.route('/tab/3/csv_contents', methods=['GET'])
def get_csv_contents():
    """Fetch contents of the RFID tags CSV file."""
    try:
        logger.debug("Entering /tab/3/csv_contents endpoint at %s", datetime.now())
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
@limiter.limit("10 per minute")
def remove_csv_item():
    """Remove an item from the RFID tags CSV file."""
    lock_file = None
    try:
        logger.debug("Entering /tab/3/remove_csv_item endpoint at %s", datetime.now())
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
@limiter.limit("5 per minute")
def sync_to_pc():
    """Sync items to the RFID tags CSV file."""
    session = None
    lock_file = None
    try:
        logger.debug("Entering /tab/3/sync_to_pc endpoint at %s", datetime.now())
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

        logger.debug(f"Found {len(csv_tag_ids)} unique tag_ids in CSV before sync")

        synced_items = []
        existing_tag_ids = csv_tag_ids.copy()

        # Query ItemMaster for 'Sold' items only
        logger.debug("Querying ItemMaster for 'Sold' items")
        try:
            sold_items = session.query(ItemMaster)\
                .filter(
                    ItemMaster.common_name == common_name,
                    ItemMaster.bin_location.in_(['pack', 'resale']),
                    ItemMaster.status == 'Sold'
                )\
                .order_by(ItemMaster.date_updated.asc())\
                .limit(quantity)\
                .all()
            logger.debug(f"Found {len(sold_items)} 'Sold' items in ItemMaster for common_name={common_name}")

            for item in sold_items:
                if len(synced_items) >= quantity:
                    break
                if item.tag_id in existing_tag_ids:
                    logger.debug(f"Skipping tag_id {item.tag_id} as it’s already in CSV")
                    continue
                synced_items.append({
                    'tag_id': item.tag_id,
                    'common_name': item.common_name,
                    'subcategory': 'Unknown',
                    'short_common_name': item.common_name,
                    'status': item.status,
                    'bin_location': item.bin_location,
                    'rental_class_num': normalize_rental_class_id(item.rental_class_num),
                    'is_new': False
                })
                existing_tag_ids.add(item.tag_id)
                logger.debug(f"Added to synced_items: tag_id={item.tag_id}, common_name={item.common_name}, status={item.status}, rental_class_num={item.rental_class_num}")
        except sqlalchemy.exc.DatabaseError as e:
            logger.error(f"Database error querying ItemMaster: {str(e)}", exc_info=True)
            return jsonify({'error': f"Database error querying ItemMaster: {str(e)}"}), 500

        # Generate new items if needed
        new_items = []
        if len(synced_items) < quantity:
            remaining_quantity = quantity - len(synced_items)
            logger.info(f"Generating {remaining_quantity} new items for common_name={common_name}")

            seed_entry = session.query(SeedRentalClass)\
                .filter(
                    SeedRentalClass.common_name == common_name,
                    SeedRentalClass.bin_location.in_(['pack', 'resale'])
                )\
                .first()
            if not seed_entry:
                logger.warning(f"No SeedRentalClass entry found for common_name={common_name} and bin_location in ['pack', 'resale']")
                return jsonify({'error': f"No SeedRentalClass entry found for common name '{common_name}'"}), 404

            rental_class_num = normalize_rental_class_id(seed_entry.rental_class_id)
            bin_location = seed_entry.bin_location

            @retry(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                retry=retry_if_exception_type(sqlalchemy.exc.DatabaseError),
                before_sleep=lambda retry_state: logger.debug(f"Retrying INSERT due to lock timeout, attempt {retry_state.attempt_number}")
            )
            def insert_new_item(new_item):
                session.add(new_item)
                session.flush()

            with session.no_autoflush:
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
                    insert_new_item(new_item)
                    new_items.append(new_item)
                    logger.debug(f"Generated new item: tag_id={tag_id}, common_name={common_name}, rental_class_num={rental_class_num}")

        if len(synced_items) > quantity:
            synced_items = synced_items[:quantity]

        # Map rental class details
        cache_key = 'rental_class_mappings'
        mappings_dict = cache_get(cache_key)
        if mappings_dict is None:
            base_mappings = session.query(RentalClassMapping).all()
            user_mappings = session.query(UserRentalClassMapping).all()
            mappings_dict = {normalize_rental_class_id(m.rental_class_id): {
                'category': m.category,
                'subcategory': m.subcategory,
                'short_common_name': m.short_common_name or 'N/A'
            } for m in base_mappings}
            for um in user_mappings:
                normalized_id = normalize_rental_class_id(um.rental_class_id)
                mappings_dict[normalized_id] = {
                    'category': um.category,
                    'subcategory': um.subcategory,
                    'short_common_name': um.short_common_name or 'N/A'
                }
                logger.debug(f"Added user mapping: rental_class_id={normalized_id}, short_common_name={um.short_common_name}")
            cache_set(cache_key, mappings_dict, timeout=3600)
            logger.debug(f"Cached rental_class_mappings for common_name={common_name}")

        for item in synced_items:
            normalized_rental_class = normalize_rental_class_id(item['rental_class_num'])
            mapping = mappings_dict.get(normalized_rental_class, {})
            item['subcategory'] = mapping.get('subcategory', 'Unknown')
            item['short_common_name'] = mapping.get('short_common_name', item['common_name'])
            logger.debug(f"Mapping for item: tag_id={item['tag_id']}, rental_class_num={normalized_rental_class}, short_common_name={item['short_common_name']}")

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
@limiter.limit("5 per minute")
def update_synced_status():
    """Update status of synced items to 'Ready to Rent'."""
    session = None
    lock_file = None
    try:
        logger.debug("Entering /tab/3/update_synced_status endpoint at %s", datetime.now())
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
                    logger.error(f"CSV file missing required fields: {required_fields}")
                    return jsonify({'error': f"CSV file missing required fields: {required_fields}"}), 400

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
        batch_size = 100
        item_dict = {}
        for i in range(0, len(tag_ids), batch_size):
            batch_tags = tag_ids[i:i + batch_size]
            items_in_db = session.query(ItemMaster.tag_id, ItemMaster.rental_class_num, ItemMaster.common_name, ItemMaster.bin_location)\
                .filter(ItemMaster.tag_id.in_(batch_tags))\
                .all()
            item_dict.update({item.tag_id: {
                'rental_class_num': normalize_rental_class_id(item.rental_class_num),
                'common_name': item.common_name,
                'bin_location': item.bin_location
            } for item in items_in_db})

        # Batch update ItemMaster status
        logger.debug("Updating ItemMaster status to 'Ready to Rent'")
        updated_items = 0
        for i in range(0, len(tag_ids), batch_size):
            batch_tags = tag_ids[i:i + batch_size]
            updated = ItemMaster.query\
                .filter(ItemMaster.tag_id.in_(batch_tags))\
                .update({ItemMaster.status: 'Ready to Rent', ItemMaster.date_updated: datetime.now()}, synchronize_session='fetch')
            updated_items += updated
            session.flush()
        logger.info(f"Updated {updated_items} items in ItemMaster")

        # Batch API updates
        api_client = APIClient()
        failed_items = []
        for item in items_to_update:
            tag_id = item['tag_id']
            try:
                params = {'filter[eq]': f"tag_id,eq,'{tag_id}'"}
                existing_items = api_client._make_request("14223767938169344381", params)
                if existing_items:
                    api_client.update_status(tag_id, 'Ready to Rent')
                    logger.debug(f"Updated status for tag_id {tag_id} in API")
                else:
                    db_item = item_dict.get(tag_id, {})
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
                # Invalidate cache for this tag_id
                cache.delete(f"tab3_items_{db_item.get('rental_class_num', '')}_{item['common_name']}")
            except Exception as api_error:
                logger.error(f"Error updating/inserting tag_id {tag_id} in API: {str(api_error)}", exc_info=True)
                failed_items.append(tag_id)
                continue

        if failed_items:
            logger.warning(f"Failed to update {len(failed_items)} items in API: {failed_items}")

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
        return jsonify({
            'updated_items': updated_items,
            'message': 'Status updated successfully',
            'failed_items': failed_items if failed_items else []
        }), 200
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
@limiter.limit("10 per minute")
def update_status():
    """Update the status of an item."""
    session = None
    try:
        logger.debug("Entering /tab/3/update_status endpoint at %s", datetime.now())
        session = db.session()
        data = request.get_json()
        tag_id = data.get('tag_id')
        new_status = data.get('status')
        date_updated = data.get('date_updated')

        if not tag_id or not new_status:
            logger.warning(f"Invalid input in update_status: tag_id={tag_id}, new_status={new_status}")
            return jsonify({'error': 'Tag ID and status are required'}), 400

        valid_statuses = ['Ready to Rent', 'Sold', 'Repair', 'Needs to be Inspected', 'Wash', 'Wet']
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
        item.date_updated = datetime.now() if not date_updated else datetime.fromisoformat(date_updated.replace('+00:00', 'Z'))
        session.commit()

        try:
            api_client = APIClient()
            api_client.update_status(tag_id, new_status)
            logger.info(f"Successfully updated API status for tag_id {tag_id} to {new_status}")
            # Invalidate cache for this item
            cache.delete(f"tab3_items_{item.rental_class_num}_{item.common_name}")
        except Exception as e:
            logger.error(f"Failed to update API status for tag_id {tag_id}: {str(e)}", exc_info=True)
            session.rollback()
            return jsonify({'error': f"Failed to update API: {str(e)}", 'local_update': 'success'}), 200

        logger.info(f"Updated status for tag_id {tag_id} to {new_status}")
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
@limiter.limit("10 per minute")
def update_notes():
    """Update the notes of an item."""
    session = None
    try:
        logger.debug("Entering /tab/3/update_notes endpoint at %s", datetime.now())
        session = db.session()
        data = request.get_json()
        tag_id = data.get('tag_id')
        new_notes = data.get('notes')
        date_updated = data.get('date_updated')

        if not tag_id:
            logger.warning(f"Invalid input in update_notes: tag_id={tag_id}")
            return jsonify({'error': 'Tag ID is required'}), 400

        item = session.query(ItemMaster).filter_by(tag_id=tag_id).first()
        if not item:
            logger.info(f"Item not found for tag_id {tag_id}")
            return jsonify({'error': 'Item not found'}), 404

        item.notes = new_notes if new_notes else ''
        item.date_updated = datetime.now() if not date_updated else datetime.fromisoformat(date_updated.replace('+00:00', 'Z'))
        session.commit()

        try:
            api_client = APIClient()
            api_client.update_notes(tag_id, new_notes if new_notes else '')
            logger.info(f"Successfully updated API notes for tag_id {tag_id}")
            # Invalidate cache for this item
            cache.delete(f"tab3_items_{item.rental_class_num}_{item.common_name}")
        except Exception as e:
            logger.error(f"Failed to update API notes for tag_id {tag_id}: {str(e)}", exc_info=True)
            session.rollback()
            return jsonify({'error': f"Failed to update API: {str(e)}", 'local_update': 'success'}), 200

        logger.info(f"Updated notes for tag_id {tag_id}")
        return jsonify({'message': 'Notes updated successfully'})
    except Exception as e:
        logger.error(f"Uncaught exception in update_notes: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab3_bp.route('/tab/3/update_quality', methods=['POST'])
@limiter.limit("10 per minute")
def update_quality():
    """Update the quality of an item."""
    session = None
    try:
        logger.debug("Entering /tab/3/update_quality endpoint at %s", datetime.now())
        session = db.session()
        data = request.get_json()
        tag_id = data.get('tag_id')
        new_quality = data.get('quality', '')
        date_updated = data.get('date_updated')

        if not tag_id:
            logger.warning(f"Invalid input in update_quality: tag_id={tag_id}")
            return jsonify({'error': 'Tag ID is required'}), 400

        if new_quality not in VALID_QUALITIES:
            logger.warning(f"Invalid quality value: {new_quality}")
            return jsonify({'error': f'Quality must be one of {", ".join(VALID_QUALITIES)}'}), 400

        item = session.query(ItemMaster).filter_by(tag_id=tag_id).first()
        if not item:
            logger.info(f"Item not found for tag_id {tag_id}")
            return jsonify({'error': 'Item not found'}), 404

        item.quality = new_quality if new_quality else None
        item.date_updated = datetime.now() if not date_updated else datetime.fromisoformat(date_updated.replace('+00:00', 'Z'))
        session.commit()

        try:
            api_client = APIClient()
            api_client.update_quality(tag_id, new_quality if new_quality else '')
            logger.info(f"Successfully updated API quality for tag_id {tag_id} to {new_quality}")
            # Invalidate cache for this item
            cache.delete(f"tab3_items_{item.rental_class_num}_{item.common_name}")
        except Exception as e:
            logger.error(f"Failed to update API quality for tag_id {tag_id}: {str(e)}", exc_info=True)
            session.rollback()
            return jsonify({'error': f"Failed to update API: {str(e)}", 'local_update': 'success'}), 200

        logger.info(f"Updated quality for tag_id {tag_id} to {new_quality}")
        return jsonify({'message': 'Quality updated successfully'})
    except Exception as e:
        logger.error(f"Uncaught exception in update_quality: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab3_bp.route('/tab/3/update_bin_location', methods=['POST'])
@limiter.limit("10 per minute")
def update_bin_location():
    """Update the bin location of an item."""
    session = None
    try:
        logger.debug("Entering /tab/3/update_bin_location endpoint at %s", datetime.now())
        session = db.session()
        data = request.get_json()
        tag_id = data.get('tag_id')
        new_bin_location = data.get('bin_location')
        date_updated = data.get('date_updated')

        if not tag_id:
            logger.warning(f"Invalid input in update_bin_location: tag_id={tag_id}")
            return jsonify({'error': 'Tag ID is required'}), 400

        valid_bin_locations = ['resale', 'sold', 'pack', 'burst']
        if new_bin_location not in valid_bin_locations and new_bin_location != '':
            logger.warning(f"Invalid bin location value: {new_bin_location}")
            return jsonify({'error': f'Bin location must be one of {", ".join(valid_bin_locations)} or empty'}), 400

        item = session.query(ItemMaster).filter_by(tag_id=tag_id).first()
        if not item:
            logger.info(f"Item not found for tag_id {tag_id}")
            return jsonify({'error': 'Item not found'}), 404

        item.bin_location = new_bin_location if new_bin_location else None
        item.date_updated = datetime.now() if not date_updated else datetime.fromisoformat(date_updated.replace('+00:00', 'Z'))
        session.commit()

        try:
            api_client = APIClient()
            api_client.update_bin_location(tag_id, new_bin_location if new_bin_location else '')
            logger.info(f"Successfully updated API bin location for tag_id {tag_id} to {new_bin_location}")
            # Invalidate cache for this item
            cache.delete(f"tab3_items_{item.rental_class_num}_{item.common_name}")
        except Exception as e:
            logger.error(f"Failed to update API bin location for tag_id {tag_id}: {str(e)}", exc_info=True)
            session.rollback()
            return jsonify({'error': f"Failed to update API: {str(e)}", 'local_update': 'success'}), 200

        logger.info(f"Updated bin location for tag_id {tag_id} to {new_bin_location}")
        return jsonify({'message': 'Bin location updated successfully'})
    except Exception as e:
        logger.error(f"Uncaught exception in update_bin_location: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab3_bp.route('/tab/3/pack_resale_common_names', methods=['GET'])
def get_pack_resale_common_names():
    """Fetch common names for pack/resale items with manual Redis caching."""
    session = None
    try:
        logger.debug("Entering /tab/3/pack_resale_common_names endpoint at %s", datetime.now())
        cache_key = 'pack_resale_common_names'
        cached_data = cache_get(cache_key)
        if cached_data:
            logger.info(f"Returning cached data for {cache_key}")
            return jsonify(cached_data), 200

        session = db.session()
        common_names = session.query(SeedRentalClass.common_name)\
            .filter(SeedRentalClass.bin_location.in_(['pack', 'resale']))\
            .distinct()\
            .order_by(SeedRentalClass.common_name.asc())\
            .all()
        common_names = [name[0] for name in common_names if name[0]]
        response = {'common_names': common_names}
        cache_set(cache_key, response, timeout=60)
        logger.info(f"Fetched and cached {len(common_names)} common names from SeedRentalClass for pack/resale")
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error fetching common names: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab3_bp.route('/tab/3/update_mappings', methods=['POST'])
@limiter.limit("5 per minute")
def update_mappings():
    """Update user rental class mappings."""
    session = None
    try:
        logger.debug("Entering /tab/3/update_mappings endpoint at %s", datetime.now())
        session = db.session()
        data = request.get_json()
        rental_class_id = data.get('rental_class_id')
        category = data.get('category')
        subcategory = data.get('subcategory')
        short_common_name = data.get('short_common_name')

        if not rental_class_id or not category or not subcategory:
            logger.warning(f"Invalid input in update_mappings: rental_class_id={rental_class_id}, category={category}, subcategory={subcategory}")
            return jsonify({'error': 'Rental class ID, category, and subcategory are required'}), 400

        normalized_rental_class_id = normalize_rental_class_id(rental_class_id)
        existing_mapping = session.query(UserRentalClassMapping).filter_by(rental_class_id=normalized_rental_class_id).first()

        if existing_mapping:
            existing_mapping.category = category
            existing_mapping.subcategory = subcategory
            existing_mapping.short_common_name = short_common_name if short_common_name else existing_mapping.short_common_name
            existing_mapping.updated_at = datetime.utcnow()
            logger.debug(f"Updated existing mapping: rental_class_id={normalized_rental_class_id}")
        else:
            new_mapping = UserRentalClassMapping(
                rental_class_id=normalized_rental_class_id,
                category=category,
                subcategory=subcategory,
                short_common_name=short_common_name if short_common_name else 'N/A',
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(new_mapping)
            logger.debug(f"Created new mapping: rental_class_id={normalized_rental_class_id}")

        session.commit()

        # Invalidate cache
        cache.delete('rental_class_mappings')
        logger.debug("Invalidated rental_class_mappings cache")

        logger.info(f"Updated mapping for rental_class_id {normalized_rental_class_id}")
        return jsonify({'message': 'Mapping updated successfully'}), 200
    except Exception as e:
        logger.error(f"Uncaught exception in update_mappings: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@tab3_bp.route('/tab/3/print', methods=['GET'])
def print_items():
    """Generate a printable view of items for a rental class and common name."""
    logger.debug("Entering /tab/3/print endpoint at %s", datetime.now())
    session = None
    try:
        session = db.session()
        rental_class_id = unquote(request.args.get('rental_class_id', ''))
        common_name = unquote(request.args.get('common_name', ''))

        if not rental_class_id or not common_name:
            logger.warning(f"Missing parameters: rental_class_id={rental_class_id}, common_name={common_name}")
            return jsonify({'error': 'rental_class_id and common_name are required'}), 400

        normalized_rental_class_id = normalize_rental_class_id(rental_class_id)
        logger.debug(f"Normalized rental_class_id: {normalized_rental_class_id}, common_name: {common_name}")

        # Query for items
        query = session.query(
            ItemMaster.tag_id,
            ItemMaster.common_name,
            ItemMaster.status,
            ItemMaster.bin_location,
            ItemMaster.last_contract_num,
            ItemMaster.date_last_scanned,
            ItemMaster.notes,
            ItemMaster.quality
        ).filter(
            ItemMaster.rental_class_num == normalized_rental_class_id,
            ItemMaster.common_name == common_name
        ).order_by(ItemMaster.date_last_scanned.desc())

        items = query.all()
        items_data = [
            {
                'tag_id': item.tag_id,
                'common_name': item.common_name,
                'status': item.status or 'N/A',
                'bin_location': item.bin_location or 'N/A',
                'last_contract_num': item.last_contract_num or 'N/A',
                'date_last_scanned': item.date_last_scanned.isoformat() if item.date_last_scanned else 'N/A',
                'notes': item.notes or '',
                'quality': item.quality or 'N/A'
            } for item in items
        ]

        # Generate HTML for printing
        html = render_template('tab3_print.html', items=items_data, rental_class_id=rental_class_id, common_name=common_name)
        response = make_response(html)
        response.headers['Content-Type'] = 'text/html'
        response.headers['Content-Disposition'] = 'inline; filename=items_print.html'
        return response
    except Exception as e:
        logger.error(f"Error generating print view: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()