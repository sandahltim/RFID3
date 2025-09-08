# app/routes/unified_store_api.py
"""
Unified Store API Routes for RFID3 System

Provides RESTful endpoints for unified store operations that combine:
- RFID inventory data (id_item_master)
- POS equipment data (pos_equipment) 
- POS transaction data (pos_transactions)

Handles proper store code correlation and cross-system filtering.
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import logging
from sqlalchemy import text, func, and_, or_
from sqlalchemy.exc import SQLAlchemyError

from .. import db
from ..models.db_models import ItemMaster
from ..services.unified_store_filter import get_unified_store_filter_service
from ..services.store_correlation_service import get_store_correlation_service
from ..utils.exceptions import APIException, handle_api_error
from ..services.logger import get_logger

logger = get_logger("unified_store_api", level=logging.INFO)

# Create blueprint
unified_store_bp = Blueprint('unified_store', __name__, url_prefix='/api/unified')

# Version marker
logger.info(f"Deployed unified_store_api.py version: 2025-08-30-v1 at {datetime.now()}")


@unified_store_bp.route('/stores', methods=['GET'])
@handle_api_error
def get_unified_stores():
    """Get all available stores with unified data counts."""
    try:
        unified_filter = get_unified_store_filter_service()
        stores = unified_filter.get_available_stores()
        
        return jsonify({
            'status': 'success',
            'data': {
                'stores': stores,
                'total_stores': len(stores),
                'total_items': sum(store['total_items'] for store in stores),
                'generated_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting unified stores: {e}")
        raise APIException(f"Failed to retrieve store data: {str(e)}")


@unified_store_bp.route('/stores/<store_code>/summary', methods=['GET'])
@handle_api_error 
def get_store_summary(store_code):
    """Get comprehensive summary for a specific store."""
    try:
        unified_filter = get_unified_store_filter_service()
        summary = unified_filter.get_unified_store_summary(store_code)
        
        if 'error' in summary:
            return jsonify({
                'status': 'error', 
                'message': summary['error']
            }), 400
        
        return jsonify({
            'status': 'success',
            'data': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting store {store_code} summary: {e}")
        raise APIException(f"Failed to retrieve store summary: {str(e)}")


@unified_store_bp.route('/stores/<store_code>/items', methods=['GET'])
@handle_api_error
def get_store_items(store_code):
    """Get paginated RFID items for a specific store with unified filtering."""
    try:
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 100)), 1000)
        
        # Get filter parameters
        status_filter = request.args.get('status', 'all')
        type_filter = request.args.get('type', 'all')
        
        # Build unified store filter
        unified_filter = get_unified_store_filter_service()
        where_clause, params = unified_filter.build_unified_store_filter(store_code, 'rfid')
        
        # Base query for RFID items
        base_query = f"""
            SELECT 
                tag_id,
                description,
                status,
                identifier_type,
                current_store,
                home_store,
                last_seen,
                rental_class_num,
                created_at
            FROM id_item_master 
            WHERE {where_clause}
        """
        
        # Add additional filters
        if status_filter != 'all':
            base_query += " AND status = :status_filter"
            params['status_filter'] = status_filter
            
        if type_filter != 'all':
            if type_filter == 'RFID':
                base_query += " AND identifier_type IS NULL AND tag_id REGEXP '^[0-9A-Fa-f]{16,}$'"
            elif type_filter == 'Serialized':
                base_query += " AND identifier_type IN ('QR', 'Sticker')"
            else:
                base_query += " AND identifier_type = :type_filter"
                params['type_filter'] = type_filter
        
        # Add pagination
        offset = (page - 1) * per_page
        paginated_query = base_query + f" ORDER BY last_seen DESC LIMIT {per_page} OFFSET {offset}"
        
        # Execute queries
        items_result = db.session.execute(text(paginated_query), params)
        items = [dict(row._mapping) for row in items_result.fetchall()]
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM id_item_master WHERE {where_clause}"
        if status_filter != 'all':
            count_query += " AND status = :status_filter"
        if type_filter != 'all':
            if type_filter == 'RFID':
                count_query += " AND identifier_type IS NULL AND tag_id REGEXP '^[0-9A-Fa-f]{16,}$'"
            elif type_filter == 'Serialized':
                count_query += " AND identifier_type IN ('QR', 'Sticker')"
            else:
                count_query += " AND identifier_type = :type_filter"
                
        total_result = db.session.execute(text(count_query), params)
        total_items = total_result.scalar()
        
        return jsonify({
            'status': 'success',
            'data': {
                'items': items,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_items': total_items,
                    'total_pages': (total_items + per_page - 1) // per_page,
                    'has_next': (page * per_page) < total_items,
                    'has_prev': page > 1
                },
                'filters': {
                    'store': store_code,
                    'status': status_filter,
                    'type': type_filter
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting store {store_code} items: {e}")
        raise APIException(f"Failed to retrieve store items: {str(e)}")


@unified_store_bp.route('/stores/<store_code>/equipment', methods=['GET'])
@handle_api_error
def get_store_equipment(store_code):
    """Get POS equipment data for a specific store."""
    try:
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 100)), 1000)
        
        # Build unified store filter for POS equipment
        unified_filter = get_unified_store_filter_service()
        where_clause, params = unified_filter.build_unified_store_filter(store_code, 'pos_equipment')
        
        # Base query for POS equipment
        base_query = f"""
            SELECT 
                id,
                contract_no,
                description,
                current_store,
                pos_store_code,
                item_value,
                created_at,
                updated_at
            FROM pos_equipment 
            WHERE {where_clause}
        """
        
        # Add pagination
        offset = (page - 1) * per_page
        paginated_query = base_query + f" ORDER BY updated_at DESC LIMIT {per_page} OFFSET {offset}"
        
        # Execute queries
        equipment_result = db.session.execute(text(paginated_query), params)
        equipment = [dict(row._mapping) for row in equipment_result.fetchall()]
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM pos_equipment WHERE {where_clause}"
        total_result = db.session.execute(text(count_query), params)
        total_equipment = total_result.scalar()
        
        return jsonify({
            'status': 'success',
            'data': {
                'equipment': equipment,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_items': total_equipment,
                    'total_pages': (total_equipment + per_page - 1) // per_page,
                    'has_next': (page * per_page) < total_equipment,
                    'has_prev': page > 1
                },
                'store_code': store_code
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting store {store_code} equipment: {e}")
        raise APIException(f"Failed to retrieve store equipment: {str(e)}")


@unified_store_bp.route('/stores/<store_code>/analytics', methods=['GET'])
@handle_api_error
def get_store_analytics(store_code):
    """Get comprehensive analytics for a specific store."""
    try:
        days = int(request.args.get('days', 30))
        date_threshold = datetime.now() - timedelta(days=days)
        
        # Build unified store filter
        unified_filter = get_unified_store_filter_service()
        
        # Get RFID analytics
        rfid_where, rfid_params = unified_filter.build_unified_store_filter(store_code, 'rfid')
        rfid_analytics = db.session.execute(text(f"""
            SELECT 
                COUNT(*) as total_items,
                COUNT(CASE WHEN status = 'Ready to Rent' THEN 1 END) as available_items,
                COUNT(CASE WHEN status IN ('On Rent', 'Delivered', 'Out to Customer') THEN 1 END) as rented_items,
                COUNT(CASE WHEN status IN ('Repair', 'Needs to be Inspected') THEN 1 END) as service_items,
                COUNT(CASE WHEN identifier_type IS NULL AND tag_id REGEXP '^[0-9A-Fa-f]{{16,}}$' THEN 1 END) as rfid_items,
                COUNT(CASE WHEN identifier_type IN ('QR', 'Sticker') THEN 1 END) as serialized_items
            FROM id_item_master 
            WHERE {rfid_where}
        """), rfid_params).fetchone()
        
        # Get POS equipment analytics
        pos_where, pos_params = unified_filter.build_unified_store_filter(store_code, 'pos_equipment') 
        pos_analytics = db.session.execute(text(f"""
            SELECT 
                COUNT(*) as total_equipment,
                COALESCE(SUM(item_value), 0) as total_value,
                AVG(item_value) as avg_value
            FROM pos_equipment 
            WHERE {pos_where}
        """), pos_params).fetchone()
        
        # Get transaction analytics
        trans_where, trans_params = unified_filter.build_unified_store_filter(store_code, 'pos_transactions')
        trans_analytics = db.session.execute(text(f"""
            SELECT 
                COUNT(*) as total_transactions,
                COUNT(CASE WHEN import_date >= :date_threshold THEN 1 END) as recent_transactions
            FROM pos_transactions 
            WHERE {trans_where}
        """), {**trans_params, 'date_threshold': date_threshold}).fetchone()
        
        # Calculate utilization rate
        total_items = rfid_analytics[0] if rfid_analytics[0] else 0
        rented_items = rfid_analytics[2] if rfid_analytics[2] else 0
        utilization_rate = round((rented_items / max(total_items, 1)) * 100, 2)
        
        analytics = {
            'store_code': store_code,
            'analysis_period_days': days,
            'rfid_inventory': {
                'total_items': total_items,
                'available_items': rfid_analytics[1] if rfid_analytics[1] else 0,
                'rented_items': rented_items,
                'service_items': rfid_analytics[3] if rfid_analytics[3] else 0,
                'rfid_items': rfid_analytics[4] if rfid_analytics[4] else 0,
                'serialized_items': rfid_analytics[5] if rfid_analytics[5] else 0,
                'utilization_rate': utilization_rate
            },
            'pos_equipment': {
                'total_equipment': pos_analytics[0] if pos_analytics[0] else 0,
                'total_value': float(pos_analytics[1]) if pos_analytics[1] else 0.0,
                'avg_value': float(pos_analytics[2]) if pos_analytics[2] else 0.0
            },
            'transactions': {
                'total_transactions': trans_analytics[0] if trans_analytics[0] else 0,
                'recent_transactions': trans_analytics[1] if trans_analytics[1] else 0
            },
            'generated_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'data': analytics
        })
        
    except Exception as e:
        logger.error(f"Error getting store {store_code} analytics: {e}")
        raise APIException(f"Failed to retrieve store analytics: {str(e)}")


@unified_store_bp.route('/health', methods=['GET'])
@handle_api_error
def get_unified_health():
    """Get health status of unified store filtering system."""
    try:
        unified_filter = get_unified_store_filter_service()
        health = unified_filter.validate_store_filtering_health()
        
        return jsonify({
            'status': 'success',
            'data': health
        })
        
    except Exception as e:
        logger.error(f"Error getting unified health: {e}")
        raise APIException(f"Failed to retrieve health status: {str(e)}")


@unified_store_bp.route('/correlation/test', methods=['POST'])
@handle_api_error
def test_store_correlation():
    """Test store code correlation functionality."""
    try:
        data = request.get_json()
        if not data or 'store_codes' not in data:
            return jsonify({
                'status': 'error',
                'message': 'store_codes array is required'
            }), 400
        
        correlation_service = get_store_correlation_service()
        unified_filter = get_unified_store_filter_service()
        
        test_results = []
        for store_code in data['store_codes']:
            # Test correlation
            if store_code in ['0', '1', '2', '3', '4']:
                rfid_code = correlation_service.correlate_pos_to_rfid(store_code)
                correlation_result = f"POS {store_code} -> RFID {rfid_code}"
            elif store_code in ['000', '3607', '6800', '728', '8101']:
                pos_code = correlation_service.correlate_rfid_to_pos(store_code)
                correlation_result = f"RFID {store_code} -> POS {pos_code}"
            else:
                correlation_result = f"Unknown format: {store_code}"
            
            # Test filtering
            summary = unified_filter.get_unified_store_summary(store_code)
            
            test_results.append({
                'input_code': store_code,
                'correlation': correlation_result,
                'summary': summary,
                'success': 'error' not in summary
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'test_results': test_results,
                'test_count': len(test_results),
                'success_count': sum(1 for r in test_results if r['success'])
            }
        })
        
    except Exception as e:
        logger.error(f"Error testing store correlation: {e}")
        raise APIException(f"Store correlation test failed: {str(e)}")


# Error handlers
@unified_store_bp.errorhandler(APIException)
def handle_api_exception(e):
    """Handle custom API exceptions."""
    return jsonify({
        'status': 'error',
        'message': str(e),
        'timestamp': datetime.now().isoformat()
    }), 500


@unified_store_bp.errorhandler(400)
def handle_bad_request(e):
    """Handle bad request errors."""
    return jsonify({
        'status': 'error',
        'message': 'Bad request',
        'details': str(e),
        'timestamp': datetime.now().isoformat()
    }), 400


@unified_store_bp.errorhandler(500)
def handle_internal_error(e):
    """Handle internal server errors."""
    logger.error(f"Internal error in unified store API: {e}")
    return jsonify({
        'status': 'error',
        'message': 'Internal server error',
        'timestamp': datetime.now().isoformat()
    }), 500