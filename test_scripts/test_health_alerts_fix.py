#!/usr/bin/env python3
"""
Test script to verify health alerts duplication fixes
Ensures each item appears only once per alert type
"""

import sys
import os
sys.path.append('/home/tim/RFID3')

from app import create_app, db
from app.models.db_models import InventoryHealthAlert, ItemMaster
from sqlalchemy import func, text
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_health_alerts_deduplication():
    """Test that health alerts deduplication works correctly."""
    
    app = create_app()
    with app.app_context():
        logger.info("=== HEALTH ALERTS DEDUPLICATION TEST ===")
        
        # 1. Check for existing duplicates before fix
        logger.info("1. Checking for existing duplicate alerts...")
        
        tag_duplicates = db.session.execute(text("""
            SELECT tag_id, alert_type, status, COUNT(*) as duplicate_count
            FROM inventory_health_alerts 
            WHERE tag_id IS NOT NULL AND status = 'active'
            GROUP BY tag_id, alert_type, status
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC
            LIMIT 10
        """)).fetchall()
        
        category_duplicates = db.session.execute(text("""
            SELECT category, subcategory, alert_type, status, COUNT(*) as duplicate_count
            FROM inventory_health_alerts 
            WHERE tag_id IS NULL AND status = 'active'
            GROUP BY category, subcategory, alert_type, status
            HAVING COUNT(*) > 1
            ORDER BY duplicate_count DESC
            LIMIT 10
        """)).fetchall()
        
        logger.info(f"Found {len(tag_duplicates)} tag-based duplicate groups:")
        for dup in tag_duplicates:
            logger.warning(f"  Tag {dup.tag_id}, Type: {dup.alert_type}, Count: {dup.duplicate_count}")
        
        logger.info(f"Found {len(category_duplicates)} category-based duplicate groups:")
        for dup in category_duplicates:
            logger.warning(f"  Category {dup.category}/{dup.subcategory}, Type: {dup.alert_type}, Count: {dup.duplicate_count}")
        
        # 2. Test alert generation doesn't create duplicates
        logger.info("\n2. Testing alert generation for duplicates...")
        
        # Count alerts before
        before_count = db.session.query(InventoryHealthAlert).filter(
            InventoryHealthAlert.status == 'active'
        ).count()
        logger.info(f"Active alerts before generation: {before_count}")
        
        # Simulate calling the generate alerts endpoint multiple times
        # This would previously create duplicates
        try:
            from app.routes.inventory_analytics import generate_inventory_alerts
            
            # Import necessary Flask context items
            from flask import Flask
            from unittest.mock import patch
            
            # Mock the request context for testing
            with app.test_request_context():
                # First generation
                result1 = generate_inventory_alerts()
                logger.info("First generation completed")
                
                # Second generation (should update, not duplicate)
                result2 = generate_inventory_alerts()
                logger.info("Second generation completed")
        
        except Exception as e:
            logger.error(f"Error during alert generation test: {e}")
        
        # Count alerts after
        after_count = db.session.query(InventoryHealthAlert).filter(
            InventoryHealthAlert.status == 'active'
        ).count()
        logger.info(f"Active alerts after double generation: {after_count}")
        
        # 3. Verify uniqueness constraints work
        logger.info("\n3. Testing database uniqueness constraints...")
        
        try:
            # Try to create duplicate tag-based alert
            duplicate_alert = InventoryHealthAlert(
                tag_id="TEST_TAG_123",
                alert_type="stale_item",
                severity="medium",
                suggested_action="Test duplicate alert",
                status="active",
                common_name="Test Item"
            )
            db.session.add(duplicate_alert)
            db.session.commit()
            
            # Try to add another identical alert
            duplicate_alert2 = InventoryHealthAlert(
                tag_id="TEST_TAG_123", 
                alert_type="stale_item",
                severity="high",  # Different severity
                suggested_action="Another test duplicate",
                status="active",
                common_name="Test Item 2"
            )
            db.session.add(duplicate_alert2)
            
            try:
                db.session.commit()
                logger.error("ERROR: Database allowed duplicate alert creation!")
            except Exception as e:
                logger.info("✓ Database correctly prevented duplicate alert creation")
                db.session.rollback()
                
            # Clean up test alert
            db.session.query(InventoryHealthAlert).filter(
                InventoryHealthAlert.tag_id == "TEST_TAG_123"
            ).delete()
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Constraint test failed: {e}")
            db.session.rollback()
        
        # 4. Performance check - ensure queries are efficient
        logger.info("\n4. Performance verification...")
        
        start_time = datetime.now()
        
        # Test the new query performance
        alert_count_by_severity = db.session.query(
            InventoryHealthAlert.severity,
            func.count(InventoryHealthAlert.id).label('count')
        ).filter(InventoryHealthAlert.status == 'active')\
         .group_by(InventoryHealthAlert.severity).all()
        
        end_time = datetime.now()
        query_time = (end_time - start_time).total_seconds()
        
        logger.info(f"Alert count query completed in {query_time:.3f} seconds")
        for severity, count in alert_count_by_severity:
            logger.info(f"  {severity}: {count} alerts")
        
        # 5. Final verification - no duplicates should exist
        logger.info("\n5. Final duplicate check...")
        
        final_tag_duplicates = db.session.execute(text("""
            SELECT COUNT(*) as duplicate_groups
            FROM (
                SELECT tag_id, alert_type, status, COUNT(*) as cnt
                FROM inventory_health_alerts 
                WHERE tag_id IS NOT NULL AND status = 'active'
                GROUP BY tag_id, alert_type, status
                HAVING COUNT(*) > 1
            ) as duplicates
        """)).scalar()
        
        final_category_duplicates = db.session.execute(text("""
            SELECT COUNT(*) as duplicate_groups
            FROM (
                SELECT category, subcategory, alert_type, status, COUNT(*) as cnt
                FROM inventory_health_alerts 
                WHERE tag_id IS NULL AND status = 'active'
                GROUP BY category, subcategory, alert_type, status
                HAVING COUNT(*) > 1
            ) as duplicates
        """)).scalar()
        
        logger.info(f"Final duplicate check:")
        logger.info(f"  Tag-based duplicate groups: {final_tag_duplicates}")
        logger.info(f"  Category-based duplicate groups: {final_category_duplicates}")
        
        if final_tag_duplicates == 0 and final_category_duplicates == 0:
            logger.info("✅ SUCCESS: No duplicate health alerts found!")
            return True
        else:
            logger.error("❌ FAILURE: Duplicate health alerts still exist!")
            return False

if __name__ == "__main__":
    success = test_health_alerts_deduplication()
    sys.exit(0 if success else 1)