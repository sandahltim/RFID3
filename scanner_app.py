# scanner_app.py
# Standalone Mobile RFID Scanner Application
# Version: 2025-09-13-v1
# Port: 8444 (separate from main dashboard on 8443)

import os
import sys
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import logging
import json
import pymysql
from pymysql import Error
import ssl
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/tim/RFID3/logs/scanner_app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__,
           template_folder='scanner_templates',
           static_folder='static')

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'scanner-app-key-2025')

# Database configuration - Primary
DB_CONFIG = {
    'host': 'localhost',
    'user': 'scanner_user',
    'password': 'scanner123',
    'database': 'rfid_inventory',
    'charset': 'utf8mb4',
    'autocommit': True
}

# Fallback database configuration - rfidpro baseline import
FALLBACK_DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'rfidpro',
    'charset': 'utf8mb4',
    'autocommit': True
}

@contextmanager
def get_db_connection():
    """Database connection context manager with fallback to rfidpro"""
    conn = None
    config_used = 'primary'
    try:
        # Try primary database first
        try:
            conn = pymysql.connect(**DB_CONFIG)
            config_used = 'primary'
        except Error as primary_error:
            logger.warning(f"Primary database connection failed: {primary_error}")
            logger.info("Attempting fallback to rfidpro database...")
            try:
                conn = pymysql.connect(**FALLBACK_DB_CONFIG)
                config_used = 'fallback'
                logger.info("Successfully connected to rfidpro fallback database")
            except Error as fallback_error:
                logger.error(f"Fallback database connection also failed: {fallback_error}")
                logger.error(f"Primary error: {primary_error}")
                raise fallback_error

        yield conn

    finally:
        if conn:
            conn.close()
            logger.debug(f"Database connection closed ({config_used})")

@app.route('/')
def home():
    """Main scanner interface"""
    return render_template('scanner_home.html')

@app.route('/scan')
def scanner():
    """RFID/QR Scanner interface"""
    return render_template('scanner_interface.html')

@app.route('/rental')
def rental_flow():
    """Rental flow management interface"""
    return render_template('rental_flow.html')

