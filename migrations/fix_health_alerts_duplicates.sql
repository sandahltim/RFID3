-- Health Alerts Duplication Fix Migration
-- Date: 2025-08-28
-- Purpose: Remove duplicate health alerts and add unique constraints

-- Start transaction for safety
START TRANSACTION;

-- Create backup table of all current alerts before cleanup
CREATE TABLE IF NOT EXISTS inventory_health_alerts_backup_20250828 AS 
SELECT * FROM inventory_health_alerts;

SELECT 'Backup created with', COUNT(*), 'total records' FROM inventory_health_alerts_backup_20250828;

-- Show current duplicate statistics
SELECT 'BEFORE CLEANUP - Duplicate Statistics:' as info;
SELECT 
    alert_type,
    COUNT(*) as total_alerts,
    COUNT(DISTINCT CONCAT(COALESCE(tag_id, ''), '|', alert_type, '|', status)) as unique_combinations,
    COUNT(*) - COUNT(DISTINCT CONCAT(COALESCE(tag_id, ''), '|', alert_type, '|', status)) as duplicates
FROM inventory_health_alerts 
GROUP BY alert_type;

-- Show top duplicate items
SELECT 'Top 10 items with most duplicates:' as info;
SELECT tag_id, alert_type, status, COUNT(*) as duplicate_count 
FROM inventory_health_alerts 
WHERE tag_id IS NOT NULL
GROUP BY tag_id, alert_type, status 
HAVING COUNT(*) > 1 
ORDER BY duplicate_count DESC 
LIMIT 10;

-- CLEANUP STEP 1: Remove duplicates for individual item alerts (tag_id based)
-- Keep the most recent alert for each (tag_id, alert_type, status) combination
DELETE h1 FROM inventory_health_alerts h1
INNER JOIN inventory_health_alerts h2 
WHERE h1.tag_id = h2.tag_id 
    AND h1.alert_type = h2.alert_type 
    AND h1.status = h2.status
    AND h1.tag_id IS NOT NULL
    AND (
        h1.created_at < h2.created_at OR 
        (h1.created_at = h2.created_at AND h1.id < h2.id)
    );

-- CLEANUP STEP 2: Remove duplicates for category-based alerts
-- Keep the most recent alert for each (category, subcategory, alert_type, status) combination
DELETE h1 FROM inventory_health_alerts h1
INNER JOIN inventory_health_alerts h2 
WHERE h1.category = h2.category 
    AND h1.subcategory = h2.subcategory
    AND h1.alert_type = h2.alert_type 
    AND h1.status = h2.status
    AND h1.tag_id IS NULL  -- Only category-based alerts
    AND h2.tag_id IS NULL
    AND (
        h1.created_at < h2.created_at OR 
        (h1.created_at = h2.created_at AND h1.id < h2.id)
    );

-- Show cleanup results
SELECT 'AFTER CLEANUP - Remaining Duplicates (should be 0):' as info;
SELECT 
    alert_type,
    COUNT(*) as total_alerts,
    COUNT(DISTINCT CONCAT(COALESCE(tag_id, ''), '|', alert_type, '|', status)) as unique_combinations,
    COUNT(*) - COUNT(DISTINCT CONCAT(COALESCE(tag_id, ''), '|', alert_type, '|', status)) as duplicates
FROM inventory_health_alerts 
GROUP BY alert_type;

-- Verify no duplicates remain for tag-based alerts
SELECT 'Remaining tag-based duplicates (should be empty):' as info;
SELECT tag_id, alert_type, status, COUNT(*) as duplicate_count 
FROM inventory_health_alerts 
WHERE tag_id IS NOT NULL
GROUP BY tag_id, alert_type, status 
HAVING COUNT(*) > 1 
ORDER BY duplicate_count DESC;

-- Verify no duplicates remain for category-based alerts  
SELECT 'Remaining category-based duplicates (should be empty):' as info;
SELECT category, subcategory, alert_type, status, COUNT(*) as duplicate_count 
FROM inventory_health_alerts 
WHERE tag_id IS NULL
GROUP BY category, subcategory, alert_type, status 
HAVING COUNT(*) > 1 
ORDER BY duplicate_count DESC;

-- Add unique constraints to prevent future duplicates
-- Constraint 1: Individual item alerts (tag_id, alert_type, status)
ALTER TABLE inventory_health_alerts 
ADD CONSTRAINT uq_health_alert_tag_type_status 
UNIQUE (tag_id, alert_type, status);

-- Constraint 2: Category-based alerts (category, subcategory, alert_type, status)  
ALTER TABLE inventory_health_alerts 
ADD CONSTRAINT uq_health_alert_category_type_status 
UNIQUE (category, subcategory, alert_type, status);

-- Add additional performance indexes if they don't exist
CREATE INDEX IF NOT EXISTS ix_health_alert_tag_id_type ON inventory_health_alerts (tag_id, alert_type);
CREATE INDEX IF NOT EXISTS ix_health_alert_category_type ON inventory_health_alerts (category, alert_type);
CREATE INDEX IF NOT EXISTS ix_health_alert_status_created ON inventory_health_alerts (status, created_at);

-- Final verification
SELECT 'FINAL STATUS:' as info;
SELECT 
    COUNT(*) as total_alerts,
    COUNT(DISTINCT CONCAT(COALESCE(tag_id, ''), '|', alert_type, '|', status)) as unique_combinations,
    COUNT(*) - COUNT(DISTINCT CONCAT(COALESCE(tag_id, ''), '|', alert_type, '|', status)) as should_be_zero_duplicates
FROM inventory_health_alerts;

-- Show constraints added
SELECT 'Unique constraints added:' as info;
SHOW INDEX FROM inventory_health_alerts WHERE Key_name LIKE 'uq_health_alert%';

-- Commit the transaction
COMMIT;

SELECT 'Health alerts duplication fix completed successfully!' as status;
SELECT 'Backup table: inventory_health_alerts_backup_20250828' as backup_info;