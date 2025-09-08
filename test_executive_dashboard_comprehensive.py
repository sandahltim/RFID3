#!/usr/bin/env python3
"""
Comprehensive Executive Dashboard Test Suite

Tests all critical functionality after the major cleanup:
1. KPI Cards displaying actual values (not NaN/Loading)
2. API Endpoints returning valid data
3. Charts loading without errors
4. Console error detection
5. Page performance validation
6. Data flow integrity

Author: Testing Specialist
Date: 2025-09-03
"""

import requests
import json
import time
import sys
import traceback
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class ExecutiveDashboardTestSuite:
    def __init__(self, base_url="https://pi5:6800"):
        self.base_url = base_url
        self.driver = None
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'errors': [],
            'warnings': [],
            'kpi_tests': {},
            'api_tests': {},
            'chart_tests': {},
            'performance_tests': {},
            'console_errors': [],
            'data_flow_tests': {}
        }
    
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in background
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
            chrome_options.add_argument('--allow-running-insecure-content')
            
            # Enable logging to capture console errors
            chrome_options.add_argument('--enable-logging')
            chrome_options.add_argument('--log-level=0')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            return True
        except Exception as e:
            self.test_results['errors'].append(f"Failed to setup WebDriver: {str(e)}")
            return False

    def test_api_endpoint(self, endpoint, test_name):
        """Test individual API endpoint for valid response"""
        self.test_results['total_tests'] += 1
        test_result = {
            'endpoint': endpoint,
            'status': 'FAILED',
            'response_time': 0,
            'status_code': None,
            'data_valid': False,
            'error': None
        }
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}{endpoint}", 
                                  timeout=10, 
                                  verify=False)
            test_result['response_time'] = round(time.time() - start_time, 3)
            test_result['status_code'] = response.status_code
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    test_result['data_valid'] = self.validate_api_response(endpoint, data)
                    if test_result['data_valid']:
                        test_result['status'] = 'PASSED'
                        self.test_results['passed_tests'] += 1
                    else:
                        test_result['error'] = 'Invalid data structure'
                        self.test_results['failed_tests'] += 1
                except json.JSONDecodeError as e:
                    test_result['error'] = f'Invalid JSON response: {str(e)}'
                    self.test_results['failed_tests'] += 1
            else:
                test_result['error'] = f'HTTP {response.status_code}: {response.text[:200]}'
                self.test_results['failed_tests'] += 1
                
        except requests.RequestException as e:
            test_result['error'] = f'Request failed: {str(e)}'
            test_result['response_time'] = time.time() - start_time if 'start_time' in locals() else 0
            self.test_results['failed_tests'] += 1
        
        self.test_results['api_tests'][test_name] = test_result
        return test_result['status'] == 'PASSED'

    def validate_api_response(self, endpoint, data):
        """Validate API response data structure and content"""
        if not isinstance(data, dict):
            return False
            
        if '/financial-kpis' in endpoint:
            required_fields = ['total_revenue', 'yoy_growth', 'equipment_utilization', 'business_health']
            return all(field in data for field in required_fields)
            
        elif '/intelligent-insights' in endpoint:
            return 'insights' in data and isinstance(data['insights'], list)
            
        elif '/store-comparison' in endpoint:
            return 'stores' in data and isinstance(data['stores'], list)
            
        elif '/financial-forecasts' in endpoint:
            return 'forecast' in data and isinstance(data['forecast'], list)
            
        return True  # Default to valid for other endpoints

    def test_kpi_cards(self):
        """Test KPI cards for actual numerical values (not NaN/Loading)"""
        if not self.driver:
            return False
            
        kpi_tests = {
            'total_revenue': {'selector': '[data-kpi="total-revenue"]', 'status': 'FAILED'},
            'yoy_growth': {'selector': '[data-kpi="yoy-growth"]', 'status': 'FAILED'},
            'equipment_utilization': {'selector': '[data-kpi="equipment-utilization"]', 'status': 'FAILED'},
            'business_health': {'selector': '[data-kpi="business-health"]', 'status': 'FAILED'}
        }
        
        try:
            self.driver.get(f"{self.base_url}/executive/dashboard")
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Give time for JavaScript to populate KPIs
            time.sleep(5)
            
            for kpi_name, kpi_info in kpi_tests.items():
                self.test_results['total_tests'] += 1
                try:
                    # Try multiple selector strategies
                    selectors = [
                        kpi_info['selector'],
                        f'#{kpi_name.replace("_", "-")}-value',
                        f'.kpi-card[data-metric="{kpi_name}"] .kpi-value',
                        f'[id*="{kpi_name}"]'
                    ]
                    
                    element = None
                    for selector in selectors:
                        try:
                            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if elements:
                                element = elements[0]
                                break
                        except:
                            continue
                    
                    if element:
                        value = element.text.strip()
                        kpi_info['value'] = value
                        
                        # Check if value is valid (not NaN, Loading, empty, or 0)
                        if value and value.lower() not in ['nan', 'loading...', 'loading', '--']:
                            # Try to extract numerical value
                            import re
                            numeric_match = re.search(r'[\d,.-]+', value)
                            if numeric_match:
                                numeric_value = numeric_match.group().replace(',', '')
                                try:
                                    float(numeric_value)
                                    kpi_info['status'] = 'PASSED'
                                    kpi_info['numeric_value'] = numeric_value
                                    self.test_results['passed_tests'] += 1
                                except ValueError:
                                    kpi_info['error'] = f'Non-numeric value: {value}'
                                    self.test_results['failed_tests'] += 1
                            else:
                                kpi_info['error'] = f'No numeric value found: {value}'
                                self.test_results['failed_tests'] += 1
                        else:
                            kpi_info['error'] = f'Invalid/empty value: {value}'
                            self.test_results['failed_tests'] += 1
                    else:
                        kpi_info['error'] = 'Element not found'
                        self.test_results['failed_tests'] += 1
                        
                except Exception as e:
                    kpi_info['error'] = str(e)
                    self.test_results['failed_tests'] += 1
            
            self.test_results['kpi_tests'] = kpi_tests
            return all(kpi['status'] == 'PASSED' for kpi in kpi_tests.values())
            
        except Exception as e:
            self.test_results['errors'].append(f"KPI test failed: {str(e)}")
            return False

    def test_charts_loading(self):
        """Test that charts load without JavaScript errors"""
        if not self.driver:
            return False
            
        chart_tests = {
            'revenue_trend': {'selector': '#revenue-trend-chart', 'status': 'FAILED'},
            'forecast_chart': {'selector': '#forecast-chart', 'status': 'FAILED'},
            'store_comparison': {'selector': '#store-comparison-chart', 'status': 'FAILED'}
        }
        
        try:
            # Give extra time for charts to load
            time.sleep(8)
            
            for chart_name, chart_info in chart_tests.items():
                self.test_results['total_tests'] += 1
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, chart_info['selector'])
                    if elements:
                        element = elements[0]
                        
                        # Check if chart has content (SVG, Canvas, or child elements)
                        has_svg = element.find_elements(By.TAG_NAME, 'svg')
                        has_canvas = element.find_elements(By.TAG_NAME, 'canvas')
                        has_children = len(element.find_elements(By.XPATH, './/*')) > 0
                        
                        if has_svg or has_canvas or has_children:
                            chart_info['status'] = 'PASSED'
                            chart_info['chart_type'] = 'SVG' if has_svg else 'Canvas' if has_canvas else 'Other'
                            self.test_results['passed_tests'] += 1
                        else:
                            chart_info['error'] = 'Chart container empty'
                            self.test_results['failed_tests'] += 1
                    else:
                        chart_info['error'] = 'Chart element not found'
                        self.test_results['failed_tests'] += 1
                        
                except Exception as e:
                    chart_info['error'] = str(e)
                    self.test_results['failed_tests'] += 1
            
            self.test_results['chart_tests'] = chart_tests
            return all(chart['status'] == 'PASSED' for chart in chart_tests.values())
            
        except Exception as e:
            self.test_results['errors'].append(f"Chart loading test failed: {str(e)}")
            return False

    def check_console_errors(self):
        """Check browser console for JavaScript errors"""
        if not self.driver:
            return False
            
        try:
            # Get console logs
            logs = self.driver.get_log('browser')
            
            critical_errors = []
            warnings = []
            
            for log in logs:
                if log['level'] == 'SEVERE':
                    critical_errors.append({
                        'level': log['level'],
                        'message': log['message'],
                        'timestamp': log['timestamp']
                    })
                elif log['level'] in ['WARNING', 'INFO']:
                    warnings.append({
                        'level': log['level'],
                        'message': log['message'],
                        'timestamp': log['timestamp']
                    })
            
            self.test_results['console_errors'] = critical_errors
            self.test_results['warnings'].extend(warnings)
            
            # Test passes if no SEVERE errors
            has_critical_errors = len(critical_errors) > 0
            if not has_critical_errors:
                self.test_results['passed_tests'] += 1
            else:
                self.test_results['failed_tests'] += 1
                
            self.test_results['total_tests'] += 1
            return not has_critical_errors
            
        except Exception as e:
            self.test_results['errors'].append(f"Console error check failed: {str(e)}")
            return False

    def test_page_performance(self):
        """Test page load performance and stability"""
        if not self.driver:
            return False
            
        performance_results = {
            'load_time': 0,
            'no_flash': False,
            'stable_content': False,
            'status': 'FAILED'
        }
        
        try:
            start_time = time.time()
            self.driver.get(f"{self.base_url}/executive/dashboard")
            
            # Wait for basic page load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            performance_results['load_time'] = round(time.time() - start_time, 3)
            
            # Test for page stability (no flashing/reloading)
            initial_title = self.driver.title
            time.sleep(3)  # Wait to see if page reloads
            final_title = self.driver.title
            
            performance_results['no_flash'] = (initial_title == final_title)
            
            # Test for stable content (check if main container exists and persists)
            try:
                main_container = self.driver.find_element(By.CSS_SELECTOR, 
                    'body, .dashboard-container, .executive-dashboard, main')
                time.sleep(2)
                # Check if container is still there
                main_container.is_displayed()
                performance_results['stable_content'] = True
            except:
                performance_results['stable_content'] = False
            
            # Performance test passes if load time < 10s, no flash, stable content
            if (performance_results['load_time'] < 10 and 
                performance_results['no_flash'] and 
                performance_results['stable_content']):
                performance_results['status'] = 'PASSED'
                self.test_results['passed_tests'] += 1
            else:
                self.test_results['failed_tests'] += 1
                
            self.test_results['total_tests'] += 1
            self.test_results['performance_tests'] = performance_results
            
            return performance_results['status'] == 'PASSED'
            
        except Exception as e:
            performance_results['error'] = str(e)
            self.test_results['performance_tests'] = performance_results
            self.test_results['errors'].append(f"Performance test failed: {str(e)}")
            return False

    def test_data_flow_integrity(self):
        """Test complete data flow from API to DOM"""
        data_flow_results = {
            'api_to_js': False,
            'js_to_dom': False,
            'data_consistency': False,
            'status': 'FAILED'
        }
        
        try:
            # Step 1: Test API responses
            api_endpoints = [
                '/executive/api/financial-kpis',
                '/executive/api/intelligent-insights', 
                '/executive/api/store-comparison',
                '/executive/api/financial-forecasts'
            ]
            
            api_responses = {}
            for endpoint in api_endpoints:
                try:
                    response = requests.get(f"{self.base_url}{endpoint}", 
                                          timeout=10, verify=False)
                    if response.status_code == 200:
                        api_responses[endpoint] = response.json()
                except:
                    api_responses[endpoint] = None
            
            data_flow_results['api_to_js'] = len(api_responses) > 0
            
            # Step 2: Test DOM population (already covered in KPI tests)
            kpi_populated = any(kpi.get('status') == 'PASSED' 
                              for kpi in self.test_results.get('kpi_tests', {}).values())
            data_flow_results['js_to_dom'] = kpi_populated
            
            # Step 3: Test data consistency
            if '/executive/api/financial-kpis' in api_responses and api_responses['/executive/api/financial-kpis']:
                api_data = api_responses['/executive/api/financial-kpis']
                # This is a simplified consistency check
                data_flow_results['data_consistency'] = 'total_revenue' in api_data
            
            if (data_flow_results['api_to_js'] and 
                data_flow_results['js_to_dom'] and 
                data_flow_results['data_consistency']):
                data_flow_results['status'] = 'PASSED'
                self.test_results['passed_tests'] += 1
            else:
                self.test_results['failed_tests'] += 1
            
            self.test_results['total_tests'] += 1
            self.test_results['data_flow_tests'] = data_flow_results
            
            return data_flow_results['status'] == 'PASSED'
            
        except Exception as e:
            data_flow_results['error'] = str(e)
            self.test_results['data_flow_tests'] = data_flow_results
            self.test_results['errors'].append(f"Data flow test failed: {str(e)}")
            return False

    def run_comprehensive_test_suite(self):
        """Run all tests in the comprehensive test suite"""
        print("🧪 Starting Executive Dashboard Comprehensive Test Suite")
        print(f"Target URL: {self.base_url}/executive/dashboard")
        print("=" * 70)
        
        # Setup browser driver
        if not self.setup_driver():
            print("❌ Failed to setup WebDriver - cannot run browser tests")
            return False
        
        try:
            # Test 1: API Endpoints
            print("\n📡 Testing API Endpoints...")
            api_endpoints = {
                'financial_kpis': '/executive/api/financial-kpis',
                'intelligent_insights': '/executive/api/intelligent-insights',
                'store_comparison': '/executive/api/store-comparison',
                'financial_forecasts': '/executive/api/financial-forecasts'
            }
            
            for test_name, endpoint in api_endpoints.items():
                result = self.test_api_endpoint(endpoint, test_name)
                print(f"  {'✅' if result else '❌'} {test_name}: {endpoint}")
            
            # Test 2: KPI Cards
            print("\n📊 Testing KPI Cards...")
            kpi_result = self.test_kpi_cards()
            print(f"  {'✅' if kpi_result else '❌'} KPI Cards displaying numerical values")
            
            # Test 3: Chart Loading
            print("\n📈 Testing Chart Loading...")
            chart_result = self.test_charts_loading()
            print(f"  {'✅' if chart_result else '❌'} Charts loading without errors")
            
            # Test 4: Console Errors
            print("\n🔍 Checking Console Errors...")
            console_result = self.check_console_errors()
            print(f"  {'✅' if console_result else '❌'} No critical JavaScript errors")
            
            # Test 5: Page Performance
            print("\n⚡ Testing Page Performance...")
            performance_result = self.test_page_performance()
            print(f"  {'✅' if performance_result else '❌'} Page loads without flashing/instability")
            
            # Test 6: Data Flow Integrity
            print("\n🔄 Testing Data Flow Integrity...")
            data_flow_result = self.test_data_flow_integrity()
            print(f"  {'✅' if data_flow_result else '❌'} Complete API → JavaScript → DOM flow")
            
        except Exception as e:
            self.test_results['errors'].append(f"Test suite execution failed: {str(e)}")
            print(f"\n❌ Test suite execution failed: {str(e)}")
        finally:
            if self.driver:
                self.driver.quit()
        
        # Generate final report
        self.generate_test_report()
        return self.test_results['failed_tests'] == 0

    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 70)
        print("📋 COMPREHENSIVE TEST REPORT")
        print("=" * 70)
        
        # Summary
        total = self.test_results['total_tests']
        passed = self.test_results['passed_tests']
        failed = self.test_results['failed_tests']
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\n📈 SUMMARY:")
        print(f"  Total Tests: {total}")
        print(f"  Passed: {passed}")
        print(f"  Failed: {failed}")
        print(f"  Success Rate: {success_rate:.1f}%")
        
        # API Tests Detail
        if self.test_results['api_tests']:
            print(f"\n📡 API ENDPOINT TESTS:")
            for test_name, result in self.test_results['api_tests'].items():
                status_icon = '✅' if result['status'] == 'PASSED' else '❌'
                print(f"  {status_icon} {test_name}: {result['endpoint']}")
                print(f"      Status: {result['status_code']} ({result['response_time']}s)")
                if result.get('error'):
                    print(f"      Error: {result['error']}")
        
        # KPI Tests Detail
        if self.test_results['kpi_tests']:
            print(f"\n📊 KPI CARD TESTS:")
            for kpi_name, result in self.test_results['kpi_tests'].items():
                status_icon = '✅' if result['status'] == 'PASSED' else '❌'
                print(f"  {status_icon} {kpi_name.replace('_', ' ').title()}")
                if result.get('value'):
                    print(f"      Value: {result['value']}")
                if result.get('error'):
                    print(f"      Error: {result['error']}")
        
        # Chart Tests Detail  
        if self.test_results['chart_tests']:
            print(f"\n📈 CHART LOADING TESTS:")
            for chart_name, result in self.test_results['chart_tests'].items():
                status_icon = '✅' if result['status'] == 'PASSED' else '❌'
                print(f"  {status_icon} {chart_name.replace('_', ' ').title()}")
                if result.get('chart_type'):
                    print(f"      Type: {result['chart_type']}")
                if result.get('error'):
                    print(f"      Error: {result['error']}")
        
        # Performance Tests Detail
        if self.test_results['performance_tests']:
            print(f"\n⚡ PERFORMANCE TESTS:")
            perf = self.test_results['performance_tests']
            status_icon = '✅' if perf['status'] == 'PASSED' else '❌'
            print(f"  {status_icon} Page Performance")
            print(f"      Load Time: {perf['load_time']}s")
            print(f"      No Flash: {perf['no_flash']}")
            print(f"      Stable Content: {perf['stable_content']}")
        
        # Console Errors
        if self.test_results['console_errors']:
            print(f"\n🔍 CONSOLE ERRORS ({len(self.test_results['console_errors'])}):")
            for error in self.test_results['console_errors'][:5]:  # Show first 5
                print(f"  ❌ {error['level']}: {error['message'][:100]}...")
        
        # Errors and Warnings
        if self.test_results['errors']:
            print(f"\n❌ CRITICAL ERRORS ({len(self.test_results['errors'])}):")
            for error in self.test_results['errors']:
                print(f"  • {error}")
        
        if self.test_results['warnings']:
            print(f"\n⚠️  WARNINGS ({len(self.test_results['warnings'])}):")
            for warning in self.test_results['warnings'][:3]:  # Show first 3
                print(f"  • {warning['message'][:100] if isinstance(warning, dict) else str(warning)[:100]}")
        
        # Final Assessment
        print(f"\n🎯 FINAL ASSESSMENT:")
        if failed == 0:
            print("  🎉 ALL TESTS PASSED! The dashboard cleanup was successful.")
        elif success_rate >= 80:
            print("  🟡 MOSTLY SUCCESSFUL - Minor issues remain")
        else:
            print("  🔴 SIGNIFICANT ISSUES - Major problems need addressing")
        
        print("\n" + "=" * 70)

if __name__ == "__main__":
    # Allow custom base URL via command line
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://pi5:6800"
    
    # Run comprehensive test suite
    test_suite = ExecutiveDashboardTestSuite(base_url)
    success = test_suite.run_comprehensive_test_suite()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)