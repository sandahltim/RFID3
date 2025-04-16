from flask import Blueprint, render_template, request, jsonify
from collections import defaultdict
from db_connection import DatabaseConnection
from ..mappings import CATEGORY_MAP, SUBCATEGORY_MAP
import sqlite3
import logging

tab2_bp = Blueprint("tab2_bp", __name__, url_prefix="/tab2")
logging.basicConfig(level=logging.DEBUG, filename='/home/tim/test_rfidpi/sync.log')

def categorize_item(rental_class_id):
    try:
        return CATEGORY_MAP.get(int(rental_class_id or 0), 'Other')
    except (ValueError, TypeError) as e:
        logging.error(f"Error categorizing item with rental_class_id {rental_class_id}: {e}")
        return 'Other'

def subcategorize_item(category, rental_class_id):
    try:
        rid = int(rental_class_id or 0)
        if category in ['Tent Tops', 'Tables and Chairs', 'Round Linen', 'Rectangle Linen', 
                        'Concession Equipment', 'AV Equipment', 'Runners and Drapes', 
                        'Other', 'Resale']:
            return SUBCATEGORY_MAP.get(rid, 'Unspecified')
        return 'Unspecified'
    except (ValueError, TypeError) as e:
        logging.error(f"Error subcategorizing item with rental_class_id {rental_class_id}: {e}")
        return 'Unspecified'

@tab2_bp.route("/")
def show_tab2():
    logging.debug("Loading /tab2/ endpoint")
    try:
        with DatabaseConnection() as conn:
            items = conn.execute("""
                SELECT im.*, rt.item_type as rfid_item_type
                FROM id_item_master im
                LEFT JOIN id_rfidtag rt ON im.tag_id = rt.tag_id
            """).fetchall()
            contracts = conn.execute("""
                SELECT DISTINCT last_contract_num, client_name, MAX(date_last_scanned) as scan_date 
                FROM id_item_master 
                WHERE last_contract_num IS NOT NULL 
                GROUP BY last_contract_num
            """).fetchall()
        items = [dict(row) for row in items]
        contract_map = {c["last_contract_num"]: {"client_name": c["client_name"], "scan_date": c["scan_date"]} for c in contracts}

        filter_common_name = request.args.get("common_name", "").lower().strip()
        filter_tag_id = request.args.get("tag_id", "").lower().strip()
        filter_bin_location = request.args.get("bin_location", "").lower().strip()
        filter_last_contract = request.args.get("last_contract_num", "").lower().strip()
        filter_status = request.args.get("status", "").lower().strip()

        filtered_items = items
        if filter_common_name:
            filtered_items = [item for item in filtered_items if filter_common_name in (item.get("common_name") or "").lower()]
        if filter_tag_id:
            filtered_items = [item for item in filtered_items if filter_tag_id in (item.get("tag_id") or "").lower()]
        if filter_bin_location:
            filtered_items = [item for item in filtered_items if filter_bin_location in (item.get("bin_location") or "").lower()]
        if filter_last_contract:
            filtered_items = [item for item in filtered_items if filter_last_contract in (item.get("last_contract_num") or "").lower()]
        if filter_status:
            filtered_items = [item for item in filtered_items if filter_status in (item.get("status") or "").lower()]

        category_map = defaultdict(list)
        for item in filtered_items:
            category = categorize_item(item.get("rental_class_num"))
            category_map[category].append(item)

        parent_data = []
        sub_map = {}
        for category, item_list in category_map.items():
            total_amount = len(item_list)
            on_contract = sum(1 for item in item_list if item.get("status") in ["Delivered", "On Rent"])
            available = sum(1 for item in item_list if item.get("status") == "Ready to Rent")
            service = total_amount - on_contract - available

            subcategory_map = defaultdict(list)
            for item in item_list:
                subcategory = subcategorize_item(category, item.get("rental_class_num"))
                subcategory_map[subcategory].append(item)

            sub_map[category] = {
                subcategory: {
                    "subcategory": subcategory,
                    "total": len(sub_items),
                    "on_contract": sum(1 for item in sub_items if item.get("status") in ["Delivered", "On Rent"]),
                    "available": sum(1 for item in sub_items if item.get("status") == "Ready to Rent"),
                    "service": len(sub_items) - sum(1 for item in sub_items if item.get("status") in ["Delivered", "On Rent", "Ready to Rent"])
                }
                for subcategory, sub_items in subcategory_map.items()
            }

            parent_data.append({
                "category": category,
                "total_amount": total_amount,
                "on_contract": on_contract,
                "available": available,
                "service": service
            })

        parent_data.sort(key=lambda x: x["category"])
        logging.debug(f"Rendering tab2 with {len(parent_data)} categories, items fetched: {len(items)}")
        for category in sub_map:
            logging.debug(f"Category {category} has subcategories: {list(sub_map[category].keys())}")

        return render_template(
            "tab2.html",
            parent_data=parent_data,
            sub_map=sub_map,
            contract_map=contract_map,
            filter_common_name=filter_common_name,
            filter_tag_id=filter_tag_id,
            filter_bin_location=filter_bin_location,
            filter_last_contract=filter_last_contract,
            filter_status=filter_status
        )
    except Exception as e:
        logging.error(f"Error in show_tab2: {e}")
        return jsonify({"error": str(e)}), 500

