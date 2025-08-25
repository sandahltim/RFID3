-- Migration: Create Inventory & Analytics tracking tables
-- Date: 2025-08-25
-- Purpose: Add comprehensive item usage history and health monitoring for inventory analytics

USE rfid_inventory;

-- Table for tracking comprehensive item lifecycle events
CREATE TABLE IF NOT EXISTS item_usage_history (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tag_id VARCHAR(255) NOT NULL,
    event_type ENUM('rental', 'return', 'service', 'status_change', 'location_change', 'quality_change') NOT NULL,
    contract_number VARCHAR(255) NULL,
    event_date DATETIME NOT NULL,
    duration_days INT NULL COMMENT 'For rentals: days on rent',
    previous_status VARCHAR(50) NULL,
    new_status VARCHAR(50) NULL,
    previous_location VARCHAR(255) NULL,
    new_location VARCHAR(255) NULL,
    previous_quality VARCHAR(50) NULL,
    new_quality VARCHAR(50) NULL,
    utilization_score DECIMAL(5,2) NULL COMMENT 'Algorithm-calculated usage intensity 0-100',
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_tag_date (tag_id, event_date),
    INDEX idx_contract (contract_number),
    INDEX idx_event_type (event_type),
    INDEX idx_event_date (event_date),
    FOREIGN KEY (tag_id) REFERENCES id_item_master(tag_id) ON DELETE CASCADE
) COMMENT 'Comprehensive tracking of item lifecycle events for analytics';

-- Table for inventory health monitoring and alerts
CREATE TABLE IF NOT EXISTS inventory_health_alerts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tag_id VARCHAR(255) NULL,
    rental_class_id VARCHAR(255) NULL,
    common_name VARCHAR(255) NULL,
    category VARCHAR(100) NULL,
    subcategory VARCHAR(100) NULL,
    alert_type ENUM('stale_item', 'high_usage', 'low_usage', 'missing', 'quality_decline', 'resale_restock', 'pack_status_review') NOT NULL,
    severity ENUM('low', 'medium', 'high', 'critical') NOT NULL,
    days_since_last_scan INT NULL,
    last_scan_date DATETIME NULL,
    suggested_action TEXT NULL,
    status ENUM('active', 'acknowledged', 'resolved', 'dismissed') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at DATETIME NULL,
    acknowledged_by VARCHAR(255) NULL,
    resolved_at DATETIME NULL,
    resolved_by VARCHAR(255) NULL,
    
    INDEX idx_tag_id (tag_id),
    INDEX idx_rental_class (rental_class_id),
    INDEX idx_alert_type (alert_type),
    INDEX idx_severity (severity),
    INDEX idx_status (status),
    INDEX idx_category (category, subcategory),
    INDEX idx_created_date (created_at)
) COMMENT 'Health monitoring alerts for proactive inventory management';

-- Table for inventory analytics configuration
CREATE TABLE IF NOT EXISTS inventory_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value JSON NOT NULL,
    description TEXT NULL,
    category VARCHAR(50) NULL COMMENT 'Group configs by category for easier management',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_category (category),
    INDEX idx_key (config_key)
) COMMENT 'Configuration settings for inventory analytics and alerting';

-- Table for aggregated inventory metrics (for performance)
CREATE TABLE IF NOT EXISTS inventory_metrics_daily (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    metric_date DATE NOT NULL,
    rental_class_id VARCHAR(255) NULL,
    category VARCHAR(100) NULL,
    subcategory VARCHAR(100) NULL,
    total_items INT DEFAULT 0,
    items_on_rent INT DEFAULT 0,
    items_available INT DEFAULT 0,
    items_in_service INT DEFAULT 0,
    items_missing INT DEFAULT 0,
    utilization_rate DECIMAL(5,2) NULL COMMENT 'Percentage of items actively used',
    avg_rental_duration DECIMAL(8,2) NULL COMMENT 'Average days on rent',
    revenue_potential DECIMAL(10,2) NULL COMMENT 'Estimated daily revenue potential',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_date_rental_class (metric_date, rental_class_id),
    INDEX idx_date (metric_date),
    INDEX idx_category (category, subcategory),
    INDEX idx_rental_class (rental_class_id)
) COMMENT 'Daily aggregated metrics for performance optimization';

-- Insert default configuration values
INSERT INTO inventory_config (config_key, config_value, description, category) VALUES
('alert_thresholds', JSON_OBJECT(
    'stale_item_days', JSON_OBJECT(
        'default', 30,
        'resale', 7,
        'pack', 14
    ),
    'high_usage_threshold', 0.8,
    'low_usage_threshold', 0.2,
    'quality_decline_threshold', 2
), 'Threshold settings for generating inventory alerts', 'alerting'),

('business_rules', JSON_OBJECT(
    'resale_categories', JSON_ARRAY('Resale'),
    'pack_bin_locations', JSON_ARRAY('pack'),
    'rental_statuses', JSON_ARRAY('On Rent', 'Delivered'),
    'available_statuses', JSON_ARRAY('Ready to Rent'),
    'service_statuses', JSON_ARRAY('Repair', 'Needs to be Inspected')
), 'Business rule definitions for inventory categorization', 'business'),

('dashboard_settings', JSON_OBJECT(
    'default_date_range', 30,
    'critical_alert_limit', 50,
    'refresh_interval_minutes', 15,
    'show_resolved_alerts', false
), 'Dashboard display and behavior settings', 'ui')

ON DUPLICATE KEY UPDATE 
config_value = VALUES(config_value),
updated_at = CURRENT_TIMESTAMP;

-- Create indexes on existing tables for better analytics performance
ALTER TABLE id_item_master 
ADD INDEX IF NOT EXISTS idx_analytics_status_date (status, date_last_scanned),
ADD INDEX IF NOT EXISTS idx_analytics_bin_location (bin_location),
ADD INDEX IF NOT EXISTS idx_analytics_rental_class (rental_class_num);

ALTER TABLE id_transactions
ADD INDEX IF NOT EXISTS idx_analytics_scan_type_date (scan_type, scan_date),
ADD INDEX IF NOT EXISTS idx_analytics_contract_date (contract_number, scan_date);

-- Log the migration
INSERT INTO migration_log (script_name, executed_at, description) 
VALUES ('create_inventory_analytics_tables.sql', NOW(), 'Created comprehensive inventory analytics and health monitoring system')
ON DUPLICATE KEY UPDATE executed_at = NOW();

SELECT 'Inventory Analytics tables created successfully' AS result;