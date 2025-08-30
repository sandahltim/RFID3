#!/usr/bin/env python3
"""
Simple and fast identifier type correction
"""
from app import create_app, db
from sqlalchemy import text
from datetime import datetime

def main():
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("IDENTIFIER TYPE CLASSIFICATION FIX")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Get before stats
        print("\nBEFORE:")
        before = db.session.execute(text("""
            SELECT identifier_type, COUNT(*) as cnt
            FROM id_item_master 
            GROUP BY identifier_type
        """)).fetchall()
        for row in before:
            print(f"  {row[0] or 'NULL'}: {row[1]:,}")
        
        print("\nProcessing...")
        
        # 1. Reset all to None
        print("  Resetting all to None...")
        db.session.execute(text("UPDATE id_item_master SET identifier_type = 'None'"))
        
        # 2. Mark RFID items (simplified query)
        print("  Marking RFID items...")
        db.session.execute(text("""
            UPDATE id_item_master im
            SET identifier_type = 'RFID'
            WHERE EXISTS (
                SELECT 1 FROM pos_equipment pe 
                WHERE CAST(im.rental_class_num AS DECIMAL) = CAST(pe.item_num AS DECIMAL)
                AND pe.category NOT IN ('UNUSED', 'NON CURRENT ITEMS')
                AND pe.inactive = 0
            )
            AND im.rental_class_num IS NOT NULL
            AND im.rental_class_num != ''
        """))
        
        db.session.commit()
        print("  Done!")
        
        # Get after stats
        print("\nAFTER:")
        after = db.session.execute(text("""
            SELECT identifier_type, COUNT(*) as cnt
            FROM id_item_master 
            GROUP BY identifier_type
            ORDER BY identifier_type
        """)).fetchall()
        for row in after:
            print(f"  {row[0] or 'NULL'}: {row[1]:,}")
        
        # Show RFID correlation
        rfid_count = db.session.execute(text("""
            SELECT COUNT(*) FROM id_item_master 
            WHERE identifier_type = 'RFID'
        """)).scalar()
        
        print(f"\n✅ SUCCESS: {rfid_count:,} items correctly marked as RFID")
        print("   (These have matching rental_class_num in POS equipment)")

if __name__ == "__main__":
    main()
