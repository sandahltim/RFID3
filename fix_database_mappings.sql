-- Fix Database Mappings and Relations for RFID3 Analytics
-- Author: Database Analysis Agent
-- Date: 2025-08-28

-- 1. Create missing rental class mappings for orphaned items
INSERT INTO user_rental_class_mappings (rental_class_id, category, subcategory, short_common_name, created_at, updated_at)
SELECT DISTINCT 
    i.rental_class_num,
    CASE 
        WHEN i.rental_class_num = '63099' THEN 'Linens'
        WHEN i.rental_class_num = '728' THEN 'Tables'
        WHEN i.rental_class_num LIKE '724%' THEN 'Linens'
        WHEN i.rental_class_num LIKE '000%' THEN 'Miscellaneous'
        WHEN i.rental_class_num LIKE '655%' THEN 'Equipment'
        ELSE 'Unassigned'
    END as category,
    CASE 
        WHEN i.rental_class_num = '63099' THEN 'General Linens'
        WHEN i.rental_class_num = '728' THEN 'Round Tables'
        WHEN i.rental_class_num LIKE '724%' THEN 'Specialty Linens'
        WHEN i.rental_class_num LIKE '000%' THEN 'Legacy Items'
        WHEN i.rental_class_num LIKE '655%' THEN 'General Equipment'
        ELSE 'Unknown'
    END as subcategory,
    CONCAT('Class ', i.rental_class_num) as short_common_name,
    NOW() as created_at,
    NOW() as updated_at
FROM id_item_master i 
LEFT JOIN user_rental_class_mappings m ON i.rental_class_num = m.rental_class_id 
WHERE i.rental_class_num IS NOT NULL 
AND i.rental_class_num != ''
AND m.rental_class_id IS NULL;

-- 2. Add proper indexes for analytics performance
CREATE INDEX IF NOT EXISTS idx_item_master_status_store ON id_item_master(status, current_store);
CREATE INDEX IF NOT EXISTS idx_item_master_rental_class ON id_item_master(rental_class_num);
CREATE INDEX IF NOT EXISTS idx_item_master_turnover ON id_item_master(turnover_ytd);
CREATE INDEX IF NOT EXISTS idx_transactions_scan_date ON id_transactions(scan_date);
CREATE INDEX IF NOT EXISTS idx_transactions_tag_id_date ON id_transactions(tag_id, scan_date);

-- 3. Add foreign key constraints (with error handling)
-- Note: Cannot add FK constraint due to existing orphaned data, so we create a view instead

-- 4. Create corrected utilization calculation view
CREATE OR REPLACE VIEW analytics_utilization_summary AS
SELECT 
    COALESCE(i.current_store, i.home_store, 'Unknown') as store_code,
    COUNT(*) as total_items,
    COUNT(CASE WHEN i.status IN ('On Rent', 'Delivered', 'Out to Customer') THEN 1 END) as items_on_rent,
    COUNT(CASE WHEN i.status = 'Ready to Rent' THEN 1 END) as items_available,
    COUNT(CASE WHEN i.status IN ('Repair', 'Needs to be Inspected', 'Wash', 'Lost') THEN 1 END) as items_unavailable,
    ROUND(
        (COUNT(CASE WHEN i.status IN ('On Rent', 'Delivered', 'Out to Customer') THEN 1 END) / 
         GREATEST(COUNT(*), 1)) * 100, 2
    ) as utilization_rate,
    SUM(COALESCE(i.sell_price, 0)) as total_inventory_value,
    SUM(COALESCE(i.turnover_ytd, 0)) as total_revenue
FROM id_item_master i
GROUP BY COALESCE(i.current_store, i.home_store, 'Unknown');

-- 5. Create enhanced category analytics view
CREATE OR REPLACE VIEW analytics_category_performance AS
SELECT 
    m.category,
    m.subcategory,
    COUNT(i.tag_id) as item_count,
    COUNT(CASE WHEN i.status IN ('On Rent', 'Delivered', 'Out to Customer') THEN 1 END) as items_on_rent,
    ROUND(
        (COUNT(CASE WHEN i.status IN ('On Rent', 'Delivered', 'Out to Customer') THEN 1 END) / 
         GREATEST(COUNT(i.tag_id), 1)) * 100, 2
    ) as utilization_rate,
    AVG(COALESCE(i.sell_price, 0)) as avg_sell_price,
    SUM(COALESCE(i.turnover_ytd, 0)) as total_revenue,
    CASE 
        WHEN COUNT(i.tag_id) = 0 THEN 0
        ELSE ROUND((SUM(COALESCE(i.turnover_ytd, 0)) / SUM(COALESCE(i.sell_price, 1))) * 100, 2)
    END as roi_percentage
FROM user_rental_class_mappings m
LEFT JOIN id_item_master i ON m.rental_class_id = i.rental_class_num
WHERE i.tag_id IS NOT NULL
GROUP BY m.category, m.subcategory
HAVING item_count > 0
ORDER BY roi_percentage DESC;

-- 6. Fix transaction correlation issues
-- Create index for better transaction lookup performance
CREATE INDEX IF NOT EXISTS idx_transactions_tag_scan ON id_transactions(tag_id, scan_date DESC);

-- 7. Create analytics summary table for better performance
CREATE TABLE IF NOT EXISTS analytics_cache (
    id INT AUTO_INCREMENT PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(12,2),
    store_code VARCHAR(20),
    calculation_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_metric_store_date (metric_name, store_code, calculation_date)
);

-- 8. Verify data integrity after fixes
SELECT 
    'Total Items' as metric,
    COUNT(*) as value 
FROM id_item_master
UNION ALL
SELECT 
    'Items with Mappings' as metric,
    COUNT(*) as value
FROM id_item_master i 
INNER JOIN user_rental_class_mappings m ON i.rental_class_num = m.rental_class_id
UNION ALL
SELECT 
    'Orphaned Items After Fix' as metric,
    COUNT(*) as value
FROM id_item_master i 
LEFT JOIN user_rental_class_mappings m ON i.rental_class_num = m.rental_class_id 
WHERE i.rental_class_num IS NOT NULL 
AND i.rental_class_num != ''
AND m.rental_class_id IS NULL;