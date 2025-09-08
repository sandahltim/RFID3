// DETAILED KPI DIAGNOSTIC
// Copy and paste this into the browser console to get detailed diagnosis

console.log('🔍 DETAILED KPI DIAGNOSTIC STARTING...');
console.log('=' .repeat(50));

// Check 1: DOM Elements
function checkDOMElements() {
    console.log('1️⃣  CHECKING DOM ELEMENTS...');
    
    const expectedElements = ['revenueKPI', 'growthKPI', 'utilizationKPI', 'healthKPI'];
    const results = {};
    
    expectedElements.forEach(id => {
        const element = document.getElementById(id);
        results[id] = {
            exists: !!element,
            text: element ? element.textContent : null,
            isLoading: element ? element.textContent.includes('Loading') : false
        };
        
        if (element) {
            console.log(`  ✅ ${id}: "${element.textContent}"`);
        } else {
            console.log(`  ❌ ${id}: NOT FOUND`);
        }
    });
    
    return results;
}

// Check 2: API Response
async function checkAPI() {
    console.log('2️⃣  CHECKING API RESPONSE...');
    
    try {
        const response = await fetch('/executive/api/financial-kpis');
        console.log(`  Status: ${response.status} ${response.statusText}`);
        
        const data = await response.json();
        console.log('  Response data:', data);
        
        // Check required fields
        const requiredFields = [
            ['success', data.success],
            ['revenue_metrics.current_3wk_avg', data?.revenue_metrics?.current_3wk_avg],
            ['revenue_metrics.yoy_growth', data?.revenue_metrics?.yoy_growth],
            ['store_metrics.utilization_avg', data?.store_metrics?.utilization_avg],
            ['operational_health.health_score', data?.operational_health?.health_score]
        ];
        
        requiredFields.forEach(([path, value]) => {
            if (value !== undefined && value !== null) {
                console.log(`  ✅ ${path}: ${value}`);
            } else {
                console.log(`  ❌ ${path}: MISSING`);
            }
        });
        
        return { success: true, data };
        
    } catch (error) {
        console.log(`  ❌ API Error: ${error.message}`);
        return { success: false, error };
    }
}

// Check 3: JavaScript Functions
function checkJavaScriptFunctions() {
    console.log('3️⃣  CHECKING JAVASCRIPT FUNCTIONS...');
    
    const functions = [
        'loadFinancialKPIs',
        'updateKPIDisplays',
        'initializeDashboard'
    ];
    
    functions.forEach(funcName => {
        if (typeof window[funcName] === 'function') {
            console.log(`  ✅ ${funcName}: EXISTS`);
        } else {
            console.log(`  ❌ ${funcName}: NOT FOUND`);
        }
    });
}

// Check 4: Console Errors
function checkConsoleErrors() {
    console.log('4️⃣  CHECKING FOR JAVASCRIPT ERRORS...');
    console.log('  (Check the Console tab for any red error messages)');
    
    // Override console.error temporarily to catch errors
    const originalError = console.error;
    const errors = [];
    
    console.error = function(...args) {
        errors.push(args.join(' '));
        originalError.apply(console, args);
    };
    
    // Restore after 5 seconds
    setTimeout(() => {
        console.error = originalError;
        if (errors.length > 0) {
            console.log('  ❌ Detected errors:', errors);
        } else {
            console.log('  ✅ No JavaScript errors detected');
        }
    }, 5000);
}

// Check 5: Library Dependencies
function checkLibraries() {
    console.log('5️⃣  CHECKING LIBRARY DEPENDENCIES...');
    
    const libraries = [
        ['Chart.js', typeof Chart !== 'undefined'],
        ['CountUp.js', typeof CountUp !== 'undefined'],
        ['Bootstrap', typeof bootstrap !== 'undefined'],
        ['jQuery (if used)', typeof $ !== 'undefined']
    ];
    
    libraries.forEach(([name, loaded]) => {
        if (loaded) {
            console.log(`  ✅ ${name}: LOADED`);
        } else {
            console.log(`  ⚠️  ${name}: NOT LOADED (may be ok)`);
        }
    });
}

// Check 6: Event Listeners
function checkEventListeners() {
    console.log('6️⃣  CHECKING EVENT LISTENERS...');
    
    // Check if DOMContentLoaded has fired
    if (document.readyState === 'loading') {
        console.log('  ⚠️  DOM still loading');
    } else {
        console.log('  ✅ DOM is ready');
    }
    
    console.log(`  Document ready state: ${document.readyState}`);
}

// Check 7: Test Manual Update
async function testManualUpdate() {
    console.log('7️⃣  TESTING MANUAL KPI UPDATE...');
    
    const testData = {
        success: true,
        revenue_metrics: { current_3wk_avg: 285750, yoy_growth: -15.3 },
        store_metrics: { utilization_avg: 82.7 },
        operational_health: { health_score: 89 }
    };
    
    try {
        if (typeof updateKPIDisplays === 'function') {
            console.log('  📊 Calling updateKPIDisplays with test data...');
            updateKPIDisplays(testData);
            console.log('  ✅ updateKPIDisplays executed without error');
        } else {
            console.log('  ❌ updateKPIDisplays function not found');
        }
    } catch (error) {
        console.log(`  ❌ Error calling updateKPIDisplays: ${error.message}`);
    }
}

// Run all diagnostics
async function runFullDiagnostic() {
    console.log('🚀 STARTING FULL DIAGNOSTIC...');
    
    const domResults = checkDOMElements();
    const apiResults = await checkAPI();
    checkJavaScriptFunctions();
    checkConsoleErrors();
    checkLibraries();
    checkEventListeners();
    await testManualUpdate();
    
    console.log('🏁 DIAGNOSTIC COMPLETE!');
    console.log('=' .repeat(50));
    
    // Summary
    console.log('📋 DIAGNOSTIC SUMMARY:');
    
    const allElementsExist = Object.values(domResults).every(r => r.exists);
    const allElementsLoading = Object.values(domResults).every(r => r.isLoading);
    
    if (allElementsExist && allElementsLoading) {
        console.log('🎯 DIAGNOSIS: Elements exist but show "Loading..." - JavaScript execution issue');
    } else if (!allElementsExist) {
        console.log('🎯 DIAGNOSIS: Some DOM elements missing - Template/HTML issue');  
    } else if (!apiResults.success) {
        console.log('🎯 DIAGNOSIS: API endpoint issue');
    } else {
        console.log('🎯 DIAGNOSIS: Unknown issue - check console errors');
    }
    
    return {
        dom: domResults,
        api: apiResults,
        summary: {
            allElementsExist,
            allElementsLoading,
            apiWorking: apiResults.success
        }
    };
}

// Auto-run the diagnostic
runFullDiagnostic();