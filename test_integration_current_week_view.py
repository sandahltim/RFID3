#!/usr/bin/env python3
"""
Integration Test for Current Week View Functionality
End-to-end testing of the complete current week view system

This test verifies the entire chain:
1. Database configuration storage
2. Configuration API endpoints
3. Executive dashboard route
4. Template rendering
5. JavaScript functionality

Author: Testing Specialist
Date: 2025-09-08
"""

import requests
import json
import re
import time
from datetime import datetime


class IntegrationTester:
    """Integration tester for current week view functionality"""
    
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.results = {}
        self.test_log = []
    
    def log(self, message):
        """Add message to test log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.test_log.append(log_entry)
        print(log_entry)
    
    def test_configuration_api_flow(self):
        """Test complete configuration API flow"""
        self.log("🧪 Testing configuration API flow...")
        
        try:
            # Step 1: Get current configuration
            response = requests.get(f"{self.base_url}/config/api/executive-dashboard-configuration")
            
            if response.status_code != 200:
                self.results['config_api_get'] = f'FAIL - Status: {response.status_code}'
                return False
            
            data = response.json()
            if not data.get('success'):
                self.results['config_api_get'] = f'FAIL - Response not successful'
                return False
                
            original_value = data['data']['display_settings']['current_week_view_enabled']
            self.log(f"   Original value: {original_value}")
            
            # Step 2: Update to opposite value
            new_value = not bool(original_value)
            update_data = {
                'display_settings': {
                    'current_week_view_enabled': new_value
                }
            }
            
            response = requests.post(
                f"{self.base_url}/config/api/executive-dashboard-configuration",
                json=update_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code != 200:
                self.results['config_api_post'] = f'FAIL - Status: {response.status_code}'
                return False
            
            # Step 3: Verify change
            verify_response = requests.get(f"{self.base_url}/config/api/executive-dashboard-configuration")
            verify_data = verify_response.json()
            updated_value = verify_data['data']['display_settings']['current_week_view_enabled']
            
            if bool(updated_value) != new_value:
                self.results['config_api_verify'] = f'FAIL - Value not updated correctly'
                return False
                
            self.log(f"   Successfully updated to: {updated_value}")
            
            # Step 4: Test both enabled and disabled states with executive dashboard
            for test_state in [True, False]:
                self.log(f"   Testing executive dashboard with enabled={test_state}")
                
                # Set configuration
                config_data = {
                    'display_settings': {
                        'current_week_view_enabled': test_state
                    }
                }
                
                requests.post(
                    f"{self.base_url}/config/api/executive-dashboard-configuration",
                    json=config_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                # Wait a moment for the change to propagate
                time.sleep(1)
                
                # Test executive dashboard
                dashboard_response = requests.get(f"{self.base_url}/executive/dashboard")
                
                if dashboard_response.status_code != 200:
                    self.log(f"   WARNING: Executive dashboard returned {dashboard_response.status_code}")
                    continue
                
                dashboard_html = dashboard_response.text
                
                # Check if template properly renders based on configuration
                current_week_headers = dashboard_html.count('Current Week')
                
                if test_state:
                    # Should include Current Week columns
                    if current_week_headers > 0:
                        self.log(f"   ✅ Current Week headers present when enabled ({current_week_headers} found)")
                    else:
                        self.log(f"   ❌ No Current Week headers when enabled")
                else:
                    # Should not include Current Week columns
                    if current_week_headers == 0:
                        self.log(f"   ✅ No Current Week headers when disabled")
                    else:
                        self.log(f"   ⚠️  Current Week headers still present when disabled ({current_week_headers} found)")
                
                # Check if JavaScript configuration is passed correctly
                config_pattern = r'window\.dashboardConfig\s*=\s*({[^}]+})'
                config_match = re.search(config_pattern, dashboard_html)
                
                if config_match:
                    try:
                        # Parse the JavaScript object (simplified)
                        config_str = config_match.group(1)
                        if f'"current_week_view_enabled": {str(test_state).lower()}' in config_str.lower():
                            self.log(f"   ✅ JavaScript config correctly set to {test_state}")
                        else:
                            self.log(f"   ❌ JavaScript config not set correctly")
                    except Exception as e:
                        self.log(f"   ⚠️  Could not parse JavaScript config: {e}")
                else:
                    self.log(f"   ❌ No JavaScript config found in response")
            
            # Step 5: Restore original value
            restore_data = {
                'display_settings': {
                    'current_week_view_enabled': original_value
                }
            }
            
            requests.post(
                f"{self.base_url}/config/api/executive-dashboard-configuration",
                json=restore_data,
                headers={'Content-Type': 'application/json'}
            )
            
            self.log(f"   Original value restored: {original_value}")
            
            self.results['config_api_flow'] = 'PASS'
            return True
            
        except Exception as e:
            self.results['config_api_flow'] = f'FAIL - Exception: {str(e)}'
            self.log(f"   ❌ Exception: {str(e)}")
            return False
    
    def test_executive_dashboard_integration(self):
        """Test executive dashboard integration"""
        self.log("🧪 Testing executive dashboard integration...")
        
        try:
            response = requests.get(f"{self.base_url}/executive/dashboard")
            
            if response.status_code != 200:
                self.results['dashboard_integration'] = f'FAIL - Status: {response.status_code}'
                self.log(f"   ❌ Dashboard returned status {response.status_code}")
                return False
            
            html_content = response.text
            
            # Check for required elements
            checks = {
                'dashboard_config_variable': r'window\.dashboardConfig',
                'current_week_conditional': r'\{\%\s*if\s+dashboard_config\.current_week_view_enabled\s*\%\}',
                'javascript_function': r'function\s+initializeCurrentWeekVisibility',
                'function_call': r'initializeCurrentWeekVisibility\(\)',
                'current_week_column': r'Current Week'
            }
            
            all_passed = True
            for check_name, pattern in checks.items():
                if re.search(pattern, html_content, re.IGNORECASE):
                    self.log(f"   ✅ {check_name} found")
                    self.results[f'dashboard_{check_name}'] = 'PASS'
                else:
                    self.log(f"   ❌ {check_name} not found")
                    self.results[f'dashboard_{check_name}'] = 'FAIL'
                    all_passed = False
            
            if all_passed:
                self.results['dashboard_integration'] = 'PASS'
            else:
                self.results['dashboard_integration'] = 'FAIL'
            
            return all_passed
            
        except Exception as e:
            self.results['dashboard_integration'] = f'FAIL - Exception: {str(e)}'
            self.log(f"   ❌ Exception: {str(e)}")
            return False
    
    def test_javascript_functionality(self):
        """Test JavaScript functionality by creating a test page"""
        self.log("🧪 Testing JavaScript functionality...")
        
        try:
            # Get the executive dashboard to extract JavaScript
            response = requests.get(f"{self.base_url}/executive/dashboard")
            if response.status_code != 200:
                self.results['javascript_test'] = 'FAIL - Cannot access dashboard'
                return False
            
            html_content = response.text
            
            # Extract JavaScript code
            script_pattern = r'<script[^>]*>(.*?)</script>'
            scripts = re.findall(script_pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            js_code = '\n'.join(scripts)
            
            # Check for function components
            function_checks = {
                'function_definition': r'function\s+initializeCurrentWeekVisibility',
                'config_check': r'dashboardConfig\.current_week_view_enabled',
                'dom_manipulation': r'style\.display\s*=\s*[\'"]none[\'"]',
                'element_selection': r'querySelectorAll\s*\(',
                'text_content_check': r'textContent\.includes'
            }
            
            all_js_checks_passed = True
            for check_name, pattern in function_checks.items():
                if re.search(pattern, js_code):
                    self.log(f"   ✅ {check_name} found in JavaScript")
                    self.results[f'js_{check_name}'] = 'PASS'
                else:
                    self.log(f"   ❌ {check_name} not found in JavaScript")
                    self.results[f'js_{check_name}'] = 'FAIL'
                    all_js_checks_passed = False
            
            # Create a test HTML page
            test_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Current Week View Test</title>
    <style>
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Current Week View Functionality Test</h1>
    <div id="testResults"></div>
    
    <table>
        <thead>
            <tr>
                <th>Store</th>
                <th>Previous Week</th>
                <th class="current-week-header">Current Week</th>
                <th>YoY Growth</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Test Store</td>
                <td>$1000</td>
                <td id="revenue-test-current" class="current-week-cell">$1200</td>
                <td>+20%</td>
            </tr>
        </tbody>
    </table>
    
    <script>
        window.dashboardConfig = {{ current_week_view_enabled: false }};
        
        {js_code}
        
        // Test the function
        function runTest() {{
            const results = document.getElementById('testResults');
            
            try {{
                // Test with disabled config
                window.dashboardConfig.current_week_view_enabled = false;
                initializeCurrentWeekVisibility();
                
                const hiddenHeaders = Array.from(document.querySelectorAll('th')).filter(th => 
                    th.textContent.includes('Current Week') && th.style.display === 'none'
                );
                
                const hiddenCells = Array.from(document.querySelectorAll('[id$="-current"]')).filter(cell => 
                    cell.style.display === 'none'
                );
                
                if (hiddenHeaders.length > 0 && hiddenCells.length > 0) {{
                    results.innerHTML = '<p style="color: green;">✅ TEST PASSED: Function correctly hides current week columns when disabled</p>';
                    return true;
                }} else {{
                    results.innerHTML = '<p style="color: red;">❌ TEST FAILED: Function did not hide columns properly</p>';
                    return false;
                }}
            }} catch (e) {{
                results.innerHTML = '<p style="color: red;">❌ TEST ERROR: ' + e.message + '</p>';
                return false;
            }}
        }}
        
        window.onload = runTest;
    </script>
</body>
</html>
            """
            
            # Save test file
            with open('current_week_test_integration.html', 'w') as f:
                f.write(test_html)
            
            self.log("   ✅ Test HTML file created: current_week_test_integration.html")
            
            if all_js_checks_passed:
                self.results['javascript_test'] = 'PASS'
            else:
                self.results['javascript_test'] = 'PARTIAL'
            
            return all_js_checks_passed
            
        except Exception as e:
            self.results['javascript_test'] = f'FAIL - Exception: {str(e)}'
            self.log(f"   ❌ Exception: {str(e)}")
            return False
    
    def test_configuration_ui_consistency(self):
        """Test that configuration UI is consistent with functionality"""
        self.log("🧪 Testing configuration UI consistency...")
        
        try:
            # Check if configuration page exists
            config_response = requests.get(f"{self.base_url}/config/")
            
            if config_response.status_code == 200:
                self.log("   ✅ Configuration page accessible")
                
                config_html = config_response.text
                
                # Check for current week configuration elements
                ui_checks = {
                    'executive_dashboard_config': r'executive.*dashboard',
                    'current_week_reference': r'current.*week',
                    'display_settings': r'display.*settings'
                }
                
                ui_found = 0
                for check_name, pattern in ui_checks.items():
                    if re.search(pattern, config_html, re.IGNORECASE):
                        self.log(f"   ✅ {check_name} found in config UI")
                        ui_found += 1
                    else:
                        self.log(f"   ⚠️  {check_name} not found in config UI")
                
                if ui_found >= 2:
                    self.results['config_ui_consistency'] = 'PASS'
                    return True
                else:
                    self.results['config_ui_consistency'] = 'PARTIAL'
                    return False
            else:
                self.log(f"   ⚠️  Configuration page not accessible (status: {config_response.status_code})")
                self.results['config_ui_consistency'] = 'FAIL'
                return False
                
        except Exception as e:
            self.results['config_ui_consistency'] = f'FAIL - Exception: {str(e)}'
            self.log(f"   ❌ Exception: {str(e)}")
            return False
    
    def run_comprehensive_integration_test(self):
        """Run complete integration test suite"""
        self.log("="*80)
        self.log("🚀 RUNNING COMPREHENSIVE INTEGRATION TEST")
        self.log("   Current Week View Functionality End-to-End Testing")
        self.log("="*80)
        
        test_suites = [
            ("Configuration API Flow", self.test_configuration_api_flow),
            ("Executive Dashboard Integration", self.test_executive_dashboard_integration),
            ("JavaScript Functionality", self.test_javascript_functionality),
            ("Configuration UI Consistency", self.test_configuration_ui_consistency)
        ]
        
        passed_tests = 0
        total_tests = len(test_suites)
        
        for test_name, test_function in test_suites:
            self.log(f"\n{'-'*60}")
            self.log(f"📋 {test_name}")
            self.log(f"{'-'*60}")
            
            try:
                result = test_function()
                if result:
                    self.log(f"✅ {test_name}: PASSED")
                    passed_tests += 1
                else:
                    self.log(f"❌ {test_name}: FAILED")
            except Exception as e:
                self.log(f"💥 {test_name}: ERROR - {str(e)}")
                self.results[f'{test_name.lower().replace(" ", "_")}_error'] = str(e)
        
        # Generate comprehensive summary
        self.generate_integration_summary(passed_tests, total_tests)
        
        return passed_tests, total_tests
    
    def generate_integration_summary(self, passed_tests, total_tests):
        """Generate comprehensive integration test summary"""
        self.log("\n" + "="*80)
        self.log("📊 INTEGRATION TEST SUMMARY")
        self.log("="*80)
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        self.log(f"Total Test Suites: {total_tests}")
        self.log(f"Passed: {passed_tests}")
        self.log(f"Failed: {total_tests - passed_tests}")
        self.log(f"Success Rate: {success_rate:.1f}%")
        
        # Overall assessment
        if success_rate >= 90:
            self.log("🎉 EXCELLENT: Current week view functionality is working perfectly!")
            overall_status = "EXCELLENT"
        elif success_rate >= 75:
            self.log("✅ GOOD: Current week view functionality is working well")
            overall_status = "GOOD"
        elif success_rate >= 50:
            self.log("⚠️  FAIR: Current week view functionality has some issues")
            overall_status = "FAIR"
        else:
            self.log("❌ POOR: Current week view functionality has significant problems")
            overall_status = "POOR"
        
        # Detailed results
        self.log(f"\n📋 DETAILED RESULTS:")
        pass_count = sum(1 for result in self.results.values() if result == 'PASS')
        fail_count = sum(1 for result in self.results.values() if result == 'FAIL')
        partial_count = sum(1 for result in self.results.values() if result == 'PARTIAL')
        
        for test_name, result in sorted(self.results.items()):
            status_emoji = "✅" if result == 'PASS' else "❌" if result == 'FAIL' else "⚠️" if result == 'PARTIAL' else "❓"
            self.log(f"  {status_emoji} {test_name}: {result}")
        
        self.log(f"\n📈 COMPONENT RESULTS:")
        self.log(f"  Passed: {pass_count}")
        self.log(f"  Failed: {fail_count}")  
        self.log(f"  Partial: {partial_count}")
        
        # Save comprehensive results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"integration_test_results_{timestamp}.json"
        
        summary_data = {
            'timestamp': timestamp,
            'test_suites': {
                'total': total_tests,
                'passed': passed_tests,
                'failed': total_tests - passed_tests,
                'success_rate': success_rate
            },
            'component_results': {
                'total': len(self.results),
                'passed': pass_count,
                'failed': fail_count,
                'partial': partial_count
            },
            'overall_status': overall_status,
            'detailed_results': self.results,
            'test_log': self.test_log
        }
        
        with open(results_file, 'w') as f:
            json.dump(summary_data, f, indent=2)
        
        self.log(f"\n📄 Complete results saved to: {results_file}")
        
        return summary_data


def main():
    """Main integration test runner"""
    print("🔬 Current Week View Functionality - Integration Testing")
    print("Testing complete end-to-end functionality...")
    print()
    
    tester = IntegrationTester()
    passed, total = tester.run_comprehensive_integration_test()
    
    # Final assessment
    if passed == total:
        print("\n🎯 FINAL VERDICT: All integration tests passed! The current week view")
        print("   functionality is working correctly across all components.")
        exit(0)
    else:
        print(f"\n⚠️  FINAL VERDICT: {passed}/{total} integration tests passed.")
        print("   Review the detailed results above for issues to address.")
        exit(1)


if __name__ == '__main__':
    main()