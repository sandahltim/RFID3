#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/tim/RFID3')

from app import create_app
from app.models.db_models import InventoryHealthAlert
from app.routes.inventory_analytics import get_stale_items_simple

def debug_alert_data():
    """Debug the stale items data to find duplicates"""
    app = create_app()
    
    with app.app_context():
        print("Getting stale items data...")
        stale_response = get_stale_items_simple()
        stale_data = stale_response.get_json()
        
        if not stale_data or "items" not in stale_data:
            print("No stale data found")
            return
            
        items = stale_data["items"]
        print(f"Total items: {len(items)}")
        
        # Check for duplicate tag_ids in the response
        tag_ids = [item["tag_id"] for item in items]
        unique_tag_ids = set(tag_ids)
        
        print(f"Unique tag_ids: {len(unique_tag_ids)}")
        print(f"Total tag_ids: {len(tag_ids)}")
        
        if len(unique_tag_ids) != len(tag_ids):
            print("\n*** FOUND DUPLICATE TAG_IDs IN RESPONSE ***")
            from collections import Counter
            duplicates = Counter(tag_ids)
            for tag_id, count in duplicates.items():
                if count > 1:
                    print(f"Tag ID {tag_id} appears {count} times")
        
        # Check existing alerts in database
        print("\nChecking existing alerts in database...")
        from app import db
        existing_alerts = db.session.query(InventoryHealthAlert).filter(
            InventoryHealthAlert.alert_type == "stale_item",
            InventoryHealthAlert.status == "active"
        ).all()
        
        existing_tag_ids = {alert.tag_id for alert in existing_alerts}
        print(f"Existing active alerts: {len(existing_alerts)}")
        
        # Check for conflicts
        conflicts = []
        for item in items:
            if item["tag_id"] in existing_tag_ids:
                conflicts.append(item["tag_id"])
        
        print(f"Tag IDs that would conflict: {len(conflicts)}")
        
        if conflicts:
            print("\nFirst 5 conflicting tag IDs:")
            for tag_id in conflicts[:5]:
                print(f"  {tag_id}")

if __name__ == "__main__":
    debug_alert_data()