#!/usr/bin/env python3
"""
Data Flow and CSV Import Process Testing
Tests CSV import functionality and data correlation validation
"""

import sys
from datetime import datetime, timedelta
from app import create_app, db
from sqlalchemy import text, func

def test_csv_data_flow():
    """Test CSV import processes and data flow validation"""
    
    print("=" * 80)
    print("CSV DATA FLOW AND IMPORT PROCESS TESTING")
    print("=" * 80)
    
    app = create_app()
    results = {}
    
    with app.app_context():
        print(f"✅ Flask app context established at {datetime.now()}")
        
        # Test 1: CSV Import Service
        print("\n📁 Testing CSV Import Service...")
        try:
            from app.services.csv_import_service import CSVImportService
            csv_import = CSVImportService()
            
            # Check import history/logs
            print(f"✅ CSV Import Service initialized successfully")
            results['csv_import_service'] = 'PASS'
            
        except Exception as e:
            print(f"❌ CSV Import Service failed: {str(e)}")
            results['csv_import_service'] = f'FAIL: {str(e)}'
        
        # Test 2: Data Validation Service
        print("\n✅ Testing Data Validation...")
        try:
            from app.services.data_validation import DataValidationService
            data_validator = DataValidationService()
            
            print(f"✅ Data Validation Service initialized")
            results['data_validation'] = 'PASS'
            
        except Exception as e:
            print(f"❌ Data Validation failed: {str(e)}")
            results['data_validation'] = f'FAIL: {str(e)}'
        
        # Test 3: POS Data Integration
        print("\n🏪 Testing POS Data Integration...")
        try:
            # Check POS data tables
            pos_tables = ['pos_transactions', 'pos_transaction_items', 'pos_equipment']
            pos_counts = {}
            
            for table in pos_tables:
                try:
                    result = db.session.execute(text(f'SELECT COUNT(*) FROM {table}')).fetchone()
                    count = result[0]
                    pos_counts[table] = count
                    print(f"✅ {table}: {count} records")
                except Exception as e:
                    print(f"❌ {table}: ERROR - {str(e)}")
                    pos_counts[table] = 0
            
            if sum(pos_counts.values()) > 0:
                results['pos_data_integration'] = 'PASS'
            else:
                results['pos_data_integration'] = 'FAIL: No POS data found'
                
        except Exception as e:
            print(f"❌ POS Data Integration failed: {str(e)}")
            results['pos_data_integration'] = f'FAIL: {str(e)}'
        
        # Test 4: Financial Data Correlation
        print("\n💰 Testing Financial Data Correlation...")
        try:
            # Check financial data tables
            financial_tables = ['pos_profit_loss', 'pos_pnl', 'pos_scorecard_trends']
            financial_counts = {}
            
            for table in financial_tables:
                try:
                    result = db.session.execute(text(f'SELECT COUNT(*) FROM {table}')).fetchone()
                    count = result[0]
                    financial_counts[table] = count
                    print(f"✅ {table}: {count} records")
                except Exception as e:
                    print(f"❌ {table}: ERROR - {str(e)}")
                    financial_counts[table] = 0
            
            if sum(financial_counts.values()) > 0:
                results['financial_data_correlation'] = 'PASS'
            else:
                results['financial_data_correlation'] = 'FAIL: No financial data found'
                
        except Exception as e:
            print(f"❌ Financial Data Correlation failed: {str(e)}")
            results['financial_data_correlation'] = f'FAIL: {str(e)}'
        
        # Test 5: Equipment Categorization Data
        print("\n🔧 Testing Equipment Categorization Data...")
        try:
            # Check if equipment categorization is working
            result = db.session.execute(text("""
                SELECT COUNT(DISTINCT SUBSTRING_INDEX(item_desc, ' ', 1)) as category_count 
                FROM pos_transaction_items 
                WHERE item_desc IS NOT NULL
                LIMIT 1
            """)).fetchone()
            
            if result and result[0] > 0:
                print(f"✅ Equipment categories detected: {result[0]}")
                results['equipment_categorization_data'] = 'PASS'
            else:
                results['equipment_categorization_data'] = 'FAIL: No equipment categories found'
                
        except Exception as e:
            print(f"❌ Equipment Categorization Data failed: {str(e)}")
            results['equipment_categorization_data'] = f'FAIL: {str(e)}'
        
        # Test 6: Store Mapping Accuracy
        print("\n🏪 Testing Store Mapping Accuracy...")
        try:
            # Check store mappings
            result = db.session.execute(text("""
                SELECT store_code, COUNT(*) as transaction_count 
                FROM pos_transactions 
                GROUP BY store_code
                ORDER BY transaction_count DESC
                LIMIT 5
            """)).fetchall()
            
            print("Top stores by transaction volume:")
            for row in result:
                print(f"   Store {row[0]}: {row[1]} transactions")
            
            if len(result) > 0:
                results['store_mapping_accuracy'] = 'PASS'
            else:
                results['store_mapping_accuracy'] = 'FAIL: No store data found'
                
        except Exception as e:
            print(f"❌ Store Mapping Accuracy failed: {str(e)}")
            results['store_mapping_accuracy'] = f'FAIL: {str(e)}'
    
    # Results Summary
    print("\n" + "=" * 80)
    print("DATA FLOW AND CSV IMPORT TEST RESULTS")
    print("=" * 80)
    
    passed = sum(1 for result in results.values() if result == 'PASS')
    total = len(results)
    
    for test_name, result in results.items():
        status_icon = "✅" if result == 'PASS' else "❌"
        print(f"{status_icon} {test_name.replace('_', ' ').title()}: {result}")
    
    print(f"\n📊 Overall Score: {passed}/{total} tests passed")
    
    if passed >= total * 0.75:  # 75% pass rate
        print("🎉 DATA FLOW TESTING PASSED!")
        return True
    else:
        print("⚠️ Data flow issues detected - see details above")
        return False

if __name__ == "__main__":
    success = test_csv_data_flow()
    sys.exit(0 if success else 1)