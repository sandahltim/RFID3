-- Migration: Create Resale Tracking Tables
-- Date: 2025-08-29
-- Purpose: Add tables for resale analytics and financial tracking

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
    INDEX idx_acquisition_date (acquisition_date),
    CONSTRAINT fk_item_financials_tag_id 
        FOREIGN KEY (tag_id) REFERENCES id_item_master(tag_id) 
        ON DELETE CASCADE ON UPDATE CASCADE
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
    UNIQUE KEY unique_tag_analysis_date (tag_id, analysis_date),
    CONSTRAINT fk_resale_analytics_tag_id 
        FOREIGN KEY (tag_id) REFERENCES id_item_master(tag_id) 
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- Insert initial data for existing items with basic calculations
INSERT IGNORE INTO item_financials (tag_id, acquisition_cost, total_revenue_ytd)
SELECT 
    tag_id,
    CASE 
        -- Estimate acquisition cost based on rental class and type
        WHEN rental_class_num LIKE '%TENT%' THEN 500.00
        WHEN rental_class_num LIKE '%CHAIR%' THEN 25.00  
        WHEN rental_class_num LIKE '%TABLE%' THEN 150.00
        WHEN rental_class_num LIKE '%LINEN%' THEN 30.00
        ELSE 100.00
    END as estimated_acquisition_cost,
    COALESCE(turnover_ytd, 0.00) as revenue_ytd
FROM id_item_master 
WHERE tag_id IS NOT NULL;

-- Insert initial resale analytics data
INSERT IGNORE INTO resale_analytics (tag_id, total_days_in_inventory)
SELECT 
    tag_id,
    COALESCE(DATEDIFF(CURRENT_DATE, date_created), 0) as days_in_inventory
FROM id_item_master 
WHERE tag_id IS NOT NULL;

-- Update days since last rent
UPDATE resale_analytics ra
SET days_since_last_rent = (
    SELECT COALESCE(
        DATEDIFF(
            CURRENT_DATE, 
            MAX(t.scan_date)
        ), 
        DATEDIFF(CURRENT_DATE, '2020-01-01')
    )
    FROM id_transactions t 
    WHERE t.tag_id = ra.tag_id 
    AND t.status IN ('On Rent', 'Delivered', 'Out to Customer')
)
WHERE analysis_date = CURRENT_DATE;