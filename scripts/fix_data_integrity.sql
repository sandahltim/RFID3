-- RFID3 Data Integrity Fix Script
-- Date: 2025-08-28
-- Purpose: Fix critical data integrity issues identified in analysis
-- BACKUP DATABASE BEFORE RUNNING THIS SCRIPT!

USE rfid_inventory;

-- ============================================================================
-- SECTION 1: CREATE STORE MAPPING TABLE
-- ============================================================================

DROP TABLE IF EXISTS store_mappings;

CREATE TABLE store_mappings (
    pos_code VARCHAR(10) PRIMARY KEY,
    db_code VARCHAR(10) NOT NULL UNIQUE,
    store_name VARCHAR(100) NOT NULL,
    region VARCHAR(50),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_db_code (db_code),
    INDEX idx_active (active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert store mappings
INSERT INTO store_mappings (pos_code, db_code, store_name, region, active) VALUES
('001', '3607', 'Wayzata', 'West', TRUE),
('002', '6800', 'Brooklyn Park', 'North', TRUE),
('003', '8101', 'Fridley', 'Central', TRUE),
('004', '728', 'Elk River', 'Northwest', TRUE);

-- ============================================================================
-- SECTION 2: ADD MISSING INDEXES FOR PERFORMANCE
-- ============================================================================

-- Check and add indexes on id_item_master
ALTER TABLE id_item_master 
ADD INDEX IF NOT EXISTS idx_tag_scan_date (tag_id, date_last_scanned),
ADD INDEX IF NOT EXISTS idx_store_status (current_store, status),
ADD INDEX IF NOT EXISTS idx_home_store (home_store),
ADD INDEX IF NOT EXISTS idx_identifier_type (identifier_type),
ADD INDEX IF NOT EXISTS idx_item_num (item_num);

-- Check and add indexes on id_transactions
ALTER TABLE id_transactions
ADD INDEX IF NOT EXISTS idx_tag_scan (tag_id, scan_date),
ADD INDEX IF NOT EXISTS idx_contract_scan (contract_number, scan_date),
ADD INDEX IF NOT EXISTS idx_scan_type (scan_type),
ADD INDEX IF NOT EXISTS idx_scan_by (scan_by);

-- Check and add indexes on item_usage_history (if table exists)
CREATE INDEX IF NOT EXISTS idx_tag_event ON item_usage_history (tag_id, event_date);
CREATE INDEX IF NOT EXISTS idx_event_type_date ON item_usage_history (event_type, event_date);

-- ============================================================================
-- SECTION 3: SYNCHRONIZE LAST SCAN DATES
-- ============================================================================

-- Update date_last_scanned to match actual last transaction
UPDATE id_item_master im
INNER JOIN (
    SELECT 
        tag_id,
        MAX(scan_date) as last_scan
    FROM id_transactions
    GROUP BY tag_id
) t ON im.tag_id = t.tag_id
SET im.date_last_scanned = t.last_scan
WHERE im.date_last_scanned IS NULL 
   OR im.date_last_scanned < t.last_scan;

-- Log the update
SELECT CONCAT('Updated ', ROW_COUNT(), ' items with correct last scan date') as update_result;

-- ============================================================================
-- SECTION 4: FIX FINANCIAL CALCULATIONS
-- ============================================================================

-- Create temporary table for turnover calculations
DROP TEMPORARY TABLE IF EXISTS temp_turnover_calc;
CREATE TEMPORARY TABLE temp_turnover_calc AS
SELECT 
    t.tag_id,
    COUNT(DISTINCT CASE 
        WHEN YEAR(t.scan_date) = YEAR(CURRENT_DATE) 
        THEN t.contract_number 
    END) as ytd_contracts,
    COUNT(DISTINCT t.contract_number) as ltd_contracts,
    COUNT(DISTINCT CASE 
        WHEN t.scan_type IN ('checkout', 'Deliver') 
        AND YEAR(t.scan_date) = YEAR(CURRENT_DATE)
        THEN t.contract_number 
    END) as ytd_rentals
FROM id_transactions t
WHERE t.scan_type IN ('checkout', 'Deliver', 'checkin', 'Pickup')
GROUP BY t.tag_id;

-- Update turnover_ytd based on actual rental transactions
UPDATE id_item_master im
INNER JOIN temp_turnover_calc tc ON im.tag_id = tc.tag_id
SET im.turnover_ytd = tc.ytd_rentals * COALESCE(im.sell_price, im.retail_price, 0)
WHERE tc.ytd_rentals > 0;

-- Update turnover_ltd 
UPDATE id_item_master im
INNER JOIN temp_turnover_calc tc ON im.tag_id = tc.tag_id
SET im.turnover_ltd = tc.ltd_contracts * COALESCE(im.sell_price, im.retail_price, 0)
WHERE tc.ltd_contracts > 0;

-- Clean up
DROP TEMPORARY TABLE IF EXISTS temp_turnover_calc;

-- ============================================================================
-- SECTION 5: CREATE DATA AUDIT LOG TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS data_audit_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id VARCHAR(255) NOT NULL,
    field_name VARCHAR(50),
    old_value TEXT,
    new_value TEXT,
    change_type ENUM('INSERT', 'UPDATE', 'DELETE') DEFAULT 'UPDATE',
    changed_by VARCHAR(100),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_audit_table_record (table_name, record_id),
    INDEX idx_audit_date (changed_at),
    INDEX idx_audit_type (change_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- SECTION 6: FIX ORPHANED RECORDS
-- ============================================================================

-- Find and log orphaned transactions
INSERT INTO data_audit_log (table_name, record_id, field_name, old_value, change_type, changed_by)
SELECT 
    'id_transactions',
    CAST(t.id as CHAR),
    'tag_id',
    t.tag_id,
    'DELETE',
    'fix_data_integrity.sql'
FROM id_transactions t
LEFT JOIN id_item_master im ON t.tag_id = im.tag_id
WHERE im.tag_id IS NULL;

-- Delete orphaned transactions (after logging)
DELETE t FROM id_transactions t
LEFT JOIN id_item_master im ON t.tag_id = im.tag_id
WHERE im.tag_id IS NULL;

SELECT CONCAT('Removed ', ROW_COUNT(), ' orphaned transactions') as cleanup_result;

-- ============================================================================
-- SECTION 7: UPDATE INVENTORY CONFIGURATION
-- ============================================================================

-- Update stale item thresholds for different categories
UPDATE inventory_config 
SET config_value = JSON_SET(
    config_value,
    '$.alert_thresholds.stale_item_days.default', 30,
    '$.alert_thresholds.stale_item_days.resale', 7,
    '$.alert_thresholds.stale_item_days.pack', 14,
    '$.alert_thresholds.stale_item_days.rental', 45,
    '$.alert_thresholds.high_usage_threshold', 0.8,
    '$.alert_thresholds.low_usage_threshold', 0.2,
    '$.alert_thresholds.quality_decline_threshold', 2
),
updated_at = CURRENT_TIMESTAMP
WHERE config_key = 'alert_thresholds';

-- ============================================================================
-- SECTION 8: CREATE INVENTORY SNAPSHOT TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS inventory_snapshots (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    snapshot_date DATE NOT NULL,
    store_code VARCHAR(10),
    total_items INT DEFAULT 0,
    items_on_rent INT DEFAULT 0,
    items_available INT DEFAULT 0,
    items_in_service INT DEFAULT 0,
    items_missing INT DEFAULT 0,
    utilization_rate DECIMAL(5,2),
    total_value DECIMAL(12,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_date_store (snapshot_date, store_code),
    INDEX idx_snapshot_date (snapshot_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- SECTION 9: POPULATE INITIAL SNAPSHOT
-- ============================================================================

INSERT INTO inventory_snapshots (
    snapshot_date, 
    store_code,
    total_items,
    items_on_rent,
    items_available,
    items_in_service,
    items_missing,
    utilization_rate,
    total_value
)
SELECT 
    CURRENT_DATE as snapshot_date,
    COALESCE(current_store, home_store, 'UNKNOWN') as store_code,
    COUNT(*) as total_items,
    SUM(CASE WHEN status IN ('On Rent', 'Delivered') THEN 1 ELSE 0 END) as items_on_rent,
    SUM(CASE WHEN status = 'Ready to Rent' THEN 1 ELSE 0 END) as items_available,
    SUM(CASE WHEN status IN ('Repair', 'Needs to be Inspected') THEN 1 ELSE 0 END) as items_in_service,
    SUM(CASE WHEN DATEDIFF(CURRENT_DATE, date_last_scanned) > 30 THEN 1 ELSE 0 END) as items_missing,
    ROUND(
        SUM(CASE WHEN status IN ('On Rent', 'Delivered') THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 
        2
    ) as utilization_rate,
    SUM(COALESCE(retail_price, sell_price, 0)) as total_value
FROM id_item_master
GROUP BY COALESCE(current_store, home_store, 'UNKNOWN')
ON DUPLICATE KEY UPDATE
    total_items = VALUES(total_items),
    items_on_rent = VALUES(items_on_rent),
    items_available = VALUES(items_available),
    items_in_service = VALUES(items_in_service),
    items_missing = VALUES(items_missing),
    utilization_rate = VALUES(utilization_rate),
    total_value = VALUES(total_value);

-- ============================================================================
-- SECTION 10: CREATE STATUS TRACKING TRIGGERS
-- ============================================================================

DELIMITER $$

-- Trigger to update item master when transaction is inserted
DROP TRIGGER IF EXISTS update_item_on_transaction$$
CREATE TRIGGER update_item_on_transaction
AFTER INSERT ON id_transactions
FOR EACH ROW
BEGIN
    -- Update last scan date and status
    UPDATE id_item_master 
    SET 
        date_last_scanned = NEW.scan_date,
        status = CASE 
            WHEN NEW.scan_type IN ('checkout', 'Deliver') THEN 'On Rent'
            WHEN NEW.scan_type IN ('checkin', 'Pickup') THEN 'Ready to Rent'
            WHEN NEW.scan_type = 'Repair' THEN 'Repair'
            ELSE status
        END,
        last_contract_num = CASE 
            WHEN NEW.contract_number IS NOT NULL THEN NEW.contract_number 
            ELSE last_contract_num 
        END,
        last_scanned_by = NEW.scan_by,
        date_updated = CURRENT_TIMESTAMP
    WHERE tag_id = NEW.tag_id;
    
    -- Log significant changes
    IF NEW.scan_type IN ('checkout', 'checkin', 'Deliver', 'Pickup') THEN
        INSERT INTO data_audit_log (table_name, record_id, field_name, new_value, change_type, changed_by)
        VALUES ('id_item_master', NEW.tag_id, 'status_change', NEW.scan_type, 'UPDATE', NEW.scan_by);
    END IF;
END$$

DELIMITER ;

-- ============================================================================
-- SECTION 11: SUMMARY REPORT
-- ============================================================================

SELECT 'Data Integrity Fixes Applied Successfully' as status;

-- Show current data quality metrics
SELECT 
    'Data Quality Metrics' as metric_type,
    COUNT(*) as total_items,
    SUM(CASE WHEN date_last_scanned IS NOT NULL THEN 1 ELSE 0 END) as items_with_scan_date,
    SUM(CASE WHEN sell_price IS NOT NULL THEN 1 ELSE 0 END) as items_with_price,
    SUM(CASE WHEN turnover_ytd IS NOT NULL AND turnover_ytd > 0 THEN 1 ELSE 0 END) as items_with_turnover,
    SUM(CASE WHEN home_store IS NOT NULL THEN 1 ELSE 0 END) as items_with_home_store,
    ROUND(
        (SUM(CASE WHEN date_last_scanned IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*)),
        2
    ) as scan_date_completeness_pct,
    ROUND(
        (SUM(CASE WHEN sell_price IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*)),
        2
    ) as price_completeness_pct
FROM id_item_master;

-- Show store distribution
SELECT 
    'Store Distribution' as metric_type,
    COALESCE(current_store, home_store, 'UNKNOWN') as store,
    COUNT(*) as item_count,
    SUM(CASE WHEN status IN ('On Rent', 'Delivered') THEN 1 ELSE 0 END) as on_rent,
    SUM(CASE WHEN status = 'Ready to Rent' THEN 1 ELSE 0 END) as available
FROM id_item_master
GROUP BY COALESCE(current_store, home_store, 'UNKNOWN');

-- End of script
SELECT 'Script execution completed successfully' as final_status;