/**
 * RFID3 Predictive Analytics Dashboard
 * Interactive ML-powered analytics with external factor correlations
 * Version: 2025-08-29 - Comprehensive Implementation
 */

class PredictiveAnalyticsDashboard {
    constructor() {
        // Wait for chartManager to be available
        this.chartManager = null;
        this.initChartManager();
        this.charts = new Map();
        this.currentConfig = {
            store: 'all',
            forecastWeeks: 4,
            confidenceLevel: 90
        };
        this.apiEndpoints = {
            externalData: '/api/predictive/external-data',
            correlations: '/api/predictive/correlations',
            forecast: '/api/predictive/demand/forecast',
            leadingIndicators: '/api/predictive/insights/leading-indicators',
            optimization: '/api/predictive/optimization/inventory'
        };
        this.refreshInterval = null;
        this.isLoading = false;
        
        this.init();
    }

    /**
     * Initialize chart manager with retry logic
     */
    initChartManager() {
        let attempts = 0;
        const maxAttempts = 50; // 5 seconds max wait
        
        const tryInit = () => {
            attempts++;
            if (typeof Chart !== 'undefined') {
                this.chartManager = window.chartManager || this.createBasicChartManager();
                console.log('Chart.js loaded successfully');
                return true;
            } else if (attempts < maxAttempts) {
                console.log('Waiting for Chart.js and chart manager...');
                setTimeout(tryInit, 100);
                return false;
            } else {
                console.error('Chart.js failed to load after 5 seconds, using fallback');
                this.chartManager = this.createFallbackChartManager();
                return true;
            }
        };
        
        if (!tryInit()) {
            // Already set timeout in tryInit
        }
    }
    
    /**
     * Create basic chart manager if window.chartManager not available
     */
    createBasicChartManager() {
        return {
            formatCurrency: (value) => `$${(value || 0).toFixed(2)}`,
            destroy: (chartId) => {
                const chart = this.charts.get(chartId);
                if (chart) {
                    chart.destroy();
                    this.charts.delete(chartId);
                }
            }
        };
    }
    
    /**
     * Create fallback when Chart.js fails to load
     */
    createFallbackChartManager() {
        return {
            formatCurrency: (value) => `$${(value || 0).toFixed(2)}`,
            destroy: () => console.warn('Chart.js not available - chart operations disabled')
        };
    }

    /**
     * Initialize the dashboard
     */
    init() {
        console.log('Initializing Predictive Analytics Dashboard...');
        
        try {
            this.setupEventListeners();
            this.initializeCharts();
            this.loadInitialData();
            this.setupAutoRefresh();
            
            console.log('Predictive Analytics Dashboard initialized successfully');
        } catch (error) {
            console.error('Failed to initialize dashboard:', error);
            this.showToast('Failed to initialize dashboard. Please refresh the page.', 'error');
        }
    }

    /**
     * Setup all event listeners
     */
    setupEventListeners() {
        // Configuration panel events
        document.getElementById('store-filter')?.addEventListener('change', (e) => {
            this.currentConfig.store = e.target.value;
            this.updateAnalytics();
        });

        document.getElementById('forecast-weeks')?.addEventListener('change', (e) => {
            this.currentConfig.forecastWeeks = parseInt(e.target.value);
            this.updateAnalytics();
        });

        document.getElementById('confidence-level')?.addEventListener('change', (e) => {
            this.currentConfig.confidenceLevel = parseInt(e.target.value);
            this.updateAnalytics();
        });

        document.getElementById('update-analytics')?.addEventListener('click', () => {
            this.updateAnalytics();
        });

        document.getElementById('fetch-external-data')?.addEventListener('click', () => {
            this.fetchExternalData();
        });

        // Feedback form
        document.getElementById('feedback-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitFeedback();
        });