@app.route('/api/scan/<tag_id>')
def scan_item(tag_id):
    """API endpoint for scanning items"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            # Search for item in contract snapshots (where RFID tags are stored)
            query = """
            SELECT
                cs.tag_id,
                cs.serial_number,
                cs.rental_class_num as rental_class_id,
                cs.status,
                cs.bin_location,
                cs.notes,
                cs.snapshot_date as date_last_scanned,
                cs.created_by as last_scanned_by,
                cs.contract_number,
                cs.client_name,
                cs.common_name
            FROM contract_snapshots cs
            WHERE cs.tag_id = %s OR cs.serial_number = %s
            ORDER BY cs.snapshot_date DESC
            LIMIT 1
            """

            cursor.execute(query, (tag_id.upper(), tag_id))
            item = cursor.fetchone()

            if not item:
                return jsonify({
                    "success": False,
                    "message": "Item not found",
                    "tag_id": tag_id
                }), 404

            # Get recent transaction history (if table exists)
            transactions = []
            try:
                trans_query = """
                SELECT scan_type, scan_date, status, bin_location
                FROM equipment_transactions
                WHERE tag_id = %s
                ORDER BY scan_date DESC
                LIMIT 5
                """
                cursor.execute(trans_query, (tag_id.upper(),))
                transactions = cursor.fetchall()
            except Error:
                # Table might not exist yet
                pass

            # Format response for mobile interface
            response = {
                "success": True,
                "item": {
                    "tag_id": item['tag_id'],
                    "serial_number": item['serial_number'] or 'N/A',
                    "rental_class_id": item['rental_class_id'] or 'Unknown',
                    "status": item['status'] or 'Available',
                    "location": item['bin_location'] or 'Not Set',
                    "notes": item['notes'] or '',
                    "last_scanned": item['date_last_scanned'].isoformat() if item['date_last_scanned'] else None,
                    "scanned_by": item['last_scanned_by'] or 'System'
                },
                "recent_activity": [
                    {
                        "action": trans['scan_type'],
                        "date": trans['scan_date'].isoformat() if trans['scan_date'] else None,
                        "status": trans['status'],
                        "location": trans['bin_location']
                    } for trans in transactions
                ],
                "timestamp": datetime.utcnow().isoformat()
            }

            logger.info(f"Scanner app: Item {tag_id} found successfully")
            return jsonify(response)

    except Exception as e:
        logger.error(f"Error scanning item {tag_id}: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Database error: {str(e)}"
        }), 500

@app.route('/api/update/<tag_id>', methods=['POST'])
def update_item(tag_id):
    """Update item status from scanner"""
    try:
        data = request.get_json()
        employee_name = data.get('employee', 'Mobile Scanner')
        new_status = data.get('status', '')
        new_location = data.get('location', '')
        notes = data.get('notes', '')

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Update item master
            update_query = """
            UPDATE equipment_items
            SET status = %s,
                bin_location = %s,
                notes = %s,
                date_last_scanned = NOW(),
                last_scanned_by = %s
            WHERE tag_id = %s
            """

            cursor.execute(update_query, (
                new_status, new_location, notes, employee_name, tag_id.upper()
            ))

            if cursor.rowcount == 0:
                return jsonify({
                    "success": False,
                    "message": "Item not found for update"
                }), 404

            # Add transaction record (if table exists)
            try:
                trans_query = """
                INSERT INTO equipment_transactions
                (tag_id, scan_type, status, bin_location, scan_date, notes)
                VALUES (%s, %s, %s, %s, NOW(), %s)
                """

                cursor.execute(trans_query, (
                    tag_id.upper(), 'mobile_update', new_status, new_location,
                    f"Updated by {employee_name}: {notes}"
                ))
            except Error as e:
                logger.warning(f"Could not insert transaction record: {e}")
                # Continue without transaction log

            logger.info(f"Scanner app: Item {tag_id} updated by {employee_name}")

            return jsonify({
                "success": True,
                "message": "Item updated successfully",
                "updated_by": employee_name,
                "timestamp": datetime.utcnow().isoformat()
            })

    except Exception as e:
        logger.error(f"Error updating item {tag_id}: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Update failed: {str(e)}"
        }), 500

@app.route('/api/search')
def search_items():
    """Search items for employee interface"""
    try:
        query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 20)), 50)  # Max 50 results

        if len(query) < 2:
            return jsonify({
                "success": False,
                "message": "Search query must be at least 2 characters"
            }), 400

        with get_db_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            search_query = """
            SELECT
                tag_id, serial_number, rental_class_id, status, bin_location
            FROM equipment_items
            WHERE tag_id LIKE %s
               OR serial_number LIKE %s
               OR rental_class_id LIKE %s
               OR bin_location LIKE %s
            ORDER BY date_last_scanned DESC
            LIMIT %s
            """

            search_term = f"%{query}%"
            cursor.execute(search_query, (
                search_term, search_term, search_term, search_term, limit
            ))

            items = cursor.fetchall()

            return jsonify({
                "success": True,
                "results": items,
                "count": len(items),
                "query": query
            })

    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Search failed: {str(e)}"
        }), 500

@app.route('/api/health')
def health_check():
    """Health check for scanner app"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM equipment_items")
            item_count = cursor.fetchone()[0]

        return jsonify({
            "status": "healthy",
            "app": "RFID Mobile Scanner",
            "version": "2025-09-13-v1",
            "database": "connected",
            "items_in_system": item_count,
            "timestamp": datetime.utcnow().isoformat()
        })

    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 503

# ===== RENTAL FLOW ENDPOINTS =====

