#!/usr/bin/env python3
"""
Executive Dashboard Data Mapping Analysis & Correction Test

This test identifies the mismatch between API responses and frontend expectations,
then provides specific fixes for the data flow issues causing "NaN" values.

Author: Testing Specialist
Date: 2025-09-03
"""

import requests
import json
import urllib3

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DataMappingAnalyzer:
    def __init__(self, base_url="https://pi5:6800"):
        self.base_url = base_url
        self.api_responses = {}
        self.mapping_issues = {}
        
    def fetch_api_responses(self):
        """Fetch all API responses to analyze structure"""
        endpoints = {
            'financial_kpis': '/executive/api/financial-kpis',
            'intelligent_insights': '/executive/api/intelligent-insights',
            'store_comparison': '/executive/api/store-comparison',
            'financial_forecasts': '/executive/api/financial-forecasts'
        }
        
        print("🔍 Fetching API responses for analysis...")
        
        for name, endpoint in endpoints.items():
            try:
                response = requests.get(f"{self.base_url}{endpoint}", 
                                      timeout=10, verify=False)
                if response.status_code == 200:
                    self.api_responses[name] = response.json()
                    print(f"  ✅ {name}: {len(json.dumps(self.api_responses[name]))} chars")
                else:
                    print(f"  ❌ {name}: HTTP {response.status_code}")
            except Exception as e:
                print(f"  ❌ {name}: {str(e)}")
    
    def analyze_kpi_mapping(self):
        """Analyze KPI data mapping issues"""
        print("\n📊 Analyzing KPI Data Mapping...")
        
        if 'financial_kpis' not in self.api_responses:
            print("  ❌ No financial KPIs data available")
            return
            
        kpi_data = self.api_responses['financial_kpis']
        print(f"  Actual API Response Structure:")
        print(f"    {json.dumps(kpi_data, indent=4)}")
        
        # Map actual API structure to expected frontend fields
        mapping_analysis = {
            'expected_frontend_fields': {
                'total_revenue': 'NOT FOUND',
                'yoy_growth': 'NOT FOUND', 
                'equipment_utilization': 'NOT FOUND',
                'business_health': 'NOT FOUND'
            },
            'actual_api_data': {},
            'suggested_mapping': {}
        }
        
        # Analyze actual data available
        if 'revenue_metrics' in kpi_data:
            revenue = kpi_data['revenue_metrics']
            mapping_analysis['actual_api_data']['revenue_metrics'] = revenue
            if 'current_3wk_avg' in revenue:
                mapping_analysis['suggested_mapping']['total_revenue'] = f"data.revenue_metrics.current_3wk_avg ({revenue['current_3wk_avg']})"
                mapping_analysis['expected_frontend_fields']['total_revenue'] = 'AVAILABLE'
            if 'yoy_growth' in revenue:
                mapping_analysis['suggested_mapping']['yoy_growth'] = f"data.revenue_metrics.yoy_growth ({revenue['yoy_growth']}%)"
                mapping_analysis['expected_frontend_fields']['yoy_growth'] = 'AVAILABLE'
        
        if 'store_metrics' in kpi_data:
            store = kpi_data['store_metrics']
            mapping_analysis['actual_api_data']['store_metrics'] = store
            if 'utilization_avg' in store:
                mapping_analysis['suggested_mapping']['equipment_utilization'] = f"data.store_metrics.utilization_avg ({store['utilization_avg']}%)"
                mapping_analysis['expected_frontend_fields']['equipment_utilization'] = 'AVAILABLE'
        
        if 'operational_health' in kpi_data:
            health = kpi_data['operational_health']
            mapping_analysis['actual_api_data']['operational_health'] = health
            if 'health_score' in health:
                mapping_analysis['suggested_mapping']['business_health'] = f"data.operational_health.health_score ({health['health_score']})"
                mapping_analysis['expected_frontend_fields']['business_health'] = 'AVAILABLE'
        
        self.mapping_issues['kpi_mapping'] = mapping_analysis
        
        print(f"\n  📋 Frontend Expectation vs Reality:")
        for field, status in mapping_analysis['expected_frontend_fields'].items():
            status_icon = '✅' if status == 'AVAILABLE' else '❌'
            print(f"    {status_icon} {field}: {status}")
        
        print(f"\n  🔧 Suggested JavaScript Mapping Changes:")
        for frontend_field, api_path in mapping_analysis['suggested_mapping'].items():
            print(f"    {frontend_field}: {api_path}")
    
    def analyze_insights_mapping(self):
        """Analyze insights data mapping"""
        print("\n💡 Analyzing Insights Data Mapping...")
        
        if 'intelligent_insights' not in self.api_responses:
            print("  ❌ No insights data available")
            return
            
        insights_data = self.api_responses['intelligent_insights']
        print(f"  Actual API Response: {json.dumps(insights_data, indent=2)}")
        
        mapping_analysis = {
            'frontend_expects': 'data.insights (array)',
            'api_provides': 'data.actionable_insights (array)',
            'mapping_issue': True,
            'fix_required': 'Change frontend to use data.actionable_insights'
        }
        
        if 'actionable_insights' in insights_data:
            insights = insights_data['actionable_insights']
            mapping_analysis['available_insights'] = len(insights)
            mapping_analysis['sample_insight'] = insights[0] if insights else None
        
        self.mapping_issues['insights_mapping'] = mapping_analysis
        print(f"  🔧 Fix: Frontend should use 'data.actionable_insights' not 'data.insights'")
    
    def analyze_forecast_mapping(self):
        """Analyze forecast data mapping"""
        print("\n📈 Analyzing Forecast Data Mapping...")
        
        if 'financial_forecasts' not in self.api_responses:
            print("  ❌ No forecast data available")
            return
            
        forecast_data = self.api_responses['financial_forecasts']
        print(f"  Actual API Response: {json.dumps(forecast_data, indent=2)}")
        
        mapping_analysis = {
            'frontend_expects': 'data.forecast (array)',
            'api_provides': 'data.forecast_data (object with next_12_weeks array)',
            'mapping_issue': True,
            'fix_required': 'Change frontend to use data.forecast_data.next_12_weeks'
        }
        
        if 'forecast_data' in forecast_data:
            forecast = forecast_data['forecast_data']
            mapping_analysis['available_data'] = forecast
            mapping_analysis['weeks_available'] = len(forecast.get('next_12_weeks', []))
        
        self.mapping_issues['forecast_mapping'] = mapping_analysis
        print(f"  🔧 Fix: Frontend should use 'data.forecast_data.next_12_weeks' not 'data.forecast'")
    
    def generate_javascript_fixes(self):
        """Generate specific JavaScript fixes for the frontend"""
        print("\n🛠️  REQUIRED JAVASCRIPT FIXES:")
        print("=" * 50)
        
        if 'kpi_mapping' in self.mapping_issues:
            print("\n1. KPI Data Mapping Fixes (in executive_dashboard.html):")
            print("   Replace the KPI update logic with:")
            print("""
   // CORRECTED KPI mapping
   function updateKPICards(data) {
       // Total Revenue from revenue_metrics.current_3wk_avg
       const totalRevenue = data.revenue_metrics?.current_3wk_avg || 0;
       document.querySelector('[data-kpi="total-revenue"]')?.textContent = 
           '$' + totalRevenue.toLocaleString();
       
       // YoY Growth from revenue_metrics.yoy_growth  
       const yoyGrowth = data.revenue_metrics?.yoy_growth || 0;
       document.querySelector('[data-kpi="yoy-growth"]')?.textContent = 
           yoyGrowth.toFixed(1) + '%';
       
       // Equipment Utilization from store_metrics.utilization_avg
       const equipUtilization = data.store_metrics?.utilization_avg || 0;
       document.querySelector('[data-kpi="equipment-utilization"]')?.textContent = 
           equipUtilization.toFixed(1) + '%';
       
       // Business Health from operational_health.health_score
       const businessHealth = data.operational_health?.health_score || 0;
       document.querySelector('[data-kpi="business-health"]')?.textContent = 
           businessHealth.toFixed(0);
   }""")
        
        if 'insights_mapping' in self.mapping_issues:
            print("\n2. Insights Data Mapping Fix:")
            print("   Change: data.insights")
            print("   To:     data.actionable_insights")
        
        if 'forecast_mapping' in self.mapping_issues:
            print("\n3. Forecast Data Mapping Fix:")
            print("   Change: data.forecast")
            print("   To:     data.forecast_data.next_12_weeks")
    
    def create_test_javascript_snippet(self):
        """Create a test JavaScript snippet to validate fixes"""
        print("\n🧪 Test JavaScript Snippet (paste in browser console):")
        print("=" * 50)
        
        test_snippet = """
// Test the corrected API data mapping
async function testKPIMapping() {
    try {
        const response = await fetch('/executive/api/financial-kpis');
        const data = await response.json();
        
        console.log('Raw API Data:', data);
        
        // Test corrected mappings
        const totalRevenue = data.revenue_metrics?.current_3wk_avg || 0;
        const yoyGrowth = data.revenue_metrics?.yoy_growth || 0;
        const equipUtilization = data.store_metrics?.utilization_avg || 0;
        const businessHealth = data.operational_health?.health_score || 0;
        
        console.log('Mapped KPI Values:');
        console.log('  Total Revenue:', '$' + totalRevenue.toLocaleString());
        console.log('  YoY Growth:', yoyGrowth.toFixed(1) + '%');
        console.log('  Equipment Utilization:', equipUtilization.toFixed(1) + '%');
        console.log('  Business Health:', businessHealth.toFixed(0));
        
        // Test if these are valid numbers (not NaN)
        console.log('Validation:');
        console.log('  Total Revenue valid:', !isNaN(totalRevenue) && totalRevenue > 0);
        console.log('  YoY Growth valid:', !isNaN(yoyGrowth));
        console.log('  Equipment Utilization valid:', !isNaN(equipUtilization) && equipUtilization > 0);
        console.log('  Business Health valid:', !isNaN(businessHealth) && businessHealth > 0);
        
    } catch (error) {
        console.error('Test failed:', error);
    }
}

// Run the test
testKPIMapping();
"""
        print(test_snippet)
    
    def run_comprehensive_analysis(self):
        """Run complete data mapping analysis"""
        print("🔍 EXECUTIVE DASHBOARD DATA MAPPING ANALYSIS")
        print("=" * 60)
        print("This analysis identifies why KPIs show 'NaN' and provides specific fixes.")
        
        self.fetch_api_responses()
        self.analyze_kpi_mapping()
        self.analyze_insights_mapping()
        self.analyze_forecast_mapping()
        
        print("\n" + "=" * 60)
        print("📋 SUMMARY OF ISSUES FOUND:")
        print("=" * 60)
        
        print("\n🎯 ROOT CAUSE OF 'NaN' VALUES:")
        print("  The frontend JavaScript is looking for fields that don't exist in the API response.")
        print("  Frontend expects: total_revenue, yoy_growth, equipment_utilization, business_health")
        print("  API provides: revenue_metrics.*, store_metrics.*, operational_health.*")
        
        self.generate_javascript_fixes()
        self.create_test_javascript_snippet()
        
        print("\n🚀 IMMEDIATE ACTION ITEMS:")
        print("  1. Update JavaScript in executive_dashboard.html with corrected field mapping")
        print("  2. Test the JavaScript snippet in browser console to verify fixes")
        print("  3. Refresh dashboard page to see actual values instead of 'NaN'")
        print("  4. Consider updating API to match frontend expectations (optional)")

if __name__ == "__main__":
    analyzer = DataMappingAnalyzer()
    analyzer.run_comprehensive_analysis()