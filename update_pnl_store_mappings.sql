-- Update P&L Store Mappings to Align with Centralized Configuration
-- This script updates the pos_store_mapping table to match the centralized stores.py config

USE rfid_inventory;

-- Update store mappings to match centralized configuration
INSERT INTO pos_store_mapping (store_code, store_name, location, active) VALUES
('3607', 'Wayzata', 'Wayzata, MN', TRUE),
('6800', 'Brooklyn Park', 'Brooklyn Park, MN', TRUE), 
('728', 'Elk River', 'Elk River, MN', TRUE),
('8101', 'Fridley', 'Fridley, MN', TRUE),
('000', 'Legacy/Unassigned', 'Multiple Locations', FALSE)
ON DUPLICATE KEY UPDATE
    store_name = VALUES(store_name),
    location = VALUES(location),
    active = VALUES(active),
    updated_at = CURRENT_TIMESTAMP;

-- Add additional columns to pos_pnl table if they don't exist
ALTER TABLE pos_pnl 
ADD COLUMN IF NOT EXISTS pos_code VARCHAR(10) DEFAULT NULL COMMENT 'POS system code (001, 002, 003, 004)',
ADD COLUMN IF NOT EXISTS business_type VARCHAR(100) DEFAULT NULL COMMENT 'Store business type',
ADD COLUMN IF NOT EXISTS manager VARCHAR(50) DEFAULT NULL COMMENT 'Store manager',
ADD INDEX IF NOT EXISTS idx_pnl_pos_code (pos_code);

-- Update pos_store_mapping with additional centralized config data
ALTER TABLE pos_store_mapping
ADD COLUMN IF NOT EXISTS pos_code VARCHAR(10) DEFAULT NULL COMMENT 'POS system code',
ADD COLUMN IF NOT EXISTS business_type VARCHAR(100) DEFAULT NULL COMMENT 'Store business type',
ADD COLUMN IF NOT EXISTS manager VARCHAR(50) DEFAULT NULL COMMENT 'Store manager',
ADD COLUMN IF NOT EXISTS opened_date DATE DEFAULT NULL COMMENT 'Store opening date',
ADD COLUMN IF NOT EXISTS emoji VARCHAR(10) DEFAULT NULL COMMENT 'Store emoji';

-- Update store mapping with centralized configuration data
UPDATE pos_store_mapping SET
    pos_code = '001',
    business_type = '90% DIY/10% Events',
    manager = 'TYLER',
    opened_date = '2008-01-01',
    emoji = '🏬'
WHERE store_code = '3607';

UPDATE pos_store_mapping SET
    pos_code = '002',
    business_type = '100% Construction',
    manager = 'ZACK',
    opened_date = '2022-01-01',
    emoji = '🏪'
WHERE store_code = '6800';

UPDATE pos_store_mapping SET
    pos_code = '004',
    business_type = '90% DIY/10% Events',
    manager = 'BRUCE',
    opened_date = '2024-01-01',
    emoji = '🏭'
WHERE store_code = '728';

UPDATE pos_store_mapping SET
    pos_code = '003',
    business_type = '100% Events (Broadway Tent & Event)',
    manager = 'TIM',
    opened_date = '2022-01-01',
    emoji = '🏢'
WHERE store_code = '8101';

UPDATE pos_store_mapping SET
    pos_code = '000',
    business_type = 'Mixed/Historical Data',
    manager = 'SYSTEM',
    opened_date = '2008-01-01',
    emoji = '❓'
WHERE store_code = '000';

-- Create enhanced view for P&L analytics with centralized store data
CREATE OR REPLACE VIEW pnl_analytics_view AS
SELECT 
    pp.store_code,
    psm.store_name,
    psm.location,
    psm.pos_code,
    psm.business_type,
    psm.manager,
    psm.emoji,
    pp.metric_type,
    pp.month_year,
    YEAR(pp.month_year) as year,
    MONTH(pp.month_year) as month,
    MONTHNAME(pp.month_year) as month_name,
    pp.actual_amount,
    pp.projected_amount,
    (pp.actual_amount - COALESCE(pp.projected_amount, 0)) as variance,
    CASE 
        WHEN pp.projected_amount > 0 THEN 
            ((pp.actual_amount - pp.projected_amount) / pp.projected_amount * 100)
        ELSE NULL 
    END as variance_percentage,
    pp.percentage_total_revenue,
    pp.ttm_actual,
    pp.ttm_projected,
    pp.data_source,
    pp.import_date,
    pp.updated_at
FROM pos_pnl pp
LEFT JOIN pos_store_mapping psm ON pp.store_code = psm.store_code
WHERE psm.active = TRUE
ORDER BY pp.store_code, pp.metric_type, pp.month_year;

-- Verify the correlation between P&L data and centralized store config
SELECT 
    'P&L Store Correlation Check' as report_type,
    COUNT(DISTINCT pp.store_code) as stores_in_pnl,
    COUNT(DISTINCT psm.store_code) as stores_in_mapping,
    COUNT(DISTINCT CASE WHEN psm.store_code IS NOT NULL THEN pp.store_code END) as properly_correlated
FROM pos_pnl pp
LEFT JOIN pos_store_mapping psm ON pp.store_code = psm.store_code;

-- Show sample data from enhanced view
SELECT * FROM pnl_analytics_view LIMIT 10;

COMMIT;
