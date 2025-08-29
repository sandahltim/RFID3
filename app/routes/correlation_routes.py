"""
Correlation API Routes
Endpoints for inventory correlation and POS integration
"""

from flask import Blueprint, request, jsonify, current_app
# from flask_login import login_required, current_user
from app import db
from app.services.pos_integration import POSIntegrationService
from app.services.data_validation import DataValidationService
from app.models.correlation_models import (
    InventoryCorrelationMaster,
    POSDataStaging,
    MigrationTracking,
    DataQualityMetrics,
    InventoryIntelligence
)
from sqlalchemy import text
from datetime import datetime
import logging

# Create blueprint
correlation_bp = Blueprint('correlation', __name__, url_prefix='/api/correlation')
logger = logging.getLogger(__name__)

@correlation_bp.route('/status', methods=['GET'])

def get_correlation_status():
    """Get overall correlation system status"""
    try:
        pos_service = POSIntegrationService(db.session)
        status = pos_service.get_correlation_status()
        
        return jsonify({
            'success': True,
            'data': status
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting correlation status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/pos/scan', methods=['GET'])

def scan_pos_files():
    """Scan for new POS CSV files"""
    try:
        pos_service = POSIntegrationService(db.session, logger)
        new_files = pos_service.scan_for_new_files()
        
        return jsonify({
            'success': True,
            'files': new_files,
            'count': len(new_files)
        }), 200
        
    except Exception as e:
        logger.error(f"Error scanning POS files: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/pos/import', methods=['POST'])

def import_pos_file():
    """Import a POS CSV file"""
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        file_type = data.get('file_type', 'equipment')
        
        if not file_path:
            return jsonify({
                'success': False,
                'error': 'file_path is required'
            }), 400
        
        pos_service = POSIntegrationService(db.session, logger)
        result = pos_service.process_csv_file(file_path, file_type)
        
        return jsonify({
            'success': result.get('success', False),
            'data': result
        }), 200 if result.get('success') else 500
        
    except Exception as e:
        logger.error(f"Error importing POS file: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/pos/auto-import', methods=['POST'])

def auto_import_pos_files():
    """Automatically import all new POS CSV files"""
    try:
        pos_service = POSIntegrationService(db.session, logger)
        results = pos_service.auto_process_new_files()
        
        successful = sum(1 for r in results if r.get('success'))
        failed = len(results) - successful
        
        return jsonify({
            'success': True,
            'summary': {
                'total': len(results),
                'successful': successful,
                'failed': failed
            },
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"Error auto-importing POS files: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/correlate', methods=['POST'])

def create_correlation():
    """Create manual correlation between RFID and POS item"""
    try:
        data = request.get_json()
        rfid_tag = data.get('rfid_tag')
        pos_item_num = data.get('pos_item_num')
        confidence = data.get('confidence', 1.0)
        
        if not rfid_tag or not pos_item_num:
            return jsonify({
                'success': False,
                'error': 'rfid_tag and pos_item_num are required'
            }), 400
        
        pos_service = POSIntegrationService(db.session, logger)
        success = pos_service.correlate_rfid_pos(rfid_tag, pos_item_num, confidence)
        
        return jsonify({
            'success': success,
            'message': 'Correlation created' if success else 'Failed to create correlation'
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Error creating correlation: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/validate/<int:correlation_id>', methods=['GET'])

def validate_correlation(correlation_id):
    """Validate a correlation and detect conflicts"""
    try:
        validator = DataValidationService(db.session, logger)
        conflicts = validator.detect_conflicts(correlation_id)
        confidence = validator.calculate_confidence_score(correlation_id)
        
        return jsonify({
            'success': True,
            'correlation_id': correlation_id,
            'conflicts': conflicts,
            'confidence_score': confidence,
            'has_conflicts': len(conflicts) > 0
        }), 200
        
    except Exception as e:
        logger.error(f"Error validating correlation: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/resolve-conflict', methods=['POST'])

def resolve_conflict():
    """Resolve a data conflict"""
    try:
        data = request.get_json()
        correlation_id = data.get('correlation_id')
        conflict = data.get('conflict', {})
        resolution = data.get('resolution')  # USE_RFID, USE_POS, MANUAL, IGNORE
        
        if not correlation_id or not resolution:
            return jsonify({
                'success': False,
                'error': 'correlation_id and resolution are required'
            }), 400
        
        validator = DataValidationService(db.session, logger)
        success = validator.resolve_conflict(
            correlation_id, 
            conflict, 
            resolution,
            'API'
        )
        
        return jsonify({
            'success': success,
            'message': 'Conflict resolved' if success else 'Failed to resolve conflict'
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Error resolving conflict: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/duplicates', methods=['GET'])

def detect_duplicates():
    """Detect duplicate items across systems"""
    try:
        validator = DataValidationService(db.session, logger)
        duplicates = validator.detect_duplicates()
        
        return jsonify({
            'success': True,
            'duplicates': duplicates,
            'count': len(duplicates)
        }), 200
        
    except Exception as e:
        logger.error(f"Error detecting duplicates: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/merge-duplicates', methods=['POST'])

def merge_duplicates():
    """Merge duplicate correlations"""
    try:
        data = request.get_json()
        correlation_ids = data.get('correlation_ids', [])
        master_id = data.get('master_id')
        
        if len(correlation_ids) < 2:
            return jsonify({
                'success': False,
                'error': 'At least 2 correlation_ids required'
            }), 400
        
        validator = DataValidationService(db.session, logger)
        success = validator.merge_duplicates(correlation_ids, master_id)
        
        return jsonify({
            'success': success,
            'message': 'Duplicates merged' if success else 'Failed to merge duplicates'
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Error merging duplicates: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/migrations', methods=['GET'])

def get_migrations():
    """Get active migration tracking"""
    try:
        migrations = MigrationTracking.query.filter(
            MigrationTracking.migration_status.in_(['PLANNED', 'IN_PROGRESS'])
        ).all()
        
        return jsonify({
            'success': True,
            'migrations': [m.to_dict() for m in migrations],
            'count': len(migrations)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting migrations: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/migration/create', methods=['POST'])

def create_migration():
    """Create a new migration plan"""
    try:
        data = request.get_json()
        
        # Find or create correlation
        correlation = InventoryCorrelationMaster.query.filter_by(
            common_name=data.get('item_name')
        ).first()
        
        if not correlation:
            return jsonify({
                'success': False,
                'error': 'Item not found in correlation master'
            }), 404
        
        # Create migration record
        migration = MigrationTracking(
            correlation_id=correlation.correlation_id,
            from_tracking_type=data.get('from_type', 'BULK'),
            to_tracking_type=data.get('to_type', 'RFID'),
            migration_status='PLANNED',
            total_items_to_migrate=data.get('total_items', 0),
            planned_start_date=datetime.strptime(data.get('start_date'), '%Y-%m-%d') if data.get('start_date') else None,
            planned_completion_date=datetime.strptime(data.get('end_date'), '%Y-%m-%d') if data.get('end_date') else None,
            estimated_cost=data.get('estimated_cost', 0),
            estimated_roi_months=data.get('roi_months', 12),
            migration_notes=data.get('notes', '')
        )
        
        db.session.add(migration)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'migration': migration.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating migration: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/quality/issues', methods=['GET'])

def get_quality_issues():
    """Get open data quality issues"""
    try:
        issues = DataQualityMetrics.query.filter_by(
            resolution_status='OPEN'
        ).order_by(
            DataQualityMetrics.severity.desc(),
            DataQualityMetrics.detected_date.desc()
        ).limit(100).all()
        
        summary = db.session.execute(text("""
            SELECT 
                severity,
                COUNT(*) as count
            FROM data_quality_metrics
            WHERE resolution_status = 'OPEN'
            GROUP BY severity
        """)).fetchall()
        
        return jsonify({
            'success': True,
            'issues': [
                {
                    'metric_id': i.metric_id,
                    'correlation_id': i.correlation_id,
                    'issue_type': i.issue_type,
                    'severity': i.severity,
                    'source_system': i.source_system,
                    'field_name': i.field_name,
                    'detected_date': i.detected_date.isoformat() if i.detected_date else None
                }
                for i in issues
            ],
            'summary': {row.severity: row.count for row in summary}
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting quality issues: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/intelligence/<int:correlation_id>', methods=['GET'])

def get_intelligence(correlation_id):
    """Get inventory intelligence for an item"""
    try:
        intelligence = InventoryIntelligence.query.filter_by(
            correlation_id=correlation_id
        ).first()
        
        if not intelligence:
            # Calculate if not exists
            db.session.execute(text("""
                CALL sp_calculate_intelligence(:corr_id)
            """), {'corr_id': correlation_id})
            db.session.commit()
            
            intelligence = InventoryIntelligence.query.filter_by(
                correlation_id=correlation_id
            ).first()
        
        return jsonify({
            'success': True,
            'intelligence': intelligence.to_dict() if intelligence else None
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting intelligence: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@correlation_bp.route('/search', methods=['POST'])

def search_correlations():
    """Search correlations with filters"""
    try:
        data = request.get_json()
        
        query = InventoryCorrelationMaster.query
        
        # Apply filters
        if data.get('rfid_tag'):
            query = query.filter(InventoryCorrelationMaster.rfid_tag_id.like(f"%{data['rfid_tag']}%"))
        
        if data.get('pos_item_num'):
            query = query.filter(InventoryCorrelationMaster.pos_item_num == data['pos_item_num'])
        
        if data.get('common_name'):
            query = query.filter(InventoryCorrelationMaster.common_name.like(f"%{data['common_name']}%"))
        
        if data.get('tracking_type'):
            query = query.filter(InventoryCorrelationMaster.tracking_type == data['tracking_type'])
        
        if data.get('min_confidence'):
            query = query.filter(InventoryCorrelationMaster.confidence_score >= data['min_confidence'])
        
        # Pagination
        page = data.get('page', 1)
        per_page = data.get('per_page', 50)
        
        results = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'items': [item.to_dict() for item in results.items],
            'pagination': {
                'page': results.page,
                'pages': results.pages,
                'per_page': results.per_page,
                'total': results.total
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error searching correlations: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500