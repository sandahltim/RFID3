from flask import Blueprint, render_template, request, jsonify
from collections import defaultdict
from db_connection import DatabaseConnection
from ..mappings import CATEGORY_MAP, SUBCATEGORY_MAP
import sqlite3
import logging

tab2_bp = Blueprint("tab2_bp", __name__, url_prefix="/tab2")
logging.basicConfig(level=logging.DEBUG, filename='/home/tim/test_rfidpi/sync.log')

def get_all_items(conn):
    query = """
        SELECT im.tag_id, im.common_name, im.status, im.bin_location, im.quality,
               im.last_contract_num, im.client_name, im.date_last_scanned, im.last_scanned_by,
               im.rental_class_num, rt.item_type as rfid_item_type
        FROM id_item_master im
        LEFT JOIN id_rfidtag rt ON im.tag_id = rt.tag_id
    """
    return conn.execute(query).fetchall()

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
            items = get_all_items(conn)
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
        middle_map = {}
        for category, item_list in category_map.items():
            total_amount = len(item_list)
            on_contract = sum(1 for item in item_list if item.get("status") in ["Delivered", "On Rent"])
            available = sum(1 for item in item_list if item.get("status") == "Ready to Rent")
            service = total_amount - on_contract - available

            subcategory_map = defaultdict(list)
            for item in item_list:
                subcategory = subcategorize_item(category, item.get("rental_class_num"))
                subcategory_map[subcategory].append(item)

            middle_map[category] = [
                {
                    "subcategory": subcategory,
                    "total": len(sub_items),
                    "on_contract": sum(1 for item in sub_items if item.get("status") in ["Delivered", "On Rent"]),
                    "available": sum(1 for item in sub_items if item.get("status") == "Ready to Rent"),
                    "service": len(sub_items) - sum(1 for item in sub_items if item.get("status") in ["Delivered", "On Rent", "Ready to Rent"])
                }
                for subcategory, sub_items in subcategory_map.items()
            ]

            parent_data.append({
                "category": category,
                "total_amount": total_amount,
                "on_contract": on_contract,
                "available": available,
                "service": service
            })

        parent_data.sort(key=lambda x: x["category"])
        for category in middle_map:
            middle_map[category].sort(key=lambda x: x["subcategory"])
        logging.debug(f"Rendering tab2 with {len(parent_data)} categories, items fetched: {len(items)}")

        return render_template(
            "tab2.html",
            parent_data=parent_data,
            middle_map=middle_map,
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
            items = get_all_items(conn)
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
        middle_map = {}
        for category, item_list in category_map.items():
            total_amount = len(item_list)
            on_contract = sum(1 for item in item_list if item.get("status") in ["Delivered", "On Rent"])
            available = sum(1 for item in item_list if item.get("status") == "Ready to Rent")
            service = total_amount - on_contract - available

            subcategory_map = defaultdict(list)
            for item in item_list:
                subcategory = subcategorize_item(category, item.get("rental_class_num"))
                subcategory_map[subcategory].append(item)

            middle_map[category] = [
                {
                    "subcategory": subcategory,
                    "total": len(sub_items),
                    "on_contract": sum(1 for item in sub_items if item.get("status") in ["Delivered", "On Rent"]),
                    "available": sum(1 for item in sub_items if item.get("status") == "Ready to Rent"),
                    "service": len(sub_items) - sum(1 for item in sub_items if item.get("status") in ["Delivered", "On Rent", "Ready to Rent"])
                }
                for subcategory, sub_items in subcategory_map.items()
            ]

            parent_data.append({
                "category": category,
                "total_amount": total_amount,
                "on_contract": on_contract,
                "available": available,
                "service": service
            })

        parent_data.sort(key=lambda x: x["category"])
        for category in middle_map:
            middle_map[category].sort(key=lambda x: x["subcategory"])
        logging.debug(f"Returning {len(parent_data)} categories for /tab2/data, items fetched: {len(items)}")

        return jsonify({
            "parent_data": parent_data,
            "middle_map": middle_map
        })
    except Exception as e:
        logging.error(f"Error in tab2_data: {e}")
        return jsonify({"error": str(e)}), 500

@tab2_bp.route("/subcat_data", methods=["GET"])
def subcat_data():
    logging.debug("Hit /tab2/subcat_data endpoint")
    try:
        category = request.args.get('category')
        subcategory = request.args.get('subcategory')
        page = int(request.args.get('page', 1))
        per_page = 20

        rental_classes = [k for k, v in SUBCATEGORY_MAP.items() if v == subcategory and CATEGORY_MAP.get(k, 'Other') == category]
        if not rental_classes:
            logging.warning(f"No rental classes found for category: {category}, subcategory: {subcategory}")
            return jsonify({'items': [], 'current_page': page, 'total_pages': 0, 'total_items': 0})

        with DatabaseConnection() as conn:
            items = get_all_items(conn)
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

        category_items = [item for item in filtered_items if categorize_item(item.get("rental_class_num")) == category]
        subcat_items = [item for item in category_items if subcategorize_item(category, item.get("rental_class_num")) == subcategory]

        total_items = len(subcat_items)
        total_pages = (total_items + per_page - 1) // per_page
        page = max(1, min(page, total_pages))
        start = (page - 1) * per_page
        end = start + per_page
        paginated_items = subcat_items[start:end]

        logging.debug(f"AJAX: Category: {category}, Subcategory: {subcategory}, Total Items: {total_items}, Page: {page}")

        return jsonify({
            "items": [{
                "tag_id": item["tag_id"],
                "common_name": item["common_name"],
                "status": item["status"],
                "bin_location": item["bin_location"],
                "quality": item["quality"],
                "last_contract_num": item["last_contract_num"],
                "client_name": item["client_name"],
                "date_last_scanned": item["date_last_scanned"],
                "last_scanned_by": item["last_scanned_by"],
                "notes": item.get("notes", "N/A")
            } for item in paginated_items],
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": page
        })
    except Exception as e:
        logging.error(f"Error in subcat_data: {e}")
        return jsonify({"error": str(e)}), 500