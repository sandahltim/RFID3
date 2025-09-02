#!/usr/bin/env python3
"""
Final Test of P&L Import Service with Centralized Store Configuration
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

def test_pnl_data_extraction():
    """Test P&L data extraction with actual CSV"""
    print("=" * 60)
    print("TESTING P&L DATA EXTRACTION")
    print("=" * 60)
    
    try:
        service = PnLImportService()
        csv_path = "/home/tim/RFID3/shared/POR/PL8.28.25.csv"
        
        if os.path.exists(csv_path):
            print(f"✓ Found P&L CSV: {csv_path}")
            
            # Test data extraction (limited)
            records = service.extract_financial_data_from_csv(csv_path)
            print(f"✓ Extracted {len(records)} records")
            
            if records:
                # Show sample records
                print("\nSample records:")
                for i, record in enumerate(records[:10]):
                    print(f"  {i+1}. {record['store_code']} ({record['store_name']}) - "
                          f"{record['month_year']} - {record['metric_type']}: ${record['actual_amount']}")
                
                # Test actual import (limited to 50 records)
                print(f"\n✓ Testing import (limited to 50 records)...")
                result = service.import_pnl_csv_data(csv_path, limit=50)
                
                if result['success']:
                    print(f"✓ Import successful: {result['records_imported']} records imported")
                    print(f"  Duplicates: {result['duplicates_skipped']}")
                    print(f"  Errors: {result['errors']}")
                    if 'summary_stats' in result:
                        stats = result['summary_stats']
                        print(f"  Summary: {stats.get('total_records', 0)} total records")
                else:
                    print(f"✗ Import failed: {result['error']}")
                    
            else:
                print("⚠ No records extracted")
                
        else:
            print(f"⚠ CSV file not found: {csv_path}")
            
    except Exception as e:
        print(f"✗ Data extraction test failed: {e}")
        traceback.print_exc()

def test_analytics_query():
    """Test P&L analytics query"""
    print("\n" + "=" * 60)
    print("TESTING P&L ANALYTICS QUERY")
    print("=" * 60)
    
    try:
        service = PnLImportService()
        
        # Test analytics query
        analytics = service.get_pnl_analytics()
        
        if analytics['success']:
            print(f"✓ Analytics query successful: {analytics['record_count']} records")
            print(f"✓ Available stores: {list(analytics['stores'].keys())}")
            
            # Show sample analytics data
            if analytics['data']:
                print("\nSample analytics data:")
                for i, data in enumerate(analytics['data'][:5]):
                    print(f"  {i+1}. {data['store_name']} - {data['month_year']} - "
                          f"{data['metric_type']}: ${data['actual_amount']}")
        else:
            print(f"✗ Analytics query failed: {analytics['error']}")
            
    except Exception as e:
        print(f"✗ Analytics test failed: {e}")
        traceback.print_exc()

def test_store_correlation():
    """Test store correlation validation"""
    print("\n" + "=" * 60)
    print("TESTING STORE CORRELATION VALIDATION")
    print("=" * 60)
    
    try:
        service = PnLImportService()
        
        # Test correlation validation
        correlation = service.validate_store_correlations()
        
        if correlation['success']:
            report = correlation['correlation_report']
            print(f"✓ Store correlation validation successful")
            print(f"  P&L stores: {report['pnl_stores']}")
            print(f"  Centralized stores: {report['centralized_stores']}")
            print(f"  Correlation: {report['correlation_percentage']:.1f}%")
            print(f"  Missing in P&L: {report['missing_in_pnl']}")
            print(f"  Missing in config: {report['missing_in_config']}")
        else:
            print(f"✗ Correlation validation failed: {correlation['error']}")
            
    except Exception as e:
        print(f"✗ Correlation test failed: {e}")
        traceback.print_exc()

def main():
    """Run complete P&L import validation"""
    print("P&L IMPORT SERVICE FINAL VALIDATION")
    print("=" * 80)
    print(f"Test started at: {datetime.now()}")
    
    test_pnl_data_extraction()
    test_analytics_query()
    test_store_correlation()
    
    print("\n" + "=" * 80)
    print("FINAL VALIDATION COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    main()
