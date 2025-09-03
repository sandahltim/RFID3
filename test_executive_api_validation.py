#!/usr/bin/env python3
"""
Executive Dashboard API Validation Test

Focused test suite for API endpoints and data validation without browser automation.
This tests the backend data flow that feeds the dashboard.

Author: Testing Specialist  
Date: 2025-09-03
"""

import requests
import json
import time
import sys
import urllib3
from datetime import datetime

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ExecutiveAPITestSuite:
    def __init__(self, base_url="https://pi5:6800"):
        self.base_url = base_url
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'errors': [],
            'api_tests': {},
            'data_validation': {}
        }
    
    def test_api_endpoint(self, endpoint, test_name, expected_fields=None):
        """Test individual API endpoint for valid response and data structure"""
        self.test_results['total_tests'] += 1
        test_result = {
            'endpoint': endpoint,
            'status': 'FAILED',
            'response_time': 0,
            'status_code': None,
            'data_valid': False,
            'data_sample': None,
            'validation_details': {},
            'error': None
        }
        
        print(f"  Testing {test_name}: {endpoint}")
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}{endpoint}", 
                                  timeout=15, 
                                  verify=False)
            test_result['response_time'] = round(time.time() - start_time, 3)
            test_result['status_code'] = response.status_code
            
            print(f"    Status Code: {response.status_code} ({test_result['response_time']}s)")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    test_result['data_sample'] = self.get_data_sample(data)
                    
                    # Validate data structure
                    validation = self.validate_api_response(endpoint, data, expected_fields)
                    test_result['data_valid'] = validation['valid']
                    test_result['validation_details'] = validation
                    
                    if test_result['data_valid']:
                        test_result['status'] = 'PASSED'
                        self.test_results['passed_tests'] += 1
                        print(f"    ✅ Data validation passed")
                    else:
                        test_result['error'] = f"Data validation failed: {validation['issues']}"
                        self.test_results['failed_tests'] += 1
                        print(f"    ❌ Data validation failed: {validation['issues']}")
                        
                except json.JSONDecodeError as e:
                    test_result['error'] = f'Invalid JSON response: {str(e)}'
                    self.test_results['failed_tests'] += 1
                    print(f"    ❌ Invalid JSON: {str(e)}")
            else:
                test_result['error'] = f'HTTP {response.status_code}: {response.text[:200]}'
                self.test_results['failed_tests'] += 1
                print(f"    ❌ HTTP Error: {response.status_code}")
                
        except requests.RequestException as e:
            test_result['error'] = f'Request failed: {str(e)}'
            self.test_results['failed_tests'] += 1
            print(f"    ❌ Request failed: {str(e)}")
        
        self.test_results['api_tests'][test_name] = test_result
        return test_result['status'] == 'PASSED'

    def get_data_sample(self, data, max_length=200):
        """Get a sample of the data for display purposes"""
        if isinstance(data, dict):
            sample = {}
            for key, value in list(data.items())[:3]:  # First 3 keys
                if isinstance(value, (str, int, float, bool)):
                    sample[key] = value
                elif isinstance(value, list) and len(value) > 0:
                    sample[key] = f"[{len(value)} items] {type(value[0]).__name__}"
                elif isinstance(value, dict):
                    sample[key] = f"{{dict with {len(value)} keys}}"
                else:
                    sample[key] = str(type(value).__name__)
            return sample
        elif isinstance(data, list):
            return f"[{len(data)} items]"
        else:
            return str(data)[:max_length]

    def validate_api_response(self, endpoint, data, expected_fields=None):
        """Validate API response data structure and content"""
        validation = {
            'valid': False,
            'issues': [],
            'structure_valid': False,
            'data_quality': {},
            'field_validation': {}
        }
        
        if not isinstance(data, dict):
            validation['issues'].append('Response is not a JSON object')
            return validation
        
        validation['structure_valid'] = True
        
        # Endpoint-specific validation
        if '/financial-kpis' in endpoint:
            required_fields = ['total_revenue', 'yoy_growth', 'equipment_utilization', 'business_health']
            validation['field_validation'] = self.validate_kpi_fields(data, required_fields)
            
        elif '/intelligent-insights' in endpoint:
            if 'insights' not in data:
                validation['issues'].append('Missing insights field')
            elif not isinstance(data['insights'], list):
                validation['issues'].append('Insights should be a list')
            else:
                validation['field_validation']['insights'] = {
                    'present': True,
                    'type': 'list',
                    'count': len(data['insights'])
                }
            
        elif '/store-comparison' in endpoint:
            if 'stores' not in data:
                validation['issues'].append('Missing stores field')
            elif not isinstance(data['stores'], list):
                validation['issues'].append('Stores should be a list')
            else:
                validation['field_validation']['stores'] = {
                    'present': True,
                    'type': 'list', 
                    'count': len(data['stores'])
                }
                
        elif '/financial-forecasts' in endpoint:
            if 'forecast' not in data:
                validation['issues'].append('Missing forecast field')
            elif not isinstance(data['forecast'], list):
                validation['issues'].append('Forecast should be a list')
            else:
                validation['field_validation']['forecast'] = {
                    'present': True,
                    'type': 'list',
                    'count': len(data['forecast'])
                }
        
        # Check for custom expected fields
        if expected_fields:
            for field in expected_fields:
                if field not in data:
                    validation['issues'].append(f'Missing required field: {field}')
                else:
                    validation['field_validation'][field] = {
                        'present': True,
                        'value': data[field],
                        'type': type(data[field]).__name__
                    }
        
        # Data quality checks
        validation['data_quality'] = self.check_data_quality(data)
        
        # Overall validation
        validation['valid'] = (len(validation['issues']) == 0 and 
                             validation['structure_valid'])
        
        return validation

    def validate_kpi_fields(self, data, required_fields):
        """Validate KPI-specific fields for proper numerical values"""
        field_validation = {}
        
        for field in required_fields:
            field_validation[field] = {
                'present': field in data,
                'valid_number': False,
                'value': None,
                'issues': []
            }
            
            if field in data:
                value = data[field]
                field_validation[field]['value'] = value
                
                # Check if it's a valid number (not NaN, null, or string "Loading")
                if isinstance(value, (int, float)) and not (isinstance(value, float) and str(value).lower() == 'nan'):
                    field_validation[field]['valid_number'] = True
                elif isinstance(value, str):
                    if value.lower() in ['nan', 'loading', 'loading...', '--', '']:
                        field_validation[field]['issues'].append(f'Invalid placeholder value: {value}')
                    else:
                        # Try to parse as number
                        try:
                            numeric_value = float(value.replace(',', '').replace('$', '').replace('%', ''))
                            field_validation[field]['valid_number'] = True
                            field_validation[field]['numeric_value'] = numeric_value
                        except (ValueError, AttributeError):
                            field_validation[field]['issues'].append(f'Cannot parse as number: {value}')
                else:
                    field_validation[field]['issues'].append(f'Unexpected data type: {type(value).__name__}')
            else:
                field_validation[field]['issues'].append('Field missing from response')
        
        return field_validation

    def check_data_quality(self, data):
        """Check overall data quality metrics"""
        quality = {
            'empty_values': 0,
            'null_values': 0,
            'zero_values': 0,
            'total_fields': 0,
            'quality_score': 0
        }
        
        def check_value(value):
            quality['total_fields'] += 1
            if value is None:
                quality['null_values'] += 1
            elif value == '' or value == []:
                quality['empty_values'] += 1
            elif value == 0:
                quality['zero_values'] += 1
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (list, dict)):
                    if len(value) == 0:
                        check_value([])
                    # Don't recurse into complex structures for this basic check
                else:
                    check_value(value)
        
        # Calculate quality score
        if quality['total_fields'] > 0:
            issues = quality['empty_values'] + quality['null_values']
            quality['quality_score'] = max(0, (quality['total_fields'] - issues) / quality['total_fields'] * 100)
        
        return quality

    def test_dashboard_accessibility(self):
        """Test if the dashboard page is accessible"""
        self.test_results['total_tests'] += 1
        
        print(f"  Testing Dashboard Page Accessibility")
        
        try:
            response = requests.get(f"{self.base_url}/executive/dashboard", 
                                  timeout=10, 
                                  verify=False)
            
            if response.status_code == 200:
                # Basic checks for HTML content
                content = response.text.lower()
                has_html = '<html' in content or '<!doctype html' in content
                has_dashboard = 'dashboard' in content or 'executive' in content
                
                if has_html and has_dashboard:
                    print(f"    ✅ Dashboard page accessible (HTML content detected)")
                    self.test_results['passed_tests'] += 1
                    return True
                else:
                    print(f"    ❌ Dashboard page accessible but content suspicious")
                    self.test_results['failed_tests'] += 1
                    return False
            else:
                print(f"    ❌ Dashboard page not accessible: HTTP {response.status_code}")
                self.test_results['failed_tests'] += 1
                return False
                
        except requests.RequestException as e:
            print(f"    ❌ Dashboard page request failed: {str(e)}")
            self.test_results['failed_tests'] += 1
            return False

    def run_api_test_suite(self):
        """Run the complete API test suite"""
        print("🧪 Starting Executive Dashboard API Validation Test Suite")
        print(f"Target URL: {self.base_url}")
        print("=" * 70)
        
        # Test 0: Dashboard Page Accessibility
        print("\n🌐 Testing Dashboard Page Accessibility...")
        self.test_dashboard_accessibility()
        
        # Test 1: API Endpoints
        print("\n📡 Testing API Endpoints...")
        
        api_tests = [
            {
                'name': 'Financial KPIs',
                'endpoint': '/executive/api/financial-kpis',
                'expected_fields': ['total_revenue', 'yoy_growth', 'equipment_utilization', 'business_health']
            },
            {
                'name': 'Intelligent Insights', 
                'endpoint': '/executive/api/intelligent-insights',
                'expected_fields': ['insights']
            },
            {
                'name': 'Store Comparison',
                'endpoint': '/executive/api/store-comparison', 
                'expected_fields': ['stores']
            },
            {
                'name': 'Financial Forecasts',
                'endpoint': '/executive/api/financial-forecasts',
                'expected_fields': ['forecast']
            }
        ]
        
        for test_config in api_tests:
            self.test_api_endpoint(
                test_config['endpoint'], 
                test_config['name'],
                test_config.get('expected_fields')
            )
            print()  # Add spacing between tests
        
        # Generate final report
        self.generate_api_test_report()
        
        return self.test_results['failed_tests'] == 0

    def generate_api_test_report(self):
        """Generate comprehensive API test report"""
        print("\n" + "=" * 70)
        print("📋 API VALIDATION TEST REPORT")
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
        
        # Detailed API Results
        if self.test_results['api_tests']:
            print(f"\n📡 API ENDPOINT DETAILED RESULTS:")
            for test_name, result in self.test_results['api_tests'].items():
                status_icon = '✅' if result['status'] == 'PASSED' else '❌'
                print(f"\n  {status_icon} {test_name}")
                print(f"      Endpoint: {result['endpoint']}")
                print(f"      Status Code: {result['status_code']}")
                print(f"      Response Time: {result['response_time']}s")
                
                if result.get('data_sample'):
                    print(f"      Data Sample: {result['data_sample']}")
                
                # Field validation details
                if result.get('validation_details', {}).get('field_validation'):
                    print(f"      Field Validation:")
                    for field, validation in result['validation_details']['field_validation'].items():
                        field_icon = '✅' if validation.get('valid_number', validation.get('present', False)) else '❌'
                        print(f"        {field_icon} {field}: {validation.get('value', 'N/A')}")
                        if validation.get('issues'):
                            for issue in validation['issues']:
                                print(f"            Issue: {issue}")
                
                # Data quality
                if result.get('validation_details', {}).get('data_quality'):
                    quality = result['validation_details']['data_quality']
                    print(f"      Data Quality Score: {quality.get('quality_score', 0):.1f}%")
                
                if result.get('error'):
                    print(f"      Error: {result['error']}")
        
        # Critical Issues Summary
        critical_issues = []
        kpi_issues = []
        
        for test_name, result in self.test_results['api_tests'].items():
            if result['status'] == 'FAILED':
                critical_issues.append(f"{test_name}: {result.get('error', 'Unknown error')}")
            
            # Special check for KPI endpoint
            if 'financial-kpis' in result['endpoint'] and result.get('validation_details'):
                field_validation = result['validation_details'].get('field_validation', {})
                for field, validation in field_validation.items():
                    if not validation.get('valid_number', False):
                        kpi_issues.append(f"{field}: {validation.get('value', 'N/A')} - {validation.get('issues', ['Invalid'])}")
        
        if critical_issues:
            print(f"\n❌ CRITICAL API ISSUES:")
            for issue in critical_issues:
                print(f"  • {issue}")
        
        if kpi_issues:
            print(f"\n⚠️  KPI DATA ISSUES (These cause 'NaN' in dashboard):")
            for issue in kpi_issues:
                print(f"  • {issue}")
        
        # Recommendations
        print(f"\n🎯 RECOMMENDATIONS:")
        if failed == 0:
            print("  🎉 All API endpoints are working correctly!")
            print("  💡 If dashboard still shows 'NaN', check JavaScript console for client-side errors")
        elif kpi_issues:
            print("  🔧 Fix KPI data quality issues - these directly cause 'NaN' values in dashboard")
            print("  📊 Check database queries and data processing logic in manager_analytics_service.py")
        elif critical_issues:
            print("  🚨 Fix API endpoint errors first - these prevent data from reaching the dashboard")
            print("  🔍 Check Flask routes and error handling in executive_dashboard.py")
        
        # Next Steps
        print(f"\n📋 NEXT STEPS:")
        if failed > 0:
            print("  1. Review failed API endpoints and fix backend issues")
            print("  2. Test individual service functions in manager_analytics_service.py")
            print("  3. Check database connectivity and data availability")
        print("  4. Run browser-based tests to validate frontend integration")
        print("  5. Check JavaScript console in browser for client-side errors")
        
        print("\n" + "=" * 70)

if __name__ == "__main__":
    # Allow custom base URL via command line
    base_url = sys.argv[1] if len(sys.argv) > 1 else "https://pi5:6800"
    
    # Run API test suite
    test_suite = ExecutiveAPITestSuite(base_url)
    success = test_suite.run_api_test_suite()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)