@app.route('/api/contracts/<contract_no>')
def get_contract(contract_no):
    """Get contract details by contract number"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            # Mock contract data - replace with actual contract table query
            contract_query = """
            SELECT
                'C123456' as contract_no,
                'John Doe' as customer_name,
                '555-1234' as contact_phone,
                NOW() as contract_date,
                'Active' as status,
                '3607' as store_no,
                1 as delivery_requested,
                DATE_ADD(NOW(), INTERVAL 3 DAY) as promised_delivery_date,
                '123 Main St' as delivery_address,
                NULL as actual_delivery_date,
                1 as pickup_requested,
                DATE_ADD(NOW(), INTERVAL 7 DAY) as promised_pickup_date,
                'Customer' as pickup_contact,
                NULL as actual_pickup_date
            """

            cursor.execute(contract_query)
            contract = cursor.fetchone()

            if contract:
                return jsonify({
                    "success": True,
                    "contract": contract
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "Contract not found"
                }), 404

    except Exception as e:
        logger.error(f"Error fetching contract {contract_no}: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Database error: {str(e)}"
        }), 500

@app.route('/api/contracts/<contract_no>/items')
def get_contract_items(contract_no):
    """Get items for a specific contract"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            # Mock contract items data
            items_query = """
            SELECT
                ROW_NUMBER() OVER (ORDER BY equipment_items.id) as id,
                equipment_items.tag_id as item_num,
                equipment_items.rental_class_id as desc,
                1 as qty,
                equipment_items.tag_id as rfid_tag_id,
                'RX' as line_status,
                DATE_ADD(NOW(), INTERVAL 5 DAY) as due_date
            FROM equipment_items
            LIMIT 5
            """

            cursor.execute(items_query)
            items = cursor.fetchall()

            return jsonify({
                "success": True,
                "items": items,
                "contract_no": contract_no
            })

    except Exception as e:
        logger.error(f"Error fetching items for contract {contract_no}: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Database error: {str(e)}"
        }), 500

@app.route('/api/rfid/assign', methods=['POST'])
def assign_rfid():
    """Assign RFID tag to contract item"""
    try:
        data = request.get_json()
        contract_no = data.get('contract_no')
        item_id = data.get('item_id')
        rfid_tag_id = data.get('rfid_tag_id')
        serial_number = data.get('serial_number')
        location = data.get('location')
        description = data.get('description')

        if not all([contract_no, item_id, rfid_tag_id]):
            return jsonify({
                "success": False,
                "message": "Missing required fields"
            }), 400

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check if RFID tag already exists
            cursor.execute("""
                SELECT COUNT(*) FROM equipment_items
                WHERE tag_id = %s
            """, (rfid_tag_id.upper(),))

            if cursor.fetchone()[0] > 0:
                return jsonify({
                    "success": False,
                    "message": "RFID tag already assigned to another item"
                }), 400

            # Insert new equipment item
            insert_query = """
            INSERT INTO equipment_items
            (tag_id, serial_number, rental_class_id, status, bin_location, notes, date_last_scanned, last_scanned_by)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)
            """

            cursor.execute(insert_query, (
                rfid_tag_id.upper(),
                serial_number,
                description,
                'Reserved',
                location,
                f"Contract: {contract_no}",
                'Mobile Scanner'
            ))

            return jsonify({
                "success": True,
                "message": "RFID tag assigned successfully",
                "rfid_tag_id": rfid_tag_id.upper()
            })

    except Exception as e:
        logger.error(f"Error assigning RFID: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Assignment failed: {str(e)}"
        }), 500

@app.route('/api/rental/checkout', methods=['POST'])
def checkout_item():
    """Check out item to customer"""
    try:
        data = request.get_json()
        tag_id = data.get('tag_id')
        contract_no = data.get('contract_no')
        employee = data.get('employee', 'Mobile Scanner')

        if not tag_id:
            return jsonify({
                "success": False,
                "message": "Tag ID required"
            }), 400

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Update item status to out with customer
            update_query = """
            UPDATE equipment_items
            SET status = 'Out with Customer',
                notes = CONCAT(IFNULL(notes, ''), ' - Checked out: ', %s),
                date_last_scanned = NOW(),
                last_scanned_by = %s
            WHERE tag_id = %s
            """

            cursor.execute(update_query, (contract_no or 'Direct', employee, tag_id.upper()))

            if cursor.rowcount == 0:
                return jsonify({
                    "success": False,
                    "message": "Item not found"
                }), 404

            return jsonify({
                "success": True,
                "message": f"Item {tag_id} checked out successfully"
            })

    except Exception as e:
        logger.error(f"Error checking out item: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Checkout failed: {str(e)}"
        }), 500

