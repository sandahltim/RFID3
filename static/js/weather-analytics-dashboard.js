/**
 * Minnesota Weather Analytics Dashboard
 * JavaScript for weather-rental correlation analytics
 */

class WeatherAnalyticsDashboard {
    constructor() {
        this.currentStore = '';
        this.charts = {};
        this.data = {};
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.updateCurrentTime();
        this.loadInitialData();
        
        // Update time every minute
        setInterval(() => this.updateCurrentTime(), 60000);
        
        // Auto-refresh data every 30 minutes
        setInterval(() => this.refreshAllData(), 1800000);
    }
    
    setupEventListeners() {
        // Store selector
        document.getElementById('store-selector').addEventListener('change', (e) => {
            this.currentStore = e.target.value;
            this.loadDashboardData();
        });
        
        // Refresh button
        document.getElementById('refresh-data').addEventListener('click', () => {
            this.refreshAllData();
        });
        
        // Tab change events
        document.querySelectorAll('[data-bs-toggle="pill"]').forEach(tab => {
            tab.addEventListener('shown.bs.tab', (e) => {
                const targetTab = e.target.getAttribute('data-bs-target').replace('#', '');
                this.handleTabChange(targetTab);
            });
        });
    }
    
    updateCurrentTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });
        document.getElementById('current-time').textContent = timeString;
    }
    
    async loadInitialData() {
        this.showLoading();
        
        try {
            // Load current weather and dashboard data in parallel
            await Promise.all([
                this.loadCurrentWeather(),
                this.loadDashboardData()
            ]);
            
            this.hideLoading();
            this.updateLastUpdated();
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.showError('Failed to load dashboard data');
        }
    }
    
    async loadCurrentWeather() {
        try {
            const response = await fetch('/api/minnesota-weather/current-weather/MSP');
            const data = await response.json();
            
            if (data.status === 'success') {
                this.updateCurrentWeatherDisplay(data.weather_data);
            }
        } catch (error) {
            console.error('Failed to load current weather:', error);
        }
    }
    
    updateCurrentWeatherDisplay(weatherData) {
        document.getElementById('current-temp').textContent = 
            weatherData.temperature ? `${Math.round(weatherData.temperature)}°F` : '--°F';
        document.getElementById('current-humidity').textContent = 
            weatherData.humidity ? `${Math.round(weatherData.humidity)}%` : '--%';
        document.getElementById('current-wind').textContent = 
            weatherData.wind_speed ? `${Math.round(weatherData.wind_speed)} mph` : '-- mph';
        document.getElementById('current-precip').textContent = '0.0"'; // Current precipitation
        document.getElementById('current-conditions').textContent = 
            weatherData.weather_description || 'Weather conditions unavailable';
        
        // Update weather icon based on conditions
        this.updateWeatherIcon(weatherData.weather_description);
    }
    
    updateWeatherIcon(condition) {
        const iconElement = document.getElementById('current-weather-icon');
        let iconClass = 'wi wi-day-sunny'; // default
        
        if (condition) {
            const conditionLower = condition.toLowerCase();
            if (conditionLower.includes('rain') || conditionLower.includes('shower')) {
                iconClass = 'wi wi-rain';
            } else if (conditionLower.includes('cloud')) {
                iconClass = 'wi wi-cloudy';
            } else if (conditionLower.includes('storm')) {
                iconClass = 'wi wi-thunderstorm';
            } else if (conditionLower.includes('snow')) {
                iconClass = 'wi wi-snow';
            } else if (conditionLower.includes('clear') || conditionLower.includes('sunny')) {
                iconClass = 'wi wi-day-sunny';
            }
        }
        
        iconElement.className = `${iconClass} weather-icon`;
    }
    
    async loadDashboardData() {
        try {
            const params = new URLSearchParams();
            if (this.currentStore) {
                params.append('store_code', this.currentStore);
            }
            params.append('days_back', '90');
            
            const response = await fetch(`/api/minnesota-weather/weather-dashboard-data?${params}`);
            const data = await response.json();
            
            if (data.status !== 'error') {
                this.data.dashboard = data;
                this.updateOverviewTab();
                this.updateCorrelationsTab();
            } else {
                console.error('Dashboard data error:', data.error);
            }
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        }
    }
    
    updateOverviewTab() {
        const dashboard = this.data.dashboard;
        
        if (dashboard && dashboard.weather_correlations) {
            const correlations = dashboard.weather_correlations;
            
            // Update key metrics
            if (correlations.key_metrics) {
                const metrics = correlations.key_metrics;
                
                document.getElementById('weather-sensitivity-score').textContent = 
                    metrics.weather_sensitivity_score ? 
                    `${Math.round(metrics.weather_sensitivity_score * 100)}%` : '--%';
                
                document.getElementById('significant-correlations').textContent = 
                    metrics.total_significant_correlations || '--';
                
                document.getElementById('forecast-confidence').textContent = '85%'; // Default confidence
            }
            
            // Update insights
            if (correlations.insights) {
                this.updateInsights(correlations.insights);
            }
            
            // Create weather-revenue chart
            this.createWeatherRevenueChart();
        }
    }
    
    updateInsights(insights) {
        const container = document.getElementById('key-insights');
        container.innerHTML = '';
        
        insights.slice(0, 5).forEach(insight => {
            const insightElement = document.createElement('div');
            insightElement.className = 'insight-item';
            insightElement.innerHTML = `
                <i class="wi wi-lightbulb text-primary me-2"></i>
                ${insight}
            `;
            container.appendChild(insightElement);
        });
    }
    
    updateCorrelationsTab() {
        const dashboard = this.data.dashboard;
        
        if (dashboard && dashboard.weather_correlations && dashboard.weather_correlations.correlations) {
            const correlations = dashboard.weather_correlations.correlations;
            
            // Update temperature correlation
            this.updateCorrelationMeter('temp', correlations.temperature_high);
            
            // Update precipitation correlation
            this.updateCorrelationMeter('precip', correlations.precipitation);
            
            // Create correlation matrix chart
            this.createCorrelationMatrixChart(correlations);
        }
    }
    
    updateCorrelationMeter(type, correlationData) {
        if (!correlationData || !correlationData.daily_revenue) return;
        
        const correlation = correlationData.daily_revenue.pearson_correlation;
        const pValue = correlationData.daily_revenue.pearson_p_value;
        
        // Update indicator position (correlation range -1 to 1, meter 0% to 100%)
        const position = ((correlation + 1) / 2) * 100;
        document.getElementById(`${type}-correlation-indicator`).style.left = `${position}%`;
        
        // Update values
        document.getElementById(`${type}-correlation-value`).textContent = correlation.toFixed(3);
        document.getElementById(`${type}-p-value`).textContent = pValue.toFixed(4);
    }
    
    async handleTabChange(tabName) {
        switch (tabName) {
            case 'forecasting':
                await this.loadForecastingData();
                break;
            case 'seasonal':
                await this.loadSeasonalData();
                break;
            case 'inventory':
                await this.loadInventoryData();
                break;
        }
    }
    
    async loadForecastingData() {
        try {
            const params = new URLSearchParams();
            if (this.currentStore) {
                params.append('store_code', this.currentStore);
            }
            params.append('days', '14');
            params.append('confidence', 'true');
            
            const response = await fetch(`/api/minnesota-weather/demand-forecast?${params}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                this.data.forecast = data;
                this.updateForecastingTab();
            }
        } catch (error) {
            console.error('Failed to load forecasting data:', error);
        }
    }
    
    updateForecastingTab() {
        const forecast = this.data.forecast;
        
        if (forecast && forecast.forecast_summary) {
            const summary = forecast.forecast_summary;
            
            // Update summary metrics
            document.getElementById('forecast-total-revenue').textContent = 
                `$${this.formatCurrency(summary.total_predicted_revenue)}`;
            document.getElementById('forecast-avg-daily').textContent = 
                `$${this.formatCurrency(summary.avg_daily_revenue)}`;
            
            if (summary.peak_day) {
                const peakDate = new Date(summary.peak_day.date);
                document.getElementById('forecast-peak-day').textContent = 
                    peakDate.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
            }
            
            // Create forecast chart
            this.createDemandForecastChart();
            
            // Update forecast list
            this.updateForecastList();
        }
    }
    
    updateForecastList() {
        const container = document.getElementById('forecast-list');
        container.innerHTML = '';
        
        if (this.data.forecast && this.data.forecast.daily_forecasts) {
            this.data.forecast.daily_forecasts.slice(0, 7).forEach(forecast => {
                const date = new Date(forecast.forecast_date);
                const riskClass = this.getRiskClass(forecast.risk_factors);
                
                const forecastElement = document.createElement('div');
                forecastElement.className = `forecast-item ${riskClass}`;
                forecastElement.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</strong>
                            <br>
                            <small class="text-muted">${forecast.weather_conditions.weather_condition}</small>
                        </div>
                        <div class="text-end">
                            <strong>$${this.formatCurrency(forecast.predictions.daily_revenue)}</strong>
                            <br>
                            <small class="text-muted">${forecast.predictions.daily_contracts} contracts</small>
                        </div>
                    </div>
                    ${forecast.recommendations && forecast.recommendations.length > 0 ? 
                        `<div class="mt-2"><small><i class="wi wi-lightbulb"></i> ${forecast.recommendations[0]}</small></div>` : ''}
                `;
                container.appendChild(forecastElement);
            });
        }
    }
    
    async loadSeasonalData() {
        try {
            const params = new URLSearchParams();
            params.append('years_back', '3');
            if (this.currentStore) {
                params.append('store_code', this.currentStore);
            }
            
            const response = await fetch(`/api/minnesota-weather/seasonal-analysis?${params}`);
            const data = await response.json();
            
            if (data.status !== 'error') {
                this.data.seasonal = data;
                this.updateSeasonalTab();
            }
        } catch (error) {
            console.error('Failed to load seasonal data:', error);
        }
    }
    
    updateSeasonalTab() {
        const seasonal = this.data.seasonal;
        
        if (seasonal && seasonal.seasonal_events) {
            this.createSeasonalChart();
            this.updateSeasonalEvents();
        }
    }
    
    updateSeasonalEvents() {
        const container = document.getElementById('seasonal-events');
        container.innerHTML = '';
        
        if (this.data.seasonal && this.data.seasonal.seasonal_events) {
            Object.entries(this.data.seasonal.seasonal_events).forEach(([eventName, eventData]) => {
                const eventElement = document.createElement('div');
                eventElement.className = 'mb-3 p-3 bg-light rounded';
                eventElement.innerHTML = `
                    <h6 class="fw-bold">${this.formatEventName(eventName)}</h6>
                    <p class="mb-2 small">${eventData.event_config.description}</p>
                    <div class="row">
                        <div class="col-6">
                            <small class="text-muted">Revenue:</small><br>
                            <strong>$${this.formatCurrency(eventData.performance_metrics.total_revenue)}</strong>
                        </div>
                        <div class="col-6">
                            <small class="text-muted">Contracts:</small><br>
                            <strong>${eventData.performance_metrics.contract_count}</strong>
                        </div>
                    </div>
                `;
                container.appendChild(eventElement);
            });
        }
    }
    
    async loadInventoryData() {
        try {
            const params = new URLSearchParams();
            if (this.currentStore) {
                params.append('store_code', this.currentStore);
            }
            
            const response = await fetch(`/api/minnesota-weather/equipment-categorization?${params}`);
            const data = await response.json();
            
            if (data.status === 'success') {
                this.data.inventory = data.categorization_data;
                this.updateInventoryTab();
            }
        } catch (error) {
            console.error('Failed to load inventory data:', error);
        }
    }
    
    updateInventoryTab() {
        if (this.data.inventory) {
            this.createInventoryMixChart();
            this.createWeatherDependencyChart();
            this.updateRecommendations();
        }
    }
    
    updateRecommendations() {
        const container = document.getElementById('recommendations-list');
        container.innerHTML = '';
        
        // Default recommendations based on weather analytics
        const recommendations = [
            'Monitor weather forecasts 3-7 days ahead for outdoor equipment planning',
            'Implement dynamic pricing based on weather conditions',
            'Cross-train staff on different equipment categories for seasonal flexibility',
            'Consider weather-contingent rental agreements for outdoor events',
            'Develop inventory transfer protocols between stores based on weather patterns'
        ];
        
        recommendations.forEach(rec => {
            const recElement = document.createElement('div');
            recElement.className = 'recommendation-item';
            recElement.innerHTML = `
                <i class="wi wi-direction-up text-warning me-2"></i>
                ${rec}
            `;
            container.appendChild(recElement);
        });
    }
    
    // Chart creation methods
    createWeatherRevenueChart() {
        const ctx = document.getElementById('weather-revenue-chart').getContext('2d');
        
        if (this.charts.weatherRevenue) {
            this.charts.weatherRevenue.destroy();
        }
        
        // Sample data - would be replaced with actual API data
        const data = {
            labels: this.generateDateLabels(30),
            datasets: [{
                label: 'Daily Revenue',
                data: this.generateSampleRevenueData(30),
                borderColor: '#74b9ff',
                backgroundColor: 'rgba(116, 185, 255, 0.1)',
                tension: 0.4,
                yAxisID: 'y'
            }, {
                label: 'Weather Score',
                data: this.generateSampleWeatherData(30),
                borderColor: '#fdcb6e',
                backgroundColor: 'rgba(253, 203, 110, 0.1)',
                tension: 0.4,
                yAxisID: 'y1'
            }]
        };
        
        this.charts.weatherRevenue = new Chart(ctx, {
            type: 'line',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day'
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Revenue ($)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Weather Score'
                        },
                        grid: {
                            drawOnChartArea: false
                        }
                    }
                }
            }
        });
    }
    
    createCorrelationMatrixChart(correlations) {
        const ctx = document.getElementById('correlation-matrix-chart').getContext('2d');
        
        if (this.charts.correlationMatrix) {
            this.charts.correlationMatrix.destroy();
        }
        
        // Extract correlation values for matrix display
        const weatherFactors = ['Temperature', 'Precipitation', 'Wind Speed', 'Humidity'];
        const businessMetrics = ['Daily Revenue', 'Daily Contracts', 'Items Rented'];
        
        const matrixData = [];
        weatherFactors.forEach((weather, i) => {
            businessMetrics.forEach((business, j) => {
                matrixData.push({
                    x: j,
                    y: i,
                    v: Math.random() * 2 - 1 // Sample correlation value
                });
            });
        });
        
        this.charts.correlationMatrix = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Correlation Strength',
                    data: matrixData,
                    backgroundColor: (ctx) => {
                        const value = ctx.parsed.v;
                        const alpha = Math.abs(value);
                        return value > 0 ? 
                            `rgba(0, 184, 148, ${alpha})` : 
                            `rgba(225, 112, 85, ${alpha})`;
                    },
                    pointRadius: 20
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        min: -0.5,
                        max: businessMetrics.length - 0.5,
                        ticks: {
                            callback: function(value) {
                                return businessMetrics[Math.round(value)] || '';
                            }
                        }
                    },
                    y: {
                        min: -0.5,
                        max: weatherFactors.length - 0.5,
                        ticks: {
                            callback: function(value) {
                                return weatherFactors[Math.round(value)] || '';
                            }
                        }
                    }
                }
            }
        });
    }
    
    createDemandForecastChart() {
        const ctx = document.getElementById('demand-forecast-chart').getContext('2d');
        
        if (this.charts.demandForecast) {
            this.charts.demandForecast.destroy();
        }
        
        let forecastData = [];
        let confidenceBands = [];
        
        if (this.data.forecast && this.data.forecast.daily_forecasts) {
            forecastData = this.data.forecast.daily_forecasts.map(f => ({
                x: f.forecast_date,
                y: f.predictions.daily_revenue
            }));
            
            confidenceBands = this.data.forecast.daily_forecasts.map(f => {
                const confidence = f.confidence_intervals && f.confidence_intervals.daily_revenue ? 
                    f.confidence_intervals.daily_revenue['80_percent'] : null;
                return {
                    x: f.forecast_date,
                    y: confidence ? confidence.upper : f.predictions.daily_revenue * 1.2,
                    yMin: confidence ? confidence.lower : f.predictions.daily_revenue * 0.8
                };
            });
        }
        
        this.charts.demandForecast = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [{
                    label: 'Predicted Revenue',
                    data: forecastData,
                    borderColor: '#74b9ff',
                    backgroundColor: 'rgba(116, 185, 255, 0.1)',
                    tension: 0.4
                }, {
                    label: '80% Confidence Band',
                    data: confidenceBands,
                    borderColor: 'rgba(116, 185, 255, 0.3)',
                    backgroundColor: 'rgba(116, 185, 255, 0.1)',
                    fill: '+1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Revenue ($)'
                        }
                    }
                }
            }
        });
    }
    
    createSeasonalChart() {
        const ctx = document.getElementById('seasonal-chart').getContext('2d');
        
        if (this.charts.seasonal) {
            this.charts.seasonal.destroy();
        }
        
        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        
        this.charts.seasonal = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: months,
                datasets: [{
                    label: 'Party/Event Equipment',
                    data: [20, 25, 40, 60, 85, 95, 100, 90, 75, 65, 45, 35],
                    backgroundColor: 'rgba(116, 185, 255, 0.8)'
                }, {
                    label: 'Construction/DIY',
                    data: [30, 35, 55, 80, 90, 95, 85, 80, 70, 60, 40, 25],
                    backgroundColor: 'rgba(253, 203, 110, 0.8)'
                }, {
                    label: 'Landscaping',
                    data: [10, 15, 30, 70, 85, 90, 80, 75, 65, 50, 25, 15],
                    backgroundColor: 'rgba(0, 184, 148, 0.8)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        title: {
                            display: true,
                            text: 'Seasonal Index (%)'
                        }
                    }
                }
            }
        });
    }
    
    createInventoryMixChart() {
        const ctx = document.getElementById('inventory-mix-chart').getContext('2d');
        
        if (this.charts.inventoryMix) {
            this.charts.inventoryMix.destroy();
        }
        
        let data = {
            labels: ['Party/Event', 'Construction/DIY', 'Landscaping', 'Mixed'],
            datasets: [{
                data: [35, 45, 15, 5],
                backgroundColor: [
                    '#74b9ff',
                    '#fdcb6e', 
                    '#00b894',
                    '#636e72'
                ]
            }]
        };
        
        // Use actual data if available
        if (this.data.inventory && this.data.inventory.industry_breakdown) {
            const breakdown = this.data.inventory.industry_breakdown;
            data.labels = breakdown.map(item => this.formatSegmentName(item.industry_segment));
            data.datasets[0].data = breakdown.map(item => item.revenue_percentage);
        }
        
        this.charts.inventoryMix = new Chart(ctx, {
            type: 'doughnut',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    createWeatherDependencyChart() {
        const ctx = document.getElementById('weather-dependency-chart').getContext('2d');
        
        if (this.charts.weatherDependency) {
            this.charts.weatherDependency.destroy();
        }
        
        this.charts.weatherDependency = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['High Dependency', 'Medium Dependency', 'Low Dependency', 'Weather Independent'],
                datasets: [{
                    label: 'Number of Items',
                    data: [120, 85, 45, 30],
                    backgroundColor: [
                        '#e17055',
                        '#fdcb6e',
                        '#74b9ff', 
                        '#00b894'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        title: {
                            display: true,
                            text: 'Number of Equipment Items'
                        }
                    }
                }
            }
        });
    }
    
    // Utility methods
    generateDateLabels(days) {
        const labels = [];
        const now = new Date();
        
        for (let i = days - 1; i >= 0; i--) {
            const date = new Date(now);
            date.setDate(date.getDate() - i);
            labels.push(date);
        }
        
        return labels;
    }
    
    generateSampleRevenueData(days) {
        const data = [];
        
        for (let i = 0; i < days; i++) {
            const baseRevenue = 800;
            const variation = Math.random() * 600 - 300;
            const weekendBoost = (i % 7 === 0 || i % 7 === 6) ? 200 : 0;
            data.push(Math.max(100, baseRevenue + variation + weekendBoost));
        }
        
        return data;
    }
    
    generateSampleWeatherData(days) {
        const data = [];
        
        for (let i = 0; i < days; i++) {
            data.push(Math.random() * 0.8 + 0.2); // Weather score 0.2 to 1.0
        }
        
        return data;
    }
    
    formatCurrency(amount) {
        return new Intl.NumberFormat('en-US').format(Math.round(amount));
    }
    
    formatEventName(eventName) {
        return eventName.split('_').map(word => 
            word.charAt(0).toUpperCase() + word.slice(1)
        ).join(' ');
    }
    
    formatSegmentName(segment) {
        const names = {
            'party_event': 'Party/Event',
            'construction_diy': 'Construction/DIY',
            'landscaping': 'Landscaping',
            'mixed': 'Mixed'
        };
        return names[segment] || segment;
    }
    
    getRiskClass(riskFactors) {
        if (!riskFactors || riskFactors.length === 0) return 'risk-low';
        
        const hasHighRisk = riskFactors.some(risk => risk.impact === 'high');
        const hasMediumRisk = riskFactors.some(risk => risk.impact === 'medium');
        
        if (hasHighRisk) return 'risk-high';
        if (hasMediumRisk) return 'risk-medium';
        return 'risk-low';
    }
    
    showLoading() {
        document.querySelectorAll('.loading-spinner').forEach(spinner => {
            spinner.style.display = 'inline-block';
        });
    }
    
    hideLoading() {
        document.querySelectorAll('.loading-spinner').forEach(spinner => {
            spinner.style.display = 'none';
        });
    }
    
    showError(message) {
        console.error(message);
        // Could implement a toast notification here
    }
    
    updateLastUpdated() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
        document.getElementById('last-updated').textContent = timeString;
    }
    
    async refreshAllData() {
        document.getElementById('refresh-data').innerHTML = 
            '<div class="loading-spinner"></div> Refreshing...';
        
        try {
            await this.loadInitialData();
            
            // Refresh current tab data
            const activeTab = document.querySelector('.nav-link.active');
            if (activeTab) {
                const targetTab = activeTab.getAttribute('data-bs-target').replace('#', '');
                await this.handleTabChange(targetTab);
            }
            
        } catch (error) {
            console.error('Refresh failed:', error);
        } finally {
            document.getElementById('refresh-data').innerHTML = 
                '<i class="wi wi-refresh"></i> Refresh Data';
        }
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new WeatherAnalyticsDashboard();
});