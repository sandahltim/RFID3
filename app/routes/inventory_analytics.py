from flask import Blueprint, render_template, request, jsonify, current_app
from .. import db
from ..models.db_models import (
    ItemMaster, Transaction, ItemUsageHistory, InventoryHealthAlert, 
    InventoryConfig, UserRentalClassMapping, RentalClassMapping
)
from sqlalchemy import func, desc, and_, or_, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import logging
import json

# Configure logging for Inventory & Analytics
logger = logging.getLogger('inventory_analytics')
logger.setLevel(logging.INFO)

# Remove existing handlers to avoid duplicates
logger.handlers = []

# File handler for inventory_analytics.log
file_handler = logging.FileHandler('/home/tim/RFID3/logs/inventory_analytics.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

inventory_analytics_bp = Blueprint('inventory_analytics', __name__)

# Version marker
logger.info("Deployed inventory_analytics.py version: 2025-08-25-v1 at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@inventory_analytics_bp.route('/tab/6')
def inventory_analytics_view():
    """Main Inventory & Analytics dashboard page."""
    logger.info("Loading Inventory & Analytics dashboard at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    return render_template('inventory_analytics.html')

@inventory_analytics_bp.route('/api/inventory/dashboard_summary', methods=['GET'])
def get_dashboard_summary():
    """Get high-level dashboard metrics for the analytics overview."""
    session = None
    try:
        session = db.session()
        logger.info("Fetching inventory dashboard summary")
        
        # Get basic inventory counts
        total_items = session.query(ItemMaster).count()
        items_on_rent = session.query(ItemMaster).filter(ItemMaster.status.in_(['On Rent', 'Delivered'])).count()
        items_available = session.query(ItemMaster).filter(ItemMaster.status == 'Ready to Rent').count()
        items_in_service = session.query(ItemMaster).filter(ItemMaster.status.in_(['Repair', 'Needs to be Inspected'])).count()
        
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

@inventory_analytics_bp.route('/api/inventory/alerts', methods=['GET'])
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
    """Get items that haven't been scanned recently based on configurable thresholds."""
    session = None
    try:
        session = db.session()
        
        # Get configuration
        config = get_alert_config(session)
        thresholds = config.get('stale_item_days', {'default': 30})
        
        # Calculate cutoff dates
        now = datetime.now()
        default_cutoff = now - timedelta(days=thresholds.get('default', 30))
        resale_cutoff = now - timedelta(days=thresholds.get('resale', 7))
        pack_cutoff = now - timedelta(days=thresholds.get('pack', 14))
        
        # Get items with category information
        stale_items = session.query(
            ItemMaster,
            UserRentalClassMapping.category,
            UserRentalClassMapping.subcategory,
            func.datediff(func.now(), ItemMaster.date_last_scanned).label('days_since_scan')
        ).outerjoin(
            UserRentalClassMapping,
            ItemMaster.rental_class_num == UserRentalClassMapping.rental_class_id
        ).filter(
            or_(
                # Default threshold
                and_(
                    or_(UserRentalClassMapping.category.is_(None), 
                        ~UserRentalClassMapping.category.in_(['Resale'])),
                    ItemMaster.bin_location != 'pack',
                    ItemMaster.date_last_scanned < default_cutoff
                ),
                # Resale items - shorter threshold
                and_(
                    UserRentalClassMapping.category == 'Resale',
                    ItemMaster.date_last_scanned < resale_cutoff
                ),
                # Pack items - medium threshold
                and_(
                    ItemMaster.bin_location == 'pack',
                    ItemMaster.date_last_scanned < pack_cutoff
                )
            )
        ).filter(
            ItemMaster.date_last_scanned.is_not(None)
        ).order_by(ItemMaster.date_last_scanned.asc()).limit(100).all()
        
        result = []
        for item, category, subcategory, days_since_scan in stale_items:
            result.append({
                'tag_id': item.tag_id,
                'common_name': item.common_name,
                'status': item.status,
                'bin_location': item.bin_location,
                'category': category,
                'subcategory': subcategory,
                'last_scan_date': item.date_last_scanned.isoformat() if item.date_last_scanned else None,
                'days_since_scan': days_since_scan,
                'last_contract': item.last_contract_num,
                'quality': item.quality
            })
        
        logger.info(f"Found {len(result)} stale items")
        return jsonify({'stale_items': result, 'thresholds_used': thresholds})
        
    except Exception as e:
        logger.error(f"Error fetching stale items: {str(e)}", exc_info=True)
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
        stale_response = get_stale_items()
        stale_data = stale_response.get_json()
        
        if stale_data and 'stale_items' in stale_data:
            for item in stale_data['stale_items']:
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
                
                alert = InventoryHealthAlert(
                    tag_id=item['tag_id'],
                    common_name=item['common_name'],
                    category=item['category'],
                    subcategory=item['subcategory'],
                    alert_type='stale_item',
                    severity=severity,
                    days_since_last_scan=days,
                    last_scan_date=datetime.fromisoformat(item['last_scan_date']) if item['last_scan_date'] else None,
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