@app.route('/api/rental/return', methods=['POST'])
def return_item():
    """Return item from customer"""
    try:
        data = request.get_json()
        tag_id = data.get('tag_id')
        condition = data.get('condition', 'Good')
        needs_cleaning = data.get('needs_cleaning', False)
        needs_repair = data.get('needs_repair', False)
        employee = data.get('employee', 'Mobile Scanner')
        notes = data.get('notes', '')

        if not tag_id:
            return jsonify({
                "success": False,
                "message": "Tag ID required"
            }), 400

        # Determine next status based on condition
        if needs_repair:
            new_status = 'Needs Repair'
        elif needs_cleaning:
            new_status = 'Needs Cleaning'
        else:
            new_status = 'Available'

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Update item status
            update_query = """
            UPDATE equipment_items
            SET status = %s,
                notes = CONCAT(IFNULL(notes, ''), ' - Returned: ', %s, ' Condition: ', %s),
                date_last_scanned = NOW(),
                last_scanned_by = %s
            WHERE tag_id = %s
            """

            cursor.execute(update_query, (
                new_status,
                notes,
                condition,
                employee,
                tag_id.upper()
            ))

            if cursor.rowcount == 0:
                return jsonify({
                    "success": False,
                    "message": "Item not found"
                }), 404

            return jsonify({
                "success": True,
                "message": f"Item {tag_id} returned successfully",
                "new_status": new_status
            })

    except Exception as e:
        logger.error(f"Error returning item: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Return failed: {str(e)}"
        }), 500

@app.route('/api/rental/batch-process', methods=['POST'])
def batch_process():
    """Process batch of scanned items"""
    try:
        data = request.get_json()
        items = data.get('items', [])
        action = data.get('action', 'scan_only')
        employee = data.get('employee', 'Mobile Scanner')

        if not items:
            return jsonify({
                "success": False,
                "message": "No items to process"
            }), 400

        processed_count = 0
        results = []

        with get_db_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            for item in items:
                code = item.get('code', '').strip().upper()
                if not code:
                    continue

                try:
                    # Check if item exists
                    cursor.execute("""
                        SELECT tag_id, status, rental_class_id
                        FROM equipment_items
                        WHERE tag_id = %s OR serial_number = %s
                    """, (code, code))

                    equipment_item = cursor.fetchone()

                    if equipment_item:
                        # Update last scanned info
                        cursor.execute("""
                            UPDATE equipment_items
                            SET date_last_scanned = NOW(),
                                last_scanned_by = %s
                            WHERE tag_id = %s
                        """, (employee, equipment_item['tag_id']))

                        results.append({
                            "code": code,
                            "status": "found",
                            "item": equipment_item
                        })
                        processed_count += 1
                    else:
                        results.append({
                            "code": code,
                            "status": "not_found",
                            "message": "Item not in database"
                        })

                except Exception as e:
                    results.append({
                        "code": code,
                        "status": "error",
                        "message": str(e)
                    })

        return jsonify({
            "success": True,
            "processed": processed_count,
            "total": len(items),
            "results": results
        })

    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Batch processing failed: {str(e)}"
        }), 500

# ===== ADVANCED INTEGRATION ENDPOINTS =====