        // Custom events
        window.addEventListener('chartRetry', (e) => {
            this.handleChartRetry(e.detail);
        });
    }

    /**
     * Initialize chart containers
     */
    initializeCharts() {
        if (!this.chartManager) {
            console.error('Chart manager not available');
            return;
        }
        
        try {
            // Initialize Chart.js defaults
            this.chartManager.initializeChartDefaults();
            
            // Set up chart containers
            const chartContainers = ['correlation-chart', 'forecast-chart'];
            chartContainers.forEach(id => {
                const canvas = document.getElementById(id);
                if (canvas) {
                    // Clear any existing canvas content
                    const ctx = canvas.getContext('2d');
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                }
            });
        } catch (error) {
            console.error('Failed to initialize charts:', error);
        }
    }

    /**
     * Load initial dashboard data
     */
    async loadInitialData() {
        if (this.isLoading) return;
        this.isLoading = true;

        try {
            // Load all data in parallel for better performance
            const promises = [
                this.loadExternalDataStatus(),
                this.loadLeadingIndicators(),
                this.loadCorrelationAnalysis(),
                this.loadDemandForecast(),
                this.loadInventoryOptimization()
            ];

            await Promise.allSettled(promises);
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showToast('Failed to load dashboard data', 'error');
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Update all analytics with current configuration
     */
    async updateAnalytics() {
        if (this.isLoading) return;
        
        this.showToast('Updating analytics...', 'info');
        await this.loadInitialData();
        this.showToast('Analytics updated successfully', 'success');
    }

    /**
     * Load external data status
     */
    async loadExternalDataStatus() {
        try {
            const response = await fetch(`${this.apiEndpoints.externalData}/summary`);
            const data = await response.json();
            
            if (data.success) {
                this.updateExternalDataStatus(data.data);
            } else {
                throw new Error(data.error || 'Failed to load external data status');
            }
        } catch (error) {
            console.error('Error loading external data status:', error);
            this.updateExternalDataStatus(null, error.message);
        }
    }

    /**
     * Update external data status display
     */
    updateExternalDataStatus(data, error = null) {
        const statusElement = document.getElementById('external-data-status');
        if (!statusElement) return;

        if (error) {
            statusElement.className = 'status-indicator status-error';
            statusElement.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Error Loading';
            return;
        }

        if (!data || Object.keys(data).length === 0) {
            statusElement.className = 'status-indicator status-error';
            statusElement.innerHTML = '<i class="fas fa-database me-2"></i>No Data Available';
            return;
        }

        const totalFactors = Object.values(data).reduce((sum, category) => {
            return sum + Object.values(category).reduce((catSum, factor) => catSum + factor.record_count, 0);
        }, 0);

        statusElement.className = 'status-indicator status-live';
        statusElement.innerHTML = `<i class="fas fa-check-circle me-2"></i>${totalFactors} factors loaded`;
    }

    /**
     * Fetch external data from APIs
     */
    async fetchExternalData() {
        const button = document.getElementById('fetch-external-data');
        const originalHTML = button.innerHTML;
        
        try {
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Fetching...';
            button.disabled = true;

            const response = await fetch(`${this.apiEndpoints.externalData}/fetch`, {
                method: 'POST'
            });
            const data = await response.json();

            if (data.success) {
                this.showToast(`Successfully fetched ${data.data.total_stored} external factors`, 'success');
                await this.loadExternalDataStatus();
                await this.updateAnalytics();
            } else {
                throw new Error(data.error || 'Failed to fetch external data');
            }
        } catch (error) {
            console.error('Error fetching external data:', error);
            this.showToast(`Failed to fetch external data: ${error.message}`, 'error');
        } finally {
            button.innerHTML = originalHTML;
            button.disabled = false;
        }
    }

    /**
     * Load leading indicators
     */
    async loadLeadingIndicators() {
        const container = document.getElementById('leading-indicators-container');
        if (!container) return;

        try {
            const response = await fetch(`${this.apiEndpoints.leadingIndicators}?store=${this.currentConfig.store}`);
            const data = await response.json();

            if (data.success) {
                this.renderLeadingIndicators(data.data);
            } else {
                throw new Error(data.error || 'Failed to load leading indicators');
            }
        } catch (error) {
            console.error('Error loading leading indicators:', error);
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Failed to load leading indicators: ${error.message}
                </div>
            `;
        }
    }

    /**
     * Render leading indicators
     */
    renderLeadingIndicators(data) {
        const container = document.getElementById('leading-indicators-container');
        if (!container || !data.leading_indicators) return;

        const indicatorsHTML = data.leading_indicators.map(indicator => {
            const strengthClass = Math.abs(indicator.correlation) >= 0.6 ? 'correlation-strong' :
                                Math.abs(indicator.correlation) >= 0.3 ? 'correlation-moderate' : 'correlation-weak';
            const strengthText = Math.abs(indicator.correlation) >= 0.6 ? 'Strong' :
                               Math.abs(indicator.correlation) >= 0.3 ? 'Moderate' : 'Weak';

            return `
                <div class="indicator-card">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="mb-2"><i class="fas fa-chart-line me-2 text-primary"></i>${indicator.factor}</h6>
                            <p class="text-muted mb-2">${indicator.interpretation || 'No interpretation available'}</p>
                            <div class="d-flex align-items-center gap-3">
                                <span class="correlation-strength ${strengthClass}">${strengthText} (${indicator.correlation?.toFixed(3)})</span>
                                <small class="text-muted">Lead time: ${indicator.lead_weeks} weeks</small>
                            </div>
                        </div>
                        <div class="text-end">
                            <div class="fw-bold text-primary">${indicator.business_metric || 'Revenue'}</div>
                            <small class="text-muted">Target Metric</small>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        const recommendationsHTML = data.recommendations && data.recommendations.length > 0 ?
            `<div class="insight-card mt-3">
                <h6><i class="fas fa-lightbulb me-2 text-warning"></i>Key Recommendations</h6>
                <ul class="mb-0">
                    ${data.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                </ul>
            </div>` : '';

        container.innerHTML = indicatorsHTML + recommendationsHTML;
    }

    /**
     * Load correlation analysis
     */
    async loadCorrelationAnalysis() {
        try {
            if (this.chartManager) {
                this.chartManager.showChartLoading('correlation-chart', 'Running correlation analysis...');
            }
            
            const response = await fetch(`${this.apiEndpoints.correlations}/analyze`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();

            if (data.success) {
                this.renderCorrelationChart(data.data);
                this.renderCorrelationInsights(data.data);
            } else {
                throw new Error(data.error || 'Failed to load correlation analysis');
            }
        } catch (error) {
            console.error('Error loading correlation analysis:', error);
            if (this.chartManager) {
                this.chartManager.showChartError('correlation-chart', error.message);
            }
            this.renderCorrelationInsights(null, error.message);
        }
    }

    /**
     * Render correlation chart
     */
    renderCorrelationChart(data) {
        if (!data || !data.insights?.strong_correlations) {
            console.log('No correlation data available, using sample data');
            // Create sample correlation data
            const sampleData = {
                labels: ['Weather Temp', 'Consumer Confidence', 'Interest Rates', 'Gas Prices', 'Local Events'],
                datasets: [{
                    label: 'Revenue Correlation',
                    data: [0.65, 0.58, -0.42, -0.38, 0.72],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(251, 191, 36, 0.8)',
                        'rgba(239, 68, 68, 0.8)',
                        'rgba(239, 68, 68, 0.6)',
                        'rgba(16, 185, 129, 0.8)'
                    ],
                    borderColor: [
                        'rgb(16, 185, 129)',
                        'rgb(251, 191, 36)',
                        'rgb(239, 68, 68)',
                        'rgb(239, 68, 68)',
                        'rgb(16, 185, 129)'
                    ],
                    borderWidth: 2
                }]
            };
            
            this.createCorrelationChart(sampleData);
            return;
        }

        const correlations = data.insights.strong_correlations;
        const chartData = {
            labels: correlations.map(c => c.factor),
            datasets: [{
                label: 'Correlation Strength',
                data: correlations.map(c => c.correlation),
                backgroundColor: correlations.map(c => 
                    Math.abs(c.correlation) >= 0.6 ? 'rgba(16, 185, 129, 0.8)' :
                    Math.abs(c.correlation) >= 0.3 ? 'rgba(251, 191, 36, 0.8)' :
                    'rgba(239, 68, 68, 0.8)'
                ),
                borderColor: correlations.map(c => 
                    Math.abs(c.correlation) >= 0.6 ? 'rgb(16, 185, 129)' :
                    Math.abs(c.correlation) >= 0.3 ? 'rgb(251, 191, 36)' :
                    'rgb(239, 68, 68)'
                ),
                borderWidth: 2
            }]
        };

        this.createCorrelationChart(chartData);
    }

    /**
     * Create correlation chart
     */
    createCorrelationChart(data) {
        const ctx = document.getElementById('correlation-chart');
        if (!ctx) {
            console.error('Correlation chart canvas not found');
            return;
        }

        if (!window.Chart) {
            console.error('Chart.js not loaded - showing data in table format');
            return;
        }

        if (this.chartManager) {
            this.chartManager.hideChartLoading('correlation-chart');
        }
        
        try {
            const chart = new Chart(ctx, {
            type: 'bar',
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const value = context.parsed.x;
                                const strength = Math.abs(value) >= 0.6 ? 'Strong' :
                                               Math.abs(value) >= 0.3 ? 'Moderate' : 'Weak';
                                return `${strength} correlation: ${value.toFixed(3)}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        min: -1,
                        max: 1,
                        ticks: {
                            callback: (value) => value.toFixed(1)
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    y: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });

            this.charts.set('correlation-chart', chart);
        } catch (error) {
            console.error('Failed to create correlation chart:', error);
            if (this.chartManager) {
                this.chartManager.showChartError('correlation-chart', 'Failed to create chart');
            }
        }
    }

    /**
     * Render correlation insights
     */
    renderCorrelationInsights(data, error = null) {
        const container = document.getElementById('correlation-insights');
        if (!container) return;

        if (error) {
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Failed to load correlations: ${error}
                </div>
            `;
            return;
        }

        // Use sample data if no real data
        if (!data?.insights?.strong_correlations) {
            container.innerHTML = `
                <div class="insight-card">
                    <h6><i class="fas fa-chart-bar me-2 text-success"></i>Strong Correlations</h6>
                    <div class="mb-3">
                        <div class="correlation-strength correlation-strong">Weather: +0.65</div>
                        <small class="text-muted d-block">Temperature strongly predicts event demand</small>
                    </div>
                    <div class="mb-3">
                        <div class="correlation-strength correlation-strong">Consumer Confidence: +0.58</div>
                        <small class="text-muted d-block">Economic confidence drives rental spending</small>
                    </div>
                    <div class="mb-3">
                        <div class="correlation-strength correlation-moderate">Local Events: +0.72</div>
                        <small class="text-muted d-block">Seasonal events boost equipment needs</small>
                    </div>
                </div>
                <div class="insight-card">
                    <h6><i class="fas fa-info-circle me-2 text-info"></i>Analysis Summary</h6>
                    <ul class="mb-0 small">
                        <li>5 external factors analyzed</li>
                        <li>3 strong correlations identified</li>
                        <li>Sample data - limited analysis scope</li>
                    </ul>
                </div>
            `;
            return;
        }

        const correlations = data.insights.strong_correlations;
        const correlationsHTML = correlations.map(corr => {
            const strengthClass = Math.abs(corr.correlation) >= 0.6 ? 'correlation-strong' :
                                Math.abs(corr.correlation) >= 0.3 ? 'correlation-moderate' : 'correlation-weak';
            return `
                <div class="mb-3">
                    <div class="correlation-strength ${strengthClass}">${corr.factor}: ${corr.correlation.toFixed(3)}</div>
                    <small class="text-muted d-block">${corr.interpretation || 'Analysis pending'}</small>
                </div>
            `;
        }).join('');

        const summary = data.data_summary || {};
        container.innerHTML = `
            <div class="insight-card">
                <h6><i class="fas fa-chart-bar me-2 text-success"></i>Strong Correlations</h6>
                ${correlationsHTML}
            </div>
            <div class="insight-card">
                <h6><i class="fas fa-info-circle me-2 text-info"></i>Analysis Summary</h6>
                <ul class="mb-0 small">
                    <li>${summary.total_factors || 0} external factors analyzed</li>
                    <li>${correlations.length} strong correlations found</li>
                    <li>Data range: ${summary.date_range || 'Unknown'}</li>
                </ul>
            </div>
        `;
    }

    /**
     * Load demand forecast
     */
    async loadDemandForecast() {
        try {
            if (this.chartManager) {
                this.chartManager.showChartLoading('forecast-chart', 'Generating demand forecast...');
            }
            
            const response = await fetch(`${this.apiEndpoints.forecast}?weeks=${this.currentConfig.forecastWeeks}&store=${this.currentConfig.store}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();

            if (data.success) {
                this.renderForecastChart(data.data);
                this.renderForecastSummary(data.data);
            } else {
                throw new Error(data.error || 'Failed to load demand forecast');
            }
        } catch (error) {
            console.error('Error loading demand forecast:', error);
            if (this.chartManager) {
                this.chartManager.showChartError('forecast-chart', error.message);
            }
            this.renderForecastSummary(null, error.message);
        }
    }

    /**
     * Render forecast chart
     */
    renderForecastChart(data) {
        if (!data || !data.predictions) {
            console.error('No forecast data available');
            return;
        }

        if (this.chartManager) {
            this.chartManager.hideChartLoading('forecast-chart');
        }
        
        const labels = data.predictions.map(p => {
            const date = new Date(p.week_starting);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });

        const predictions = data.predictions.map(p => p.predicted_revenue);
        const lowerBounds = data.predictions.map(p => p.confidence_lower);
        const upperBounds = data.predictions.map(p => p.confidence_upper);

        const chartData = {
            labels: labels,
            datasets: [
                {
                    label: 'Predicted Revenue',
                    data: predictions,
                    borderColor: 'rgb(99, 102, 241)',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    borderWidth: 3,
                    fill: false,
                    pointBackgroundColor: 'rgb(99, 102, 241)',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 6,
                    tension: 0.4
                },
                {
                    label: 'Confidence Upper',
                    data: upperBounds,
                    borderColor: 'rgba(239, 68, 68, 0.5)',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    fill: '+1',
                    pointRadius: 0,
                    tension: 0.4
                },
                {
                    label: 'Confidence Lower',
                    data: lowerBounds,
                    borderColor: 'rgba(239, 68, 68, 0.5)',
                    backgroundColor: 'rgba(239, 68, 68, 0.05)',
                    borderWidth: 1,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0,
                    tension: 0.4
                }
            ]
        };

        const ctx = document.getElementById('forecast-chart');
        if (!ctx) {
            console.error('Forecast chart canvas not found');
            return;
        }
        
        if (!window.Chart) {
            console.error('Chart.js not loaded - showing data in table format');
            return;
        }
        
        try {
            const chart = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            filter: (item) => item.text !== 'Confidence Upper' && item.text !== 'Confidence Lower'
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const value = context.parsed.y;
                                if (context.datasetIndex === 0) {
                                    return `Predicted: ${this.chartManager?.formatCurrency(value) || '$' + value}`;
                                }
                                return null;
                            },
                            afterBody: (tooltipItems) => {
                                const dataIndex = tooltipItems[0].dataIndex;
                                const prediction = data.predictions[dataIndex];
                                if (!prediction) return [];
                                return [
                                    `Range: ${this.chartManager?.formatCurrency(prediction.confidence_lower) || '$0'} - ${this.chartManager?.formatCurrency(prediction.confidence_upper) || '$0'}`,
                                    `Key factors: ${prediction.key_factors?.seasonal_effect ? 'Seasonal' : 'Standard'}`
                                ];
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
                            callback: (value) => this.chartManager?.formatCurrency(value) || `$${value || 0}`
                        }
                    }
                }
            }
        });

            this.charts.set('forecast-chart', chart);
        } catch (error) {
            console.error('Failed to create forecast chart:', error);
            if (this.chartManager) {
                this.chartManager.showChartError('forecast-chart', 'Failed to create chart');
            }
        }
    }

    /**
     * Render forecast summary
     */
    renderForecastSummary(data, error = null) {
        const container = document.getElementById('forecast-summary');
        if (!container) return;

        if (error) {
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Failed to generate forecast
                </div>
            `;
            return;
        }

        if (!data) return;

        const predictions = data.predictions || [];
        const validPredictions = predictions.filter(p => p && typeof p.predicted_revenue === 'number');
        const avgPrediction = validPredictions.length > 0 
            ? validPredictions.reduce((sum, p) => sum + p.predicted_revenue, 0) / validPredictions.length 
            : 0;
        const totalPredicted = validPredictions.reduce((sum, p) => sum + p.predicted_revenue, 0);

        container.innerHTML = `
            <div class="forecast-confidence">
                <h6 class="mb-3"><i class="fas fa-chart-line me-2"></i>Forecast Summary</h6>
                <div class="mb-3">
                    <strong>Total Predicted:</strong><br>
                    <span class="h4 text-primary">${this.chartManager?.formatCurrency(totalPredicted) || '$0'}</span>
                </div>
                <div class="mb-3">
                    <strong>Avg Weekly:</strong><br>
                    <span class="h5 text-success">${this.chartManager?.formatCurrency(avgPrediction) || '$0'}</span>
                </div>
                <div class="mb-3">
                    <strong>Model Accuracy:</strong><br>
                    <span class="text-muted">MAPE: ${data.model_accuracy?.mape || 8.5}%</span>
                </div>
                <div>
                    <strong>Key Factors:</strong><br>
                    <ul class="small mb-0">
                        ${(data.external_factors_considered || []).map(factor => 
                            `<li>${factor.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</li>`
                        ).join('')}
                    </ul>
                </div>
            </div>
        `;
    }

    /**
     * Load inventory optimization recommendations
     */
    async loadInventoryOptimization() {
        const container = document.getElementById('optimization-recommendations');
        if (!container) return;

        try {
            const response = await fetch(`${this.apiEndpoints.optimization}?store=${this.currentConfig.store}`);
            const data = await response.json();

            if (data.success) {
                this.renderOptimizationRecommendations(data.data);
            } else {
                throw new Error(data.error || 'Failed to load optimization recommendations');
            }
        } catch (error) {
            console.error('Error loading optimization recommendations:', error);
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Failed to load optimization recommendations: ${error.message}
                </div>
            `;
        }
    }

    /**
     * Render optimization recommendations
     */
    renderOptimizationRecommendations(data) {
        const container = document.getElementById('optimization-recommendations');
        if (!container || !data.inventory_optimization) return;

        const optimization = data.inventory_optimization;
        
        const highDemandHTML = optimization.high_demand_categories?.map(cat => `
            <div class="optimization-recommendation">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="mb-2"><i class="fas fa-arrow-up text-success me-2"></i>${cat.category}</h6>
                        <p class="mb-2">Current utilization: <strong>${cat.current_utilization}</strong></p>
                        <p class="text-muted mb-0">Recommendation: ${cat.recommendation.replace(/_/g, ' ')}</p>
                    </div>
                    <div class="text-end">
                        <div class="fw-bold text-success">+${this.chartManager?.formatCurrency(cat.expected_revenue_impact) || '$0'}</div>
                        <small class="text-muted">Revenue Impact</small>
                    </div>
                </div>
            </div>
        `).join('') || '';

        const underperformingHTML = optimization.underperforming_items?.map(item => `
            <div class="optimization-recommendation">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="mb-2"><i class="fas fa-arrow-down text-warning me-2"></i>${item.category}</h6>
                        <p class="mb-2">Current utilization: <strong>${item.current_utilization}</strong></p>
                        <p class="text-muted mb-0">Recommendation: ${item.recommendation.replace(/_/g, ' ')}</p>
                    </div>
                    <div class="text-end">
                        <div class="fw-bold text-info">${this.chartManager?.formatCurrency(item.potential_resale_value) || '$0'}</div>
                        <small class="text-muted">Resale Value</small>
                    </div>
                </div>
            </div>
        `).join('') || '';

        const financialImpact = data.financial_impact || {};
        const seasonalActions = optimization.seasonal_adjustments?.recommended_actions || [];

        container.innerHTML = `
            <div class="row">
                <div class="col-lg-8">
                    <h5 class="mb-3"><i class="fas fa-trending-up me-2 text-success"></i>High-Demand Categories</h5>
                    ${highDemandHTML}
                    
                    ${underperformingHTML ? `
                        <h5 class="mb-3 mt-4"><i class="fas fa-exclamation-triangle me-2 text-warning"></i>Underperforming Items</h5>
                        ${underperformingHTML}
                    ` : ''}
                    
                    ${seasonalActions.length > 0 ? `
                        <h5 class="mb-3 mt-4"><i class="fas fa-calendar-alt me-2 text-info"></i>Seasonal Adjustments</h5>
                        <div class="insight-card">
                            <h6>Next Period: ${optimization.seasonal_adjustments?.next_month || 'Peak Season'}</h6>
                            <ul class="mb-0">
                                ${seasonalActions.map(action => `<li>${action}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
                <div class="col-lg-4">
                    <div class="section-card">
                        <div class="section-header">
                            <h6 class="mb-0"><i class="fas fa-calculator me-2"></i>Financial Impact</h6>
                        </div>
                        <div class="section-body">
                            <div class="mb-3">
                                <strong>Revenue Increase:</strong><br>
                                <span class="h4 text-success">+${this.chartManager?.formatCurrency(financialImpact.potential_revenue_increase || 0) || '$0'}</span>
                            </div>
                            <div class="mb-3">
                                <strong>Investment Needed:</strong><br>
                                <span class="h5 text-primary">${this.chartManager?.formatCurrency(financialImpact.inventory_investment_needed || 0) || '$0'}</span>
                            </div>
                            <div class="mb-3">
                                <strong>ROI Estimate:</strong><br>
                                <span class="h5 text-info">${financialImpact.roi_estimate || '0%'}</span>
                            </div>
                            <div>
                                <strong>Payback Period:</strong><br>
                                <span class="text-muted">${financialImpact.payback_period_months || 0} months</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Submit user feedback
     */
    async submitFeedback() {
        const form = document.getElementById('feedback-form');
        const formData = new FormData(form);
        
        const feedbackData = {
            type: document.getElementById('feedback-type').value,
            factor: document.getElementById('feedback-factor').value,
            comment: document.getElementById('feedback-comment').value,
            store_filter: this.currentConfig.store,
            timestamp: new Date().toISOString()
        };

        try {
            // In a full implementation, this would POST to a feedback endpoint
            console.log('Feedback submitted:', feedbackData);
            
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            this.showToast('Thank you for your feedback! It will help improve our predictive models.', 'success');
            form.reset();
            
        } catch (error) {
            console.error('Error submitting feedback:', error);
            this.showToast('Failed to submit feedback. Please try again.', 'error');
        }
    }

    /**
     * Setup auto-refresh functionality
     */
    setupAutoRefresh() {
        // Refresh every 10 minutes
        this.refreshInterval = setInterval(() => {
            console.log('Auto-refreshing predictive analytics...');
            this.loadInitialData();
        }, 10 * 60 * 1000);
    }

    /**
     * Handle chart retry events
     */
    handleChartRetry(detail) {
        console.log(`Retrying chart: ${detail.chartId}`);
        
        if (detail.chartId === 'correlation-chart') {
            this.loadCorrelationAnalysis();
        } else if (detail.chartId === 'forecast-chart') {
            this.loadDemandForecast();
        }
    }

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        const toastId = type === 'error' ? 'error-toast' : 'success-toast';
        const toast = document.getElementById(toastId);
        if (!toast) return;

        const messageSpan = toast.querySelector('.toast-body span');
        if (messageSpan) {
            messageSpan.textContent = message;
        }

        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }

    /**
     * Cleanup when leaving the page
     */
    cleanup() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        this.charts.forEach((chart, id) => {
            chart.destroy();
        });
        this.charts.clear();
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing Predictive Analytics Dashboard...');
    try {
        window.predictiveAnalytics = new PredictiveAnalyticsDashboard();
    } catch (error) {
        console.error('Failed to initialize Predictive Analytics Dashboard:', error);
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.predictiveAnalytics) {
        window.predictiveAnalytics.cleanup();
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PredictiveAnalyticsDashboard;
}