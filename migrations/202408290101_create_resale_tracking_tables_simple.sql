-- Migration: Create Resale Tracking Tables (Simple Version)
-- Date: 2025-08-29
-- Purpose: Add tables for resale analytics and financial tracking without FK constraints initially

-- Table for tracking item financial metrics
CREATE TABLE IF NOT EXISTS item_financials (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tag_id VARCHAR(255) NOT NULL,
    acquisition_cost DECIMAL(10,2) DEFAULT 0.00,
    acquisition_date DATE,
    total_revenue_ytd DECIMAL(10,2) DEFAULT 0.00,
    maintenance_cost_ytd DECIMAL(10,2) DEFAULT 0.00,
    last_rental_revenue DECIMAL(10,2) DEFAULT 0.00,
    estimated_resale_value DECIMAL(10,2) DEFAULT 0.00,
    roi_percentage DECIMAL(5,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_tag_id (tag_id),
    INDEX idx_roi (roi_percentage),
    INDEX idx_acquisition_date (acquisition_date)
);

-- Table for resale analytics and recommendations  
CREATE TABLE IF NOT EXISTS resale_analytics (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tag_id VARCHAR(255) NOT NULL,
    time_utilization DECIMAL(5,2) DEFAULT 0.00,
    dollar_utilization DECIMAL(5,2) DEFAULT 0.00,
    days_since_last_rent INT DEFAULT 0,
    total_days_in_inventory INT DEFAULT 0,
    resale_candidate_score DECIMAL(8,2) DEFAULT 0.00,
    recommended_action ENUM('keep', 'resale', 'repair', 'dispose') DEFAULT 'keep',
    analysis_date DATE DEFAULT (CURRENT_DATE),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_tag_id (tag_id),
    INDEX idx_candidate_score (resale_candidate_score),
    INDEX idx_recommended_action (recommended_action),
    INDEX idx_analysis_date (analysis_date),
    INDEX idx_time_utilization (time_utilization),
    INDEX idx_dollar_utilization (dollar_utilization),
    UNIQUE KEY unique_tag_analysis_date (tag_id, analysis_date)
);