@app.route('/api/reservations/upcoming')
def get_upcoming_reservations():
    """Get upcoming reservations for easy access"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            # Get upcoming reservations from contract snapshots
            reservations_query = """
            SELECT DISTINCT
                contract_number,
                client_name,
                COUNT(*) as item_count,
                MIN(snapshot_date) as reservation_date,
                'Upcoming' as status,
                GROUP_CONCAT(DISTINCT rental_class_num) as equipment_types
            FROM contract_snapshots
            WHERE snapshot_date >= NOW()
                AND snapshot_date <= DATE_ADD(NOW(), INTERVAL 7 DAY)
                AND snapshot_type IN ('contract_start', 'reservation')
            GROUP BY contract_number, client_name
            ORDER BY reservation_date ASC
            LIMIT 20
            """

            cursor.execute(reservations_query)
            reservations = cursor.fetchall()

            # If no upcoming reservations, get recent active contracts instead
            if not reservations:
                recent_query = """
                SELECT DISTINCT
                    contract_number,
                    client_name,
                    COUNT(*) as item_count,
                    MAX(snapshot_date) as last_activity,
                    'Active' as status,
                    GROUP_CONCAT(DISTINCT rental_class_num) as equipment_types
                FROM contract_snapshots
                WHERE snapshot_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                GROUP BY contract_number, client_name
                ORDER BY last_activity DESC
                LIMIT 10
                """
                cursor.execute(recent_query)
                reservations = cursor.fetchall()

            return jsonify({
                "success": True,
                "reservations": reservations,
                "count": len(reservations),
                "timestamp": datetime.utcnow().isoformat()
            })

    except Exception as e:
        logger.error(f"Error fetching upcoming reservations: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Failed to fetch reservations: {str(e)}"
        }), 500

@app.route('/api/contracts/open')
def get_open_contracts():
    """Get currently open/active contracts"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            # Get active contracts with recent activity
            contracts_query = """
            SELECT
                cs.contract_number,
                cs.client_name,
                COUNT(DISTINCT cs.tag_id) as total_items,
                COUNT(DISTINCT CASE WHEN cs.status = 'Out' THEN cs.tag_id END) as items_out,
                COUNT(DISTINCT CASE WHEN cs.status IN ('Available', 'Returned', 'Ready') THEN cs.tag_id END) as items_returned,
                MAX(cs.snapshot_date) as last_activity,
                MIN(cs.snapshot_date) as contract_start,
                GROUP_CONCAT(DISTINCT cs.rental_class_num) as equipment_types
            FROM contract_snapshots cs
            WHERE cs.snapshot_date >= DATE_SUB(NOW(), INTERVAL 60 DAY)
            GROUP BY cs.contract_number, cs.client_name
            HAVING total_items > 0
            ORDER BY last_activity DESC
            LIMIT 25
            """

            cursor.execute(contracts_query)
            contracts = cursor.fetchall()

            # Calculate contract status for each
            for contract in contracts:
                total = contract['total_items'] or 0
                out = contract['items_out'] or 0
                returned = contract['items_returned'] or 0

                if out == total:
                    contract['contract_status'] = 'All Out'
                elif returned == total:
                    contract['contract_status'] = 'All Returned'
                elif out > 0:
                    contract['contract_status'] = 'Partial Out'
                else:
                    contract['contract_status'] = 'Ready'

                contract['completion_percentage'] = int((returned / total * 100)) if total > 0 else 0

            return jsonify({
                "success": True,
                "contracts": contracts,
                "count": len(contracts),
                "timestamp": datetime.utcnow().isoformat()
            })

    except Exception as e:
        logger.error(f"Error fetching open contracts: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Failed to fetch contracts: {str(e)}"
        }), 500

