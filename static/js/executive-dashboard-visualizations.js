/**
 * Executive Dashboard Enhanced Visualizations
 * Multi-location Equipment Rental Business Analytics
 */

class ExecutiveDashboardVisualizations {
    constructor() {
        this.charts = {};
        this.sparklines = {};
        this.gauges = {};
        this.counters = {};
        this.map = null;
        this.locationData = [
            { name: 'Wayzata', code: 'WAY', lat: 44.9737, lng: -93.5067, color: '#3b82f6' },
            { name: 'Brooklyn Park', code: 'BRP', lat: 45.0942, lng: -93.3563, color: '#10b981' },
            { name: 'Fridley', code: 'FRD', lat: 45.0861, lng: -93.2635, color: '#f59e0b' },
            { name: 'Elk River', code: 'ELK', lat: 45.3077, lng: -93.5677, color: '#ef4444' }
        ];
        this.init();
    }

    init() {
        this.initializeAnimatedCounters();
        this.initializeSparklines();
        this.initializeGaugeCharts();
        this.initializePerformanceHeatmap();
        this.initializeWaterfallChart();
        this.initializeLocationMap();
        this.initializePerformanceComparison();
        this.setupInteractiveControls();
    }

    // Animated Counter Implementation
    initializeAnimatedCounters() {
        const counterElements = document.querySelectorAll('.animated-counter');
        
        counterElements.forEach(element => {
            const countUp = new CountUp(element.id, 0, {
                duration: 2,
                useEasing: true,
                useGrouping: true,
                separator: ',',
                decimal: '.',
                prefix: element.textContent.includes('$') ? '$' : '',
                suffix: element.textContent.includes('%') ? '%' : ''
            });
            
            this.counters[element.id] = countUp;
        });
    }

    updateAnimatedCounter(elementId, value, options = {}) {
        if (this.counters[elementId]) {
            const element = document.getElementById(elementId);
            const prefix = options.prefix || (element.textContent.includes('$') ? '$' : '');
            const suffix = options.suffix || (element.textContent.includes('%') ? '%' : '');
            
            this.counters[elementId].options.prefix = prefix;
            this.counters[elementId].options.suffix = suffix;
            this.counters[elementId].update(value);
            
            // Add pulse animation for significant changes
            if (Math.abs(value - this.counters[elementId].endVal) > (this.counters[elementId].endVal * 0.1)) {
                element.classList.add('pulse-animation');
                setTimeout(() => element.classList.remove('pulse-animation'), 2000);
            }
        }
    }

