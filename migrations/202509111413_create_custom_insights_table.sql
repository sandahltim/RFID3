-- Custom Insights Database Migration
-- Version: 2025-09-11 - User-submitted business insights tracking
-- Description: Create table for storing custom business insights from executive dashboard

-- Custom Insights table
CREATE TABLE IF NOT EXISTS custom_insights (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Insight details
    date DATE NOT NULL COMMENT 'Date when the event/insight occurred',
    event_type VARCHAR(50) NOT NULL COMMENT 'Type of event: weather, local_event, economic, operational, marketing, other',
    description TEXT NOT NULL COMMENT 'Detailed description of the insight or event',
    impact_category VARCHAR(50) NOT NULL COMMENT 'Category of impact: revenue, operations, customer_behavior, etc.',
    impact_magnitude VARCHAR(20) DEFAULT NULL COMMENT 'Magnitude of impact: low, medium, high, critical',
    store_code VARCHAR(10) DEFAULT NULL COMMENT 'Specific store affected, null for all stores',
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Indexes for performance
    INDEX idx_insight_date (date),
    INDEX idx_insight_type (event_type),
    INDEX idx_insight_store (store_code),
    INDEX idx_insight_active (is_active, created_at),
    INDEX idx_insight_impact (impact_category, impact_magnitude)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='User-submitted custom business insights and external factors tracking';

-- Add table comment for documentation
ALTER TABLE custom_insights COMMENT = 'Stores user-submitted business insights for correlation analysis and business intelligence';