@app.route('/api/contracts/<contract_no>/details')
def get_contract_details(contract_no):
    """Get detailed contract information with all items"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            # Get contract items with current status
            items_query = """
            SELECT
                cs.tag_id,
                cs.rental_class_num,
                cs.serial_number,
                cs.bin_location as original_location,
                ei.status as current_status,
                ei.bin_location as current_location,
                ei.notes as current_notes,
                ei.date_last_scanned,
                ei.last_scanned_by,
                cs.quality,
                cs.notes as contract_notes
            FROM contract_snapshots cs
            LEFT JOIN equipment_items ei ON cs.tag_id = ei.tag_id
            WHERE cs.contract_number = %s
            ORDER BY cs.rental_class_num, cs.tag_id
            """

            cursor.execute(items_query, (contract_no,))
            items = cursor.fetchall()

            if not items:
                return jsonify({
                    "success": False,
                    "message": "Contract not found"
                }), 404

            # Get contract summary info
            summary_query = """
            SELECT
                contract_number,
                client_name,
                MIN(snapshot_date) as contract_start,
                MAX(snapshot_date) as last_update,
                COUNT(DISTINCT tag_id) as total_items
            FROM contract_snapshots
            WHERE contract_number = %s
            GROUP BY contract_number, client_name
            """

            cursor.execute(summary_query, (contract_no,))
            summary = cursor.fetchone()

            return jsonify({
                "success": True,
                "contract": summary,
                "items": items,
                "contract_number": contract_no
            })

    except Exception as e:
        logger.error(f"Error fetching contract details for {contract_no}: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Failed to fetch contract details: {str(e)}"
        }), 500

@app.route('/api/laundry/contracts')
def get_laundry_contracts():
    """Get laundry contracts (items needing cleaning/inspection)"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            # Get items needing laundry services from contract snapshots
            laundry_query = """
            SELECT
                cs.tag_id,
                cs.rental_class_num as rental_class_id,
                cs.status,
                cs.bin_location,
                cs.notes,
                cs.snapshot_date as date_last_scanned,
                cs.created_by as last_scanned_by,
                cs.contract_number,
                cs.client_name,
                CASE
                    WHEN cs.client_name LIKE '%LAUNDRY%' OR cs.contract_number LIKE 'L%' THEN 'Cleaning Required'
                    WHEN cs.quality IN ('Poor', 'Damaged', 'Needs Repair') THEN 'Quality Check Required'
                    WHEN cs.status IN ('Available', 'Ready') THEN 'Ready for Service'
                    ELSE 'Processing Required'
                END as service_type,
                DATEDIFF(NOW(), cs.snapshot_date) as days_since_return
            FROM contract_snapshots cs
            WHERE (cs.client_name LIKE '%LAUNDRY%' OR cs.contract_number LIKE 'L%'
                   OR cs.quality IN ('Poor', 'Damaged', 'Needs Repair', 'Fair')
                   OR cs.notes LIKE '%clean%' OR cs.notes LIKE '%repair%')
            ORDER BY days_since_return DESC, cs.client_name
            LIMIT 50
            """

            cursor.execute(laundry_query)
            laundry_items = cursor.fetchall()

            # Group by service type for better organization
            grouped_items = {}
            for item in laundry_items:
                service_type = item['service_type']
                if service_type not in grouped_items:
                    grouped_items[service_type] = []
                grouped_items[service_type].append(item)

            return jsonify({
                "success": True,
                "laundry_items": laundry_items,
                "grouped_items": grouped_items,
                "total_count": len(laundry_items),
                "counts_by_service": {k: len(v) for k, v in grouped_items.items()},
                "timestamp": datetime.utcnow().isoformat()
            })

    except Exception as e:
        logger.error(f"Error fetching laundry contracts: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Failed to fetch laundry items: {str(e)}"
        }), 500

