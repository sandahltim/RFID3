/**
 * RFID3 Dashboard Integration Manager
 * Coordinates all dashboard components and ensures data consistency
 * Version: 2025-08-28 - Executive Integration Enhancement
 */

class DashboardIntegrationManager {
    constructor() {
        this.components = new Map();
        this.globalState = {
            filters: {
                store: 'all',
                period: 12,
                type: 'all'
            },
            refreshInterval: 5 * 60 * 1000, // 5 minutes
            autoRefresh: true,
            lastRefresh: null
        };
        this.eventHandlers = new Map();
        this.apiCache = new Map();
        this.cacheTimeout = 2 * 60 * 1000; // 2 minutes
    }

    /**
     * Initialize the dashboard integration system
     */
    async init() {
        console.log('Initializing Dashboard Integration Manager...');
        
        try {
            // Register dashboard components
            await this.registerComponents();
            
            // Setup global event handlers
            this.setupGlobalEventHandlers();
            
            // Setup filter synchronization
            this.setupFilterSync();
            
            // Initialize auto-refresh system
            this.setupAutoRefresh();
            
            // Load initial data
            await this.loadInitialData();
            
            console.log('Dashboard Integration Manager initialized successfully');
            return true;
        } catch (error) {
            console.error('Dashboard Integration Manager initialization failed:', error);
            this.showGlobalError('Dashboard initialization failed', error);
            return false;
        }
    }

    /**
     * Register all dashboard components
     */
    async registerComponents() {
        // Register Executive Dashboard
        if (document.getElementById('executive-kpis')) {
            this.components.set('executive', {
                type: 'executive',
                element: document.getElementById('executive-kpis'),
                refreshFunction: 'refreshExecutiveDashboard',
                priority: 1
            });
        }

        // Register Inventory Analytics
        if (document.getElementById('business-intelligence')) {
            this.components.set('inventory', {
                type: 'inventory',
                element: document.getElementById('business-intelligence'),
                refreshFunction: 'refreshInventoryAnalytics',
                priority: 2
            });
        }

        // Register individual charts
        ['revenueTrendChart', 'storePerformanceChart', 'utilizationGauge', 
         'inventoryDistributionChart', 'forecastChart'].forEach(chartId => {
            const element = document.getElementById(chartId);
            if (element) {
                this.components.set(chartId, {
                    type: 'chart',
                    element: element,
                    chartManager: window.chartManager,
                    priority: 3
                });
            }
        });

        console.log(`Registered ${this.components.size} dashboard components`);
    }

