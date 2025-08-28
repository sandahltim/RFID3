# app/routes/pos_routes.py
# POS API Routes
# Created: 2025-08-28
from flask import Blueprint, request, jsonify, current_app, render_template
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_, text
from app import db
from app.models.pos_models import (
    POSTransaction, POSTransactionItem, POSCustomer,
    POSRFIDCorrelation, POSInventoryDiscrepancy, POSAnalytics,
    POSImportLog
)
from app.models.db_models import ItemMaster
from app.services.pos_import_service import pos_import_service
from app.services.pos_correlation_service import pos_correlation_service
from app.services.logger import get_logger

logger = get_logger(__name__)

# Create Blueprint
pos_bp = Blueprint('pos', __name__, url_prefix='/api/pos')


@pos_bp.route('/import', methods=['POST'])
def import_pos_data():
    """Import POS data from CSV files."""
    try:
        # Get import parameters
        data = request.get_json() or {}
        base_path = data.get('base_path', '/home/tim/RFID3/shared/POR')
        
        # Run import
        results = pos_import_service.import_all_pos_data(base_path)
        
        return jsonify({
            'success': True,
            'message': f"Imported {results['total_imported']} records",
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"POS import failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@pos_bp.route('/correlate', methods=['POST'])
def correlate_pos_rfid():
    """Correlate POS items with RFID inventory."""
    try:
        data = request.get_json() or {}
        contract_no = data.get('contract_no')
        
        if contract_no:
            # Correlate single transaction
            results = pos_correlation_service.correlate_transaction_items(contract_no)
            
            # Detect discrepancies
            discrepancies = pos_correlation_service.detect_discrepancies(contract_no)
            results['discrepancies'] = discrepancies
        else:
            # Batch correlation
            limit = data.get('limit', 100)
            results = pos_correlation_service.correlate_all_transactions(limit)
        
        return jsonify({
            'success': True,
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"Correlation failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@pos_bp.route('/transactions', methods=['GET'])
def get_transactions():
    """Get POS transactions with pagination and filters."""
    try:
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        # Filters
        store_no = request.args.get('store_no')
        status = request.args.get('status')
        customer_no = request.args.get('customer_no')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        # Build query
        query = POSTransaction.query
        
        if store_no:
            query = query.filter_by(store_no=store_no)
        if status:
            query = query.filter_by(status=status)
        if customer_no:
            query = query.filter_by(customer_no=customer_no)
        if date_from:
            query = query.filter(POSTransaction.contract_date >= datetime.fromisoformat(date_from))
        if date_to:
            query = query.filter(POSTransaction.contract_date <= datetime.fromisoformat(date_to))
        
        # Order by date descending
        query = query.order_by(POSTransaction.contract_date.desc())
        
        # Paginate
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'data': [t.to_dict() for t in paginated.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginated.total,
                'pages': paginated.pages
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get transactions: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@pos_bp.route('/transaction/<contract_no>', methods=['GET'])
def get_transaction_detail(contract_no):
    """Get detailed POS transaction with items and correlations."""
    try:
        # Get transaction
        transaction = POSTransaction.query.filter_by(contract_no=contract_no).first()
        if not transaction:
            return jsonify({
                'success': False,
                'message': 'Transaction not found'
            }), 404
        
        # Get transaction items with correlations
        items = db.session.query(
            POSTransactionItem,
            POSRFIDCorrelation
        ).outerjoin(
            POSRFIDCorrelation,
            and_(
                POSTransactionItem.item_num == POSRFIDCorrelation.pos_item_num,
                POSRFIDCorrelation.is_active == True
            )
        ).filter(
            POSTransactionItem.contract_no == contract_no
        ).all()
        
        # Format response
        response = transaction.to_dict()
        response['items'] = []
        
        for item, correlation in items:
            item_data = item.to_dict()
            if correlation:
                item_data['correlation'] = {
                    'rfid_class': correlation.rfid_rental_class_num,
                    'rfid_name': correlation.rfid_common_name,
                    'confidence': float(correlation.confidence_score) if correlation.confidence_score else 0,
                    'type': correlation.correlation_type
                }
            else:
                item_data['correlation'] = None
            response['items'].append(item_data)
        
        # Get customer info
        if transaction.customer_no:
            customer = POSCustomer.query.filter_by(cnum=transaction.customer_no).first()
            if customer:
                response['customer'] = customer.to_dict()
        
        # Get discrepancies
        discrepancies = POSInventoryDiscrepancy.query.filter_by(
            contract_no=contract_no,
            status='open'
        ).all()
        response['discrepancies'] = [d.to_dict() for d in discrepancies]
        
        return jsonify({
            'success': True,
            'data': response
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get transaction detail: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@pos_bp.route('/discrepancies', methods=['GET'])
def get_discrepancies():
    """Get POS-RFID discrepancies."""
    try:
        # Filters
        status = request.args.get('status', 'open')
        severity = request.args.get('severity')
        discrepancy_type = request.args.get('type')
        limit = request.args.get('limit', 100, type=int)
        
        # Build query
        query = POSInventoryDiscrepancy.query
        
        if status:
            query = query.filter_by(status=status)
        if severity:
            query = query.filter_by(severity=severity)
        if discrepancy_type:
            query = query.filter_by(discrepancy_type=discrepancy_type)
        
        # Order by severity and date
        query = query.order_by(
            text("FIELD(severity, 'critical', 'high', 'medium', 'low')"),
            POSInventoryDiscrepancy.created_at.desc()
        )
        
        discrepancies = query.limit(limit).all()
        
        return jsonify({
            'success': True,
            'data': [d.to_dict() for d in discrepancies],
            'count': len(discrepancies)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get discrepancies: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@pos_bp.route('/discrepancy/<int:discrepancy_id>/resolve', methods=['POST'])
def resolve_discrepancy(discrepancy_id):
    """Resolve a POS-RFID discrepancy."""
    try:
        data = request.get_json() or {}
        resolution_notes = data.get('resolution_notes', '')
        resolved_by = data.get('resolved_by', 'system')
        
        discrepancy = POSInventoryDiscrepancy.query.get(discrepancy_id)
        if not discrepancy:
            return jsonify({
                'success': False,
                'message': 'Discrepancy not found'
            }), 404
        
        discrepancy.status = 'resolved'
        discrepancy.resolution_notes = resolution_notes
        discrepancy.resolved_by = resolved_by
        discrepancy.resolved_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Discrepancy resolved'
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to resolve discrepancy: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@pos_bp.route('/analytics/dashboard', methods=['GET'])
def get_analytics_dashboard():
    """Get POS analytics dashboard data."""
    try:
        # Get date range
        days = request.args.get('days', 30, type=int)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get correlation statistics
        correlation_stats = pos_correlation_service.analyze_correlation_quality()
        
        # Calculate revenue metrics
        revenue_data = db.session.query(
            func.date(POSTransaction.contract_date).label('date'),
            func.sum(POSTransaction.total).label('revenue'),
            func.count(POSTransaction.id).label('transactions')
        ).filter(
            POSTransaction.contract_date >= start_date
        ).group_by(
            func.date(POSTransaction.contract_date)
        ).all()
        
        # Calculate top items by revenue
        top_items = db.session.query(
            POSTransactionItem.item_num,
            POSTransactionItem.desc,
            func.sum(POSTransactionItem.price * POSTransactionItem.qty).label('total_revenue'),
            func.sum(POSTransactionItem.qty).label('total_quantity')
        ).join(
            POSTransaction,
            POSTransactionItem.contract_no == POSTransaction.contract_no
        ).filter(
            POSTransaction.contract_date >= start_date
        ).group_by(
            POSTransactionItem.item_num,
            POSTransactionItem.desc
        ).order_by(
            func.sum(POSTransactionItem.price * POSTransactionItem.qty).desc()
        ).limit(10).all()
        
        # Calculate inventory turnover for top items
        turnover_data = []
        for item in top_items[:5]:
            # Get correlation for this item
            correlation = POSRFIDCorrelation.query.filter_by(
                pos_item_num=item.item_num,
                is_active=True
            ).first()
            
            if correlation and correlation.rfid_rental_class_num:
                turnover = pos_correlation_service.calculate_inventory_turnover(
                    correlation.rfid_rental_class_num,
                    days
                )
                turnover['pos_item'] = item.item_num
                turnover['description'] = item.desc
                turnover_data.append(turnover)
        
        # Format response
        response = {
            'period': {
                'days': days,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'correlation_quality': correlation_stats,
            'revenue': {
                'daily': [
                    {
                        'date': r.date.isoformat(),
                        'revenue': float(r.revenue) if r.revenue else 0,
                        'transactions': r.transactions
                    }
                    for r in revenue_data
                ],
                'total': sum(float(r.revenue) if r.revenue else 0 for r in revenue_data)
            },
            'top_items': [
                {
                    'item_num': item.item_num,
                    'description': item.desc,
                    'revenue': float(item.total_revenue) if item.total_revenue else 0,
                    'quantity': item.total_quantity
                }
                for item in top_items
            ],
            'inventory_turnover': turnover_data,
            'discrepancies': {
                'open': POSInventoryDiscrepancy.query.filter_by(status='open').count(),
                'critical': POSInventoryDiscrepancy.query.filter_by(
                    status='open',
                    severity='critical'
                ).count(),
                'high': POSInventoryDiscrepancy.query.filter_by(
                    status='open',
                    severity='high'
                ).count()
            }
        }
        
        return jsonify({
            'success': True,
            'data': response
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get analytics dashboard: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@pos_bp.route('/correlation/manual', methods=['POST'])
def create_manual_correlation():
    """Create manual POS-RFID correlation."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['pos_item_num', 'rfid_rental_class_num']
        for field in required:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Check if correlation already exists
        existing = POSRFIDCorrelation.query.filter_by(
            pos_item_num=data['pos_item_num'],
            rfid_rental_class_num=data['rfid_rental_class_num'],
            is_active=True
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'message': 'Correlation already exists'
            }), 400
        
        # Get RFID item details
        rfid_item = ItemMaster.query.filter_by(
            rental_class_num=data['rfid_rental_class_num']
        ).first()
        
        # Create correlation
        correlation = POSRFIDCorrelation(
            pos_item_num=data['pos_item_num'],
            pos_item_desc=data.get('pos_item_desc'),
            rfid_rental_class_num=data['rfid_rental_class_num'],
            rfid_common_name=rfid_item.common_name if rfid_item else None,
            correlation_type='manual',
            confidence_score=1.0,
            match_criteria={'method': 'manual', 'user': data.get('created_by', 'system')},
            created_by=data.get('created_by', 'system'),
            verified_at=datetime.utcnow(),
            verified_by=data.get('created_by', 'system')
        )
        
        db.session.add(correlation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Correlation created successfully',
            'data': correlation.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Failed to create manual correlation: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@pos_bp.route('/import/status', methods=['GET'])
def get_import_status():
    """Get POS import history and status."""
    try:
        # Get recent imports
        imports = POSImportLog.query.order_by(
            POSImportLog.created_at.desc()
        ).limit(10).all()
        
        return jsonify({
            'success': True,
            'data': [log.to_dict() for log in imports]
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get import status: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@pos_bp.route('/dashboard')
def pos_dashboard():
    """Render POS correlation dashboard."""
    return render_template('pos_dashboard.html')


