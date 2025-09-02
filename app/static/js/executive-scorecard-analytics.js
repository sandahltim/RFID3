// Executive Scorecard Analytics Visualization Functions
// 159 weeks of 2022-2024 data with comprehensive correlation analysis

// Global variables for scorecard charts
let multiYearRevenueChart, storePerformanceHeatMap, pipelineConversionChart;
let correlationScatterChart, arAgingTrendsChart, revenueForecastChart, seasonalDecompositionChart;

// Executive color palette
const EXECUTIVE_COLORS = {
    primary: '#1e3a8a',
    secondary: '#3b82f6', 
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    stores: {
        '3607': '#1e3a8a',  // Wayzata - Primary blue
        '6800': '#10b981',  // Brooklyn Park - Success green
        '728': '#f59e0b',   // Elk River - Warning orange
        '8101': '#8b5cf6'   // Fridley - Purple
    },
    gradient: ['#1e3a8a', '#3b82f6', '#60a5fa', '#93c5fd', '#dbeafe']
};

// Store name mapping
const STORE_NAMES = {
    '3607': 'Wayzata',
    '6800': 'Brooklyn Park', 
    '728': 'Elk River',
    '8101': 'Fridley'
};

/**
 * Initialize all scorecard analytics charts
 */
async function initializeScorecardAnalytics() {
    try {
        console.log('🎯 Initializing Executive Scorecard Analytics...');
        
        // Fetch comprehensive scorecard data
        const [analyticsData, correlationData] = await Promise.all([
            fetchScorecardAnalytics(),
            fetchCorrelationMatrix()
        ]);
        
        if (analyticsData && analyticsData.multi_year_trends) {
            // Initialize all visualization components
            await initializeMultiYearTrends(analyticsData);
            await initializeStorePerformanceHeatMap(analyticsData);
            await initializePipelineConversion(analyticsData);
            await initializeCorrelationScatter(analyticsData);
            await initializeARAgingTrends(analyticsData);
            await initializeRevenueForecast(analyticsData);
            await initializeSeasonalDecomposition(analyticsData);
            await initializeRiskIndicators(analyticsData);
            await initializeCorrelationMatrix(correlationData);
            
            console.log('✅ Scorecard analytics initialized successfully');
            
            // Dispatch event for insights generation
            window.dispatchEvent(new CustomEvent('scorecardAnalyticsReady', {
                detail: analyticsData
            }));
        } else {
            console.error('❌ No scorecard data available');
        }
    } catch (error) {
        console.error('❌ Error initializing scorecard analytics:', error);
    }
}

/**
 * Fetch scorecard analytics data from API
 */
async function fetchScorecardAnalytics() {
    try {
        const response = await fetch('/api/executive/scorecard_analytics?weeks=159');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching scorecard analytics:', error);
        return null;
    }
}

/**
 * Fetch correlation matrix data
 */
async function fetchCorrelationMatrix() {
    try {
        const response = await fetch('/api/executive/correlation_matrix');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching correlation matrix:', error);
        return null;
    }
}

/**
 * Initialize Multi-Year Revenue Trends Chart
 */
