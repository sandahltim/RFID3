#!/usr/bin/env python3
"""
Fix Inventory Analytics Calculation Issues
==========================================
Date: 2025-08-28
Purpose: Correct calculation logic in inventory analytics to show accurate data
Author: Database Correlation Analyst
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app import create_app, db
from app.models.db_models import (
    ItemMaster, Transaction, ItemUsageHistory, 
    InventoryHealthAlert, InventoryConfig
)
from sqlalchemy import func, and_, or_, text
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Store mapping for consistency
STORE_MAPPING = {
    '001': '3607',  # Wayzata
    '002': '6800',  # Brooklyn Park  
    '003': '8101',  # Fridley
    '004': '728',   # Elk River
}

STORE_NAMES = {
    '3607': 'Wayzata',
    '6800': 'Brooklyn Park',
    '8101': 'Fridley', 
    '728': 'Elk River'
}

class InventoryAnalyticsFixer:
    """Fix inventory analytics calculation issues."""
    
    def __init__(self):
        """Initialize the fixer with database connection."""
        self.app = create_app()
        self.app.app_context().push()
        logger.info("Inventory Analytics Fixer initialized")
    
    def calculate_true_utilization(self, store_filter=None):
        """
        Calculate accurate utilization based on actual rental periods.
        
        Returns:
            dict: Utilization metrics by category
        """
        logger.info(f"Calculating true utilization for store: {store_filter or 'all'}")
        
        with db.session() as session:
            # Base query
            query = session.query(ItemMaster)
            
            # Apply store filter if provided
            if store_filter and store_filter != 'all':
                query = query.filter(
                    or_(
                        ItemMaster.home_store == store_filter,
                        ItemMaster.current_store == store_filter
                    )
                )
            
            # Get total items
            total_items = query.count()
            
            if total_items == 0:
                logger.warning("No items found for utilization calculation")
                return {
                    'total_items': 0,
                    'utilization_rate': 0,
                    'items_on_rent': 0,
                    'items_available': 0
                }
            
            # Calculate items currently on rent (accurate status check)
            items_on_rent = query.filter(
                ItemMaster.status.in_(['On Rent', 'Delivered', 'Out'])
            ).count()
            
            # Calculate items available
            items_available = query.filter(
                ItemMaster.status.in_(['Ready to Rent', 'Available', 'In Stock'])
            ).count()
            
            # Calculate items in service/repair
            items_in_service = query.filter(
                ItemMaster.status.in_(['Repair', 'Needs to be Inspected', 'Service'])
            ).count()
            
            # Calculate true utilization rate
            utilization_rate = round((items_on_rent / total_items) * 100, 2) if total_items > 0 else 0
            
            # Calculate rental frequency (last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            rental_frequency_query = text("""
                SELECT 
                    COUNT(DISTINCT im.tag_id) as active_items,
                    COUNT(DISTINCT t.contract_number) as total_rentals,
                    AVG(DATEDIFF(CURRENT_DATE, t.scan_date)) as avg_days_since_rental
                FROM id_item_master im
                LEFT JOIN id_transactions t ON im.tag_id = t.tag_id
                    AND t.scan_type IN ('checkout', 'Deliver')
                    AND t.scan_date >= :thirty_days_ago
                WHERE (:store_filter IS NULL 
                    OR im.home_store = :store_filter 
                    OR im.current_store = :store_filter)
            """)
            
            rental_metrics = session.execute(
                rental_frequency_query,
                {'thirty_days_ago': thirty_days_ago, 'store_filter': store_filter}
            ).fetchone()
            
            # Build comprehensive utilization metrics
            metrics = {
                'total_items': total_items,
                'items_on_rent': items_on_rent,
                'items_available': items_available,
                'items_in_service': items_in_service,
                'items_missing': total_items - items_on_rent - items_available - items_in_service,
                'utilization_rate': utilization_rate,
                'availability_rate': round((items_available / total_items) * 100, 2) if total_items > 0 else 0,
                'service_rate': round((items_in_service / total_items) * 100, 2) if total_items > 0 else 0,
                'rental_frequency': {
                    'active_items_30d': rental_metrics[0] if rental_metrics else 0,
                    'total_rentals_30d': rental_metrics[1] if rental_metrics else 0,
                    'avg_days_since_rental': float(rental_metrics[2]) if rental_metrics and rental_metrics[2] else 0
                }
            }
            
            logger.info(f"Utilization calculated: {utilization_rate}% for {total_items} items")
            return metrics
    
    def fix_financial_calculations(self):
        """
        Fix turnover and financial calculations for all items.
        """
        logger.info("Starting financial calculations fix...")
        
        with db.session() as session:
            # Get items with financial data issues
            items_to_fix = session.query(ItemMaster).filter(
                or_(
                    ItemMaster.turnover_ytd.is_(None),
                    ItemMaster.turnover_ytd == 0,
                    ItemMaster.turnover_ltd.is_(None)
                )
            ).all()
            
            logger.info(f"Found {len(items_to_fix)} items with financial data issues")
            
            fixed_count = 0
            for item in items_to_fix:
                # Calculate YTD turnover from transactions
                ytd_rentals = session.query(func.count(func.distinct(Transaction.contract_number))).filter(
                    Transaction.tag_id == item.tag_id,
                    Transaction.scan_type.in_(['checkout', 'Deliver']),
                    func.year(Transaction.scan_date) == datetime.now().year
                ).scalar() or 0
                
                # Calculate lifetime turnover
                ltd_rentals = session.query(func.count(func.distinct(Transaction.contract_number))).filter(
                    Transaction.tag_id == item.tag_id,
                    Transaction.scan_type.in_(['checkout', 'Deliver'])
                ).scalar() or 0
                
                # Calculate turnover value
                rental_price = item.sell_price or item.retail_price or Decimal('0')
                
                # Update item
                if ytd_rentals > 0 or ltd_rentals > 0:
                    item.turnover_ytd = Decimal(str(ytd_rentals)) * rental_price
                    item.turnover_ltd = Decimal(str(ltd_rentals)) * rental_price
                    fixed_count += 1
            
            session.commit()
            logger.info(f"Fixed financial calculations for {fixed_count} items")
            
            return {'items_fixed': fixed_count}
    
    def recalculate_stale_items(self):
        """
        Recalculate stale items with proper thresholds by category.
        """
        logger.info("Recalculating stale items with category-specific thresholds...")
        
        with db.session() as session:
            # Get configuration for thresholds
            config = session.query(InventoryConfig).filter(
                InventoryConfig.config_key == 'alert_thresholds'
            ).first()
            
            if config and config.config_value:
                thresholds = config.config_value.get('stale_item_days', {})
            else:
                thresholds = {
                    'default': 30,
                    'resale': 7,
                    'pack': 14,
                    'rental': 45
                }
            
            # Clear existing stale item alerts
            session.query(InventoryHealthAlert).filter(
                InventoryHealthAlert.alert_type == 'stale_item'
            ).delete()
            
            # Find stale items by category
            stale_items = []
            
            # Check resale items (7 days)
            resale_threshold = datetime.now() - timedelta(days=thresholds.get('resale', 7))
            resale_items = session.query(ItemMaster).filter(
                ItemMaster.bin_location.ilike('%resale%'),
                or_(
                    ItemMaster.date_last_scanned < resale_threshold,
                    ItemMaster.date_last_scanned.is_(None)
                )
            ).all()
            
            for item in resale_items:
                days_stale = (datetime.now() - (item.date_last_scanned or item.date_created)).days
                stale_items.append({
                    'item': item,
                    'category': 'resale',
                    'days_stale': days_stale,
                    'threshold': thresholds.get('resale', 7)
                })
            
            # Check pack items (14 days)
            pack_threshold = datetime.now() - timedelta(days=thresholds.get('pack', 14))
            pack_items = session.query(ItemMaster).filter(
                ItemMaster.bin_location.ilike('%pack%'),
                or_(
                    ItemMaster.date_last_scanned < pack_threshold,
                    ItemMaster.date_last_scanned.is_(None)
                )
            ).all()
            
            for item in pack_items:
                days_stale = (datetime.now() - (item.date_last_scanned or item.date_created)).days
                stale_items.append({
                    'item': item,
                    'category': 'pack',
                    'days_stale': days_stale,
                    'threshold': thresholds.get('pack', 14)
                })
            
            # Check regular rental items (30-45 days depending on status)
            rental_threshold = datetime.now() - timedelta(days=thresholds.get('default', 30))
            regular_items = session.query(ItemMaster).filter(
                ~ItemMaster.bin_location.ilike('%resale%'),
                ~ItemMaster.bin_location.ilike('%pack%'),
                or_(
                    ItemMaster.date_last_scanned < rental_threshold,
                    ItemMaster.date_last_scanned.is_(None)
                )
            ).all()
            
            for item in regular_items:
                days_stale = (datetime.now() - (item.date_last_scanned or item.date_created)).days
                stale_items.append({
                    'item': item,
                    'category': 'rental',
                    'days_stale': days_stale,
                    'threshold': thresholds.get('default', 30)
                })
            
            # Create alerts for stale items
            alerts_created = 0
            for stale_data in stale_items:
                item = stale_data['item']
                days = stale_data['days_stale']
                
                # Determine severity
                if days > 180:
                    severity = 'critical'
                elif days > 90:
                    severity = 'high'
                elif days > 60:
                    severity = 'medium'
                else:
                    severity = 'low'
                
                # Create alert
                alert = InventoryHealthAlert(
                    tag_id=item.tag_id,
                    rental_class_id=item.rental_class_num,
                    common_name=item.common_name,
                    category=stale_data['category'],
                    alert_type='stale_item',
                    severity=severity,
                    days_since_last_scan=days,
                    last_scan_date=item.date_last_scanned,
                    suggested_action=f"Item not scanned in {days} days (threshold: {stale_data['threshold']} days). Verify location and status.",
                    status='active'
                )
                session.add(alert)
                alerts_created += 1
            
            session.commit()
            logger.info(f"Created {alerts_created} stale item alerts")
            
            return {
                'total_stale_items': len(stale_items),
                'alerts_created': alerts_created,
                'by_category': {
                    'resale': len([s for s in stale_items if s['category'] == 'resale']),
                    'pack': len([s for s in stale_items if s['category'] == 'pack']),
                    'rental': len([s for s in stale_items if s['category'] == 'rental'])
                }
            }
    
    def synchronize_store_data(self):
        """
        Ensure store codes are properly mapped across all tables.
        """
        logger.info("Synchronizing store data across tables...")
        
        with db.session() as session:
            # Update items with missing or incorrect store codes
            update_query = text("""
                UPDATE id_item_master im
                JOIN store_mappings sm ON (
                    im.home_store = sm.pos_code 
                    OR im.current_store = sm.pos_code
                )
                SET 
                    im.home_store = CASE 
                        WHEN im.home_store = sm.pos_code THEN sm.db_code 
                        ELSE im.home_store 
                    END,
                    im.current_store = CASE 
                        WHEN im.current_store = sm.pos_code THEN sm.db_code 
                        ELSE im.current_store 
                    END
                WHERE im.home_store IN ('001', '002', '003', '004')
                   OR im.current_store IN ('001', '002', '003', '004')
            """)
            
            result = session.execute(update_query)
            session.commit()
            
            logger.info(f"Updated store codes for {result.rowcount} items")
            
            return {'items_updated': result.rowcount}
    
    def generate_analytics_summary(self):
        """
        Generate a comprehensive analytics summary with all fixes applied.
        """
        logger.info("Generating comprehensive analytics summary...")
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'utilization_metrics': {},
            'financial_health': {},
            'data_quality': {},
            'alerts_summary': {}
        }
        
        with db.session() as session:
            # Overall utilization
            summary['utilization_metrics'] = self.calculate_true_utilization()
            
            # Financial metrics
            financial_query = session.query(
                func.count(ItemMaster.tag_id).label('total_items'),
                func.sum(ItemMaster.turnover_ytd).label('total_ytd_turnover'),
                func.sum(ItemMaster.turnover_ltd).label('total_ltd_turnover'),
                func.sum(ItemMaster.retail_price).label('total_inventory_value'),
                func.avg(ItemMaster.turnover_ytd).label('avg_ytd_turnover')
            ).first()
            
            summary['financial_health'] = {
                'total_inventory_value': float(financial_query.total_inventory_value or 0),
                'total_ytd_turnover': float(financial_query.total_ytd_turnover or 0),
                'total_ltd_turnover': float(financial_query.total_ltd_turnover or 0),
                'avg_ytd_turnover': float(financial_query.avg_ytd_turnover or 0),
                'roi_percentage': round(
                    (float(financial_query.total_ytd_turnover or 0) / 
                     float(financial_query.total_inventory_value or 1)) * 100, 2
                )
            }
            
            # Data quality metrics
            quality_query = session.query(
                func.count(ItemMaster.tag_id).label('total'),
                func.sum(func.if_(ItemMaster.date_last_scanned.isnot(None), 1, 0)).label('with_scan_date'),
                func.sum(func.if_(ItemMaster.sell_price.isnot(None), 1, 0)).label('with_price'),
                func.sum(func.if_(ItemMaster.turnover_ytd.isnot(None), 1, 0)).label('with_turnover'),
                func.sum(func.if_(ItemMaster.home_store.isnot(None), 1, 0)).label('with_store')
            ).first()
            
            total = quality_query.total or 1
            summary['data_quality'] = {
                'total_records': total,
                'completeness_scores': {
                    'scan_date': round((quality_query.with_scan_date or 0) / total * 100, 2),
                    'pricing': round((quality_query.with_price or 0) / total * 100, 2),
                    'turnover': round((quality_query.with_turnover or 0) / total * 100, 2),
                    'store_assignment': round((quality_query.with_store or 0) / total * 100, 2)
                },
                'overall_quality_score': round(
                    ((quality_query.with_scan_date or 0) + 
                     (quality_query.with_price or 0) + 
                     (quality_query.with_turnover or 0) + 
                     (quality_query.with_store or 0)) / (total * 4) * 100, 2
                )
            }
            
            # Alerts summary
            alerts_query = session.query(
                InventoryHealthAlert.severity,
                func.count(InventoryHealthAlert.id).label('count')
            ).filter(
                InventoryHealthAlert.status == 'active'
            ).group_by(InventoryHealthAlert.severity).all()
            
            summary['alerts_summary'] = {
                'by_severity': {alert.severity: alert.count for alert in alerts_query},
                'total_active': sum(alert.count for alert in alerts_query)
            }
        
        return summary

def main():
    """Main execution function."""
    logger.info("="*60)
    logger.info("Starting Inventory Analytics Fix Process")
    logger.info("="*60)
    
    fixer = InventoryAnalyticsFixer()
    
    try:
        # Step 1: Synchronize store data
        logger.info("\nStep 1: Synchronizing store data...")
        store_result = fixer.synchronize_store_data()
        logger.info(f"Result: {store_result}")
        
        # Step 2: Fix financial calculations
        logger.info("\nStep 2: Fixing financial calculations...")
        financial_result = fixer.fix_financial_calculations()
        logger.info(f"Result: {financial_result}")
        
        # Step 3: Recalculate stale items
        logger.info("\nStep 3: Recalculating stale items...")
        stale_result = fixer.recalculate_stale_items()
        logger.info(f"Result: {stale_result}")
        
        # Step 4: Generate summary
        logger.info("\nStep 4: Generating analytics summary...")
        summary = fixer.generate_analytics_summary()
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("ANALYTICS SUMMARY AFTER FIXES")
        logger.info("="*60)
        logger.info(f"Utilization Rate: {summary['utilization_metrics']['utilization_rate']}%")
        logger.info(f"Total Inventory Value: ${summary['financial_health']['total_inventory_value']:,.2f}")
        logger.info(f"YTD Turnover: ${summary['financial_health']['total_ytd_turnover']:,.2f}")
        logger.info(f"ROI: {summary['financial_health']['roi_percentage']}%")
        logger.info(f"Data Quality Score: {summary['data_quality']['overall_quality_score']}%")
        logger.info(f"Active Alerts: {summary['alerts_summary']['total_active']}")
        
        logger.info("\n" + "="*60)
        logger.info("Inventory Analytics Fix Process Completed Successfully!")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Error during fix process: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()