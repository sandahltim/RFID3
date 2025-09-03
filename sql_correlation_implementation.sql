-- RFID3 Database Correlation Implementation Scripts
-- Created: 2025-09-02
-- Purpose: Implement correlation infrastructure between POS and RFID systems

-- =====================================================
-- PHASE 1: SCHEMA UPDATES
-- =====================================================

-- 1.1 Add correlation fields to equipment_items table
ALTER TABLE equipment_items 
ADD COLUMN IF NOT EXISTS rfid_rental_class_num VARCHAR(255) COMMENT 'Maps to id_item_master.rental_class_num',
ADD COLUMN IF NOT EXISTS correlation_confidence DECIMAL(3,2) DEFAULT NULL COMMENT 'Confidence score 0.00-1.00',
ADD COLUMN IF NOT EXISTS correlation_method VARCHAR(50) DEFAULT NULL COMMENT 'How correlation was established',
ADD COLUMN IF NOT EXISTS correlation_date DATETIME DEFAULT NULL COMMENT 'When correlation was made',
ADD COLUMN IF NOT EXISTS correlation_verified BOOLEAN DEFAULT FALSE COMMENT 'Has correlation been manually verified',
ADD INDEX IF NOT EXISTS idx_rfid_correlation (rfid_rental_class_num),
ADD INDEX IF NOT EXISTS idx_correlation_confidence (correlation_confidence);

