#!/usr/bin/env python3
"""
Comprehensive RFID Data Correlation Fix
This script fixes the major data correlation issues in the RFID3 system
"""

import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG

class ComprehensiveDataFix:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.issues_found = []
        self.fixes_applied = []
        
    def connect(self):
        """Connect to database"""
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.connection.cursor(dictionary=True)
            print("✓ Connected to database")
            return True
        except Error as e:
            print(f"✗ Database connection failed: {e}")
            return False
    
    def analyze_issues(self):
        """Comprehensive analysis of data issues"""
        print("\n" + "="*80)
        print("COMPREHENSIVE DATA ANALYSIS")
        print("="*80)
        
        issues = []
        
        # Issue 1: Check RFID items in wrong stores
        print("\n1. Analyzing RFID Store Assignments...")
        query = """
        SELECT 
            current_store,
            COUNT(*) as rfid_count,
            COUNT(DISTINCT rental_class_num) as rental_classes
        FROM id_item_master
        WHERE identifier_type = 'RFID'
        GROUP BY current_store
        """
        self.cursor.execute(query)
        rfid_stores = self.cursor.fetchall()
        
        for store in rfid_stores:
            if store['current_store'] not in ['8101', None]:
                issues.append({
                    'type': 'RFID_WRONG_STORE',
                    'store': store['current_store'],
                    'count': store['rfid_count'],
                    'severity': 'HIGH',
                    'fix': f"Move {store['rfid_count']} RFID items from store {store['current_store']}"
                })
                print(f"   ✗ Store {store['current_store']}: {store['rfid_count']} RFID items (INCORRECT)")
            elif store['current_store'] is None:
                print(f"   ⚠ NULL store: {store['rfid_count']} RFID items (needs assignment)")
        
        # Issue 2: Check POS equipment key patterns
        print("\n2. Analyzing POS Equipment Key Patterns...")
        query = """
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN key_field LIKE '%-1' THEN 1 ELSE 0 END) as bulk_1,
            SUM(CASE WHEN key_field LIKE '%-2' THEN 1 ELSE 0 END) as bulk_2,
            SUM(CASE WHEN key_field LIKE '%-3' THEN 1 ELSE 0 END) as bulk_3,
            SUM(CASE WHEN key_field LIKE '%-4' THEN 1 ELSE 0 END) as bulk_4,
            SUM(CASE WHEN key_field LIKE '%#%' THEN 1 ELSE 0 END) as serialized
        FROM pos_equipment
        """
        self.cursor.execute(query)
        pos_patterns = self.cursor.fetchone()
        
        print(f"   Total POS items: {pos_patterns['total']:,}")
        print(f"   Bulk -1 items: {pos_patterns['bulk_1']:,}")
        print(f"   Bulk -2 items: {pos_patterns['bulk_2']:,}")
        print(f"   Bulk -3 items: {pos_patterns['bulk_3']:,}")
        print(f"   Bulk -4 items: {pos_patterns['bulk_4']:,}")
        print(f"   Serialized (#) items: {pos_patterns['serialized']:,}")
        
        total_bulk = (pos_patterns['bulk_1'] + pos_patterns['bulk_2'] + 
                     pos_patterns['bulk_3'] + pos_patterns['bulk_4'])
        
        if total_bulk > 0:
            issues.append({
                'type': 'UNCLASSIFIED_BULK',
                'count': total_bulk,
                'severity': 'MEDIUM',
                'fix': f"Classify {total_bulk:,} bulk items in POS equipment"
            })
        
        # Issue 3: Check correlation between tables
        print("\n3. Analyzing Table Correlations...")
        query = """
        SELECT 
            (SELECT COUNT(*) FROM id_item_master) as rfid_items,
            (SELECT COUNT(*) FROM pos_equipment) as pos_items,
            (SELECT COUNT(*) FROM pos_rfid_correlations WHERE is_active = 1) as active_correlations
        """
        self.cursor.execute(query)
        counts = self.cursor.fetchone()
        
        print(f"   ID Item Master records: {counts['rfid_items']:,}")
        print(f"   POS Equipment records: {counts['pos_items']:,}")
        print(f"   Active correlations: {counts['active_correlations']:,}")
        
        if counts['active_correlations'] == 0:
            issues.append({
                'type': 'NO_CORRELATIONS',
                'severity': 'HIGH',
                'fix': 'Create correlations between RFID and POS data'
            })
        
        # Issue 4: Check store mappings
        print("\n4. Analyzing Store Mappings...")
        query = """
        SELECT 
            rfid_store_code,
            pos_store_code,
            store_name,
            is_active
        FROM store_correlations
        ORDER BY rfid_store_code
        """
        self.cursor.execute(query)
        mappings = self.cursor.fetchall()
        
        for mapping in mappings:
            status = "✓" if mapping['is_active'] else "✗"
            print(f"   {status} {mapping['rfid_store_code']} → {mapping['pos_store_code']} ({mapping['store_name']})")
        
        self.issues_found = issues
        
        # Summary
        print("\n" + "="*80)
        print(f"ISSUES FOUND: {len(issues)}")
        print("="*80)
        
        for issue in issues:
            print(f"\n[{issue['severity']}] {issue['type']}")
            print(f"   Fix: {issue['fix']}")
        
        return issues
    
    def create_comprehensive_fix_sql(self):
        """Generate comprehensive SQL fix script"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        sql_file = f"/home/tim/RFID3/scripts/comprehensive_fix_{timestamp}.sql"
        
        with open(sql_file, 'w') as f:
            f.write(f"""-- ============================================================================
