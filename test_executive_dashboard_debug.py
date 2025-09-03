#!/usr/bin/env python3
"""
Executive Dashboard Debug Test Suite

This comprehensive test suite validates the complete data flow and identifies
any remaining issues that might cause KPIs to show "NaN" or "Loading..."

Author: Testing Specialist
Date: 2025-09-03
"""

import requests
import json
import time
import urllib3
from datetime import datetime

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ExecutiveDashboardDebugger:
    def __init__(self, base_url="https://pi5:6800"):
        self.base_url = base_url
        self.debug_results = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_checks': 0,
                'passed_checks': 0,
                'failed_checks': 0,
                'warnings': 0
            },
            'api_health': {},
            'data_integrity': {},
            'frontend_validation': {},
            'recommendations': []
        }
    
    def check_api_health(self):
        """Check all API endpoints for proper responses"""
        print("🔍 Checking API Health...")
        
        endpoints = {
            'dashboard_page': '/executive/dashboard',
            'financial_kpis': '/executive/api/financial-kpis',
            'intelligent_insights': '/executive/api/intelligent-insights', 
            'store_comparison': '/executive/api/store-comparison',
            'financial_forecasts': '/executive/api/financial-forecasts'
        }
        
        for name, endpoint in endpoints.items():
            self.debug_results['summary']['total_checks'] += 1
            
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", 
                                      timeout=15, verify=False)
                response_time = round(time.time() - start_time, 3)
                
                result = {
                    'endpoint': endpoint,
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'content_length': len(response.content),
                    'healthy': response.status_code == 200
                }
                
                if response.status_code == 200:
                    if 'api' in endpoint:
                        try:
                            data = response.json()
                            result['is_json'] = True
                            result['has_success_field'] = 'success' in data
                            result['success_value'] = data.get('success', False)
                            result['data_keys'] = list(data.keys()) if isinstance(data, dict) else []
                        except json.JSONDecodeError:
                            result['is_json'] = False
                            result['error'] = 'Invalid JSON response'
                            result['healthy'] = False
                    else:
                        result['is_html'] = '<html' in response.text.lower()
                
                status_icon = '✅' if result['healthy'] else '❌'
                print(f"  {status_icon} {name}: {response.status_code} ({response_time}s)")
                
                if result['healthy']:
                    self.debug_results['summary']['passed_checks'] += 1
                else:
                    self.debug_results['summary']['failed_checks'] += 1
                    
                self.debug_results['api_health'][name] = result
                
            except Exception as e:
                print(f"  ❌ {name}: FAILED - {str(e)}")
                self.debug_results['api_health'][name] = {
                    'endpoint': endpoint,
                    'healthy': False,
                    'error': str(e)
                }
                self.debug_results['summary']['failed_checks'] += 1
    
    def validate_kpi_data_integrity(self):
        """Validate the integrity of KPI data"""
        print("\n📊 Validating KPI Data Integrity...")
        
        if 'financial_kpis' not in self.debug_results['api_health']:
            print("  ❌ No KPI data available for validation")
            return
        
        kpi_health = self.debug_results['api_health']['financial_kpis']
        if not kpi_health.get('healthy'):
            print("  ❌ KPI API is not healthy")
            return
        
        try:
            response = requests.get(f"{self.base_url}/executive/api/financial-kpis", 
                                  timeout=10, verify=False)
            data = response.json()
            
            integrity_check = {
                'api_structure_valid': False,
                'required_sections': {},
                'kpi_values': {},
                'data_quality_score': 0,
                'issues': []
            }
            
            # Check required sections
            required_sections = ['revenue_metrics', 'store_metrics', 'operational_health']
            for section in required_sections:
                self.debug_results['summary']['total_checks'] += 1
                
                if section in data:
                    integrity_check['required_sections'][section] = True
                    self.debug_results['summary']['passed_checks'] += 1
                    print(f"  ✅ {section} section present")
                else:
                    integrity_check['required_sections'][section] = False
                    integrity_check['issues'].append(f'Missing section: {section}')
                    self.debug_results['summary']['failed_checks'] += 1
                    print(f"  ❌ {section} section missing")
            
            # Validate specific KPI values
            kpi_mappings = {
                'total_revenue': ('revenue_metrics', 'current_3wk_avg'),
                'yoy_growth': ('revenue_metrics', 'yoy_growth'),
                'equipment_utilization': ('store_metrics', 'utilization_avg'),
                'business_health': ('operational_health', 'health_score')
            }
            
            for kpi_name, (section, field) in kpi_mappings.items():
                self.debug_results['summary']['total_checks'] += 1
                
                if section in data and field in data[section]:
                    value = data[section][field]
                    integrity_check['kpi_values'][kpi_name] = {
                        'raw_value': value,
                        'valid': isinstance(value, (int, float)) and not (isinstance(value, float) and str(value).lower() == 'nan'),
                        'formatted_value': self.format_kpi_value(kpi_name, value)
                    }
                    
                    if integrity_check['kpi_values'][kpi_name]['valid']:
                        self.debug_results['summary']['passed_checks'] += 1
                        print(f"  ✅ {kpi_name}: {integrity_check['kpi_values'][kpi_name]['formatted_value']}")
                    else:
                        integrity_check['issues'].append(f'Invalid {kpi_name} value: {value}')
                        self.debug_results['summary']['failed_checks'] += 1
                        print(f"  ❌ {kpi_name}: Invalid value {value}")
                else:
                    integrity_check['kpi_values'][kpi_name] = {'valid': False, 'missing': True}
                    integrity_check['issues'].append(f'Missing KPI: {kpi_name} ({section}.{field})')
                    self.debug_results['summary']['failed_checks'] += 1
                    print(f"  ❌ {kpi_name}: Missing from {section}.{field}")
            
            # Calculate overall data quality score
            valid_kpis = sum(1 for kpi in integrity_check['kpi_values'].values() if kpi.get('valid', False))
            total_kpis = len(kpi_mappings)
            integrity_check['data_quality_score'] = (valid_kpis / total_kpis * 100) if total_kpis > 0 else 0
            
            integrity_check['api_structure_valid'] = all(integrity_check['required_sections'].values())
            
            print(f"\n  📈 Data Quality Score: {integrity_check['data_quality_score']:.1f}%")
            
            self.debug_results['data_integrity'] = integrity_check
            
        except Exception as e:
            print(f"  ❌ Data integrity check failed: {str(e)}")
            self.debug_results['data_integrity'] = {'error': str(e)}
    
    def format_kpi_value(self, kpi_name, value):
        """Format KPI value for display"""
        if not isinstance(value, (int, float)):
            return str(value)
        
        if kpi_name == 'total_revenue':
            return f'${value:,.0f}'
        elif kpi_name in ['yoy_growth', 'equipment_utilization']:
            return f'{value:.1f}%'
        elif kpi_name == 'business_health':
            return f'{value:.0f}'
        else:
            return str(value)
    
    def test_frontend_javascript_compatibility(self):
        """Test JavaScript/frontend compatibility"""
        print("\n🌐 Testing Frontend JavaScript Compatibility...")
        
        # Check if the dashboard page loads and has expected elements
        self.debug_results['summary']['total_checks'] += 1
        
        try:
            response = requests.get(f"{self.base_url}/executive/dashboard", 
                                  timeout=10, verify=False)
            
            if response.status_code == 200:
                html_content = response.text
                
                frontend_check = {
                    'page_loads': True,
                    'has_kpi_elements': False,
                    'has_javascript': False,
                    'kpi_element_ids': [],
                    'javascript_functions': []
                }
                
                # Check for KPI elements
                kpi_ids = ['revenueKPI', 'growthKPI', 'utilizationKPI', 'healthKPI']
                found_kpi_ids = []
                for kpi_id in kpi_ids:
                    if f'id="{kpi_id}"' in html_content:
                        found_kpi_ids.append(kpi_id)
                
                frontend_check['kpi_element_ids'] = found_kpi_ids
                frontend_check['has_kpi_elements'] = len(found_kpi_ids) == len(kpi_ids)
                
                # Check for key JavaScript functions
                js_functions = ['updateKPIDisplays', 'loadFinancialKPIs', 'formatCurrency']
                found_js_functions = []
                for func in js_functions:
                    if func in html_content:
                        found_js_functions.append(func)
                
                frontend_check['javascript_functions'] = found_js_functions
                frontend_check['has_javascript'] = len(found_js_functions) > 0
                
                # Check for Chart.js and other dependencies
                frontend_check['has_chartjs'] = 'chart.js' in html_content.lower()
                frontend_check['has_countup'] = 'countup' in html_content.lower()
                
                if frontend_check['has_kpi_elements'] and frontend_check['has_javascript']:
                    print("  ✅ Frontend elements and JavaScript found")
                    self.debug_results['summary']['passed_checks'] += 1
                else:
                    print(f"  ❌ Frontend issues - KPI elements: {frontend_check['has_kpi_elements']}, JavaScript: {frontend_check['has_javascript']}")
                    self.debug_results['summary']['failed_checks'] += 1
                
                self.debug_results['frontend_validation'] = frontend_check
                
            else:
                print(f"  ❌ Dashboard page failed to load: HTTP {response.status_code}")
                self.debug_results['summary']['failed_checks'] += 1
                
        except Exception as e:
            print(f"  ❌ Frontend compatibility test failed: {str(e)}")
            self.debug_results['summary']['failed_checks'] += 1
    
    def generate_debug_recommendations(self):
        """Generate specific recommendations based on findings"""
        recommendations = []
        
        # API Health recommendations
        failed_apis = [name for name, result in self.debug_results['api_health'].items() 
                      if not result.get('healthy', False)]
        if failed_apis:
            recommendations.append({
                'category': 'API Health',
                'priority': 'HIGH',
                'issue': f'Failed APIs: {", ".join(failed_apis)}',
                'action': 'Fix API endpoints and ensure they return proper responses'
            })
        
        # Data Integrity recommendations
        if 'data_integrity' in self.debug_results:
            data_issues = self.debug_results['data_integrity'].get('issues', [])
            if data_issues:
                recommendations.append({
                    'category': 'Data Integrity',
                    'priority': 'HIGH',
                    'issue': f'{len(data_issues)} data issues found',
                    'action': 'Fix data processing in manager_analytics_service.py',
                    'details': data_issues[:3]  # Show first 3 issues
                })
            
            quality_score = self.debug_results['data_integrity'].get('data_quality_score', 0)
            if quality_score < 80:
                recommendations.append({
                    'category': 'Data Quality',
                    'priority': 'MEDIUM',
                    'issue': f'Data quality score: {quality_score:.1f}%',
                    'action': 'Improve data validation and error handling'
                })
        
        # Frontend recommendations
        if 'frontend_validation' in self.debug_results:
            frontend = self.debug_results['frontend_validation']
            if not frontend.get('has_kpi_elements', False):
                recommendations.append({
                    'category': 'Frontend',
                    'priority': 'HIGH',
                    'issue': 'Missing KPI elements in HTML',
                    'action': 'Ensure KPI element IDs exist: revenueKPI, growthKPI, utilizationKPI, healthKPI'
                })
            
            if not frontend.get('has_javascript', False):
                recommendations.append({
                    'category': 'Frontend',
                    'priority': 'HIGH',
                    'issue': 'Missing JavaScript functions',
                    'action': 'Ensure updateKPIDisplays and loadFinancialKPIs functions exist'
                })
        
        self.debug_results['recommendations'] = recommendations
        
        # Generate success recommendations if everything looks good
        if not recommendations:
            recommendations.append({
                'category': 'Success',
                'priority': 'INFO',
                'issue': 'All checks passed',
                'action': 'Dashboard should be working correctly. Check browser console for any client-side errors.'
            })
    
    def run_comprehensive_debug(self):
        """Run complete debug suite"""
        print("🐛 EXECUTIVE DASHBOARD COMPREHENSIVE DEBUG SUITE")
        print("=" * 60)
        print("This debug suite identifies all issues preventing proper KPI display.\n")
        
        self.check_api_health()
        self.validate_kpi_data_integrity()
        self.test_frontend_javascript_compatibility()
        self.generate_debug_recommendations()
        
        self.print_debug_report()
    
    def print_debug_report(self):
        """Print comprehensive debug report"""
        print("\n" + "=" * 60)
        print("🐛 DEBUG REPORT")
        print("=" * 60)
        
        # Summary
        summary = self.debug_results['summary']
        success_rate = (summary['passed_checks'] / summary['total_checks'] * 100) if summary['total_checks'] > 0 else 0
        
        print(f"\n📊 SUMMARY:")
        print(f"  Total Checks: {summary['total_checks']}")
        print(f"  Passed: {summary['passed_checks']}")
        print(f"  Failed: {summary['failed_checks']}")
        print(f"  Success Rate: {success_rate:.1f}%")
        
        # Detailed findings
        if success_rate < 100:
            print(f"\n❌ ISSUES FOUND:")
            
            # API Health issues
            failed_apis = [(name, result) for name, result in self.debug_results['api_health'].items() 
                          if not result.get('healthy', False)]
            if failed_apis:
                print(f"  🔌 API Health Issues:")
                for name, result in failed_apis:
                    print(f"    • {name}: {result.get('error', 'Unknown error')}")
            
            # Data integrity issues
            if 'data_integrity' in self.debug_results:
                issues = self.debug_results['data_integrity'].get('issues', [])
                if issues:
                    print(f"  📊 Data Integrity Issues:")
                    for issue in issues[:5]:  # Show first 5
                        print(f"    • {issue}")
        
        # Valid KPI values (if any)
        if 'data_integrity' in self.debug_results and 'kpi_values' in self.debug_results['data_integrity']:
            valid_kpis = [(name, kpi) for name, kpi in self.debug_results['data_integrity']['kpi_values'].items() 
                         if kpi.get('valid', False)]
            if valid_kpis:
                print(f"\n✅ VALID KPI VALUES:")
                for name, kpi in valid_kpis:
                    print(f"  • {name}: {kpi.get('formatted_value', kpi.get('raw_value', 'N/A'))}")
        
        # Recommendations
        if self.debug_results['recommendations']:
            print(f"\n🎯 RECOMMENDATIONS:")
            for i, rec in enumerate(self.debug_results['recommendations'], 1):
                priority_icon = {'HIGH': '🚨', 'MEDIUM': '⚠️', 'LOW': '💡', 'INFO': 'ℹ️'}.get(rec['priority'], '•')
                print(f"  {priority_icon} {rec['category']} ({rec['priority']}): {rec['action']}")
                if rec.get('details'):
                    for detail in rec['details']:
                        print(f"      - {detail}")
        
        # Next steps
        print(f"\n📋 IMMEDIATE NEXT STEPS:")
        if success_rate >= 90:
            print("  1. ✅ Backend systems are healthy")
            print("  2. 🌐 Open browser developer console at https://pi5:6800/executive/dashboard")
            print("  3. 🔍 Look for JavaScript errors or failed API calls")
            print("  4. 🧪 Run the test JavaScript snippet provided earlier")
        else:
            print("  1. 🔧 Fix API endpoint issues first")
            print("  2. 📊 Validate data processing in backend services")
            print("  3. 🌐 Test frontend after backend issues are resolved")
        
        print("\n" + "=" * 60)
        
        return success_rate >= 90

if __name__ == "__main__":
    debugger = ExecutiveDashboardDebugger()
    is_healthy = debugger.run_comprehensive_debug()
    
    if is_healthy:
        print("\n🎉 Dashboard appears to be healthy - check browser console for client-side issues")
    else:
        print("\n🚨 Critical issues found - address backend problems first")
    
    exit(0 if is_healthy else 1)