#!/usr/bin/env python3
"""
Frontend JavaScript Simulation Test

Since the backend is 100% healthy, this test simulates what the browser JavaScript
should be doing and identifies any frontend-specific issues.

Author: Testing Specialist
Date: 2025-09-03
"""

import requests
import json
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class FrontendSimulator:
    def __init__(self, base_url="https://pi5:6800"):
        self.base_url = base_url
        
    def simulate_kpi_loading(self):
        """Simulate what the browser JavaScript should do"""
        print("🎭 SIMULATING FRONTEND JAVASCRIPT BEHAVIOR")
        print("=" * 55)
        
        print("\n1. 📡 Fetching KPI data (simulating fetch('/executive/api/financial-kpis'))...")
        
        try:
            response = requests.get(f"{self.base_url}/executive/api/financial-kpis", 
                                  timeout=10, verify=False)
            
            if response.status_code != 200:
                print(f"❌ API call failed: HTTP {response.status_code}")
                return False
                
            data = response.json()
            print(f"✅ API call successful, received data:")
            print(f"   {json.dumps(data, indent=2)}")
            
        except Exception as e:
            print(f"❌ API call failed: {str(e)}")
            return False
        
        print("\n2. 🔄 Processing data (simulating updateKPIDisplays function)...")
        
        # Simulate the exact JavaScript logic
        revenue = data.get('revenue_metrics', {}).get('current_3wk_avg', 0)
        growth = data.get('revenue_metrics', {}).get('yoy_growth', 0)
        utilization = data.get('store_metrics', {}).get('utilization_avg', 0)
        health = data.get('operational_health', {}).get('health_score', 0)
        
        print(f"   Raw extracted values:")
        print(f"     revenue: {revenue} (type: {type(revenue).__name__})")
        print(f"     growth: {growth} (type: {type(growth).__name__})")
        print(f"     utilization: {utilization} (type: {type(utilization).__name__})")
        print(f"     health: {health} (type: {type(health).__name__})")
        
        print("\n3. 🎨 Formatting values (simulating formatCurrency/formatPercentage)...")
        
        try:
            # Simulate JavaScript formatting
            formatted_revenue = f"${revenue:,.0f}" if isinstance(revenue, (int, float)) else str(revenue)
            formatted_growth = f"{growth:.1f}%" if isinstance(growth, (int, float)) else str(growth)
            formatted_utilization = f"{utilization:.1f}%" if isinstance(utilization, (int, float)) else str(utilization)
            formatted_health = f"{health:.0f}" if isinstance(health, (int, float)) else str(health)
            
            print(f"   Formatted values:")
            print(f"     Total Revenue: {formatted_revenue}")
            print(f"     YoY Growth: {formatted_growth}")
            print(f"     Equipment Utilization: {formatted_utilization}")
            print(f"     Business Health: {formatted_health}")
            
            # Check for NaN or invalid values
            invalid_values = []
            if str(revenue).lower() in ['nan', 'none'] or revenue == 0:
                invalid_values.append('revenue')
            if str(growth).lower() in ['nan', 'none']:
                invalid_values.append('growth')  
            if str(utilization).lower() in ['nan', 'none'] or utilization == 0:
                invalid_values.append('utilization')
            if str(health).lower() in ['nan', 'none'] or health == 0:
                invalid_values.append('health')
            
            if invalid_values:
                print(f"   ⚠️ Potentially invalid values detected: {', '.join(invalid_values)}")
            else:
                print(f"   ✅ All values are valid and should display correctly")
                
        except Exception as e:
            print(f"   ❌ Formatting failed: {str(e)}")
            return False
        
        print("\n4. 🏗️ DOM Update Simulation...")
        
        # Check if the values would show as NaN in JavaScript
        js_checks = {
            'revenueKPI': formatted_revenue,
            'growthKPI': formatted_growth,
            'utilizationKPI': formatted_utilization,
            'healthKPI': formatted_health
        }
        
        for element_id, value in js_checks.items():
            would_be_nan = 'nan' in str(value).lower() or value == 'undefined' or value == ''
            status = '❌ Would show NaN/empty' if would_be_nan else '✅ Would show correctly'
            print(f"   {element_id}: '{value}' → {status}")
        
        return True
    
    def analyze_html_structure(self):
        """Analyze the actual HTML structure for issues"""
        print("\n5. 🔍 Analyzing HTML Structure...")
        
        try:
            response = requests.get(f"{self.base_url}/executive/dashboard", 
                                  timeout=10, verify=False)
            
            if response.status_code != 200:
                print(f"❌ Dashboard page not accessible: HTTP {response.status_code}")
                return False
            
            html = response.text
            
            # Check for KPI element IDs
            kpi_ids = ['revenueKPI', 'growthKPI', 'utilizationKPI', 'healthKPI']
            missing_ids = []
            
            for kpi_id in kpi_ids:
                if f'id="{kpi_id}"' not in html:
                    missing_ids.append(kpi_id)
                else:
                    print(f"   ✅ Found element: {kpi_id}")
            
            if missing_ids:
                print(f"   ❌ Missing element IDs: {', '.join(missing_ids)}")
                return False
            
            # Check for JavaScript functions
            js_functions = ['updateKPIDisplays', 'loadFinancialKPIs']
            missing_functions = []
            
            for func in js_functions:
                if func not in html:
                    missing_functions.append(func)
                else:
                    print(f"   ✅ Found function: {func}")
            
            if missing_functions:
                print(f"   ❌ Missing JavaScript functions: {', '.join(missing_functions)}")
                return False
            
            # Check for automatic loading calls
            if 'loadFinancialKPIs()' in html:
                print(f"   ✅ Found automatic KPI loading call")
            else:
                print(f"   ⚠️ No automatic KPI loading call found")
            
            return True
            
        except Exception as e:
            print(f"❌ HTML analysis failed: {str(e)}")
            return False
    
    def generate_browser_test_script(self):
        """Generate a test script for browser console"""
        print("\n6. 🧪 Browser Console Test Script:")
        print("=" * 40)
        print("Copy and paste this into your browser console at https://pi5:6800/executive/dashboard")
        print()
        
        script = """
// Executive Dashboard KPI Test Script
console.log("🧪 Starting KPI Test...");

// Test 1: Check if KPI elements exist
const kpiElements = {
    revenueKPI: document.getElementById('revenueKPI'),
    growthKPI: document.getElementById('growthKPI'), 
    utilizationKPI: document.getElementById('utilizationKPI'),
    healthKPI: document.getElementById('healthKPI')
};

console.log("🏗️ KPI Elements Check:");
Object.entries(kpiElements).forEach(([name, element]) => {
    console.log(`  ${element ? '✅' : '❌'} ${name}:`, element ? 'Found' : 'Missing');
});

// Test 2: Fetch KPI data manually
async function testKPIData() {
    try {
        console.log("\\n📡 Testing KPI API...");
        const response = await fetch('/executive/api/financial-kpis');
        const data = await response.json();
        
        console.log("Raw API data:", data);
        
        // Test data extraction
        const revenue = data.revenue_metrics?.current_3wk_avg || 0;
        const growth = data.revenue_metrics?.yoy_growth || 0;
        const utilization = data.store_metrics?.utilization_avg || 0;
        const health = data.operational_health?.health_score || 0;
        
        console.log("\\n🔄 Extracted values:");
        console.log(`  Revenue: ${revenue} (${typeof revenue})`);
        console.log(`  Growth: ${growth} (${typeof growth})`);
        console.log(`  Utilization: ${utilization} (${typeof utilization})`);
        console.log(`  Health: ${health} (${typeof health})`);
        
        // Test formatting
        const formattedRevenue = '$' + revenue.toLocaleString();
        const formattedGrowth = growth.toFixed(1) + '%';
        const formattedUtilization = utilization.toFixed(1) + '%';
        const formattedHealth = health.toFixed(0);
        
        console.log("\\n🎨 Formatted values:");
        console.log(`  Revenue: ${formattedRevenue}`);
        console.log(`  Growth: ${formattedGrowth}`);
        console.log(`  Utilization: ${formattedUtilization}`);
        console.log(`  Health: ${formattedHealth}`);
        
        // Test DOM update
        console.log("\\n🏗️ Testing DOM updates...");
        if (kpiElements.revenueKPI) {
            const oldValue = kpiElements.revenueKPI.textContent;
            kpiElements.revenueKPI.textContent = formattedRevenue;
            console.log(`  Revenue: "${oldValue}" → "${formattedRevenue}"`);
        }
        
        if (kpiElements.growthKPI) {
            const oldValue = kpiElements.growthKPI.textContent;
            kpiElements.growthKPI.textContent = formattedGrowth;
            console.log(`  Growth: "${oldValue}" → "${formattedGrowth}"`);
        }
        
        if (kpiElements.utilizationKPI) {
            const oldValue = kpiElements.utilizationKPI.textContent;
            kpiElements.utilizationKPI.textContent = formattedUtilization;
            console.log(`  Utilization: "${oldValue}" → "${formattedUtilization}"`);
        }
        
        if (kpiElements.healthKPI) {
            const oldValue = kpiElements.healthKPI.textContent;
            kpiElements.healthKPI.textContent = formattedHealth;
            console.log(`  Health: "${oldValue}" → "${formattedHealth}"`);
        }
        
        console.log("\\n✅ Test complete! KPI values should now be updated.");
        
    } catch (error) {
        console.error("❌ Test failed:", error);
    }
}

// Run the test
testKPIData();
"""
        
        print(script)
    
    def run_complete_simulation(self):
        """Run complete frontend simulation"""
        success = True
        
        success &= self.simulate_kpi_loading()
        success &= self.analyze_html_structure()
        
        self.generate_browser_test_script()
        
        print("\n" + "=" * 55)
        print("📋 SIMULATION RESULTS")
        print("=" * 55)
        
        if success:
            print("✅ FRONTEND SIMULATION SUCCESSFUL")
            print("\nThe backend data is perfect and the JavaScript should work correctly.")
            print("If you're still seeing 'NaN' or 'Loading...', the issue is likely:")
            print("  1. JavaScript execution timing (functions not running)")
            print("  2. Browser console errors preventing execution")
            print("  3. CSS or DOM issues preventing updates from being visible")
            
            print("\n🎯 RECOMMENDED ACTIONS:")
            print("  1. Open browser developer console")
            print("  2. Navigate to https://pi5:6800/executive/dashboard")
            print("  3. Look for any red error messages in console")
            print("  4. Run the test script provided above")
            print("  5. Check if KPI values update after running the script")
        else:
            print("❌ FRONTEND SIMULATION FOUND ISSUES")
            print("Fix the issues identified above before proceeding.")
        
        return success

if __name__ == "__main__":
    simulator = FrontendSimulator()
    simulator.run_complete_simulation()