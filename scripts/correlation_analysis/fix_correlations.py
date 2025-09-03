"""
Fix POS-RFID Correlations
Handles the ItemNum decimal format issue and establishes correlations
"""

import os
os.environ['FLASK_SKIP_SCHEDULER'] = '1'

from app import create_app, db
from sqlalchemy import text
import re

def normalize_item_num(item_num):
    """Normalize ItemNum by removing .0 suffix"""
    if item_num is None:
        return None
    
    # Convert to string and remove .0 suffix
    normalized = str(item_num)
    if normalized.endswith('.0'):
        normalized = normalized[:-2]
    
    return normalized

def test_correlations():
    """Test correlation potential between POS and RFIDpro data using seed data as primary correlation"""
    app = create_app()
    
    with app.app_context():
        print("🔍 ANALYZING CORRELATION POTENTIAL (POS ↔ RFIDpro seed ↔ item_master)...")
        
        # Get data volumes first
        pos_total = db.session.execute(text("SELECT COUNT(DISTINCT item_num) FROM equipment_items")).fetchone()[0]
        seed_total = db.session.execute(text("SELECT COUNT(DISTINCT rental_class_id) FROM seed_rental_classes WHERE rental_class_id IS NOT NULL")).fetchone()[0]
        rfid_total = db.session.execute(text("SELECT COUNT(DISTINCT rental_class_num) FROM id_item_master WHERE rental_class_num IS NOT NULL AND rental_class_num != ''")).fetchone()[0]
        
        print(f"\n📊 Data volumes:")
        print(f"POS equipment items: {pos_total:,}")
        print(f"RFIDpro seed rental_class_id: {seed_total:,}")
        print(f"RFIDpro item_master rental_class_num: {rfid_total:,}")
        
        # Get sample data from each system
        print(f"\n📊 Sample data comparison...")
        
        # Get POS ItemNum values (normalized)
        pos_result = db.session.execute(text("""
            SELECT DISTINCT item_num 
            FROM equipment_items 
            WHERE item_num IS NOT NULL
            ORDER BY CAST(item_num AS UNSIGNED) DESC
            LIMIT 20
        """))
        
        pos_items = [normalize_item_num(row[0]) for row in pos_result if row[0]]
        pos_items = [item for item in pos_items if item and item != '0']
        print(f"Sample POS ItemNum (normalized): {pos_items[:10]}")
        
        # Get RFIDpro seed rental_class_id values  
        seed_result = db.session.execute(text("""
            SELECT DISTINCT rental_class_id 
            FROM seed_rental_classes 
            WHERE rental_class_id IS NOT NULL 
            AND rental_class_id != ''
            ORDER BY CAST(rental_class_id AS UNSIGNED) DESC
            LIMIT 20
        """))
        
        seed_classes = [str(row[0]).strip() for row in seed_result if row[0] and str(row[0]).strip()]
        print(f"Sample RFIDpro seed rental_class_id: {seed_classes[:10]}")
        
        # Get RFID rental_class_num values
        rfid_result = db.session.execute(text("""
            SELECT DISTINCT rental_class_num 
            FROM id_item_master 
            WHERE rental_class_num IS NOT NULL 
            AND rental_class_num != ''
            ORDER BY CAST(rental_class_num AS UNSIGNED) DESC
            LIMIT 20
        """))
        
        rfid_classes = [str(row[0]).strip() for row in rfid_result if row[0] and str(row[0]).strip()]
        print(f"Sample RFID rental_class_num: {rfid_classes[:10]}")
        
        # Find correlations: POS ↔ seed_rental_classes
        pos_set = set(pos_items)
        seed_set = set(seed_classes)
        pos_seed_matches = pos_set & seed_set
        
        # Find correlations: seed_rental_classes ↔ item_master  
        seed_rfid_matches = seed_set & set(rfid_classes)
        
        # Find three-way correlations: POS ↔ seed ↔ item_master
        threeway_matches = pos_set & seed_set & set(rfid_classes)
        
        print(f"\n🎯 CORRELATION ANALYSIS:")
        print(f"POS ↔ RFIDpro seed matches: {len(pos_seed_matches)}")
        print(f"RFIDpro seed ↔ item_master matches: {len(seed_rfid_matches)}")
        print(f"Three-way POS ↔ seed ↔ item_master matches: {len(threeway_matches)}")
        print(f"Sample three-way matches: {list(threeway_matches)[:10]}")
        
        print(f"\n📈 CORRELATION RATES:")
        print(f"POS → RFIDpro seed rate: {len(pos_seed_matches)/pos_total*100:.1f}%")
        print(f"Expected correlations should be: {len(pos_seed_matches):,} (not just 52!)")
        
        return pos_seed_matches

