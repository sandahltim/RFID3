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

@tab2_bp.route("/subcat_data", methods=["GET"])
def subcat_data():
    category = request.args.get('category', '').strip()
    subcategory = request.args.get('subcategory', '').strip()
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    per_page = 20

    logging.debug(f"Hit /tab2/subcat_data: category={category}, subcategory={subcategory or 'ALL'}, page={page}")
    try:
        with DatabaseConnection() as conn:
            items = conn.execute("""
                SELECT im.*, rt.item_type as rfid_item_type
                FROM id_item_master im
                LEFT JOIN id_rfidtag rt ON im.tag_id = rt.tag_id
            """).fetchall()
        items = [dict(row) for row in items]
        logging.debug(f"Fetched {len(items)} items from id_item_master")

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

        subcat_items = []
        for item in filtered_items:
            item_category = categorize_item(item.get("rental_class_num")).lower()
            item_subcategory = subcategorize_item(item_category, item.get("rental_class_num")).lower()
            if item_category == category.lower():
                if not subcategory or item_subcategory == subcategory.lower():
                    subcat_items.append(item)

        total_items = len(subcat_items)
        total_pages = (total_items + per_page - 1) // per_page
        page = max(1, min(page, total_pages))
        start = (page - 1) * per_page
        end = start + per_page
        paginated_items = subcat_items[start:end]

        logging.debug(f"Filtered {total_items} items for category={category}, subcategory={subcategory or 'ALL'}, page={page}")

        return jsonify({
            "items": [{
                "tag_id": item.get("tag_id", "N/A"),
                "common_name": item.get("common_name", "N/A"),
                "status": item.get("status", "N/A"),
                "bin_location": item.get("bin_location", "N/A"),
                "quality": item.get("quality", "N/A"),
                "last_contract_num": item.get("last_contract_num", "N/A"),
                "date_last_scanned": item.get("date_last_scanned", "N/A"),
                "last_scanned_by": item.get("last_scanned_by", "Unknown"),
                "notes": item.get("notes", "N/A"),
                "client_name": item.get("client_name", "N/A")
            } for item in paginated_items],
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": page
        })
    except Exception as e:
        logging.error(f"Error in subcat_data: {e}")
        return jsonify({"error": str(e)}), 500