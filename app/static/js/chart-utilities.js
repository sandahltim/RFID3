/**
 * RFID3 Executive Dashboard Chart Utilities
 * Enhanced visualization components with Fortune 500-level presentation
 * Version: 2025-08-28 - Executive Visual Enhancement
 */

class RFID3ChartManager {
    constructor() {
        this.charts = new Map();
        this.defaultColors = {
            primary: ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'],
            gradients: {
                primary: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                success: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
                warning: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                info: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)'
            }
        };
        this.refreshInterval = null;
        this.errorRetryCount = 0;
        this.maxRetries = 3;
    }

    /**
     * Initialize Chart.js with global defaults for executive presentation
     */
    initializeChartDefaults() {
        Chart.defaults.font.family = "'Segoe UI', system-ui, -apple-system, sans-serif";
        Chart.defaults.font.size = 12;
        Chart.defaults.color = '#4a5568';
        Chart.defaults.backgroundColor = 'rgba(255, 255, 255, 0.8)';
        
        Chart.defaults.plugins.legend.labels.usePointStyle = true;
        Chart.defaults.plugins.legend.labels.padding = 15;
        Chart.defaults.plugins.legend.labels.font = {
            weight: '600'
        };

        Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(26, 32, 44, 0.95)';
        Chart.defaults.plugins.tooltip.titleColor = '#ffffff';
        Chart.defaults.plugins.tooltip.bodyColor = '#ffffff';
        Chart.defaults.plugins.tooltip.borderColor = 'rgba(102, 126, 234, 0.8)';
        Chart.defaults.plugins.tooltip.borderWidth = 2;
        Chart.defaults.plugins.tooltip.cornerRadius = 12;
        Chart.defaults.plugins.tooltip.padding = 16;
    }

    /**
     * Create executive revenue trend chart with enhanced styling
     */
    createRevenueTrendChart(canvasId, data, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) {
            console.error(`Canvas element ${canvasId} not found`);
            return null;
        }

        // Destroy existing chart if it exists
        this.destroyChart(canvasId);

        const chartConfig = {
            type: 'line',
            data: {
                labels: data.labels || [],
                datasets: [{
                    label: 'Total Revenue',
                    data: data.values || [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#10b981',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    pointHoverBackgroundColor: '#059669',
                    pointHoverBorderColor: '#ffffff',
                    pointHoverBorderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const value = context.parsed.y;
                                return `Revenue: ${this.formatCurrency(value)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                weight: '500'
                            }
                        }
                    },
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)',
                            drawBorder: false
                        },
                        ticks: {
                            callback: (value) => this.formatCurrency(value),
                            font: {
                                weight: '500'
                            }
                        }
                    }
                },
                ...options
            }
        };

        const chart = new Chart(ctx, chartConfig);
        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Create store performance comparison chart
     */
    createStorePerformanceChart(canvasId, data, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) {
            console.error(`Canvas element ${canvasId} not found`);
            return null;
        }

        this.destroyChart(canvasId);

        const storeNames = {
            '6800': 'Brooklyn Park',
            '3607': 'Wayzata', 
            '8101': 'Fridley',
            '728': 'Elk River',
            '000': 'Legacy/Unassigned'
        };

        const chartConfig = {
            type: 'bar',
            data: {
                labels: data.stores?.map(store => storeNames[store.code] || store.code) || [],
                datasets: [{
                    label: 'Revenue per Hour',
                    data: data.values || [],
                    backgroundColor: [
                        'rgba(99, 102, 241, 0.8)',
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(245, 101, 101, 0.8)',
                        'rgba(251, 191, 36, 0.8)',
                        'rgba(139, 92, 246, 0.8)'
                    ],
                    borderColor: [
                        'rgb(99, 102, 241)',
                        'rgb(16, 185, 129)',
                        'rgb(245, 101, 101)',
                        'rgb(251, 191, 36)',
                        'rgb(139, 92, 246)'
                    ],
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const value = context.parsed.y;
                                return `Revenue/Hour: ${this.formatCurrency(value)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                weight: '600'
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)',
                            drawBorder: false
                        },
                        ticks: {
                            callback: (value) => this.formatCurrency(value),
                            font: {
                                weight: '500'
                            }
                        }
                    }
                },
                ...options
            }
        };

        const chart = new Chart(ctx, chartConfig);
        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Create inventory distribution donut chart with center text
     */
    createInventoryDistributionChart(canvasId, data, centerText = null, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) {
            console.error(`Canvas element ${canvasId} not found`);
            return null;
        }

        this.destroyChart(canvasId);

        const chartConfig = {
            type: 'doughnut',
            data: {
                labels: data.labels || [],
                datasets: [{
                    data: data.values || [],
                    backgroundColor: this.defaultColors.primary.slice(0, data.labels?.length || 0),
                    borderColor: '#ffffff',
                    borderWidth: 4,
                    hoverBorderWidth: 6,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            generateLabels: (chart) => {
                                const data = chart.data;
                                const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
                                return data.labels.map((label, index) => {
                                    const value = data.datasets[0].data[index];
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return {
                                        text: `${label} (${percentage}%)`,
                                        fillStyle: data.datasets[0].backgroundColor[index],
                                        strokeStyle: '#ffffff',
                                        lineWidth: 2,
                                        pointStyle: 'circle',
                                        hidden: false,
                                        index: index
                                    };
                                });
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const value = context.parsed;
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${context.label}: ${this.formatNumber(value)} (${percentage}%)`;
                            }
                        }
                    }
                },
                ...options
            },
            plugins: centerText ? [this.createCenterTextPlugin(canvasId, centerText)] : []
        };

        const chart = new Chart(ctx, chartConfig);
        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Create KPI scorecard visualization
     */
    createKPIScorecard(containerId, kpiData) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return;
        }

        const scorecardHtml = kpiData.map(kpi => {
            const trendIcon = kpi.trend === 'up' ? 'fa-arrow-up text-success' : 
                             kpi.trend === 'down' ? 'fa-arrow-down text-danger' : 
                             'fa-minus text-warning';
            
            const cardClass = kpi.status === 'good' ? 'border-success' :
                             kpi.status === 'warning' ? 'border-warning' :
                             'border-danger';

            return `
                <div class="col-md-3 mb-4">
                    <div class="card h-100 ${cardClass} kpi-card" data-kpi="${kpi.key}">
                        <div class="card-body text-center">
                            <div class="kpi-icon mb-2">
                                <i class="${kpi.icon} fa-2x text-${kpi.status === 'good' ? 'success' : 
                                    kpi.status === 'warning' ? 'warning' : 'danger'}"></i>
                            </div>
                            <h3 class="kpi-value mb-1" data-value="${kpi.value}">
                                ${kpi.format === 'currency' ? this.formatCurrency(kpi.value) : 
                                  kpi.format === 'percentage' ? kpi.value + '%' :
                                  this.formatNumber(kpi.value)}
                            </h3>
                            <p class="kpi-label text-muted mb-2">${kpi.label}</p>
                            <div class="kpi-trend">
                                <i class="fas ${trendIcon}"></i>
                                <span class="ms-1">${kpi.change || '0%'}</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = `<div class="row">${scorecardHtml}</div>`;
        
        // Add click handlers for drill-down
        container.querySelectorAll('.kpi-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const kpiKey = e.currentTarget.dataset.kpi;
                this.handleKPIDrilldown(kpiKey);
            });
        });
    }

    /**
     * Create real-time utilization gauge chart
     */
    createUtilizationGauge(canvasId, value, target = 75) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        this.destroyChart(canvasId);

        const chartConfig = {
            type: 'doughnut',
            data: {
                datasets: [{
                    data: [value, 100 - value],
                    backgroundColor: [
                        value >= target ? '#10b981' : value >= target * 0.8 ? '#f59e0b' : '#ef4444',
                        'rgba(229, 231, 235, 0.3)'
                    ],
                    borderWidth: 0,
                    cutout: '75%'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: false
                    }
                }
            },
            plugins: [this.createCenterTextPlugin(canvasId, {
                text: `${value}%`,
                subtext: 'Utilization',
                fontSize: 24,
                subfontSize: 14
            })]
        };

        const chart = new Chart(ctx, chartConfig);
        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Create predictive analytics forecast chart
     */
    createForecastChart(canvasId, historicalData, forecastData, options = {}) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        this.destroyChart(canvasId);

        const chartConfig = {
            type: 'line',
            data: {
                labels: [...(historicalData.labels || []), ...(forecastData.labels || [])],
                datasets: [
                    {
                        label: 'Historical',
                        data: [...(historicalData.values || []), ...Array(forecastData.labels?.length || 0).fill(null)],
                        borderColor: '#6366f1',
                        backgroundColor: 'rgba(99, 102, 241, 0.1)',
                        borderWidth: 3,
                        fill: false,
                        pointBackgroundColor: '#6366f1',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        pointRadius: 4
                    },
                    {
                        label: 'Forecast',
                        data: [...Array(historicalData.labels?.length || 0).fill(null), ...(forecastData.values || [])],
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        borderWidth: 3,
                        borderDash: [10, 5],
                        fill: false,
                        pointBackgroundColor: '#ef4444',
                        pointBorderColor: '#ffffff',
                        pointBorderWidth: 2,
                        pointRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const value = context.parsed.y;
                                return `${context.dataset.label}: ${this.formatCurrency(value)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        ticks: {
                            callback: (value) => this.formatCurrency(value)
                        }
                    }
                },
                ...options
            }
        };

        const chart = new Chart(ctx, chartConfig);
        this.charts.set(canvasId, chart);
        return chart;
    }

    /**
     * Helper function to create center text plugin
     */
    createCenterTextPlugin(chartId, textConfig) {
        return {
            id: `centerText_${chartId}`,
            afterDraw: (chart) => {
                const ctx = chart.ctx;
                const centerX = chart.chartArea.left + (chart.chartArea.right - chart.chartArea.left) / 2;
                const centerY = chart.chartArea.top + (chart.chartArea.bottom - chart.chartArea.top) / 2;
                
                ctx.save();
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillStyle = textConfig.color || '#2d3748';
                
                // Main text
                ctx.font = `bold ${textConfig.fontSize || 16}px "Segoe UI", system-ui, sans-serif`;
                ctx.fillText(textConfig.text || '', centerX, centerY - (textConfig.subtext ? 10 : 0));
                
                // Subtext
                if (textConfig.subtext) {
                    ctx.font = `${textConfig.subfontSize || 12}px "Segoe UI", system-ui, sans-serif`;
                    ctx.fillText(textConfig.subtext, centerX, centerY + 15);
                }
                
                ctx.restore();
            }
        };
    }

    /**
     * Auto-refresh functionality for real-time data
     */
    enableAutoRefresh(refreshCallback, intervalMinutes = 5) {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        this.refreshInterval = setInterval(() => {
            console.log('Auto-refreshing dashboard charts...');
            refreshCallback();
        }, intervalMinutes * 60 * 1000);
        
        console.log(`Auto-refresh enabled: ${intervalMinutes} minutes`);
    }

    /**
     * Disable auto-refresh
     */
    disableAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
            console.log('Auto-refresh disabled');
        }
    }

    /**
     * Update chart data with smooth animation
     */
    updateChartData(chartId, newData, animate = true) {
        const chart = this.charts.get(chartId);
        if (!chart) {
            console.error(`Chart ${chartId} not found`);
            return;
        }

        // Update data
        if (newData.labels) {
            chart.data.labels = newData.labels;
        }
        if (newData.datasets) {
            chart.data.datasets = newData.datasets;
        }

        // Update with animation
        chart.update(animate ? 'default' : 'none');
    }

    /**
     * Destroy specific chart
     */
    destroyChart(chartId) {
        const existingChart = this.charts.get(chartId);
        if (existingChart) {
            existingChart.destroy();
            this.charts.delete(chartId);
        }
    }

    /**
     * Destroy all charts
     */
    destroyAllCharts() {
        this.charts.forEach((chart, id) => {
            chart.destroy();
        });
        this.charts.clear();
    }

    /**
     * Handle KPI drill-down interactions
     */
    handleKPIDrilldown(kpiKey) {
        console.log(`KPI drill-down requested for: ${kpiKey}`);
        
        // Emit custom event for parent components to handle
        window.dispatchEvent(new CustomEvent('kpiDrilldown', {
            detail: { kpi: kpiKey }
        }));
    }

    /**
     * Format currency values for display
     */
    formatCurrency(amount) {
        if (amount === null || amount === undefined || isNaN(amount)) return '$0';
        
        if (Math.abs(amount) < 1000) {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: 'USD',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            }).format(amount);
        } else if (Math.abs(amount) < 1000000) {
            return `$${(amount / 1000).toFixed(1)}K`;
        } else {
            return `$${(amount / 1000000).toFixed(1)}M`;
        }
    }

    /**
     * Format numeric values for display
     */
    formatNumber(num) {
        if (num === null || num === undefined || isNaN(num)) return '0';
        
        if (Math.abs(num) < 1000) {
            return num.toString();
        } else if (Math.abs(num) < 1000000) {
            return `${(num / 1000).toFixed(1)}K`;
        } else {
            return `${(num / 1000000).toFixed(1)}M`;
        }
    }

    /**
     * Show loading state for chart container
     */
    showChartLoading(canvasId, message = 'Loading chart data...') {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        const container = canvas.parentElement;
        if (!container) return;

        const loadingHtml = `
            <div class="chart-loading d-flex flex-column align-items-center justify-content-center" style="height: 200px;">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="text-muted">${message}</p>
            </div>
        `;

        // Hide canvas and show loading
        canvas.style.display = 'none';
        
        // Remove existing loading if present
        const existingLoading = container.querySelector('.chart-loading');
        if (existingLoading) {
            existingLoading.remove();
        }
        
        container.insertAdjacentHTML('beforeend', loadingHtml);
    }

    /**
     * Hide loading state and show chart
     */
    hideChartLoading(canvasId) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        const container = canvas.parentElement;
        if (!container) return;

        // Show canvas and remove loading
        canvas.style.display = 'block';
        
        const loading = container.querySelector('.chart-loading');
        if (loading) {
            loading.remove();
        }
    }

    /**
     * Show error state for chart
     */
    showChartError(canvasId, message = 'Failed to load chart data') {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;

        const container = canvas.parentElement;
        const errorHtml = `
            <div class="chart-error alert alert-danger d-flex align-items-center" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <div>
                    <strong>Chart Error:</strong> ${message}
                    <button class="btn btn-sm btn-outline-danger ms-2" onclick="window.chartManager.retryChart('${canvasId}')">
                        <i class="fas fa-redo"></i> Retry
                    </button>
                </div>
            </div>
        `;

        canvas.style.display = 'none';
        
        // Remove existing error if present
        const existingError = container.querySelector('.chart-error');
        if (existingError) {
            existingError.remove();
        }
        
        container.insertAdjacentHTML('beforeend', errorHtml);
    }

    /**
     * Retry failed chart loading
     */
    retryChart(canvasId) {
        if (this.errorRetryCount < this.maxRetries) {
            this.errorRetryCount++;
            console.log(`Retrying chart ${canvasId}, attempt ${this.errorRetryCount}`);
            
            // Remove error display
            const canvas = document.getElementById(canvasId);
            if (canvas) {
                canvas.style.display = 'block';
                const container = canvas.parentElement;
                const error = container.querySelector('.chart-error');
                if (error) error.remove();
            }
            
            // Emit retry event
            window.dispatchEvent(new CustomEvent('chartRetry', {
                detail: { chartId: canvasId, attempt: this.errorRetryCount }
            }));
        } else {
            console.error(`Max retry attempts reached for chart ${canvasId}`);
        }
    }
}

// Initialize global chart manager
window.chartManager = new RFID3ChartManager();

// Auto-initialize Chart.js defaults when script loads
document.addEventListener('DOMContentLoaded', () => {
    window.chartManager.initializeChartDefaults();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RFID3ChartManager;
}
