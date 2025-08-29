-- Configuration System Database Migration
-- Version: 2025-08-29 - Fortune 500 Configuration Management
-- Description: Create comprehensive user configuration tables

-- Main user configurations table
CREATE TABLE IF NOT EXISTS user_configurations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL DEFAULT 'default_user',
    config_type VARCHAR(50) NOT NULL,
    config_name VARCHAR(100) NOT NULL,
    config_data JSON NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_config (user_id, config_type, config_name),
    INDEX idx_user_config_type (user_id, config_type),
    INDEX idx_config_active (is_active, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Prediction parameters configuration
CREATE TABLE IF NOT EXISTS prediction_parameters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL DEFAULT 'default_user',
    parameter_set_name VARCHAR(100) NOT NULL DEFAULT 'default',
    
    -- Forecast Horizons
    forecast_weekly_enabled BOOLEAN DEFAULT TRUE,
    forecast_monthly_enabled BOOLEAN DEFAULT TRUE,
    forecast_quarterly_enabled BOOLEAN DEFAULT TRUE,
    forecast_yearly_enabled BOOLEAN DEFAULT FALSE,
    
    -- Confidence Intervals
    confidence_80_enabled BOOLEAN DEFAULT TRUE,
    confidence_90_enabled BOOLEAN DEFAULT TRUE,
    confidence_95_enabled BOOLEAN DEFAULT FALSE,
    default_confidence_level DECIMAL(5,2) DEFAULT 90.0,
    
    -- External Factor Weights
    seasonality_weight DECIMAL(5,3) DEFAULT 0.3,
    trend_weight DECIMAL(5,3) DEFAULT 0.4,
    economic_weight DECIMAL(5,3) DEFAULT 0.2,
    promotional_weight DECIMAL(5,3) DEFAULT 0.1,
    
    -- Alert Thresholds
    low_stock_threshold DECIMAL(5,3) DEFAULT 0.2,
    high_stock_threshold DECIMAL(5,3) DEFAULT 2.0,
    demand_spike_threshold DECIMAL(5,3) DEFAULT 1.5,
    
    -- Store-specific settings
    store_specific_enabled BOOLEAN DEFAULT TRUE,
    store_mappings JSON DEFAULT '{}',
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_user_param_set (user_id, parameter_set_name),
    INDEX idx_prediction_user (user_id, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Correlation analysis settings
CREATE TABLE IF NOT EXISTS correlation_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL DEFAULT 'default_user',
    setting_name VARCHAR(100) NOT NULL DEFAULT 'default',
    
    -- Minimum correlation thresholds
    min_correlation_weak DECIMAL(4,3) DEFAULT 0.3,
    min_correlation_moderate DECIMAL(4,3) DEFAULT 0.5,
    min_correlation_strong DECIMAL(4,3) DEFAULT 0.7,
    
    -- Statistical significance levels
    p_value_threshold DECIMAL(4,3) DEFAULT 0.05,
    confidence_level DECIMAL(4,3) DEFAULT 0.95,
    
    -- Lag periods for time-series analysis
    max_lag_periods INT DEFAULT 12,
    min_lag_periods INT DEFAULT 1,
    default_lag_period INT DEFAULT 3,
    
    -- Factor selection preferences
    economic_factors_enabled BOOLEAN DEFAULT TRUE,
    seasonal_factors_enabled BOOLEAN DEFAULT TRUE,
    promotional_factors_enabled BOOLEAN DEFAULT TRUE,
    weather_factors_enabled BOOLEAN DEFAULT FALSE,
    
    -- Analysis preferences
    auto_correlation_enabled BOOLEAN DEFAULT TRUE,
    cross_correlation_enabled BOOLEAN DEFAULT TRUE,
    partial_correlation_enabled BOOLEAN DEFAULT FALSE,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_user_correlation_setting (user_id, setting_name),
    INDEX idx_correlation_user (user_id, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Business Intelligence configuration
CREATE TABLE IF NOT EXISTS business_intelligence_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL DEFAULT 'default_user',
    config_name VARCHAR(100) NOT NULL DEFAULT 'default',
    
    -- KPI targets and goals
    revenue_target_monthly DECIMAL(15,2) DEFAULT 100000.0,
    revenue_target_quarterly DECIMAL(15,2) DEFAULT 300000.0,
    revenue_target_yearly DECIMAL(15,2) DEFAULT 1200000.0,
    
    inventory_turnover_target DECIMAL(5,2) DEFAULT 6.0,
    profit_margin_target DECIMAL(5,3) DEFAULT 0.25,
    customer_satisfaction_target DECIMAL(5,3) DEFAULT 0.85,
    
    -- Performance benchmarks
    benchmark_industry_avg_enabled BOOLEAN DEFAULT TRUE,
    benchmark_historical_enabled BOOLEAN DEFAULT TRUE,
    benchmark_competitor_enabled BOOLEAN DEFAULT FALSE,
    
    -- ROI calculation parameters
    roi_calculation_period VARCHAR(20) DEFAULT 'quarterly',
    roi_include_overhead BOOLEAN DEFAULT TRUE,
    roi_include_labor_costs BOOLEAN DEFAULT TRUE,
    roi_discount_rate DECIMAL(5,3) DEFAULT 0.08,
    
    -- Resale recommendation criteria
    resale_min_profit_margin DECIMAL(5,3) DEFAULT 0.15,
    resale_max_age_months INT DEFAULT 24,
    resale_condition_threshold DECIMAL(4,2) DEFAULT 7.0,
    resale_demand_threshold DECIMAL(5,3) DEFAULT 0.3,
    
    -- Alert thresholds
    performance_alert_threshold DECIMAL(5,3) DEFAULT 0.8,
    critical_alert_threshold DECIMAL(5,3) DEFAULT 0.6,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_user_bi_config (user_id, config_name),
    INDEX idx_bi_user (user_id, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Data integration settings
CREATE TABLE IF NOT EXISTS data_integration_settings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL DEFAULT 'default_user',
    setting_name VARCHAR(100) NOT NULL DEFAULT 'default',
    
    -- CSV import schedules and automation
    csv_auto_import_enabled BOOLEAN DEFAULT FALSE,
    csv_import_frequency VARCHAR(20) DEFAULT 'daily',
    csv_import_time VARCHAR(8) DEFAULT '02:00:00',
    csv_backup_enabled BOOLEAN DEFAULT TRUE,
    csv_validation_strict BOOLEAN DEFAULT TRUE,
    
    -- External API configurations
    api_timeout_seconds INT DEFAULT 30,
    api_retry_attempts INT DEFAULT 3,
    api_rate_limit_enabled BOOLEAN DEFAULT TRUE,
    api_rate_limit_requests INT DEFAULT 100,
    api_rate_limit_window INT DEFAULT 3600,
    
    -- Data refresh intervals
    real_time_refresh_enabled BOOLEAN DEFAULT FALSE,
    refresh_interval_minutes INT DEFAULT 15,
    background_refresh_enabled BOOLEAN DEFAULT TRUE,
    
    -- Quality check parameters
    data_quality_checks_enabled BOOLEAN DEFAULT TRUE,
    missing_data_threshold DECIMAL(5,3) DEFAULT 0.1,
    outlier_detection_enabled BOOLEAN DEFAULT TRUE,
    outlier_detection_method VARCHAR(20) DEFAULT 'iqr',
    
    -- File processing settings
    max_file_size_mb INT DEFAULT 50,
    supported_formats JSON DEFAULT '["csv", "xlsx", "json"]',
    archive_processed_files BOOLEAN DEFAULT TRUE,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_user_integration_setting (user_id, setting_name),
    INDEX idx_integration_user (user_id, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- User interface preferences
CREATE TABLE IF NOT EXISTS user_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL DEFAULT 'default_user',
    preference_name VARCHAR(100) NOT NULL DEFAULT 'default',
    
    -- Dashboard layouts and themes
    dashboard_theme VARCHAR(20) DEFAULT 'executive',
    dashboard_layout VARCHAR(20) DEFAULT 'grid',
    chart_color_scheme VARCHAR(20) DEFAULT 'professional',
    dark_mode_enabled BOOLEAN DEFAULT FALSE,
    
    -- Default views and filters
    default_time_range VARCHAR(20) DEFAULT '30_days',
    default_store_filter VARCHAR(50) DEFAULT 'all',
    auto_refresh_enabled BOOLEAN DEFAULT TRUE,
    auto_refresh_interval INT DEFAULT 300,
    
    -- Notification preferences
    email_notifications_enabled BOOLEAN DEFAULT TRUE,
    push_notifications_enabled BOOLEAN DEFAULT FALSE,
    alert_frequency VARCHAR(20) DEFAULT 'immediate',
    notification_types JSON DEFAULT '["critical", "warning"]',
    
    -- Report formats and scheduling
    report_format VARCHAR(10) DEFAULT 'pdf',
    report_schedule_enabled BOOLEAN DEFAULT FALSE,
    report_frequency VARCHAR(20) DEFAULT 'weekly',
    report_recipients JSON DEFAULT '[]',
    
    -- Access permissions and roles
    role VARCHAR(20) DEFAULT 'user',
    accessible_tabs JSON DEFAULT '["tab1", "tab2", "tab3", "tab4", "tab5"]',
    data_export_enabled BOOLEAN DEFAULT TRUE,
    configuration_access BOOLEAN DEFAULT FALSE,
    
    -- UI/UX preferences
    show_tooltips BOOLEAN DEFAULT TRUE,
    show_animations BOOLEAN DEFAULT TRUE,
    compact_mode BOOLEAN DEFAULT FALSE,
    keyboard_shortcuts_enabled BOOLEAN DEFAULT TRUE,
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_user_preference (user_id, preference_name),
    INDEX idx_preferences_user (user_id, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Configuration audit trail
CREATE TABLE IF NOT EXISTS configuration_audit (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    config_type VARCHAR(50) NOT NULL,
    config_id INT NOT NULL,
    action VARCHAR(20) NOT NULL,
    old_values JSON,
    new_values JSON,
    change_reason TEXT,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_audit_user_date (user_id, created_at),
    INDEX idx_audit_config (config_type, config_id),
    INDEX idx_audit_action (action, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default configuration records
INSERT IGNORE INTO prediction_parameters (user_id, parameter_set_name) VALUES ('default_user', 'default');
INSERT IGNORE INTO correlation_settings (user_id, setting_name) VALUES ('default_user', 'default');
INSERT IGNORE INTO business_intelligence_config (user_id, config_name) VALUES ('default_user', 'default');
INSERT IGNORE INTO data_integration_settings (user_id, setting_name) VALUES ('default_user', 'default');
INSERT IGNORE INTO user_preferences (user_id, preference_name) VALUES ('default_user', 'default');

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_config_tables_updated ON user_configurations(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_prediction_updated ON prediction_parameters(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_correlation_updated ON correlation_settings(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_bi_config_updated ON business_intelligence_config(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_integration_updated ON data_integration_settings(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_preferences_updated ON user_preferences(updated_at DESC);

-- Add constraints for data validation
ALTER TABLE prediction_parameters 
ADD CONSTRAINT chk_prediction_weights 
CHECK (seasonality_weight >= 0 AND seasonality_weight <= 1 AND
       trend_weight >= 0 AND trend_weight <= 1 AND
       economic_weight >= 0 AND economic_weight <= 1 AND
       promotional_weight >= 0 AND promotional_weight <= 1);

ALTER TABLE correlation_settings 
ADD CONSTRAINT chk_correlation_thresholds 
CHECK (min_correlation_weak >= 0 AND min_correlation_weak <= 1 AND
       min_correlation_moderate >= 0 AND min_correlation_moderate <= 1 AND
       min_correlation_strong >= 0 AND min_correlation_strong <= 1 AND
       min_correlation_weak < min_correlation_moderate AND
       min_correlation_moderate < min_correlation_strong);

-- Create configuration summary view for easy access
CREATE OR REPLACE VIEW configuration_summary AS
SELECT 
    'prediction' as config_type,
    pp.user_id,
    pp.parameter_set_name as config_name,
    pp.is_active,
    pp.updated_at,
    CASE 
        WHEN pp.forecast_weekly_enabled THEN 'Weekly,'
        ELSE ''
    END +
    CASE 
        WHEN pp.forecast_monthly_enabled THEN 'Monthly,'
        ELSE ''
    END +
    CASE 
        WHEN pp.forecast_quarterly_enabled THEN 'Quarterly,'
        ELSE ''
    END as enabled_features
FROM prediction_parameters pp
WHERE pp.is_active = TRUE

UNION ALL

SELECT 
    'correlation' as config_type,
    cs.user_id,
    cs.setting_name as config_name,
    cs.is_active,
    cs.updated_at,
    CONCAT('Weak:', cs.min_correlation_weak, 
           ' Mod:', cs.min_correlation_moderate,
           ' Strong:', cs.min_correlation_strong) as enabled_features
FROM correlation_settings cs
WHERE cs.is_active = TRUE

UNION ALL

SELECT 
    'business_intelligence' as config_type,
    bi.user_id,
    bi.config_name,
    bi.is_active,
    bi.updated_at,
    CONCAT('Monthly Target: $', FORMAT(bi.revenue_target_monthly, 0)) as enabled_features
FROM business_intelligence_config bi
WHERE bi.is_active = TRUE

UNION ALL

SELECT 
    'data_integration' as config_type,
    di.user_id,
    di.setting_name as config_name,
    di.is_active,
    di.updated_at,
    CASE 
        WHEN di.csv_auto_import_enabled THEN CONCAT('Auto CSV (', di.csv_import_frequency, ')')
        ELSE 'Manual CSV'
    END as enabled_features
FROM data_integration_settings di
WHERE di.is_active = TRUE

UNION ALL

SELECT 
    'user_preferences' as config_type,
    up.user_id,
    up.preference_name as config_name,
    up.is_active,
    up.updated_at,
    CONCAT('Theme:', up.dashboard_theme, ' Layout:', up.dashboard_layout) as enabled_features
FROM user_preferences up
WHERE up.is_active = TRUE;

-- Grant necessary permissions (adjust as needed for your user)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON user_configurations TO 'your_app_user'@'%';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON prediction_parameters TO 'your_app_user'@'%';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON correlation_settings TO 'your_app_user'@'%';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON business_intelligence_config TO 'your_app_user'@'%';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON data_integration_settings TO 'your_app_user'@'%';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON user_preferences TO 'your_app_user'@'%';
-- GRANT SELECT, INSERT ON configuration_audit TO 'your_app_user'@'%';
-- GRANT SELECT ON configuration_summary TO 'your_app_user'@'%';