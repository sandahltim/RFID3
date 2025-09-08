#!/usr/bin/env python3
"""
Populate ItemUsageHistory table with data generated from existing transactions
This will enable the Usage Analysis tab to display meaningful data
"""

from app import create_app, db
from app.models.db_models import ItemMaster, Transaction, ItemUsageHistory, UserRentalClassMapping
from sqlalchemy import func, and_
from datetime import datetime, timedelta
import random

def populate_usage_history():
    """Generate usage history from transaction data"""
    
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("POPULATING ITEM USAGE HISTORY")
        print("=" * 60)
        
        # Check current state
        existing_count = db.session.query(func.count(ItemUsageHistory.id)).scalar()
        print(f"Current ItemUsageHistory records: {existing_count}")
        
        if existing_count > 0:
            response = input("Usage history already exists. Clear and regenerate? (y/n): ")
            if response.lower() == 'y':
                db.session.query(ItemUsageHistory).delete()
                db.session.commit()
                print("Cleared existing usage history")
        
        # Get transactions grouped by tag_id
        print("\nAnalyzing transactions to generate usage history...")
        
        # Get items with transactions in the last 90 days
        cutoff_date = datetime.now() - timedelta(days=90)
        
        items_with_activity = (
            db.session.query(
                Transaction.tag_id,
                func.min(Transaction.scan_date).label('first_scan'),
                func.max(Transaction.scan_date).label('last_scan'),
                func.count(Transaction.id).label('transaction_count')
            )
            .filter(Transaction.scan_date >= cutoff_date)
            .group_by(Transaction.tag_id)
            .limit(1000)  # Process first 1000 items
            .all()
        )
        
        print(f"Found {len(items_with_activity)} items with recent activity")
        
        usage_records = []
        for item in items_with_activity:
            # Get item details
            item_master = db.session.query(ItemMaster).filter_by(tag_id=item.tag_id).first()
            if not item_master:
                continue
            
            # Get detailed transactions
            transactions = (
                db.session.query(Transaction)
                .filter(
                    Transaction.tag_id == item.tag_id,
                    Transaction.scan_date >= cutoff_date
                )
                .order_by(Transaction.scan_date)
                .all()
            )
            
            previous_status = "Ready to Rent"
            for i, trans in enumerate(transactions):
                # Determine event type based on transaction patterns
                if i == 0 or (i > 0 and (trans.scan_date - transactions[i-1].scan_date).days > 1):
                    event_type = "rental"
                    new_status = "On Rent"
                elif "return" in (trans.transaction_type or "").lower():
                    event_type = "return"
                    new_status = "Ready to Rent"
                else:
                    event_type = "status_change"
                    new_status = item_master.status
                
                # Calculate duration for returns
                duration_days = None
                if event_type == "return" and i > 0:
                    duration_days = (trans.scan_date - transactions[i-1].scan_date).days
                
                # Calculate utilization score (0-100)
                utilization_score = min(100, item.transaction_count * 10)
                
                usage_record = ItemUsageHistory(
                    tag_id=item.tag_id,
                    event_type=event_type,
                    contract_number=trans.contract_num,
                    event_date=trans.scan_date,
                    duration_days=duration_days,
                    previous_status=previous_status,
                    new_status=new_status,
                    previous_location=trans.location_scanned if i > 0 else None,
                    new_location=trans.location_scanned,
                    utilization_score=utilization_score,
                    notes=f"Generated from transaction {trans.id}"
                )
                
                usage_records.append(usage_record)
                previous_status = new_status
                
                # Limit records per item
                if len(usage_records) % 100 == 0:
                    print(f"  Generated {len(usage_records)} usage history records...")
        
        # Bulk insert usage records
        if usage_records:
            print(f"\nInserting {len(usage_records)} usage history records...")
            db.session.bulk_save_objects(usage_records)
            db.session.commit()
            print("✓ Usage history populated successfully")
        else:
            print("No usage history records to insert")
        
        # Verify the results
        final_count = db.session.query(func.count(ItemUsageHistory.id)).scalar()
        print(f"\nFinal ItemUsageHistory records: {final_count}")
        
        # Show sample records
        sample_records = db.session.query(ItemUsageHistory).limit(5).all()
        if sample_records:
            print("\nSample usage history records:")
            for record in sample_records:
                print(f"  - {record.tag_id}: {record.event_type} on {record.event_date}")
        
        return True

if __name__ == "__main__":
    populate_usage_history()