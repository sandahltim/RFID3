-- RFID3 Database Optimization Scripts
-- Generated: August 29, 2025
-- Purpose: Implement critical database improvements and data quality fixes

-- ============================================================================
-- SECTION 1: DATA QUALITY FIXES
-- ============================================================================

-- 1.1 Fix Missing Store Locations Based on Transaction History
UPDATE id_item_master im
INNER JOIN (
    SELECT 
        tag_id,
        SUBSTRING_INDEX(GROUP_CONCAT(scan_by ORDER BY scan_date DESC), ',', 1) as last_scanner
    FROM id_transactions
    WHERE scan_date > DATE_SUB(NOW(), INTERVAL 90 DAY)
    GROUP BY tag_id
) t ON im.tag_id = t.tag_id
SET 
    im.home_store = CASE 
        WHEN im.home_store IS NULL THEN '6800'  -- Default store
        ELSE im.home_store 
    END,
    im.current_store = CASE 
        WHEN im.current_store IS NULL THEN '6800'  -- Default store
        ELSE im.current_store 
    END
WHERE im.home_store IS NULL OR im.current_store IS NULL;

-- 1.2 Populate Missing Rental Class Mappings
INSERT IGNORE INTO rental_class_mappings (rental_class_id, category, subcategory, short_common_name)
SELECT DISTINCT 
    rental_class_num as rental_class_id,
    CASE 
        WHEN common_name LIKE '%Tent%' THEN 'Tents'
        WHEN common_name LIKE '%Table%' THEN 'Tables'
        WHEN common_name LIKE '%Chair%' THEN 'Chairs'
        WHEN common_name LIKE '%Linen%' THEN 'Linens'
        WHEN common_name LIKE '%Dance%' THEN 'Dance Floors'
        WHEN common_name LIKE '%Light%' THEN 'Lighting'
        WHEN common_name LIKE '%Bar%' THEN 'Bars'
        ELSE 'Miscellaneous'
    END as category,
    common_name as subcategory,
    LEFT(common_name, 50) as short_common_name
FROM id_item_master
WHERE rental_class_num IS NOT NULL
AND rental_class_num NOT IN (SELECT rental_class_id FROM rental_class_mappings);

-- 1.3 Update Item Status Based on Recent Transactions
UPDATE id_item_master im
SET status = 'Ready to Rent'
WHERE im.tag_id IN (
    SELECT DISTINCT tag_id 
    FROM id_transactions 
    WHERE scan_type = 'Return' 
    AND scan_date > DATE_SUB(NOW(), INTERVAL 7 DAY)
)
AND im.status != 'Ready to Rent';

-- ============================================================================
-- SECTION 2: CREATE MISSING TABLES AND STRUCTURES
-- ============================================================================

