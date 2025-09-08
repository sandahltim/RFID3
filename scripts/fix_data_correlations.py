#!/usr/bin/env python3
"""
RFID Data Correlation Fix Script
Purpose: Fix incorrect RFID store assignments and identifier classifications
Date: 2025-08-30
"""

import mysql.connector
from mysql.connector import Error
import json
from datetime import datetime
from tabulate import tabulate
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG

class RFIDDataCorrelationFixer:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.stats = {
            'before': {},
            'after': {},
            'changes': []
        }
        
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.connection.cursor(dictionary=True)
            print("✓ Connected to database")
            return True
        except Error as e:
            print(f"✗ Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✓ Disconnected from database")
    
    def analyze_current_state(self):
        """Analyze current data issues"""
        print("\n" + "="*80)
        print("PHASE 1: ANALYZING CURRENT DATA ISSUES")
        print("="*80)
        
        # Check RFID distribution by store
        query = """
        SELECT 
            current_store,
            COUNT(*) as total_items,
            SUM(CASE WHEN identifier_type = 'RFID' THEN 1 ELSE 0 END) as rfid_items,
            SUM(CASE WHEN rental_class_num IS NOT NULL AND rental_class_num != '' THEN 1 ELSE 0 END) as has_rental_class
        FROM id_item_master
        GROUP BY current_store
        ORDER BY current_store
        """
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        
        print("\nCurrent RFID Distribution by Store:")
        headers = ["Store", "Total Items", "RFID Items", "Has Rental Class"]
        rows = [[r['current_store'], r['total_items'], r['rfid_items'], r['has_rental_class']] for r in results]
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        
        self.stats['before']['rfid_by_store'] = results
        
        # Check tag patterns
        query = """
        SELECT 
            CASE 
                WHEN tag_id LIKE '%-1' THEN 'Ends with -1 (Bulk Store 1)'
                WHEN tag_id LIKE '%-2' THEN 'Ends with -2 (Bulk Store 2)'
                WHEN tag_id LIKE '%-3' THEN 'Ends with -3 (Bulk Store 3)'
                WHEN tag_id LIKE '%-4' THEN 'Ends with -4 (Bulk Store 4)'
                WHEN tag_id LIKE '%#%' THEN 'Contains # (Sticker/Serialized)'
                ELSE 'Other Pattern'
            END as pattern,
            COUNT(*) as count
        FROM id_item_master
        WHERE tag_id IS NOT NULL
        GROUP BY pattern
        """
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        
        print("\nTag Pattern Distribution:")
        headers = ["Pattern", "Count"]
        rows = [[r['pattern'], r['count']] for r in results]
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        
        self.stats['before']['tag_patterns'] = results
        
        # Identify problematic RFID assignments
        query = """
        SELECT 
            current_store,
            COUNT(*) as incorrect_rfid_count
        FROM id_item_master
        WHERE identifier_type = 'RFID'
            AND current_store NOT IN ('8101', NULL)
        GROUP BY current_store
        """
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        
        if results:
            print("\n⚠️  INCORRECT RFID ASSIGNMENTS FOUND:")
            for r in results:
                print(f"   Store {r['current_store']}: {r['incorrect_rfid_count']} items incorrectly marked as RFID")
    
    def backup_tables(self):
        """Create backup tables before making changes"""
        print("\n" + "="*80)
        print("PHASE 2: CREATING BACKUP TABLES")
        print("="*80)
        
        backup_date = datetime.now().strftime('%Y%m%d_%H%M%S')
        tables_to_backup = ['id_item_master', 'store_correlations', 'pos_equipment']
        
        for table in tables_to_backup:
            backup_table = f"{table}_backup_{backup_date}"
            
            # Check if backup already exists
            self.cursor.execute(f"SHOW TABLES LIKE '{backup_table}'")
            if self.cursor.fetchone():
                print(f"   Backup {backup_table} already exists, skipping...")
                continue
            
            # Create backup
            query = f"CREATE TABLE {backup_table} AS SELECT * FROM {table}"
            try:
                self.cursor.execute(query)
                self.connection.commit()
                
                # Get row count
                self.cursor.execute(f"SELECT COUNT(*) as count FROM {backup_table}")
                count = self.cursor.fetchone()['count']
                print(f"✓ Backed up {table} → {backup_table} ({count:,} rows)")
            except Error as e:
                print(f"✗ Failed to backup {table}: {e}")
                return False
        
        return True
    
    def fix_store_correlations(self):
        """Fix the store correlation mappings"""
        print("\n" + "="*80)
        print("PHASE 3: FIXING STORE CORRELATIONS")
        print("="*80)
        
        # Deactivate all current correlations
        self.cursor.execute("UPDATE store_correlations SET is_active = 0")
        
        # Insert correct mappings
        correlations = [
            ('8101', '4', 'Fridley (RFID Test)', 'Fridley, MN'),
            ('3607', '1', 'Wayzata (POS Only)', 'Wayzata, MN'),
            ('6800', '2', 'Brooklyn Park (POS Only)', 'Brooklyn Park, MN'),
            ('728', '3', 'Elk River (POS Only)', 'Elk River, MN'),
            ('000', '0', 'Header/Noise Data', 'System Generated')
        ]
        
        for rfid_code, pos_code, name, location in correlations:
            query = """
            INSERT INTO store_correlations (rfid_store_code, pos_store_code, store_name, store_location, is_active)
            VALUES (%s, %s, %s, %s, 1)
            ON DUPLICATE KEY UPDATE
                store_name = VALUES(store_name),
                store_location = VALUES(store_location),
                is_active = VALUES(is_active)
            """
            self.cursor.execute(query, (rfid_code, pos_code, name, location))
            print(f"✓ Updated: {rfid_code} → {pos_code} ({name})")
        
        self.connection.commit()
        self.stats['changes'].append("Store correlations updated")
    
    def fix_identifier_classifications(self):
        """Fix identifier type classifications based on tag patterns"""
        print("\n" + "="*80)
        print("PHASE 4: FIXING IDENTIFIER CLASSIFICATIONS")
        print("="*80)
        
        # First, preserve legitimate RFID items from NULL store
        query = """
        CREATE TEMPORARY TABLE IF NOT EXISTS temp_legitimate_rfid AS
        SELECT tag_id
        FROM id_item_master
        WHERE current_store IS NULL 
            AND rental_class_num IS NOT NULL 
            AND rental_class_num != ''
            AND identifier_type = 'RFID'
        """
        self.cursor.execute(query)
        self.cursor.execute("SELECT COUNT(*) as count FROM temp_legitimate_rfid")
        rfid_from_null = self.cursor.fetchone()['count']
        print(f"   Found {rfid_from_null} legitimate RFID items in NULL store")
        
        # Reset all identifier types to None
        print("   Resetting all identifier types...")
        self.cursor.execute("UPDATE id_item_master SET identifier_type = 'None'")
        
        # Mark Bulk items
        query = """
        UPDATE id_item_master 
        SET identifier_type = 'Bulk'
        WHERE (tag_id LIKE '%-1' OR tag_id LIKE '%-2' OR tag_id LIKE '%-3' OR tag_id LIKE '%-4')
            AND tag_id IS NOT NULL
        """
        self.cursor.execute(query)
        bulk_count = self.cursor.rowcount
        print(f"✓ Marked {bulk_count:,} items as 'Bulk'")
        
        # Mark Sticker items
        query = """
        UPDATE id_item_master 
        SET identifier_type = 'Sticker'
        WHERE tag_id LIKE '%#%' AND tag_id IS NOT NULL
        """
        self.cursor.execute(query)
        sticker_count = self.cursor.rowcount
        print(f"✓ Marked {sticker_count:,} items as 'Sticker'")
        
        # Mark legitimate RFID items in Fridley
        query = """
        UPDATE id_item_master 
        SET identifier_type = 'RFID'
        WHERE current_store = '8101'
            AND rental_class_num IS NOT NULL 
            AND rental_class_num != ''
            AND tag_id NOT LIKE '%-1' 
            AND tag_id NOT LIKE '%-2'
            AND tag_id NOT LIKE '%-3'
            AND tag_id NOT LIKE '%-4'
            AND tag_id NOT LIKE '%#%'
        """
        self.cursor.execute(query)
        fridley_rfid = self.cursor.rowcount
        print(f"✓ Marked {fridley_rfid:,} Fridley items as 'RFID'")
        
        # Reassign legitimate RFID from NULL store to Fridley
        query = """
        UPDATE id_item_master 
        SET identifier_type = 'RFID',
            current_store = '8101'
        WHERE tag_id IN (SELECT tag_id FROM temp_legitimate_rfid)
        """
        self.cursor.execute(query)
        reassigned = self.cursor.rowcount
        print(f"✓ Reassigned {reassigned:,} RFID items from NULL store to Fridley")
        
        # Mark store 000 items
        query = """
        UPDATE id_item_master 
        SET notes = CONCAT(IFNULL(notes, ''), ' [Header/Noise Data]')
        WHERE current_store = '000'
        """
        self.cursor.execute(query)
        store_000 = self.cursor.rowcount
        print(f"✓ Marked {store_000:,} items in store 000 as header/noise data")
        
        self.connection.commit()
        self.stats['changes'].extend([
            f"Bulk items classified: {bulk_count}",
            f"Sticker items classified: {sticker_count}",
            f"RFID items in Fridley: {fridley_rfid}",
            f"RFID items reassigned from NULL: {reassigned}"
        ])
    
    def update_pos_equipment(self):
        """Update POS equipment table to match corrections"""
        print("\n" + "="*80)
        print("PHASE 5: UPDATING POS_EQUIPMENT TABLE")
        print("="*80)
        
        # Clear all RFID rental class assignments
        self.cursor.execute("UPDATE pos_equipment SET rfid_rental_class_num = NULL")
        cleared = self.cursor.rowcount
        print(f"   Cleared {cleared:,} RFID rental class assignments")
        
        # Only assign RFID rental classes for true Fridley RFID items
        query = """
        UPDATE pos_equipment pe
        INNER JOIN id_item_master im ON pe.key_field = im.tag_id
        SET pe.rfid_rental_class_num = im.rental_class_num
        WHERE im.identifier_type = 'RFID'
            AND im.current_store = '8101'
            AND im.rental_class_num IS NOT NULL
        """
        self.cursor.execute(query)
        updated = self.cursor.rowcount
        print(f"✓ Updated {updated:,} POS equipment records with RFID rental classes")
        
        self.connection.commit()
        self.stats['changes'].append(f"POS equipment RFID assignments updated: {updated}")
    
    def verify_corrections(self):
        """Verify that corrections were applied successfully"""
        print("\n" + "="*80)
        print("PHASE 6: VERIFYING CORRECTIONS")
        print("="*80)
        
        # Check final RFID distribution
        query = """
        SELECT 
            current_store,
            COUNT(*) as total_items,
            SUM(CASE WHEN identifier_type = 'RFID' THEN 1 ELSE 0 END) as rfid_items,
            SUM(CASE WHEN identifier_type = 'Bulk' THEN 1 ELSE 0 END) as bulk_items,
            SUM(CASE WHEN identifier_type = 'Sticker' THEN 1 ELSE 0 END) as sticker_items,
            SUM(CASE WHEN identifier_type = 'None' THEN 1 ELSE 0 END) as none_items
        FROM id_item_master
        GROUP BY current_store
        ORDER BY current_store
        """
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        
        print("\nFinal Item Distribution by Store:")
        headers = ["Store", "Total", "RFID", "Bulk", "Sticker", "None"]
        rows = [[r['current_store'], r['total_items'], r['rfid_items'], 
                r['bulk_items'], r['sticker_items'], r['none_items']] for r in results]
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        
        self.stats['after']['distribution'] = results
        
        # Verify only Fridley has RFID
        query = """
        SELECT current_store, COUNT(*) as rfid_count
        FROM id_item_master
        WHERE identifier_type = 'RFID'
        GROUP BY current_store
        """
        self.cursor.execute(query)
        rfid_stores = self.cursor.fetchall()
        
        print("\nStores with RFID Items:")
        if rfid_stores:
            for store in rfid_stores:
                status = "✓ CORRECT" if store['current_store'] == '8101' else "✗ ERROR"
                print(f"   Store {store['current_store']}: {store['rfid_count']} items {status}")
        else:
            print("   No RFID items found (check if this is expected)")
        
        # Check identifier type totals
        query = """
        SELECT identifier_type, COUNT(*) as count
        FROM id_item_master
        GROUP BY identifier_type
        ORDER BY count DESC
        """
        self.cursor.execute(query)
        results = self.cursor.fetchall()
        
        print("\nIdentifier Type Summary:")
        headers = ["Type", "Count"]
        rows = [[r['identifier_type'], r['count']] for r in results]
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    
    def generate_report(self):
        """Generate final report"""
        print("\n" + "="*80)
        print("CORRECTION SUMMARY REPORT")
        print("="*80)
        
        print("\nChanges Applied:")
        for change in self.stats['changes']:
            print(f"   • {change}")
        
        print("\nKey Outcomes:")
        print("   ✓ RFID items now correctly limited to Fridley (Store 8101)")
        print("   ✓ Other stores marked as POS-only")
        print("   ✓ Identifier types classified based on tag patterns")
        print("   ✓ Store 000 marked as header/noise data")
        print("   ✓ Legitimate RFID data preserved and reassigned")
        
        # Save report to file
        report_file = f"/home/tim/RFID3/logs/data_correlation_fix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(self.stats, f, indent=2, default=str)
        print(f"\n✓ Detailed report saved to: {report_file}")
    
    def run(self, dry_run=False):
        """Execute the complete fix process"""
        print("\n" + "="*80)
        print("RFID DATA CORRELATION FIX SCRIPT")
        print(f"Mode: {'DRY RUN' if dry_run else 'LIVE EXECUTION'}")
        print("="*80)
        
        if not self.connect():
            return False
        
        try:
            # Analyze current state
            self.analyze_current_state()
            
            if dry_run:
                print("\n⚠️  DRY RUN MODE - No changes will be made")
                print("Run with --execute flag to apply fixes")
                return True
            
            # Confirm before proceeding
            print("\n⚠️  WARNING: This will modify the database!")
            response = input("Do you want to proceed? (yes/no): ").strip().lower()
            if response != 'yes':
                print("Operation cancelled")
                return False
            
            # Execute fixes
            if not self.backup_tables():
                print("✗ Backup failed, aborting")
                return False
            
            self.fix_store_correlations()
            self.fix_identifier_classifications()
            self.update_pos_equipment()
            self.verify_corrections()
            self.generate_report()
            
            print("\n✓ DATA CORRELATION FIX COMPLETED SUCCESSFULLY")
            return True
            
        except Error as e:
            print(f"\n✗ Error during execution: {e}")
            if not dry_run:
                print("Rolling back changes...")
                self.connection.rollback()
            return False
        finally:
            self.disconnect()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix RFID data correlations')
    parser.add_argument('--execute', action='store_true', help='Execute fixes (without this flag, runs in dry-run mode)')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')
    args = parser.parse_args()
    
    fixer = RFIDDataCorrelationFixer()
    success = fixer.run(dry_run=not args.execute)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()