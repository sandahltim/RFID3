#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/tim/RFID3')

from app import create_app
from app.models.db_models import InventoryHealthAlert
from app import db
from datetime import datetime
from sqlalchemy import text

def test_alert_generation():
    """Test alert generation with sample data"""
    app = create_app()
    
    with app.app_context():
        print("Testing direct alert creation with sample data...")
        
        # Sample stale items data (simulating what get_stale_items_simple would return)
        sample_items = [
            {
                "tag_id": "TEST001",
                "common_name": "Test Item 1",
                "category": "Test Category",
                "subcategory": "Test Subcategory",
                "days_since_scan": 200,
                "master_last_scan": "2024-12-18T14:29:26"
            },
            {
                "tag_id": "TEST002", 
                "common_name": "Test Item 2",
                "category": "Test Category",
                "subcategory": "Test Subcategory",
                "days_since_scan": 150,
                "master_last_scan": "2024-12-18T14:30:00"
            },
            {
                "tag_id": "TEST003",
                "common_name": "Test Item 3", 
                "category": "Test Category",
                "subcategory": "Test Subcategory",
                "days_since_scan": 100,
                "master_last_scan": "2024-12-18T14:31:00"
            }
        ]
        
        alerts_created = 0
        alerts_updated = 0
        
        for item in sample_items:
            # Process each item with its own isolated session
            item_session = db.session()
            try:
                # Determine severity based on days since scan
                days = item["days_since_scan"]
                if days > 180:
                    severity = "critical"
                    action = f"Item not scanned in {days} days. Verify location and condition immediately."
                elif days > 90:
                    severity = "high"
                    action = f"Item not scanned in {days} days. Schedule inspection and update location."
                elif days > 60:
                    severity = "medium"
                    action = f"Item overdue for scanning. Verify status and scan if available."
                else:
                    severity = "low"
                    action = f"Item approaching stale threshold. Consider scanning during next inventory check."

                # Use the correct field names from simplified API
                last_scan_field = item.get("master_last_scan")
                last_scan_date = (
                    datetime.fromisoformat(last_scan_field)
                    if last_scan_field
                    else None
                )

                # Check if alert already exists for this tag_id and alert_type
                existing_alert = item_session.query(InventoryHealthAlert).filter(
                    InventoryHealthAlert.tag_id == item["tag_id"],
                    InventoryHealthAlert.alert_type == "stale_item",
                    InventoryHealthAlert.status == "active"
                ).first()

                if existing_alert:
                    # Update existing alert if data has changed
                    needs_update = (
                        existing_alert.severity != severity or
                        existing_alert.days_since_last_scan != days or
                        existing_alert.suggested_action != action or
                        existing_alert.last_scan_date != last_scan_date
                    )
                    
                    if needs_update:
                        existing_alert.severity = severity
                        existing_alert.days_since_last_scan = days
                        existing_alert.last_scan_date = last_scan_date
                        existing_alert.suggested_action = action
                        existing_alert.created_at = datetime.now()  # Refresh timestamp
                        
                        item_session.commit()
                        alerts_updated += 1
                        print(f"Updated existing alert for tag_id: {item['tag_id']}")
                else:
                    # Use INSERT IGNORE or ON DUPLICATE KEY UPDATE to handle constraints at SQL level
                    try:
                        # Try to create new alert using raw SQL to avoid SQLAlchemy batching
                        insert_sql = """
                        INSERT INTO inventory_health_alerts 
                        (tag_id, common_name, category, subcategory, alert_type, severity, 
                         days_since_last_scan, last_scan_date, suggested_action, status, created_at)
                        VALUES (%(tag_id)s, %(common_name)s, %(category)s, %(subcategory)s, %(alert_type)s, 
                               %(severity)s, %(days_since_last_scan)s, %(last_scan_date)s, %(suggested_action)s, 
                               %(status)s, %(created_at)s)
                        ON DUPLICATE KEY UPDATE
                            severity = VALUES(severity),
                            days_since_last_scan = VALUES(days_since_last_scan),
                            last_scan_date = VALUES(last_scan_date),
                            suggested_action = VALUES(suggested_action),
                            created_at = VALUES(created_at)
                        """
                        
                        item_session.execute(text(insert_sql), {
                            'tag_id': item["tag_id"],
                            'common_name': item["common_name"],
                            'category': item["category"],
                            'subcategory': item["subcategory"],
                            'alert_type': 'stale_item',
                            'severity': severity,
                            'days_since_last_scan': days,
                            'last_scan_date': last_scan_date,
                            'suggested_action': action,
                            'status': 'active',
                            'created_at': datetime.now()
                        })
                        item_session.commit()
                        alerts_created += 1
                        print(f"Upserted alert for tag_id: {item['tag_id']}")
                        
                    except Exception as sql_error:
                        print(f"SQL upsert failed for tag_id {item['tag_id']}: {str(sql_error)}")
                        item_session.rollback()
                        # Fall back to ORM approach
                        try:
                            alert = InventoryHealthAlert(
                                tag_id=item["tag_id"],
                                common_name=item["common_name"],
                                category=item["category"],
                                subcategory=item["subcategory"],
                                alert_type="stale_item",
                                severity=severity,
                                days_since_last_scan=days,
                                last_scan_date=last_scan_date,
                                suggested_action=action,
                                status="active",
                            )
                            
                            item_session.add(alert)
                            item_session.commit()
                            alerts_created += 1
                            print(f"Created new alert via ORM for tag_id: {item['tag_id']}")
                        except Exception as orm_error:
                            print(f"ORM creation also failed for tag_id {item['tag_id']}: {str(orm_error)}")
                            item_session.rollback()

            except Exception as e:
                print(f"Alert processing failed for tag_id {item['tag_id']}: {str(e)}")
                item_session.rollback()
                # Continue processing other items
            finally:
                item_session.close()
        
        print(f"\nResults: {alerts_created} alerts created, {alerts_updated} alerts updated")
        
        # Test running it again to see if duplicates are handled correctly
        print("\n--- Running again to test duplicate handling ---")
        alerts_created_2 = 0
        alerts_updated_2 = 0
        
        for item in sample_items:
            # Process each item with its own isolated session
            item_session = db.session()
            try:
                days = item["days_since_scan"]
                if days > 180:
                    severity = "critical"
                    action = f"Item not scanned in {days} days. Verify location and condition immediately."
                elif days > 90:
                    severity = "high"
                    action = f"Item not scanned in {days} days. Schedule inspection and update location."
                elif days > 60:
                    severity = "medium"
                    action = f"Item overdue for scanning. Verify status and scan if available."
                else:
                    severity = "low"
                    action = f"Item approaching stale threshold. Consider scanning during next inventory check."

                last_scan_field = item.get("master_last_scan")
                last_scan_date = (
                    datetime.fromisoformat(last_scan_field)
                    if last_scan_field
                    else None
                )

                existing_alert = item_session.query(InventoryHealthAlert).filter(
                    InventoryHealthAlert.tag_id == item["tag_id"],
                    InventoryHealthAlert.alert_type == "stale_item",
                    InventoryHealthAlert.status == "active"
                ).first()

                if existing_alert:
                    print(f"Found existing alert for tag_id: {item['tag_id']} - skipping creation")
                else:
                    # Try SQL upsert again
                    insert_sql = """
                    INSERT INTO inventory_health_alerts 
                    (tag_id, common_name, category, subcategory, alert_type, severity, 
                     days_since_last_scan, last_scan_date, suggested_action, status, created_at)
                    VALUES (%(tag_id)s, %(common_name)s, %(category)s, %(subcategory)s, %(alert_type)s, 
                           %(severity)s, %(days_since_last_scan)s, %(last_scan_date)s, %(suggested_action)s, 
                           %(status)s, %(created_at)s)
                    ON DUPLICATE KEY UPDATE
                        severity = VALUES(severity),
                        days_since_last_scan = VALUES(days_since_last_scan),
                        last_scan_date = VALUES(last_scan_date),
                        suggested_action = VALUES(suggested_action),
                        created_at = VALUES(created_at)
                    """
                    
                    item_session.execute(text(insert_sql), {
                        'tag_id': item["tag_id"],
                        'common_name': item["common_name"],
                        'category': item["category"],
                        'subcategory': item["subcategory"],
                        'alert_type': 'stale_item',
                        'severity': severity,
                        'days_since_last_scan': days,
                        'last_scan_date': last_scan_date,
                        'suggested_action': action,
                        'status': 'active',
                        'created_at': datetime.now()
                    })
                    item_session.commit()
                    print(f"Upserted (should be update) alert for tag_id: {item['tag_id']}")

            except Exception as e:
                print(f"Second run processing failed for tag_id {item['tag_id']}: {str(e)}")
                item_session.rollback()
            finally:
                item_session.close()
        
        print(f"Second run results: {alerts_created_2} alerts created, {alerts_updated_2} alerts updated")

if __name__ == "__main__":
    test_alert_generation()