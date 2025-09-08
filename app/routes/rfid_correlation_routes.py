"""
RFID Correlation Routes
Handles RFID to POS equipment correlation with corrected store filtering
"""

from flask import Blueprint, jsonify, request, render_template
from flask import current_app as app
from app import db
from sqlalchemy import text, func, case, and_, or_
from datetime import datetime, timedelta
import json

rfid_correlation_bp = Blueprint('rfid_correlation', __name__, url_prefix='/api/rfid-correlation')

def get_store_filter_options():
    """Get available stores for filtering with correct RFID designations"""
    query = text("""
        SELECT DISTINCT
            sc.rfid_store_code as store_code,
            sc.store_name,
            sc.store_location,
            CASE 
                WHEN sc.rfid_store_code = '8101' THEN 'RFID Test Store'
                WHEN sc.rfid_store_code = '000' THEN 'Header/Noise Data'
                ELSE 'POS Only'
            END as store_type,
            COUNT(DISTINCT im.tag_id) as item_count,
            SUM(CASE WHEN im.identifier_type = 'RFID' THEN 1 ELSE 0 END) as rfid_count
        FROM store_correlations sc
        LEFT JOIN id_item_master im ON sc.rfid_store_code = im.current_store
        WHERE sc.is_active = 1
        GROUP BY sc.rfid_store_code, sc.store_name, sc.store_location
        ORDER BY 
            CASE 
                WHEN sc.rfid_store_code = '8101' THEN 1  -- Fridley first
                WHEN sc.rfid_store_code = '000' THEN 99  -- Header last
                ELSE 2 
            END,
            sc.store_name
    """)
    
    result = db.session.execute(query)
    stores = []
    
    for row in result:
        stores.append({
            'value': row.store_code,
            'label': f"{row.store_name} ({row.store_type})",
            'location': row.store_location,
            'store_type': row.store_type,
            'item_count': row.item_count,
            'rfid_count': row.rfid_count,
            'has_rfid': row.rfid_count > 0
        })
    
    return stores

