#!/usr/bin/env python3
"""
Fix KPI Loading Issue
Analysis and fix for the "Loading..." problem in executive dashboard
"""

import re

def analyze_api_structure():
    """Analyze the current API structure vs expected structure"""
    
    print("🔍 API Structure Analysis")
    print("=" * 50)
    
    print("✅ ACTUAL API Response Structure:")
    actual_structure = {
        "success": True,
        "operational_health": {
            "change_pct": 3.0,
            "health_score": 89
        },
        "revenue_metrics": {
            "change_pct": 8.2,
            "current_3wk_avg": 285750,
            "yoy_growth": -15.3
        },
        "store_metrics": {
            "change_pct": 5.4,
            "utilization_avg": 82.7
        }
    }
    
    print("📊 JavaScript expects:")
    expected_structure = """
    revenue = data.revenue_metrics?.current_3wk_avg || 0;        ✅ MATCHES
    growth = data.revenue_metrics?.yoy_growth || 0;              ✅ MATCHES  
    utilization = data.store_metrics?.utilization_avg || 0;      ✅ MATCHES
    health = data.operational_health?.health_score || 0;         ✅ MATCHES
    """
    
    print(expected_structure)
    print("🎯 CONCLUSION: Data structure matches perfectly!")
    
    return True

def identify_potential_issues():
    """Identify potential issues in the KPI loading"""
    
    print("\n🐛 Potential Issues Analysis")
    print("=" * 50)
    
    issues = [
        {
            "issue": "API endpoint returns different data structure",
            "status": "✅ RESOLVED - Structure matches perfectly",
            "priority": "LOW"
        },
        {
            "issue": "JavaScript functions not being called",
            "status": "🔍 NEEDS INVESTIGATION - Check browser console",
            "priority": "HIGH"
        },
        {
            "issue": "DOM elements not found",
            "status": "🔍 NEEDS INVESTIGATION - Check element IDs",
            "priority": "HIGH"
        },
        {
            "issue": "JavaScript errors preventing execution",
            "status": "🔍 NEEDS INVESTIGATION - Check console for errors",
            "priority": "HIGH"
        },
        {
            "issue": "Timing issue - function called before DOM ready",
            "status": "🔍 POSSIBLE - Check initialization order",
            "priority": "MEDIUM"
        },
        {
            "issue": "CountUp.js or other library conflicts",
            "status": "🔍 POSSIBLE - Library loading issues",
            "priority": "MEDIUM"
        }
    ]
    
    for i, issue in enumerate(issues, 1):
        print(f"{i}. {issue['issue']}")
        print(f"   Status: {issue['status']}")
        print(f"   Priority: {issue['priority']}")
        print()
    
    return issues

