/**
 * RFID3 Configuration Interface
 * Fortune 500-Level Interactive Configuration Management
 * Version: 2025-08-29
 */

class ConfigurationManager {
    constructor() {
        this.currentConfig = {};
        this.unsavedChanges = false;
        this.validationRules = this.initValidationRules();
        this.init();
    }

    init() {
        console.log('Initializing Configuration Manager...');
        this.setupEventListeners();
        this.loadConfigurations();
        this.initializeSliders();
        this.setupFormValidation();
        this.setupAutoSave();
    }

    initValidationRules() {
        return {
            prediction: {
                seasonality_weight: { min: 0, max: 1 },
                trend_weight: { min: 0, max: 1 },
                economic_weight: { min: 0, max: 1 },
                promotional_weight: { min: 0, max: 1 },
                low_stock_threshold: { min: 0.05, max: 0.5 },
                high_stock_threshold: { min: 1.5, max: 5.0 },
                demand_spike_threshold: { min: 1.2, max: 3.0 }
            },
            correlation: {
                correlation_weak: { min: 0.1, max: 0.5 },
                correlation_moderate: { min: 0.3, max: 0.7 },
                correlation_strong: { min: 0.5, max: 0.9 },
                min_lag_periods: { min: 1, max: 6 },
                max_lag_periods: { min: 6, max: 24 },
                default_lag_period: { min: 1, max: 12 }
            }
        };
    }

    setupEventListeners() {
        // Tab navigation
        document.querySelectorAll('[data-bs-toggle="pill"]').forEach(tab => {
            tab.addEventListener('shown.bs.tab', (event) => {
                this.onTabChange(event.target);
            });
        });

        // Form submissions
        document.getElementById('prediction-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.savePredictionConfiguration();
        });

