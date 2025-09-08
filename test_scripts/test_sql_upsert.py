#!/usr/bin/env python3

import mysql.connector
from datetime import datetime
import sys
sys.path.append('/home/tim/RFID3')
from config import DB_CONFIG

def test_sql_upsert():
    """Test the SQL UPSERT logic directly without Flask app context"""
    
    # Connect to database directly
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        print("Testing SQL UPSERT logic for health alerts...")
        
        # Sample test data
        test_data = [
            {
                'tag_id': 'TEST001',
                'common_name': 'Test Item 1',
                'category': 'Test Category',
                'subcategory': 'Test Subcategory',
                'alert_type': 'stale_item',
                'severity': 'critical',
                'days_since_last_scan': 200,
                'last_scan_date': datetime(2024, 12, 18, 14, 29, 26),
                'suggested_action': 'Item not scanned in 200 days. Verify location and condition immediately.',
                'status': 'active',
                'created_at': datetime.now()
            },
            {
                'tag_id': 'TEST002',
                'common_name': 'Test Item 2',
                'category': 'Test Category',
                'subcategory': 'Test Subcategory',
                'alert_type': 'stale_item',
                'severity': 'high',
                'days_since_last_scan': 150,
                'last_scan_date': datetime(2024, 12, 18, 14, 30, 0),
                'suggested_action': 'Item not scanned in 150 days. Schedule inspection and update location.',
                'status': 'active',
                'created_at': datetime.now()
            },
            {
                'tag_id': 'TEST003',
                'common_name': 'Test Item 3',
                'category': 'Test Category',
                'subcategory': 'Test Subcategory',
                'alert_type': 'stale_item',
                'severity': 'high',
                'days_since_last_scan': 100,
                'last_scan_date': datetime(2024, 12, 18, 14, 31, 0),
                'suggested_action': 'Item not scanned in 100 days. Schedule inspection and update location.',
                'status': 'active',
                'created_at': datetime.now()
            }
        ]
        
        # SQL upsert query
        upsert_sql = """
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
        
        print("First run - Creating/updating alerts individually...")
        for i, data in enumerate(test_data):
            try:
                cursor.execute(upsert_sql, data)
                conn.commit()
                print(f"  ✓ Successfully processed alert {i+1} for tag_id: {data['tag_id']}")
            except Exception as e:
                print(f"  ✗ Failed to process alert {i+1} for tag_id {data['tag_id']}: {str(e)}")
                conn.rollback()
        
        print("\nSecond run - Testing duplicate handling...")
        for i, data in enumerate(test_data):
            # Modify the data slightly to test updates
            data['days_since_last_scan'] = data['days_since_last_scan'] + 1
            data['suggested_action'] = f"Updated: {data['suggested_action']}"
            data['created_at'] = datetime.now()
            
            try:
                cursor.execute(upsert_sql, data)
                conn.commit()
                print(f"  ✓ Successfully updated alert {i+1} for tag_id: {data['tag_id']}")
            except Exception as e:
                print(f"  ✗ Failed to update alert {i+1} for tag_id {data['tag_id']}: {str(e)}")
                conn.rollback()
        
        # Check final state
        cursor.execute("""
            SELECT tag_id, severity, days_since_last_scan, created_at 
            FROM inventory_health_alerts 
            WHERE tag_id IN ('TEST001', 'TEST002', 'TEST003')
            ORDER BY tag_id
        """)
        results = cursor.fetchall()
        
        print(f"\nFinal state in database:")
        for row in results:
            print(f"  Tag ID: {row[0]}, Severity: {row[1]}, Days: {row[2]}, Created: {row[3]}")
        
        # Clean up test data
        cursor.execute("""
            DELETE FROM inventory_health_alerts 
            WHERE tag_id IN ('TEST001', 'TEST002', 'TEST003')
        """)
        conn.commit()
        print(f"\nTest cleanup completed - removed {cursor.rowcount} test records")
        
        print("\n✅ SQL UPSERT test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    test_sql_upsert()