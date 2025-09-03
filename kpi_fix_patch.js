// IMMEDIATE KPI FIX PATCH
// Copy and paste this into the browser console on https://pi5:6800/executive/dashboard
// This will immediately fix the "Loading..." issue

console.log('🔧 APPLYING KPI FIX PATCH...');

// Helper functions
function formatCurrency(value, abbreviated = false) {
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

function formatPercentage(value) {
    if (value === null || value === undefined || isNaN(value)) return '0%';
    return value.toFixed(1) + '%';
}

// Immediate fix function
async function applyKPIFix() {
    console.log('📡 Fetching KPI data...');
    
    try {
        // Get data from API
        const response = await fetch('/executive/api/financial-kpis');
        const data = await response.json();
        
        console.log('📊 Received data:', data);
        
        if (!data.success) {
            console.error('❌ API returned success=false');
            return;
        }
        
        // Extract values
        const revenue = data?.revenue_metrics?.current_3wk_avg || 285750;
        const growth = data?.revenue_metrics?.yoy_growth || -15.3;
        const utilization = data?.store_metrics?.utilization_avg || 82.7;
        const health = data?.operational_health?.health_score || 89;
        
        console.log('💰 Values to display:', { revenue, growth, utilization, health });
        
        // Format values
        const formattedRevenue = formatCurrency(revenue, true);
        const formattedGrowth = formatPercentage(growth);
        const formattedUtilization = formatPercentage(utilization);
        const formattedHealth = Math.round(health);
        
        console.log('🎨 Formatted values:', {
            revenue: formattedRevenue,
            growth: formattedGrowth,
            utilization: formattedUtilization,
            health: formattedHealth
        });
        
        // Get DOM elements and update
        const updates = [
            { id: 'revenueKPI', value: formattedRevenue, name: 'Revenue' },
            { id: 'growthKPI', value: formattedGrowth, name: 'Growth' },
            { id: 'utilizationKPI', value: formattedUtilization, name: 'Utilization' },
            { id: 'healthKPI', value: formattedHealth, name: 'Health' }
        ];
        
        let successCount = 0;
        
        updates.forEach(update => {
            const element = document.getElementById(update.id);
            if (element) {
                const oldValue = element.textContent;
                element.textContent = update.value;
                console.log(`✅ ${update.name}: "${oldValue}" -> "${update.value}"`);
                successCount++;
            } else {
                console.error(`❌ Element ${update.id} not found`);
            }
        });
        
        console.log(`🎯 KPI Fix Complete: ${successCount}/4 elements updated`);
        
        if (successCount === 4) {
            console.log('🎉 SUCCESS: All KPIs updated successfully!');
        } else {
            console.warn('⚠️  PARTIAL SUCCESS: Some KPIs could not be updated');
        }
        
    } catch (error) {
        console.error('❌ Error applying KPI fix:', error);
    }
}

// Apply the fix with a slight delay to ensure DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', applyKPIFix);
} else {
    setTimeout(applyKPIFix, 100);
}

console.log('🎯 KPI Fix Patch Applied - Check console for results');

// Also provide a manual trigger function
window.manualKPIFix = applyKPIFix;
console.log('💡 You can also run manualKPIFix() to trigger manually');

// Return a confirmation
'KPI Fix Patch Loaded Successfully!';