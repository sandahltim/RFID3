from flask import Blueprint, render_template, request, jsonify
from collections import defaultdict
from db_connection import DatabaseConnection
import sqlite3

tab1_bp = Blueprint("tab1_bp", __name__, url_prefix="/tab1")
HAND_COUNTED_DB = "/home/tim/test_rfidpi/tab5_hand_counted.db"

def get_tab1_data():
    with DatabaseConnection() as conn:
        rows = conn.execute("SELECT * FROM id_item_master WHERE status IN ('Delivered', 'On Rent')").fetchall()
    items = [dict(row) for row in rows]

    # Fetch hand-counted items
    with sqlite3.connect(HAND_COUNTED_DB, timeout=10) as conn:
        conn.row_factory = sqlite3.Row
        hand_counted_items = conn.execute("SELECT * FROM hand_counted_items").fetchall()
    hand_counted = [dict(row) for row in hand_counted_items]

    # Combine RFID and hand-counted items
    all_items = items + hand_counted

    contract_totals = defaultdict(lambda: {"total": 0, "client_name": None, "first_scan_date": None, "items": []})
    for item in all_items:
        contract = item.get("last_contract_num")
        if not contract:
            continue
        # Skip hand-counted items that aren't active (e.g., closed contracts starting with 'C')
        if item.get("tag_id") is None and not contract.lower().startswith("l"):
            continue
        contract_totals[contract]["total"] += item.get("total_items", 1)
        contract_totals[contract]["items"].append(item)
        if not contract_totals[contract]["client_name"]:
            contract_totals[contract]["client_name"] = item.get("client_name")
        current_first_scan = contract_totals[contract]["first_scan_date"]
        item_scan_date = item.get("date_last_scanned")
        if item_scan_date and (not current_first_scan or item_scan_date < current_first_scan):
            contract_totals[contract]["first_scan_date"] = item_scan_date

    parent_data = [
        {
            "contract": contract,
            "total": info["total"],
            "client_name": info["client_name"],
            "first_scan_date": info["first_scan_date"]
        }
        for contract, info in contract_totals.items()
    ]
    parent_data.sort(key=lambda x: x["contract"])

    child_map = {}
    for contract, info in contract_totals.items():
        rental_class_totals = defaultdict(lambda: {"total": 0, "available": 0, "on_rent": 0, "service": 0, "items": []})
        for item in info["items"]:
            # Use a unique key for hand-counted items: id_common_name
            if item.get("tag_id") is None:
                rental_class_id = f"hand_{item.get('id')}_{item.get('common_name', 'unknown').replace(' ', '_')}"
            else:
                rental_class_id = item.get("rental_class_num", "unknown")
            common_name = item.get("common_name", "Unknown")
            rental_class_totals[rental_class_id]["common_name"] = common_name
            rental_class_totals[rental_class_id]["total"] += item.get("total_items", 1)
            if item.get("status") == "Ready to Rent":
                rental_class_totals[rental_class_id]["available"] += item.get("total_items", 1)
            elif item.get("status") in ["On Rent", "Delivered"]:
                rental_class_totals[rental_class_id]["on_rent"] += item.get("total_items", 1)
            else:
                rental_class_totals[rental_class_id]["service"] += item.get("total_items", 1)
            rental_class_totals[rental_class_id]["items"].append(item)
        child_map[contract] = dict(rental_class_totals)

    return parent_data, child_map

@tab1_bp.route("/")
def show_tab1():
    parent_data, child_map = get_tab1_data()
    return render_template("tab1.html", parent_data=parent_data, child_map=child_map)

@tab1_bp.route("/data", methods=["GET"])
def tab1_data():
    parent_data, child_map = get_tab1_data()
    return jsonify({
        "parent_data": parent_data,
        "child_map": child_map
    })

@tab1_bp.route("/subcat_data", methods=["GET"])
def subcat_data():
    contract = request.args.get('contract')
    common_name = request.args.get('common_name')
    page = int(request.args.get('page', 1))
    per_page = 20

    with DatabaseConnection() as conn:
        rows = conn.execute("SELECT * FROM id_item_master WHERE last_contract_num = ? AND status IN ('Delivered', 'On Rent')", (contract,)).fetchall()
    items = [dict(row) for row in rows]

    # Fetch hand-counted items
    with sqlite3.connect(HAND_COUNTED_DB, timeout=10) as conn:
        conn.row_factory = sqlite3.Row
        hand_counted_items = conn.execute(
            "SELECT * FROM hand_counted_items WHERE last_contract_num = ? AND last_contract_num LIKE 'L%'",
            (contract,)
        ).fetchall()
    hand_counted = [dict(row) for row in hand_counted_items]

    # Combine RFID and hand-counted items
    all_items = items + hand_counted

    filtered_items = [item for item in all_items if item.get("common_name") == common_name]
    total_items = sum(item.get("total_items", 1) for item in filtered_items)
    total_pages = (total_items + per_page - 1) // per_page
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    end = start + per_page
    paginated_items = filtered_items[start:end]

    return jsonify({
        "items": paginated_items,
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page
    })