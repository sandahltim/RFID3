-- =============================================================================
-- INVENTORY DATA CORRELATION SYSTEM
-- Version: 1.0.0
-- Purpose: Bridge RFID, POS, QR/Barcode systems with migration tracking
-- =============================================================================

-- -----------------------------------------------------------------------------
-- MASTER CORRELATION TABLE
-- Central hub linking all inventory tracking systems
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory_correlation_master (
    correlation_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    -- Universal identifiers
    master_item_id VARCHAR(100) UNIQUE NOT NULL, -- Generated unique ID across all systems
    
    -- RFID System identifiers
    rfid_tag_id VARCHAR(255),
    rfid_item_num INT,
    
    -- POS System identifiers  
    pos_item_num VARCHAR(50),
    pos_item_class VARCHAR(50),
    pos_key VARCHAR(100),
    pos_serial_no VARCHAR(100),
    
    -- QR/Barcode identifiers
    qr_code VARCHAR(255),
    barcode VARCHAR(255),
    
    -- Common attributes
    common_name VARCHAR(255),
    manufacturer VARCHAR(100),
    model_number VARCHAR(100),
    category VARCHAR(100),
    department VARCHAR(100),
    
    -- Tracking type and migration status
    tracking_type ENUM('RFID', 'QR', 'BARCODE', 'BULK', 'HYBRID') NOT NULL,
    tracking_status ENUM('ACTIVE', 'MIGRATING', 'LEGACY', 'RETIRED') DEFAULT 'ACTIVE',
    migration_phase ENUM('BULK_ONLY', 'TRANSITIONING', 'PARTIAL_TAGGED', 'FULLY_TAGGED', 'COMPLETE'),
    
    -- Quantity management (for bulk items)
    is_bulk_item BOOLEAN DEFAULT FALSE,
    bulk_quantity_on_hand DECIMAL(10,2),
    tagged_quantity INT DEFAULT 0,
    untagged_quantity INT DEFAULT 0,
    
    -- Data quality indicators
    confidence_score DECIMAL(3,2) DEFAULT 1.00, -- 0.00 to 1.00
    last_verified_date DATETIME,
    verification_source VARCHAR(50),
    
    -- Metadata
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    
    INDEX idx_rfid_tag (rfid_tag_id),
    INDEX idx_pos_item (pos_item_num, pos_item_class),
    INDEX idx_tracking_type (tracking_type),
    INDEX idx_migration_phase (migration_phase),
    INDEX idx_common_name (common_name),
    INDEX idx_confidence (confidence_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- POS DATA STAGING TABLE
-- Stores raw POS CSV imports before correlation
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pos_data_staging (
    staging_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    -- POS identifiers
    item_num VARCHAR(50),
    item_key VARCHAR(100),
    name VARCHAR(255),
    location VARCHAR(50),
    category VARCHAR(100),
    department VARCHAR(100),
    type_desc VARCHAR(100),
    
    -- Quantity and valuation
    quantity DECIMAL(10,2),
    home_store VARCHAR(10),
    current_store VARCHAR(10),
    item_group VARCHAR(50),
    
    -- Equipment details
    manufacturer VARCHAR(100),
    model_no VARCHAR(100),
    serial_no VARCHAR(100),
    part_no VARCHAR(100),
    license_no VARCHAR(50),
    model_year INT,
    
    -- Financial metrics
    turnover_mtd DECIMAL(12,2),
    turnover_ytd DECIMAL(12,2),
    turnover_ltd DECIMAL(12,2),
    repair_cost_ltd DECIMAL(12,2),
    sell_price DECIMAL(10,2),
    retail_price DECIMAL(10,2),
    
    -- Import metadata
    import_batch_id VARCHAR(50),
    import_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    file_name VARCHAR(255),
    row_number INT,
    
    -- Processing status
    processing_status ENUM('PENDING', 'MATCHED', 'PARTIAL', 'ORPHANED', 'ERROR') DEFAULT 'PENDING',
    correlation_id BIGINT,
    match_confidence DECIMAL(3,2),
    error_message TEXT,
    
    INDEX idx_pos_staging_status (processing_status),
    INDEX idx_pos_staging_batch (import_batch_id),
    INDEX idx_pos_item_key (item_num, item_key),
    FOREIGN KEY (correlation_id) REFERENCES inventory_correlation_master(correlation_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- RFID-POS MAPPING TABLE
-- Many-to-many relationship between RFID tags and POS items
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rfid_pos_mapping (
    mapping_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    correlation_id BIGINT NOT NULL,
    rfid_tag_id VARCHAR(255) NOT NULL,
    pos_item_num VARCHAR(50),
    pos_item_class VARCHAR(50),
    
    -- Relationship metadata
    mapping_type ENUM('ONE_TO_ONE', 'ONE_TO_MANY', 'PARTIAL', 'INFERRED') DEFAULT 'ONE_TO_ONE',
    confidence_score DECIMAL(3,2) DEFAULT 1.00,
    
    -- Validation
    is_validated BOOLEAN DEFAULT FALSE,
    validated_date DATETIME,
    validated_by VARCHAR(100),
    
    -- Active status
    is_active BOOLEAN DEFAULT TRUE,
    effective_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    expiry_date DATETIME,
    
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_rfid_pos (rfid_tag_id, pos_item_num, pos_item_class),
    INDEX idx_correlation (correlation_id),
    INDEX idx_active_mappings (is_active, effective_date),
    FOREIGN KEY (correlation_id) REFERENCES inventory_correlation_master(correlation_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- MIGRATION TRACKING TABLE
-- Track items transitioning from bulk to individual tracking
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS migration_tracking (
    migration_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    correlation_id BIGINT NOT NULL,
    
    -- Migration details
    from_tracking_type ENUM('BULK', 'QR', 'BARCODE', 'RFID'),
    to_tracking_type ENUM('RFID', 'QR', 'BARCODE', 'HYBRID'),
    migration_status ENUM('PLANNED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'ROLLED_BACK'),
    
    -- Quantities
    total_items_to_migrate INT,
    items_migrated INT DEFAULT 0,
    items_remaining INT,
    
    -- Timeline
    planned_start_date DATE,
    actual_start_date DATETIME,
    planned_completion_date DATE,
    actual_completion_date DATETIME,
    
    -- Cost-benefit analysis
    estimated_cost DECIMAL(10,2),
    actual_cost DECIMAL(10,2),
    estimated_roi_months INT,
    
    -- Progress tracking
    last_batch_processed VARCHAR(50),
    last_processed_date DATETIME,
    error_count INT DEFAULT 0,
    
    -- Notes
    migration_notes TEXT,
    rollback_reason TEXT,
    
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_migration_status (migration_status),
    INDEX idx_migration_correlation (correlation_id),
    FOREIGN KEY (correlation_id) REFERENCES inventory_correlation_master(correlation_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- DATA QUALITY METRICS TABLE
-- Track data quality issues and resolutions
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS data_quality_metrics (
    metric_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    -- Issue identification
    correlation_id BIGINT,
    issue_type ENUM('MISSING_DATA', 'DUPLICATE', 'MISMATCH', 'ORPHANED', 'STALE', 'INCONSISTENT'),
    severity ENUM('CRITICAL', 'HIGH', 'MEDIUM', 'LOW'),
    
    -- Issue details
    source_system VARCHAR(50),
    field_name VARCHAR(100),
    expected_value TEXT,
    actual_value TEXT,
    
    -- Resolution
    resolution_status ENUM('OPEN', 'IN_PROGRESS', 'RESOLVED', 'IGNORED'),
    resolution_method VARCHAR(100),
    resolved_date DATETIME,
    resolved_by VARCHAR(100),
    
    -- Impact assessment
    affected_records INT,
    business_impact VARCHAR(255),
    
    -- Metadata
    detected_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    detection_method VARCHAR(100),
    
    INDEX idx_quality_status (resolution_status),
    INDEX idx_quality_severity (severity),
    INDEX idx_quality_correlation (correlation_id),
    FOREIGN KEY (correlation_id) REFERENCES inventory_correlation_master(correlation_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- INVENTORY INTELLIGENCE TABLE
-- Aggregated metrics for business intelligence
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS inventory_intelligence (
    intelligence_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    correlation_id BIGINT NOT NULL,
    
    -- Utilization metrics
    utilization_rate DECIMAL(5,2), -- Percentage
    days_since_last_use INT,
    total_uses_30d INT,
    total_uses_90d INT,
    total_uses_365d INT,
    
    -- Financial metrics
    revenue_30d DECIMAL(12,2),
    revenue_90d DECIMAL(12,2),
    revenue_365d DECIMAL(12,2),
    roi_percentage DECIMAL(6,2),
    
    -- Predictive indicators
    demand_trend ENUM('INCREASING', 'STABLE', 'DECREASING'),
    seasonality_factor DECIMAL(3,2),
    recommended_quantity INT,
    reorder_point INT,
    
    -- Risk indicators
    damage_frequency DECIMAL(5,2),
    loss_risk_score DECIMAL(3,2),
    obsolescence_risk DECIMAL(3,2),
    
    -- Tracking recommendations
    should_add_tracking BOOLEAN DEFAULT FALSE,
    recommended_tracking_type VARCHAR(20),
    tracking_roi_estimate DECIMAL(10,2),
    
    -- Calculation metadata
    last_calculated DATETIME DEFAULT CURRENT_TIMESTAMP,
    calculation_version VARCHAR(20),
    
    INDEX idx_intelligence_correlation (correlation_id),
    INDEX idx_utilization (utilization_rate),
    INDEX idx_demand_trend (demand_trend),
    FOREIGN KEY (correlation_id) REFERENCES inventory_correlation_master(correlation_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- AUDIT LOG TABLE
-- Track all changes to correlation data
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS correlation_audit_log (
    audit_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    -- What changed
    table_name VARCHAR(100),
    record_id BIGINT,
    action VARCHAR(20), -- INSERT, UPDATE, DELETE, MERGE
    
    -- Change details
    old_values JSON,
    new_values JSON,
    changed_fields JSON,
    
    -- Who and when
    changed_by VARCHAR(100),
    changed_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    change_source VARCHAR(50), -- API, CSV_IMPORT, MANUAL, SYSTEM
    
    -- Context
    session_id VARCHAR(100),
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    
    INDEX idx_audit_table (table_name),
    INDEX idx_audit_date (changed_date),
    INDEX idx_audit_user (changed_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- -----------------------------------------------------------------------------
-- INVENTORY ANALYTICS VIEWS
-- -----------------------------------------------------------------------------

-- View: Current inventory status with full correlation
CREATE OR REPLACE VIEW v_inventory_status AS
SELECT 
    icm.correlation_id,
    icm.master_item_id,
    icm.common_name,
    icm.tracking_type,
    icm.tracking_status,
    icm.migration_phase,
    
    -- RFID data
    im.tag_id AS rfid_tag,
    im.status AS rfid_status,
    im.bin_location,
    im.quality,
    im.date_last_scanned,
    
    -- POS data  
    pds.item_num AS pos_item_num,
    pds.quantity AS pos_quantity,
    pds.turnover_ytd AS pos_revenue_ytd,
    
    -- Intelligence metrics
    ii.utilization_rate,
    ii.demand_trend,
    ii.should_add_tracking,
    
    -- Quality score
    icm.confidence_score,
    
    CASE 
        WHEN icm.tracking_type = 'BULK' AND ii.should_add_tracking = TRUE 
            THEN 'READY_FOR_TAGGING'
        WHEN icm.tracking_type = 'BULK' 
            THEN 'BULK_TRACKING'
        WHEN icm.tracking_type IN ('RFID', 'QR', 'BARCODE') 
            THEN 'INDIVIDUALLY_TRACKED'
        ELSE 'UNKNOWN'
    END AS tracking_recommendation
    
FROM inventory_correlation_master icm
LEFT JOIN id_item_master im ON icm.rfid_tag_id = im.tag_id
LEFT JOIN pos_data_staging pds ON icm.correlation_id = pds.correlation_id 
    AND pds.processing_status = 'MATCHED'
LEFT JOIN inventory_intelligence ii ON icm.correlation_id = ii.correlation_id;

-- View: Migration progress dashboard
CREATE OR REPLACE VIEW v_migration_progress AS
SELECT 
    mt.migration_id,
    icm.common_name,
    icm.category,
    mt.from_tracking_type,
    mt.to_tracking_type,
    mt.migration_status,
    mt.total_items_to_migrate,
    mt.items_migrated,
    ROUND((mt.items_migrated / NULLIF(mt.total_items_to_migrate, 0)) * 100, 2) AS progress_percentage,
    mt.planned_completion_date,
    DATEDIFF(mt.planned_completion_date, CURRENT_DATE) AS days_remaining,
    mt.estimated_roi_months
FROM migration_tracking mt
JOIN inventory_correlation_master icm ON mt.correlation_id = icm.correlation_id
WHERE mt.migration_status IN ('PLANNED', 'IN_PROGRESS');

-- View: Data quality dashboard
CREATE OR REPLACE VIEW v_data_quality_summary AS
SELECT 
    source_system,
    issue_type,
    severity,
    COUNT(*) AS issue_count,
    SUM(affected_records) AS total_affected_records,
    COUNT(CASE WHEN resolution_status = 'OPEN' THEN 1 END) AS open_issues,
    COUNT(CASE WHEN resolution_status = 'RESOLVED' THEN 1 END) AS resolved_issues,
    AVG(CASE 
        WHEN resolution_status = 'RESOLVED' 
        THEN TIMESTAMPDIFF(HOUR, detected_date, resolved_date) 
    END) AS avg_resolution_hours
FROM data_quality_metrics
GROUP BY source_system, issue_type, severity;

-- -----------------------------------------------------------------------------
-- STORED PROCEDURES FOR DATA PROCESSING
-- -----------------------------------------------------------------------------

DELIMITER //

-- Procedure: Process POS CSV import
CREATE PROCEDURE sp_process_pos_import(
    IN p_batch_id VARCHAR(50),
    IN p_file_name VARCHAR(255)
)
BEGIN
    DECLARE v_matched INT DEFAULT 0;
    DECLARE v_partial INT DEFAULT 0;
    DECLARE v_orphaned INT DEFAULT 0;
    DECLARE v_error INT DEFAULT 0;
    
    -- Start transaction
    START TRANSACTION;
    
    -- Match POS items with existing correlations
    UPDATE pos_data_staging pds
    LEFT JOIN inventory_correlation_master icm ON 
        (pds.item_num = icm.pos_item_num AND pds.item_key = icm.pos_key)
        OR (pds.serial_no = icm.rfid_tag_id)
        OR (LOWER(pds.name) = LOWER(icm.common_name) AND pds.manufacturer = icm.manufacturer)
    SET 
        pds.processing_status = CASE
            WHEN icm.correlation_id IS NOT NULL AND pds.serial_no = icm.rfid_tag_id THEN 'MATCHED'
            WHEN icm.correlation_id IS NOT NULL THEN 'PARTIAL'
            ELSE 'ORPHANED'
        END,
        pds.correlation_id = icm.correlation_id,
        pds.match_confidence = CASE
            WHEN icm.correlation_id IS NOT NULL AND pds.serial_no = icm.rfid_tag_id THEN 1.00
            WHEN icm.correlation_id IS NOT NULL AND pds.item_num = icm.pos_item_num THEN 0.90
            WHEN icm.correlation_id IS NOT NULL THEN 0.70
            ELSE 0.00
        END
    WHERE pds.import_batch_id = p_batch_id;
    
    -- Create new correlation records for orphaned items
    INSERT INTO inventory_correlation_master (
        master_item_id,
        pos_item_num,
        pos_key,
        pos_serial_no,
        common_name,
        manufacturer,
        model_number,
        category,
        department,
        tracking_type,
        is_bulk_item,
        bulk_quantity_on_hand,
        confidence_score,
        created_by
    )
    SELECT 
        CONCAT('POS_', pds.item_num, '_', UUID()),
        pds.item_num,
        pds.item_key,
        pds.serial_no,
        pds.name,
        pds.manufacturer,
        pds.model_no,
        pds.category,
        pds.department,
        CASE 
            WHEN pds.quantity > 1 THEN 'BULK'
            WHEN pds.serial_no IS NOT NULL THEN 'BARCODE'
            ELSE 'BULK'
        END,
        CASE WHEN pds.quantity > 1 THEN TRUE ELSE FALSE END,
        pds.quantity,
        0.50, -- Lower confidence for new items
        CONCAT('POS_IMPORT_', p_batch_id)
    FROM pos_data_staging pds
    WHERE pds.import_batch_id = p_batch_id
        AND pds.processing_status = 'ORPHANED';
    
    -- Update correlation IDs for newly created records
    UPDATE pos_data_staging pds
    JOIN inventory_correlation_master icm ON pds.item_num = icm.pos_item_num
    SET pds.correlation_id = icm.correlation_id
    WHERE pds.import_batch_id = p_batch_id
        AND pds.processing_status = 'ORPHANED'
        AND icm.created_by = CONCAT('POS_IMPORT_', p_batch_id);
    
    -- Get summary counts
    SELECT 
        SUM(CASE WHEN processing_status = 'MATCHED' THEN 1 ELSE 0 END),
        SUM(CASE WHEN processing_status = 'PARTIAL' THEN 1 ELSE 0 END),
        SUM(CASE WHEN processing_status = 'ORPHANED' THEN 1 ELSE 0 END),
        SUM(CASE WHEN processing_status = 'ERROR' THEN 1 ELSE 0 END)
    INTO v_matched, v_partial, v_orphaned, v_error
    FROM pos_data_staging
    WHERE import_batch_id = p_batch_id;
    
    -- Log the import
    INSERT INTO correlation_audit_log (
        table_name,
        action,
        new_values,
        changed_by,
        change_source
    ) VALUES (
        'pos_data_staging',
        'IMPORT',
        JSON_OBJECT(
            'batch_id', p_batch_id,
            'file_name', p_file_name,
            'matched', v_matched,
            'partial', v_partial,
            'orphaned', v_orphaned,
            'error', v_error
        ),
        'SYSTEM',
        'CSV_IMPORT'
    );
    
    COMMIT;
    
    -- Return summary
    SELECT v_matched AS matched_count,
           v_partial AS partial_count,
           v_orphaned AS orphaned_count,
           v_error AS error_count;
END//

-- Procedure: Calculate inventory intelligence metrics
CREATE PROCEDURE sp_calculate_intelligence(
    IN p_correlation_id BIGINT
)
BEGIN
    DECLARE v_utilization DECIMAL(5,2);
    DECLARE v_demand_trend VARCHAR(20);
    DECLARE v_should_track BOOLEAN;
    
    -- Calculate utilization from transactions
    SELECT 
        COUNT(DISTINCT DATE(t.scan_date)) / 30.0 * 100
    INTO v_utilization
    FROM id_transactions t
    JOIN inventory_correlation_master icm ON t.tag_id = icm.rfid_tag_id
    WHERE icm.correlation_id = p_correlation_id
        AND t.scan_date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY);
    
    -- Determine demand trend
    WITH monthly_usage AS (
        SELECT 
            MONTH(t.scan_date) AS month,
            COUNT(*) AS usage_count
        FROM id_transactions t
        JOIN inventory_correlation_master icm ON t.tag_id = icm.rfid_tag_id
        WHERE icm.correlation_id = p_correlation_id
            AND t.scan_date >= DATE_SUB(CURRENT_DATE, INTERVAL 90 DAY)
        GROUP BY MONTH(t.scan_date)
    )
    SELECT 
        CASE 
            WHEN COUNT(*) < 2 THEN 'STABLE'
            WHEN (SELECT usage_count FROM monthly_usage ORDER BY month DESC LIMIT 1) > 
                 (SELECT AVG(usage_count) FROM monthly_usage) * 1.2 THEN 'INCREASING'
            WHEN (SELECT usage_count FROM monthly_usage ORDER BY month DESC LIMIT 1) < 
                 (SELECT AVG(usage_count) FROM monthly_usage) * 0.8 THEN 'DECREASING'
            ELSE 'STABLE'
        END
    INTO v_demand_trend
    FROM monthly_usage;
    
    -- Determine if should add tracking
    SELECT 
        CASE 
            WHEN icm.tracking_type = 'BULK' 
                AND COALESCE(pds.turnover_ytd, 0) > 10000 
                AND COALESCE(pds.quantity, 0) > 10
            THEN TRUE
            ELSE FALSE
        END
    INTO v_should_track
    FROM inventory_correlation_master icm
    LEFT JOIN pos_data_staging pds ON icm.correlation_id = pds.correlation_id
    WHERE icm.correlation_id = p_correlation_id;
    
    -- Insert or update intelligence record
    INSERT INTO inventory_intelligence (
        correlation_id,
        utilization_rate,
        demand_trend,
        should_add_tracking,
        last_calculated
    ) VALUES (
        p_correlation_id,
        v_utilization,
        v_demand_trend,
        v_should_track,
        CURRENT_TIMESTAMP
    )
    ON DUPLICATE KEY UPDATE
        utilization_rate = v_utilization,
        demand_trend = v_demand_trend,
        should_add_tracking = v_should_track,
        last_calculated = CURRENT_TIMESTAMP;
END//

-- Procedure: Detect and log data quality issues
CREATE PROCEDURE sp_detect_quality_issues()
BEGIN
    DECLARE v_issue_count INT DEFAULT 0;
    
    -- Detect orphaned RFID tags (in RFID but not in correlation)
    INSERT INTO data_quality_metrics (
        issue_type,
        severity,
        source_system,
        field_name,
        actual_value,
        resolution_status,
        detection_method
    )
    SELECT 
        'ORPHANED',
        'HIGH',
        'RFID',
        'tag_id',
        im.tag_id,
        'OPEN',
        'AUTOMATED_SCAN'
    FROM id_item_master im
    LEFT JOIN inventory_correlation_master icm ON im.tag_id = icm.rfid_tag_id
    WHERE icm.correlation_id IS NULL
        AND im.status = 'Ready to Rent'
        AND NOT EXISTS (
            SELECT 1 FROM data_quality_metrics dqm 
            WHERE dqm.actual_value = im.tag_id 
                AND dqm.issue_type = 'ORPHANED'
                AND dqm.resolution_status = 'OPEN'
        );
    
    -- Detect mismatched quantities
    INSERT INTO data_quality_metrics (
        correlation_id,
        issue_type,
        severity,
        source_system,
        field_name,
        expected_value,
        actual_value,
        resolution_status,
        detection_method
    )
    SELECT 
        icm.correlation_id,
        'MISMATCH',
        'MEDIUM',
        'POS',
        'quantity',
        icm.bulk_quantity_on_hand,
        pds.quantity,
        'OPEN',
        'AUTOMATED_SCAN'
    FROM inventory_correlation_master icm
    JOIN pos_data_staging pds ON icm.correlation_id = pds.correlation_id
    WHERE ABS(COALESCE(icm.bulk_quantity_on_hand, 0) - COALESCE(pds.quantity, 0)) > 1
        AND icm.tracking_type = 'BULK'
        AND pds.processing_status = 'MATCHED';
    
    SELECT ROW_COUNT() INTO v_issue_count;
    
    -- Return count of new issues detected
    SELECT v_issue_count AS new_issues_detected;
END//

DELIMITER ;

-- -----------------------------------------------------------------------------
-- INDEXES FOR PERFORMANCE
-- -----------------------------------------------------------------------------

-- Performance indexes for large datasets
CREATE INDEX idx_transactions_scan_date ON id_transactions(scan_date);
CREATE INDEX idx_transactions_tag_contract ON id_transactions(tag_id, contract_number);
CREATE INDEX idx_item_master_status_quality ON id_item_master(status, quality);

-- -----------------------------------------------------------------------------
-- INITIAL DATA SETUP
-- -----------------------------------------------------------------------------

-- Insert tracking type migration paths
INSERT INTO inventory_correlation_master (
    master_item_id, 
    common_name, 
    tracking_type, 
    migration_phase,
    confidence_score
) VALUES
    ('BULK_STRAPS_001', 'Ratchet Straps', 'BULK', 'BULK_ONLY', 1.00),
    ('BULK_STAKES_001', 'Tent Stakes', 'BULK', 'BULK_ONLY', 1.00),
    ('TRANSITION_POLES_001', 'Metal Tent Poles', 'HYBRID', 'TRANSITIONING', 0.85),
    ('RFID_TABLE_001', '60" Round Table', 'RFID', 'FULLY_TAGGED', 1.00),
    ('RFID_CHAIR_001', 'Chiavari Chair', 'RFID', 'FULLY_TAGGED', 1.00);

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON inventory_correlation_master TO 'rfid_app'@'localhost';
GRANT SELECT, INSERT, UPDATE ON pos_data_staging TO 'rfid_app'@'localhost';
GRANT SELECT ON v_inventory_status TO 'rfid_app'@'localhost';
GRANT SELECT ON v_migration_progress TO 'rfid_app'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_process_pos_import TO 'rfid_app'@'localhost';
GRANT EXECUTE ON PROCEDURE sp_calculate_intelligence TO 'rfid_app'@'localhost';