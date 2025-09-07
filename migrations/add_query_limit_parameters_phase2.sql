-- Phase 2 Migration: Add Query Limit Parameters to ExecutiveDashboardConfiguration
-- Date: 2025-09-07
-- Purpose: Convert hardcoded LIMIT clauses to configurable parameters

-- Add query limit parameters to executive_dashboard_configuration table
ALTER TABLE executive_dashboard_configuration
ADD COLUMN executive_summary_revenue_weeks INT DEFAULT 3 COMMENT 'Weeks for executive summary revenue (LIMIT 3)',
ADD COLUMN financial_kpis_current_revenue_weeks INT DEFAULT 3 COMMENT 'Weeks for current revenue in financial KPIs',
ADD COLUMN financial_kpis_debug_weeks INT DEFAULT 3 COMMENT 'Debug query weeks for revenue calculation',
ADD COLUMN location_kpis_revenue_weeks INT DEFAULT 3 COMMENT 'Location-specific revenue weeks',
ADD COLUMN location_kpis_payroll_weeks INT DEFAULT 3 COMMENT 'Location-specific payroll weeks',
ADD COLUMN location_comparison_revenue_weeks INT DEFAULT 3 COMMENT 'Location comparison revenue weeks',
ADD COLUMN insights_profit_margin_weeks INT DEFAULT 3 COMMENT 'Profit margin calculation weeks',
ADD COLUMN insights_trend_analysis_weeks INT DEFAULT 12 COMMENT 'Trend analysis weeks (LIMIT 12)',
ADD COLUMN forecasts_historical_weeks INT DEFAULT 24 COMMENT 'Financial forecasts historical weeks (LIMIT 24)',
ADD COLUMN forecasting_historical_weeks INT DEFAULT 52 COMMENT 'Predictive forecasting weeks (52 weeks/.limit(52))';

-- Update existing default configuration with new parameters (if record exists)
UPDATE executive_dashboard_configuration 
SET 
    executive_summary_revenue_weeks = 3,
    financial_kpis_current_revenue_weeks = 3,
    financial_kpis_debug_weeks = 3,
    location_kpis_revenue_weeks = 3,
    location_kpis_payroll_weeks = 3,
    location_comparison_revenue_weeks = 3,
    insights_profit_margin_weeks = 3,
    insights_trend_analysis_weeks = 12,
    forecasts_historical_weeks = 24,
    forecasting_historical_weeks = 52,
    updated_at = NOW()
WHERE user_id = 'default_user' AND config_name = 'default';

-- Insert default configuration if it doesn't exist
INSERT IGNORE INTO executive_dashboard_configuration (
    user_id, config_name,
    executive_summary_revenue_weeks,
    financial_kpis_current_revenue_weeks,
    financial_kpis_debug_weeks,
    location_kpis_revenue_weeks,
    location_kpis_payroll_weeks,
    location_comparison_revenue_weeks,
    insights_profit_margin_weeks,
    insights_trend_analysis_weeks,
    forecasts_historical_weeks,
    forecasting_historical_weeks,
    created_at,
    updated_at
) VALUES (
    'default_user', 'default',
    3, 3, 3, 3, 3, 3, 3, 12, 24, 52,
    NOW(), NOW()
);

-- Verify the migration
SELECT 
    user_id,
    config_name,
    executive_summary_revenue_weeks,
    financial_kpis_current_revenue_weeks,
    insights_trend_analysis_weeks,
    forecasts_historical_weeks,
    forecasting_historical_weeks,
    updated_at
FROM executive_dashboard_configuration
WHERE user_id = 'default_user' AND config_name = 'default';