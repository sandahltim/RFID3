#!/usr/bin/env python3
"""
Batched identifier type correction to avoid lock timeouts
"""
from app import create_app, db
from sqlalchemy import text
from datetime import datetime

def main():
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("BATCHED IDENTIFIER TYPE CLASSIFICATION FIX")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Get before stats
        print("\nBEFORE:")
        before = db.session.execute(text("""
            SELECT identifier_type, COUNT(*) as cnt
            FROM id_item_master 
            GROUP BY identifier_type
            ORDER BY identifier_type
        """)).fetchall()
        total_before = sum(row[1] for row in before)
        for row in before:
            pct = (row[1] / total_before * 100) if total_before > 0 else 0
            print(f"  {row[0] or 'NULL':<10}: {row[1]:>7,} ({pct:>5.1f}%)")
        
        print(f"\nTotal items: {total_before:,}")
        
        # Find items that should be RFID
        print("\n1. Finding items with RFID correlation...")
        rfid_items = db.session.execute(text("""
            SELECT im.tag_id
            FROM id_item_master im
            WHERE EXISTS (
                SELECT 1 FROM pos_equipment pe 
                WHERE CAST(im.rental_class_num AS DECIMAL) = CAST(pe.item_num AS DECIMAL)
                AND pe.category NOT IN ('UNUSED', 'NON CURRENT ITEMS')
                AND pe.inactive = 0
            )
            AND im.rental_class_num IS NOT NULL
            AND im.rental_class_num != ''
        """)).fetchall()
        
        rfid_tags = [row[0] for row in rfid_items]
        print(f"   Found {len(rfid_tags):,} items with RFID correlation")
        
        # Process in batches
        BATCH_SIZE = 1000
        
        # Reset non-RFID items to None
        print("\n2. Resetting non-RFID items to 'None'...")
        if rfid_tags:
            # Reset items that are NOT in the RFID list
            for i in range(0, len(rfid_tags), BATCH_SIZE):
                batch = rfid_tags[i:i+BATCH_SIZE]
                placeholders = ','.join([':tag_' + str(j) for j in range(len(batch))])
                params = {f'tag_{j}': tag for j, tag in enumerate(batch)}
                
                db.session.execute(text(f"""
                    UPDATE id_item_master 
                    SET identifier_type = 'None'
                    WHERE tag_id NOT IN ({placeholders})
                    AND identifier_type != 'None'
                """), params)
                
                if i % (BATCH_SIZE * 10) == 0:
                    print(f"   Processed {i:,} / {len(rfid_tags):,} exclusions...")
        else:
            # No RFID items, reset all
            db.session.execute(text("""
                UPDATE id_item_master 
                SET identifier_type = 'None'
                WHERE identifier_type != 'None'
            """))
        
        # Also reset any remaining non-None items
        db.session.execute(text("""
            UPDATE id_item_master 
            SET identifier_type = 'None'
            WHERE identifier_type IS NULL OR identifier_type NOT IN ('None', 'RFID')
        """))
        
        print("   Done resetting")
        
        # Mark RFID items
        print("\n3. Marking RFID items...")
        if rfid_tags:
            for i in range(0, len(rfid_tags), BATCH_SIZE):
                batch = rfid_tags[i:i+BATCH_SIZE]
                placeholders = ','.join([':tag_' + str(j) for j in range(len(batch))])
                params = {f'tag_{j}': tag for j, tag in enumerate(batch)}
                
                db.session.execute(text(f"""
                    UPDATE id_item_master 
                    SET identifier_type = 'RFID'
                    WHERE tag_id IN ({placeholders})
                """), params)
                
                if i % (BATCH_SIZE * 10) == 0:
                    print(f"   Marked {i:,} / {len(rfid_tags):,} as RFID...")
            
            print(f"   Marked {len(rfid_tags):,} items as RFID")
        
        # Commit all changes
        db.session.commit()
        print("\n✅ Changes committed")
        
        # Get after stats
        print("\nAFTER:")
        after = db.session.execute(text("""
            SELECT identifier_type, COUNT(*) as cnt
            FROM id_item_master 
            GROUP BY identifier_type
            ORDER BY identifier_type
        """)).fetchall()
        total_after = sum(row[1] for row in after)
        for row in after:
            pct = (row[1] / total_after * 100) if total_after > 0 else 0
            print(f"  {row[0] or 'NULL':<10}: {row[1]:>7,} ({pct:>5.1f}%)")
        
        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY:")
        print(f"  Total items processed: {total_after:,}")
        print(f"  Items with RFID tags: {len(rfid_tags):,}")
        print(f"  Items without RFID: {total_after - len(rfid_tags):,}")
        
        # Show correlation details
        print("\n📈 RFID/POS Correlation Details:")
        correlation = db.session.execute(text("""
            SELECT 
                COUNT(DISTINCT pe.item_num) as pos_items,
                COUNT(DISTINCT im.rental_class_num) as rfid_nums,
                COUNT(DISTINCT CASE 
                    WHEN im.identifier_type = 'RFID' 
                    THEN im.rental_class_num 
                END) as matched
            FROM pos_equipment pe
            LEFT JOIN id_item_master im 
                ON CAST(pe.item_num AS DECIMAL) = CAST(im.rental_class_num AS DECIMAL)
            WHERE pe.category NOT IN ('UNUSED', 'NON CURRENT ITEMS')
            AND pe.inactive = 0
        """)).fetchone()
        
        print(f"  Active POS items: {correlation[0]:,}")
        print(f"  Unique rental_class_nums in RFID: {correlation[1]:,}") 
        print(f"  Successfully matched: {correlation[2]:,}")
        
        print("\n✅ Classification correction completed successfully!")

if __name__ == "__main__":
    main()
