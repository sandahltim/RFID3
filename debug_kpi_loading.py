#!/usr/bin/env python3
"""
Debug KPI Loading Issue
Comprehensive testing script for the executive dashboard KPI loading problem
"""

import requests
import json
from datetime import datetime

def test_api_endpoint():
    """Test the financial KPIs API endpoint"""
    print("🔍 Testing API endpoint...")
    
    try:
        # Test API endpoint
        response = requests.get('https://pi5:6800/executive/api/financial-kpis', verify=False)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {response.headers}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response: {json.dumps(data, indent=2)}")
            
            # Check data structure
            print(f"\n📊 Data Structure Analysis:")
            print(f"  - Success: {data.get('success')}")
            print(f"  - Revenue: {data.get('revenue_metrics', {}).get('current_3wk_avg')}")
            print(f"  - YoY Growth: {data.get('revenue_metrics', {}).get('yoy_growth')}")
            print(f"  - Utilization: {data.get('store_metrics', {}).get('utilization_avg')}")
            print(f"  - Health Score: {data.get('operational_health', {}).get('health_score')}")
            
            return data
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Exception testing API: {e}")
        return None

def generate_debug_html():
    """Generate a debug HTML file to test KPI loading"""
    
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KPI Loading Debug Test</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .kpi-card { border: 1px solid #ccc; padding: 20px; margin: 10px; display: inline-block; width: 200px; }
        .kpi-value { font-size: 24px; font-weight: bold; color: #0066cc; }
        .debug-info { background: #f5f5f5; padding: 10px; margin: 10px 0; border-left: 4px solid #ccc; }
        .error { color: red; }
        .success { color: green; }
    </style>
</head>
<body>
    <h1>KVI Loading Debug Test</h1>
    
    <div class="debug-info">
        <h3>Test Status:</h3>
        <div id="debugStatus">Initializing...</div>
    </div>
    
    <h2>KPI Cards</h2>
    
    <div class="kpi-card">
        <div>Revenue (3-Week Avg)</div>
        <div class="kpi-value" id="revenueKPI">Loading...</div>
    </div>
    
    <div class="kpi-card">
        <div>YoY Growth</div>
        <div class="kpi-value" id="growthKPI">Loading...</div>
    </div>
    
    <div class="kpi-card">
        <div>Equipment Utilization</div>
        <div class="kpi-value" id="utilizationKPI">Loading...</div>
    </div>
    
    <div class="kpi-card">
        <div>Business Health</div>
        <div class="kpi-value" id="healthKPI">Loading...</div>
    </div>
    
    <div class="debug-info">
        <h3>Debug Log:</h3>
        <div id="debugLog"></div>
    </div>
    
    <button onclick="testKPILoading()">Reload KPIs</button>
    <button onclick="testDirectAPI()">Test API Direct</button>
    <button onclick="clearDebug()">Clear Log</button>

<script>
// Debug logging function
function debugLog(message) {
    console.log(message);
    const logDiv = document.getElementById('debugLog');
    logDiv.innerHTML += '<div>' + new Date().toISOString() + ': ' + message + '</div>';
}

// Format currency
function formatCurrency(value, abbreviated = false) {
    if (!value) return '$0';
    
    if (abbreviated && value >= 1000) {
        if (value >= 1000000) {
            return '$' + (value / 1000000).toFixed(1) + 'M';
        } else if (value >= 1000) {
            return '$' + (value / 1000).toFixed(0) + 'K';
        }
    }
    
    return '$' + value.toLocaleString();
}

// Format percentage
function formatPercentage(value) {
    if (value === null || value === undefined) return '0%';
    return value.toFixed(1) + '%';
}

// Test KPI loading function
async function testKPILoading() {
    debugLog('🔍 Starting KPI loading test...');
    document.getElementById('debugStatus').textContent = 'Loading...';
    
    try {
        const response = await fetch('/executive/api/financial-kpis');
        debugLog('📡 Fetch response status: ' + response.status);
        
        if (!response.ok) {
            throw new Error('HTTP ' + response.status);
        }
        
        const data = await response.json();
        debugLog('📊 API Response received: ' + JSON.stringify(data));
        
        if (data.success) {
            updateKPIDisplays(data);
            document.getElementById('debugStatus').innerHTML = '<span class="success">✅ KPIs loaded successfully</span>';
        } else {
            debugLog('❌ API returned success=false');
            document.getElementById('debugStatus').innerHTML = '<span class="error">❌ API returned success=false</span>';
        }
        
    } catch (error) {
        debugLog('❌ Error loading KPIs: ' + error.message);
        document.getElementById('debugStatus').innerHTML = '<span class="error">❌ Error: ' + error.message + '</span>';
    }
}

// Test direct API call
async function testDirectAPI() {
    debugLog('🧪 Testing direct API call...');
    
    try {
        const result = await fetch('/executive/api/financial-kpis')
            .then(r => r.json());
        debugLog('📊 Direct API result: ' + JSON.stringify(result, null, 2));
        console.log('Direct API result:', result);
    } catch (error) {
        debugLog('❌ Direct API test failed: ' + error.message);
    }
}

// Update KPI displays
function updateKPIDisplays(data) {
    debugLog('🎯 updateKPIDisplays called with data');
    
    const revenue = data.revenue_metrics?.current_3wk_avg || 0;
    const growth = data.revenue_metrics?.yoy_growth || 0;
    const utilization = data.store_metrics?.utilization_avg || 0;
    const health = data.operational_health?.health_score || 0;

    debugLog('💰 Extracted values: revenue=' + revenue + ', growth=' + growth + ', utilization=' + utilization + ', health=' + health);
    
    // Format values
    const formattedRevenue = formatCurrency(revenue);
    const formattedGrowth = formatPercentage(growth);
    const formattedUtilization = formatPercentage(utilization);
    const formattedHealth = Math.round(health);
    
    debugLog('🎨 Formatted values: ' + JSON.stringify({
        revenue: formattedRevenue,
        growth: formattedGrowth,
        utilization: formattedUtilization,
        health: formattedHealth
    }));

    // Check if DOM elements exist
    const elements = {
        revenue: document.getElementById('revenueKPI'),
        growth: document.getElementById('growthKPI'),
        utilization: document.getElementById('utilizationKPI'),
        health: document.getElementById('healthKPI')
    };
    
    debugLog('🔍 DOM elements check: ' + JSON.stringify({
        revenue: !!elements.revenue,
        growth: !!elements.growth,
        utilization: !!elements.utilization,
        health: !!elements.health
    }));

    // Update DOM elements
    if (elements.revenue) {
        elements.revenue.textContent = formattedRevenue;
        debugLog('✅ Revenue updated to: ' + formattedRevenue);
    } else {
        debugLog('❌ Revenue element not found');
    }
    
    if (elements.growth) {
        elements.growth.textContent = formattedGrowth;
        debugLog('✅ Growth updated to: ' + formattedGrowth);
    } else {
        debugLog('❌ Growth element not found');
    }
    
    if (elements.utilization) {
        elements.utilization.textContent = formattedUtilization;
        debugLog('✅ Utilization updated to: ' + formattedUtilization);
    } else {
        debugLog('❌ Utilization element not found');
    }
    
    if (elements.health) {
        elements.health.textContent = formattedHealth;
        debugLog('✅ Health updated to: ' + formattedHealth);
    } else {
        debugLog('❌ Health element not found');
    }
    
    debugLog('✅ KPI displays update complete');
}

// Clear debug log
function clearDebug() {
    document.getElementById('debugLog').innerHTML = '';
}

// Initialize on page load
window.addEventListener('DOMContentLoaded', function() {
    debugLog('🚀 Page loaded, starting initial KPI test...');
    testKPILoading();
});

</script>

</body>
</html>'''
    
    return html_content

def main():
    """Main debug function"""
    print("🐛 KPI Loading Debug Script")
    print("=" * 50)
    
    # Test API endpoint
    api_data = test_api_endpoint()
    
    if api_data:
        print("\n✅ API endpoint is working correctly")
        print("\n🔧 Debugging Steps:")
        print("1. API endpoint returns correct data structure")
        print("2. Check JavaScript execution in browser")
        print("3. Verify DOM element IDs match")
        print("4. Check for JavaScript errors in console")
        print("5. Verify timing of function calls")
        
        # Generate debug HTML
        debug_html = generate_debug_html()
        debug_file = '/home/tim/RFID3/debug_kpi_test.html'
        
        with open(debug_file, 'w') as f:
            f.write(debug_html)
        
        print(f"\n📁 Debug HTML file created: {debug_file}")
        print("   Open this file in a browser to test KPI loading directly")
        
        print("\n🔍 Manual Debugging Steps:")
        print("1. Open browser to https://pi5:6800/executive/dashboard")
        print("2. Press F12 to open Developer Tools")
        print("3. Go to Console tab")
        print("4. Run: fetch('/executive/api/financial-kpis').then(r=>r.json()).then(console.log)")
        print("5. Check for any JavaScript errors")
        print("6. Verify loadFinancialKPIs() is being called")
        print("7. Check if updateKPIDisplays() receives data")
        
        print("\n📊 Expected API Data Structure:")
        print(json.dumps(api_data, indent=2))
        
    else:
        print("\n❌ API endpoint is not working")
        print("Check if Flask application is running on https://pi5:6800")

if __name__ == "__main__":
    main()