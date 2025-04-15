from flask import Blueprint, render_template, request, jsonify
from collections import defaultdict
from db_connection import DatabaseConnection
from datetime import datetime
import logging

tab6_bp = Blueprint("tab6_bp", __name__, url_prefix="/tab6")
logging.basicConfig(level=logging.DEBUG)

def get_resale_items(conn):
    query = """
        SELECT im.*, rt.item_type
        FROM id_item_master im
        LEFT JOIN id_rfidtag rt ON im.tag_id = rt.tag_id
        WHERE LOWER(im.bin_location) = 'resale'
        ORDER BY im.last_contract_num, im.tag_id
    """
    return conn.execute(query).fetchall()

def categorize_item(item):
    common_name = item.get("common_name", "").upper()
    if any(word in common_name for word in ["FOG", "JUICE"]):
        return "A/V Resale"
    elif "CHOCOLATE" in common_name:
        return "Chocolate Resale"
    elif any(word in common_name for word in ["COTTON CANDY", "COTTON CANDY BAGS"]):
        return "Cotton Candy Resale"
    elif any(word in common_name for word in ["FUEL STERNO", "BUTANE CARTRIDGE 8 OUNCE", "AISLE CLOTH", "GARBAGE CAN"]):
        return "Disposable Resale"
    elif any(word in common_name for word in ["POPCORN", "NACHO CHEESE", "DONUT", "MINI DONUT"]):
        return "Popcorn-Cheese-Donut Resale"
    elif "FRUSHEEZE" in common_name:
        return "Slushie Resale"
    elif "SNOKONE" in common_name:
        return "SnoKone Resale"
    elif "8 X 30" in common_name:
        return "8ft Banq KwikCovers"
    elif "6 X 30" in common_name:
        return "6ft Banq KwikCovers"
    elif "ROUND 60" in common_name:
        return "60\" Rd KwikCovers"
    elif "ROUND 48" in common_name:
        return "48\" Rd KwikCovers"
    elif any(word in common_name for word in ["ROUND 30", "ROUND 36"]):
        return "30\"/36\" Rd KwikCovers"
    return "Other"

@tab6_bp.route("/")
def show_tab6():
    logging.debug("Loading /tab6/ endpoint")
    try:
        with DatabaseConnection() as conn:
            rows = get_resale_items(conn)
        items = [dict(row) for row in rows]

        filter_common_name = request.args.get("common_name", "").strip()
        filter_tag_id = request.args.get("tag_id", "").strip()
        filter_last_contract = request.args.get("last_contract_num", "").strip()
        filter_rental_class_num = request.args.get("rental_class_num", "").strip()

        filtered_items = items
        if filter_common_name:
            filtered_items = [item for item in filtered_items if filter_common_name.lower() in item.get("common_name", "").lower()]
        if filter_tag_id:
            filtered_items = [item for item in filtered_items if filter_tag_id.lower() in item.get("tag_id", "").lower()]
        if filter_last_contract:
            filtered_items = [item for item in filtered_items if filter_last_contract.lower() in item.get("last_contract_num", "").lower()]
        if filter_rental_class_num:
            rental_class_nums = [num.strip() for num in filter_rental_class_num.split(',') if num.strip()]
            filtered_items = [item for item in filtered_items if item.get("rental_class_num") in rental_class_nums]

        category_map = defaultdict(list)
        for item in filtered_items:
            cat = categorize_item(item)
            category_map[cat].append(item)

        parent_data = []
        middle_map = {}
        for category, item_list in category_map.items():
            total_amount = len(item_list)
            on_contract = sum(1 for item in item_list if item["status"] in ["Delivered", "On Rent"])

            common_name_map = defaultdict(list)
            for item in item_list:
                common_name = item.get("common_name", "Unknown")
                common_name_map[common_name].append(item)
            middle_map[category] = [
                {"common_name": name, "total": len(items)}
                for name, items in common_name_map.items()
            ]

            parent_data.append({
                "category": category,
                "total_amount": total_amount,
                "on_contract": on_contract
            })

        parent_data.sort(key=lambda x: x["category"])
        logging.debug(f"Rendering tab6 with {len(parent_data)} categories")

        return render_template(
            "tab6.html",
            parent_data=parent_data,
            middle_map=middle_map,
            filter_common_name=filter_common_name,
            filter_tag_id=filter_tag_id,
            filter_last_contract=filter_last_contract,
            filter_rental_class_num=filter_rental_class_num
        )
    except Exception as e:
        logging.error(f"Error in show_tab6: {e}")
        return jsonify({"error": str(e)}), 500