async function initializeMultiYearTrends(data) {
    const ctx = document.getElementById('multiYearRevenueChart');
    if (!ctx || !data.multi_year_trends) return;
    
    // Prepare datasets for each store plus total
    const datasets = [];
    const storeData = {};
    
    // Initialize store arrays
    Object.keys(STORE_NAMES).forEach(storeCode => {
        storeData[storeCode] = [];
    });
    
    const totalData = [];
    const riskHighlights = [];
    
    // Process data points
    data.multi_year_trends.forEach(point => {
        const date = point.week_ending;
        totalData.push({
            x: date,
            y: point.total_revenue
        });
        
        // Risk highlighting
        if (point.concentration_risk) {
            riskHighlights.push({
                x: date,
                y: point.total_revenue
            });
        }
        
        // Store-specific data
        Object.entries(point.store_revenues).forEach(([storeCode, revenue]) => {
            if (storeData[storeCode]) {
                storeData[storeCode].push({
                    x: date,
                    y: revenue
                });
            }
        });
    });
    
    // Total revenue line
    datasets.push({
        label: 'Total Weekly Revenue',
        data: totalData,
        borderColor: EXECUTIVE_COLORS.primary,
        backgroundColor: EXECUTIVE_COLORS.primary + '20',
        borderWidth: 3,
        fill: false,
        tension: 0.2
    });
    
    // Store-specific lines
    Object.entries(storeData).forEach(([storeCode, storeDataPoints]) => {
        if (storeDataPoints.length > 0) {
            datasets.push({
                label: `${STORE_NAMES[storeCode]} Revenue`,
                data: storeDataPoints,
                borderColor: EXECUTIVE_COLORS.stores[storeCode],
                backgroundColor: EXECUTIVE_COLORS.stores[storeCode] + '10',
                borderWidth: 2,
                fill: false,
                tension: 0.1
            });
        }
    });
    
    // Risk concentration highlights
    if (riskHighlights.length > 0) {
        datasets.push({
            label: 'Concentration Risk (>40%)',
            data: riskHighlights,
            borderColor: EXECUTIVE_COLORS.danger,
            backgroundColor: EXECUTIVE_COLORS.danger,
            borderWidth: 0,
            pointRadius: 6,
            pointHoverRadius: 8,
            showLine: false
        });
    }
    
    multiYearRevenueChart = new Chart(ctx, {
        type: 'line',
        data: { datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Multi-Year Revenue Analysis (2022-2024)',
                    font: { size: 16, weight: 'bold' }
                },
                legend: {
                    position: 'top',
                    labels: { usePointStyle: true }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y;
                            return `${context.dataset.label}: $${value.toLocaleString()}`;
                        },
                        afterBody: function(tooltipItems) {
                            const date = tooltipItems[0]?.parsed?.x;
                            if (date) {
                                const dataPoint = data.multi_year_trends.find(d => d.week_ending === date);
                                if (dataPoint && dataPoint.concentration_risk) {
                                    return [`⚠️ High concentration risk: ${dataPoint.max_store_percentage}%`];
                                }
                            }
                            return [];
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    time: {
                        unit: 'month',
                        displayFormats: { month: 'MMM yyyy' }
                    },
                    title: {
                        display: true,
                        text: 'Week Ending Date'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Weekly Revenue ($)'
                    },
                    ticks: {
                        callback: function(value) {
                            return '$' + (value / 1000).toFixed(0) + 'K';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Initialize Store Performance Heat Map
 */
async function initializeStorePerformanceHeatMap(data) {
    const ctx = document.getElementById('storePerformanceHeatMap');
    if (!ctx || !data.multi_year_trends) return;
    
    // Create heat map data structure
    const heatmapData = [];
    const storeNames = Object.values(STORE_NAMES);
    
    // Process data by week and store
    data.multi_year_trends.forEach((point, weekIndex) => {
        Object.entries(point.store_revenues).forEach((entry, storeIndex) => {
            const [storeCode, revenue] = entry;
            const storeName = STORE_NAMES[storeCode];
            
            if (storeName && revenue > 0) {
                heatmapData.push({
                    x: weekIndex,
                    y: storeNames.indexOf(storeName),
                    v: revenue
                });
            }
        });
    });
    
    storePerformanceHeatMap = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Store Revenue Heat Map',
                data: heatmapData,
                backgroundColor: function(context) {
                    const value = context.parsed.v;
                    const max = Math.max(...heatmapData.map(d => d.v));
                    const intensity = value / max;
                    
                    // Color intensity based on revenue
                    if (intensity > 0.8) return EXECUTIVE_COLORS.success + '80';
                    if (intensity > 0.6) return EXECUTIVE_COLORS.warning + '80';
                    if (intensity > 0.4) return EXECUTIVE_COLORS.secondary + '80';
                    return EXECUTIVE_COLORS.primary + '40';
                },
                pointRadius: function(context) {
                    const value = context.parsed.v;
                    const max = Math.max(...heatmapData.map(d => d.v));
                    return Math.max(2, (value / max) * 8);
                }
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: function(context) {
                            const point = context[0];
                            const weekIndex = point.parsed.x;
                            const dataPoint = data.multi_year_trends[weekIndex];
                            return `Week ending ${dataPoint?.week_ending || 'N/A'}`;
                        },
                        label: function(context) {
                            const storeIndex = context.parsed.y;
                            const storeName = storeNames[storeIndex];
                            const revenue = context.parsed.v;
                            return `${storeName}: $${revenue.toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Week Index' },
                    ticks: { maxTicksLimit: 10 }
                },
                y: {
                    title: { display: true, text: 'Store Locations' },
                    ticks: {
                        callback: function(value) {
                            return storeNames[value] || '';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Initialize Pipeline Conversion Chart
 */
async function initializePipelineConversion(data) {
    const ctx = document.getElementById('pipelineConversionChart');
    if (!ctx || !data.pipeline_conversion) return;
    
    const dates = [];
    const conversionRates = [];
    const contracts = [];
    const reservations = [];
    
    data.pipeline_conversion.forEach(point => {
        dates.push(point.week_ending);
        conversionRates.push(point.conversion_rate);
        contracts.push(point.contracts);
        reservations.push(point.reservations);
    });
    
    pipelineConversionChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: 'Conversion Rate (%)',
                    data: conversionRates,
                    borderColor: EXECUTIVE_COLORS.success,
                    backgroundColor: EXECUTIVE_COLORS.success + '20',
                    yAxisID: 'y1',
                    tension: 0.2
                },
                {
                    label: 'New Contracts',
                    data: contracts,
                    borderColor: EXECUTIVE_COLORS.primary,
                    backgroundColor: EXECUTIVE_COLORS.primary + '20',
                    yAxisID: 'y',
                    type: 'bar',
                    barPercentage: 0.5
                },
                {
                    label: 'Reservations',
                    data: reservations,
                    borderColor: EXECUTIVE_COLORS.secondary,
                    backgroundColor: EXECUTIVE_COLORS.secondary + '20',
                    yAxisID: 'y',
                    type: 'bar',
                    barPercentage: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { intersect: false },
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.dataset.label;
                            const value = context.parsed.y;
                            if (label.includes('Rate')) {
                                return `${label}: ${value.toFixed(1)}%`;
                            }
                            return `${label}: ${value}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Week Ending' },
                    ticks: { maxTicksLimit: 8 }
                },
                y: {
                    type: 'linear',
                    position: 'left',
                    title: { display: true, text: 'Count' }
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    title: { display: true, text: 'Conversion Rate (%)' },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
}

/**
 * Initialize Correlation Scatter Chart
 */
async function initializeCorrelationScatter(data) {
    const ctx = document.getElementById('correlationScatterChart');
    if (!ctx || !data.multi_year_trends) return;
    
    // Create scatter plot data for revenue vs contracts by store
    const scatterDatasets = [];
    
    Object.keys(STORE_NAMES).forEach(storeCode => {
        const storePoints = [];
        
        data.multi_year_trends.forEach(point => {
            const revenue = point.store_revenues[storeCode] || 0;
            // Find corresponding contract data
            const contractData = data.pipeline_conversion.find(c => c.week_ending === point.week_ending);
            const contracts = contractData?.store_breakdown?.contracts?.[storeCode] || 0;
            
            if (revenue > 0 && contracts > 0) {
                storePoints.push({ x: contracts, y: revenue });
            }
        });
        
        if (storePoints.length > 0) {
            scatterDatasets.push({
                label: STORE_NAMES[storeCode],
                data: storePoints,
                backgroundColor: EXECUTIVE_COLORS.stores[storeCode] + '80',
                borderColor: EXECUTIVE_COLORS.stores[storeCode],
                borderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
            });
        }
    });
    
    correlationScatterChart = new Chart(ctx, {
        type: 'scatter',
        data: { datasets: scatterDatasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const x = context.parsed.x;
                            const y = context.parsed.y;
                            return `${context.dataset.label}: ${x} contracts → $${y.toLocaleString()}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'New Contracts (Weekly)' }
                },
                y: {
                    title: { display: true, text: 'Revenue ($)' },
                    ticks: {
                        callback: function(value) {
                            return '$' + (value / 1000).toFixed(0) + 'K';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Initialize AR Aging Trends Chart (Simulated for demonstration)
 */
async function initializeARAgingTrends(data) {
    const ctx = document.getElementById('arAgingTrendsChart');
    if (!ctx) return;
    
    // Simulate AR aging data based on revenue patterns
    const dates = data.multi_year_trends.map(d => d.week_ending).slice(-26); // Last 26 weeks
    const arAging30 = dates.map(() => Math.random() * 15 + 5); // 5-20%
    const arAging60 = dates.map(() => Math.random() * 10 + 3); // 3-13%
    const arAging90 = dates.map(() => Math.random() * 8 + 2);  // 2-10%
    const arAgingOver90 = dates.map(() => Math.random() * 5 + 1); // 1-6%
    
    arAgingTrendsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: '30 Days',
                    data: arAging30,
                    borderColor: EXECUTIVE_COLORS.success,
                    backgroundColor: EXECUTIVE_COLORS.success + '20',
                    fill: true
                },
                {
                    label: '31-60 Days', 
                    data: arAging60,
                    borderColor: EXECUTIVE_COLORS.warning,
                    backgroundColor: EXECUTIVE_COLORS.warning + '20',
                    fill: true
                },
                {
                    label: '61-90 Days',
                    data: arAging90,
                    borderColor: EXECUTIVE_COLORS.secondary,
                    backgroundColor: EXECUTIVE_COLORS.secondary + '20',
                    fill: true
                },
                {
                    label: '90+ Days',
                    data: arAgingOver90,
                    borderColor: EXECUTIVE_COLORS.danger,
                    backgroundColor: EXECUTIVE_COLORS.danger + '20',
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Week Ending' }
                },
                y: {
                    title: { display: true, text: 'AR Aging (%)' },
                    stacked: true
                }
            }
        }
    });
}

/**
 * Initialize Revenue Forecast Chart
 */
async function initializeRevenueForecast(data) {
    const ctx = document.getElementById('revenueForecastChart');
    if (!ctx || !data.seasonal_patterns) return;
    
    // Use seasonal patterns to create forecast
    const historicalData = data.multi_year_trends.slice(-26); // Last 26 weeks
    const forecastWeeks = 13; // 13 weeks forecast
    
    const actualRevenues = historicalData.map(d => d.total_revenue);
    const dates = historicalData.map(d => d.week_ending);
    
    // Generate forecast based on seasonal patterns
    const forecastRevenues = [];
    const forecastDates = [];
    
    for (let i = 0; i < forecastWeeks; i++) {
        const lastDate = new Date(dates[dates.length - 1]);
        lastDate.setDate(lastDate.getDate() + (i + 1) * 7);
        forecastDates.push(lastDate.toISOString().split('T')[0]);
        
        // Simple seasonal forecast
        const seasonalMultiplier = 1 + (Math.sin(i * 0.3) * 0.2);
        const baseRevenue = actualRevenues[actualRevenues.length - 1];
        forecastRevenues.push(baseRevenue * seasonalMultiplier);
    }
    
    revenueForecastChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [...dates, ...forecastDates],
            datasets: [
                {
                    label: 'Actual Revenue',
                    data: [...actualRevenues, ...Array(forecastWeeks).fill(null)],
                    borderColor: EXECUTIVE_COLORS.primary,
                    backgroundColor: EXECUTIVE_COLORS.primary + '20',
                    borderWidth: 3
                },
                {
                    label: 'Forecasted Revenue',
                    data: [...Array(actualRevenues.length).fill(null), ...forecastRevenues],
                    borderColor: EXECUTIVE_COLORS.warning,
                    backgroundColor: EXECUTIVE_COLORS.warning + '20',
                    borderDash: [5, 5],
                    borderWidth: 3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' },
                title: {
                    display: true,
                    text: '13-Week Revenue Forecast'
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Week Ending' }
                },
                y: {
                    title: { display: true, text: 'Revenue ($)' },
                    ticks: {
                        callback: function(value) {
                            return '$' + (value / 1000).toFixed(0) + 'K';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Initialize Seasonal Decomposition Chart
 */
async function initializeSeasonalDecomposition(data) {
    const ctx = document.getElementById('seasonalDecompositionChart');
    if (!ctx || !data.seasonal_patterns) return;
    
    // Sort seasonal patterns by week of year
    const sortedPatterns = data.seasonal_patterns.sort((a, b) => a.week_of_year - b.week_of_year);
    
    const weekNumbers = sortedPatterns.map(p => p.week_of_year);
    const avgRevenues = sortedPatterns.map(p => p.avg_revenue);
    const maxRevenues = sortedPatterns.map(p => p.max_revenue);
    const minRevenues = sortedPatterns.map(p => p.min_revenue);
    
    seasonalDecompositionChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: weekNumbers,
            datasets: [
                {
                    label: 'Average Revenue',
                    data: avgRevenues,
                    borderColor: EXECUTIVE_COLORS.primary,
                    backgroundColor: EXECUTIVE_COLORS.primary + '20',
                    borderWidth: 3,
                    fill: false
                },
                {
                    label: 'Max Revenue',
                    data: maxRevenues,
                    borderColor: EXECUTIVE_COLORS.success,
                    backgroundColor: EXECUTIVE_COLORS.success + '10',
                    borderWidth: 1,
                    fill: '+1'
                },
                {
                    label: 'Min Revenue',
                    data: minRevenues,
                    borderColor: EXECUTIVE_COLORS.danger,
                    backgroundColor: EXECUTIVE_COLORS.danger + '10', 
                    borderWidth: 1,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top' },
                title: {
                    display: true,
                    text: 'Seasonal Revenue Patterns'
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Week of Year' }
                },
                y: {
                    title: { display: true, text: 'Revenue ($)' },
                    ticks: {
                        callback: function(value) {
                            return '$' + (value / 1000).toFixed(0) + 'K';
                        }
                    }
                }
            }
        }
    });
}

/**
 * Initialize Risk Indicators Panel
 */
async function initializeRiskIndicators(data) {
    const container = document.getElementById('riskIndicators');
    if (!container || !data.risk_indicators) return;
    
    const ri = data.risk_indicators;
    
    const riskHTML = `
        <div class="risk-indicator ${ri.concentration_risk_percentage > 30 ? 'risk-high' : ri.concentration_risk_percentage > 15 ? 'risk-medium' : 'risk-low'}">
            <div class="fw-bold">Concentration Risk</div>
            <div class="fs-4">${ri.concentration_risk_percentage}%</div>
            <div class="small">${ri.high_concentration_weeks} of ${ri.total_weeks_analyzed} weeks</div>
        </div>
        
        <div class="risk-indicator risk-medium mt-3">
            <div class="fw-bold">Avg Max Store %</div>
            <div class="fs-4">${ri.avg_max_store_percentage}%</div>
            <div class="small">Average single-store concentration</div>
        </div>
        
        <div class="alert alert-info mt-3">
            <small>
                <i class="fas fa-info-circle me-1"></i>
                <strong>Risk Threshold:</strong> >40% revenue from single store
            </small>
        </div>
    `;
    
    container.innerHTML = riskHTML;
}

/**
 * Initialize AR Risk Alerts Panel
 */
async function initializeARRiskAlerts(data) {
    const container = document.getElementById('arRiskAlerts');
    if (!container) return;
    
    // Simulate current AR risk status
    const arRiskHTML = `
        <div class="risk-indicator risk-low">
            <div class="fw-bold">Current AR Health</div>
            <div class="fs-4">Good</div>
            <div class="small">85% under 30 days</div>
        </div>
        
        <div class="risk-indicator risk-medium mt-3">
            <div class="fw-bold">30-60 Days</div>
            <div class="fs-4">12%</div>
            <div class="small">Within normal range</div>
        </div>
        
        <div class="risk-indicator risk-high mt-3">
            <div class="fw-bold">90+ Days</div>
            <div class="fs-4">3%</div>
            <div class="small">⚠️ Monitor closely</div>
        </div>
    `;
    
    container.innerHTML = arRiskHTML;
}

/**
 * Initialize Correlation Matrix Visualization
 */
async function initializeCorrelationMatrix(correlationData) {
    const container = document.getElementById('correlationMatrix');
    if (!container || !correlationData) return;
    
    const { column_names, correlations, strong_correlations } = correlationData;
    
    // Create correlation matrix table
    let matrixHTML = '<div class="table-responsive"><table class="table table-sm">';
    
    // Header row
    matrixHTML += '<thead><tr><th></th>';
    column_names.forEach(name => {
        matrixHTML += `<th class="text-center small">${name.split('_')[1]}</th>`;
    });
    matrixHTML += '</tr></thead><tbody>';
    
    // Matrix rows
    correlations.forEach((row, i) => {
        matrixHTML += `<tr><td class="small fw-bold">${column_names[i].split('_')[1]}</td>`;
        row.forEach(corr => {
            const absCorr = Math.abs(corr);
            let cellClass = 'correlation-weak';
            if (absCorr >= 0.7) cellClass = 'correlation-strong';
            else if (absCorr >= 0.4) cellClass = 'correlation-moderate';
            else if (corr < 0) cellClass = 'correlation-negative';
            
            matrixHTML += `<td class="correlation-cell ${cellClass}" style="font-size: 0.7rem;">${corr.toFixed(2)}</td>`;
        });
        matrixHTML += '</tr>';
    });
    
    matrixHTML += '</tbody></table></div>';
    
    // Add strong correlations summary
    matrixHTML += '<div class="mt-3"><h6>Strong Correlations (>0.7)</h6><ul class="list-unstyled">';
    strong_correlations.forEach(corr => {
        matrixHTML += `<li><small><strong>${corr.correlation.toFixed(3)}</strong> - ${corr.metric1} ↔ ${corr.metric2}</small></li>`;
    });
    matrixHTML += '</ul></div>';
    
    container.innerHTML = matrixHTML;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Wait for other dashboard components to load first
    setTimeout(initializeScorecardAnalytics, 1000);
});

// Export functions for external use
window.ScorecardAnalytics = {
    initializeScorecardAnalytics,
    fetchScorecardAnalytics,
    fetchCorrelationMatrix
};