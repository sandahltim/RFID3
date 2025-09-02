#!/usr/bin/env python3
"""
Test P&L Import Service with Centralized Store Configuration
This script tests the updated P&L import service to ensure proper correlation
"""

import sys
import os
import json
from datetime import datetime
import traceback

# Add the app directory to Python path
sys.path.append('/home/tim/RFID3')
sys.path.append('/home/tim/RFID3/app')

from app.services.pnl_import_service import PnLImportService
from app.config.stores import STORES, get_store_name, get_all_store_codes

def test_centralized_store_config():
    """Test that centralized store configuration is working"""
    print("=" * 60)
    print("TESTING CENTRALIZED STORE CONFIGURATION")
    print("=" * 60)
    
    # Test store mappings
    print("Available stores from centralized config:")
    for store_code in get_all_store_codes():
        store_info = STORES[store_code]
        print(f"  {store_code}: {store_info.name} ({store_info.location}) - POS: {store_info.pos_code}")
    
    print("\nStore name lookups:")
    test_codes = ['3607', '6800', '728', '8101', '000']
    for code in test_codes:
        name = get_store_name(code)
        print(f"  {code} -> {name}")

def test_pnl_import_service():
    """Test the P&L import service initialization"""
    print("\n" + "=" * 60)
    print("TESTING P&L IMPORT SERVICE")
    print("=" * 60)
    
    try:
        # Initialize service
        service = PnLImportService()
        print(f"✓ P&L Import Service initialized successfully")
        print(f"✓ Store mappings loaded: {service.store_mappings}")
        print(f"✓ Metric types supported: {len(service.metric_types)}")
        
        # Test CSV structure analysis
        csv_path = "/home/tim/RFID3/shared/POR/PL8.28.25.csv"
        if os.path.exists(csv_path):
            print(f"\n✓ Found P&L CSV file: {csv_path}")
            structure = service.analyze_csv_structure(csv_path)
            if 'error' not in structure:
                print(f"✓ CSV structure analysis successful")
                print(f"  - Total columns: {structure.get('total_columns', 0)}")
                print(f"  - Store columns found: {structure.get('store_columns', [])}")
                
                # Test data extraction (limited)
                print(f"\n✓ Testing data extraction (limited to 5 records)...")
                records = service.extract_financial_data_from_csv(csv_path)
                if records:
                    print(f"✓ Extracted {len(records)} records from CSV")
                    print("Sample records:")
                    for i, record in enumerate(records[:5]):
                        print(f"  {i+1}. {record['store_code']} ({record['store_name']}) - "
                              f"{record['month_year']} - {record['metric_type']}: ${record['actual_amount']}")
                else:
                    print("⚠ No records extracted from CSV")
            else:
                print(f"✗ CSV structure analysis failed: {structure['error']}")
        else:
            print(f"⚠ P&L CSV file not found: {csv_path}")
        
        # Test store correlation validation
        print(f"\n✓ Testing store correlation validation...")
        correlation_result = service.validate_store_correlations()
        if correlation_result['success']:
            report = correlation_result['correlation_report']
            print(f"✓ Correlation validation successful")
            print(f"  - P&L stores: {report['pnl_stores']}")
            print(f"  - Centralized stores: {report['centralized_stores']}")
            print(f"  - Correlation percentage: {report['correlation_percentage']:.1f}%")
        else:
            print(f"✗ Correlation validation failed: {correlation_result['error']}")
            
    except Exception as e:
        print(f"✗ P&L Import Service test failed: {e}")
        traceback.print_exc()

def test_database_schema_alignment():
    """Test database schema alignment"""
    print("\n" + "=" * 60)
    print("TESTING DATABASE SCHEMA ALIGNMENT")
    print("=" * 60)
    
    try:
        service = PnLImportService()
        
        # Test database connection
        session = service.Session()
        try:
            # Test pos_store_mapping table
            from sqlalchemy import text
            result = session.execute(text("SELECT store_code, store_name, active FROM pos_store_mapping ORDER BY store_code"))
            mapping_data = result.fetchall()
            
            print(f"✓ Database connection successful")
            print(f"✓ pos_store_mapping table contains {len(mapping_data)} records:")
            for row in mapping_data:
                active_status = "ACTIVE" if row[2] else "INACTIVE"
                print(f"  {row[0]}: {row[1]} ({active_status})")
            
            # Test pos_pnl table structure
            pnl_result = session.execute(text("SELECT COUNT(*) as total_records, COUNT(DISTINCT store_code) as unique_stores FROM pos_pnl"))
            pnl_stats = pnl_result.fetchone()
            print(f"✓ pos_pnl table contains {pnl_stats[0]} records across {pnl_stats[1]} stores")
            
        finally:
            session.close()
            
    except Exception as e:
        print(f"✗ Database schema test failed: {e}")
        traceback.print_exc()

def main():
    """Run all P&L import correlation tests"""
    print("P&L IMPORT SERVICE CORRELATION FIX VALIDATION")
    print("=" * 80)
    print(f"Test started at: {datetime.now()}")
    
    # Run all tests
    test_centralized_store_config()
    test_pnl_import_service()
    test_database_schema_alignment()
    
    print("\n" + "=" * 80)
    print("TESTS COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    main()
