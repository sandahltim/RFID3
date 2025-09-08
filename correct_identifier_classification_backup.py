#!/usr/bin/env python3
"""
Correct Identifier Type Classification Service
Fixes the identifier_type column based on actual business logic:

1. RFID: Items in both RFIDpro API and POS equipment (rental_class_num = ItemNum) 
2. Sticker: Serialized items (Key ends with #1, #2, #3, etc.) - individual tracking with QR/RFID soon
3. Bulk: Store-specific items (Key ends with -1, -2, -3, -4) with quantity tracking
4. None/QR: Items that don't fit other categories
"""

from app import create_app, db
from app.models.db_models import ItemMaster
from sqlalchemy import text
import sys
from datetime import datetime
import re

def main():
    app = create_app()
    
    with app.app_context():
        print("🏷️  RFID3 Correct Identifier Type Classification")
        print("=" * 65)
        
        print("📊 Current (incorrect) identifier type distribution...")
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
        print(f"Total items: {total_items:,}")
        for row in current_stats:
            id_type, count, percentage = row
            print(f"  {id_type or 'NULL'}: {count:,} ({percentage}%)")
        
        print("\n🔍 Analyzing correct classification logic...")
        
        # 1. RFID items: Must have matching rental_class_num in POS ItemNum
        print("1️⃣  RFID items (in both RFIDpro API AND POS equipment)...")
        rfid_items = db.session.execute(text("""
            SELECT COUNT(DISTINCT im.tag_id)
            FROM id_item_master im
            INNER JOIN pos_equipment pe ON im.rental_class_num = pe.item_num
            WHERE pe.category NOT IN ('UNUSED', 'NON CURRENT ITEMS')
            AND pe.inactive = 0
            AND im.rental_class_num IS NOT NULL
        """)).scalar()
        print(f"   True RFID items: {rfid_items:,}")
        
        # 2. Check if we need to import Key field from CSV for proper analysis
        has_key_data = db.session.execute(text("""
            SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'rfid3_database' 
            AND TABLE_NAME = 'pos_equipment' 
            AND COLUMN_NAME = 'key_field'
        """)).scalar()
        
        if has_key_data == 0:
            print("⚠️  Key field not imported from CSV - need to update import process")
            print("   Cannot classify Sticker/Bulk types without Key field")
            
            if len(sys.argv) > 1 and sys.argv[1] == '--fix-schema':
                print("🔧 Adding key_field column to pos_equipment...")
                db.session.execute(text("""
                    ALTER TABLE pos_equipment 
                    ADD COLUMN key_field VARCHAR(100) AFTER item_num
                """))
                db.session.commit()
                print("✅ Added key_field column - need to re-import CSV data")
                return
        else:
            print("✅ Key field exists in database")
            
            # Analyze patterns in Key field
            print("2️⃣  Sticker items (serialized with #num pattern)...")
            sticker_count = db.session.execute(text("""
                SELECT COUNT(*)
                FROM pos_equipment
                WHERE key_field REGEXP '#[0-9]+$'
                AND category NOT IN ('UNUSED', 'NON CURRENT ITEMS')
                AND inactive = 0
            """)).scalar()
            print(f"   Serialized items (future QR/RFID): {sticker_count:,}")
            
            print("3️⃣  Bulk items (store-specific with -1,-2,-3,-4 pattern)...")
            bulk_count = db.session.execute(text("""
                SELECT COUNT(*)
                FROM pos_equipment  
                WHERE key_field REGEXP '.*-[1-4]$'
                AND category NOT IN ('UNUSED', 'NON CURRENT ITEMS')
                AND inactive = 0
                AND qty > 1
            """)).scalar()
            print(f"   Store-specific bulk items: {bulk_count:,}")
        
        # Execute classification fix
        if len(sys.argv) > 1 and sys.argv[1] == '--execute':
            response = 'yes'
            print("Auto-confirmed via --execute flag")
        else:
            response = input("Proceed with identifier type correction? (yes/no): ").lower().strip()
        
        if response != 'yes':
            print("Classification correction cancelled")
            return
        
        print("\n🚀 Executing identifier type corrections...")
        corrections_made = 0
        
        # Fix RFID classification: Only items with RFID API match
        rfid_fixed = db.session.execute(text("""
            UPDATE id_item_master im
            INNER JOIN pos_equipment pe ON im.rental_class_num = pe.item_num
            SET im.identifier_type = 'RFID'
            WHERE pe.category NOT IN ('UNUSED', 'NON CURRENT ITEMS')
            AND pe.inactive = 0
            AND im.rental_class_num IS NOT NULL
            AND im.identifier_type != 'RFID'
        """)).rowcount
        corrections_made += rfid_fixed
        print(f"✅ Fixed RFID classification: {rfid_fixed:,} items")
        
        # Fix non-RFID items (items NOT in POS or not matching)
        non_rfid_fixed = db.session.execute(text("""
            UPDATE id_item_master im
            LEFT JOIN pos_equipment pe ON im.rental_class_num = pe.item_num
                AND pe.category NOT IN ('UNUSED', 'NON CURRENT ITEMS')
                AND pe.inactive = 0
            SET im.identifier_type = 'None'
            WHERE (pe.item_num IS NULL OR im.rental_class_num IS NULL)
            AND im.identifier_type != 'None'
        """)).rowcount
        corrections_made += non_rfid_fixed
        print(f"✅ Fixed non-RFID classification: {non_rfid_fixed:,} items")
        
        if has_key_data > 0:
            # Note: Sticker and Bulk classification would need the Key field
            # This would be implemented after CSV import is updated
            print("ℹ️  Sticker/Bulk classification requires Key field in database")
            print("   Run CSV re-import first, then run this script again")
        
        db.session.commit()
        
        print(f"\n📊 Updated identifier type distribution...")
        updated_stats = db.session.execute(text("""
            SELECT 
                identifier_type,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM id_item_master), 1) as percentage
            FROM id_item_master 
            GROUP BY identifier_type
            ORDER BY count DESC
        """)).fetchall()
        
        for row in updated_stats:
            id_type, count, percentage = row
            print(f"  {id_type or 'NULL'}: {count:,} ({percentage}%)")
        
        print(f"\n✅ Identifier type corrections completed!")
        print(f"   Total corrections: {corrections_made:,}")
        
        # Show correlation stats
        print(f"\n📈 RFID/POS Correlation Summary:")
        correlation_stats = db.session.execute(text("""
            SELECT 
                COUNT(DISTINCT pe.item_num) as clean_pos_items,
                COUNT(DISTINCT im.rental_class_num) as rfid_rental_classes,
                COUNT(DISTINCT CASE WHEN im.rental_class_num = pe.item_num THEN pe.item_num END) as matched_items
            FROM pos_equipment pe
            LEFT JOIN id_item_master im ON pe.item_num = im.rental_class_num
            WHERE pe.category NOT IN ('UNUSED', 'NON CURRENT ITEMS')
            AND pe.inactive = 0
        """)).fetchone()
        
        clean_pos, rfid_classes, matched = correlation_stats
        print(f"   Clean POS items: {clean_pos:,}")
        print(f"   RFID rental_class_nums: {rfid_classes:,}")
        print(f"   Items with RFID tags: {matched:,}")
        print(f"   Items without RFID: {clean_pos - matched:,}")

if __name__ == "__main__":
    main()