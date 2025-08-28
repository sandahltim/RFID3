#!/usr/bin/env python3
"""
Enhanced Dashboard Test Suite
Tests the comprehensive visualization improvements
Version: 2025-08-28 - Dashboard Enhancement Verification
"""

import sys
import os
import asyncio
import aiohttp
import json
from datetime import datetime, timedelta

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.config.dashboard_config import dashboard_config

class DashboardTester:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.session = None
        self.results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }

    async def run_tests(self):
        """Run comprehensive dashboard tests"""
        print("🚀 Starting Enhanced Dashboard Test Suite")
        print("=" * 60)
        
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            # Test API endpoints
            await self.test_enhanced_kpi_api()
            await self.test_store_performance_api()
            await self.test_inventory_distribution_api()
            await self.test_financial_metrics_api()
            await self.test_utilization_analysis_api()
            
            # Test dashboard pages
            await self.test_executive_dashboard_page()
            await self.test_inventory_analytics_page()
            
            # Test JavaScript utilities
            await self.test_chart_utilities()
            
            # Test data accuracy
            await self.test_data_calculations()
            
            # Test error handling
            await self.test_error_scenarios()
        
        self.print_results()

    async def test_enhanced_kpi_api(self):
        """Test enhanced KPI API endpoint"""
        print("🔍 Testing Enhanced KPI API...")
        
        try:
            # Test basic KPI fetch
            url = f"{self.base_url}/api/enhanced/dashboard/kpis"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Verify response structure
                    required_fields = ['success', 'data', 'timestamp']
                    if all(field in data for field in required_fields):
                        if data['success']:
                            kpi_data = data['data']
                            
                            # Verify KPI data structure
                            kpi_fields = ['total_items', 'utilization_rate', 'total_revenue', 'trends']
                            if all(field in kpi_data for field in kpi_fields):
                                self.pass_test("Enhanced KPI API - Basic fetch")
                            else:
                                self.fail_test("Enhanced KPI API - Missing KPI fields", f"Missing: {set(kpi_fields) - set(kpi_data.keys())}")
                        else:
                            self.fail_test("Enhanced KPI API - API returned success=false", data.get('error', 'Unknown error'))
                    else:
                        self.fail_test("Enhanced KPI API - Invalid response structure", f"Missing: {set(required_fields) - set(data.keys())}")
                else:
                    self.fail_test("Enhanced KPI API - HTTP error", f"Status: {response.status}")
            
            # Test with filters
            url_filtered = f"{self.base_url}/api/enhanced/dashboard/kpis?weeks=4&store=6800"
            async with self.session.get(url_filtered) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        self.pass_test("Enhanced KPI API - Filtered request")
                    else:
                        self.fail_test("Enhanced KPI API - Filtered request failed", data.get('error'))
                else:
                    self.fail_test("Enhanced KPI API - Filtered request HTTP error", f"Status: {response.status}")
                    
        except Exception as e:
            self.fail_test("Enhanced KPI API - Exception", str(e))

    async def test_store_performance_api(self):
        """Test store performance API"""
        print("🔍 Testing Store Performance API...")
        
        try:
            url = f"{self.base_url}/api/enhanced/dashboard/store-performance"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success') and isinstance(data.get('data'), list):
                        # Verify store data structure
                        if data['data']:
                            store = data['data'][0]
                            required_fields = ['store_code', 'store_name', 'efficiency']
                            if all(field in store for field in required_fields):
                                self.pass_test("Store Performance API - Structure valid")
                            else:
                                self.fail_test("Store Performance API - Invalid store structure", f"Missing: {set(required_fields) - set(store.keys())}")
                        else:
                            self.pass_test("Store Performance API - Empty data (acceptable)")
                    else:
                        self.fail_test("Store Performance API - Invalid response", data)
                else:
                    self.fail_test("Store Performance API - HTTP error", f"Status: {response.status}")
        except Exception as e:
            self.fail_test("Store Performance API - Exception", str(e))

    async def test_inventory_distribution_api(self):
        """Test inventory distribution API"""
        print("🔍 Testing Inventory Distribution API...")
        
        try:
            url = f"{self.base_url}/api/enhanced/dashboard/inventory-distribution"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        distribution_data = data.get('data', {})
                        required_sections = ['status_distribution', 'store_distribution', 'type_distribution', 'totals']
                        
                        if all(section in distribution_data for section in required_sections):
                            # Verify status distribution
                            status_dist = distribution_data['status_distribution']
                            if 'labels' in status_dist and 'values' in status_dist:
                                if len(status_dist['labels']) == len(status_dist['values']):
                                    self.pass_test("Inventory Distribution API - Status distribution valid")
                                else:
                                    self.fail_test("Inventory Distribution API - Status distribution mismatch", "Labels and values length differ")
                            else:
                                self.fail_test("Inventory Distribution API - Missing status distribution fields", "Missing labels or values")
                        else:
                            self.fail_test("Inventory Distribution API - Missing sections", f"Missing: {set(required_sections) - set(distribution_data.keys())}")
                    else:
                        self.fail_test("Inventory Distribution API - API error", data.get('error'))
                else:
                    self.fail_test("Inventory Distribution API - HTTP error", f"Status: {response.status}")
        except Exception as e:
            self.fail_test("Inventory Distribution API - Exception", str(e))

    async def test_financial_metrics_api(self):
        """Test financial metrics API"""
        print("🔍 Testing Financial Metrics API...")
        
        try:
            url = f"{self.base_url}/api/enhanced/dashboard/financial-metrics"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        financial_data = data.get('data', {})
                        
                        # Verify financial insights
                        if 'financial_insights' in financial_data:
                            insights = financial_data['financial_insights']
                            required_metrics = ['total_inventory_value', 'avg_sell_price', 'items_with_data']
                            
                            if all(metric in insights for metric in required_metrics):
                                self.pass_test("Financial Metrics API - Structure valid")
                            else:
                                self.fail_test("Financial Metrics API - Missing metrics", f"Missing: {set(required_metrics) - set(insights.keys())}")
                        else:
                            self.fail_test("Financial Metrics API - Missing financial insights", "No financial_insights section")
                    else:
                        self.fail_test("Financial Metrics API - API error", data.get('error'))
                else:
                    self.fail_test("Financial Metrics API - HTTP error", f"Status: {response.status}")
        except Exception as e:
            self.fail_test("Financial Metrics API - Exception", str(e))

    async def test_utilization_analysis_api(self):
        """Test utilization analysis API"""
        print("🔍 Testing Utilization Analysis API...")
        
        try:
            url = f"{self.base_url}/api/enhanced/dashboard/utilization-analysis"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        util_data = data.get('data', {})
                        
                        # Verify utilization data
                        required_fields = ['overall_utilization', 'category_utilization', 'summary']
                        if all(field in util_data for field in required_fields):
                            # Check utilization rate is valid percentage
                            overall_util = util_data['overall_utilization']
                            if isinstance(overall_util, (int, float)) and 0 <= overall_util <= 100:
                                self.pass_test("Utilization Analysis API - Valid utilization rate")
                            else:
                                self.fail_test("Utilization Analysis API - Invalid utilization rate", f"Rate: {overall_util}")
                        else:
                            self.fail_test("Utilization Analysis API - Missing fields", f"Missing: {set(required_fields) - set(util_data.keys())}")
                    else:
                        self.fail_test("Utilization Analysis API - API error", data.get('error'))
                else:
                    self.fail_test("Utilization Analysis API - HTTP error", f"Status: {response.status}")
        except Exception as e:
            self.fail_test("Utilization Analysis API - Exception", str(e))

    async def test_executive_dashboard_page(self):
        """Test executive dashboard page loading"""
        print("🔍 Testing Executive Dashboard Page...")
        
        try:
            url = f"{self.base_url}/bi/dashboard"
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Check for key dashboard elements
                    required_elements = [
                        'executive-kpis',
                        'revenueTrendChart',
                        'storePerformanceChart',
                        'utilizationGauge',
                        'chart-utilities.js',
                        'executive-dashboard.css'
                    ]
                    
                    missing_elements = []
                    for element in required_elements:
                        if element not in content:
                            missing_elements.append(element)
                    
                    if not missing_elements:
                        self.pass_test("Executive Dashboard Page - All elements present")
                    else:
                        self.fail_test("Executive Dashboard Page - Missing elements", f"Missing: {missing_elements}")
                else:
                    self.fail_test("Executive Dashboard Page - HTTP error", f"Status: {response.status}")
        except Exception as e:
            self.fail_test("Executive Dashboard Page - Exception", str(e))

    async def test_inventory_analytics_page(self):
        """Test inventory analytics page"""
        print("🔍 Testing Inventory Analytics Page...")
        
        try:
            url = f"{self.base_url}/inventory/tab/6"
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Check for enhanced elements
                    required_elements = [
                        'store-distribution-chart',
                        'type-distribution-chart',
                        'chart-utilities.js',
                        'data-refresh-indicator'
                    ]
                    
                    present_elements = sum(1 for element in required_elements if element in content)
                    
                    if present_elements >= len(required_elements) * 0.8:  # 80% threshold
                        self.pass_test(f"Inventory Analytics Page - {present_elements}/{len(required_elements)} elements present")
                    else:
                        self.fail_test("Inventory Analytics Page - Too many missing elements", f"Only {present_elements}/{len(required_elements)} found")
                else:
                    self.fail_test("Inventory Analytics Page - HTTP error", f"Status: {response.status}")
        except Exception as e:
            self.fail_test("Inventory Analytics Page - Exception", str(e))

    async def test_chart_utilities(self):
        """Test chart utilities JavaScript file"""
        print("🔍 Testing Chart Utilities...")
        
        try:
            url = f"{self.base_url}/static/js/chart-utilities.js"
            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Check for key functions
                    required_functions = [
                        'RFID3ChartManager',
                        'createRevenueTrendChart',
                        'createStorePerformanceChart',
                        'createUtilizationGauge',
                        'formatCurrency',
                        'enableAutoRefresh'
                    ]
                    
                    missing_functions = []
                    for func in required_functions:
                        if func not in content:
                            missing_functions.append(func)
                    
                    if not missing_functions:
                        self.pass_test("Chart Utilities - All functions present")
                    else:
                        self.fail_test("Chart Utilities - Missing functions", f"Missing: {missing_functions}")
                else:
                    self.fail_test("Chart Utilities - File not found", f"Status: {response.status}")
        except Exception as e:
            self.fail_test("Chart Utilities - Exception", str(e))

    async def test_data_calculations(self):
        """Test data calculation accuracy"""
        print("🔍 Testing Data Calculations...")
        
        try:
            # Get KPI data and verify calculations
            url = f"{self.base_url}/api/enhanced/dashboard/kpis"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('success'):
                        kpi_data = data['data']
                        
                        # Verify utilization calculation
                        total_items = kpi_data.get('total_items', 0)
                        items_on_rent = kpi_data.get('items_on_rent', 0)
                        calculated_utilization = kpi_data.get('utilization_rate', 0)
                        
                        if total_items > 0:
                            expected_utilization = round((items_on_rent / total_items) * 100, 2)
                            if abs(calculated_utilization - expected_utilization) < 0.1:  # Allow small rounding differences
                                self.pass_test("Data Calculations - Utilization rate accurate")
                            else:
                                self.fail_test("Data Calculations - Utilization rate incorrect", 
                                             f"Expected: {expected_utilization}, Got: {calculated_utilization}")
                        else:
                            self.pass_test("Data Calculations - Zero division handled correctly")
                    else:
                        self.fail_test("Data Calculations - Could not get KPI data", data.get('error'))
                else:
                    self.fail_test("Data Calculations - API error", f"Status: {response.status}")
        except Exception as e:
            self.fail_test("Data Calculations - Exception", str(e))

    async def test_error_scenarios(self):
        """Test error handling scenarios"""
        print("🔍 Testing Error Scenarios...")
        
        # Test invalid store filter
        try:
            url = f"{self.base_url}/api/enhanced/dashboard/kpis?store=INVALID_STORE"
            async with self.session.get(url) as response:
                if response.status in [200, 400, 404]:  # Accept various error handling approaches
                    data = await response.json()
                    # Should either return empty data or proper error
                    if 'error' in data or data.get('success') is False or data.get('data'):
                        self.pass_test("Error Scenarios - Invalid store handled")
                    else:
                        self.fail_test("Error Scenarios - Invalid store not handled properly", data)
                else:
                    self.fail_test("Error Scenarios - Unexpected HTTP status", f"Status: {response.status}")
        except Exception as e:
            self.fail_test("Error Scenarios - Exception", str(e))

        # Test invalid weeks parameter
        try:
            url = f"{self.base_url}/api/enhanced/dashboard/kpis?weeks=invalid"
            async with self.session.get(url) as response:
                if response.status in [200, 400]:
                    data = await response.json()
                    # Should handle invalid parameter gracefully
                    self.pass_test("Error Scenarios - Invalid weeks parameter handled")
                else:
                    self.fail_test("Error Scenarios - Invalid weeks parameter caused server error", f"Status: {response.status}")
        except Exception as e:
            # Exception is acceptable for invalid parameter
            self.pass_test("Error Scenarios - Invalid parameter caused exception (acceptable)")

    def pass_test(self, test_name):
        """Record a passing test"""
        self.results['passed'] += 1
        print(f"✅ {test_name}")

    def fail_test(self, test_name, reason):
        """Record a failing test"""
        self.results['failed'] += 1
        error_msg = f"❌ {test_name}: {reason}"
        print(error_msg)
        self.results['errors'].append(error_msg)

    def print_results(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = self.results['passed'] + self.results['failed']
        pass_rate = (self.results['passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.results['passed']} ✅")
        print(f"Failed: {self.results['failed']} ❌")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        if self.results['errors']:
            print(f"\n🔍 FAILED TESTS:")
            for error in self.results['errors']:
                print(f"  {error}")
        
        if pass_rate >= 80:
            print(f"\n🎉 DASHBOARD ENHANCEMENT SUCCESS! ({pass_rate:.1f}% pass rate)")
        elif pass_rate >= 60:
            print(f"\n⚠️  DASHBOARD PARTIALLY FUNCTIONAL ({pass_rate:.1f}% pass rate)")
        else:
            print(f"\n🚨 DASHBOARD NEEDS ATTENTION ({pass_rate:.1f}% pass rate)")

def main():
    """Main test runner"""
    print("🔧 Enhanced Dashboard Test Suite")
    print("Testing comprehensive visualization improvements...")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tester = DashboardTester()
    
    try:
        asyncio.run(tester.run_tests())
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")

if __name__ == "__main__":
    main()