        document.getElementById('correlation-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveCorrelationConfiguration();
        });

        document.getElementById('bi-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveBusinessIntelligenceConfiguration();
        });

        document.getElementById('integration-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveDataIntegrationConfiguration();
        });

        document.getElementById('preferences-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveUserPreferences();
        });

        document.getElementById('executive-dashboard-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveExecutiveDashboardConfiguration();
        });

        document.getElementById('labor-cost-form')?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveLaborCostConfiguration();
        });

        // Reset buttons
        document.getElementById('reset-prediction')?.addEventListener('click', () => {
            this.resetConfiguration('prediction');
        });

        document.getElementById('reset-correlation')?.addEventListener('click', () => {
            this.resetConfiguration('correlation');
        });

        document.getElementById('reset-bi')?.addEventListener('click', () => {
            this.resetConfiguration('bi');
        });

        document.getElementById('reset-integration')?.addEventListener('click', () => {
            this.resetConfiguration('integration');
        });

        document.getElementById('reset-preferences')?.addEventListener('click', () => {
            this.resetConfiguration('preferences');
        });

        document.getElementById('reset-executive-dashboard')?.addEventListener('click', () => {
            this.resetConfiguration('executive-dashboard');
        });

        document.getElementById('reset-labor-cost')?.addEventListener('click', () => {
            this.resetConfiguration('labor-cost');
        });

        // Change detection for unsaved changes warning
        document.querySelectorAll('.config-form input, .config-form select').forEach(element => {
            element.addEventListener('change', () => {
                this.unsavedChanges = true;
                this.updateSaveButtonStates();
            });
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                this.saveCurrentConfiguration();
            }
        });

        // Before unload warning
        window.addEventListener('beforeunload', (e) => {
            if (this.unsavedChanges) {
                e.preventDefault();
                e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
                return e.returnValue;
            }
        });
    }

    initializeSliders() {
        // Setup range sliders with real-time updates
        const sliders = [
            { id: 'seasonality_weight', display: 'seasonality_value' },
            { id: 'trend_weight', display: 'trend_value' },
            { id: 'economic_weight', display: 'economic_value' },
            { id: 'promotional_weight', display: 'promotional_value' }
        ];

        sliders.forEach(slider => {
            const element = document.getElementById(slider.id);
            const display = document.getElementById(slider.display);
            
            if (element && display) {
                element.addEventListener('input', (e) => {
                    const value = parseFloat(e.target.value);
                    display.textContent = Math.round(value * 100) + '%';
                    this.validateWeightDistribution();
                });
            }
        });
    }

    validateWeightDistribution() {
        const seasonality = parseFloat(document.getElementById('seasonality_weight')?.value || 0);
        const trend = parseFloat(document.getElementById('trend_weight')?.value || 0);
        const economic = parseFloat(document.getElementById('economic_weight')?.value || 0);
        const promotional = parseFloat(document.getElementById('promotional_weight')?.value || 0);
        
        const total = seasonality + trend + economic + promotional;
        const tolerance = 0.05; // 5% tolerance
        
        const weightContainer = document.querySelector('.external-factors-container');
        if (weightContainer) {
            if (Math.abs(total - 1.0) > tolerance) {
                weightContainer.classList.add('warning');
                this.showWeightWarning(total);
            } else {
                weightContainer.classList.remove('warning');
                this.hideWeightWarning();
            }
        }
    }

    showWeightWarning(total) {
        let warning = document.getElementById('weight-warning');
        if (!warning) {
            warning = document.createElement('div');
            warning.id = 'weight-warning';
            warning.className = 'alert alert-warning mt-2';
            warning.innerHTML = `
                <i class="fas fa-exclamation-triangle me-2"></i>
                <span id="weight-warning-text"></span>
            `;
            
            const weightSection = document.querySelector('.external-factors-container') || 
                                document.querySelector('[for="seasonality_weight"]').closest('.form-group-advanced');
            if (weightSection) {
                weightSection.appendChild(warning);
            }
        }
        
        const percentage = Math.round(total * 100);
        document.getElementById('weight-warning-text').textContent = 
            `Warning: Factor weights total ${percentage}% (should equal 100%)`;
    }

    hideWeightWarning() {
        const warning = document.getElementById('weight-warning');
        if (warning) {
            warning.remove();
        }
    }

    setupFormValidation() {
        // Add real-time validation for numerical inputs
        document.querySelectorAll('input[type="number"]').forEach(input => {
            input.addEventListener('blur', (e) => {
                this.validateField(e.target);
            });
        });

        // Custom validation for correlation thresholds
        const correlationInputs = ['correlation_weak', 'correlation_moderate', 'correlation_strong'];
        correlationInputs.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.addEventListener('change', () => {
                    this.validateCorrelationThresholds();
                });
            }
        });
    }

    validateField(field) {
        const value = parseFloat(field.value);
        const rules = this.getValidationRules(field.id);
        
        if (rules) {
            const isValid = value >= rules.min && value <= rules.max;
            
            if (isValid) {
                field.classList.remove('is-invalid');
                field.classList.add('is-valid');
                this.removeFieldError(field);
            } else {
                field.classList.remove('is-valid');
                field.classList.add('is-invalid');
                this.showFieldError(field, `Value must be between ${rules.min} and ${rules.max}`);
            }
            
            return isValid;
        }
        
        return true;
    }

    getValidationRules(fieldId) {
        for (const [configType, rules] of Object.entries(this.validationRules)) {
            if (rules[fieldId]) {
                return rules[fieldId];
            }
        }
        return null;
    }

    showFieldError(field, message) {
        let errorDiv = field.parentNode.querySelector('.field-error');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'field-error invalid-feedback';
            field.parentNode.appendChild(errorDiv);
        }
        errorDiv.textContent = message;
    }

    removeFieldError(field) {
        const errorDiv = field.parentNode.querySelector('.field-error');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    validateCorrelationThresholds() {
        const weak = parseFloat(document.getElementById('correlation_weak')?.value || 0);
        const moderate = parseFloat(document.getElementById('correlation_moderate')?.value || 0);
        const strong = parseFloat(document.getElementById('correlation_strong')?.value || 0);
        
        let valid = true;
        let message = '';
        
        if (weak >= moderate) {
            valid = false;
            message = 'Weak threshold must be less than moderate threshold';
        } else if (moderate >= strong) {
            valid = false;
            message = 'Moderate threshold must be less than strong threshold';
        }
        
        if (!valid) {
            this.showConfigurationAlert('warning', message, 'correlation-form');
        } else {
            this.hideConfigurationAlert('correlation-form');
        }
        
        return valid;
    }

    setupAutoSave() {
        // Auto-save every 5 minutes if there are unsaved changes
        setInterval(() => {
            if (this.unsavedChanges) {
                this.autoSave();
            }
        }, 300000); // 5 minutes
    }

    autoSave() {
        console.log('Auto-saving configurations...');
        // This would save to localStorage or make a draft API call
        const draftData = this.collectAllFormData();
        localStorage.setItem('rfid_config_draft', JSON.stringify({
            timestamp: new Date().toISOString(),
            data: draftData
        }));
    }

    loadConfigurations() {
        // Load each configuration type
        this.loadPredictionConfiguration();
        this.loadCorrelationConfiguration();
        this.loadBusinessIntelligenceConfiguration();
        this.loadDataIntegrationConfiguration();
        this.loadUserPreferences();
        this.loadExecutiveDashboardConfiguration();
        this.loadLaborCostConfiguration();
        
        // Check for draft data
        this.checkForDraftData();
    }

    checkForDraftData() {
        const draft = localStorage.getItem('rfid_config_draft');
        if (draft) {
            try {
                const draftData = JSON.parse(draft);
                const draftTime = new Date(draftData.timestamp);
                const hoursSinceDraft = (new Date() - draftTime) / (1000 * 60 * 60);
                
                if (hoursSinceDraft < 24) { // Show draft if less than 24 hours old
                    this.showDraftRecoveryOption(draftData);
                }
            } catch (e) {
                console.warn('Error parsing draft data:', e);
                localStorage.removeItem('rfid_config_draft');
            }
        }
    }

    showDraftRecoveryOption(draftData) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-info alert-dismissible fade show';
        alert.innerHTML = `
            <i class="fas fa-info-circle me-2"></i>
            <strong>Draft Recovery:</strong> We found unsaved changes from ${new Date(draftData.timestamp).toLocaleString()}.
            <button type="button" class="btn btn-sm btn-outline-info ms-2" onclick="configManager.restoreDraft()">
                Restore Draft
            </button>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(alert, container.firstChild);
        }
        
        this.draftData = draftData;
    }

    restoreDraft() {
        if (this.draftData && this.draftData.data) {
            this.populateFormsWithData(this.draftData.data);
            this.unsavedChanges = true;
            this.updateSaveButtonStates();
            
            // Remove the draft alert
            const alert = document.querySelector('.alert-info');
            if (alert) {
                alert.remove();
            }
            
            this.showNotification('success', 'Draft configuration restored successfully');
        }
    }

    async loadPredictionConfiguration() {
        try {
            const response = await fetch('/config/api/prediction');
            const result = await response.json();
            
            if (result.success) {
                this.populatePredictionForm(result.data);
                this.currentConfig.prediction = result.data;
            } else {
                console.error('Error loading prediction configuration:', result.error);
            }
        } catch (error) {
            console.error('Error loading prediction configuration:', error);
            this.showNotification('error', 'Failed to load prediction configuration');
        }
    }

    populatePredictionForm(data) {
        // Populate forecast horizons
        if (data.forecast_horizons) {
            document.getElementById('forecast_weekly').checked = data.forecast_horizons.weekly;
            document.getElementById('forecast_monthly').checked = data.forecast_horizons.monthly;
            document.getElementById('forecast_quarterly').checked = data.forecast_horizons.quarterly;
            document.getElementById('forecast_yearly').checked = data.forecast_horizons.yearly;
        }

        // Populate confidence intervals
        if (data.confidence_intervals) {
            document.getElementById('confidence_80').checked = data.confidence_intervals['80'];
            document.getElementById('confidence_90').checked = data.confidence_intervals['90'];
            document.getElementById('confidence_95').checked = data.confidence_intervals['95'];
            document.getElementById('default_confidence').value = data.confidence_intervals.default;
        }

        // Populate external factors
        if (data.external_factors) {
            const factors = data.external_factors;
            this.setSliderValue('seasonality_weight', factors.seasonality, 'seasonality_value');
            this.setSliderValue('trend_weight', factors.trend, 'trend_value');
            this.setSliderValue('economic_weight', factors.economic, 'economic_value');
            this.setSliderValue('promotional_weight', factors.promotional, 'promotional_value');
        }

        // Populate thresholds
        if (data.thresholds) {
            document.getElementById('low_stock_threshold').value = Math.round(data.thresholds.low_stock * 100);
            document.getElementById('high_stock_threshold').value = Math.round(data.thresholds.high_stock * 100);
            document.getElementById('demand_spike_threshold').value = Math.round(data.thresholds.demand_spike * 100);
        }

        // Populate store-specific settings
        if (data.store_specific) {
            document.getElementById('store_specific_enabled').checked = data.store_specific.enabled;
            this.updateStoreMappingsPreview(data.store_specific.mappings);
        }
    }

    setSliderValue(sliderId, value, displayId) {
        const slider = document.getElementById(sliderId);
        const display = document.getElementById(displayId);
        
        if (slider) {
            slider.value = value;
        }
        if (display) {
            display.textContent = Math.round(value * 100) + '%';
        }
    }

    updateStoreMappingsPreview(mappings) {
        const preview = document.getElementById('store_mappings_preview');
        if (preview && Object.keys(mappings).length > 0) {
            let html = '<div class="row">';
            for (const [store, config] of Object.entries(mappings)) {
                html += `
                    <div class="col-md-6 mb-2">
                        <small class="text-muted"><strong>${store}:</strong></small><br>
                        <small>Confidence: ${config.confidence_level || 90}%</small>
                    </div>
                `;
            }
            html += '</div>';
            preview.innerHTML = html;
        }
    }

    async loadCorrelationConfiguration() {
        try {
            const response = await fetch('/config/api/correlation');
            const result = await response.json();
            
            if (result.success) {
                this.populateCorrelationForm(result.data);
                this.currentConfig.correlation = result.data;
            } else {
                console.error('Error loading correlation configuration:', result.error);
            }
        } catch (error) {
            console.error('Error loading correlation configuration:', error);
            this.showNotification('error', 'Failed to load correlation configuration');
        }
    }

    populateCorrelationForm(data) {
        // Populate correlation thresholds
        if (data.thresholds) {
            document.getElementById('correlation_weak').value = data.thresholds.weak;
            document.getElementById('correlation_moderate').value = data.thresholds.moderate;
            document.getElementById('correlation_strong').value = data.thresholds.strong;
        }

        // Populate statistical settings
        if (data.statistical) {
            document.getElementById('p_value_threshold').value = data.statistical.p_value;
            document.getElementById('confidence_level_corr').value = data.statistical.confidence;
        }

        // Populate lag periods
        if (data.lag_periods) {
            document.getElementById('min_lag_periods').value = data.lag_periods.min;
            document.getElementById('max_lag_periods').value = data.lag_periods.max;
            document.getElementById('default_lag_period').value = data.lag_periods.default;
        }

        // Populate factor selections
        if (data.factors) {
            document.getElementById('economic_factors').checked = data.factors.economic;
            document.getElementById('seasonal_factors').checked = data.factors.seasonal;
            document.getElementById('promotional_factors').checked = data.factors.promotional;
            document.getElementById('weather_factors').checked = data.factors.weather;
        }

        // Populate analysis types
        if (data.analysis_types) {
            document.getElementById('auto_correlation').checked = data.analysis_types.auto_correlation;
            document.getElementById('cross_correlation').checked = data.analysis_types.cross_correlation;
            document.getElementById('partial_correlation').checked = data.analysis_types.partial_correlation;
        }
    }

    async loadBusinessIntelligenceConfiguration() {
        try {
            const response = await fetch('/config/api/business-intelligence');
            const result = await response.json();
            
            if (result.success) {
                this.populateBusinessIntelligenceForm(result.data);
                this.currentConfig.businessIntelligence = result.data;
            }
        } catch (error) {
            console.error('Error loading BI configuration:', error);
        }
    }

    populateBusinessIntelligenceForm(data) {
        // Populate KPI targets
        if (data.kpi_targets) {
            const kpis = data.kpi_targets;
            document.getElementById('revenue_monthly').value = kpis.revenue_monthly;
            document.getElementById('revenue_quarterly').value = kpis.revenue_quarterly;
            document.getElementById('revenue_yearly').value = kpis.revenue_yearly;
            document.getElementById('inventory_turnover').value = kpis.inventory_turnover;
            document.getElementById('profit_margin').value = Math.round(kpis.profit_margin * 100);
            document.getElementById('customer_satisfaction').value = Math.round(kpis.customer_satisfaction * 100);
        }

        // Populate benchmarks
        if (data.benchmarks) {
            document.getElementById('industry_benchmark').checked = data.benchmarks.industry_avg;
            document.getElementById('historical_benchmark').checked = data.benchmarks.historical;
            document.getElementById('competitor_benchmark').checked = data.benchmarks.competitor;
        }

        // Populate ROI settings
        if (data.roi_calculation) {
            const roi = data.roi_calculation;
            document.getElementById('roi_period').value = roi.period;
            document.getElementById('discount_rate').value = Math.round(roi.discount_rate * 100);
            document.getElementById('include_overhead').checked = roi.include_overhead;
            document.getElementById('include_labor').checked = roi.include_labor;
        }

        // Populate resale criteria
        if (data.resale_criteria) {
            const resale = data.resale_criteria;
            document.getElementById('resale_profit_margin').value = Math.round(resale.min_profit_margin * 100);
            document.getElementById('resale_max_age').value = resale.max_age_months;
            document.getElementById('condition_threshold').value = resale.condition_threshold;
            document.getElementById('demand_threshold').value = Math.round(resale.demand_threshold * 100);
        }
    }

    async loadDataIntegrationConfiguration() {
        try {
            const response = await fetch('/config/api/data-integration');
            const result = await response.json();
            
            if (result.success) {
                this.populateDataIntegrationForm(result.data);
                this.currentConfig.dataIntegration = result.data;
            }
        } catch (error) {
            console.error('Error loading data integration configuration:', error);
        }
    }

    populateDataIntegrationForm(data) {
        // Populate CSV import settings
        if (data.csv_import) {
            const csv = data.csv_import;
            document.getElementById('csv_auto_import').checked = csv.auto_import_enabled;
            document.getElementById('import_frequency').value = csv.frequency;
            document.getElementById('import_time').value = csv.time.substring(0, 5); // HH:MM format
            document.getElementById('csv_backup').checked = csv.backup_enabled;
            document.getElementById('csv_validation').checked = csv.validation_strict;
        }

        // Populate API configuration
        if (data.api_config) {
            const api = data.api_config;
            document.getElementById('api_timeout').value = api.timeout_seconds;
            document.getElementById('retry_attempts').value = api.retry_attempts;
            document.getElementById('rate_limit_enabled').checked = api.rate_limit_enabled;
            document.getElementById('rate_limit_requests').value = api.rate_limit_requests;
            document.getElementById('rate_limit_window').value = api.rate_limit_window;
        }

        // Populate refresh settings
        if (data.refresh_settings) {
            const refresh = data.refresh_settings;
            document.getElementById('real_time_refresh').checked = refresh.real_time_enabled;
            document.getElementById('refresh_interval').value = refresh.interval_minutes;
            document.getElementById('background_refresh').checked = refresh.background_enabled;
        }

        // Populate quality checks
        if (data.quality_checks) {
            const quality = data.quality_checks;
            document.getElementById('quality_checks').checked = quality.enabled;
            document.getElementById('missing_data_threshold').value = Math.round(quality.missing_data_threshold * 100);
            document.getElementById('outlier_detection').checked = quality.outlier_detection_enabled;
            document.getElementById('outlier_method').value = quality.outlier_method;
        }
    }

    async loadUserPreferences() {
        try {
            const response = await fetch('/config/api/user-preferences');
            const result = await response.json();
            
            if (result.success) {
                this.populateUserPreferencesForm(result.data);
                this.currentConfig.userPreferences = result.data;
            }
        } catch (error) {
            console.error('Error loading user preferences:', error);
        }
    }

    populateUserPreferencesForm(data) {
        // Populate dashboard settings
        if (data.dashboard) {
            const dashboard = data.dashboard;
            document.getElementById('dashboard_theme').value = dashboard.theme;
            document.getElementById('dashboard_layout').value = dashboard.layout;
            document.getElementById('color_scheme').value = dashboard.color_scheme;
            document.getElementById('dark_mode').checked = dashboard.dark_mode;
        }

        // Populate defaults
        if (data.defaults) {
            const defaults = data.defaults;
            document.getElementById('default_time_range').value = defaults.time_range;
            document.getElementById('default_store').value = defaults.store_filter;
            document.getElementById('auto_refresh_ui').checked = defaults.auto_refresh;
            document.getElementById('refresh_interval_ui').value = defaults.refresh_interval;
        }

        // Populate notifications
        if (data.notifications) {
            const notifications = data.notifications;
            document.getElementById('email_notifications').checked = notifications.email_enabled;
            document.getElementById('push_notifications').checked = notifications.push_enabled;
            document.getElementById('alert_frequency').value = notifications.frequency;
            
            // Handle notification types array
            if (notifications.types && Array.isArray(notifications.types)) {
                document.getElementById('critical_alerts').checked = notifications.types.includes('critical');
                document.getElementById('warning_alerts').checked = notifications.types.includes('warning');
                document.getElementById('info_alerts').checked = notifications.types.includes('info');
            }
        }

        // Populate report settings
        if (data.reports) {
            const reports = data.reports;
            document.getElementById('report_format').value = reports.format;
            document.getElementById('report_schedule').checked = reports.schedule_enabled;
            document.getElementById('report_frequency').value = reports.frequency;
            
            if (reports.recipients && Array.isArray(reports.recipients)) {
                document.getElementById('report_recipients').value = reports.recipients.join(', ');
            }
        }

        // Populate UI preferences
        if (data.ui_preferences) {
            const ui = data.ui_preferences;
            document.getElementById('show_tooltips').checked = ui.show_tooltips;
            document.getElementById('show_animations').checked = ui.show_animations;
            document.getElementById('compact_mode').checked = ui.compact_mode;
            document.getElementById('keyboard_shortcuts').checked = ui.keyboard_shortcuts;
        }
    }

    async savePredictionConfiguration() {
        const formData = this.collectPredictionFormData();
        
        if (!this.validatePredictionData(formData)) {
            return;
        }

        try {
            this.showLoadingState('prediction-form');
            
            const response = await fetch('/config/api/prediction', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('success', 'Prediction configuration saved successfully');
                this.unsavedChanges = false;
                this.updateSaveButtonStates();
                localStorage.removeItem('rfid_config_draft'); // Clear draft
            } else {
                this.showNotification('error', 'Error saving prediction configuration: ' + result.error);
            }
        } catch (error) {
            console.error('Error saving prediction configuration:', error);
            this.showNotification('error', 'Failed to save prediction configuration');
        } finally {
            this.hideLoadingState('prediction-form');
        }
    }

    collectPredictionFormData() {
        return {
            forecast_horizons: {
                weekly: document.getElementById('forecast_weekly').checked,
                monthly: document.getElementById('forecast_monthly').checked,
                quarterly: document.getElementById('forecast_quarterly').checked,
                yearly: document.getElementById('forecast_yearly').checked
            },
            confidence_intervals: {
                '80': document.getElementById('confidence_80').checked,
                '90': document.getElementById('confidence_90').checked,
                '95': document.getElementById('confidence_95').checked,
                default: parseFloat(document.getElementById('default_confidence').value)
            },
            external_factors: {
                seasonality: parseFloat(document.getElementById('seasonality_weight').value),
                trend: parseFloat(document.getElementById('trend_weight').value),
                economic: parseFloat(document.getElementById('economic_weight').value),
                promotional: parseFloat(document.getElementById('promotional_weight').value)
            },
            thresholds: {
                low_stock: parseFloat(document.getElementById('low_stock_threshold').value) / 100,
                high_stock: parseFloat(document.getElementById('high_stock_threshold').value) / 100,
                demand_spike: parseFloat(document.getElementById('demand_spike_threshold').value) / 100
            },
            store_specific: {
                enabled: document.getElementById('store_specific_enabled').checked,
                mappings: {} // Would be populated from a more complex UI
            }
        };
    }

    validatePredictionData(data) {
        // Validate that at least one forecast horizon is selected
        const horizons = data.forecast_horizons;
        if (!horizons.weekly && !horizons.monthly && !horizons.quarterly && !horizons.yearly) {
            this.showNotification('warning', 'Please select at least one forecast horizon');
            return false;
        }

        // Validate that at least one confidence interval is selected
        const intervals = data.confidence_intervals;
        if (!intervals['80'] && !intervals['90'] && !intervals['95']) {
            this.showNotification('warning', 'Please select at least one confidence interval');
            return false;
        }

        // Validate weight distribution
        const factors = data.external_factors;
        const total = factors.seasonality + factors.trend + factors.economic + factors.promotional;
        const tolerance = 0.05;
        
        if (Math.abs(total - 1.0) > tolerance) {
            this.showNotification('warning', `External factor weights must total 100% (currently ${Math.round(total * 100)}%)`);
            return false;
        }

        return true;
    }

    async saveCorrelationConfiguration() {
        const formData = this.collectCorrelationFormData();
        
        if (!this.validateCorrelationData(formData)) {
            return;
        }

        try {
            this.showLoadingState('correlation-form');
            
            const response = await fetch('/config/api/correlation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('success', 'Correlation configuration saved successfully');
                this.unsavedChanges = false;
                this.updateSaveButtonStates();
            } else {
                this.showNotification('error', 'Error saving correlation configuration: ' + result.error);
            }
        } catch (error) {
            console.error('Error saving correlation configuration:', error);
            this.showNotification('error', 'Failed to save correlation configuration');
        } finally {
            this.hideLoadingState('correlation-form');
        }
    }

    collectCorrelationFormData() {
        return {
            thresholds: {
                weak: parseFloat(document.getElementById('correlation_weak').value),
                moderate: parseFloat(document.getElementById('correlation_moderate').value),
                strong: parseFloat(document.getElementById('correlation_strong').value)
            },
            statistical: {
                p_value: parseFloat(document.getElementById('p_value_threshold').value),
                confidence: parseFloat(document.getElementById('confidence_level_corr').value)
            },
            lag_periods: {
                min: parseInt(document.getElementById('min_lag_periods').value),
                max: parseInt(document.getElementById('max_lag_periods').value),
                default: parseInt(document.getElementById('default_lag_period').value)
            },
            factors: {
                economic: document.getElementById('economic_factors').checked,
                seasonal: document.getElementById('seasonal_factors').checked,
                promotional: document.getElementById('promotional_factors').checked,
                weather: document.getElementById('weather_factors').checked
            },
            analysis_types: {
                auto_correlation: document.getElementById('auto_correlation').checked,
                cross_correlation: document.getElementById('cross_correlation').checked,
                partial_correlation: document.getElementById('partial_correlation').checked
            }
        };
    }

    validateCorrelationData(data) {
        // Validate threshold order
        const thresholds = data.thresholds;
        if (thresholds.weak >= thresholds.moderate) {
            this.showNotification('warning', 'Weak correlation threshold must be less than moderate threshold');
            return false;
        }
        if (thresholds.moderate >= thresholds.strong) {
            this.showNotification('warning', 'Moderate correlation threshold must be less than strong threshold');
            return false;
        }

        // Validate lag periods
        const lag = data.lag_periods;
        if (lag.min >= lag.max) {
            this.showNotification('warning', 'Minimum lag periods must be less than maximum lag periods');
            return false;
        }
        if (lag.default < lag.min || lag.default > lag.max) {
            this.showNotification('warning', 'Default lag period must be between minimum and maximum values');
            return false;
        }

        // Validate that at least one analysis type is selected
        const analysis = data.analysis_types;
        if (!analysis.auto_correlation && !analysis.cross_correlation && !analysis.partial_correlation) {
            this.showNotification('warning', 'Please select at least one analysis type');
            return false;
        }

        return true;
    }

    async saveBusinessIntelligenceConfiguration() {
        const formData = this.collectBusinessIntelligenceFormData();
        
        try {
            this.showLoadingState('bi-form');
            
            const response = await fetch('/config/api/business-intelligence', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('success', 'Business Intelligence configuration saved successfully');
                this.unsavedChanges = false;
                this.updateSaveButtonStates();
            } else {
                this.showNotification('error', 'Error saving BI configuration: ' + result.error);
            }
        } catch (error) {
            console.error('Error saving BI configuration:', error);
            this.showNotification('error', 'Failed to save BI configuration');
        } finally {
            this.hideLoadingState('bi-form');
        }
    }

    collectBusinessIntelligenceFormData() {
        return {
            kpi_targets: {
                revenue_monthly: parseFloat(document.getElementById('revenue_monthly').value),
                revenue_quarterly: parseFloat(document.getElementById('revenue_quarterly').value),
                revenue_yearly: parseFloat(document.getElementById('revenue_yearly').value),
                inventory_turnover: parseFloat(document.getElementById('inventory_turnover').value),
                profit_margin: parseFloat(document.getElementById('profit_margin').value) / 100,
                customer_satisfaction: parseFloat(document.getElementById('customer_satisfaction').value) / 100
            },
            benchmarks: {
                industry_avg: document.getElementById('industry_benchmark').checked,
                historical: document.getElementById('historical_benchmark').checked,
                competitor: document.getElementById('competitor_benchmark').checked
            },
            roi_calculation: {
                period: document.getElementById('roi_period').value,
                include_overhead: document.getElementById('include_overhead').checked,
                include_labor: document.getElementById('include_labor').checked,
                discount_rate: parseFloat(document.getElementById('discount_rate').value) / 100
            },
            resale_criteria: {
                min_profit_margin: parseFloat(document.getElementById('resale_profit_margin').value) / 100,
                max_age_months: parseInt(document.getElementById('resale_max_age').value),
                condition_threshold: parseFloat(document.getElementById('condition_threshold').value),
                demand_threshold: parseFloat(document.getElementById('demand_threshold').value) / 100
            }
        };
    }

    async saveDataIntegrationConfiguration() {
        const formData = this.collectDataIntegrationFormData();
        
        try {
            this.showLoadingState('integration-form');
            
            const response = await fetch('/config/api/data-integration', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('success', 'Data Integration configuration saved successfully');
                this.unsavedChanges = false;
                this.updateSaveButtonStates();
            } else {
                this.showNotification('error', 'Error saving Data Integration configuration: ' + result.error);
            }
        } catch (error) {
            console.error('Error saving Data Integration configuration:', error);
            this.showNotification('error', 'Failed to save Data Integration configuration');
        } finally {
            this.hideLoadingState('integration-form');
        }
    }

    collectDataIntegrationFormData() {
        return {
            csv_import: {
                auto_import_enabled: document.getElementById('csv_auto_import').checked,
                frequency: document.getElementById('import_frequency').value,
                time: document.getElementById('import_time').value + ':00', // Add seconds
                backup_enabled: document.getElementById('csv_backup').checked,
                validation_strict: document.getElementById('csv_validation').checked
            },
            api_config: {
                timeout_seconds: parseInt(document.getElementById('api_timeout').value),
                retry_attempts: parseInt(document.getElementById('retry_attempts').value),
                rate_limit_enabled: document.getElementById('rate_limit_enabled').checked,
                rate_limit_requests: parseInt(document.getElementById('rate_limit_requests').value),
                rate_limit_window: parseInt(document.getElementById('rate_limit_window').value)
            },
            refresh_settings: {
                real_time_enabled: document.getElementById('real_time_refresh').checked,
                interval_minutes: parseInt(document.getElementById('refresh_interval').value),
                background_enabled: document.getElementById('background_refresh').checked
            },
            quality_checks: {
                enabled: document.getElementById('quality_checks').checked,
                missing_data_threshold: parseFloat(document.getElementById('missing_data_threshold').value) / 100,
                outlier_detection_enabled: document.getElementById('outlier_detection').checked,
                outlier_method: document.getElementById('outlier_method').value
            }
        };
    }

    async saveUserPreferences() {
        const formData = this.collectUserPreferencesFormData();
        
        try {
            this.showLoadingState('preferences-form');
            
            const response = await fetch('/config/api/user-preferences', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('success', 'User preferences saved successfully');
                this.unsavedChanges = false;
                this.updateSaveButtonStates();
            } else {
                this.showNotification('error', 'Error saving user preferences: ' + result.error);
            }
        } catch (error) {
            console.error('Error saving user preferences:', error);
            this.showNotification('error', 'Failed to save user preferences');
        } finally {
            this.hideLoadingState('preferences-form');
        }
    }

    collectUserPreferencesFormData() {
        // Collect notification types
        const notificationTypes = [];
        if (document.getElementById('critical_alerts').checked) notificationTypes.push('critical');
        if (document.getElementById('warning_alerts').checked) notificationTypes.push('warning');
        if (document.getElementById('info_alerts').checked) notificationTypes.push('info');

        // Collect report recipients
        const recipientsInput = document.getElementById('report_recipients').value;
        const recipients = recipientsInput ? recipientsInput.split(',').map(email => email.trim()) : [];

        return {
            dashboard: {
                theme: document.getElementById('dashboard_theme').value,
                layout: document.getElementById('dashboard_layout').value,
                color_scheme: document.getElementById('color_scheme').value,
                dark_mode: document.getElementById('dark_mode').checked
            },
            defaults: {
                time_range: document.getElementById('default_time_range').value,
                store_filter: document.getElementById('default_store').value,
                auto_refresh: document.getElementById('auto_refresh_ui').checked,
                refresh_interval: parseInt(document.getElementById('refresh_interval_ui').value)
            },
            notifications: {
                email_enabled: document.getElementById('email_notifications').checked,
                push_enabled: document.getElementById('push_notifications').checked,
                frequency: document.getElementById('alert_frequency').value,
                types: notificationTypes
            },
            reports: {
                format: document.getElementById('report_format').value,
                schedule_enabled: document.getElementById('report_schedule').checked,
                frequency: document.getElementById('report_frequency').value,
                recipients: recipients
            },
            ui_preferences: {
                show_tooltips: document.getElementById('show_tooltips').checked,
                show_animations: document.getElementById('show_animations').checked,
                compact_mode: document.getElementById('compact_mode').checked,
                keyboard_shortcuts: document.getElementById('keyboard_shortcuts').checked
            }
        };
    }

    async resetConfiguration(configType) {
        if (!confirm(`Are you sure you want to reset ${configType} configuration to defaults? This cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch(`/config/api/reset/${configType}`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('success', result.message);
                // Reload the specific configuration
                switch (configType) {
                    case 'prediction':
                        await this.loadPredictionConfiguration();
                        break;
                    case 'correlation':
                        await this.loadCorrelationConfiguration();
                        break;
                    case 'bi':
                        await this.loadBusinessIntelligenceConfiguration();
                        break;
                    case 'integration':
                        await this.loadDataIntegrationConfiguration();
                        break;
                    case 'preferences':
                        await this.loadUserPreferences();
                        break;
                    case 'executive-dashboard':
                        await this.loadExecutiveDashboardConfiguration();
                        break;
                    case 'labor-cost':
                        await this.loadLaborCostConfiguration();
                        break;
                }
                this.unsavedChanges = false;
                this.updateSaveButtonStates();
            } else {
                this.showNotification('error', 'Error resetting configuration: ' + result.error);
            }
        } catch (error) {
            console.error('Error resetting configuration:', error);
            this.showNotification('error', 'Failed to reset configuration');
        }
    }

    onTabChange(tab) {
        const targetId = tab.getAttribute('data-bs-target');
        console.log('Tab changed to:', targetId);
        
        // Update URL hash without triggering page reload
        const hashName = targetId.replace('#', '').replace('-panel', '');
        history.replaceState(null, null, `#${hashName}`);
        
        // Any tab-specific initialization can go here
    }

    saveCurrentConfiguration() {
        const activeTab = document.querySelector('.nav-link.active');
        if (activeTab) {
            const targetId = activeTab.getAttribute('data-bs-target');
            switch (targetId) {
                case '#prediction-panel':
                    this.savePredictionConfiguration();
                    break;
                case '#correlation-panel':
                    this.saveCorrelationConfiguration();
                    break;
                case '#bi-panel':
                    this.saveBusinessIntelligenceConfiguration();
                    break;
                case '#integration-panel':
                    this.saveDataIntegrationConfiguration();
                    break;
                case '#preferences-panel':
                    this.saveUserPreferences();
                    break;
                case '#executive-dashboard-panel':
                    this.saveExecutiveDashboardConfiguration();
                    break;
                case '#labor-cost-panel':
                    this.saveLaborCostConfiguration();
                    break;
            }
        }
    }

    collectAllFormData() {
        return {
            prediction: this.collectPredictionFormData(),
            correlation: this.collectCorrelationFormData(),
            businessIntelligence: this.collectBusinessIntelligenceFormData(),
            dataIntegration: this.collectDataIntegrationFormData(),
            userPreferences: this.collectUserPreferencesFormData(),
            executiveDashboard: this.collectExecutiveDashboardFormData(),
            laborCost: this.collectLaborCostFormData()
        };
    }

    populateFormsWithData(data) {
        if (data.prediction) this.populatePredictionForm(data.prediction);
        if (data.correlation) this.populateCorrelationForm(data.correlation);
        if (data.businessIntelligence) this.populateBusinessIntelligenceForm(data.businessIntelligence);
        if (data.dataIntegration) this.populateDataIntegrationForm(data.dataIntegration);
        if (data.userPreferences) this.populateUserPreferencesForm(data.userPreferences);
        if (data.executiveDashboard) this.populateExecutiveDashboardForm(data.executiveDashboard);
        if (data.laborCost) this.populateLaborCostForm(data.laborCost);
    }

    updateSaveButtonStates() {
        const saveButtons = document.querySelectorAll('.btn-config-primary');
        saveButtons.forEach(button => {
            if (this.unsavedChanges) {
                button.classList.add('btn-warning');
                button.classList.remove('btn-config-primary');
                button.innerHTML = button.innerHTML.replace('Save', 'Save Changes');
            } else {
                button.classList.remove('btn-warning');
                button.classList.add('btn-config-primary');
                button.innerHTML = button.innerHTML.replace('Save Changes', 'Save');
            }
        });
    }

    showLoadingState(formId) {
        const form = document.getElementById(formId);
        if (form) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                const originalText = submitButton.innerHTML;
                submitButton.setAttribute('data-original-text', originalText);
                submitButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';
            }
        }
    }

    hideLoadingState(formId) {
        const form = document.getElementById(formId);
        if (form) {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = false;
                const originalText = submitButton.getAttribute('data-original-text');
                if (originalText) {
                    submitButton.innerHTML = originalText;
                }
            }
        }
    }

    showNotification(type, message) {
        // Remove existing notifications
        const existing = document.querySelector('.config-notification');
        if (existing) {
            existing.remove();
        }

        // Create new notification
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show config-notification`;
        notification.style.position = 'fixed';
        notification.style.top = '20px';
        notification.style.right = '20px';
        notification.style.zIndex = '9999';
        notification.style.minWidth = '300px';
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    showConfigurationAlert(type, message, formId) {
        let alertContainer = document.querySelector(`#${formId} .config-alert-container`);
        if (!alertContainer) {
            alertContainer = document.createElement('div');
            alertContainer.className = 'config-alert-container';
            const form = document.getElementById(formId);
            if (form) {
                form.insertBefore(alertContainer, form.firstChild);
            }
        }

        alertContainer.innerHTML = `
            <div class="alert alert-${type} alert-dismissible fade show">
                <i class="fas fa-${type === 'warning' ? 'exclamation-triangle' : 'info-circle'} me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
    }

    hideConfigurationAlert(formId) {
        const alertContainer = document.querySelector(`#${formId} .config-alert-container`);
        if (alertContainer) {
            alertContainer.innerHTML = '';
        }
    }

    // Executive Dashboard Configuration Methods
    async loadExecutiveDashboardConfiguration() {
        try {
            const response = await fetch('/config/api/executive-dashboard-configuration');
            const result = await response.json();
            
            if (result.success) {
                this.populateExecutiveDashboardForm(result.data);
                this.currentConfig.executiveDashboard = result.data;
            }
        } catch (error) {
            console.error('Error loading executive dashboard configuration:', error);
        }
    }

    populateExecutiveDashboardForm(data) {
        // Populate query limits
        if (data.query_limits) {
            const limits = data.query_limits;
            document.getElementById('executive_summary_revenue_weeks').value = limits.executive_summary_revenue_weeks || 3;
            document.getElementById('financial_kpis_current_revenue_weeks').value = limits.financial_kpis_current_revenue_weeks || 3;
            document.getElementById('financial_kpis_debug_weeks').value = limits.financial_kpis_debug_weeks || 3;
            document.getElementById('location_kpis_revenue_weeks').value = limits.location_kpis_revenue_weeks || 3;
            document.getElementById('location_kpis_payroll_weeks').value = limits.location_kpis_payroll_weeks || 3;
            document.getElementById('location_comparison_revenue_weeks').value = limits.location_comparison_revenue_weeks || 3;
            document.getElementById('insights_profit_margin_weeks').value = limits.insights_profit_margin_weeks || 3;
            document.getElementById('insights_trend_analysis_weeks').value = limits.insights_trend_analysis_weeks || 12;
            document.getElementById('forecasts_historical_weeks').value = limits.forecasts_historical_weeks || 24;
            document.getElementById('forecasting_historical_weeks').value = limits.forecasting_historical_weeks || 52;
        }

        // Populate health scoring
        if (data.health_scoring) {
            const health = data.health_scoring;
            document.getElementById('health_excellent_threshold').value = Math.round((health.excellent_threshold || 0.9) * 100);
            document.getElementById('health_good_threshold').value = Math.round((health.good_threshold || 0.75) * 100);
            document.getElementById('health_fair_threshold').value = Math.round((health.fair_threshold || 0.5) * 100);
            document.getElementById('enable_predictive_health').checked = health.enable_predictive || false;
        }

        // Populate revenue tiers
        if (data.revenue_tiers) {
            const tiers = data.revenue_tiers;
            document.getElementById('tier_1_threshold').value = tiers.tier_1_threshold || 10000;
            document.getElementById('tier_2_threshold').value = tiers.tier_2_threshold || 50000;
            document.getElementById('tier_3_threshold').value = tiers.tier_3_threshold || 100000;
        }
    }

    collectExecutiveDashboardFormData() {
        return {
            query_limits: {
                executive_summary_revenue_weeks: parseInt(document.getElementById('executive_summary_revenue_weeks').value) || 3,
                financial_kpis_current_revenue_weeks: parseInt(document.getElementById('financial_kpis_current_revenue_weeks').value) || 3,
                financial_kpis_debug_weeks: parseInt(document.getElementById('financial_kpis_debug_weeks').value) || 3,
                location_kpis_revenue_weeks: parseInt(document.getElementById('location_kpis_revenue_weeks').value) || 3,
                location_kpis_payroll_weeks: parseInt(document.getElementById('location_kpis_payroll_weeks').value) || 3,
                location_comparison_revenue_weeks: parseInt(document.getElementById('location_comparison_revenue_weeks').value) || 3,
                insights_profit_margin_weeks: parseInt(document.getElementById('insights_profit_margin_weeks').value) || 3,
                insights_trend_analysis_weeks: parseInt(document.getElementById('insights_trend_analysis_weeks').value) || 12,
                forecasts_historical_weeks: parseInt(document.getElementById('forecasts_historical_weeks').value) || 24,
                forecasting_historical_weeks: parseInt(document.getElementById('forecasting_historical_weeks').value) || 52
            },
            health_scoring: {
                excellent_threshold: parseFloat(document.getElementById('health_excellent_threshold').value) / 100 || 0.9,
                good_threshold: parseFloat(document.getElementById('health_good_threshold').value) / 100 || 0.75,
                fair_threshold: parseFloat(document.getElementById('health_fair_threshold').value) / 100 || 0.5,
                enable_predictive: document.getElementById('enable_predictive_health').checked
            },
            revenue_tiers: {
                tier_1_threshold: parseInt(document.getElementById('tier_1_threshold').value) || 10000,
                tier_2_threshold: parseInt(document.getElementById('tier_2_threshold').value) || 50000,
                tier_3_threshold: parseInt(document.getElementById('tier_3_threshold').value) || 100000
            },
            store_overrides: this.collectStoreOverrides('executive-dashboard')
        };
    }

    async saveExecutiveDashboardConfiguration() {
        const formData = this.collectExecutiveDashboardFormData();
        
        try {
            this.showLoadingState('executive-dashboard-form');
            
            const response = await fetch('/config/api/executive-dashboard-configuration', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('success', 'Executive Dashboard configuration saved successfully');
                this.unsavedChanges = false;
                this.updateSaveButtonStates();
            } else {
                this.showNotification('error', 'Error saving executive dashboard configuration: ' + result.error);
            }
        } catch (error) {
            console.error('Error saving executive dashboard configuration:', error);
            this.showNotification('error', 'Failed to save executive dashboard configuration');
        } finally {
            this.hideLoadingState('executive-dashboard-form');
        }
    }

    // Labor Cost Configuration Methods
    async loadLaborCostConfiguration() {
        try {
            const response = await fetch('/config/api/labor-cost-configuration');
            const result = await response.json();
            
            if (result.success) {
                this.populateLaborCostForm(result.data);
                this.currentConfig.laborCost = result.data;
            }
        } catch (error) {
            console.error('Error loading labor cost configuration:', error);
        }
    }

    populateLaborCostForm(data) {
        // Populate labor cost thresholds
        if (data.thresholds) {
            const thresholds = data.thresholds;
            document.getElementById('labor_cost_warning_threshold').value = Math.round((thresholds.warning_threshold || 0.15) * 100);
            document.getElementById('labor_cost_critical_threshold').value = Math.round((thresholds.critical_threshold || 0.25) * 100);
            document.getElementById('efficiency_target').value = Math.round((thresholds.efficiency_target || 0.85) * 100);
            document.getElementById('overtime_threshold').value = Math.round((thresholds.overtime_threshold || 1.4) * 100);
        }

        // Populate processing settings
        if (data.processing) {
            const processing = data.processing;
            document.getElementById('auto_calculate').checked = processing.auto_calculate_enabled || false;
            document.getElementById('include_benefits').checked = processing.include_benefits || true;
            document.getElementById('include_overtime').checked = processing.include_overtime || true;
            document.getElementById('calculation_frequency').value = processing.frequency || 'daily';
        }

        // Populate alert settings
        if (data.alerts) {
            const alerts = data.alerts;
            document.getElementById('enable_labor_alerts').checked = alerts.enabled || false;
            document.getElementById('alert_frequency').value = alerts.frequency || 'immediate';
            document.getElementById('escalation_enabled').checked = alerts.escalation_enabled || false;
            document.getElementById('alert_recipients').value = (alerts.recipients || []).join(', ');
        }
    }

    collectLaborCostFormData() {
        // Collect alert recipients
        const recipientsInput = document.getElementById('alert_recipients').value;
        const recipients = recipientsInput ? recipientsInput.split(',').map(email => email.trim()) : [];

        return {
            thresholds: {
                warning_threshold: parseFloat(document.getElementById('labor_cost_warning_threshold').value) / 100 || 0.15,
                critical_threshold: parseFloat(document.getElementById('labor_cost_critical_threshold').value) / 100 || 0.25,
                efficiency_target: parseFloat(document.getElementById('efficiency_target').value) / 100 || 0.85,
                overtime_threshold: parseFloat(document.getElementById('overtime_threshold').value) / 100 || 1.4
            },
            processing: {
                auto_calculate_enabled: document.getElementById('auto_calculate').checked,
                include_benefits: document.getElementById('include_benefits').checked,
                include_overtime: document.getElementById('include_overtime').checked,
                frequency: document.getElementById('calculation_frequency').value
            },
            alerts: {
                enabled: document.getElementById('enable_labor_alerts').checked,
                frequency: document.getElementById('alert_frequency').value,
                escalation_enabled: document.getElementById('escalation_enabled').checked,
                recipients: recipients
            },
            store_overrides: this.collectStoreOverrides('labor-cost')
        };
    }

    async saveLaborCostConfiguration() {
        const formData = this.collectLaborCostFormData();
        
        try {
            this.showLoadingState('labor-cost-form');
            
            const response = await fetch('/config/api/labor-cost-configuration', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('success', 'Labor Cost configuration saved successfully');
                this.unsavedChanges = false;
                this.updateSaveButtonStates();
            } else {
                this.showNotification('error', 'Error saving labor cost configuration: ' + result.error);
            }
        } catch (error) {
            console.error('Error saving labor cost configuration:', error);
            this.showNotification('error', 'Failed to save labor cost configuration');
        } finally {
            this.hideLoadingState('labor-cost-form');
        }
    }

    // Helper method for collecting store overrides
    collectStoreOverrides(configType) {
        const overrides = {};
        const overrideTextarea = document.getElementById(`${configType}-store-overrides`);
        
        if (overrideTextarea && overrideTextarea.value.trim()) {
            try {
                const parsed = JSON.parse(overrideTextarea.value);
                return parsed;
            } catch (e) {
                console.warn(`Invalid JSON in ${configType} store overrides:`, e);
            }
        }
        
        return overrides;
    }
}

// Initialize the configuration manager when the page loads
let configManager;

document.addEventListener('DOMContentLoaded', () => {
    configManager = new ConfigurationManager();
});

// Export for global access
window.configManager = configManager;