-- 1.2 Create dedicated equipment to RFID mapping table
CREATE TABLE IF NOT EXISTS equipment_rfid_mapping (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    pos_item_num VARCHAR(50) NOT NULL COMMENT 'Equipment item number from POS',
    rfid_rental_class_num VARCHAR(255) NOT NULL COMMENT 'Rental class from RFID system',
    mapping_type ENUM('exact', 'pattern', 'manual', 'ai_suggested', 'name_match', 'serial_match') NOT NULL,
    confidence_score DECIMAL(3,2) NOT NULL DEFAULT 0.50,
    match_details JSON COMMENT 'Details about what matched',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT 'system',
    verified_at DATETIME DEFAULT NULL,
    verified_by VARCHAR(100) DEFAULT NULL,
    notes TEXT,
    UNIQUE KEY uq_pos_rfid (pos_item_num, rfid_rental_class_num),
    INDEX idx_pos_item (pos_item_num),
    INDEX idx_rfid_class (rfid_rental_class_num),
    INDEX idx_confidence (confidence_score),
    INDEX idx_active (is_active),
    INDEX idx_mapping_type (mapping_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Maps POS equipment items to RFID rental classes';

-- 1.3 Create normalized view for transaction items
CREATE OR REPLACE VIEW normalized_transaction_items AS
SELECT 
    id,
    store_code,
    contract_no,
    -- Normalize item numbers by removing .0 suffix
    CASE 
        WHEN item_num LIKE '%.0' THEN SUBSTRING(item_num, 1, LENGTH(item_num) - 2)
        ELSE item_num
    END as normalized_item_num,
    item_num as original_item_num,
    qty,
    price,
    line_status,
    due_date,
    import_date
FROM pos_transaction_items
WHERE item_num IS NOT NULL;

-- 1.4 Add missing indexes for better performance
CREATE INDEX IF NOT EXISTS idx_equipment_name ON equipment_items(name);
CREATE INDEX IF NOT EXISTS idx_equipment_serial ON equipment_items(serial_no);
CREATE INDEX IF NOT EXISTS idx_id_master_common_name ON id_item_master(common_name);
CREATE INDEX IF NOT EXISTS idx_id_master_serial ON id_item_master(serial_number);

-- Create functional index for normalized item numbers (if MySQL 8.0+)
-- ALTER TABLE pos_transaction_items 
-- ADD INDEX idx_normalized_item ((CAST(REPLACE(item_num, '.0', '') AS CHAR(50))));

-- =====================================================
-- PHASE 2: DATA QUALITY IMPROVEMENTS
-- =====================================================

-- 2.1 Create data quality monitoring table
CREATE TABLE IF NOT EXISTS correlation_data_quality (
    id INT AUTO_INCREMENT PRIMARY KEY,
    check_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    table_name VARCHAR(100),
    quality_metric VARCHAR(100),
    metric_value DECIMAL(10,2),
    details JSON,
    INDEX idx_check_date (check_date),
    INDEX idx_table_metric (table_name, quality_metric)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2.2 Stored procedure to check data quality
DELIMITER $$
CREATE PROCEDURE IF NOT EXISTS check_correlation_data_quality()
BEGIN
    DECLARE total_equipment INT;
    DECLARE correlated_equipment INT;
    DECLARE correlation_rate DECIMAL(5,2);
    
    -- Check equipment correlation rate
    SELECT COUNT(*) INTO total_equipment FROM equipment_items;
    SELECT COUNT(*) INTO correlated_equipment FROM equipment_items WHERE rfid_rental_class_num IS NOT NULL;
    SET correlation_rate = IF(total_equipment > 0, (correlated_equipment * 100.0 / total_equipment), 0);
    
    INSERT INTO correlation_data_quality (table_name, quality_metric, metric_value, details)
    VALUES ('equipment_items', 'correlation_rate', correlation_rate, 
            JSON_OBJECT('total', total_equipment, 'correlated', correlated_equipment));
    
    -- Check for duplicate item numbers
    INSERT INTO correlation_data_quality (table_name, quality_metric, metric_value, details)
    SELECT 
        'pos_transaction_items',
        'duplicate_formats',
        COUNT(*),
        JSON_OBJECT('sample', JSON_ARRAYAGG(item_num))
    FROM (
        SELECT item_num
        FROM pos_transaction_items
        WHERE item_num LIKE '%.0'
        GROUP BY SUBSTRING(item_num, 1, LENGTH(item_num) - 2)
        HAVING COUNT(DISTINCT item_num) > 1
        LIMIT 10
    ) dupes;
    
    -- Check RFID coverage
    INSERT INTO correlation_data_quality (table_name, quality_metric, metric_value, details)
    SELECT 
        'id_item_master',
        'items_per_rental_class',
        AVG(tag_count),
        JSON_OBJECT('min', MIN(tag_count), 'max', MAX(tag_count), 'total_classes', COUNT(*))
    FROM (
        SELECT rental_class_num, COUNT(*) as tag_count
        FROM id_item_master
        WHERE rental_class_num IS NOT NULL
        GROUP BY rental_class_num
    ) counts;
END$$
DELIMITER ;

-- =====================================================
-- PHASE 3: INITIAL CORRELATION BUILDING
-- =====================================================

-- 3.1 Exact numeric matching
INSERT IGNORE INTO equipment_rfid_mapping (
    pos_item_num, 
    rfid_rental_class_num, 
    mapping_type, 
    confidence_score,
    match_details
)
SELECT DISTINCT 
    e.item_num,
    i.rental_class_num,
    'exact',
    1.00,
    JSON_OBJECT(
        'match_type', 'exact_numeric',
        'pos_name', e.name,
        'rfid_name', i.common_name,
        'tag_count', tag_count
    )
FROM equipment_items e
INNER JOIN (
    SELECT 
        rental_class_num, 
        MAX(common_name) as common_name,
        COUNT(DISTINCT tag_id) as tag_count
    FROM id_item_master
    WHERE rental_class_num IS NOT NULL
    GROUP BY rental_class_num
) i ON e.item_num = i.rental_class_num;

-- 3.2 Name-based pattern matching
INSERT IGNORE INTO equipment_rfid_mapping (
    pos_item_num, 
    rfid_rental_class_num, 
    mapping_type, 
    confidence_score,
    match_details
)
SELECT DISTINCT
    e.item_num,
    i.rental_class_num,
    'name_match',
    CASE 
        WHEN UPPER(e.name) = UPPER(i.common_name) THEN 0.95
        WHEN UPPER(e.name) LIKE CONCAT('%', UPPER(i.common_name), '%') THEN 0.80
        WHEN UPPER(i.common_name) LIKE CONCAT('%', UPPER(e.name), '%') THEN 0.75
        ELSE 0.60
    END as confidence,
    JSON_OBJECT(
        'match_type', 'name_similarity',
        'pos_name', e.name,
        'rfid_name', i.common_name,
        'similarity_type', 
        CASE 
            WHEN UPPER(e.name) = UPPER(i.common_name) THEN 'exact'
            WHEN UPPER(e.name) LIKE CONCAT('%', UPPER(i.common_name), '%') THEN 'contains_rfid'
            WHEN UPPER(i.common_name) LIKE CONCAT('%', UPPER(e.name), '%') THEN 'contains_pos'
            ELSE 'partial'
        END
    )
FROM equipment_items e
CROSS JOIN (
    SELECT DISTINCT rental_class_num, common_name
    FROM id_item_master
    WHERE rental_class_num IS NOT NULL
    AND common_name IS NOT NULL
) i
WHERE 
    (UPPER(e.name) = UPPER(i.common_name)
    OR UPPER(e.name) LIKE CONCAT('%', UPPER(i.common_name), '%')
    OR UPPER(i.common_name) LIKE CONCAT('%', UPPER(e.name), '%'))
    AND e.name IS NOT NULL
LIMIT 1000;

-- 3.3 Update equipment_items with high-confidence correlations
UPDATE equipment_items e
INNER JOIN equipment_rfid_mapping m ON e.item_num = m.pos_item_num
SET 
    e.rfid_rental_class_num = m.rfid_rental_class_num,
    e.correlation_confidence = m.confidence_score,
    e.correlation_method = m.mapping_type,
    e.correlation_date = NOW()
WHERE 
    m.confidence_score >= 0.80
    AND m.is_active = TRUE
    AND e.rfid_rental_class_num IS NULL;

-- =====================================================
-- PHASE 4: CORRELATION ANALYTICS
-- =====================================================

-- 4.1 Create correlation statistics view
CREATE OR REPLACE VIEW correlation_statistics AS
SELECT 
    'Equipment Items' as category,
    COUNT(*) as total_items,
    SUM(CASE WHEN rfid_rental_class_num IS NOT NULL THEN 1 ELSE 0 END) as correlated_items,
    ROUND(SUM(CASE WHEN rfid_rental_class_num IS NOT NULL THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as correlation_rate,
    AVG(CASE WHEN correlation_confidence IS NOT NULL THEN correlation_confidence ELSE 0 END) as avg_confidence
FROM equipment_items
UNION ALL
SELECT 
    'Transaction Items',
    COUNT(DISTINCT normalized_item_num),
    COUNT(DISTINCT CASE WHEN e.rfid_rental_class_num IS NOT NULL THEN t.normalized_item_num END),
    ROUND(COUNT(DISTINCT CASE WHEN e.rfid_rental_class_num IS NOT NULL THEN t.normalized_item_num END) * 100.0 / 
          COUNT(DISTINCT t.normalized_item_num), 2),
    NULL
FROM normalized_transaction_items t
LEFT JOIN equipment_items e ON t.normalized_item_num = e.item_num;

-- 4.2 Find uncorrelated high-activity items
CREATE OR REPLACE VIEW uncorrelated_high_activity AS
SELECT 
    t.normalized_item_num as item_num,
    COUNT(*) as transaction_count,
    SUM(t.qty) as total_quantity,
    AVG(t.price) as avg_price,
    MAX(t.import_date) as last_activity,
    e.name as equipment_name,
    'No RFID correlation' as issue
FROM normalized_transaction_items t
LEFT JOIN equipment_items e ON t.normalized_item_num = e.item_num
WHERE 
    e.rfid_rental_class_num IS NULL
    OR e.item_num IS NULL
GROUP BY t.normalized_item_num, e.name
HAVING transaction_count > 10
ORDER BY transaction_count DESC;

-- =====================================================
-- PHASE 5: MONITORING AND MAINTENANCE
-- =====================================================

-- 5.1 Create correlation audit log
CREATE TABLE IF NOT EXISTS correlation_audit_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    action_type VARCHAR(50),
    table_affected VARCHAR(100),
    record_id VARCHAR(100),
    old_value JSON,
    new_value JSON,
    user_name VARCHAR(100),
    action_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    INDEX idx_action_time (action_timestamp),
    INDEX idx_action_type (action_type),
    INDEX idx_record (table_affected, record_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5.2 Trigger to track correlation changes
DELIMITER $$
CREATE TRIGGER IF NOT EXISTS track_equipment_correlation_changes
AFTER UPDATE ON equipment_items
FOR EACH ROW
BEGIN
    IF OLD.rfid_rental_class_num != NEW.rfid_rental_class_num 
       OR (OLD.rfid_rental_class_num IS NULL AND NEW.rfid_rental_class_num IS NOT NULL)
       OR (OLD.rfid_rental_class_num IS NOT NULL AND NEW.rfid_rental_class_num IS NULL) THEN
        
        INSERT INTO correlation_audit_log (
            action_type,
            table_affected,
            record_id,
            old_value,
            new_value,
            user_name
        ) VALUES (
            'correlation_update',
            'equipment_items',
            NEW.item_num,
            JSON_OBJECT(
                'rfid_rental_class_num', OLD.rfid_rental_class_num,
                'confidence', OLD.correlation_confidence,
                'method', OLD.correlation_method
            ),
            JSON_OBJECT(
                'rfid_rental_class_num', NEW.rfid_rental_class_num,
                'confidence', NEW.correlation_confidence,
                'method', NEW.correlation_method
            ),
            IFNULL(@current_user, USER())
        );
    END IF;
END$$
DELIMITER ;

-- =====================================================
-- UTILITY QUERIES
-- =====================================================

-- Find potential correlations for manual review
SELECT 
    e.item_num as pos_item,
    e.name as pos_name,
    i.rental_class_num as rfid_class,
    i.common_name as rfid_name,
    'Review for correlation' as action_needed,
    CASE 
        WHEN LENGTH(e.name) > 10 AND LENGTH(i.common_name) > 10 
             AND SUBSTRING(UPPER(e.name), 1, 10) = SUBSTRING(UPPER(i.common_name), 1, 10) 
        THEN 'High - Name prefix match'
        WHEN e.category = i.department THEN 'Medium - Category match'
        ELSE 'Low - Manual review needed'
    END as priority
FROM equipment_items e
CROSS JOIN (
    SELECT DISTINCT rental_class_num, common_name, department
    FROM id_item_master
    WHERE rental_class_num IS NOT NULL
) i
WHERE 
    e.rfid_rental_class_num IS NULL
    AND (
        SUBSTRING(UPPER(e.name), 1, 5) = SUBSTRING(UPPER(i.common_name), 1, 5)
        OR e.category = i.department
    )
ORDER BY priority DESC
LIMIT 100;

-- Summary report
SELECT 
    'Correlation Summary Report' as report_title,
    NOW() as generated_at,
    (SELECT COUNT(*) FROM equipment_items) as total_equipment,
    (SELECT COUNT(*) FROM equipment_items WHERE rfid_rental_class_num IS NOT NULL) as correlated_equipment,
    (SELECT COUNT(*) FROM equipment_rfid_mapping) as total_mappings,
    (SELECT COUNT(*) FROM equipment_rfid_mapping WHERE confidence_score >= 0.80) as high_confidence_mappings,
    (SELECT COUNT(DISTINCT rental_class_num) FROM id_item_master WHERE rental_class_num IS NOT NULL) as total_rfid_classes,
    (SELECT COUNT(DISTINCT rfid_rental_class_num) FROM equipment_items WHERE rfid_rental_class_num IS NOT NULL) as mapped_rfid_classes;