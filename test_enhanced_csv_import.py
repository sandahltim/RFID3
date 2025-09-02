#!/usr/bin/env python3
"""
Test script for enhanced financial CSV import service
Tests Excel CSV parsing with actual Scorecard Trends data
"""

import sys
import json
import logging
from pathlib import Path

# Add the project root to Python path
sys.path.append('/home/tim/RFID3')

from app.services.financial_csv_import_service import FinancialCSVImportService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_diagnostic_analysis():
    """Test CSV diagnostic analysis"""
    print("=" * 60)
    print("TESTING CSV DIAGNOSTIC ANALYSIS")
    print("=" * 60)
    
    service = FinancialCSVImportService()
    
    try:
        # Run diagnostic analysis on ScorecardTrends file
        analysis = service.diagnostic_csv_analysis()
        
        print(f"File: {analysis.get('file_path', 'N/A')}")
        print(f"Total Rows: {analysis.get('total_rows', 0)}")
        print(f"Total Columns: {analysis.get('total_columns', 0)}")
        print()
        
        # Show first 10 headers
        headers = analysis.get('headers', [])
        print("Headers (first 10):")
        for i, header in enumerate(headers[:10]):
            print(f"  {i+1:2d}: '{header}'")
        print()
        
        # Show sample data
        sample_data = analysis.get('sample_data', {})
        if sample_data:
            print("Sample Data (first 3 rows, first 5 columns):")
            for row_key, row_data in sample_data.items():
                print(f"  {row_key}:")
                for i, (col, val) in enumerate(list(row_data.items())[:5]):
                    print(f"    '{col}': '{val}'")
                print()
        
        # Store analysis
        store_analysis = analysis.get('store_analysis', {})
        if store_analysis:
            print("Store-Specific Column Analysis:")
            for store, store_data in store_analysis.items():
                print(f"  {store}:")
                print(f"    Columns: {store_data.get('column_count', 0)} found")
                for col in store_data.get('columns', [])[:3]:
                    print(f"      - '{col}'")
                    
                    # Show stats if available
                    for key, value in store_data.items():
                        if key.endswith('_stats'):
                            print(f"        Stats: {value}")
                print()
        
        return analysis
        
    except Exception as e:
        print(f"ERROR in diagnostic analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_enhanced_import():
    """Test enhanced CSV import"""
    print("=" * 60)
    print("TESTING ENHANCED CSV IMPORT")
    print("=" * 60)
    
    service = FinancialCSVImportService()
    
    try:
        # Test scorecard trends import
        result = service.import_scorecard_trends()
        
        print("Import Result:")
        print(f"  Success: {result.get('success', False)}")
        print(f"  File: {result.get('file_path', 'N/A')}")
        print(f"  Total Records: {result.get('total_records', 0)}")
        print(f"  Imported Records: {result.get('imported_records', 0)}")
        print(f"  Columns Imported: {result.get('columns_imported', 0)}")
        
        # Show conversion stats
        conversion_stats = result.get('conversion_stats', {})
        if conversion_stats:
            print("\n  Data Conversion Stats:")
            print(f"    Currency Columns: {len(conversion_stats.get('currency_columns', []))}")
            for col in conversion_stats.get('currency_columns', [])[:5]:
                print(f"      - {col}")
                
            print(f"    Percentage Columns: {len(conversion_stats.get('percentage_columns', []))}")
            for col in conversion_stats.get('percentage_columns', []):
                print(f"      - {col}")
                
            print(f"    Numeric Columns: {len(conversion_stats.get('numeric_columns', []))}")
            for col in conversion_stats.get('numeric_columns', [])[:5]:
                print(f"      - {col}")
        
        # Show parsing issues
        parsing_issues = result.get('parsing_issues', 0)
        if parsing_issues > 0:
            print(f"\n  Parsing Issues: {parsing_issues}")
        
        # Show any errors
        if not result.get('success'):
            print(f"  Error: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"ERROR in enhanced import: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_data_verification():
    """Test data verification"""
    print("=" * 60)
    print("TESTING DATA VERIFICATION")
    print("=" * 60)
    
    service = FinancialCSVImportService()
    
    try:
        verification = service.verify_import()
        
        for table_name, table_data in verification.items():
            print(f"Table: {table_name}")
            
            if table_data.get('exists', False):
                print(f"  Records: {table_data.get('record_count', 0)}")
                
                # Show store data check for scorecard trends
                store_check = table_data.get('store_data_check')
                if store_check:
                    print("  Store Revenue Data:")
                    print(f"    Total Rows: {store_check.get('total_rows', 0)}")
                    print(f"    Store 3607 Data: {store_check.get('store_3607_data', 0)}")
                    print(f"    Store 6800 Data: {store_check.get('store_6800_data', 0)}")
                    print(f"    Store 728 Data: {store_check.get('store_728_data', 0)}")
                    print(f"    Store 8101 Data: {store_check.get('store_8101_data', 0)}")
                
                # Show sample records
                samples = table_data.get('sample_records', [])
                if samples:
                    print("  Sample Records:")
                    for i, sample in enumerate(samples[:2]):  # First 2 samples
                        print(f"    Record {i+1}:")
                        for key, value in list(sample.items())[:5]:  # First 5 fields
                            print(f"      {key}: {value}")
                        print()
            else:
                print(f"  ERROR: {table_data.get('error', 'Table does not exist')}")
            print()
        
        return verification
        
    except Exception as e:
        print(f"ERROR in data verification: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_currency_parser():
    """Test currency parsing functionality"""
    print("=" * 60)
    print("TESTING CURRENCY PARSING")
    print("=" * 60)
    
    service = FinancialCSVImportService()
    
    test_values = [
        '" $118,244 "',  # Quoted with spaces
        '$16,707',       # Standard currency
        '$-',            # Empty/dash
        '$ -',           # Spaced dash
        '',              # Empty string
        'NULL',          # NULL string
        '10%',           # Percentage
        '128',           # Plain number
        '(1,500)',       # Negative in parentheses
        'nan'            # NaN string
    ]
    
    print("Currency Parser Tests:")
    for test_val in test_values:
        result = service.aggressive_currency_cleaner(test_val)
        print(f"  '{test_val}' -> {result}")
    
    print("\nPercentage Parser Tests:")
    percentage_tests = ['10%', '25%', '0%', '', 'NULL', '48%']
    for test_val in percentage_tests:
        result = service.aggressive_percentage_cleaner(test_val)
        print(f"  '{test_val}' -> {result}")
    
    print("\nNumeric Parser Tests:")
    numeric_tests = ['128', '1,500', '', 'NULL', '0']
    for test_val in numeric_tests:
        result = service.aggressive_numeric_cleaner(test_val)
        print(f"  '{test_val}' -> {result}")

def main():
    """Main test function"""
    print("Enhanced Financial CSV Import Service Test Suite")
    print("=" * 60)
    
    # Test 1: Currency parsing
    test_currency_parser()
    print()
    
    # Test 2: Diagnostic analysis
    diagnostic_result = test_diagnostic_analysis()
    print()
    
    # Test 3: Enhanced import
    import_result = test_enhanced_import()
    print()
    
    # Test 4: Data verification
    verification_result = test_data_verification()
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if diagnostic_result:
        print("✓ Diagnostic analysis: PASSED")
    else:
        print("✗ Diagnostic analysis: FAILED")
    
    if import_result and import_result.get('success'):
        print("✓ Enhanced import: PASSED")
    else:
        print("✗ Enhanced import: FAILED")
    
    if verification_result:
        print("✓ Data verification: PASSED")
    else:
        print("✗ Data verification: FAILED")

if __name__ == "__main__":
    main()
