# app/routes/store_correlation_api.py
"""
Store Correlation API Routes
Provides RESTful endpoints for managing store correlations and cross-system analytics.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging

from ..services.store_correlation_service import get_store_correlation_service
from ..services.rfid_api_compatibility import get_rfid_api_compatibility_layer
from ..services.enhanced_filtering_service import get_enhanced_filtering_service
from ..utils.exceptions import APIException
from ..services.logger import get_logger

logger = get_logger("store_correlation_api", level=logging.INFO)

# Create blueprint
store_correlation_bp = Blueprint('store_correlation', __name__, url_prefix='/api/correlation')


@store_correlation_bp.route('/mapping', methods=['GET'])
def get_store_mapping():
    """Get store correlation mappings."""
    try:
        correlation_service = get_store_correlation_service()
        
        mapping_type = request.args.get('type', 'both')  # 'rfid_to_pos', 'pos_to_rfid', 'both'
        
        if mapping_type == 'rfid_to_pos':
            mapping = correlation_service.get_rfid_to_pos_mapping()
        elif mapping_type == 'pos_to_rfid':
            mapping = correlation_service.get_pos_to_rfid_mapping()
        else:  # both
            mapping = {
                'rfid_to_pos': correlation_service.get_rfid_to_pos_mapping(),
                'pos_to_rfid': correlation_service.get_pos_to_rfid_mapping()
            }
        
        return jsonify({
            'status': 'success',
            'data': mapping,
            'type': mapping_type
        })
        
    except Exception as e:
        logger.error(f"Error getting store mapping: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@store_correlation_bp.route('/store/<store_code>/info', methods=['GET'])
def get_store_info(store_code):
    """Get comprehensive information for a store."""
    try:
        correlation_service = get_store_correlation_service()
        
        code_type = request.args.get('type', 'auto')  # 'rfid', 'pos', 'auto'
        
        store_info = correlation_service.get_store_info(store_code, code_type)
        
        if not store_info:
            return jsonify({
                'status': 'error',
                'message': f'Store not found: {store_code}'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': store_info
        })
        
    except Exception as e:
        logger.error(f"Error getting store info for {store_code}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@store_correlation_bp.route('/convert', methods=['POST'])
def convert_store_code():
    """Convert between RFID and POS store codes."""
    try:
        data = request.get_json()
        if not data or 'store_code' not in data:
            return jsonify({
                'status': 'error',
                'message': 'store_code is required'
            }), 400
        
        store_code = data['store_code']
        from_type = data.get('from_type', 'auto')
        to_type = data.get('to_type', 'opposite')
        
        correlation_service = get_store_correlation_service()
        
        # Auto-detect source type if needed
        if from_type == 'auto':
            if store_code in ['1', '2', '3', '4', '0']:
                from_type = 'pos'
            elif store_code in ['3607', '6800', '728', '8101', '000']:
                from_type = 'rfid'
            else:
                return jsonify({
                    'status': 'error',
                    'message': f'Cannot auto-detect store code type: {store_code}'
                }), 400
        
        # Determine target type
        if to_type == 'opposite':
            to_type = 'pos' if from_type == 'rfid' else 'rfid'
        
        # Perform conversion
        if from_type == 'rfid' and to_type == 'pos':
            converted_code = correlation_service.correlate_rfid_to_pos(store_code)
        elif from_type == 'pos' and to_type == 'rfid':
            converted_code = correlation_service.correlate_pos_to_rfid(store_code)
        else:
            return jsonify({
                'status': 'error',
                'message': f'Invalid conversion: {from_type} to {to_type}'
            }), 400
        
        if converted_code is None:
            return jsonify({
                'status': 'error',
                'message': f'No correlation found for store: {store_code}'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': {
                'original_code': store_code,
                'original_type': from_type,
                'converted_code': converted_code,
                'converted_type': to_type
            }
        })
        
    except Exception as e:
        logger.error(f"Error converting store code: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@store_correlation_bp.route('/analytics/unified', methods=['GET'])
def get_unified_analytics():
    """Get unified analytics across RFID and POS systems."""
    try:
        store_code = request.args.get('store')
        date_range_days = int(request.args.get('days', 30))
        
        filtering_service = get_enhanced_filtering_service()
        
        analytics = filtering_service.get_unified_store_analytics(
            store_code=store_code if store_code and store_code != 'all' else None,
            date_range_days=date_range_days
        )
        
        return jsonify({
            'status': 'success',
            'data': analytics
        })
        
    except Exception as e:
        logger.error(f"Error getting unified analytics: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@store_correlation_bp.route('/analytics/cross-system', methods=['GET'])
def get_cross_system_analytics():
    """Get cross-system analytics with correlation health."""
    try:
        rfid_store = request.args.get('rfid_store')
        pos_store = request.args.get('pos_store')
        date_range_days = int(request.args.get('days', 30))
        
        correlation_service = get_store_correlation_service()
        
        analytics = correlation_service.get_cross_system_analytics(
            rfid_store_code=rfid_store,
            pos_store_code=pos_store,
            date_range_days=date_range_days
        )
        
        return jsonify({
            'status': 'success',
            'data': analytics
        })
        
    except Exception as e:
        logger.error(f"Error getting cross-system analytics: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@store_correlation_bp.route('/update/item/<tag_id>', methods=['POST'])
def update_item_correlation(tag_id):
    """Update correlation for a specific item."""
    try:
        data = request.get_json() or {}
        force_update = data.get('force_update', False)
        
        correlation_service = get_store_correlation_service()
        
        success = correlation_service.update_item_correlation(
            tag_id=tag_id,
            force_update=force_update
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Updated correlation for item {tag_id}'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to update correlation for item {tag_id}'
            }), 400
        
    except Exception as e:
        logger.error(f"Error updating item correlation: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@store_correlation_bp.route('/update/bulk', methods=['POST'])
def bulk_update_correlations():
    """Bulk update correlations for specified table(s)."""
    try:
        data = request.get_json() or {}
        table_name = data.get('table', 'all')  # 'all', 'items', 'transactions', 'equipment'
        batch_size = int(data.get('batch_size', 1000))
        
        correlation_service = get_store_correlation_service()
        
        results = correlation_service.bulk_update_correlations(
            table_name=table_name,
            batch_size=batch_size
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'update_results': results,
                'table': table_name,
                'batch_size': batch_size
            }
        })
        
    except Exception as e:
        logger.error(f"Error in bulk correlation update: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@store_correlation_bp.route('/health', methods=['GET'])
def get_correlation_health():
    """Get correlation system health status."""
    try:
        correlation_service = get_store_correlation_service()
        
        # Get correlation integrity
        integrity = correlation_service.validate_correlation_integrity()
        
        # Get performance metrics
        filtering_service = get_enhanced_filtering_service()
        performance = filtering_service.validate_filter_performance('correlation')
        
        # Get API compatibility status
        compatibility_layer = get_rfid_api_compatibility_layer()
        compatibility = compatibility_layer.validate_api_compatibility()
        
        health_status = {
            'overall_status': (
                'healthy' if integrity['is_valid'] and compatibility['is_compatible'] 
                else 'issues_detected'
            ),
            'integrity': integrity,
            'performance': performance,
            'api_compatibility': compatibility,
            'checked_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'data': health_status
        })
        
    except Exception as e:
        logger.error(f"Error getting correlation health: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@store_correlation_bp.route('/compatibility/validate', methods=['GET'])
def validate_api_compatibility():
    """Validate RFID API compatibility."""
    try:
        compatibility_layer = get_rfid_api_compatibility_layer()
        
        validation_report = compatibility_layer.validate_api_compatibility()
        
        return jsonify({
            'status': 'success',
            'data': validation_report
        })
        
    except Exception as e:
        logger.error(f"Error validating API compatibility: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@store_correlation_bp.route('/compatibility/guidelines', methods=['GET'])
def get_compatibility_guidelines():
    """Get API compatibility guidelines."""
    try:
        compatibility_layer = get_rfid_api_compatibility_layer()
        
        guidelines = compatibility_layer.get_compatibility_guidelines()
        
        return jsonify({
            'status': 'success',
            'data': guidelines
        })
        
    except Exception as e:
        logger.error(f"Error getting compatibility guidelines: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@store_correlation_bp.route('/performance/validate', methods=['GET'])
def validate_performance():
    """Validate correlation system performance."""
    try:
        query_type = request.args.get('type', 'basic')  # 'basic', 'correlation', 'cross_system'
        
        filtering_service = get_enhanced_filtering_service()
        
        performance_results = filtering_service.validate_filter_performance(query_type)
        
        return jsonify({
            'status': 'success',
            'data': performance_results
        })
        
    except Exception as e:
        logger.error(f"Error validating performance: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@store_correlation_bp.route('/stats', methods=['GET'])
def get_correlation_stats():
    """Get correlation system statistics."""
    try:
        correlation_service = get_store_correlation_service()
        
        # Get basic mapping statistics
        rfid_to_pos = correlation_service.get_rfid_to_pos_mapping()
        pos_to_rfid = correlation_service.get_pos_to_rfid_mapping()
        
        # Get database statistics
        from .. import db
        from sqlalchemy import text
        
        stats_query = text("""
            SELECT 
                (SELECT COUNT(*) FROM store_correlations WHERE is_active = TRUE) as active_correlations,
                (SELECT COUNT(*) FROM id_item_master WHERE rfid_store_code IS NOT NULL) as correlated_items,
                (SELECT COUNT(*) FROM pos_transactions WHERE rfid_store_code IS NOT NULL) as correlated_transactions,
                (SELECT COUNT(*) FROM pos_equipment WHERE rfid_home_store IS NOT NULL) as correlated_equipment,
                (SELECT COUNT(*) FROM id_item_master) as total_items,
                (SELECT COUNT(*) FROM pos_transactions) as total_transactions,
                (SELECT COUNT(*) FROM pos_equipment) as total_equipment
        """)
        
        result = db.session.execute(stats_query).fetchone()
        
        stats = {
            'mappings': {
                'active_correlations': len(rfid_to_pos),
                'rfid_stores': list(rfid_to_pos.keys()),
                'pos_stores': list(pos_to_rfid.keys())
            },
            'coverage': {
                'correlated_items': int(result[1] or 0),
                'total_items': int(result[4] or 0),
                'item_correlation_rate': round((int(result[1] or 0) / max(int(result[4] or 0), 1)) * 100, 1),
                'correlated_transactions': int(result[2] or 0),
                'total_transactions': int(result[5] or 0),
                'transaction_correlation_rate': round((int(result[2] or 0) / max(int(result[5] or 0), 1)) * 100, 1),
                'correlated_equipment': int(result[3] or 0),
                'total_equipment': int(result[6] or 0),
                'equipment_correlation_rate': round((int(result[3] or 0) / max(int(result[6] or 0), 1)) * 100, 1)
            },
            'generated_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'data': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting correlation stats: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# Error handlers
@store_correlation_bp.errorhandler(APIException)
def handle_api_exception(e):
    """Handle custom API exceptions."""
    return jsonify({
        'status': 'error',
        'message': str(e),
        'error_code': getattr(e, 'error_code', 'UNKNOWN'),
        'details': getattr(e, 'details', {})
    }), 500


@store_correlation_bp.errorhandler(400)
def handle_bad_request(e):
    """Handle bad request errors."""
    return jsonify({
        'status': 'error',
        'message': 'Bad request',
        'details': str(e)
    }), 400


@store_correlation_bp.errorhandler(404)
def handle_not_found(e):
    """Handle not found errors.""" 
    return jsonify({
        'status': 'error',
        'message': 'Resource not found',
        'details': str(e)
    }), 404


@store_correlation_bp.errorhandler(500)
def handle_internal_error(e):
    """Handle internal server errors."""
    logger.error(f"Internal error in store correlation API: {e}")
    return jsonify({
        'status': 'error',
        'message': 'Internal server error',
        'details': str(e)
    }), 500