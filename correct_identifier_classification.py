#!/usr/bin/env python3
"""
Enhanced Identifier Type Classification Service
Fixes the identifier_type column based on actual business logic:

1. RFID: Items in both RFIDpro API and POS equipment (rental_class_num = ItemNum) 
2. Sticker: Serialized items (Key ends with #1, #2, #3, etc.) - individual tracking with QR/RFID soon
3. Bulk: Store-specific items (Key ends with -1, -2, -3, -4) with quantity tracking
4. None/QR: Items that don't fit other categories

Enhanced to handle data type mismatches and correct Key field access.
"""

from app import create_app, db
from sqlalchemy import text
import sys
from datetime import datetime

def main():
    app = create_app()
    
    with app.app_context():
        print("🏷️  RFID3 Enhanced Identifier Type Classification")
        print("=" * 70)
        print(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Show current state
        print("\n📊 BEFORE: Current identifier type distribution...")
        current_stats = db.session.execute(text("""
            SELECT 
                identifier_type,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM id_item_master), 1) as percentage
            FROM id_item_master 
            GROUP BY identifier_type
            ORDER BY count DESC
        """)).fetchall()
        
        total_items = sum(row[1] for row in current_stats)
        print(f"Total items in id_item_master: {total_items:,}")
        for row in current_stats:
            id_type, count, percentage = row
            print(f"  {id_type or 'NULL':<10} : {count:>8,} ({percentage:>5}%)")
        
        print("\n🔍 Analyzing data for correct classification...")
        
        # 1. RFID items: Must have matching rental_class_num in POS ItemNum (with type conversion)
        print("\n1️⃣  RFID items (in both RFIDpro API AND POS equipment)...")
        rfid_analysis = db.session.execute(text("""
            SELECT 
                COUNT(DISTINCT im.tag_id) as total_rfid,
                COUNT(DISTINCT im.rental_class_num) as unique_rental_nums
            FROM id_item_master im
            INNER JOIN pos_equipment pe ON CAST(im.rental_class_num AS DECIMAL) = CAST(pe.item_num AS DECIMAL)
            WHERE pe.category NOT IN ('UNUSED', 'NON CURRENT ITEMS')
            AND pe.inactive = 0
            AND im.rental_class_num IS NOT NULL
            AND im.rental_class_num != ''
        """)).fetchone()
        print(f"   Items with RFID tags (matching POS): {rfid_analysis[0]:,}")
        print(f"   Unique rental_class_nums matched: {rfid_analysis[1]:,}")
        
        # 2. Analyze Key field patterns (second column in pos_equipment)
        print("\n2️⃣  Analyzing Key field patterns in POS equipment...")
        
        # Get column names to find the Key field position
        columns = db.session.execute(text("""
            SELECT COLUMN_NAME, ORDINAL_POSITION 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'rfid3_database' 
            AND TABLE_NAME = 'pos_equipment'
            ORDER BY ORDINAL_POSITION
            LIMIT 3
        """)).fetchall()
        
        print("   POS Equipment columns:")
        for col in columns:
            print(f"     Position {col[1]}: {col[0]}")
        
        # The Key field is in the second position, accessed by column name from query
        key_patterns = db.session.execute(text("""
            SELECT 
                SUM(CASE WHEN SUBSTRING(key_field, 2) REGEXP '#[0-9]+$' THEN 1 ELSE 0 END) as sticker_pattern,
                SUM(CASE WHEN SUBSTRING(key_field, 2) REGEXP '-[1-4]$' AND qty > 1 THEN 1 ELSE 0 END) as bulk_pattern,
                SUM(CASE WHEN SUBSTRING(key_field, 2) REGEXP '-[0-9]+$' THEN 1 ELSE 0 END) as any_dash_pattern,
                COUNT(*) as total_pos_items,
                COUNT(DISTINCT item_num) as unique_item_nums
            FROM pos_equipment 
            WHERE category NOT IN ('UNUSED', 'NON CURRENT ITEMS')
            AND inactive = 0
        """)).fetchone()
        
        print(f"\n   Sticker items (Key ends with #num): {key_patterns[0]:,}")
        print(f"   Bulk items (Key ends with -1/-2/-3/-4 and Qty>1): {key_patterns[1]:,}")
        print(f"   Any dash pattern: {key_patterns[2]:,}")
        print(f"   Total active POS items: {key_patterns[3]:,}")
        print(f"   Unique ItemNum values: {key_patterns[4]:,}")
        
        # Get user confirmation
        print("\n" + "=" * 70)
        if len(sys.argv) > 1 and sys.argv[1] == '--execute':
            response = 'yes'
            print("🚀 Auto-executing via --execute flag")
        else:
            print("⚠️  WARNING: This will update the identifier_type for all items!")
            response = input("Proceed with identifier type correction? (yes/no): ").lower().strip()
        
        if response != 'yes':
            print("❌ Classification correction cancelled")
            return
        
        print("\n🚀 Executing identifier type corrections...")
        print("=" * 70)
        
        # Step 1: Reset all to None first for clean slate
        print("\n📝 Step 1: Resetting all items to 'None'...")
        reset_count = db.session.execute(text("""
            UPDATE id_item_master 
            SET identifier_type = 'None'
            WHERE identifier_type != 'None' OR identifier_type IS NULL
        """)).rowcount
        print(f"   Reset {reset_count:,} items to 'None'")
        
        # Step 2: Mark RFID items (with proper type conversion)
        print("\n📝 Step 2: Identifying and marking RFID items...")
        rfid_fixed = db.session.execute(text("""
            UPDATE id_item_master im
            INNER JOIN pos_equipment pe ON CAST(im.rental_class_num AS DECIMAL) = CAST(pe.item_num AS DECIMAL)
            SET im.identifier_type = 'RFID'
            WHERE pe.category NOT IN ('UNUSED', 'NON CURRENT ITEMS')
            AND pe.inactive = 0
            AND im.rental_class_num IS NOT NULL
            AND im.rental_class_num != ''
        """)).rowcount
        print(f"   ✅ Marked {rfid_fixed:,} items as RFID")
        
        # Step 3: Mark Sticker items based on POS Key patterns
        print("\n📝 Step 3: Identifying and marking Sticker items...")
        # First, find items in id_item_master that correspond to POS items with # pattern
        sticker_fixed = db.session.execute(text("""
            UPDATE id_item_master im
            INNER JOIN (
                SELECT DISTINCT CAST(item_num AS DECIMAL) as item_num_decimal
                FROM pos_equipment
                WHERE SUBSTRING(key_field, 2) REGEXP '#[0-9]+$'
                AND category NOT IN ('UNUSED', 'NON CURRENT ITEMS')
                AND inactive = 0
            ) pe ON CAST(im.rental_class_num AS DECIMAL) = pe.item_num_decimal
            SET im.identifier_type = 'Sticker'
            WHERE im.identifier_type = 'None'
        """)).rowcount
        print(f"   ✅ Marked {sticker_fixed:,} items as Sticker")
        
        # Step 4: Mark Bulk items based on POS Key patterns
        print("\n📝 Step 4: Identifying and marking Bulk items...")
        bulk_fixed = db.session.execute(text("""
            UPDATE id_item_master im
            INNER JOIN (
                SELECT DISTINCT CAST(item_num AS DECIMAL) as item_num_decimal
                FROM pos_equipment
                WHERE SUBSTRING(key_field, 2) REGEXP '-[1-4]$'
                AND qty > 1
                AND category NOT IN ('UNUSED', 'NON CURRENT ITEMS')
                AND inactive = 0
            ) pe ON CAST(im.rental_class_num AS DECIMAL) = pe.item_num_decimal
            SET im.identifier_type = 'Bulk'
            WHERE im.identifier_type = 'None'
        """)).rowcount
        print(f"   ✅ Marked {bulk_fixed:,} items as Bulk")
        
        # Commit all changes
        db.session.commit()
        
        # Show updated distribution
        print("\n📊 AFTER: Updated identifier type distribution...")
        updated_stats = db.session.execute(text("""
            SELECT 
                identifier_type,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM id_item_master), 1) as percentage
            FROM id_item_master 
            GROUP BY identifier_type
            ORDER BY identifier_type
        """)).fetchall()
        
        for row in updated_stats:
            id_type, count, percentage = row
            print(f"  {id_type or 'NULL':<10} : {count:>8,} ({percentage:>5}%)")
        
        # Calculate total corrections
        total_corrections = reset_count + rfid_fixed + sticker_fixed + bulk_fixed
        
        print("\n" + "=" * 70)
        print("✅ IDENTIFIER TYPE CORRECTIONS COMPLETED!")
        print(f"   Total items processed: {total_items:,}")
        print(f"   Total corrections made: {total_corrections:,}")
        
        # Show detailed correlation summary
        print("\n📈 RFID/POS Correlation Summary:")
        correlation_stats = db.session.execute(text("""
            SELECT 
                COUNT(DISTINCT pe.item_num) as clean_pos_items,
                COUNT(DISTINCT im.rental_class_num) as rfid_rental_classes,
                COUNT(DISTINCT CASE 
                    WHEN CAST(im.rental_class_num AS DECIMAL) = CAST(pe.item_num AS DECIMAL) 
                    THEN pe.item_num 
                END) as matched_items
            FROM pos_equipment pe
            LEFT JOIN id_item_master im 
                ON CAST(pe.item_num AS DECIMAL) = CAST(im.rental_class_num AS DECIMAL)
            WHERE pe.category NOT IN ('UNUSED', 'NON CURRENT ITEMS')
            AND pe.inactive = 0
        """)).fetchone()
        
        clean_pos, rfid_classes, matched = correlation_stats
        print(f"   Clean POS items: {clean_pos:,}")
        print(f"   RFID items with rental_class_num: {rfid_classes:,}")
        print(f"   Items successfully matched: {matched:,}")
        print(f"   POS items without RFID: {clean_pos - matched:,}")
        
        # Show breakdown by identifier type with examples
        print("\n📋 Sample items by identifier type:")
        for id_type in ['RFID', 'Sticker', 'Bulk', 'None']:
            samples = db.session.execute(text("""
                SELECT tag_id, item_name, rental_class_num
                FROM id_item_master
                WHERE identifier_type = :id_type
                LIMIT 3
            """), {'id_type': id_type}).fetchall()
            
            if samples:
                print(f"\n   {id_type} examples:")
                for s in samples:
                    print(f"     Tag: {s[0]}, Name: {s[1][:30]}, RentalClass: {s[2]}")

if __name__ == "__main__":
    main()
