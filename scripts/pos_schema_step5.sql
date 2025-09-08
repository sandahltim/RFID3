-- POS Schema Enhancement - Step 5: Indexes and Supporting Tables

-- Add performance indexes
CREATE INDEX IF NOT EXISTS idx_item_num ON id_item_master(item_num);
CREATE INDEX IF NOT EXISTS idx_identifier_type ON id_item_master(identifier_type);
CREATE INDEX IF NOT EXISTS idx_store_location ON id_item_master(current_store);
CREATE INDEX IF NOT EXISTS idx_department ON id_item_master(department);
CREATE INDEX IF NOT EXISTS idx_manufacturer ON id_item_master(manufacturer);
CREATE INDEX IF NOT EXISTS idx_turnover_ytd ON id_item_master(turnover_ytd);
CREATE INDEX IF NOT EXISTS idx_data_source ON id_item_master(data_source);
CREATE INDEX IF NOT EXISTS idx_pos_updated ON id_item_master(pos_last_updated);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_store_status ON id_item_master(current_store, status);
CREATE INDEX IF NOT EXISTS idx_department_status ON id_item_master(department, status);
CREATE INDEX IF NOT EXISTS idx_identifier_status ON id_item_master(identifier_type, status);

-- Create store mappings table
CREATE TABLE IF NOT EXISTS store_mappings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pos_store_code VARCHAR(10) NOT NULL COMMENT 'POS store code (001, 002, 003, 004)',
    store_id VARCHAR(10) NOT NULL COMMENT 'Internal store ID (3607, 6800, 8101, 728)', 
    store_name VARCHAR(100) NOT NULL COMMENT 'Store name',
    location VARCHAR(100) COMMENT 'Store location/address',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_pos_code (pos_store_code),
    UNIQUE KEY uk_store_id (store_id),
    INDEX idx_pos_code (pos_store_code),
    INDEX idx_store_id (store_id)
);

-- Insert store mappings
INSERT INTO store_mappings (pos_store_code, store_id, store_name, location) VALUES
('001', '3607', 'Wayzata', 'Wayzata, MN'),
('002', '6800', 'Brooklyn Park', 'Brooklyn Park, MN'), 
('003', '8101', 'Fridley', 'Fridley, MN'),
('004', '728', 'Elk River', 'Elk River, MN')
ON DUPLICATE KEY UPDATE 
    store_name = VALUES(store_name),
    location = VALUES(location);

-- Create POS import log table
CREATE TABLE IF NOT EXISTS pos_import_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    import_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    import_type ENUM('equip', 'customer', 'transactions', 'transitems') NOT NULL,
    file_name VARCHAR(255),
    records_processed INT DEFAULT 0,
    records_inserted INT DEFAULT 0,
    records_updated INT DEFAULT 0,
    records_skipped INT DEFAULT 0,
    records_failed INT DEFAULT 0,
    processing_time_seconds INT,
    status ENUM('success', 'partial', 'failed') DEFAULT 'failed',
    error_summary TEXT,
    created_by VARCHAR(50) DEFAULT 'SYSTEM',
    INDEX idx_import_date (import_date),
    INDEX idx_import_type (import_type),
    INDEX idx_status (status)
);

-- Update existing RFID records with default values
UPDATE id_item_master 
SET data_source = 'RFID_API', 
    identifier_type = 'RFID',
    created_by = 'API_IMPORT'
WHERE data_source IS NULL OR data_source = '';

-- Log schema enhancement completion
INSERT INTO pos_import_log (import_type, file_name, status, error_summary, created_by)
VALUES ('equip', 'SCHEMA_ENHANCEMENT', 'success', 
    'POS integration fields added to id_item_master successfully', 
    'SCHEMA_MIGRATION');

SELECT 'POS Integration Schema Enhancement Complete - Ready for equip.csv import' as Status;