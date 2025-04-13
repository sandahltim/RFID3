from flask import Blueprint, render_template, request, jsonify
from db_connection import DatabaseConnection
from collections import defaultdict
import logging

tab7_bp = Blueprint("tab7_bp", __name__, url_prefix="/tab7")
logging.basicConfig(level=logging.DEBUG)

def get_tag_data(filter_tag_id="", filter_common_name="", filter_category="", filter_status=""):
    with DatabaseConnection() as conn:
        query = "SELECT * FROM id_rfidtag WHERE 1=1"
        params = []
        if filter_tag_id:
            query += " AND tag_id LIKE ?"
            params.append(f"%{filter_tag_id}%")
        if filter_common_name:
            query += " AND common_name LIKE ?"
            params.append(f"%{filter_common_name}%")
        if filter_category:
            query += " AND category = ?"
            params.append(filter_category)
        if filter_status:
            query += " AND status = ?"
            params.append(filter_status)
        query += " ORDER BY tag_id"
        tags = conn.execute(query, params).fetchall()

        # Sync with id_item_master
        items = conn.execute("SELECT tag_id, status, last_contract_num FROM id_item_master").fetchall()
        item_map = {item['tag_id']: item for item in items}

    tag_list = [dict(tag) for tag in tags]
    for tag in tag_list:
        item = item_map.get(tag['tag_id'])
        if item:
            if item['status'] in ['On Rent', 'Delivered'] and tag['status'] != 'out/used':
                tag['status'] = 'out/used'
                tag['last_contract_num'] = item['last_contract_num']
                conn.execute(
                    "UPDATE id_rfidtag SET status = ?, last_contract_num = ?, last_updated = ? WHERE tag_id = ?",
                    ('out/used', item['last_contract_num'], datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), tag['tag_id'])
                )
            elif item['status'] == 'Ready to Rent' and tag['status'] == 'out/used':
                tag['status'] = 'active'
                tag['last_contract_num'] = None
                conn.execute(
                    "UPDATE id_rfidtag SET status = ?, last_contract_num = ?, last_updated = ? WHERE tag_id = ?",
                    ('active', None, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), tag['tag_id'])
                )

    return tag_list

@tab7_bp.route("/")
def show_tab7():
    logging.debug("Loading /tab7/ endpoint")
    try:
        filter_tag_id = request.args.get("tag_id", "").lower().strip()
        filter_common_name = request.args.get("common_name", "").lower().strip()
        filter_category = request.args.get("category", "").strip()
        filter_status = request.args.get("status", "").strip()

        tags = get_tag_data(filter_tag_id, filter_common_name, filter_category, filter_status)

        category_map = defaultdict(list)
        for tag in tags:
            category_map[tag['category']].append(tag)

        parent_data = [
            {
                "category": cat,
                "total": len(items),
                "out_used": sum(1 for item in items if item['status'] == 'out/used'),
                "active": sum(1 for item in items if item['status'] == 'active')
            }
            for cat, items in category_map.items()
        ]
        parent_data.sort(key=lambda x: x['category'])

        return render_template(
            "tab7.html",
            parent_data=parent_data,
            tags=tags,
            filter_tag_id=filter_tag_id,
            filter_common_name=filter_common_name,
            filter_category=filter_category,
            filter_status=filter_status
        )
    except Exception as e:
        logging.error(f"Error in show_tab7: {e}")
        return "Internal Server Error", 500

@tab7_bp.route("/data", methods=["GET"])
def tab7_data():
    logging.debug("Loading /tab7/data endpoint")
    try:
        filter_tag_id = request.args.get("tag_id", "").lower().strip()
        filter_common_name = request.args.get("common_name", "").lower().strip()
        filter_category = request.args.get("category", "").strip()
        filter_status = request.args.get("status", "").strip()

        tags = get_tag_data(filter_tag_id, filter_common_name, filter_category, filter_status)

        return jsonify({
            "tags": tags,
            "category_counts": {
                cat: {
                    "total": len(items),
                    "out_used": sum(1 for item in items if item['status'] == 'out/used'),
                    "active": sum(1 for item in items if item['status'] == 'active')
                }
                for cat, items in defaultdict(list, {tag['category']: [tag] for tag in tags}).items()
            }
        })
    except Exception as e:
        logging.error(f"Error in tab7_data: {e}")
        return jsonify({"error": str(e)}), 500

@tab7_bp.route("/print_tags", methods=["GET"])
def print_tags():
    logging.debug("Generating tag print list")
    try:
        with DatabaseConnection() as conn:
            tags = conn.execute("""
                SELECT t.tag_id, t.common_name, t.item_type
                FROM id_rfidtag t
                JOIN id_item_master m ON t.tag_id = m.tag_id
                WHERE m.status IN ('On Rent', 'Delivered')
                AND (t.item_type = 'resale' OR m.bin_location LIKE '%bundle%')
            """).fetchall()

        html = """
        <html>
        <head>
            <title>RFID Tag Print List</title>
            <style>
                @page { size: A4; margin: 20mm; }
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                table { width: 100%; border-collapse: collapse; }
                th, td { border: 1px solid black; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <h1>RFID Tags to Reprogram</h1>
            <table>
                <thead>
                    <tr>
                        <th>EPC</th>
                        <th>Common Name</th>
                        <th>Item Type</th>
                    </tr>
                </thead>
                <tbody>
        """
        for tag in tags:
            html += f"""
                <tr>
                    <td>{tag['tag_id']}</td>
                    <td>{tag['common_name']}</td>
                    <td>{tag['item_type']}</td>
                </tr>
            """
        html += """
                </tbody>
            </table>
        </body>
        </html>
        """
        return html
    except Exception as e:
        logging.error(f"Error generating print list: {e}")
        return "Internal Server Error", 500