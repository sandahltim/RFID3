-- Migration: Add Dual-Mode Timeframe Support to Executive Dashboard
-- Version: 2025-09-08-v1
-- Purpose: Extend ExecutiveDashboardConfiguration for period view vs average view modes

-- Add new columns to executive_dashboard_configuration for dual-mode support
ALTER TABLE executive_dashboard_configuration ADD COLUMN IF NOT EXISTS
    -- Display Mode Configuration
    available_periods JSON DEFAULT '["1", "3", "8", "12", "16", "26", "52"]' COMMENT 'Available period options for user selection',
    default_period_weeks INT DEFAULT 3 COMMENT 'Default period when dashboard loads',
    max_period_weeks INT DEFAULT 52 COMMENT 'Maximum allowed period selection',
    min_period_weeks INT DEFAULT 1 COMMENT 'Minimum allowed period selection',
    
    -- View Mode Configuration  
    default_view_mode ENUM('average', 'period') DEFAULT 'average' COMMENT 'Default: average=rolling avg, period=show individual weeks',
    default_store VARCHAR(10) DEFAULT 'all' COMMENT 'Default store selection: all, 3607, 6800, 728, 8101',
    
    -- Display Options
    show_custom_period_input BOOLEAN DEFAULT TRUE COMMENT 'Allow users to enter custom period length',
    show_comparison_mode BOOLEAN DEFAULT TRUE COMMENT 'Enable side-by-side store comparison',
    auto_refresh_interval_seconds INT DEFAULT 300 COMMENT 'Auto-refresh interval in seconds (300=5min)',
    
    -- Chart Configuration
    max_data_points_per_chart INT DEFAULT 26 COMMENT 'Maximum data points to display on charts',
    show_trend_lines BOOLEAN DEFAULT TRUE COMMENT 'Display trend lines on charts',
    show_data_labels BOOLEAN DEFAULT TRUE COMMENT 'Show data labels on chart points',
    chart_animation_enabled BOOLEAN DEFAULT TRUE COMMENT 'Enable chart animations and transitions',
    
    -- Store Configuration
    available_stores JSON DEFAULT '["all", "3607", "6800", "728", "8101"]' COMMENT 'Available stores for selection',
    store_display_names JSON DEFAULT '{"all": "All Locations", "3607": "Wayzata", "6800": "Brooklyn Park", "728": "Elk River", "8101": "Fridley"}' COMMENT 'Display names for store selector',
    
    -- UI Configuration
    show_period_labels BOOLEAN DEFAULT TRUE COMMENT 'Show period labels on charts and cards',
    compact_mode_enabled BOOLEAN DEFAULT FALSE COMMENT 'Enable compact display mode',
    show_tooltips BOOLEAN DEFAULT TRUE COMMENT 'Show interactive tooltips on hover';

-- Create user preferences table for storing individual user selections
CREATE TABLE IF NOT EXISTS user_dashboard_preferences (
    user_id VARCHAR(50) PRIMARY KEY,
    preferred_store VARCHAR(10) DEFAULT 'all' COMMENT 'Users last selected store',
    preferred_period INT DEFAULT 3 COMMENT 'Users preferred period length in weeks',  
    preferred_mode ENUM('average','period') DEFAULT 'average' COMMENT 'Users preferred view mode',
    last_custom_period INT NULL COMMENT 'Last custom period entered by user',
    auto_refresh_enabled BOOLEAN DEFAULT TRUE COMMENT 'User preference for auto-refresh',
    last_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_last_used (user_id, last_used_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default user preferences 
INSERT INTO user_dashboard_preferences (user_id) VALUES ('default_user')
ON DUPLICATE KEY UPDATE last_used_at = CURRENT_TIMESTAMP;

-- Update existing configuration with new defaults
UPDATE executive_dashboard_configuration 
SET 
    available_periods = '["1", "3", "8", "12", "16", "26", "52"]',
    default_period_weeks = 3,
    default_view_mode = 'average',
    available_stores = '["all", "3607", "6800", "728", "8101"]',
    store_display_names = '{"all": "All Locations", "3607": "Wayzata", "6800": "Brooklyn Park", "728": "Elk River", "8101": "Fridley"}',
    updated_at = CURRENT_TIMESTAMP
WHERE user_id = 'default_user' AND config_name = 'default';

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_user_prefs_lookup ON user_dashboard_preferences (user_id, preferred_store, preferred_mode);