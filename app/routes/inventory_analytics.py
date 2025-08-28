from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db
from ..models.db_models import (
    ItemMaster, Transaction, ItemUsageHistory, InventoryHealthAlert, 
    InventoryConfig, UserRentalClassMapping, RentalClassMapping
)
from ..services.logger import get_logger
from ..utils.exceptions import DatabaseException, ValidationException, handle_api_error, log_and_handle_exception
from sqlalchemy import func, desc, and_, or_, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import json
from decimal import Decimal

logger = get_logger(__name__)

inventory_analytics_bp = Blueprint('inventory_analytics', __name__)

# Version marker
logger.info("Deployed inventory_analytics.py version: 2025-08-27-POS-v1 at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

def build_global_filters(store_filter='all', type_filter='all'):
    """Build SQLAlchemy filters for store and inventory type selection."""
    filters = []
    
    if store_filter and store_filter != 'all':
        # Filter by either home_store or current_store
        filters.append(
            or_(ItemMaster.home_store == store_filter,
                ItemMaster.current_store == store_filter)
        )
        logger.debug(f"Applied store filter: {store_filter}")
    
    if type_filter and type_filter != 'all':
        filters.append(ItemMaster.identifier_type == type_filter)
        logger.debug(f"Applied inventory type filter: {type_filter}")
    
    return filters

def apply_global_filters(query, request_args=None):
    """Apply store and inventory type filters to any ItemMaster query."""
    if request_args is None:
        request_args = request.args
    
    store_filter = request_args.get('store', 'all')
    type_filter = request_args.get('type', 'all')
    
    filters = build_global_filters(store_filter, type_filter)
    for filter_condition in filters:
        query = query.filter(filter_condition)
    
    return query

@inventory_analytics_bp.route('/tab/6')
def inventory_analytics_view():
    """Main Inventory & Analytics dashboard page."""
    logger.info("Loading Inventory & Analytics dashboard at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    return render_template('inventory_analytics.html')

@inventory_analytics_bp.route('/api/inventory/dashboard_summary', methods=['GET'])
@handle_api_error
def get_dashboard_summary():
    """Get high-level dashboard metrics with store and inventory type filtering."""
    
    # Check if we should use backup data during refresh
    try:
        from ..services.backup_fallback import backup_service
        if backup_service.should_use_backup():
            logger.info("API refresh in progress, using backup data")
            return jsonify(backup_service.load_backup_data())
    except Exception as e:
        logger.warning(f"Backup fallback failed, proceeding with live data: {e}")
    
    session = None
    try:
        session = db.session()
        
        # Get filter parameters
        store_filter = request.args.get('store', 'all')
        type_filter = request.args.get('type', 'all')
        logger.info(f"Fetching dashboard summary with filters: store={store_filter}, type={type_filter}")
        
        # Build base query with global filters
        base_query = session.query(ItemMaster)
        base_query = apply_global_filters(base_query)
        
        # Get basic inventory counts with filters applied
        total_items = base_query.count()
        items_on_rent = base_query.filter(ItemMaster.status.in_(['On Rent', 'Delivered'])).count()
        items_available = base_query.filter(ItemMaster.status == 'Ready to Rent').count()
        items_in_service = base_query.filter(ItemMaster.status.in_(['Repair', 'Needs to be Inspected'])).count()
        
        # Calculate utilization rate
        utilization_rate = round((items_on_rent / max(total_items, 1)) * 100, 2)
        
        # Get active alerts by severity
        alert_counts = session.query(
            InventoryHealthAlert.severity,
            func.count(InventoryHealthAlert.id).label('count')
        ).filter(
            InventoryHealthAlert.status == 'active'
        ).group_by(InventoryHealthAlert.severity).all()
        
        alerts_by_severity = {alert.severity: alert.count for alert in alert_counts}
        
        # Get recent activity (last 7 days)
        recent_activity_date = datetime.now() - timedelta(days=7)
        recent_scans = session.query(func.count(Transaction.id)).filter(
            Transaction.scan_date >= recent_activity_date
        ).scalar() or 0
        
        # Calculate inventory health score (0-100)
        health_score = calculate_inventory_health_score(session, {
            'total_items': total_items,
            'active_alerts': alerts_by_severity,
            'utilization_rate': utilization_rate,
            'recent_activity': recent_scans
        })
        
        summary = {
            'inventory_overview': {
                'total_items': total_items,
                'items_on_rent': items_on_rent,
                'items_available': items_available,
                'items_in_service': items_in_service,
                'utilization_rate': utilization_rate
            },
            'health_metrics': {
                'health_score': health_score,
                'active_alerts': sum(alerts_by_severity.values()),
                'critical_alerts': alerts_by_severity.get('critical', 0),
                'high_alerts': alerts_by_severity.get('high', 0),
                'medium_alerts': alerts_by_severity.get('medium', 0),
                'low_alerts': alerts_by_severity.get('low', 0)
            },
            'activity_metrics': {
                'recent_scans': recent_scans,
                'scan_rate_per_day': round(recent_scans / 7, 1)
            },
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Dashboard summary calculated: {summary['inventory_overview']['total_items']} total items, health score: {health_score}")
        return jsonify(summary)
        
    except Exception as e:
        logger.error(f"Error fetching dashboard summary: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@inventory_analytics_bp.route('/api/inventory/business_intelligence', methods=['GET'])
@handle_api_error
def get_business_intelligence():
    """Get POS business intelligence metrics with real data."""
    session = None
    try:
        session = db.session()
        
        # Get filter parameters
        store_filter = request.args.get('store', 'all')
        type_filter = request.args.get('type', 'all')
        logger.info(f"Fetching business intelligence with filters: store={store_filter}, type={type_filter}")
        
        # Build base query with filters
        base_query = session.query(ItemMaster)
        base_query = apply_global_filters(base_query)
        
        # Store Distribution Analysis
        store_distribution = session.query(
            ItemMaster.current_store,
            func.count(ItemMaster.tag_id).label('item_count'),
            func.avg(ItemMaster.sell_price).label('avg_sell_price'),
            func.sum(ItemMaster.turnover_ytd).label('total_turnover')
        ).filter(*build_global_filters(store_filter, type_filter)).group_by(ItemMaster.current_store).all()
        
        # Inventory Type Distribution
        type_distribution = base_query.with_entities(
            ItemMaster.identifier_type,
            func.count(ItemMaster.tag_id).label('count'),
            func.avg(ItemMaster.sell_price).label('avg_price')
        ).group_by(ItemMaster.identifier_type).all()
        
        # Financial Analytics (Real POS Data)
        financial_data = base_query.filter(
            or_(ItemMaster.sell_price.isnot(None), 
                ItemMaster.turnover_ytd.isnot(None),
                ItemMaster.repair_cost_ltd.isnot(None))
        ).with_entities(
            func.count(ItemMaster.tag_id).label('items_with_financial_data'),
            func.sum(ItemMaster.sell_price).label('total_inventory_value'),
            func.avg(ItemMaster.sell_price).label('avg_sell_price'),
            func.sum(ItemMaster.turnover_ytd).label('total_turnover_ytd'),
            func.avg(ItemMaster.turnover_ytd).label('avg_turnover_ytd'),
            func.sum(ItemMaster.repair_cost_ltd).label('total_repair_costs'),
            func.avg(ItemMaster.repair_cost_ltd).label('avg_repair_cost')
        ).first()
        
        # Top Manufacturers by Item Count
        top_manufacturers = base_query.filter(
            ItemMaster.manufacturer.isnot(None),
            ItemMaster.manufacturer != ''
        ).with_entities(
            ItemMaster.manufacturer,
            func.count(ItemMaster.tag_id).label('item_count'),
            func.avg(ItemMaster.sell_price).label('avg_price')
        ).group_by(ItemMaster.manufacturer).order_by(desc('item_count')).limit(10).all()
        
        # High Value Items (top 10% by sell_price) - MariaDB compatible approach
        price_threshold_query = base_query.filter(ItemMaster.sell_price.isnot(None))
        if price_threshold_query.count() > 0:
            # Get all prices and calculate 90th percentile manually (MariaDB compatible)
            all_prices = [item.sell_price for item in price_threshold_query.all() if item.sell_price]
            if all_prices:
                all_prices.sort()
                percentile_index = int(0.9 * len(all_prices))
                price_percentile = float(all_prices[min(percentile_index, len(all_prices) - 1)])
                
                high_value_items = base_query.filter(
                    ItemMaster.sell_price >= price_percentile
                ).count()
            else:
                high_value_items = 0
                price_percentile = 0
        else:
            high_value_items = 0
            price_percentile = 0
        
        # Convert Decimal objects to float for JSON serialization
        def decimal_to_float(value):
            if isinstance(value, Decimal):
                return float(value)
            return value
        
        # Build response
        business_intel = {
            'store_analysis': {
                'distribution': [{
                    'store_code': store.current_store or 'Unassigned',
                    'item_count': store.item_count,
                    'avg_sell_price': decimal_to_float(store.avg_sell_price) if store.avg_sell_price else 0,
                    'total_turnover': decimal_to_float(store.total_turnover) if store.total_turnover else 0
                } for store in store_distribution],
                'total_stores': len([s for s in store_distribution if s.current_store])
            },
            'inventory_type_analysis': {
                'distribution': [{
                    'type': type_dist.identifier_type or 'Untyped',
                    'count': type_dist.count,
                    'avg_price': decimal_to_float(type_dist.avg_price) if type_dist.avg_price else 0
                } for type_dist in type_distribution],
                'total_types': len(type_distribution)
            },
            'financial_insights': {
                'items_with_data': financial_data.items_with_financial_data or 0,
                'total_inventory_value': decimal_to_float(financial_data.total_inventory_value) if financial_data.total_inventory_value else 0,
                'avg_sell_price': decimal_to_float(financial_data.avg_sell_price) if financial_data.avg_sell_price else 0,
                'total_turnover_ytd': decimal_to_float(financial_data.total_turnover_ytd) if financial_data.total_turnover_ytd else 0,
                'avg_turnover_ytd': decimal_to_float(financial_data.avg_turnover_ytd) if financial_data.avg_turnover_ytd else 0,
                'total_repair_costs': decimal_to_float(financial_data.total_repair_costs) if financial_data.total_repair_costs else 0,
                'avg_repair_cost': decimal_to_float(financial_data.avg_repair_cost) if financial_data.avg_repair_cost else 0,
                'high_value_items': high_value_items,
                'high_value_threshold': decimal_to_float(price_percentile) if price_percentile else 0
            },
            'manufacturer_insights': {
                'top_manufacturers': [{
                    'manufacturer': mfr.manufacturer,
                    'item_count': mfr.item_count,
                    'avg_price': decimal_to_float(mfr.avg_price) if mfr.avg_price else 0
                } for mfr in top_manufacturers]
            },
            'filter_context': {
                'store_filter': store_filter,
                'type_filter': type_filter,
                'total_items_in_view': base_query.count()
            },
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Business intelligence calculated for {business_intel['filter_context']['total_items_in_view']} items")
        return jsonify(business_intel)
        
    except Exception as e:
        logger.error(f"Error fetching business intelligence: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@inventory_analytics_bp.route('/api/inventory/alerts', methods=['GET'])
@handle_api_error
def get_inventory_alerts():
    """Get inventory health alerts with filtering and pagination."""
    session = None
    try:
        session = db.session()
        
        # Get query parameters
        severity = request.args.get('severity')
        alert_type = request.args.get('alert_type')
        status = request.args.get('status', 'active')
        limit = min(int(request.args.get('limit', 50)), 200)  # Cap at 200
        offset = int(request.args.get('offset', 0))
        
        # Build query
        query = session.query(InventoryHealthAlert)
        
        # Apply filters
        if status != 'all':
            query = query.filter(InventoryHealthAlert.status == status)
        if severity:
            query = query.filter(InventoryHealthAlert.severity == severity)
        if alert_type:
            query = query.filter(InventoryHealthAlert.alert_type == alert_type)
        
        # Get total count for pagination
        total_count = query.count()
        
        # Apply ordering and pagination
        alerts = query.order_by(
            desc(InventoryHealthAlert.severity),
            desc(InventoryHealthAlert.created_at)
        ).limit(limit).offset(offset).all()
        
        result = {
            'alerts': [alert.to_dict() for alert in alerts],
            'pagination': {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_count
            }
        }
        
        logger.info(f"Returning {len(alerts)} inventory alerts (total: {total_count})")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error fetching inventory alerts: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@inventory_analytics_bp.route('/api/inventory/stale_items', methods=['GET'])
def get_stale_items():
    """🚀 ENHANCED: Get items with TRUE activity-based stale analysis including Touch Scans!"""
    session = None
    try:
        session = db.session()
        logger.info("🚀 Fetching stale items with GAME-CHANGING transaction integration!")
        
        # Get configuration
        config = get_alert_config(session)
        thresholds = config.get('stale_item_days', {'default': 30})
        default_days = thresholds.get('default', 30)
        resale_days = thresholds.get('resale', 7)
        pack_days = thresholds.get('pack', 14)
        
        logger.info(f"🎯 Thresholds - Default: {default_days}, Resale: {resale_days}, Pack: {pack_days} days")
        
        # 🔥 ENHANCED QUERY: True activity-based stale analysis INCLUDING Touch Scans!
        stale_query = text("""
        SELECT 
            m.tag_id,
            m.serial_number,
            m.client_name,
            m.rental_class_num,
            m.common_name,
            m.quality,
            m.bin_location,
            m.status,
            m.last_contract_num,
            m.notes,
            m.date_last_scanned as master_last_scan,
            u.category,
            u.subcategory,
            COALESCE(t.latest_scan, m.date_last_scanned) as true_last_activity,
            DATEDIFF(NOW(), COALESCE(t.latest_scan, m.date_last_scanned)) as true_days_stale,
            t.latest_scan_type,
            COALESCE(t.touch_scan_count, 0) as touch_scan_count,
            COALESCE(t.status_scan_count, 0) as status_scan_count,
            COALESCE(t.total_scan_count, 0) as total_scan_count,
            t.latest_scan as transaction_last_scan,
            CASE 
                WHEN t.touch_scan_count > 0 AND t.status_scan_count > 0 THEN 'MIXED_ACTIVITY'
                WHEN t.touch_scan_count > 0 THEN 'TOUCH_MANAGED'
                WHEN t.status_scan_count > 0 THEN 'STATUS_ONLY' 
                ELSE 'NO_RECENT_ACTIVITY'
            END as activity_type,
            CASE
                WHEN COALESCE(t.latest_scan, m.date_last_scanned) >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 'VERY_RECENT'
                WHEN COALESCE(t.latest_scan, m.date_last_scanned) >= DATE_SUB(NOW(), INTERVAL 14 DAY) THEN 'RECENT'
                WHEN COALESCE(t.latest_scan, m.date_last_scanned) >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 'MODERATE'
                ELSE 'TRULY_STALE'
            END as activity_level
        FROM id_item_master m
        LEFT JOIN user_rental_class_mappings u ON m.rental_class_num = u.rental_class_id
        LEFT JOIN (
            SELECT 
                tag_id,
                MAX(scan_date) as latest_scan,
                SUBSTRING_INDEX(GROUP_CONCAT(scan_type ORDER BY scan_date DESC), ',', 1) as latest_scan_type,
                SUM(CASE WHEN scan_type = 'Touch Scan' THEN 1 ELSE 0 END) as touch_scan_count,
                SUM(CASE WHEN scan_type != 'Touch Scan' THEN 1 ELSE 0 END) as status_scan_count,
                COUNT(*) as total_scan_count
            FROM id_transactions 
            WHERE scan_date >= DATE_SUB(NOW(), INTERVAL 90 DAY)
            GROUP BY tag_id
        ) t ON m.tag_id = t.tag_id
        WHERE DATEDIFF(NOW(), COALESCE(t.latest_scan, m.date_last_scanned)) > 
            CASE 
                WHEN u.category = 'Resale' OR m.bin_location = 'resale' THEN :resale_days
                WHEN m.bin_location LIKE '%pack%' THEN :pack_days  
                ELSE :default_days 
            END
        AND (m.date_last_scanned IS NOT NULL OR t.latest_scan IS NOT NULL)
        ORDER BY true_days_stale DESC
        LIMIT 1000
        """)
        
        result_rows = session.execute(stale_query, {
            'default_days': default_days,
            'resale_days': resale_days,
            'pack_days': pack_days
        }).fetchall()
        
        logger.info(f"🎉 Found {len(result_rows)} items using REVOLUTIONARY transaction analysis!")
        
        # Convert to enhanced data structure
        result = []
        activity_stats = {
            'MIXED_ACTIVITY': 0,
            'TOUCH_MANAGED': 0, 
            'STATUS_ONLY': 0,
            'NO_RECENT_ACTIVITY': 0
        }
        
        touch_managed_count = 0
        previously_hidden_count = 0
        
        for row in result_rows:
            # Check if this item was previously hidden by master-only analysis
            master_days_stale = None
            if row.master_last_scan:
                master_days_stale = (datetime.now() - row.master_last_scan).days
            
            is_previously_hidden = (
                row.touch_scan_count > 0 and  # Has touch scan activity
                master_days_stale and master_days_stale > row.true_days_stale  # Transaction is newer than master
            )
            
            if is_previously_hidden:
                previously_hidden_count += 1
            
            if row.touch_scan_count > 0:
                touch_managed_count += 1
            
            item_dict = {
                'tag_id': row.tag_id,
                'serial_number': row.serial_number,
                'client_name': row.client_name,
                'rental_class_num': row.rental_class_num,
                'common_name': row.common_name,
                'quality': row.quality,
                'bin_location': row.bin_location,
                'status': row.status,
                'last_contract_num': row.last_contract_num,
                'notes': row.notes,
                'master_last_scan': row.master_last_scan.isoformat() if row.master_last_scan else None,
                'category': row.category,
                'subcategory': row.subcategory,
                'true_last_activity': row.true_last_activity.isoformat() if row.true_last_activity else None,
                'days_since_scan': row.true_days_stale,  # UI compatibility
                'true_days_stale': row.true_days_stale,
                'latest_scan_type': row.latest_scan_type,
                'touch_scan_count': row.touch_scan_count,
                'status_scan_count': row.status_scan_count,
                'transaction_count': row.total_scan_count,  # UI compatibility
                'total_scan_count': row.total_scan_count,
                'activity_type': row.activity_type,
                'activity_level': row.activity_level,
                'has_recent_activity': row.total_scan_count > 0,
                'is_touch_managed': row.touch_scan_count > 0,
                'was_previously_hidden': is_previously_hidden,
                'master_vs_transaction_days': {
                    'master_days_stale': master_days_stale,
                    'transaction_days_stale': row.true_days_stale,
                    'difference': master_days_stale - row.true_days_stale if master_days_stale else 0
                } if master_days_stale else None
            }
            result.append(item_dict)
            activity_stats[row.activity_type] += 1
        
        logger.info(f"🔥 GAME CHANGER: {touch_managed_count} items have Touch Scan management!")
        logger.info(f"🚨 PREVIOUSLY HIDDEN: {previously_hidden_count} items were invisible in old analysis!")
        logger.info(f"📊 Activity breakdown: {activity_stats}")
        
        return jsonify({
            'stale_items': result,
            'thresholds_used': {
                'default_days': default_days,
                'resale_days': resale_days,
                'pack_days': pack_days
            },
            'enhanced_summary': {
                'total_stale_items': len(result),
                'items_with_transactions': sum(1 for item in result if item['total_scan_count'] > 0),
                'items_with_touch_scans': touch_managed_count,
                'items_with_status_scans': sum(1 for item in result if item['status_scan_count'] > 0),
                'previously_hidden_by_old_analysis': previously_hidden_count,
                'activity_breakdown': activity_stats,
                'touch_managed_percentage': round((touch_managed_count / len(result) * 100), 1) if result else 0
            },
            'revolution_notes': {
                'enhancement': 'Now includes ALL transaction activity including Touch Scans!',
                'impact': f'Revealed {previously_hidden_count} previously hidden actively managed items',
                'touch_scan_discovery': f'{touch_managed_count} items show active inventory management via Touch Scans'
            },
            'analysis_upgrade': 'REVOLUTIONARY - True activity visibility achieved!'
        })
        
    except Exception as e:
        logger.error(f"💥 Error in revolutionary stale items analysis: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to fetch enhanced stale items: {str(e)}'}), 500
    finally:
        if session:
            session.close()

@inventory_analytics_bp.route('/api/inventory/stale_items_simple', methods=['GET'])
def get_stale_items_simple():
    """Get stale inventory items - SIMPLIFIED VERSION FOR DEBUGGING."""
    session = None
    try:
        session = db.session()
        
        # Get query parameters
        limit = min(int(request.args.get('limit', 25)), 100)
        offset = int(request.args.get('offset', 0))
        
        # Simple hardcoded thresholds for now
        default_days = 30
        resale_days = 7
        pack_days = 14
        
        logger.info(f"Fetching stale items with thresholds - Default: {default_days}, Resale: {resale_days}, Pack: {pack_days} days")
        
        # Simplified query for debugging
        stale_query = text("""
        SELECT 
            m.tag_id,
            m.common_name,
            u.category,
            u.subcategory,
            m.date_last_scanned as master_last_scan,
            DATEDIFF(NOW(), m.date_last_scanned) as days_since_scan,
            m.bin_location,
            m.status
        FROM id_item_master m
        LEFT JOIN user_rental_class_mappings u ON m.rental_class_num = u.rental_class_id
        WHERE m.date_last_scanned IS NOT NULL
          AND DATEDIFF(NOW(), m.date_last_scanned) > 
            CASE 
                WHEN u.category = 'Resale' OR m.bin_location = 'resale' THEN :resale_days
                WHEN m.bin_location LIKE '%pack%' THEN :pack_days  
                ELSE :default_days 
            END
        ORDER BY m.date_last_scanned ASC
        LIMIT :limit OFFSET :offset
        """)
        
        result_rows = session.execute(stale_query, {
            'resale_days': resale_days,
            'pack_days': pack_days,
            'default_days': default_days,
            'limit': limit,
            'offset': offset
        })
        
        rows = result_rows.fetchall()
        items = []
        for row in rows:
            items.append({
                'tag_id': row.tag_id,
                'common_name': row.common_name,
                'category': row.category,
                'subcategory': row.subcategory, 
                'master_last_scan': row.master_last_scan.isoformat() if row.master_last_scan else None,
                'days_since_scan': row.days_since_scan,
                'bin_location': row.bin_location,
                'status': row.status
            })
        
        # Get total count for pagination
        count_query = text("""
        SELECT COUNT(*) as total
        FROM id_item_master m
        LEFT JOIN user_rental_class_mappings u ON m.rental_class_num = u.rental_class_id
        WHERE m.date_last_scanned IS NOT NULL
          AND DATEDIFF(NOW(), m.date_last_scanned) > 
            CASE 
                WHEN u.category = 'Resale' OR m.bin_location = 'resale' THEN :resale_days
                WHEN m.bin_location LIKE '%pack%' THEN :pack_days  
                ELSE :default_days 
            END
        """)
        
        total_result = session.execute(count_query, {
            'resale_days': resale_days,
            'pack_days': pack_days,
            'default_days': default_days
        })
        total_count = total_result.scalar()
        
        logger.info(f"Found {total_count} total stale items, returning {len(items)}")
        
        return jsonify({
            'items': items,
            'pagination': {
                'total': total_count,
                'limit': limit,
                'offset': offset,
                'has_more': offset + len(items) < total_count
            },
            'summary': {
                'total_stale_items': total_count,
                'showing': len(items)
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting stale items: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@inventory_analytics_bp.route('/api/inventory/usage_patterns', methods=['GET'])
def get_usage_patterns():
    """Get comprehensive usage patterns based on transaction history."""
    session = None
    try:
        session = db.session()
        days_back = int(request.args.get('days', 90))
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Simplified usage patterns by category
        usage_patterns = session.query(
            UserRentalClassMapping.category,
            UserRentalClassMapping.subcategory,
            func.count(func.distinct(ItemMaster.tag_id)).label('total_items'),
            func.count(Transaction.id).label('total_transactions')
        ).join(
            ItemMaster,
            UserRentalClassMapping.rental_class_id == ItemMaster.rental_class_num
        ).outerjoin(
            Transaction,
            and_(
                ItemMaster.tag_id == Transaction.tag_id,
                Transaction.scan_date >= cutoff_date
            )
        ).group_by(
            UserRentalClassMapping.category,
            UserRentalClassMapping.subcategory
        ).having(
            func.count(func.distinct(ItemMaster.tag_id)) > 5  # Only categories with 5+ items
        ).order_by(
            desc('total_transactions')
        ).limit(20).all()  # Limit results for performance
        
        patterns = []
        for pattern in usage_patterns:
            activity_rate = (pattern.total_transactions or 0) / max(pattern.total_items, 1)
            patterns.append({
                'category': pattern.category,
                'subcategory': pattern.subcategory,
                'total_items': pattern.total_items,
                'total_transactions': pattern.total_transactions or 0,
                'activity_rate': round(activity_rate, 2),
                'transactions_per_item': round(activity_rate, 2)
            })
        
        logger.info(f"Generated usage patterns for {len(patterns)} categories over {days_back} days")
        return jsonify({
            'usage_patterns': patterns,
            'analysis_period_days': days_back,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error generating usage patterns: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

@inventory_analytics_bp.route('/api/inventory/data_discrepancies', methods=['GET'])
def get_data_discrepancies():
    """Identify discrepancies between ItemMaster and Transaction data."""
    session = None
    try:
        session = db.session()
        
        # Items with transactions but outdated date_last_scanned
        outdated_items = session.query(
            ItemMaster.tag_id,
            ItemMaster.common_name,
            ItemMaster.date_last_scanned,
            func.max(Transaction.scan_date).label('latest_transaction')
        ).join(
            Transaction,
            ItemMaster.tag_id == Transaction.tag_id
        ).group_by(
            ItemMaster.tag_id
        ).having(
            or_(
                ItemMaster.date_last_scanned.is_(None),
                func.max(Transaction.scan_date) > ItemMaster.date_last_scanned
            )
        ).limit(50).all()
        
        # Items in master with no transactions  
        no_transactions = session.query(
            ItemMaster.tag_id,
            ItemMaster.common_name,
            ItemMaster.status,
            ItemMaster.date_created
        ).outerjoin(
            Transaction,
            ItemMaster.tag_id == Transaction.tag_id
        ).filter(
            Transaction.tag_id.is_(None)
        ).limit(50).all()
        
        # Transaction orphans (transactions without master records)
        orphaned_transactions = session.query(
            Transaction.tag_id,
            func.max(Transaction.scan_date).label('latest_scan'),
            func.count(Transaction.id).label('transaction_count')
        ).outerjoin(
            ItemMaster,
            Transaction.tag_id == ItemMaster.tag_id
        ).filter(
            ItemMaster.tag_id.is_(None)
        ).group_by(
            Transaction.tag_id
        ).limit(50).all()
        
        discrepancies = {
            'outdated_master_records': [
                {
                    'tag_id': item.tag_id,
                    'common_name': item.common_name,
                    'master_last_scan': item.date_last_scanned.isoformat() if item.date_last_scanned else None,
                    'transaction_last_scan': item.latest_transaction.isoformat() if item.latest_transaction else None,
                    'days_difference': (item.latest_transaction - (item.date_last_scanned or item.latest_transaction)).days if item.latest_transaction else None
                }
                for item in outdated_items
            ],
            'items_without_transactions': [
                {
                    'tag_id': item.tag_id,
                    'common_name': item.common_name,
                    'status': item.status,
                    'created_date': item.date_created.isoformat() if item.date_created else None
                }
                for item in no_transactions
            ],
            'orphaned_transactions': [
                {
                    'tag_id': trans.tag_id,
                    'latest_scan': trans.latest_scan.isoformat() if trans.latest_scan else None,
                    'transaction_count': trans.transaction_count
                }
                for trans in orphaned_transactions
            ]
        }
        
        logger.info(f"Found data discrepancies: {len(discrepancies['outdated_master_records'])} outdated, {len(discrepancies['items_without_transactions'])} without transactions, {len(discrepancies['orphaned_transactions'])} orphaned")
        
        return jsonify(discrepancies)
        
    except Exception as e:
        logger.error(f"Error analyzing data discrepancies: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

def calculate_inventory_health_score(session, metrics):
    """Calculate overall inventory health score (0-100) based on various factors."""
    try:
        score = 100  # Start with perfect score
        
        # Deduct points for active alerts
        total_alerts = sum(metrics['active_alerts'].values())
        if total_alerts > 0:
            # Critical alerts: -5 points each
            score -= metrics['active_alerts'].get('critical', 0) * 5
            # High alerts: -2 points each
            score -= metrics['active_alerts'].get('high', 0) * 2
            # Medium alerts: -1 point each
            score -= metrics['active_alerts'].get('medium', 0) * 1
            # Low alerts: -0.5 points each
            score -= metrics['active_alerts'].get('low', 0) * 0.5
        
        # Adjust for utilization rate (optimal is 60-80%)
        utilization = metrics['utilization_rate']
        if utilization < 40:  # Under-utilized
            score -= (40 - utilization) * 0.5
        elif utilization > 90:  # Over-utilized
            score -= (utilization - 90) * 1.5
        
        # Adjust for recent activity
        if metrics['recent_activity'] < 50:  # Low activity indicator
            score -= 10
        
        # Ensure score stays within bounds
        return max(0, min(100, round(score, 1)))
        
    except Exception as e:
        logger.error(f"Error calculating health score: {str(e)}")
        return 50  # Return neutral score on error

@inventory_analytics_bp.route('/api/inventory/generate_alerts', methods=['POST'])
def generate_inventory_alerts():
    """Generate health alerts from current inventory analysis."""
    session = None
    try:
        session = db.session()
        logger.info("Starting automatic alert generation")
        
        # Clear old alerts (keep resolved/dismissed ones)
        old_alerts_deleted = session.query(InventoryHealthAlert).filter(
            InventoryHealthAlert.status == 'active'
        ).delete()
        
        alerts_created = 0
        
        # Get stale items and create alerts  
        stale_response = get_stale_items_simple()
        stale_data = stale_response.get_json()
        
        if stale_data and 'items' in stale_data:
            for item in stale_data['items']:
                # Determine severity based on days since scan
                days = item['days_since_scan']
                if days > 180:
                    severity = 'critical'
                    action = f"Item not scanned in {days} days. Verify location and condition immediately."
                elif days > 90:
                    severity = 'high'
                    action = f"Item not scanned in {days} days. Schedule inspection and update location."
                elif days > 60:
                    severity = 'medium'
                    action = f"Item overdue for scanning. Verify status and scan if available."
                else:
                    severity = 'low'
                    action = f"Item approaching stale threshold. Consider scanning during next inventory check."
                
                # Use the correct field names from simplified API
                last_scan_field = item.get('master_last_scan')
                
                alert = InventoryHealthAlert(
                    tag_id=item['tag_id'],
                    common_name=item['common_name'],
                    category=item['category'],
                    subcategory=item['subcategory'],
                    alert_type='stale_item',
                    severity=severity,
                    days_since_last_scan=days,
                    last_scan_date=datetime.fromisoformat(last_scan_field) if last_scan_field else None,
                    suggested_action=action,
                    status='active'
                )
                session.add(alert)
                alerts_created += 1
        
        # Check for low utilization categories
        utilization_alerts = check_utilization_patterns(session)
        alerts_created += utilization_alerts
        
        session.commit()
        logger.info(f"Alert generation complete: {alerts_created} new alerts, {old_alerts_deleted} old alerts cleared")
        
        return jsonify({
            'success': True,
            'alerts_created': alerts_created,
            'old_alerts_cleared': old_alerts_deleted,
            'message': f'Generated {alerts_created} health alerts'
        })
        
    except Exception as e:
        logger.error(f"Error generating alerts: {str(e)}", exc_info=True)
        if session:
            session.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        if session:
            session.close()

def check_utilization_patterns(session):
    """Check for utilization-based alerts and create them."""
    try:
        alerts_created = 0
        
        # Get category utilization data
        category_stats = session.query(
            UserRentalClassMapping.category,
            UserRentalClassMapping.subcategory,
            func.count(ItemMaster.tag_id).label('total_items'),
            func.sum(func.case([(ItemMaster.status.in_(['On Rent', 'Delivered']), 1)], else_=0)).label('items_on_rent')
        ).outerjoin(
            ItemMaster,
            UserRentalClassMapping.rental_class_id == ItemMaster.rental_class_num
        ).group_by(
            UserRentalClassMapping.category,
            UserRentalClassMapping.subcategory
        ).having(func.count(ItemMaster.tag_id) > 10).all()  # Only categories with 10+ items
        
        for stat in category_stats:
            if stat.total_items and stat.total_items > 0:
                utilization_rate = (stat.items_on_rent or 0) / stat.total_items
                
                # Create alert for very low utilization categories
                if utilization_rate < 0.05 and stat.total_items > 50:  # Less than 5% utilization with 50+ items
                    alert = InventoryHealthAlert(
                        category=stat.category,
                        subcategory=stat.subcategory,
                        alert_type='low_usage',
                        severity='medium',
                        suggested_action=f'Category has {stat.total_items} items but only {utilization_rate:.1%} utilization. Consider reducing inventory or marketing push.',
                        status='active'
                    )
                    session.add(alert)
                    alerts_created += 1
                    
                # Create alert for very high utilization categories  
                elif utilization_rate > 0.9:  # More than 90% utilization
                    alert = InventoryHealthAlert(
                        category=stat.category,
                        subcategory=stat.subcategory,
                        alert_type='high_usage',
                        severity='high',
                        suggested_action=f'Category has {utilization_rate:.1%} utilization. Consider expanding inventory to meet demand.',
                        status='active'
                    )
                    session.add(alert)
                    alerts_created += 1
        
        return alerts_created
        
    except Exception as e:
        logger.error(f"Error checking utilization patterns: {str(e)}")
        return 0

def get_alert_config(session):
    """Get alert configuration from database."""
    try:
        config_record = session.query(InventoryConfig).filter(
            InventoryConfig.config_key == 'alert_thresholds'
        ).first()
        
        if config_record:
            return config_record.config_value
        else:
            # Return default configuration
            return {
                'stale_item_days': {'default': 30, 'resale': 7, 'pack': 14},
                'high_usage_threshold': 0.8,
                'low_usage_threshold': 0.2,
                'quality_decline_threshold': 2
            }
    except Exception as e:
        logger.error(f"Error fetching alert config: {str(e)}")
        return {'stale_item_days': {'default': 30, 'resale': 7, 'pack': 14}}

@inventory_analytics_bp.route('/api/inventory/configuration', methods=['GET'])
def get_configuration():
    """Get current inventory analytics configuration."""
    session = None
    try:
        session = db.session()
        logger.info("Fetching inventory configuration")
        
        # Get alert thresholds configuration
        alert_config = get_alert_config(session)
        
        # Get business rules configuration
        business_config_record = session.query(InventoryConfig).filter(
            InventoryConfig.config_key == 'business_rules'
        ).first()
        
        business_rules = business_config_record.config_value if business_config_record else {
            'resale_categories': ['Resale'],
            'pack_bin_locations': ['pack'],
            'rental_statuses': ['On Rent', 'Delivered'],
            'available_statuses': ['Ready to Rent'],
            'service_statuses': ['Repair', 'Needs to be Inspected']
        }
        
        # Get dashboard settings
        dashboard_config_record = session.query(InventoryConfig).filter(
            InventoryConfig.config_key == 'dashboard_settings'
        ).first()
        
        dashboard_settings = dashboard_config_record.config_value if dashboard_config_record else {
            'default_date_range': 30,
            'critical_alert_limit': 50,
            'refresh_interval_minutes': 15,
            'show_resolved_alerts': False
        }
        
        configuration = {
            'alert_thresholds': alert_config,
            'business_rules': business_rules,
            'dashboard_settings': dashboard_settings
        }
        
        logger.info("Successfully fetched configuration")
        return jsonify(configuration)
        
    except Exception as e:
        logger.error(f"Error fetching configuration: {str(e)}")
        return jsonify({'error': f'Failed to fetch configuration: {str(e)}'}), 500
    finally:
        if session:
            session.close()

@inventory_analytics_bp.route('/api/inventory/configuration', methods=['PUT'])
def update_configuration():
    """Update inventory analytics configuration."""
    session = None
    try:
        session = db.session()
        data = request.get_json()
        logger.info(f"Updating inventory configuration with data: {data}")
        
        if not data:
            return jsonify({'error': 'No configuration data provided'}), 400
            
        # Update alert thresholds if provided
        if 'alert_thresholds' in data:
            alert_config_record = session.query(InventoryConfig).filter(
                InventoryConfig.config_key == 'alert_thresholds'
            ).first()
            
            if alert_config_record:
                alert_config_record.config_value = data['alert_thresholds']
                alert_config_record.updated_at = datetime.now()
            else:
                alert_config_record = InventoryConfig(
                    config_key='alert_thresholds',
                    config_value=data['alert_thresholds'],
                    description='Threshold settings for generating inventory alerts',
                    category='alerting'
                )
                session.add(alert_config_record)
        
        # Update business rules if provided
        if 'business_rules' in data:
            business_config_record = session.query(InventoryConfig).filter(
                InventoryConfig.config_key == 'business_rules'
            ).first()
            
            if business_config_record:
                business_config_record.config_value = data['business_rules']
                business_config_record.updated_at = datetime.now()
            else:
                business_config_record = InventoryConfig(
                    config_key='business_rules',
                    config_value=data['business_rules'],
                    description='Business rule definitions for inventory categorization',
                    category='business'
                )
                session.add(business_config_record)
        
        # Update dashboard settings if provided
        if 'dashboard_settings' in data:
            dashboard_config_record = session.query(InventoryConfig).filter(
                InventoryConfig.config_key == 'dashboard_settings'
            ).first()
            
            if dashboard_config_record:
                dashboard_config_record.config_value = data['dashboard_settings']
                dashboard_config_record.updated_at = datetime.now()
            else:
                dashboard_config_record = InventoryConfig(
                    config_key='dashboard_settings',
                    config_value=data['dashboard_settings'],
                    description='Dashboard display and behavior settings',
                    category='ui'
                )
                session.add(dashboard_config_record)
        
        session.commit()
        logger.info("Configuration updated successfully")
        return jsonify({'message': 'Configuration updated successfully'})
        
    except Exception as e:
        if session:
            session.rollback()
        logger.error(f"Error updating configuration: {str(e)}")
        return jsonify({'error': f'Failed to update configuration: {str(e)}'}), 500
    finally:
        if session:
            session.close()