-- COMPREHENSIVE RFID DATA FIX
-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- ============================================================================

-- Create backup tables
CREATE TABLE IF NOT EXISTS id_item_master_backup_{timestamp} AS SELECT * FROM id_item_master;
CREATE TABLE IF NOT EXISTS pos_equipment_backup_{timestamp} AS SELECT * FROM pos_equipment;
CREATE TABLE IF NOT EXISTS store_correlations_backup_{timestamp} AS SELECT * FROM store_correlations;

-- ============================================================================
-- FIX 1: CORRECT STORE CORRELATIONS
-- ============================================================================

-- Clear and reset store correlations
TRUNCATE TABLE store_correlations;

INSERT INTO store_correlations (rfid_store_code, pos_store_code, store_name, store_location, is_active) VALUES
('8101', '4', 'Fridley RFID Test', 'Fridley, MN', 1),
('3607', '1', 'Wayzata', 'Wayzata, MN', 1),
('6800', '2', 'Brooklyn Park', 'Brooklyn Park, MN', 1),
('728', '3', 'Elk River', 'Elk River, MN', 1),
('000', '0', 'Header/System', 'System Generated', 1);

-- ============================================================================
-- FIX 2: CORRECT RFID ASSIGNMENTS IN ID_ITEM_MASTER
-- ============================================================================

-- Reset all identifier types
UPDATE id_item_master SET identifier_type = 'None';

-- Mark NULL store RFID items and assign to Fridley
UPDATE id_item_master 
SET current_store = '8101',
    identifier_type = 'RFID'
WHERE current_store IS NULL 
    AND rental_class_num IS NOT NULL 
    AND rental_class_num != '';

-- Remove incorrect RFID assignments from other stores
UPDATE id_item_master 
SET identifier_type = 'None'
WHERE identifier_type = 'RFID' 
    AND current_store NOT IN ('8101');

-- ============================================================================
-- FIX 3: CREATE POS-RFID CORRELATIONS
-- ============================================================================

-- Clear existing correlations
TRUNCATE TABLE pos_rfid_correlations;

-- Create correlations for Fridley RFID items
INSERT INTO pos_rfid_correlations (
    pos_item_num,
    pos_item_desc,
    rfid_tag_id,
    rfid_rental_class_num,
    rfid_common_name,
    correlation_type,
    confidence_score,
    is_active,
    created_at,
    created_by
)
SELECT 
    pe.item_num,
    pe.name,
    im.tag_id,
    im.rental_class_num,
    im.common_name,
    'exact',
    1.00,
    1,
    NOW(),
    'system_fix'
FROM pos_equipment pe
INNER JOIN id_item_master im ON pe.current_store = '4.0' AND im.current_store = '8101'
WHERE im.identifier_type = 'RFID'
    AND im.rental_class_num IS NOT NULL
LIMIT 1000;  -- Start with first 1000 correlations

