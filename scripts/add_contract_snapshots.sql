-- Migration script to add contract_snapshots table
-- Version: 2025-08-24-v1
-- Purpose: Store historical snapshots of contract items to preserve data integrity

CREATE TABLE IF NOT EXISTS contract_snapshots (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contract_number VARCHAR(255) NOT NULL,
    tag_id VARCHAR(255) NOT NULL,
    client_name VARCHAR(255),
    common_name VARCHAR(255),
    rental_class_num VARCHAR(255),
    status VARCHAR(50),
    quality VARCHAR(50),
    bin_location VARCHAR(255),
    serial_number VARCHAR(255),
    notes TEXT,
    snapshot_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    snapshot_type VARCHAR(50) NOT NULL COMMENT 'contract_start, contract_end, status_change, periodic',
    created_by VARCHAR(255),
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    
    INDEX ix_contract_snapshots_contract_number (contract_number),
    INDEX ix_contract_snapshots_snapshot_date (snapshot_date),
    INDEX ix_contract_snapshots_tag_id (tag_id),
    INDEX ix_contract_snapshots_type (snapshot_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Historical snapshots of contract items for data preservation';

-- Create a sample trigger to automatically snapshot when items change contracts
-- This can be enabled later when ready for production use
/*
DELIMITER //
CREATE TRIGGER contract_snapshot_on_contract_change
    AFTER UPDATE ON id_item_master
    FOR EACH ROW
BEGIN
    IF OLD.last_contract_num != NEW.last_contract_num AND NEW.last_contract_num IS NOT NULL THEN
        INSERT INTO contract_snapshots (
            contract_number, tag_id, client_name, common_name, rental_class_num,
            status, quality, bin_location, serial_number, notes,
            snapshot_date, snapshot_type, created_by, latitude, longitude
        ) VALUES (
            NEW.last_contract_num, NEW.tag_id, NEW.client_name, NEW.common_name, NEW.rental_class_num,
            NEW.status, NEW.quality, NEW.bin_location, NEW.serial_number, NEW.notes,
            NOW(), 'status_change', 'system_trigger', NEW.latitude, NEW.longitude
        );
    END IF;
END//
DELIMITER ;
*/