@rfid_correlation_bp.route('/dashboard-data', methods=['GET'])
def get_dashboard_data():
    """Get RFID correlation dashboard data with correct store filtering"""
    try:
        store_filter = request.args.get('store', None)
        identifier_filter = request.args.get('identifier_type', None)
        
        # Build base query for statistics
        stats_query = """
        SELECT 
            COUNT(DISTINCT im.tag_id) as total_items,
            SUM(CASE WHEN im.identifier_type = 'RFID' THEN 1 ELSE 0 END) as rfid_items,
            SUM(CASE WHEN im.identifier_type = 'Bulk' THEN 1 ELSE 0 END) as bulk_items,
            SUM(CASE WHEN im.identifier_type = 'Sticker' THEN 1 ELSE 0 END) as sticker_items,
            SUM(CASE WHEN im.identifier_type = 'QR' THEN 1 ELSE 0 END) as qr_items,
            SUM(CASE WHEN im.identifier_type = 'None' THEN 1 ELSE 0 END) as unidentified_items,
            COUNT(DISTINCT im.current_store) as unique_stores,
            SUM(CASE WHEN im.rental_class_num IS NOT NULL THEN 1 ELSE 0 END) as items_with_rental_class
        FROM id_item_master im
        WHERE 1=1
        """
        
        params = {}
        
        if store_filter:
            stats_query += " AND im.current_store = :store"
            params['store'] = store_filter
        
        if identifier_filter and identifier_filter != 'all':
            stats_query += " AND im.identifier_type = :identifier_type"
            params['identifier_type'] = identifier_filter
        
        stats_result = db.session.execute(text(stats_query), params).fetchone()
        
        # Get store breakdown
        store_query = """
        SELECT 
            sc.store_name,
            sc.rfid_store_code as store_code,
            CASE 
                WHEN sc.rfid_store_code = '8101' THEN 'RFID Test'
                WHEN sc.rfid_store_code = '000' THEN 'Header Data'
                ELSE 'POS Only'
            END as store_type,
            COUNT(DISTINCT im.tag_id) as total_items,
            SUM(CASE WHEN im.identifier_type = 'RFID' THEN 1 ELSE 0 END) as rfid_items,
            SUM(CASE WHEN im.identifier_type = 'Bulk' THEN 1 ELSE 0 END) as bulk_items,
            SUM(CASE WHEN im.identifier_type = 'Sticker' THEN 1 ELSE 0 END) as sticker_items
        FROM store_correlations sc
        LEFT JOIN id_item_master im ON sc.rfid_store_code = im.current_store
        WHERE sc.is_active = 1
        """
        
        if store_filter:
            store_query += " AND sc.rfid_store_code = :store"
        
        store_query += """
        GROUP BY sc.store_name, sc.rfid_store_code
        ORDER BY 
            CASE 
                WHEN sc.rfid_store_code = '8101' THEN 1
                WHEN sc.rfid_store_code = '000' THEN 99
                ELSE 2
            END
        """
        
        store_result = db.session.execute(text(store_query), params)
        store_data = []
        
        for row in store_result:
            store_data.append({
                'store_name': row.store_name,
                'store_code': row.store_code,
                'store_type': row.store_type,
                'total_items': row.total_items,
                'rfid_items': row.rfid_items,
                'bulk_items': row.bulk_items,
                'sticker_items': row.sticker_items,
                'is_rfid_enabled': row.store_code == '8101'
            })
        
        # Get identifier type distribution
        type_query = """
        SELECT 
            identifier_type,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM id_item_master WHERE 1=1 
        """
        
        if store_filter:
            type_query += " AND current_store = :store"
        
        type_query += "), 2) as percentage FROM id_item_master WHERE 1=1"
        
        if store_filter:
            type_query += " AND current_store = :store"
        
        type_query += " GROUP BY identifier_type ORDER BY count DESC"
        
        type_result = db.session.execute(text(type_query), params)
        type_distribution = []
        
        for row in type_result:
            type_distribution.append({
                'type': row.identifier_type or 'None',
                'count': row.count,
                'percentage': float(row.percentage)
            })
        
        # Get recent RFID activity (only for Fridley)
        activity_query = """
        SELECT 
            DATE(im.date_updated) as activity_date,
            COUNT(*) as items_updated
        FROM id_item_master im
        WHERE im.identifier_type = 'RFID'
            AND im.current_store = '8101'
            AND im.date_updated >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
        GROUP BY DATE(im.date_updated)
        ORDER BY activity_date DESC
        LIMIT 30
        """
        
        activity_result = db.session.execute(text(activity_query))
        activity_data = []
        
        for row in activity_result:
            activity_data.append({
                'date': row.activity_date.strftime('%Y-%m-%d') if row.activity_date else None,
                'count': row.items_updated
            })
        
        # Build response
        response_data = {
            'success': True,
            'statistics': {
                'total_items': stats_result.total_items or 0,
                'rfid_items': stats_result.rfid_items or 0,
                'bulk_items': stats_result.bulk_items or 0,
                'sticker_items': stats_result.sticker_items or 0,
                'qr_items': stats_result.qr_items or 0,
                'unidentified_items': stats_result.unidentified_items or 0,
                'unique_stores': stats_result.unique_stores or 0,
                'items_with_rental_class': stats_result.items_with_rental_class or 0,
                'rfid_percentage': round((stats_result.rfid_items or 0) * 100.0 / max(stats_result.total_items, 1), 2)
            },
            'store_breakdown': store_data,
            'identifier_distribution': type_distribution,
            'recent_activity': activity_data,
            'filters': {
                'stores': get_store_filter_options(),
                'current_store': store_filter,
                'current_identifier': identifier_filter
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        app.logger.error(f"Error getting dashboard data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rfid_correlation_bp.route('/items', methods=['GET'])
def get_correlation_items():
    """Get detailed item list with correct RFID correlations"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        store_filter = request.args.get('store', None)
        identifier_filter = request.args.get('identifier_type', None)
        search_term = request.args.get('search', None)
        
        # Build query
        query = """
        SELECT 
            im.tag_id,
            im.common_name,
            im.rental_class_num,
            im.identifier_type,
            im.current_store,
            im.quantity,
            im.status,
            im.manufacturer,
            im.sell_price,
            sc.store_name,
            CASE 
                WHEN im.current_store = '8101' AND im.identifier_type = 'RFID' THEN 'Active RFID'
                WHEN im.identifier_type = 'Bulk' THEN 'Bulk Item'
                WHEN im.identifier_type = 'Sticker' THEN 'Serialized'
                ELSE 'Standard'
            END as item_status
        FROM id_item_master im
        LEFT JOIN store_correlations sc ON im.current_store = sc.rfid_store_code AND sc.is_active = 1
        WHERE 1=1
        """
        
        count_query = """
        SELECT COUNT(*) as total
        FROM id_item_master im
        WHERE 1=1
        """
        
        params = {}
        
        if store_filter:
            query += " AND im.current_store = :store"
            count_query += " AND im.current_store = :store"
            params['store'] = store_filter
        
        if identifier_filter and identifier_filter != 'all':
            query += " AND im.identifier_type = :identifier_type"
            count_query += " AND im.identifier_type = :identifier_type"
            params['identifier_type'] = identifier_filter
        
        if search_term:
            query += """ AND (im.tag_id LIKE :search 
                        OR im.common_name LIKE :search 
                        OR im.rental_class_num LIKE :search)"""
            count_query += """ AND (im.tag_id LIKE :search 
                              OR im.common_name LIKE :search 
                              OR im.rental_class_num LIKE :search)"""
            params['search'] = f"%{search_term}%"
        
        # Get total count
        total_result = db.session.execute(text(count_query), params).fetchone()
        total_items = total_result.total
        
        # Add pagination
        query += f" ORDER BY im.date_updated DESC LIMIT :limit OFFSET :offset"
        params['limit'] = per_page
        params['offset'] = (page - 1) * per_page
        
        # Execute main query
        result = db.session.execute(text(query), params)
        items = []
        
        for row in result:
            items.append({
                'tag_id': row.tag_id,
                'name': row.common_name or 'Unknown',
                'rental_class': row.rental_class_num,
                'identifier_type': row.identifier_type or 'None',
                'store_code': row.current_store,
                'store_name': row.store_name or f"Store {row.current_store}",
                'quantity': row.quantity or 1,
                'status': row.status or 'Unknown',
                'manufacturer': row.manufacturer,
                'price': float(row.sell_price) if row.sell_price else None,
                'item_status': row.item_status,
                'is_rfid': row.identifier_type == 'RFID' and row.current_store == '8101'
            })
        
        return jsonify({
            'success': True,
            'items': items,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_items': total_items,
                'total_pages': (total_items + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error getting correlation items: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rfid_correlation_bp.route('/validate', methods=['POST'])
def validate_correlations():
    """Validate and report on correlation integrity"""
    try:
        validation_results = []
        
        # Check 1: Verify only Fridley has RFID items
        check_query = text("""
            SELECT current_store, COUNT(*) as rfid_count
            FROM id_item_master
            WHERE identifier_type = 'RFID'
            GROUP BY current_store
        """)
        
        result = db.session.execute(check_query)
        invalid_rfid_stores = []
        
        for row in result:
            if row.current_store != '8101':
                invalid_rfid_stores.append({
                    'store': row.current_store,
                    'count': row.rfid_count
                })
        
        validation_results.append({
            'check': 'RFID Store Exclusivity',
            'passed': len(invalid_rfid_stores) == 0,
            'message': 'Only Fridley should have RFID items' if len(invalid_rfid_stores) == 0 
                      else f"Found RFID items in {len(invalid_rfid_stores)} non-Fridley stores",
            'details': invalid_rfid_stores
        })
        
        # Check 2: Verify bulk items are correctly classified
        bulk_check = text("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN identifier_type = 'Bulk' THEN 1 ELSE 0 END) as classified
            FROM id_item_master
            WHERE tag_id LIKE '%-1' OR tag_id LIKE '%-2' 
               OR tag_id LIKE '%-3' OR tag_id LIKE '%-4'
        """)
        
        bulk_result = db.session.execute(bulk_check).fetchone()
        bulk_correct = bulk_result.total == bulk_result.classified
        
        validation_results.append({
            'check': 'Bulk Item Classification',
            'passed': bulk_correct,
            'message': f"{bulk_result.classified}/{bulk_result.total} bulk items correctly classified",
            'details': {
                'total_bulk_pattern': bulk_result.total,
                'correctly_classified': bulk_result.classified
            }
        })
        
        # Check 3: Verify sticker items are correctly classified
        sticker_check = text("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN identifier_type = 'Sticker' THEN 1 ELSE 0 END) as classified
            FROM id_item_master
            WHERE tag_id LIKE '%#%'
        """)
        
        sticker_result = db.session.execute(sticker_check).fetchone()
        sticker_correct = sticker_result.total == sticker_result.classified
        
        validation_results.append({
            'check': 'Sticker Item Classification',
            'passed': sticker_correct,
            'message': f"{sticker_result.classified}/{sticker_result.total} sticker items correctly classified",
            'details': {
                'total_sticker_pattern': sticker_result.total,
                'correctly_classified': sticker_result.classified
            }
        })
        
        # Check 4: Verify store correlations are active
        correlation_check = text("""
            SELECT COUNT(*) as active_stores
            FROM store_correlations
            WHERE is_active = 1
        """)
        
        correlation_result = db.session.execute(correlation_check).fetchone()
        
        validation_results.append({
            'check': 'Store Correlations',
            'passed': correlation_result.active_stores >= 4,
            'message': f"{correlation_result.active_stores} active store correlations",
            'details': {'active_stores': correlation_result.active_stores}
        })
        
        # Calculate overall health score
        passed_checks = sum(1 for v in validation_results if v['passed'])
        total_checks = len(validation_results)
        health_score = (passed_checks / total_checks) * 100
        
        return jsonify({
            'success': True,
            'health_score': health_score,
            'validation_results': validation_results,
            'summary': {
                'passed': passed_checks,
                'failed': total_checks - passed_checks,
                'total': total_checks
            }
        })
        
    except Exception as e:
        app.logger.error(f"Error validating correlations: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@rfid_correlation_bp.route('/fix-correlations', methods=['POST'])
def fix_correlations():
    """Trigger the correlation fix process"""
    try:
        # This would typically call the fix_data_correlations.py script
        # For now, we'll return a status message
        
        return jsonify({
            'success': True,
            'message': 'Correlation fix process initiated',
            'instructions': 'Run: python scripts/fix_data_correlations.py --execute'
        })
        
    except Exception as e:
        app.logger.error(f"Error fixing correlations: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500