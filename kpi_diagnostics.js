
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
