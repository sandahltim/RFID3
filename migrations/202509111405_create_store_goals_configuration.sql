-- Store Goals Configuration Database Migration
-- Version: 2025-09-11 - Store-Specific Goals Management System
-- Description: Create comprehensive store goals configuration table

-- Store Goals Configuration table
CREATE TABLE IF NOT EXISTS store_goals_configuration (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Company-wide goals (JSON for flexibility)
    company_goals JSON DEFAULT NULL COMMENT 'Company-wide goal targets',
    
    -- Store-specific revenue goals (JSON for flexibility)
    store_revenue_goals JSON DEFAULT NULL COMMENT 'Store-specific revenue targets by store code',
    
    -- Store-specific labor goals (JSON for flexibility)  
    store_labor_goals JSON DEFAULT NULL COMMENT 'Store-specific labor targets by store code',
    
    -- Store-specific delivery goals (JSON for flexibility)
    store_delivery_goals JSON DEFAULT NULL COMMENT 'Store-specific delivery targets by store code',
    
    -- Additional goals for future extensibility
    additional_goals JSON DEFAULT NULL COMMENT 'Additional goal categories for future expansion',
    
    -- Metadata
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(50) DEFAULT 'system',
    notes TEXT DEFAULT NULL,
    
    -- Indexes for performance
    INDEX idx_active (is_active, updated_at),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='Store-specific goals configuration with extensible JSON structure';

-- Insert default configuration if none exists
INSERT IGNORE INTO store_goals_configuration (
    company_goals,
    store_revenue_goals,
    store_labor_goals,
    store_delivery_goals,
    created_by,
    notes
) VALUES (
    JSON_OBJECT(
        'monthly_revenue_target', 500000,
        'ar_aging_threshold', 15.0,
        'deliveries_goal', 50,
        'wage_ratio_goal', 25.0,
        'revenue_per_hour_goal', 150
    ),
    JSON_OBJECT(
        '3607', JSON_OBJECT('reservation_goal', 50000, 'contract_goal', 25),
        '6800', JSON_OBJECT('reservation_goal', 75000, 'contract_goal', 35),
        '728', JSON_OBJECT('reservation_goal', 40000, 'contract_goal', 20),
        '8101', JSON_OBJECT('reservation_goal', 60000, 'contract_goal', 30)
    ),
    JSON_OBJECT(
        '3607', JSON_OBJECT('labor_percentage', 22.0, 'revenue_per_hour', 175),
        '6800', JSON_OBJECT('labor_percentage', 25.0, 'revenue_per_hour', 145),
        '728', JSON_OBJECT('labor_percentage', 28.0, 'revenue_per_hour', 120),
        '8101', JSON_OBJECT('labor_percentage', 26.0, 'revenue_per_hour', 160)
    ),
    JSON_OBJECT(
        '3607', JSON_OBJECT('weekly_deliveries', 65, 'avg_revenue_per_delivery', 450),
        '6800', JSON_OBJECT('weekly_deliveries', 45, 'avg_revenue_per_delivery', 380),
        '728', JSON_OBJECT('weekly_deliveries', 25, 'avg_revenue_per_delivery', 320),
        '8101', JSON_OBJECT('weekly_deliveries', 35, 'avg_revenue_per_delivery', 400)
    ),
    'migration',
    'Default store goals configuration created during migration'
);

-- Add SQL comments for documentation
ALTER TABLE store_goals_configuration COMMENT = 'Extensible store goals configuration system supporting dynamic goal categories';