    /**
     * Setup global event handlers
     */
    setupGlobalEventHandlers() {
        // Filter change events
        window.addEventListener('filterChanged', async (event) => {
            await this.handleFilterChange(event.detail);
        });

        // Chart click events
        window.addEventListener('chartClicked', (event) => {
            this.handleChartInteraction(event.detail);
        });

        // KPI drill-down events
        window.addEventListener('kpiDrilldown', (event) => {
            this.handleKPIDrilldown(event.detail);
        });

        // Auto-refresh events
        window.addEventListener('refreshRequested', async (event) => {
            await this.refreshDashboard(event.detail.component);
        });

        // Error handling events
        window.addEventListener('dashboardError', (event) => {
            this.handleComponentError(event.detail);
        });

        // Visibility change for performance optimization
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseAutoRefresh();
            } else {
                this.resumeAutoRefresh();
            }
        });
    }

    /**
     * Setup filter synchronization across components
     */
    setupFilterSync() {
        // Store filter
        const storeFilter = document.getElementById('storeFilter');
        if (storeFilter) {
            storeFilter.addEventListener('change', (e) => {
                this.updateGlobalFilter('store', e.target.value);
            });
        }

        // Period filter
        const periodFilter = document.getElementById('periodFilter');
        if (periodFilter) {
            periodFilter.addEventListener('change', (e) => {
                this.updateGlobalFilter('period', parseInt(e.target.value));
            });
        }

        // Type filter
        const typeFilter = document.getElementById('typeFilter');
        if (typeFilter) {
            typeFilter.addEventListener('change', (e) => {
                this.updateGlobalFilter('type', e.target.value);
            });
        }

        // Global filters (if available)
        if (window.GlobalFilters && typeof window.GlobalFilters.onChange === 'function') {
            window.GlobalFilters.onChange((filters) => {
                this.globalState.filters = { ...this.globalState.filters, ...filters };
                this.broadcastFilterChange();
            });
        }
    }

    /**
     * Update global filter and trigger refresh
     */
    async updateGlobalFilter(filterType, value) {
        console.log(`Updating global filter: ${filterType} = ${value}`);
        
        this.globalState.filters[filterType] = value;
        
        // Clear cache for filter-dependent data
        this.clearFilterCache();
        
        // Broadcast filter change to all components
        this.broadcastFilterChange();
        
        // Refresh dashboard with new filters
        await this.refreshDashboard('all');
    }

    /**
     * Broadcast filter changes to all components
     */
    broadcastFilterChange() {
        window.dispatchEvent(new CustomEvent('filterChanged', {
            detail: {
                filters: { ...this.globalState.filters },
                timestamp: Date.now()
            }
        }));
    }

    /**
     * Setup auto-refresh system
     */
    setupAutoRefresh() {
        if (this.globalState.autoRefresh) {
            this.refreshTimer = setInterval(async () => {
                console.log('Auto-refreshing dashboard components...');
                await this.refreshDashboard('auto');
            }, this.globalState.refreshInterval);
        }
    }

    /**
     * Pause auto-refresh (when tab is hidden)
     */
    pauseAutoRefresh() {
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
            console.log('Auto-refresh paused (tab hidden)');
        }
    }

    /**
     * Resume auto-refresh (when tab becomes visible)
     */
    resumeAutoRefresh() {
        if (this.globalState.autoRefresh && !this.refreshTimer) {
            this.setupAutoRefresh();
            console.log('Auto-refresh resumed (tab visible)');
        }
    }

    /**
     * Load initial data for all components
     */
    async loadInitialData() {
        console.log('Loading initial dashboard data...');
        
        const loadingPromises = [];
        
        // Load data based on component priority
        const sortedComponents = Array.from(this.components.entries())
            .sort(([, a], [, b]) => a.priority - b.priority);
        
        for (const [componentId, component] of sortedComponents) {
            loadingPromises.push(this.loadComponentData(componentId, component));
        }
        
        try {
            await Promise.all(loadingPromises);
            this.globalState.lastRefresh = new Date();
            this.updateRefreshIndicators('live');
        } catch (error) {
            console.error('Failed to load initial data:', error);
            this.updateRefreshIndicators('error');
        }
    }

    /**
     * Load data for a specific component
     */
    async loadComponentData(componentId, component) {
        try {
            switch (component.type) {
                case 'executive':
                    return await this.loadExecutiveData();
                case 'inventory':
                    return await this.loadInventoryData();
                case 'chart':
                    return await this.loadChartData(componentId);
                default:
                    console.warn(`Unknown component type: ${component.type}`);
            }
        } catch (error) {
            console.error(`Failed to load data for component ${componentId}:`, error);
            this.handleComponentError({
                componentId,
                error: error.message,
                type: 'data_loading'
            });
        }
    }

    /**
     * Load executive dashboard data
     */
    async loadExecutiveData() {
        const cacheKey = `executive_${JSON.stringify(this.globalState.filters)}`;
        
        // Check cache first
        if (this.apiCache.has(cacheKey)) {
            const cached = this.apiCache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                return cached.data;
            }
        }
        
        try {
            const params = new URLSearchParams({
                weeks: this.globalState.filters.period,
                store: this.globalState.filters.store
            });
            
            const response = await fetch(`/api/enhanced/dashboard/kpis?${params}`);
            
            // Handle 404 gracefully - endpoint doesn't exist yet
            if (response.status === 404) {
                console.warn('Enhanced dashboard KPIs endpoint not implemented yet');
                return { mock: true, message: 'Enhanced KPIs endpoint not available' };
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Cache the result
                this.apiCache.set(cacheKey, {
                    data: data.data,
                    timestamp: Date.now()
                });
                
                // Update executive dashboard
                if (window.executiveDashboard && typeof window.executiveDashboard.updateData === 'function') {
                    window.executiveDashboard.updateData(data.data);
                }
                
                return data.data;
            } else {
                throw new Error(data.error || 'Failed to load executive data');
            }
        } catch (error) {
            console.error('Executive data loading failed:', error);
            throw error;
        }
    }

    /**
     * Load inventory analytics data
     */
    async loadInventoryData() {
        const cacheKey = `inventory_${JSON.stringify(this.globalState.filters)}`;
        
        // Check cache first
        if (this.apiCache.has(cacheKey)) {
            const cached = this.apiCache.get(cacheKey);
            if (Date.now() - cached.timestamp < this.cacheTimeout) {
                return cached.data;
            }
        }
        
        try {
            const promises = [
                this.fetchWithFilters('/api/enhanced/dashboard/inventory-distribution'),
                this.fetchWithFilters('/api/enhanced/dashboard/financial-metrics'),
                this.fetchWithFilters('/api/enhanced/dashboard/utilization-analysis')
            ];
            
            const [distribution, financial, utilization] = await Promise.all(promises);
            
            // Handle mock responses from unimplemented endpoints
            const inventoryData = {
                distribution: distribution.mock ? null : distribution.data,
                financial: financial.mock ? null : financial.data,
                utilization: utilization.mock ? null : utilization.data,
                hasMockData: distribution.mock || financial.mock || utilization.mock
            };
            
            // Cache the result
            this.apiCache.set(cacheKey, {
                data: inventoryData,
                timestamp: Date.now()
            });
            
            // Update inventory analytics components
            if (window.inventoryAnalytics && typeof window.inventoryAnalytics.updateData === 'function') {
                window.inventoryAnalytics.updateData(inventoryData);
            }
            
            return inventoryData;
        } catch (error) {
            console.error('Inventory data loading failed:', error);
            throw error;
        }
    }

    /**
     * Load data for specific chart
     */
    async loadChartData(chartId) {
        if (!window.chartManager) {
            console.warn('Chart manager not available');
            return;
        }

        try {
            switch (chartId) {
                case 'revenueTrendChart':
                    return await this.loadRevenueTrendData();
                case 'storePerformanceChart':
                    return await this.loadStorePerformanceData();
                case 'utilizationGauge':
                    return await this.loadUtilizationData();
                case 'inventoryDistributionChart':
                    return await this.loadDistributionData();
                case 'forecastChart':
                    return await this.loadForecastData();
                default:
                    console.warn(`Unknown chart: ${chartId}`);
            }
        } catch (error) {
            window.chartManager.showChartError(chartId, `Failed to load ${chartId} data`);
            throw error;
        }
    }

    /**
     * Fetch data with current filters applied
     */
    async fetchWithFilters(endpoint) {
        const params = new URLSearchParams();
        
        if (this.globalState.filters.store !== 'all') {
            params.set('store', this.globalState.filters.store);
        }
        if (this.globalState.filters.period) {
            params.set('weeks', this.globalState.filters.period);
        }
        if (this.globalState.filters.type !== 'all') {
            params.set('type', this.globalState.filters.type);
        }
        
        const url = params.toString() ? `${endpoint}?${params}` : endpoint;
        const response = await fetch(url);
        
        // Handle 404s gracefully for unimplemented enhanced endpoints
        if (response.status === 404 && endpoint.includes('/api/enhanced/')) {
            console.warn(`Enhanced endpoint not implemented: ${endpoint}`);
            return { 
                success: false, 
                data: null, 
                message: `Endpoint ${endpoint} not implemented yet`,
                mock: true 
            };
        }
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'API request failed');
        }
        
        return data;
    }

    /**
     * Refresh dashboard components
     */
    async refreshDashboard(scope = 'all') {
        console.log(`Refreshing dashboard components: ${scope}`);
        
        this.updateRefreshIndicators('refreshing');
        
        try {
            // Clear cache if full refresh
            if (scope === 'all') {
                this.clearCache();
            }
            
            // Refresh components based on scope
            const refreshPromises = [];
            
            for (const [componentId, component] of this.components.entries()) {
                if (scope === 'all' || scope === componentId || scope === component.type) {
                    refreshPromises.push(this.loadComponentData(componentId, component));
                }
            }
            
            await Promise.all(refreshPromises);
            
            this.globalState.lastRefresh = new Date();
            this.updateRefreshIndicators('live');
            
            console.log('Dashboard refresh completed successfully');
            
        } catch (error) {
            console.error('Dashboard refresh failed:', error);
            this.updateRefreshIndicators('error');
            this.showGlobalError('Dashboard refresh failed', error);
        }
    }

    /**
     * Handle filter changes
     */
    async handleFilterChange(detail) {
        console.log('Handling filter change:', detail);
        
        // Update internal state
        this.globalState.filters = { ...this.globalState.filters, ...detail.filters };
        
        // Clear filter-dependent cache
        this.clearFilterCache();
        
        // Refresh components
        await this.refreshDashboard('all');
    }

    /**
     * Handle chart interactions
     */
    handleChartInteraction(detail) {
        console.log('Chart interaction:', detail);
        
        // Implement drill-down logic
        switch (detail.chartType) {
            case 'store-performance':
                this.drillDownToStore(detail.storeCode);
                break;
            case 'utilization':
                this.drillDownToUtilization(detail.category);
                break;
            case 'revenue-trend':
                this.drillDownToRevenue(detail.period);
                break;
        }
    }

    /**
     * Handle KPI drill-downs
     */
    handleKPIDrilldown(detail) {
        console.log('KPI drill-down:', detail);
        
        // Navigate to appropriate detailed view
        switch (detail.kpi) {
            case 'totalRevenue':
                window.location.href = '/bi/revenue-analysis';
                break;
            case 'utilization':
                this.switchToTab('usage-analysis-tab');
                break;
            case 'activeAlerts':
                this.switchToTab('alerts-tab');
                break;
            case 'efficiency':
                window.location.href = '/bi/efficiency-analysis';
                break;
        }
    }

    /**
     * Switch to specific tab in multi-tab interface
     */
    switchToTab(tabId) {
        const tabElement = document.getElementById(tabId);
        if (tabElement) {
            const tab = new bootstrap.Tab(tabElement);
            tab.show();
        }
    }

    /**
     * Handle component errors
     */
    handleComponentError(detail) {
        console.error('Component error:', detail);
        
        // Update component status
        if (detail.componentId) {
            this.updateComponentStatus(detail.componentId, 'error');
        }
        
        // Show user-friendly error message
        if (detail.type === 'critical') {
            this.showGlobalError('Critical dashboard error', detail.error);
        }
    }

    /**
     * Update refresh indicators
     */
    updateRefreshIndicators(status) {
        const indicators = document.querySelectorAll('.data-refresh-indicator');
        
        indicators.forEach(indicator => {
            indicator.className = `data-refresh-indicator ${status}`;
            
            switch (status) {
                case 'live':
                    indicator.innerHTML = '<i class="fas fa-circle"></i> Live';
                    break;
                case 'refreshing':
                    indicator.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Refreshing...';
                    break;
                case 'stale':
                    indicator.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Stale';
                    break;
                case 'error':
                    indicator.innerHTML = '<i class="fas fa-times"></i> Error';
                    break;
            }
        });
    }

    /**
     * Update individual component status
     */
    updateComponentStatus(componentId, status) {
        const statusElement = document.getElementById(`${componentId}Status`);
        if (statusElement) {
            statusElement.className = `data-refresh-indicator ${status}`;
            
            switch (status) {
                case 'loading':
                    statusElement.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
                    break;
                case 'live':
                    statusElement.innerHTML = '<i class="fas fa-circle"></i> Live';
                    break;
                case 'error':
                    statusElement.innerHTML = '<i class="fas fa-times"></i> Error';
                    break;
            }
        }
    }

    /**
     * Show global error message
     */
    showGlobalError(title, error) {
        const alertHtml = `
            <div class="alert alert-danger alert-dismissible fade show position-fixed" 
                 style="top: 20px; right: 20px; z-index: 9999; max-width: 400px;" 
                 role="alert">
                <h6 class="alert-heading">${title}</h6>
                <p class="mb-1">${error.message || error}</p>
                <small class="text-muted">Check console for details</small>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', alertHtml);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            const alert = document.querySelector('.alert-danger');
            if (alert) alert.remove();
        }, 10000);
    }

    /**
     * Clear all cache
     */
    clearCache() {
        this.apiCache.clear();
        console.log('API cache cleared');
    }

    /**
     * Clear filter-dependent cache
     */
    clearFilterCache() {
        const keysToDelete = [];
        for (const key of this.apiCache.keys()) {
            if (key.includes('executive_') || key.includes('inventory_')) {
                keysToDelete.push(key);
            }
        }
        keysToDelete.forEach(key => this.apiCache.delete(key));
        console.log(`Cleared ${keysToDelete.length} filter-dependent cache entries`);
    }

    /**
     * Cleanup resources
     */
    cleanup() {
        console.log('Cleaning up Dashboard Integration Manager...');
        
        // Clear timers
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
        
        // Clear cache
        this.clearCache();
        
        // Clear components
        this.components.clear();
        this.eventHandlers.clear();
        
        console.log('Dashboard Integration Manager cleanup complete');
    }
}

// Global dashboard integration instance
window.dashboardIntegration = new DashboardIntegrationManager();

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Initializing global dashboard integration...');
    await window.dashboardIntegration.init();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.dashboardIntegration) {
        window.dashboardIntegration.cleanup();
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardIntegrationManager;
}
