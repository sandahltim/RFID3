// KPI Loading Fix and Test Script
// Run this in browser console to debug and fix the KPI loading issue

console.log('🔧 KPI Loading Fix Script Starting...');

// First, let's test if the basic API works
async function testAPI() {
    console.log('📡 Testing API...');
    try {
        const response = await fetch('/executive/api/financial-kpis');
        const data = await response.json();
        console.log('✅ API Response:', data);
        return data;
    } catch (error) {
        console.error('❌ API Error:', error);
        return null;
    }
}

// Test if DOM elements exist
function testDOMElements() {
    console.log('🔍 Testing DOM elements...');
    
    const elements = {
        revenueKPI: document.getElementById('revenueKPI'),
        growthKPI: document.getElementById('growthKPI'),
        utilizationKPI: document.getElementById('utilizationKPI'),
        healthKPI: document.getElementById('healthKPI')
    };
    
    console.log('DOM Elements:', elements);
    
    // Check each element
    Object.entries(elements).forEach(([name, element]) => {
        if (element) {
            console.log(`✅ ${name}: Found (current text: "${element.textContent}")`);
        } else {
            console.error(`❌ ${name}: NOT FOUND`);
        }
    });
    
    return elements;
}

// Format currency function
function formatCurrencyFixed(value, abbreviated = false) {
    if (!value || isNaN(value)) return '$0';
    
    if (abbreviated && value >= 1000) {
        if (value >= 1000000) {
            return '$' + (value / 1000000).toFixed(1) + 'M';
        } else if (value >= 1000) {
            return '$' + Math.round(value / 1000) + 'K';
        }
    }
    
    return '$' + value.toLocaleString();
}

// Format percentage function
function formatPercentageFixed(value) {
    if (value === null || value === undefined || isNaN(value)) return '0%';
    return value.toFixed(1) + '%';
}

// Fixed update function
function updateKPIDisplaysFixed(data) {
    console.log('🎯 updateKPIDisplaysFixed called with:', data);
    
    // Extract values
    const revenue = data?.revenue_metrics?.current_3wk_avg || 0;
    const growth = data?.revenue_metrics?.yoy_growth || 0;
    const utilization = data?.store_metrics?.utilization_avg || 0;
    const health = data?.operational_health?.health_score || 0;
    
    console.log('💰 Raw values:', { revenue, growth, utilization, health });
    
    // Format values
    const formattedRevenue = formatCurrencyFixed(revenue, true);
    const formattedGrowth = formatPercentageFixed(growth);
    const formattedUtilization = formatPercentageFixed(utilization);
    const formattedHealth = Math.round(health);
    
    console.log('🎨 Formatted values:', {
        revenue: formattedRevenue,
        growth: formattedGrowth,
        utilization: formattedUtilization,
        health: formattedHealth
    });
    
    // Get DOM elements
    const revenueEl = document.getElementById('revenueKPI');
    const growthEl = document.getElementById('growthKPI');
    const utilizationEl = document.getElementById('utilizationKPI');
    const healthEl = document.getElementById('healthKPI');
    
    // Update elements with explicit checks
    if (revenueEl) {
        revenueEl.textContent = formattedRevenue;
        console.log('✅ Updated revenueKPI to:', formattedRevenue);
    } else {
        console.error('❌ revenueKPI element not found');
    }
    
    if (growthEl) {
        growthEl.textContent = formattedGrowth;
        console.log('✅ Updated growthKPI to:', formattedGrowth);
    } else {
        console.error('❌ growthKPI element not found');
    }
    
    if (utilizationEl) {
        utilizationEl.textContent = formattedUtilization;
        console.log('✅ Updated utilizationKPI to:', formattedUtilization);
    } else {
        console.error('❌ utilizationKPI element not found');
    }
    
    if (healthEl) {
        healthEl.textContent = formattedHealth;
        console.log('✅ Updated healthKPI to:', formattedHealth);
    } else {
        console.error('❌ healthKPI element not found');
    }
    
    return { revenueEl, growthEl, utilizationEl, healthEl };
}

// Complete test and fix function
async function fixKPIs() {
    console.log('🔧 Starting complete KPI fix...');
    
    // 1. Test DOM elements
    const elements = testDOMElements();
    
    // 2. Test API
    const apiData = await testAPI();
    
    if (!apiData || !apiData.success) {
        console.error('❌ Cannot fix KPIs - API data unavailable');
        return;
    }
    
    // 3. Apply fix
    updateKPIDisplaysFixed(apiData);
    
    // 4. Verify fix
    setTimeout(() => {
        console.log('🏁 Final verification:');
        Object.entries(elements).forEach(([name, element]) => {
            if (element) {
                const currentText = element.textContent;
                const isLoading = currentText.includes('Loading');
                console.log(`${name}: "${currentText}" ${isLoading ? '❌ Still loading' : '✅ Fixed'}`);
            }
        });
    }, 500);
    
    return 'Fix applied!';
}

// Auto-run the fix
fixKPIs();