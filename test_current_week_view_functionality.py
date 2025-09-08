#!/usr/bin/env python3
"""
Current Week View Functionality Test Suite
Comprehensive testing of current_week_view_enabled implementation

Test Coverage:
1. Database schema validation
2. Configuration API (GET/POST)
3. Model functionality
4. JavaScript integration
5. Template rendering
6. End-to-end functionality

Author: Testing Specialist
Date: 2025-09-08
"""

import unittest
import requests
import json
import pymysql
import sys
import os
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'rfid_user',
    'password': 'rfid_user_password',
    'database': 'rfid_inventory',
    'charset': 'utf8mb4'
}

# Base URL for API tests
BASE_URL = 'http://localhost:5000'

class TestCurrentWeekViewFunctionality(unittest.TestCase):
    """Comprehensive test suite for current_week_view_enabled functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        print(f"\n{'='*60}")
        print(f"🧪 Running test: {self._testMethodName}")
        print(f"{'='*60}")
        
        # Connect to database
        try:
            self.db_conn = pymysql.connect(**DB_CONFIG)
            self.cursor = self.db_conn.cursor()
            print("✅ Database connection established")
        except Exception as e:
            self.fail(f"❌ Database connection failed: {e}")
    
    def tearDown(self):
        """Clean up test fixtures"""
        if hasattr(self, 'db_conn'):
            self.db_conn.close()
            print("✅ Database connection closed")
    
    def test_01_database_schema_validation(self):
        """Test 1: Verify database column exists and has correct properties"""
        print("\n🔍 Testing database schema...")
        
        # Check if table exists
        self.cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'rfid_inventory' 
            AND table_name = 'executive_dashboard_configuration'
        """)
        
        table_exists = self.cursor.fetchone()
        self.assertIsNotNone(table_exists, "❌ executive_dashboard_configuration table does not exist")
        print("✅ executive_dashboard_configuration table exists")
        
        # Check column schema
        self.cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_schema = 'rfid_inventory' 
            AND table_name = 'executive_dashboard_configuration'
            AND column_name = 'current_week_view_enabled'
        """)
        
        column_info = self.cursor.fetchone()
        self.assertIsNotNone(column_info, "❌ current_week_view_enabled column does not exist")
        
        column_name, data_type, is_nullable, column_default = column_info
        
        # Validate column properties
        self.assertEqual(column_name, 'current_week_view_enabled')
        self.assertEqual(data_type, 'tinyint')
        self.assertEqual(is_nullable, 'NO')
        self.assertEqual(column_default, '1')
        
        print("✅ current_week_view_enabled column schema validated:")
        print(f"   - Data type: {data_type}")
        print(f"   - Nullable: {is_nullable}")
        print(f"   - Default: {column_default}")
        
        # Check current values
        self.cursor.execute("SELECT id, current_week_view_enabled FROM executive_dashboard_configuration LIMIT 5")
        values = self.cursor.fetchall()
        print(f"✅ Current values: {values}")
        
        # Ensure there's at least one record with default value
        if values:
            for record_id, enabled in values:
                self.assertIn(enabled, [0, 1], f"❌ Invalid value {enabled} for record {record_id}")
                print(f"   - Record {record_id}: {enabled} ({'enabled' if enabled else 'disabled'})")
    
    def test_02_configuration_api_get(self):
        """Test 2: Verify GET API returns display_settings"""
        print("\n🔍 Testing configuration API GET...")
        
        try:
            response = requests.get(f"{BASE_URL}/config/api/executive-dashboard-configuration")
            
            self.assertEqual(response.status_code, 200, 
                           f"❌ API returned status {response.status_code}")
            print(f"✅ API responded with status 200")
            
            data = response.json()
            self.assertTrue(data.get('success'), 
                          f"❌ API response not successful: {data}")
            print("✅ API response marked as successful")
            
            # Check if display_settings exists
            config_data = data.get('data', {})
            self.assertIn('display_settings', config_data, 
                         "❌ display_settings section missing from API response")
            print("✅ display_settings section found in response")
            
            display_settings = config_data['display_settings']
            self.assertIn('current_week_view_enabled', display_settings,
                         "❌ current_week_view_enabled missing from display_settings")
            print("✅ current_week_view_enabled found in display_settings")
            
            current_week_enabled = display_settings['current_week_view_enabled']
            self.assertIsInstance(current_week_enabled, (bool, int),
                                f"❌ current_week_view_enabled is not boolean/int: {type(current_week_enabled)}")
            
            print(f"✅ current_week_view_enabled value: {current_week_enabled}")
            
            # Store original value for POST test
            self.original_value = bool(current_week_enabled)
            
        except requests.exceptions.RequestException as e:
            self.fail(f"❌ API request failed: {e}")
        except json.JSONDecodeError as e:
            self.fail(f"❌ Invalid JSON response: {e}")
    
    def test_03_configuration_api_post(self):
        """Test 3: Verify POST API can update display_settings"""
        print("\n🔍 Testing configuration API POST...")
        
        # First get current configuration
        response = requests.get(f"{BASE_URL}/config/api/executive-dashboard-configuration")
        self.assertEqual(response.status_code, 200)
        
        original_config = response.json()['data']
        original_value = original_config['display_settings']['current_week_view_enabled']
        
        print(f"📊 Original value: {original_value}")
        
        # Test updating to opposite value
        new_value = not bool(original_value)
        print(f"🔄 Testing update to: {new_value}")
        
        update_data = {
            'display_settings': {
                'current_week_view_enabled': new_value
            }
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/config/api/executive-dashboard-configuration",
                json=update_data,
                headers={'Content-Type': 'application/json'}
            )
            
            self.assertEqual(response.status_code, 200,
                           f"❌ POST API returned status {response.status_code}")
            print("✅ POST API responded with status 200")
            
            result = response.json()
            self.assertTrue(result.get('success'),
                          f"❌ POST API response not successful: {result}")
            print("✅ POST API response marked as successful")
            
            # Verify the change was persisted
            verify_response = requests.get(f"{BASE_URL}/config/api/executive-dashboard-configuration")
            verify_data = verify_response.json()['data']
            updated_value = verify_data['display_settings']['current_week_view_enabled']
            
            self.assertEqual(bool(updated_value), new_value,
                           f"❌ Value not updated: expected {new_value}, got {updated_value}")
            print(f"✅ Value successfully updated to: {updated_value}")
            
            # Restore original value
            restore_data = {
                'display_settings': {
                    'current_week_view_enabled': original_value
                }
            }
            
            restore_response = requests.post(
                f"{BASE_URL}/config/api/executive-dashboard-configuration",
                json=restore_data,
                headers={'Content-Type': 'application/json'}
            )
            
            self.assertEqual(restore_response.status_code, 200)
            print(f"✅ Original value restored: {original_value}")
            
        except requests.exceptions.RequestException as e:
            self.fail(f"❌ POST API request failed: {e}")
    
    def test_04_model_functionality(self):
        """Test 4: Verify model field is properly defined and accessible"""
        print("\n🔍 Testing model functionality...")
        
        # Check if we can directly query the field
        self.cursor.execute("""
            SELECT id, user_id, current_week_view_enabled, created_at, updated_at
            FROM executive_dashboard_configuration 
            WHERE is_active = 1 
            LIMIT 3
        """)
        
        records = self.cursor.fetchall()
        self.assertGreater(len(records), 0, 
                         "❌ No active configuration records found")
        print(f"✅ Found {len(records)} active configuration records")
        
        for record in records:
            record_id, user_id, enabled, created, updated = record
            
            # Validate data types
            self.assertIsInstance(record_id, int, 
                                f"❌ Record ID should be int, got {type(record_id)}")
            self.assertIsInstance(user_id, str,
                                f"❌ User ID should be str, got {type(user_id)}")
            self.assertIn(enabled, [0, 1],
                        f"❌ current_week_view_enabled should be 0 or 1, got {enabled}")
            
            print(f"   - Record {record_id} (user: {user_id}): enabled={enabled}")
        
        # Test updating via direct SQL
        print("\n🔧 Testing direct SQL update...")
        
        # Get first record
        test_record = records[0]
        test_id = test_record[0]
        original_value = test_record[2]
        new_value = 1 - original_value  # flip 0->1 or 1->0
        
        # Update the value
        self.cursor.execute("""
            UPDATE executive_dashboard_configuration 
            SET current_week_view_enabled = %s, updated_at = %s
            WHERE id = %s
        """, (new_value, datetime.now(), test_id))
        
        self.db_conn.commit()
        
        # Verify update
        self.cursor.execute("""
            SELECT current_week_view_enabled 
            FROM executive_dashboard_configuration 
            WHERE id = %s
        """, (test_id,))
        
        updated_result = self.cursor.fetchone()
        self.assertEqual(updated_result[0], new_value,
                       f"❌ Direct SQL update failed: expected {new_value}, got {updated_result[0]}")
        print(f"✅ Direct SQL update successful: {original_value} -> {new_value}")
        
        # Restore original value
        self.cursor.execute("""
            UPDATE executive_dashboard_configuration 
            SET current_week_view_enabled = %s, updated_at = %s
            WHERE id = %s
        """, (original_value, datetime.now(), test_id))
        
        self.db_conn.commit()
        print(f"✅ Original value restored: {original_value}")
    
    def test_05_template_integration(self):
        """Test 5: Verify template properly uses dashboard_config variable"""
        print("\n🔍 Testing template integration...")
        
        # Read the executive dashboard template
        template_path = "app/templates/executive_dashboard.html"
        
        self.assertTrue(os.path.exists(template_path),
                       f"❌ Template file not found: {template_path}")
        print(f"✅ Template file found: {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Check for dashboard_config usage
        self.assertIn('dashboard_config', template_content,
                     "❌ dashboard_config variable not found in template")
        print("✅ dashboard_config variable found in template")
        
        # Check for current_week_view_enabled usage
        self.assertIn('current_week_view_enabled', template_content,
                     "❌ current_week_view_enabled not found in template")
        print("✅ current_week_view_enabled found in template")
        
        # Check for conditional rendering
        if_statement = "{% if dashboard_config.current_week_view_enabled %}"
        self.assertIn(if_statement, template_content,
                     f"❌ Conditional statement not found: {if_statement}")
        print("✅ Conditional rendering statement found")
        
        # Check for endif
        endif_statement = "{% endif %}"
        endif_count = template_content.count(endif_statement)
        if_count = template_content.count(if_statement)
        
        self.assertGreaterEqual(endif_count, if_count,
                              f"❌ Mismatched if/endif statements: {if_count} if, {endif_count} endif")
        print(f"✅ Template conditional statements balanced: {if_count} if, {endif_count} endif")
        
        # Check for JavaScript function
        js_function = "initializeCurrentWeekVisibility"
        self.assertIn(js_function, template_content,
                     f"❌ JavaScript function not found: {js_function}")
        print(f"✅ JavaScript function found: {js_function}")
    
    def test_06_javascript_functionality(self):
        """Test 6: Verify JavaScript function exists and is properly structured"""
        print("\n🔍 Testing JavaScript functionality...")
        
        # Read the executive dashboard template (contains the JavaScript)
        template_path = "app/templates/executive_dashboard.html"
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Extract JavaScript section
        js_start = template_content.find('<script>')
        js_end = template_content.rfind('</script>')
        
        self.assertNotEqual(js_start, -1, "❌ No JavaScript section found")
        self.assertNotEqual(js_end, -1, "❌ JavaScript section not properly closed")
        print("✅ JavaScript section found in template")
        
        js_content = template_content[js_start:js_end]
        
        # Check for window.dashboardConfig
        self.assertIn('window.dashboardConfig', js_content,
                     "❌ window.dashboardConfig not found")
        print("✅ window.dashboardConfig found")
        
        # Check for initializeCurrentWeekVisibility function
        function_def = "function initializeCurrentWeekVisibility"
        self.assertIn(function_def, js_content,
                     f"❌ Function definition not found: {function_def}")
        print("✅ initializeCurrentWeekVisibility function definition found")
        
        # Check for function call
        function_call = "initializeCurrentWeekVisibility()"
        self.assertIn(function_call, js_content,
                     f"❌ Function call not found: {function_call}")
        print("✅ initializeCurrentWeekVisibility function call found")
        
        # Check for column hiding logic
        self.assertIn('style.display = \'none\'', js_content,
                     "❌ Column hiding logic not found")
        print("✅ Column hiding logic found")
        
        # Check for querySelector/querySelectorAll
        self.assertIn('querySelectorAll', js_content,
                     "❌ DOM query methods not found")
        print("✅ DOM query methods found")
    
    def test_07_end_to_end_functionality(self):
        """Test 7: End-to-end test of the complete functionality"""
        print("\n🔍 Testing end-to-end functionality...")
        
        # Step 1: Get current configuration
        response = requests.get(f"{BASE_URL}/config/api/executive-dashboard-configuration")
        self.assertEqual(response.status_code, 200)
        
        original_config = response.json()['data']
        original_enabled = original_config['display_settings']['current_week_view_enabled']
        
        print(f"📊 Original setting: current_week_view_enabled = {original_enabled}")
        
        # Step 2: Test both enabled and disabled states
        for test_value in [True, False]:
            print(f"\n🧪 Testing with current_week_view_enabled = {test_value}")
            
            # Update configuration
            update_data = {
                'display_settings': {
                    'current_week_view_enabled': test_value
                }
            }
            
            response = requests.post(
                f"{BASE_URL}/config/api/executive-dashboard-configuration",
                json=update_data,
                headers={'Content-Type': 'application/json'}
            )
            
            self.assertEqual(response.status_code, 200)
            print(f"✅ Configuration updated to: {test_value}")
            
            # Verify in database
            self.cursor.execute("""
                SELECT current_week_view_enabled 
                FROM executive_dashboard_configuration 
                WHERE is_active = 1 
                LIMIT 1
            """)
            
            db_result = self.cursor.fetchone()
            self.assertIsNotNone(db_result, "❌ No active configuration found")
            
            db_value = bool(db_result[0])
            self.assertEqual(db_value, test_value,
                           f"❌ Database value mismatch: expected {test_value}, got {db_value}")
            print(f"✅ Database value verified: {db_value}")
            
            # Test API response includes the new value
            verify_response = requests.get(f"{BASE_URL}/config/api/executive-dashboard-configuration")
            verify_data = verify_response.json()['data']
            api_value = verify_data['display_settings']['current_week_view_enabled']
            
            self.assertEqual(bool(api_value), test_value,
                           f"❌ API value mismatch: expected {test_value}, got {api_value}")
            print(f"✅ API value verified: {api_value}")
        
        # Step 3: Restore original configuration
        restore_data = {
            'display_settings': {
                'current_week_view_enabled': original_enabled
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/config/api/executive-dashboard-configuration",
            json=restore_data,
            headers={'Content-Type': 'application/json'}
        )
        
        self.assertEqual(response.status_code, 200)
        print(f"✅ Original configuration restored: {original_enabled}")
    
    def test_08_configuration_ui_integration(self):
        """Test 8: Verify configuration UI can handle the setting"""
        print("\n🔍 Testing configuration UI integration...")
        
        # Check if configuration.js handles display_settings
        config_js_path = "app/static/js/configuration.js"
        
        if os.path.exists(config_js_path):
            with open(config_js_path, 'r', encoding='utf-8') as f:
                config_js_content = f.read()
            
            print(f"✅ Configuration JavaScript file found: {config_js_path}")
            
            # Look for display_settings handling
            if 'display_settings' in config_js_content:
                print("✅ display_settings referenced in configuration.js")
            else:
                print("⚠️  display_settings not found in configuration.js (may need implementation)")
            
            # Look for executive dashboard configuration handling
            if 'executive' in config_js_content.lower() and 'dashboard' in config_js_content.lower():
                print("✅ Executive dashboard configuration handling found")
            else:
                print("⚠️  Executive dashboard configuration handling may need implementation")
        else:
            print(f"⚠️  Configuration JavaScript file not found: {config_js_path}")
        
        # Check configuration template
        config_template_path = "app/templates/configuration.html"
        
        if os.path.exists(config_template_path):
            print(f"✅ Configuration template found: {config_template_path}")
            
            with open(config_template_path, 'r', encoding='utf-8') as f:
                config_template_content = f.read()
            
            if 'current_week_view' in config_template_content:
                print("✅ current_week_view referenced in configuration template")
            else:
                print("⚠️  current_week_view not found in configuration template")
        else:
            print(f"⚠️  Configuration template not found: {config_template_path}")
    
    def run_comprehensive_test(self):
        """Run all tests in sequence and provide summary"""
        print(f"\n{'='*80}")
        print("🚀 RUNNING COMPREHENSIVE CURRENT WEEK VIEW FUNCTIONALITY TESTS")
        print(f"{'='*80}")
        
        test_methods = [
            self.test_01_database_schema_validation,
            self.test_02_configuration_api_get,
            self.test_03_configuration_api_post,
            self.test_04_model_functionality,
            self.test_05_template_integration,
            self.test_06_javascript_functionality,
            self.test_07_end_to_end_functionality,
            self.test_08_configuration_ui_integration
        ]
        
        results = {}
        
        for test_method in test_methods:
            test_name = test_method.__name__
            try:
                test_method()
                results[test_name] = "✅ PASSED"
            except Exception as e:
                results[test_name] = f"❌ FAILED: {str(e)}"
        
        # Print summary
        print(f"\n{'='*80}")
        print("📊 TEST RESULTS SUMMARY")
        print(f"{'='*80}")
        
        passed = sum(1 for result in results.values() if result.startswith("✅"))
        total = len(results)
        
        for test_name, result in results.items():
            print(f"{test_name}: {result}")
        
        print(f"\n📈 OVERALL RESULTS: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED! Current week view functionality is working correctly.")
        else:
            print("⚠️  Some tests failed. See details above for issues to resolve.")
        
        return results


def main():
    """Main test runner"""
    if len(sys.argv) > 1 and sys.argv[1] == '--single':
        # Run individual tests
        unittest.main(argv=sys.argv[2:])
    else:
        # Run comprehensive test suite
        tester = TestCurrentWeekViewFunctionality()
        tester.setUp()
        try:
            results = tester.run_comprehensive_test()
            
            # Save results to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = f"current_week_view_test_results_{timestamp}.json"
            
            with open(results_file, 'w') as f:
                json.dump({
                    'timestamp': timestamp,
                    'results': results,
                    'summary': {
                        'total_tests': len(results),
                        'passed': sum(1 for r in results.values() if r.startswith("✅")),
                        'failed': sum(1 for r in results.values() if r.startswith("❌"))
                    }
                }, f, indent=2)
            
            print(f"\n📄 Results saved to: {results_file}")
            
        finally:
            tester.tearDown()


if __name__ == '__main__':
    main()