@tab2_bp.route("/data", methods=["GET"])
def tab2_data():
    logging.debug("Loading /tab2/data endpoint")
    try:
        with DatabaseConnection() as conn:
            items = conn.execute("""
                SELECT im.*, rt.item_type as rfid_item_type
                FROM id_item_master im
                LEFT JOIN id_rfidtag rt ON im.tag_id = rt.tag_id
            """).fetchall()
        items = [dict(row) for row in items]

        filter_common_name = request.args.get("common_name", "").lower().strip()
        filter_tag_id = request.args.get("tag_id", "").lower().strip()
        filter_bin_location = request.args.get("bin_location", "").lower().strip()
        filter_last_contract = request.args.get("last_contract_num", "").lower().strip()
        filter_status = request.args.get("status", "").lower().strip()

        filtered_items = items
        if filter_common_name:
            filtered_items = [item for item in filtered_items if filter_common_name in (item.get("common_name") or "").lower()]
        if filter_tag_id:
            filtered_items = [item for item in filtered_items if filter_tag_id in (item.get("tag_id") or "").lower()]
        if filter_bin_location:
            filtered_items = [item for item in filtered_items if filter_bin_location in (item.get("bin_location") or "").lower()]
        if filter_last_contract:
            filtered_items = [item for item in filtered_items if filter_last_contract in (item.get("last_contract_num") or "").lower()]
        if filter_status:
            filtered_items = [item for item in filtered_items if filter_status in (item.get("status") or "").lower()]

        category_map = defaultdict(list)
        for item in filtered_items:
            category = categorize_item(item.get("rental_class_num"))
            category_map[category].append(item)

        parent_data = []
        sub_map = {}
        for category, item_list in category_map.items():
            total_amount = len(item_list)
            on_contract = sum(1 for item in item_list if item.get("status") in ["Delivered", "On Rent"])
            available = sum(1 for item in item_list if item.get("status") == "Ready to Rent")
            service = total_amount - on_contract - available

            subcategory_map = defaultdict(list)
            for item in item_list:
                subcategory = subcategorize_item(category, item.get("rental_class_num"))
                subcategory_map[subcategory].append(item)

            sub_map[category] = {
                subcategory: {
                    "subcategory": subcategory,
                    "total": len(sub_items),
                    "on_contract": sum(1 for item in sub_items if item.get("status") in ["Delivered", "On Rent"]),
                    "available": sum(1 for item in sub_items if item.get("status") == "Ready to Rent"),
                    "service": len(sub_items) - sum(1 for item in sub_items if item.get("status") in ["Delivered", "On Rent", "Ready to Rent"])
                }
                for subcategory, sub_items in subcategory_map.items()
            }

            parent_data.append({
                "category": category,
                "total_amount": total_amount,
                "on_contract": on_contract,
                "available": available,
                "service": service
            })

        parent_data.sort(key=lambda x: x["category"])
        logging.debug(f"Returning {len(parent_data)} categories for /tab2/data, items fetched: {len(items)}")

        return jsonify({
            "parent_data": parent_data,
            "sub_map": sub_map
        })
    except Exception as e:
        logging.error(f"Error in tab2_data: {e}")
        return jsonify({"error": str(e)}), 500

@tab2_bp.route('/subcat_data')
def subcat_data():
    try:
        category = request.args.get('category', '')
        subcategory = request.args.get('subcategory', '')
        page = int(request.args.get('page', 1))
        per_page = 10

        filters = {
            'common_name': request.args.get('common_name', ''),
            'tag_id': request.args.get('tag_id', ''),
            'bin_location': request.args.get('bin_location', ''),
            'last_contract_num': request.args.get('last_contract_num', ''),
            'status': request.args.get('status', '')
        }

        rental_classes = [k for k, v in SUBCATEGORY_MAP.items() if v == subcategory and CATEGORY_MAP.get(k, 'Other') == category]
        if not rental_classes:
            logger.warning(f"No rental classes found for category: {category}, subcategory: {subcategory}")
            return jsonify({'items': [], 'current_page': page, 'total_pages': 0, 'total_items': 0})

        # Optimized query: filter rental_class_num first, limit joins
        query = """
            SELECT im.tag_id, im.common_name, im.status, im.bin_location, im.quality,
                   im.last_contract_num, im.client_name, im.date_last_scanned, im.last_scanned_by,
                   it.notes
            FROM id_item_master im
            LEFT JOIN id_transactions it ON im.tag_id = it.tag_id
            WHERE im.rental_class_num IN %s
        """
        params = [tuple(rental_classes)]

        conditions = []
        if filters['common_name']:
            conditions.append("im.common_name LIKE ?")
            params.append(f"%{filters['common_name']}%")
        if filters['tag_id']:
            conditions.append("im.tag_id LIKE ?")
            params.append(f"%{filters['tag_id']}%")
        if filters['bin_location']:
            conditions.append("im.bin_location LIKE ?")
            params.append(f"%{filters['bin_location']}%")
        if filters['last_contract_num']:
            conditions.append("im.last_contract_num LIKE ?")
            params.append(f"%{filters['last_contract_num']}%")
        if filters['status']:
            conditions.append("im.status = ?")
            params.append(filters['status'])

        if conditions:
            query += " AND " + " AND ".join(conditions)

        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            items = [dict(row) for row in cursor.fetchall()]
            logger.debug(f"Filtered {len(items)} items for category: {category}, subcategory: {subcategory}")

            total_items = len(items)
            total_pages = (total_items + per_page - 1) // per_page
            start = (page - 1) * per_page
            end = start + per_page
            paginated_items = items[start:end]

            return jsonify({
                'items': paginated_items,
                'current_page': page,
                'total_pages': max(total_pages, 1),
                'total_items': total_items
            })
    except Exception as e:
        logger.error(f"Error in subcat_data route: {str(e)}")
        return jsonify({"error": str(e)}), 500