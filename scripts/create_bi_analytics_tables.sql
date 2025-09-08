-- Business Intelligence Analytics Tables
-- Created: 2025-08-27
-- Purpose: Integrate payroll, scorecard, and operational metrics for executive analytics

-- ====================================================================
-- 1. STORE PERFORMANCE METRICS TABLE
-- ====================================================================
CREATE TABLE IF NOT EXISTS bi_store_performance (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    period_ending DATE NOT NULL,
    store_code VARCHAR(10) NOT NULL,
    period_type ENUM('WEEKLY', 'BIWEEKLY', 'MONTHLY', 'QUARTERLY') DEFAULT 'BIWEEKLY',
    
    -- Revenue Metrics
    rental_revenue DECIMAL(12,2),
    total_revenue DECIMAL(12,2),
    revenue_growth_pct DECIMAL(8,2),  -- Period-over-period growth
    revenue_ytd DECIMAL(12,2),
    
    -- Labor Metrics
    payroll_cost DECIMAL(12,2),
    wage_hours DECIMAL(10,2),
    avg_wage_rate DECIMAL(8,2),
    labor_cost_ratio DECIMAL(8,4),  -- Payroll/Revenue ratio
    overtime_hours DECIMAL(10,2),
    
    -- Efficiency Metrics
    revenue_per_hour DECIMAL(10,2),
    items_per_hour DECIMAL(10,2),
    
    -- Comparison Metrics
    budget_revenue DECIMAL(12,2),
    budget_variance_pct DECIMAL(8,2),
    prior_year_revenue DECIMAL(12,2),
    yoy_growth_pct DECIMAL(8,2),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_period_store (period_ending, store_code),
    INDEX idx_store_period (store_code, period_ending),
    INDEX idx_period_type (period_type, period_ending),
    UNIQUE KEY uk_period_store_type (period_ending, store_code, period_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================================================
-- 2. OPERATIONAL SCORECARD TABLE
-- ====================================================================
CREATE TABLE IF NOT EXISTS bi_operational_scorecard (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    week_ending DATE NOT NULL,
    store_code VARCHAR(10),
    
    -- Contract Metrics
    new_contracts_count INT DEFAULT 0,
    open_quotes_count INT DEFAULT 0,
    contract_conversion_rate DECIMAL(8,4),
    avg_contract_value DECIMAL(12,2),
    
    -- Delivery & Fulfillment
    deliveries_scheduled_7d INT DEFAULT 0,
    pickups_scheduled_7d INT DEFAULT 0,
    on_time_delivery_rate DECIMAL(8,4),
    
    -- Pipeline Metrics
    reservation_pipeline_14d DECIMAL(12,2),
    reservation_pipeline_total DECIMAL(12,2),
    pipeline_conversion_rate DECIMAL(8,4),
    
    -- Financial Health
    ar_total DECIMAL(12,2),
    ar_over_45_days DECIMAL(12,2),
    ar_over_45_days_pct DECIMAL(8,4),
    discount_total DECIMAL(12,2),
    discount_rate_pct DECIMAL(8,4),
    
    -- Customer Metrics
    active_customers INT DEFAULT 0,
    new_customers INT DEFAULT 0,
    customer_retention_rate DECIMAL(8,4),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_week_store (week_ending, store_code),
    INDEX idx_store_week (store_code, week_ending),
    INDEX idx_ar_health (ar_over_45_days_pct, week_ending),
    UNIQUE KEY uk_week_store (week_ending, store_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================================================
-- 3. INVENTORY PERFORMANCE TABLE
-- ====================================================================
CREATE TABLE IF NOT EXISTS bi_inventory_performance (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    period_ending DATE NOT NULL,
    store_code VARCHAR(10),
    rental_class VARCHAR(50),
    
    -- Inventory Levels
    total_units INT DEFAULT 0,
    available_units INT DEFAULT 0,
    on_rent_units INT DEFAULT 0,
    in_repair_units INT DEFAULT 0,
    
    -- Utilization Metrics
    utilization_rate DECIMAL(8,4),
    turnover_rate DECIMAL(8,4),
    days_on_rent_avg DECIMAL(10,2),
    idle_days_avg DECIMAL(10,2),
    
    -- Financial Metrics
    inventory_value DECIMAL(12,2),
    rental_revenue DECIMAL(12,2),
    roi_percentage DECIMAL(8,4),
    revenue_per_unit DECIMAL(10,2),
    
    -- Quality Metrics
    damage_rate DECIMAL(8,4),
    repair_cost DECIMAL(12,2),
    write_off_count INT DEFAULT 0,
    write_off_value DECIMAL(12,2),
    
    -- Demand Indicators
    stockout_incidents INT DEFAULT 0,
    lost_revenue_estimate DECIMAL(12,2),
    demand_forecast_units INT DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_period_store_class (period_ending, store_code, rental_class),
    INDEX idx_utilization (utilization_rate, period_ending),
    INDEX idx_turnover (turnover_rate, period_ending),
    UNIQUE KEY uk_period_store_class (period_ending, store_code, rental_class)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================================================
-- 4. EXECUTIVE KPI SUMMARY TABLE
-- ====================================================================
CREATE TABLE IF NOT EXISTS bi_executive_kpis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    period_ending DATE NOT NULL,
    period_type ENUM('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'YEARLY') DEFAULT 'WEEKLY',
    
    -- Company-wide Revenue
    total_revenue DECIMAL(14,2),
    rental_revenue DECIMAL(14,2),
    service_revenue DECIMAL(14,2),
    revenue_growth_pct DECIMAL(8,2),
    
    -- Profitability
    gross_profit DECIMAL(14,2),
    gross_margin_pct DECIMAL(8,4),
    ebitda DECIMAL(14,2),
    ebitda_margin_pct DECIMAL(8,4),
    
    -- Operational Efficiency
    labor_cost_ratio DECIMAL(8,4),
    inventory_turnover DECIMAL(8,4),
    asset_utilization DECIMAL(8,4),
    
    -- Customer Metrics
    customer_count INT DEFAULT 0,
    customer_acquisition_cost DECIMAL(10,2),
    customer_lifetime_value DECIMAL(12,2),
    net_promoter_score DECIMAL(8,2),
    
    -- Cash Flow
    operating_cash_flow DECIMAL(14,2),
    days_sales_outstanding DECIMAL(10,2),
    cash_conversion_cycle DECIMAL(10,2),
    
    -- Store Comparison (JSON for flexibility)
    store_rankings JSON,
    best_performing_store VARCHAR(10),
    improvement_opportunities JSON,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_period_type (period_type, period_ending),
    UNIQUE KEY uk_period_type (period_ending, period_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================================================
-- 5. PREDICTIVE ANALYTICS TABLE
-- ====================================================================
CREATE TABLE IF NOT EXISTS bi_predictive_analytics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    forecast_date DATE NOT NULL,
    target_date DATE NOT NULL,
    store_code VARCHAR(10),
    metric_name VARCHAR(50) NOT NULL,
    
    -- Forecast Values
    predicted_value DECIMAL(14,4),
    confidence_low DECIMAL(14,4),
    confidence_high DECIMAL(14,4),
    confidence_level DECIMAL(8,4),
    
    -- Model Performance
    model_type VARCHAR(50),
    mape_score DECIMAL(8,4),  -- Mean Absolute Percentage Error
    r_squared DECIMAL(8,4),
    
    -- Actual vs Predicted (updated when actuals available)
    actual_value DECIMAL(14,4),
    variance_pct DECIMAL(8,4),
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_forecast_target (forecast_date, target_date),
    INDEX idx_store_metric (store_code, metric_name, target_date),
    UNIQUE KEY uk_forecast (target_date, store_code, metric_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================================================
-- 6. ALERT THRESHOLDS AND RULES TABLE
-- ====================================================================
CREATE TABLE IF NOT EXISTS bi_alert_rules (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL,
    metric_name VARCHAR(50) NOT NULL,
    store_code VARCHAR(10),  -- NULL for company-wide rules
    
    -- Threshold Configuration
    threshold_type ENUM('ABSOLUTE', 'PERCENTAGE', 'TREND') DEFAULT 'ABSOLUTE',
    warning_threshold DECIMAL(14,4),
    critical_threshold DECIMAL(14,4),
    comparison_period INT DEFAULT 1,  -- Days/weeks/months to compare
    
    -- Alert Configuration
    is_active BOOLEAN DEFAULT TRUE,
    notification_emails TEXT,
    notification_frequency ENUM('IMMEDIATE', 'DAILY', 'WEEKLY') DEFAULT 'DAILY',
    
    -- Last Alert Status
    last_triggered TIMESTAMP NULL,
    current_status ENUM('NORMAL', 'WARNING', 'CRITICAL') DEFAULT 'NORMAL',
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_active_rules (is_active, metric_name),
    UNIQUE KEY uk_rule_store (rule_name, store_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================================================
-- 7. DATA IMPORT LOG TABLE
-- ====================================================================
CREATE TABLE IF NOT EXISTS bi_import_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    import_type VARCHAR(50) NOT NULL,
    file_name VARCHAR(255),
    period_start DATE,
    period_end DATE,
    
    -- Import Statistics
    records_processed INT DEFAULT 0,
    records_imported INT DEFAULT 0,
    records_skipped INT DEFAULT 0,
    records_error INT DEFAULT 0,
    
    -- Status
    status ENUM('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED') DEFAULT 'PENDING',
    error_message TEXT,
    
    -- Timing
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    processing_time_seconds INT DEFAULT 0,
    
    -- Metadata
    imported_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_import_type (import_type, period_end),
    INDEX idx_status (status, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ====================================================================
-- Sample Alert Rules
-- ====================================================================
INSERT INTO bi_alert_rules (rule_name, metric_name, threshold_type, warning_threshold, critical_threshold, notification_emails) 
VALUES 
    ('Low Inventory Utilization', 'utilization_rate', 'PERCENTAGE', 60, 40, 'ops@company.com'),
    ('High Labor Cost Ratio', 'labor_cost_ratio', 'PERCENTAGE', 35, 45, 'cfo@company.com'),
    ('AR Aging Alert', 'ar_over_45_days_pct', 'PERCENTAGE', 25, 40, 'ar@company.com'),
    ('Revenue Decline', 'revenue_growth_pct', 'PERCENTAGE', -5, -15, 'exec@company.com')
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- Create views for common executive queries
CREATE OR REPLACE VIEW v_executive_dashboard AS
SELECT 
    e.period_ending,
    e.total_revenue,
    e.revenue_growth_pct,
    e.gross_margin_pct,
    e.labor_cost_ratio,
    e.inventory_turnover,
    e.days_sales_outstanding,
    e.best_performing_store,
    e.store_rankings
FROM bi_executive_kpis e
WHERE e.period_type = 'WEEKLY'
ORDER BY e.period_ending DESC
LIMIT 52;

CREATE OR REPLACE VIEW v_store_comparison AS
SELECT 
    sp.store_code,
    sp.period_ending,
    sp.total_revenue,
    sp.labor_cost_ratio,
    sp.revenue_per_hour,
    os.new_contracts_count,
    os.reservation_pipeline_total,
    os.ar_over_45_days_pct
FROM bi_store_performance sp
LEFT JOIN bi_operational_scorecard os 
    ON sp.store_code = os.store_code 
    AND sp.period_ending = os.week_ending
WHERE sp.period_type = 'WEEKLY'
ORDER BY sp.period_ending DESC, sp.total_revenue DESC;