-- ============================================================================
-- FIX 4: CLASSIFY POS EQUIPMENT IDENTIFIERS
-- ============================================================================

-- Add identifier_type column to pos_equipment if not exists
ALTER TABLE pos_equipment 
ADD COLUMN IF NOT EXISTS identifier_type VARCHAR(20) DEFAULT 'None';

-- Classify bulk items in POS equipment
UPDATE pos_equipment 
SET identifier_type = 'Bulk'
WHERE key_field LIKE '%-1' 
   OR key_field LIKE '%-2' 
   OR key_field LIKE '%-3' 
   OR key_field LIKE '%-4';

-- Classify serialized items
UPDATE pos_equipment 
SET identifier_type = 'Sticker'
WHERE key_field LIKE '%#%';

-- Mark Fridley items with RFID correlations
UPDATE pos_equipment pe
SET pe.identifier_type = 'RFID'
WHERE pe.current_store = '4.0'
    AND EXISTS (
        SELECT 1 FROM pos_rfid_correlations prc 
        WHERE prc.pos_item_num = pe.item_num 
        AND prc.is_active = 1
    );

-- ============================================================================
-- FIX 5: CREATE PROPER VIEWS
-- ============================================================================

-- Drop and recreate corrected store summary view
DROP VIEW IF EXISTS v_store_summary_corrected;

CREATE VIEW v_store_summary_corrected AS
SELECT 
    sc.store_name,
    sc.rfid_store_code,
    sc.pos_store_code,
    COUNT(DISTINCT im.tag_id) as rfid_items,
    COUNT(DISTINCT pe.id) as pos_items,
    SUM(CASE WHEN im.identifier_type = 'RFID' THEN 1 ELSE 0 END) as active_rfid,
    SUM(CASE WHEN pe.identifier_type = 'Bulk' THEN 1 ELSE 0 END) as bulk_items,
    SUM(CASE WHEN pe.identifier_type = 'Sticker' THEN 1 ELSE 0 END) as sticker_items
FROM store_correlations sc
LEFT JOIN id_item_master im ON sc.rfid_store_code = im.current_store
LEFT JOIN pos_equipment pe ON sc.pos_store_code = pe.current_store
WHERE sc.is_active = 1
GROUP BY sc.store_name, sc.rfid_store_code, sc.pos_store_code;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT 'VERIFICATION RESULTS' as Status;

-- Verify RFID exclusivity to Fridley
SELECT 
    'RFID in Fridley Only' as Check_Item,
    CASE 
        WHEN COUNT(*) = 0 THEN 'PASS'
        ELSE CONCAT('FAIL: ', COUNT(*), ' items')
    END as Result
FROM id_item_master
WHERE identifier_type = 'RFID' AND current_store != '8101';

-- Verify bulk classification
SELECT 
    'Bulk Items Classified' as Check_Item,
    CONCAT(COUNT(*), ' items') as Result
FROM pos_equipment
WHERE identifier_type = 'Bulk';

-- Verify correlations created
SELECT 
    'Active Correlations' as Check_Item,
    CONCAT(COUNT(*), ' correlations') as Result
FROM pos_rfid_correlations
WHERE is_active = 1;