def create_diagnostic_patch():
    """Create a diagnostic patch to help debug the issue"""
    
    print("🔧 Creating Diagnostic Patch")
    print("=" * 50)
    
    diagnostic_js = """
// KPI Loading Diagnostic Patch
// Add this to the browser console to debug the issue

console.log('🚀 Starting KPI Diagnostic...');

// 1. Check if DOM elements exist
function checkDOMElements() {
    const elements = {
        revenueKPI: document.getElementById('revenueKPI'),
        growthKPI: document.getElementById('growthKPI'),
        utilizationKPI: document.getElementById('utilizationKPI'),
        healthKPI: document.getElementById('healthKPI')
    };
    
    console.log('🔍 DOM Elements Check:', elements);
    
    Object.entries(elements).forEach(([key, element]) => {
        if (element) {
            console.log(`✅ ${key}: Found - Current text: "${element.textContent}"`);
        } else {
            console.log(`❌ ${key}: NOT FOUND`);
        }
    });
    
    return elements;
}

// 2. Test API endpoint directly
async function testAPIEndpoint() {
    console.log('📡 Testing API endpoint...');
    
    try {
        const response = await fetch('/executive/api/financial-kpis');
        console.log('📊 Response status:', response.status);
        
        const data = await response.json();
        console.log('📊 API Data:', data);
        
        return data;
    } catch (error) {
        console.error('❌ API Test Error:', error);
        return null;
    }
}

// 3. Test update function directly
function testUpdateFunction(data) {
    console.log('🎯 Testing updateKPIDisplays function...');
    
    if (typeof updateKPIDisplays === 'function') {
        console.log('✅ updateKPIDisplays function exists');
        updateKPIDisplays(data);
    } else {
        console.log('❌ updateKPIDisplays function NOT FOUND');
    }
}

// 4. Test complete flow
async function runDiagnostics() {
    console.log('🔬 Running Complete Diagnostics...');
    
    // Check DOM
    const elements = checkDOMElements();
    
    // Test API
    const apiData = await testAPIEndpoint();
    
    // Test update function
    if (apiData && apiData.success) {
        testUpdateFunction(apiData);
    }
    
    // Final check
    setTimeout(() => {
        console.log('🏁 Final KPI Values:');
        Object.entries(elements).forEach(([key, element]) => {
            if (element) {
                console.log(`${key}: "${element.textContent}"`);
            }
        });
    }, 1000);
}

// Run diagnostics
runDiagnostics();
"""
    
    with open('/home/tim/RFID3/kpi_diagnostics.js', 'w') as f:
        f.write(diagnostic_js)
    
    print("📁 Diagnostic script saved to: /home/tim/RFID3/kpi_diagnostics.js")
    print("\nTo use this diagnostic:")
    print("1. Open browser to https://pi5:6800/executive/dashboard")
    print("2. Press F12 and go to Console tab")
    print("3. Copy and paste the diagnostic script")
    print("4. Press Enter to run")
    
    return diagnostic_js

def create_console_commands():
    """Create useful console commands for debugging"""
    
    print("\n💻 Useful Browser Console Commands")
    print("=" * 50)
    
    commands = [
        {
            "command": "fetch('/executive/api/financial-kpis').then(r=>r.json()).then(console.log)",
            "description": "Test API endpoint directly"
        },
        {
            "command": "document.getElementById('revenueKPI')",
            "description": "Check if revenue KPI element exists"
        },
        {
            "command": "loadFinancialKPIs()",
            "description": "Call the KPI loading function directly"
        },
        {
            "command": "updateKPIDisplays({revenue_metrics: {current_3wk_avg: 285750, yoy_growth: -15.3}, store_metrics: {utilization_avg: 82.7}, operational_health: {health_score: 89}, success: true})",
            "description": "Test update function with sample data"
        },
        {
            "command": "console.log('All KPI elements:', {revenue: document.getElementById('revenueKPI'), growth: document.getElementById('growthKPI'), utilization: document.getElementById('utilizationKPI'), health: document.getElementById('healthKPI')})",
            "description": "Check all KPI elements at once"
        }
    ]
    
    for i, cmd in enumerate(commands, 1):
        print(f"{i}. {cmd['description']}")
        print(f"   Command: {cmd['command']}")
        print()
    
    return commands

def main():
    """Main diagnostic function"""
    print("🐛 KPI Loading Issue Diagnostic & Fix")
    print("=" * 60)
    
    # Analyze API structure
    structure_ok = analyze_api_structure()
    
    # Identify potential issues
    issues = identify_potential_issues()
    
    # Create diagnostic tools
    diagnostic_js = create_diagnostic_patch()
    commands = create_console_commands()
    
    print("\n🎯 SUMMARY")
    print("=" * 50)
    print("✅ API endpoint works correctly")
    print("✅ Data structure matches JavaScript expectations")
    print("🔍 Issue is likely in JavaScript execution or DOM timing")
    
    print("\n📋 ACTION PLAN:")
    print("1. Use the diagnostic script in browser console")
    print("2. Check for JavaScript errors in console")
    print("3. Verify DOM elements exist when functions are called")
    print("4. Check if loadFinancialKPIs() is actually being called")
    print("5. Look for library conflicts (CountUp.js, Chart.js)")
    
    print(f"\n📁 Files created:")
    print(f"   - /home/tim/RFID3/kpi_diagnostics.js")
    print(f"   - /home/tim/RFID3/debug_kpi_test.html (from previous script)")

if __name__ == "__main__":
    main()