@tab6_bp.route("/data", methods=["GET"])
def tab6_data():
    logging.debug("Loading /tab6/data endpoint")
    try:
        with DatabaseConnection() as conn:
            rows = get_resale_items(conn)
        items = [dict(row) for row in rows]

        filter_common_name = request.args.get("common_name", "").strip()
        filter_tag_id = request.args.get("tag_id", "").strip()
        filter_last_contract = request.args.get("last_contract_num", "").strip()
        filter_rental_class_num = request.args.get("rental_class_num", "").strip()

        filtered_items = items
        if filter_common_name:
            filtered_items = [item for item in filtered_items if filter_common_name.lower() in item.get("common_name", "").lower()]
        if filter_tag_id:
            filtered_items = [item for item in filtered_items if filter_tag_id.lower() in item.get("tag_id", "").lower()]
        if filter_last_contract:
            filtered_items = [item for item in filtered_items if filter_last_contract.lower() in item.get("last_contract_num", "").lower()]
        if filter_rental_class_num:
            rental_class_nums = [num.strip() for num in filter_rental_class_num.split(',') if num.strip()]
            filtered_items = [item for item in filtered_items if item.get("rental_class_num") in rental_class_nums]

        category_map = defaultdict(list)
        for item in filtered_items:
            cat = categorize_item(item)
            category_map[cat].append(item)

        parent_data = []
        middle_map = {}
        for category, item_list in category_map.items():
            total_amount = len(item_list)
            on_contract = sum(1 for item in item_list if item["status"] in ["Delivered", "On Rent"])

            common_name_map = defaultdict(list)
            for item in item_list:
                common_name = item.get("common_name", "Unknown")
                common_name_map[common_name].append(item)
            middle_map[category] = [
                {"common_name": name, "total": len(items)}
                for name, items in common_name_map.items()
            ]

            parent_data.append({
                "category": category,
                "total_amount": total_amount,
                "on_contract": on_contract
            })

        parent_data.sort(key=lambda x: x["category"])
        logging.debug(f"Returning {len(parent_data)} categories for /tab6/data")

        return jsonify({
            "parent_data": parent_data,
            "middle_map": middle_map
        })
    except Exception as e:
        logging.error(f"Error in tab6_data: {e}")
        return jsonify({"error": str(e)}), 500

@tab6_bp.route("/subcat_data", methods=["GET"])
def subcat_data():
    logging.debug("Hit /tab6/subcat_data endpoint")
    category = request.args.get('category')
    common_name = request.args.get('common_name')
    page = int(request.args.get('page', 1))
    per_page = 20

    try:
        with DatabaseConnection() as conn:
            rows = get_resale_items(conn)
        items = [dict(row) for row in rows]

        filter_common_name = request.args.get("common_name_filter", "").strip()
        filter_tag_id = request.args.get("tag_id", "").strip()
        filter_last_contract = request.args.get("last_contract_num", "").strip()
        filter_rental_class_num = request.args.get("rental_class_num", "").strip()

        filtered_items = items
        if filter_common_name:
            filtered_items = [item for item in filtered_items if filter_common_name.lower() in item.get("common_name", "").lower()]
        if filter_tag_id:
            filtered_items = [item for item in filtered_items if filter_tag_id.lower() in item.get("tag_id", "").lower()]
        if filter_last_contract:
            filtered_items = [item for item in filtered_items if filter_last_contract.lower() in item.get("last_contract_num", "").lower()]
        if filter_rental_class_num:
            rental_class_nums = [num.strip() for num in filter_rental_class_num.split(',') if num.strip()]
            filtered_items = [item for item in filtered_items if item.get("rental_class_num") in rental_class_nums]

        category_items = [item for item in filtered_items if categorize_item(item) == category]
        subcat_items = [item for item in category_items if item.get("common_name") == common_name] if common_name else category_items

        total_items = len(subcat_items)
        total_pages = (total_items + per_page - 1) // per_page
        page = max(1, min(page, total_pages))
        start = (page - 1) * per_page
        end = start + per_page
        paginated_items = subcat_items[start:end]

        logging.debug(f"AJAX: Category: {category}, Common Name: {common_name}, Total Items: {total_items}, Page: {page}")

        return jsonify({
            "items": [{
                "tag_id": item["tag_id"],
                "common_name": item["common_name"],
                "date_last_scanned": item.get("date_last_scanned", "N/A"),
                "last_scanned_by": item.get("last_scanned_by", "Unknown"),
                "last_contract_num": item.get("last_contract_num", "N/A")
            } for item in paginated_items],
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": page
        })
    except Exception as e:
        logging.error(f"Error in subcat_data: {e}")
        return jsonify({"error": str(e)}), 500

@tab6_bp.route("/mark_sold", methods=["POST"])
def mark_sold():
    logging.debug("Hit /tab6/mark_sold endpoint")
    tag_id = request.form.get("tag_id")
    if not tag_id:
        logging.error("Missing tag_id in mark_sold request")
        return jsonify({"error": "Missing tag_id"}), 400

    try:
        with DatabaseConnection() as conn:
            cursor = conn.cursor()
            # Verify tag exists in id_rfidtag
            cursor.execute("SELECT item_type FROM id_rfidtag WHERE tag_id = ?", (tag_id,))
            row = cursor.fetchone()
            if not row:
                logging.warning(f"Tag {tag_id} not found in id_rfidtag")
                return jsonify({"error": "Tag not found"}), 404
            if row[0] != 'resale':
                logging.warning(f"Tag {tag_id} is not a resale item")
                return jsonify({"error": "Tag is not a resale item"}), 400

            # Update id_rfidtag
            cursor.execute("""
                UPDATE id_rfidtag
                SET status = 'sold', date_sold = ?, reuse_count = reuse_count + 1, last_updated = ?
                WHERE tag_id = ?
            """, (
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                tag_id
            ))
            if cursor.rowcount == 0:
                logging.warning(f"Failed to update tag {tag_id}")
                return jsonify({"error": "Failed to mark tag as sold"}), 500
            conn.commit()
        logging.debug(f"Tag {tag_id} marked as sold")
        return jsonify({"message": f"Tag {tag_id} marked as sold"}), 200
    except Exception as e:
        logging.error(f"Error marking tag sold: {e}")
        return jsonify({"error": str(e)}), 500