def create_correlation_table():
    """Create a correlation mapping table"""
    app = create_app()
    
    with app.app_context():
        print("🔧 CREATING CORRELATION MAPPING...")
        
        try:
            # Drop and recreate correlation table with enhanced schema
            db.session.execute(text("DROP TABLE IF EXISTS equipment_rfid_correlations"))
            
            # Create enhanced correlation table
            db.session.execute(text("""
                CREATE TABLE equipment_rfid_correlations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    pos_item_num VARCHAR(50) NOT NULL,
                    normalized_item_num VARCHAR(50) NOT NULL,
                    rfid_rental_class_num VARCHAR(50) NOT NULL,
                    pos_equipment_name VARCHAR(500),
                    rfid_common_name VARCHAR(500),
                    rfid_tag_count INT DEFAULT 0,
                    confidence_score DECIMAL(5,2) DEFAULT 100.00,
                    correlation_type VARCHAR(30) DEFAULT 'exact_match',
                    seed_class_id VARCHAR(50),
                    seed_category VARCHAR(200),
                    seed_subcategory VARCHAR(200),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_pos_item (pos_item_num),
                    INDEX idx_rfid_class (rfid_rental_class_num),
                    INDEX idx_normalized (normalized_item_num),
                    INDEX idx_seed_class (seed_class_id),
                    INDEX idx_correlation_type (correlation_type)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            
            db.session.commit()
            print("✅ Correlation table created successfully")
            
        except Exception as e:
            print(f"❌ Error creating correlation table: {e}")
            db.session.rollback()

def populate_correlations():
    """Populate the correlation table using seed data as primary correlation source"""
    app = create_app()
    
    with app.app_context():
        print("🔄 POPULATING CORRELATIONS (POS ↔ seed ↔ item_master)...")
        
        try:
            # Clear existing correlations
            db.session.execute(text("DELETE FROM equipment_rfid_correlations"))
            
            # Get all POS equipment items
            equipment_result = db.session.execute(text("""
                SELECT item_num, name, category 
                FROM equipment_items 
                ORDER BY item_num
            """))
            
            correlations_found = 0
            total_processed = 0
            
            for eq_row in equipment_result:
                total_processed += 1
                pos_item_num = str(eq_row[0])
                normalized = normalize_item_num(eq_row[0])
                equipment_name = eq_row[1]
                equipment_category = eq_row[2]
                
                if normalized:
                    # First check if this normalized ID exists in seed_rental_classes
                    seed_result = db.session.execute(text("""
                        SELECT rental_class_id, common_name, bin_location
                        FROM seed_rental_classes 
                        WHERE rental_class_id = :rental_class_id
                        LIMIT 1
                    """), {'rental_class_id': normalized})
                    
                    seed_match = seed_result.fetchone()
                    
                    if seed_match:
                        # Get RFID tag count from item_master if available
                        rfid_result = db.session.execute(text("""
                            SELECT rental_class_num, common_name, COUNT(*) as tag_count
                            FROM id_item_master 
                            WHERE rental_class_num = :rental_class
                            GROUP BY rental_class_num, common_name
                            LIMIT 1
                        """), {'rental_class': normalized})
                        
                        rfid_match = rfid_result.fetchone()
                        
                        # Use RFID data if available, otherwise seed data
                        rfid_name = rfid_match[1] if rfid_match else seed_match[1]
                        tag_count = rfid_match[2] if rfid_match else 0
                        correlation_type = 'pos_seed_rfid' if rfid_match else 'pos_seed_only'
                        
                        # Insert correlation
                        db.session.execute(text("""
                            INSERT INTO equipment_rfid_correlations 
                            (pos_item_num, normalized_item_num, rfid_rental_class_num, 
                             pos_equipment_name, rfid_common_name, rfid_tag_count, 
                             confidence_score, correlation_type,
                             seed_class_id, seed_category, seed_subcategory)
                            VALUES 
                            (:pos_item, :normalized, :rfid_class, 
                             :pos_name, :rfid_name, :tag_count, 
                             100.00, :corr_type, :seed_id, :seed_cat, :seed_subcat)
                        """), {
                            'pos_item': pos_item_num,
                            'normalized': normalized,
                            'rfid_class': normalized,  # Same as normalized for seed correlation
                            'pos_name': equipment_name,
                            'rfid_name': rfid_name,
                            'tag_count': tag_count,
                            'corr_type': correlation_type,
                            'seed_id': seed_match[0],
                            'seed_cat': seed_match[2],  # bin_location as category
                            'seed_subcat': None  # No subcategory in seed_rental_classes
                        })
                        
                        correlations_found += 1
                
                # Commit every 100 records
                if total_processed % 100 == 0:
                    db.session.commit()
                    print(f"  Processed {total_processed} items, found {correlations_found} correlations...")
            
            # Final commit
            db.session.commit()
            
            print(f"✅ CORRELATION COMPLETE!")
            print(f"   Total equipment processed: {total_processed:,}")
            print(f"   Correlations established: {correlations_found:,}")
            print(f"   Success rate: {correlations_found/total_processed*100:.1f}%")
            
        except Exception as e:
            print(f"❌ Error populating correlations: {e}")
            db.session.rollback()

if __name__ == "__main__":
    print("🚀 STARTING CORRELATION FIX PROCESS...")
    
    # Step 1: Test correlations to see potential
    matches = test_correlations()
    
    if len(matches) > 0:
        print(f"\n✅ Found {len(matches)} potential correlations!")
        
        # Step 2: Create correlation table
        create_correlation_table()
        
        # Step 3: Populate correlations
        populate_correlations()
        
        print("\n🎯 CORRELATION SETUP COMPLETE!")
        print("You can now use equipment_rfid_correlations table for analytics")
        
    else:
        print("\n❌ No correlations found - check data formats")