#!/usr/bin/env python3
"""
Identifier Type Transition Service
Handles transitions: Sticker → RFID, Bulk → Sticker, Bulk → RFID
"""

from app import create_app, db
from app.services.data_merge_strategy import get_merge_strategy
from app.models.db_models import ItemMaster
from sqlalchemy import text, and_
import sys
from datetime import datetime

def main():
    app = create_app()
    
    with app.app_context():
        merge_strategy = get_merge_strategy()
        
        print("🔄 RFID3 Identifier Type Transition Service")
        print("=" * 60)
        
        # Analyze current identifier types
        print("📊 Current identifier type distribution...")
        type_stats = db.session.execute(text("""
            SELECT 
                identifier_type,
                COUNT(*) as count,
                COUNT(*) * 100.0 / (SELECT COUNT(*) FROM id_item_master) as percentage
            FROM id_item_master 
            GROUP BY identifier_type
            ORDER BY count DESC
        """)).fetchall()
        
        total_items = sum(row[1] for row in type_stats)
        print(f"Total RFID items: {total_items:,}")
        
        for row in type_stats:
            id_type, count, percentage = row
            print(f"  {id_type or 'NULL'}: {count:,} ({percentage:.1f}%)")
        
        # Identify transition candidates
        print("\n🔍 Identifying transition candidates...")
        
        # Sticker → RFID transitions (items with both serial_number and tag_id)
        sticker_to_rfid = db.session.execute(text("""
            SELECT 
                tag_id, item_num, common_name, serial_number, identifier_type
            FROM id_item_master 
            WHERE identifier_type = 'Sticker' 
            AND tag_id IS NOT NULL 
            AND LENGTH(tag_id) = 24
            AND serial_number IS NOT NULL
        """)).fetchall()
        
        print(f"🏷️  Sticker → RFID candidates: {len(sticker_to_rfid)}")
        if len(sticker_to_rfid) > 0:
            print(f"   Example: {sticker_to_rfid[0][0]} - {sticker_to_rfid[0][2]}")
        
        # Bulk → Sticker transitions (items with serial_number but no tag_id)
        bulk_to_sticker = db.session.execute(text("""
            SELECT 
                tag_id, item_num, common_name, serial_number, identifier_type
            FROM id_item_master 
            WHERE identifier_type = 'Bulk'
            AND serial_number IS NOT NULL
            AND (tag_id IS NULL OR LENGTH(tag_id) != 24)
        """)).fetchall()
        
        print(f"📦  Bulk → Sticker candidates: {len(bulk_to_sticker)}")
        if len(bulk_to_sticker) > 0:
            print(f"   Example: {bulk_to_sticker[0][1]} - {bulk_to_sticker[0][2]}")
        
        # Bulk → RFID transitions (items with tag_id but marked as bulk)
        bulk_to_rfid = db.session.execute(text("""
            SELECT 
                tag_id, item_num, common_name, serial_number, identifier_type
            FROM id_item_master 
            WHERE identifier_type = 'Bulk'
            AND tag_id IS NOT NULL 
            AND LENGTH(tag_id) = 24
        """)).fetchall()
        
        print(f"🏷️  Bulk → RFID candidates: {len(bulk_to_rfid)}")
        if len(bulk_to_rfid) > 0:
            print(f"   Example: {bulk_to_rfid[0][0]} - {bulk_to_rfid[0][2]}")
        
        total_transitions = len(sticker_to_rfid) + len(bulk_to_sticker) + len(bulk_to_rfid)
        
        if total_transitions == 0:
            print("\n✅ No identifier type transitions needed")
            return
        
        print(f"\n🚀 Total transition opportunities: {total_transitions}")
        
        # Confirm transitions
        if len(sys.argv) > 1 and sys.argv[1] == '--execute':
            response = 'yes'
            print("Auto-confirmed via --execute flag")
        else:
            response = input("Proceed with identifier type transitions? (yes/no): ").lower().strip()
        
        if response != 'yes':
            print("Transitions cancelled")
            sys.exit(0)
        
        # Execute transitions
        transitions_made = 0
        
        # Process Sticker → RFID
        for row in sticker_to_rfid:
            tag_id, item_num, name, serial, old_type = row
            success = execute_transition(tag_id, 'Sticker', 'RFID', 
                                       f"RFID tag assigned: {tag_id}")
            if success:
                transitions_made += 1
        
        # Process Bulk → Sticker  
        for row in bulk_to_sticker:
            tag_id, item_num, name, serial, old_type = row
            success = execute_transition(tag_id or f"item_{item_num}", 'Bulk', 'Sticker',
                                       f"Serial number assigned: {serial}")
            if success:
                transitions_made += 1
        
        # Process Bulk → RFID
        for row in bulk_to_rfid:
            tag_id, item_num, name, serial, old_type = row
            success = execute_transition(tag_id, 'Bulk', 'RFID',
                                       f"Direct RFID tagging: {tag_id}")
            if success:
                transitions_made += 1
        
        print(f"\n✅ Identifier type transitions completed!")
        print(f"   Transitions processed: {transitions_made}/{total_transitions}")
        
        # Show updated distribution
        print("\n📊 Updated identifier type distribution...")
        updated_stats = db.session.execute(text("""
            SELECT 
                identifier_type,
                COUNT(*) as count,
                COUNT(*) * 100.0 / (SELECT COUNT(*) FROM id_item_master) as percentage
            FROM id_item_master 
            GROUP BY identifier_type
            ORDER BY count DESC
        """)).fetchall()
        
        for row in updated_stats:
            id_type, count, percentage = row
            print(f"  {id_type or 'NULL'}: {count:,} ({percentage:.1f}%)")

def execute_transition(tag_id: str, old_type: str, new_type: str, reason: str) -> bool:
    """Execute a single identifier type transition"""
    try:
        merge_strategy = get_merge_strategy()
        
        # Update the item record
        update_result = db.session.execute(text("""
            UPDATE id_item_master 
            SET identifier_type = :new_type,
                date_updated = NOW()
            WHERE tag_id = :tag_id OR (tag_id IS NULL AND item_num IN (
                SELECT item_num FROM id_item_master WHERE tag_id = :tag_id
            ))
        """), {
            'tag_id': tag_id,
            'new_type': new_type
        })
        
        if update_result.rowcount > 0:
            # Record the transition
            merge_strategy.create_identifier_transition_record(
                tag_id, old_type, new_type, reason
            )
            db.session.commit()
            return True
        else:
            print(f"⚠️  No records updated for {tag_id}")
            return False
            
    except Exception as e:
        print(f"❌ Transition failed for {tag_id}: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    main()