-- 2.1 Create Store Master Table
CREATE TABLE IF NOT EXISTS store_master (
    store_id VARCHAR(10) PRIMARY KEY,
    store_name VARCHAR(100) NOT NULL,
    store_type ENUM('Main', 'Satellite', 'Warehouse', 'Partner') DEFAULT 'Main',
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(2),
    zip VARCHAR(10),
    phone VARCHAR(20),
    manager_name VARCHAR(100),
    manager_email VARCHAR(100),
    active BOOLEAN DEFAULT TRUE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_active (active),
    INDEX idx_store_type (store_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2.2 Populate Store Master with Known Stores
INSERT IGNORE INTO store_master (store_id, store_name, store_type) VALUES
('6800', 'Main Warehouse', 'Warehouse'),
('000', 'Central Hub', 'Main'),
('3607', 'North Branch', 'Satellite'),
('8101', 'South Branch', 'Satellite'),
('728', 'East Branch', 'Satellite');

-- 2.3 Create Item Activity Summary Table for Analytics
CREATE TABLE IF NOT EXISTS item_activity_summary (
    tag_id VARCHAR(255) PRIMARY KEY,
    first_scan_date DATETIME,
    last_scan_date DATETIME,
    total_scans INT DEFAULT 0,
    total_rentals INT DEFAULT 0,
    total_returns INT DEFAULT 0,
    total_deliveries INT DEFAULT 0,
    total_pickups INT DEFAULT 0,
    avg_rental_duration_days DECIMAL(10,2),
    max_rental_duration_days INT,
    revenue_generated DECIMAL(10,2) DEFAULT 0.00,
    days_since_last_activity INT,
    activity_score DECIMAL(5,2) DEFAULT 0.00,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (tag_id) REFERENCES id_item_master(tag_id) ON DELETE CASCADE,
    INDEX idx_last_scan (last_scan_date),
    INDEX idx_activity_score (activity_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2.4 Create Data Quality Monitoring Table
CREATE TABLE IF NOT EXISTS data_quality_metrics (
    metric_id INT PRIMARY KEY AUTO_INCREMENT,
    metric_date DATE NOT NULL,
    table_name VARCHAR(100) NOT NULL,
    total_records INT,
    records_with_issues INT,
    issue_type VARCHAR(100),
    issue_description TEXT,
    severity ENUM('Critical', 'High', 'Medium', 'Low') DEFAULT 'Medium',
    resolved BOOLEAN DEFAULT FALSE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_metric (metric_date, table_name, issue_type),
    INDEX idx_severity (severity),
    INDEX idx_resolved (resolved)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================================
-- SECTION 3: ADD MISSING INDEXES FOR PERFORMANCE
-- ============================================================================

-- 3.1 Composite Indexes for Common Queries
CREATE INDEX IF NOT EXISTS idx_item_store_status 
ON id_item_master(home_store, current_store, status);

CREATE INDEX IF NOT EXISTS idx_item_identifier_rental 
ON id_item_master(identifier_type, rental_class_num);

CREATE INDEX IF NOT EXISTS idx_trans_contract_scan 
ON id_transactions(contract_number, scan_type, scan_date);

CREATE INDEX IF NOT EXISTS idx_trans_tag_scan 
ON id_transactions(tag_id, scan_date);

-- 3.2 Covering Indexes for Analytics Queries
CREATE INDEX IF NOT EXISTS idx_item_analytics 
ON id_item_master(status, identifier_type, date_last_scanned)
INCLUDE (rental_class_num, home_store, current_store);

-- ============================================================================
-- SECTION 4: POPULATE ANALYTICS TABLES
-- ============================================================================

-- 4.1 Populate Item Activity Summary
INSERT INTO item_activity_summary (
    tag_id,
    first_scan_date,
    last_scan_date,
    total_scans,
    total_rentals,
    total_returns,
    total_deliveries,
    total_pickups,
    avg_rental_duration_days,
    days_since_last_activity
)
SELECT 
    t.tag_id,
    MIN(t.scan_date) as first_scan_date,
    MAX(t.scan_date) as last_scan_date,
    COUNT(*) as total_scans,
    SUM(CASE WHEN t.scan_type = 'Rental' THEN 1 ELSE 0 END) as total_rentals,
    SUM(CASE WHEN t.scan_type = 'Return' THEN 1 ELSE 0 END) as total_returns,
    SUM(CASE WHEN t.scan_type = 'Delivery' THEN 1 ELSE 0 END) as total_deliveries,
    SUM(CASE WHEN t.scan_type = 'Pickup' THEN 1 ELSE 0 END) as total_pickups,
    AVG(CASE 
        WHEN t.scan_type = 'Return' THEN 
            DATEDIFF(t.scan_date, (
                SELECT MAX(t2.scan_date) 
                FROM id_transactions t2 
                WHERE t2.tag_id = t.tag_id 
                AND t2.scan_type = 'Rental' 
                AND t2.scan_date < t.scan_date
            ))
        ELSE NULL 
    END) as avg_rental_duration_days,
    DATEDIFF(NOW(), MAX(t.scan_date)) as days_since_last_activity
FROM id_transactions t
GROUP BY t.tag_id
ON DUPLICATE KEY UPDATE
    last_scan_date = VALUES(last_scan_date),
    total_scans = VALUES(total_scans),
    total_rentals = VALUES(total_rentals),
    total_returns = VALUES(total_returns),
    total_deliveries = VALUES(total_deliveries),
    total_pickups = VALUES(total_pickups),
    avg_rental_duration_days = VALUES(avg_rental_duration_days),
    days_since_last_activity = VALUES(days_since_last_activity);

-- 4.2 Calculate Activity Scores
UPDATE item_activity_summary
SET activity_score = (
    (100 - LEAST(days_since_last_activity, 100)) * 0.5 +  -- Recency: 50%
    LEAST(total_rentals * 10, 30) +                        -- Rental frequency: 30%
    LEAST(total_scans * 2, 20)                            -- Scan frequency: 20%
);

-- ============================================================================
-- SECTION 5: DATA INTEGRITY CONSTRAINTS
-- ============================================================================

-- 5.1 Add Foreign Key Constraints (with CASCADE for maintenance)
ALTER TABLE id_item_master
ADD CONSTRAINT fk_item_home_store 
FOREIGN KEY (home_store) REFERENCES store_master(store_id) 
ON UPDATE CASCADE ON DELETE SET NULL;

ALTER TABLE id_item_master
ADD CONSTRAINT fk_item_current_store 
FOREIGN KEY (current_store) REFERENCES store_master(store_id) 
ON UPDATE CASCADE ON DELETE SET NULL;

-- 5.2 Add Check Constraints for Data Validation
ALTER TABLE id_item_master
ADD CONSTRAINT chk_identifier_type 
CHECK (identifier_type IN ('None', 'QR', 'Sticker', 'Bulk', 'RFID'));

ALTER TABLE id_transactions
ADD CONSTRAINT chk_scan_type 
CHECK (scan_type IN ('Touch Scan', 'Rental', 'Return', 'Delivery', 'Pickup'));

-- ============================================================================
-- SECTION 6: DATA QUALITY MONITORING PROCEDURES
-- ============================================================================

DELIMITER //

-- 6.1 Procedure to Check Data Quality Daily
CREATE PROCEDURE IF NOT EXISTS sp_check_data_quality()
BEGIN
    DECLARE v_date DATE DEFAULT CURDATE();
    
    -- Check for missing store locations
    INSERT INTO data_quality_metrics (metric_date, table_name, total_records, records_with_issues, issue_type, issue_description, severity)
    SELECT 
        v_date,
        'id_item_master',
        COUNT(*),
        SUM(CASE WHEN home_store IS NULL OR current_store IS NULL THEN 1 ELSE 0 END),
        'Missing Store Location',
        'Items without home_store or current_store',
        'High'
    FROM id_item_master
    ON DUPLICATE KEY UPDATE
        total_records = VALUES(total_records),
        records_with_issues = VALUES(records_with_issues);
    
    -- Check for orphaned transactions
    INSERT INTO data_quality_metrics (metric_date, table_name, total_records, records_with_issues, issue_type, issue_description, severity)
    SELECT 
        v_date,
        'id_transactions',
        COUNT(*),
        SUM(CASE WHEN im.tag_id IS NULL THEN 1 ELSE 0 END),
        'Orphaned Transactions',
        'Transactions without corresponding item master record',
        'Critical'
    FROM id_transactions t
    LEFT JOIN id_item_master im ON t.tag_id = im.tag_id
    ON DUPLICATE KEY UPDATE
        total_records = VALUES(total_records),
        records_with_issues = VALUES(records_with_issues);
    
    -- Check for stale inventory
    INSERT INTO data_quality_metrics (metric_date, table_name, total_records, records_with_issues, issue_type, issue_description, severity)
    SELECT 
        v_date,
        'id_item_master',
        COUNT(*),
        SUM(CASE WHEN date_last_scanned IS NULL OR DATEDIFF(NOW(), date_last_scanned) > 180 THEN 1 ELSE 0 END),
        'Stale Inventory',
        'Items not scanned in over 180 days',
        'Medium'
    FROM id_item_master
    ON DUPLICATE KEY UPDATE
        total_records = VALUES(total_records),
        records_with_issues = VALUES(records_with_issues);
END//

-- 6.2 Procedure to Sync Item Status with Transactions
CREATE PROCEDURE IF NOT EXISTS sp_sync_item_status()
BEGIN
    -- Update items that were recently rented
    UPDATE id_item_master im
    INNER JOIN (
        SELECT tag_id, MAX(scan_date) as last_rental
        FROM id_transactions
        WHERE scan_type = 'Rental'
        AND scan_date > DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY tag_id
    ) t ON im.tag_id = t.tag_id
    SET im.status = 'On Rent'
    WHERE im.status != 'On Rent';
    
    -- Update items that were recently returned
    UPDATE id_item_master im
    INNER JOIN (
        SELECT t1.tag_id
        FROM id_transactions t1
        WHERE t1.scan_type = 'Return'
        AND t1.scan_date = (
            SELECT MAX(t2.scan_date)
            FROM id_transactions t2
            WHERE t2.tag_id = t1.tag_id
        )
        AND t1.scan_date > DATE_SUB(NOW(), INTERVAL 30 DAY)
    ) recent_returns ON im.tag_id = recent_returns.tag_id
    SET im.status = 'Ready to Rent'
    WHERE im.status != 'Ready to Rent';
END//

DELIMITER ;

-- ============================================================================
-- SECTION 7: VIEWS FOR REPORTING AND ANALYTICS
-- ============================================================================

-- 7.1 Comprehensive Inventory View
CREATE OR REPLACE VIEW v_inventory_complete AS
SELECT 
    im.tag_id,
    im.serial_number,
    im.rental_class_num,
    im.common_name,
    rcm.category,
    rcm.subcategory,
    im.identifier_type,
    im.status,
    im.quality,
    im.home_store,
    sm_home.store_name as home_store_name,
    im.current_store,
    sm_current.store_name as current_store_name,
    im.date_last_scanned,
    DATEDIFF(NOW(), im.date_last_scanned) as days_since_scan,
    ias.total_rentals,
    ias.total_returns,
    ias.avg_rental_duration_days,
    ias.activity_score,
    im.turnover_ytd,
    im.turnover_ltd,
    im.sell_price,
    im.retail_price
FROM id_item_master im
LEFT JOIN rental_class_mappings rcm ON im.rental_class_num = rcm.rental_class_id
LEFT JOIN store_master sm_home ON im.home_store = sm_home.store_id
LEFT JOIN store_master sm_current ON im.current_store = sm_current.store_id
LEFT JOIN item_activity_summary ias ON im.tag_id = ias.tag_id;

-- 7.2 Active Rentals View
CREATE OR REPLACE VIEW v_active_rentals AS
SELECT 
    t.contract_number,
    t.tag_id,
    im.common_name,
    im.rental_class_num,
    t.client_name,
    t.scan_date as rental_date,
    DATEDIFF(NOW(), t.scan_date) as days_on_rent,
    im.current_store,
    im.status
FROM id_transactions t
INNER JOIN id_item_master im ON t.tag_id = im.tag_id
WHERE t.scan_type = 'Rental'
AND t.scan_date = (
    SELECT MAX(t2.scan_date)
    FROM id_transactions t2
    WHERE t2.tag_id = t.tag_id
)
AND NOT EXISTS (
    SELECT 1
    FROM id_transactions t3
    WHERE t3.tag_id = t.tag_id
    AND t3.scan_type = 'Return'
    AND t3.scan_date > t.scan_date
);

-- 7.3 Data Quality Dashboard View
CREATE OR REPLACE VIEW v_data_quality_dashboard AS
SELECT 
    metric_date,
    table_name,
    issue_type,
    severity,
    records_with_issues,
    total_records,
    ROUND((records_with_issues / total_records * 100), 2) as issue_percentage,
    resolved
FROM data_quality_metrics
WHERE metric_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
ORDER BY metric_date DESC, severity ASC;

-- ============================================================================
-- SECTION 8: SCHEDULED MAINTENANCE EVENTS
-- ============================================================================

-- 8.1 Create Event to Run Daily Data Quality Check
DELIMITER //
CREATE EVENT IF NOT EXISTS event_daily_data_quality
ON SCHEDULE EVERY 1 DAY
STARTS CONCAT(CURDATE() + INTERVAL 1 DAY, ' 02:00:00')
DO
BEGIN
    CALL sp_check_data_quality();
    CALL sp_sync_item_status();
END//
DELIMITER ;

-- 8.2 Enable Event Scheduler
SET GLOBAL event_scheduler = ON;

-- ============================================================================
-- SECTION 9: FINAL VERIFICATION QUERIES
-- ============================================================================

-- 9.1 Verify Store Master Population
SELECT 'Store Master Records' as check_name, COUNT(*) as count FROM store_master;

-- 9.2 Verify Rental Class Mappings
SELECT 'Rental Class Mappings' as check_name, COUNT(*) as count FROM rental_class_mappings;

-- 9.3 Verify Activity Summary Population
SELECT 'Activity Summary Records' as check_name, COUNT(*) as count FROM item_activity_summary;

-- 9.4 Check Current Data Quality Issues
SELECT * FROM v_data_quality_dashboard LIMIT 10;

-- 9.5 Summary Statistics After Optimization
SELECT 
    'Post-Optimization Stats' as report_type,
    (SELECT COUNT(*) FROM id_item_master WHERE home_store IS NOT NULL) as items_with_home_store,
    (SELECT COUNT(*) FROM id_item_master WHERE current_store IS NOT NULL) as items_with_current_store,
    (SELECT COUNT(*) FROM rental_class_mappings) as rental_mappings,
    (SELECT COUNT(*) FROM item_activity_summary) as activity_records,
    (SELECT COUNT(*) FROM v_active_rentals) as active_rentals;

-- ============================================================================
-- END OF OPTIMIZATION SCRIPTS
-- Run these scripts in sequence during a maintenance window
-- Estimated execution time: 15-30 minutes depending on data volume
-- ============================================================================