    // Sparkline Charts
    initializeSparklines() {
        const sparklineConfigs = {
            revenueSparkline: { color: '#3b82f6', fill: 'rgba(59, 130, 246, 0.1)' },
            growthSparkline: { color: '#10b981', fill: 'rgba(16, 185, 129, 0.1)' },
            utilizationSparkline: { color: '#f59e0b', fill: 'rgba(245, 158, 11, 0.1)' },
            healthSparkline: { color: '#0369a1', fill: 'rgba(3, 105, 161, 0.1)' }
        };

        Object.keys(sparklineConfigs).forEach(canvasId => {
            const canvas = document.getElementById(canvasId);
            if (canvas) {
                const ctx = canvas.getContext('2d');
                const config = sparklineConfigs[canvasId];
                
                this.sparklines[canvasId] = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            data: [],
                            borderColor: config.color,
                            backgroundColor: config.fill,
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4,
                            pointRadius: 0,
                            pointHoverRadius: 3
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                mode: 'index',
                                intersect: false,
                                displayColors: false
                            }
                        },
                        scales: {
                            x: { display: false },
                            y: { display: false }
                        },
                        interaction: {
                            intersect: false
                        }
                    }
                });
            }
        });
    }

    updateSparkline(chartId, data, labels) {
        if (this.sparklines[chartId]) {
            this.sparklines[chartId].data.labels = labels;
            this.sparklines[chartId].data.datasets[0].data = data;
            this.sparklines[chartId].update('none');
        }
    }

    // Gauge Charts
    initializeGaugeCharts() {
        this.initializeGauge('utilizationGauge', 'utilizationGaugeValue', '#3b82f6');
        this.initializeGauge('healthGauge', 'healthGaugeValue', '#10b981');
        this.initializeGauge('efficiencyGauge', 'efficiencyGaugeValue', '#f59e0b');
    }

    initializeGauge(gaugeId, valueId, color) {
        const gauge = document.getElementById(gaugeId);
        if (gauge) {
            const circumference = 2 * Math.PI * 80;
            gauge.style.strokeDasharray = `${circumference} ${circumference}`;
            gauge.style.strokeDashoffset = circumference;
            gauge.style.stroke = color;
            
            this.gauges[gaugeId] = {
                element: gauge,
                valueElement: document.getElementById(valueId),
                circumference: circumference,
                currentValue: 0
            };
        }
    }

    updateGauge(gaugeId, percentage, animationDuration = 1000) {
        const gauge = this.gauges[gaugeId];
        if (!gauge) return;

        const targetOffset = gauge.circumference - (percentage / 100) * gauge.circumference;
        
        // Cancel any existing animation
        if (gauge.animation) {
            clearInterval(gauge.animation);
        }

        const startOffset = parseFloat(gauge.element.style.strokeDashoffset) || gauge.circumference;
        const startTime = Date.now();

        gauge.animation = setInterval(() => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / animationDuration, 1);
            
            // Easing function
            const easeOutCubic = 1 - Math.pow(1 - progress, 3);
            const currentOffset = startOffset + (targetOffset - startOffset) * easeOutCubic;
            
            gauge.element.style.strokeDashoffset = currentOffset;
            
            // Update value display
            const currentPercentage = Math.round((1 - currentOffset / gauge.circumference) * 100);
            if (gauge.valueElement) {
                gauge.valueElement.textContent = gaugeId.includes('health') ? 
                    Math.round(percentage * 10) : `${currentPercentage}%`;
            }

            if (progress >= 1) {
                clearInterval(gauge.animation);
                gauge.currentValue = percentage;
            }
        }, 16); // ~60fps
    }

    // Performance Heatmap
    initializePerformanceHeatmap() {
        this.renderHeatmap('revenue');
        this.setupHeatmapControls();
    }

    renderHeatmap(metric) {
        const container = document.getElementById('performanceHeatmap');
        if (!container) return;

        // Sample data - replace with actual data
        const heatmapData = {
            revenue: {
                'Wayzata': 92,
                'Brooklyn Park': 87,
                'Fridley': 73,
                'Elk River': 89
            },
            utilization: {
                'Wayzata': 85,
                'Brooklyn Park': 92,
                'Fridley': 78,
                'Elk River': 83
            },
            health: {
                'Wayzata': 8.7,
                'Brooklyn Park': 9.2,
                'Fridley': 7.3,
                'Elk River': 8.9
            }
        };

        const data = heatmapData[metric];
        const maxValue = Math.max(...Object.values(data));
        
        container.innerHTML = '';

        Object.keys(data).forEach((location, index) => {
            const value = data[location];
            const intensity = value / maxValue;
            const performanceClass = this.getPerformanceClass(intensity);
            
            const cell = document.createElement('div');
            cell.className = `col-lg-3 col-md-6 mb-3`;
            cell.innerHTML = `
                <div class="heatmap-cell ${performanceClass}" 
                     style="height: 120px; position: relative;"
                     data-location="${location}" data-value="${value}">
                    <div class="text-center">
                        <h5 class="mb-1">${location}</h5>
                        <div class="fs-4 fw-bold">
                            ${metric === 'health' ? value.toFixed(1) : 
                              metric === 'revenue' ? `${value}%` : `${value}%`}
                        </div>
                        <small class="opacity-75">
                            ${metric === 'health' ? 'Health Score' : 
                              metric === 'revenue' ? 'Revenue Target' : 'Utilization Rate'}
                        </small>
                    </div>
                </div>
            `;
            
            container.appendChild(cell);

            // Add click handler for drill-down
            cell.querySelector('.heatmap-cell').addEventListener('click', () => {
                this.showLocationDetails(location, metric, value);
            });
        });

        // Update active button
        document.querySelectorAll('[id^="heatmap"]').forEach(btn => {
            btn.classList.remove('active');
        });
        document.getElementById(`heatmap${metric.charAt(0).toUpperCase() + metric.slice(1)}`).classList.add('active');
    }

    getPerformanceClass(intensity) {
        if (intensity >= 0.9) return 'performance-excellent';
        if (intensity >= 0.75) return 'performance-good';
        if (intensity >= 0.6) return 'performance-average';
        return 'performance-poor';
    }

    setupHeatmapControls() {
        document.getElementById('heatmapRevenue')?.addEventListener('click', () => this.renderHeatmap('revenue'));
        document.getElementById('heatmapUtilization')?.addEventListener('click', () => this.renderHeatmap('utilization'));
        document.getElementById('heatmapHealth')?.addEventListener('click', () => this.renderHeatmap('health'));
    }

    showLocationDetails(location, metric, value) {
        // Create a modal or detailed view for location-specific data
        console.log(`Showing details for ${location}: ${metric} = ${value}`);
        // Implementation for detailed location view
    }

    // Waterfall Chart
    initializeWaterfallChart() {
        const ctx = document.getElementById('waterfallChart');
        if (!ctx) return;

        this.charts.waterfall = new Chart(ctx.getContext('2d'), {
            type: 'bar',
            data: {
                labels: ['Starting Revenue', 'Wayzata', 'Brooklyn Park', 'Fridley', 'Elk River', 'Total Revenue'],
                datasets: [{
                    label: 'Revenue Flow',
                    data: [0, 125000, 98000, 67000, 89000, 379000],
                    backgroundColor: [
                        '#6b7280',  // Starting
                        '#3b82f6',  // Wayzata
                        '#10b981',  // Brooklyn Park
                        '#f59e0b',  // Fridley
                        '#ef4444',  // Elk River
                        '#059669'   // Total
                    ],
                    borderColor: [
                        '#4b5563', '#1e40af', '#059669', '#d97706', '#dc2626', '#047857'
                    ],
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const value = context.parsed.y;
                                return `Revenue: $${value.toLocaleString()}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: (value) => `$${(value/1000).toFixed(0)}K`
                        }
                    }
                },
                animation: {
                    duration: 2000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    // Location Map
    initializeLocationMap() {
        const mapContainer = document.getElementById('locationMap');
        if (!mapContainer) return;

        // Initialize Leaflet map centered on Minnesota locations
        this.map = L.map('locationMap').setView([45.0, -93.4], 10);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);

        // Add location markers
        this.locationData.forEach(location => {
            const marker = L.circleMarker([location.lat, location.lng], {
                radius: 12,
                color: location.color,
                fillColor: location.color,
                fillOpacity: 0.8,
                weight: 3
            }).addTo(this.map);

            // Custom popup with performance data
            const popupContent = `
                <div class="text-center p-2">
                    <h6 class="mb-2">${location.name}</h6>
                    <div class="small">
                        <div>Revenue: <span class="fw-bold text-success">$125K</span></div>
                        <div>Utilization: <span class="fw-bold text-primary">85%</span></div>
                        <div>Health: <span class="fw-bold text-info">8.7</span></div>
                    </div>
                    <button class="btn btn-sm btn-outline-primary mt-2" 
                            onclick="dashboard.showLocationDashboard('${location.code}')">
                        View Details
                    </button>
                </div>
            `;

            marker.bindPopup(popupContent);

            // Hover effects
            marker.on('mouseover', () => {
                marker.setRadius(16);
            });

            marker.on('mouseout', () => {
                marker.setRadius(12);
            });
        });
    }

    // Performance Comparison Chart
    initializePerformanceComparison() {
        const ctx = document.getElementById('performanceComparisonChart');
        if (!ctx) return;

        this.charts.comparison = new Chart(ctx.getContext('2d'), {
            type: 'radar',
            data: {
                labels: ['Revenue', 'Utilization', 'Health Score', 'Growth', 'Efficiency', 'Customer Satisfaction'],
                datasets: [
                    {
                        label: 'Wayzata',
                        data: [92, 85, 87, 78, 89, 91],
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderWidth: 2,
                        pointBackgroundColor: '#3b82f6'
                    },
                    {
                        label: 'Brooklyn Park',
                        data: [87, 92, 92, 85, 88, 87],
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        borderWidth: 2,
                        pointBackgroundColor: '#10b981'
                    },
                    {
                        label: 'Fridley',
                        data: [73, 78, 73, 82, 75, 79],
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        borderWidth: 2,
                        pointBackgroundColor: '#f59e0b'
                    },
                    {
                        label: 'Elk River',
                        data: [89, 83, 89, 91, 86, 88],
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        borderWidth: 2,
                        pointBackgroundColor: '#ef4444'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                },
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20
                        }
                    }
                },
                animation: {
                    duration: 2000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    setupInteractiveControls() {
        // Add keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case '1':
                        e.preventDefault();
                        this.renderHeatmap('revenue');
                        break;
                    case '2':
                        e.preventDefault();
                        this.renderHeatmap('utilization');
                        break;
                    case '3':
                        e.preventDefault();
                        this.renderHeatmap('health');
                        break;
                }
            }
        });

        // Add refresh data functionality
        setInterval(() => {
            this.refreshAllVisualizations();
        }, 30000); // Refresh every 30 seconds
    }

    // Public methods for updating data
    updateDashboardData(data) {
        // Update KPI counters
        if (data.revenue) {
            this.updateAnimatedCounter('revenueKPI', data.revenue.value, { prefix: '$' });
            this.updateSparkline('revenueSparkline', data.revenue.trend, data.revenue.labels);
        }

        if (data.growth) {
            this.updateAnimatedCounter('growthKPI', data.growth.value, { suffix: '%' });
            this.updateSparkline('growthSparkline', data.growth.trend, data.growth.labels);
        }

        if (data.utilization) {
            this.updateAnimatedCounter('utilizationKPI', data.utilization.value, { suffix: '%' });
            this.updateSparkline('utilizationSparkline', data.utilization.trend, data.utilization.labels);
            this.updateGauge('utilizationGauge', data.utilization.value);
        }

        if (data.health) {
            this.updateAnimatedCounter('healthKPI', data.health.value);
            this.updateSparkline('healthSparkline', data.health.trend, data.health.labels);
            this.updateGauge('healthGauge', data.health.value * 10); // Convert to percentage for gauge
        }

        if (data.efficiency) {
            this.updateGauge('efficiencyGauge', data.efficiency.value);
        }
    }

    refreshAllVisualizations() {
        // Simulate real-time updates
        const sampleData = {
            revenue: {
                value: Math.floor(Math.random() * 50000) + 350000,
                trend: Array.from({length: 7}, () => Math.floor(Math.random() * 10000) + 45000),
                labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6', 'Week 7']
            },
            growth: {
                value: Math.random() * 20 + 10,
                trend: Array.from({length: 7}, () => Math.random() * 5 + 8),
                labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6', 'Week 7']
            },
            utilization: {
                value: Math.random() * 30 + 70,
                trend: Array.from({length: 7}, () => Math.random() * 20 + 75),
                labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6', 'Week 7']
            },
            health: {
                value: Math.random() * 2 + 8,
                trend: Array.from({length: 7}, () => Math.random() * 1 + 7.5),
                labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6', 'Week 7']
            },
            efficiency: {
                value: Math.random() * 25 + 75
            }
        };

        this.updateDashboardData(sampleData);
    }

    // Utility method for location dashboard navigation
    showLocationDashboard(locationCode) {
        console.log(`Navigating to ${locationCode} dashboard`);
        // Implementation for location-specific dashboard
        window.location.href = `/location-dashboard/${locationCode}`;
    }

    // Method to export visualization data
    exportVisualizationData() {
        const exportData = {
            timestamp: new Date().toISOString(),
            charts: Object.keys(this.charts),
            sparklines: Object.keys(this.sparklines),
            gauges: Object.keys(this.gauges),
            locations: this.locationData
        };

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `executive-dashboard-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }
}

// Global instance
window.dashboard = new ExecutiveDashboardVisualizations();