-- Show final summary
SELECT * FROM v_store_summary_corrected;
""")
        
        print(f"\n✓ SQL script generated: {sql_file}")
        return sql_file
    
    def apply_basic_fixes(self):
        """Apply basic fixes that can be done safely"""
        print("\n" + "="*80)
        print("APPLYING BASIC FIXES")
        print("="*80)
        
        try:
            # Fix 1: Update store correlations
            print("\n1. Updating store correlations...")
            
            # Deactivate all
            self.cursor.execute("UPDATE store_correlations SET is_active = 0")
            
            # Insert/update correct mappings
            mappings = [
                ('8101', '4', 'Fridley RFID Test', 'Fridley, MN'),
                ('3607', '1', 'Wayzata', 'Wayzata, MN'),
                ('6800', '2', 'Brooklyn Park', 'Brooklyn Park, MN'),
                ('728', '3', 'Elk River', 'Elk River, MN'),
                ('000', '0', 'Header/System', 'System Generated')
            ]
            
            for rfid_code, pos_code, name, location in mappings:
                query = """
                INSERT INTO store_correlations (rfid_store_code, pos_store_code, store_name, store_location, is_active)
                VALUES (%s, %s, %s, %s, 1)
                ON DUPLICATE KEY UPDATE
                    store_name = VALUES(store_name),
                    store_location = VALUES(store_location),
                    is_active = 1
                """
                self.cursor.execute(query, (rfid_code, pos_code, name, location))
            
            self.connection.commit()
            print("   ✓ Store correlations updated")
            
            # Fix 2: Reassign NULL store RFID items to Fridley
            print("\n2. Reassigning NULL store RFID items...")
            
            query = """
            UPDATE id_item_master 
            SET current_store = '8101'
            WHERE current_store IS NULL 
                AND rental_class_num IS NOT NULL 
                AND rental_class_num != ''
                AND identifier_type = 'RFID'
            """
            self.cursor.execute(query)
            reassigned = self.cursor.rowcount
            self.connection.commit()
            
            print(f"   ✓ Reassigned {reassigned} RFID items to Fridley")
            
            # Fix 3: Remove RFID from wrong stores
            print("\n3. Removing RFID from non-Fridley stores...")
            
            query = """
            UPDATE id_item_master 
            SET identifier_type = 'None'
            WHERE identifier_type = 'RFID' 
                AND current_store NOT IN ('8101')
            """
            self.cursor.execute(query)
            removed = self.cursor.rowcount
            self.connection.commit()
            
            print(f"   ✓ Removed RFID designation from {removed} items")
            
            self.fixes_applied = [
                f"Updated store correlations",
                f"Reassigned {reassigned} NULL store RFID items to Fridley",
                f"Removed RFID from {removed} non-Fridley items"
            ]
            
            return True
            
        except Error as e:
            print(f"\n✗ Error applying fixes: {e}")
            self.connection.rollback()
            return False
    
    def generate_report(self):
        """Generate comprehensive report"""
        print("\n" + "="*80)
        print("FINAL REPORT")
        print("="*80)
        
        # Get final statistics
        query = """
        SELECT 
            current_store,
            identifier_type,
            COUNT(*) as count
        FROM id_item_master
        WHERE identifier_type = 'RFID'
        GROUP BY current_store, identifier_type
        """
        self.cursor.execute(query)
        rfid_final = self.cursor.fetchall()
        
        print("\nFinal RFID Distribution:")
        for row in rfid_final:
            print(f"   Store {row['current_store']}: {row['count']} RFID items")
        
        print("\nFixes Applied:")
        for fix in self.fixes_applied:
            print(f"   • {fix}")
        
        # Save report
        report = {
            'timestamp': datetime.now().isoformat(),
            'issues_found': self.issues_found,
            'fixes_applied': self.fixes_applied,
            'final_rfid_distribution': rfid_final
        }
        
        report_file = f"/home/tim/RFID3/logs/comprehensive_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n✓ Report saved to: {report_file}")
    
    def run(self, apply_fixes=False):
        """Run the comprehensive fix process"""
        if not self.connect():
            return False
        
        try:
            # Analyze issues
            issues = self.analyze_issues()
            
            # Generate SQL script
            sql_file = self.create_comprehensive_fix_sql()
            
            if apply_fixes:
                print("\n⚠️  Applying fixes to database...")
                if self.apply_basic_fixes():
                    print("✓ Basic fixes applied successfully")
                    self.generate_report()
                else:
                    print("✗ Fix application failed")
                    return False
            else:
                print("\n" + "="*80)
                print("DRY RUN COMPLETE")
                print("="*80)
                print(f"\nTo apply fixes:")
                print(f"1. Review SQL script: {sql_file}")
                print(f"2. Run: mysql -u rfid_user -p rfid_inventory < {sql_file}")
                print(f"3. Or run this script with --apply flag")
            
            return True
            
        except Exception as e:
            print(f"\n✗ Error: {e}")
            return False
        finally:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
                print("\n✓ Disconnected from database")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Comprehensive RFID data fix')
    parser.add_argument('--apply', action='store_true', help='Apply fixes to database')
    args = parser.parse_args()
    
    fixer = ComprehensiveDataFix()
    success = fixer.run(apply_fixes=args.apply)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()