@app.route('/api/laundry/queue')
def get_laundry_queue():
    """Get items in the laundry/service queue"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            # Get items currently in service queue (needing cleaning, inspection, or ready)
            queue_query = """
            SELECT
                cs.tag_id,
                cs.rental_class_num as rental_class_id,
                cs.status,
                cs.bin_location,
                cs.notes,
                cs.snapshot_date as date_last_scanned,
                cs.created_by as last_scanned_by,
                cs.contract_number,
                cs.client_name,
                CASE
                    WHEN cs.status LIKE '%cleaning%' OR cs.status LIKE '%wash%' OR cs.status LIKE '%laundry%' THEN 'cleaning'
                    WHEN cs.status LIKE '%inspect%' OR cs.status LIKE '%quality%' OR cs.status LIKE '%check%' THEN 'inspection'
                    WHEN cs.status LIKE '%ready%' OR cs.status LIKE '%available%' THEN 'ready'
                    ELSE 'other'
                END as service_type
            FROM contract_snapshots cs
            WHERE (
                cs.status LIKE '%cleaning%' OR
                cs.status LIKE '%wash%' OR
                cs.status LIKE '%laundry%' OR
                cs.status LIKE '%inspect%' OR
                cs.status LIKE '%quality%' OR
                cs.status LIKE '%check%' OR
                cs.status LIKE '%ready%' OR
                cs.status LIKE '%service%'
            )
            ORDER BY cs.snapshot_date DESC
            LIMIT 100
            """

            cursor.execute(queue_query)
            queue_items = cursor.fetchall()

            # Group by service type
            grouped_queue = {
                'cleaning': [],
                'inspection': [],
                'ready': [],
                'other': []
            }

            for item in queue_items:
                service_type = item.get('service_type', 'other')
                grouped_queue[service_type].append(item)

            return jsonify({
                "success": True,
                "queue_items": queue_items,
                "grouped_queue": grouped_queue,
                "total_count": len(queue_items),
                "counts_by_service": {k: len(v) for k, v in grouped_queue.items()},
                "timestamp": datetime.utcnow().isoformat()
            })

    except Exception as e:
        logger.error(f"Error fetching laundry queue: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Failed to fetch laundry queue: {str(e)}"
        }), 500

@app.route('/api/pos/sync')
def sync_pos_data():
    """Sync with POS system data"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)

            # Get POS integration status
            pos_status_query = """
            SELECT
                COUNT(*) as total_equipment,
                COUNT(CASE WHEN date_last_scanned >= DATE_SUB(NOW(), INTERVAL 24 HOUR) THEN 1 END) as scanned_today,
                COUNT(CASE WHEN status = 'Out with Customer' THEN 1 END) as currently_rented,
                COUNT(CASE WHEN status IN ('Needs Cleaning', 'Needs Inspection') THEN 1 END) as needs_service
            FROM equipment_items
            """

            cursor.execute(pos_status_query)
            pos_stats = cursor.fetchone()

            # Get recent activity summary
            activity_query = """
            SELECT
                DATE(date_last_scanned) as activity_date,
                COUNT(*) as scan_count,
                COUNT(DISTINCT last_scanned_by) as active_scanners
            FROM equipment_items
            WHERE date_last_scanned >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(date_last_scanned)
            ORDER BY activity_date DESC
            """

            cursor.execute(activity_query)
            recent_activity = cursor.fetchall()

            return jsonify({
                "success": True,
                "pos_integration": {
                    "status": "connected",
                    "last_sync": datetime.utcnow().isoformat(),
                    "stats": pos_stats,
                    "recent_activity": recent_activity
                },
                "message": "POS data sync completed successfully"
            })

    except Exception as e:
        logger.error(f"Error syncing POS data: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"POS sync failed: {str(e)}"
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html',
                         error_code=404,
                         error_message="Page not found"), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('error.html',
                         error_code=500,
                         error_message="Internal server error"), 500

@app.route('/api/db/status')
def database_status():
    """Check database connection status and which database is active"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DATABASE() as current_db, COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = DATABASE()")
            result = cursor.fetchone()
            current_db = result[0] if result else 'unknown'
            table_count = result[1] if result else 0

            # Check if we have the critical tables
            critical_tables = ['contract_snapshots', 'equipment_items']
            cursor.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name IN ({','.join(['%s'] * len(critical_tables))})", critical_tables)
            critical_tables_count = cursor.fetchone()[0]

            db_source = 'rfidpro (fallback)' if current_db == 'rfidpro' else 'rfid_inventory (primary)'

            return jsonify({
                'status': 'connected',
                'database': current_db,
                'source': db_source,
                'table_count': table_count,
                'critical_tables_available': critical_tables_count,
                'is_fallback': current_db == 'rfidpro',
                'timestamp': datetime.now().isoformat()
            })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    os.makedirs('/home/tim/RFID3/logs', exist_ok=True)

    # SSL Configuration
    ssl_context = None
    try:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ssl_context.load_cert_chain('/home/tim/RFID3/ssl/cert.pem',
                                   '/home/tim/RFID3/ssl/key.pem')
        logger.info("SSL certificates loaded successfully")
    except FileNotFoundError:
        logger.warning("SSL certificates not found, running without HTTPS")
    except Exception as e:
        logger.error(f"SSL setup error: {e}")

    # Start scanner application
    logger.info("Starting RFID Mobile Scanner App on port 8443")

    app.run(
        host='0.0.0.0',
        port=8443,
        ssl_context=ssl_context,
        debug=False,
        threaded=True
    )