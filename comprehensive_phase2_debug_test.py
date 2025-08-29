#!/usr/bin/env python3
"""
RFID3 Phase 2 Comprehensive Debug Analysis
==========================================

This script performs a comprehensive verification of Phase 2 completion status
by testing all claimed functionality against actual implementation.
"""

import sys
import os
import json
import requests
import mysql.connector
from datetime import datetime
import traceback

# Add the app directory to Python path
sys.path.insert(0, '/home/tim/RFID3')

class Phase2DebugAnalyzer:
    def __init__(self):
        self.results = {}
        self.db_config = {
            'host': 'localhost',
            'user': 'rfid_user',
            'password': 'rfid_user_password',
            'database': 'rfid_inventory'
        }
        self.base_url = 'http://localhost:6801'
        
    def test_database_connectivity(self):
        """Test database connection and basic functionality"""
        print("\n" + "="*60)
        print("1. DATABASE CONNECTIVITY TEST")
        print("="*60)
        
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            conn.close()
            
            status = "PASS" if result[0] == 1 else "FAIL"
            print(f"✅ Database Connection: {status}")
            self.results['database_connection'] = status
            return True
            
        except Exception as e:
            print(f"❌ Database Connection: FAIL - {e}")
            self.results['database_connection'] = f"FAIL - {e}"
            return False
    
    def test_table_record_counts(self):
        """Test actual record counts in all Phase 2 tables"""
        print("\n" + "="*60)
        print("2. TABLE RECORD COUNTS VERIFICATION")
        print("="*60)
        
        expected_tables = {
            'pos_equipment': {'expected': 25000, 'description': 'POS Equipment data'},
            'pos_customers': {'expected': 0, 'description': 'POS Customer data (failed import)'},
            'pos_transactions': {'expected': 0, 'description': 'POS Transaction data (failed import)'},
            'pos_transaction_items': {'expected': 0, 'description': 'POS Transaction items'},
            'pos_pnl': {'expected': 180, 'description': 'P&L data'},
            'id_item_master': {'expected': 65942, 'description': 'RFID Item master'},
            'id_transactions': {'expected': 26574, 'description': 'RFID Transactions'},
            'executive_kpi': {'expected': 6, 'description': 'Executive KPIs'},
            'executive_payroll_trends': {'expected': 328, 'description': 'Payroll trends'},
            'executive_scorecard_trends': {'expected': 0, 'description': 'Scorecard trends'},
            'resale_analytics': {'expected': 1000, 'description': 'Resale analytics'},
        }
        
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            table_results = {}
            for table, info in expected_tables.items():
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    actual_count = cursor.fetchone()[0]
                    expected_count = info['expected']
                    
                    if actual_count == expected_count:
                        status = "✅ PASS"
                    elif actual_count > 0:
                        status = f"⚠️  PARTIAL ({actual_count} records)"
                    else:
                        status = "❌ EMPTY"
                    
                    print(f"{status} {table}: {actual_count:,} records ({info['description']})")
                    table_results[table] = {
                        'actual': actual_count,
                        'expected': expected_count,
                        'status': status
                    }
                    
                except Exception as e:
                    print(f"❌ FAIL {table}: Error - {e}")
                    table_results[table] = {'error': str(e)}
            
            conn.close()
            self.results['table_counts'] = table_results
            return True
            
        except Exception as e:
            print(f"❌ Table count verification failed: {e}")
            self.results['table_counts'] = f"FAIL - {e}"
            return False
    
    def test_csv_import_functionality(self):
        """Test CSV import processes"""
        print("\n" + "="*60)
        print("3. CSV IMPORT FUNCTIONALITY TEST")
        print("="*60)
        
        csv_files = [
            'customer8.26.25.csv',
            'transactions8.26.25.csv', 
            'equip8.26.25.csv',
            'PL8.28.25.csv',
            'Payroll Trends.csv',
            'Scorecard Trends.csv'
        ]
        
        import_results = {}
        csv_path = '/home/tim/RFID3/shared/POR/'
        
        for csv_file in csv_files:
            file_path = os.path.join(csv_path, csv_file)
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                status = f"✅ EXISTS ({file_size:,} bytes)"
                import_results[csv_file] = {'exists': True, 'size': file_size}
            else:
                status = "❌ MISSING"
                import_results[csv_file] = {'exists': False}
            
            print(f"{status} {csv_file}")
        
        # Test import script functionality
        try:
            import subprocess
            result = subprocess.run([
                'python3', '/home/tim/RFID3/limited_data_import.py'
            ], capture_output=True, text=True, timeout=30)
            
            if "Equipment import completed" in result.stdout:
                print("✅ PASS Equipment import script working")
                import_results['equipment_import'] = 'WORKING'
            else:
                print("❌ FAIL Equipment import script issues")
                import_results['equipment_import'] = 'FAILED'
            
            if "Customer import failed" in result.stdout:
                print("⚠️  EXPECTED Customer import failing (column mismatch)")
                import_results['customer_import'] = 'EXPECTED_FAILURE'
            
            if "Transaction.*failed" in result.stdout:
                print("❌ FAIL Transaction import failing (schema issue)")
                import_results['transaction_import'] = 'SCHEMA_ISSUE'
                
        except Exception as e:
            print(f"❌ Import script test failed: {e}")
            import_results['script_test'] = f"FAILED - {e}"
        
        self.results['csv_import'] = import_results
        return True
    
    def test_api_endpoints(self):
        """Test API endpoint functionality"""
        print("\n" + "="*60)
        print("4. API ENDPOINTS TEST")
        print("="*60)
        
        endpoints = {
            '/api/inventory/dashboard_summary': 'Inventory dashboard summary',
            '/api/inventory/business_intelligence': 'Business intelligence data',
            '/api/inventory/alerts': 'Health alerts system',
            '/': 'Main web interface',
            '/tab7': 'Executive dashboard',
            '/bi/dashboard': 'BI dashboard'
        }
        
        api_results = {}
        
        for endpoint, description in endpoints.items():
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                
                if response.status_code == 200:
                    if 'application/json' in response.headers.get('content-type', ''):
                        try:
                            data = response.json()
                            status = f"✅ PASS (JSON, {len(str(data))} chars)"
                            api_results[endpoint] = {'status': 'PASS', 'type': 'JSON'}
                        except:
                            status = f"⚠️  PASS (Non-JSON response)"
                            api_results[endpoint] = {'status': 'PASS', 'type': 'HTML'}
                    else:
                        status = f"✅ PASS (HTML)"
                        api_results[endpoint] = {'status': 'PASS', 'type': 'HTML'}
                elif response.status_code == 404:
                    status = f"❌ NOT FOUND"
                    api_results[endpoint] = {'status': 'NOT_FOUND'}
                else:
                    status = f"❌ HTTP {response.status_code}"
                    api_results[endpoint] = {'status': f'HTTP_{response.status_code}'}
                
                print(f"{status} {endpoint} - {description}")
                
            except requests.exceptions.Timeout:
                print(f"⏰ TIMEOUT {endpoint} - {description}")
                api_results[endpoint] = {'status': 'TIMEOUT'}
            except Exception as e:
                print(f"❌ ERROR {endpoint} - {e}")
                api_results[endpoint] = {'status': f'ERROR - {e}'}
        
        self.results['api_endpoints'] = api_results
        return True
    
    def test_business_analytics(self):
        """Test business analytics calculations"""
        print("\n" + "="*60)
        print("5. BUSINESS ANALYTICS TEST")
        print("="*60)
        
        analytics_tests = {}
        
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Test equipment utilization calculation
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN turnover_ytd > 0 THEN 1 ELSE 0 END) as active
                FROM pos_equipment 
                WHERE current_store IS NOT NULL
            """)
            equip_result = cursor.fetchone()
            
            if equip_result[0] > 0:
                utilization = (equip_result[1] / equip_result[0]) * 100
                print(f"✅ PASS Equipment utilization calculation: {utilization:.1f}% ({equip_result[1]:,}/{equip_result[0]:,})")
                analytics_tests['equipment_utilization'] = 'PASS'
            else:
                print(f"❌ FAIL No equipment data for utilization")
                analytics_tests['equipment_utilization'] = 'NO_DATA'
            
            # Test P&L analytics
            cursor.execute("""
                SELECT store_code, metric_type, COUNT(*) as records
                FROM pos_pnl 
                GROUP BY store_code, metric_type
                ORDER BY store_code, metric_type
                LIMIT 10
            """)
            pnl_results = cursor.fetchall()
            
            if pnl_results:
                print(f"✅ PASS P&L analytics data available ({len(pnl_results)} metric groups)")
                analytics_tests['pnl_analytics'] = 'PASS'
                
                for store, metric, count in pnl_results[:5]:
                    print(f"    Store {store}: {metric} ({count} records)")
            else:
                print(f"❌ FAIL No P&L analytics data")
                analytics_tests['pnl_analytics'] = 'NO_DATA'
            
            # Test ROI calculations
            cursor.execute("""
                SELECT AVG(sell_price) as avg_price,
                       AVG(turnover_ytd) as avg_turnover
                FROM pos_equipment 
                WHERE sell_price > 0 AND turnover_ytd > 0
            """)
            roi_result = cursor.fetchone()
            
            if roi_result[0] and roi_result[1]:
                roi_estimate = (roi_result[1] / roi_result[0]) * 100
                print(f"✅ PASS ROI calculation possible: {roi_estimate:.1f}% (avg turnover/price)")
                analytics_tests['roi_calculation'] = 'PASS'
            else:
                print(f"❌ FAIL Insufficient data for ROI calculation")
                analytics_tests['roi_calculation'] = 'INSUFFICIENT_DATA'
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Business analytics test failed: {e}")
            analytics_tests['error'] = str(e)
        
        self.results['business_analytics'] = analytics_tests
        return True
    
    def test_database_schema_integrity(self):
        """Test database schema and relationships"""
        print("\n" + "="*60)
        print("6. DATABASE SCHEMA INTEGRITY TEST")
        print("="*60)
        
        schema_tests = {}
        
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Test for required indexes
            cursor.execute("""
                SELECT table_name, index_name, column_name
                FROM information_schema.statistics
                WHERE table_schema = 'rfid_inventory'
                AND table_name IN ('pos_equipment', 'pos_transactions', 'pos_pnl')
                ORDER BY table_name, index_name
            """)
            indexes = cursor.fetchall()
            
            if indexes:
                print(f"✅ PASS Database indexes present ({len(indexes)} indexes found)")
                schema_tests['indexes'] = 'PASS'
            else:
                print(f"⚠️  WARNING No custom indexes found")
                schema_tests['indexes'] = 'WARNING'
            
            # Test foreign key relationships
            cursor.execute("""
                SELECT table_name, constraint_name, referenced_table_name
                FROM information_schema.key_column_usage
                WHERE table_schema = 'rfid_inventory'
                AND referenced_table_name IS NOT NULL
            """)
            foreign_keys = cursor.fetchall()
            
            if foreign_keys:
                print(f"✅ PASS Foreign key relationships ({len(foreign_keys)} found)")
                schema_tests['foreign_keys'] = 'PASS'
            else:
                print(f"⚠️  WARNING No foreign key relationships found")
                schema_tests['foreign_keys'] = 'WARNING'
            
            # Test for data consistency
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM pos_equipment WHERE current_store IS NOT NULL) as equipment_with_store,
                    (SELECT COUNT(DISTINCT store_code) FROM pos_pnl) as pnl_stores,
                    (SELECT COUNT(DISTINCT current_store) FROM pos_equipment WHERE current_store IS NOT NULL) as equipment_stores
            """)
            consistency = cursor.fetchone()
            
            print(f"✅ INFO Data consistency check:")
            print(f"    Equipment with store assignment: {consistency[0]:,}")
            print(f"    Stores in P&L data: {consistency[1]}")
            print(f"    Stores in equipment data: {consistency[2]}")
            
            schema_tests['data_consistency'] = {
                'equipment_with_store': consistency[0],
                'pnl_stores': consistency[1], 
                'equipment_stores': consistency[2]
            }
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Schema integrity test failed: {e}")
            schema_tests['error'] = str(e)
        
        self.results['schema_integrity'] = schema_tests
        return True
    
    def generate_report(self):
        """Generate comprehensive debug report"""
        print("\n" + "="*60)
        print("PHASE 2 COMPLETION STATUS SUMMARY")
        print("="*60)
        
        print("\n📊 RECORD COUNT VERIFICATION:")
        table_counts = self.results.get('table_counts', {})
        for table, info in table_counts.items():
            if isinstance(info, dict) and 'actual' in info:
                print(f"  {table}: {info['actual']:,} records")
        
        print("\n🔧 CSV IMPORT STATUS:")
        csv_import = self.results.get('csv_import', {})
        if 'equipment_import' in csv_import:
            print(f"  Equipment Import: {csv_import['equipment_import']}")
        if 'customer_import' in csv_import:
            print(f"  Customer Import: {csv_import['customer_import']}")
        if 'transaction_import' in csv_import:
            print(f"  Transaction Import: {csv_import['transaction_import']}")
        
        print("\n🌐 API ENDPOINT STATUS:")
        api_endpoints = self.results.get('api_endpoints', {})
        working_apis = sum(1 for ep in api_endpoints.values() if ep.get('status') == 'PASS')
        total_apis = len(api_endpoints)
        print(f"  Working APIs: {working_apis}/{total_apis}")
        
        print("\n📈 BUSINESS ANALYTICS STATUS:")
        analytics = self.results.get('business_analytics', {})
        working_analytics = sum(1 for test in analytics.values() if test == 'PASS')
        total_analytics = len([k for k in analytics.keys() if k != 'error'])
        print(f"  Working Analytics: {working_analytics}/{total_analytics}")
        
        print("\n" + "="*60)
        print("CRITICAL ISSUES IDENTIFIED:")
        print("="*60)
        
        issues = []
        
        # Check for major data import failures
        if table_counts.get('pos_customers', {}).get('actual', 0) == 0:
            issues.append("❌ CRITICAL: POS Customer data import completely failed")
        
        if table_counts.get('pos_transactions', {}).get('actual', 0) == 0:
            issues.append("❌ CRITICAL: POS Transaction data import completely failed")
        
        if table_counts.get('pos_transaction_items', {}).get('actual', 0) == 0:
            issues.append("❌ CRITICAL: POS Transaction Items data missing")
        
        # Check for API failures
        failed_apis = [ep for ep, info in api_endpoints.items() if info.get('status') not in ['PASS']]
        if failed_apis:
            issues.append(f"❌ API ISSUES: {len(failed_apis)} endpoints not working properly")
        
        # Check for missing analytics
        if analytics.get('pnl_analytics') != 'PASS':
            issues.append("⚠️  WARNING: P&L analytics may have data issues")
        
        if not issues:
            print("✅ No critical issues identified in current scope")
        else:
            for issue in issues:
                print(issue)
        
        print("\n" + "="*60)
        print("PHASE 2 COMPLETION ASSESSMENT:")
        print("="*60)
        
        # Calculate completion percentage
        completed_items = 0
        total_items = 0
        
        # Database connectivity (essential)
        if self.results.get('database_connection') == 'PASS':
            completed_items += 1
        total_items += 1
        
        # Core data import (25K+ equipment records claimed)
        if table_counts.get('pos_equipment', {}).get('actual', 0) >= 25000:
            completed_items += 1
        total_items += 1
        
        # P&L data import
        if table_counts.get('pos_pnl', {}).get('actual', 0) > 0:
            completed_items += 1
        total_items += 1
        
        # Executive dashboard data
        if table_counts.get('executive_kpi', {}).get('actual', 0) > 0:
            completed_items += 1
        total_items += 1
        
        # API endpoints working
        if working_apis >= total_apis * 0.8:  # 80% of APIs working
            completed_items += 1
        total_items += 1
        
        # Business analytics functional
        if working_analytics >= total_analytics * 0.6:  # 60% of analytics working
            completed_items += 1
        total_items += 1
        
        completion_percentage = (completed_items / total_items) * 100
        
        print(f"📊 OVERALL COMPLETION: {completion_percentage:.1f}% ({completed_items}/{total_items})")
        
        if completion_percentage >= 80:
            print("✅ ASSESSMENT: Phase 2 is SUBSTANTIALLY COMPLETE")
        elif completion_percentage >= 60:
            print("⚠️  ASSESSMENT: Phase 2 is PARTIALLY COMPLETE with major gaps")
        else:
            print("❌ ASSESSMENT: Phase 2 has SIGNIFICANT INCOMPLETE ITEMS")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f'/home/tim/RFID3/phase2_debug_report_{timestamp}.json'
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n📄 Detailed report saved: {report_file}")
        
        return completion_percentage, issues

def main():
    """Main execution function"""
    print("RFID3 PHASE 2 COMPREHENSIVE DEBUG ANALYSIS")
    print("=" * 60)
    print(f"Analysis started at: {datetime.now()}")
    
    analyzer = Phase2DebugAnalyzer()
    
    # Run all tests
    tests = [
        analyzer.test_database_connectivity,
        analyzer.test_table_record_counts,
        analyzer.test_csv_import_functionality,
        analyzer.test_api_endpoints,
        analyzer.test_business_analytics,
        analyzer.test_database_schema_integrity
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            traceback.print_exc()
    
    # Generate final report
    completion_percentage, issues = analyzer.generate_report()
    
    print(f"\n🕐 Analysis completed at: {datetime.now()}")
    
    return completion_percentage >= 60  # Return True if reasonably complete

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)