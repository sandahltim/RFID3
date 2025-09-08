-- Create P&L (Profit and Loss) data table for financial analytics
-- Migration: 202508290500_create_pnl_data_table.sql
-- Description: Create table to store monthly actual and projected P&L data

USE rfid_inventory;

-- Create P&L data table
CREATE TABLE IF NOT EXISTS pos_pnl (
    id INT AUTO_INCREMENT PRIMARY KEY,
    store_code VARCHAR(10) NOT NULL,
    month_year DATE NOT NULL,
    metric_type ENUM('Rental Revenue', 'Sales Revenue', 'COGS', 'Gross Profit', 'Operating Expenses', 'Net Income') NOT NULL,
    actual_amount DECIMAL(12,2) DEFAULT NULL,
    projected_amount DECIMAL(12,2) DEFAULT NULL,
    ttm_actual DECIMAL(12,2) DEFAULT NULL,
    ttm_projected DECIMAL(12,2) DEFAULT NULL,
    percentage_total_revenue DECIMAL(5,2) DEFAULT NULL,
    peg_target DECIMAL(12,2) DEFAULT NULL,
    data_source VARCHAR(50) DEFAULT 'CSV_IMPORT',
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    INDEX idx_pnl_store_date (store_code, month_year),
    INDEX idx_pnl_metric_type (metric_type),
    INDEX idx_pnl_store_metric (store_code, metric_type),
    INDEX idx_pnl_date_range (month_year),
    INDEX idx_pnl_import_date (import_date),
    
    -- Unique constraint to prevent duplicates
    UNIQUE KEY unique_store_month_metric (store_code, month_year, metric_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create store mapping reference table for P&L data
CREATE TABLE IF NOT EXISTS pos_store_mapping (
    id INT AUTO_INCREMENT PRIMARY KEY,
    store_code VARCHAR(10) NOT NULL UNIQUE,
    store_name VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default store mappings
INSERT IGNORE INTO pos_store_mapping (store_code, store_name, location) VALUES
('3607', 'Wayzata', 'Wayzata, MN'),
('6800', 'Brooklyn Park', 'Brooklyn Park, MN'),
('728', 'Elk River', 'Elk River, MN'),
('8101', 'Fridley', 'Fridley, MN'),
('000', 'Legacy/Unassigned', 'Unknown/Legacy');

-- Create P&L analytics summary view for quick access
CREATE OR REPLACE VIEW pnl_summary_view AS
SELECT 
    psm.store_name,
    pp.store_code,
    pp.metric_type,
    YEAR(pp.month_year) as year,
    MONTH(pp.month_year) as month,
    pp.actual_amount,
    pp.projected_amount,
    (pp.actual_amount - pp.projected_amount) as variance,
    CASE 
        WHEN pp.projected_amount > 0 THEN 
            ((pp.actual_amount - pp.projected_amount) / pp.projected_amount * 100)
        ELSE NULL 
    END as variance_percentage,
    pp.ttm_actual,
    pp.ttm_projected,
    pp.percentage_total_revenue,
    pp.peg_target
FROM pos_pnl pp
LEFT JOIN pos_store_mapping psm ON pp.store_code = psm.store_code
WHERE psm.active = TRUE;

-- Create index on the view for better performance
-- Note: Views don't support direct indexing, but underlying table indexes help

-- Sample data verification query
-- SELECT store_name, metric_type, COUNT(*) as record_count, 
--        MIN(month_year) as earliest_date, MAX(month_year) as latest_date,
--        SUM(actual_amount) as total_actual, SUM(projected_amount) as total_projected
-- FROM pnl_summary_view 
-- GROUP BY store_name, metric_type
-- ORDER BY store_name, metric_type;

COMMIT;