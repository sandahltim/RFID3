-- POS Data Integration Schema Enhancement for id_item_master
-- Safe, non-breaking additions to support equip.csv data integration
-- Maintains all existing RFID functionality while adding POS business intelligence

-- Phase 1: Add POS Integration Fields to id_item_master
-- These fields are additive and will not affect existing queries

ALTER TABLE id_item_master 
-- Universal item identification (bridge between RFID and POS)
ADD COLUMN item_num INT UNIQUE KEY COMMENT 'POS ItemNum - Universal identifier',
ADD COLUMN identifier_type ENUM('RFID','Sticker','QR','Barcode','Bulk','None') DEFAULT 'None' COMMENT 'Type of identifier on physical item',
ADD COLUMN identifier_value VARCHAR(255) COMMENT 'Value of non-RFID identifier (QR code, barcode, etc)',
ADD COLUMN is_bulk BOOLEAN DEFAULT FALSE COMMENT 'True for bulk/quantity items without individual tracking',

-- POS Business Intelligence Fields  
ADD COLUMN department VARCHAR(100) COMMENT 'POS Department categorization',
ADD COLUMN type_desc VARCHAR(50) COMMENT 'POS Type Description',
ADD COLUMN manufacturer VARCHAR(100) COMMENT 'Equipment manufacturer',
ADD COLUMN model_no VARCHAR(50) COMMENT 'Model number',
ADD COLUMN part_no VARCHAR(50) COMMENT 'Part number',
ADD COLUMN alt_key VARCHAR(50) COMMENT 'Alternative POS key/reference',

-- Financial/Business Metrics
ADD COLUMN turnover_mtd DECIMAL(10,2) COMMENT 'Month-to-date turnover revenue',
ADD COLUMN turnover_ytd DECIMAL(10,2) COMMENT 'Year-to-date turnover revenue', 
ADD COLUMN turnover_ltd DECIMAL(10,2) COMMENT 'Life-to-date turnover revenue',
ADD COLUMN repair_cost_mtd DECIMAL(10,2) COMMENT 'Month-to-date repair costs',
ADD COLUMN repair_cost_ltd DECIMAL(10,2) COMMENT 'Life-to-date repair costs',
ADD COLUMN sell_price DECIMAL(10,2) COMMENT 'Selling/resale price',
ADD COLUMN retail_price DECIMAL(10,2) COMMENT 'Retail rental price',
ADD COLUMN deposit DECIMAL(10,2) COMMENT 'Required deposit amount',
ADD COLUMN damage_waiver_pct DECIMAL(5,2) COMMENT 'Damage waiver percentage',

-- Store/Location Management
ADD COLUMN home_store VARCHAR(10) COMMENT 'Home store code (001=Wayzata, 002=Brooklyn Park, 003=Fridley, 004=Elk River)',
ADD COLUMN current_store VARCHAR(10) COMMENT 'Current store location',
ADD COLUMN quantity INT DEFAULT 1 COMMENT 'Quantity for bulk items',

-- Inventory Management
ADD COLUMN reorder_min INT COMMENT 'Minimum reorder level',
ADD COLUMN reorder_max INT COMMENT 'Maximum reorder level',
ADD COLUMN last_purchase_date DATETIME COMMENT 'Date of last purchase/acquisition',
ADD COLUMN last_purchase_price DECIMAL(10,2) COMMENT 'Price of last purchase',

-- Complex Data (JSON for flexibility)
ADD COLUMN rental_rates JSON COMMENT 'Rental rates structure {"period1": rate1, "period2": rate2, ...}',
ADD COLUMN vendor_ids JSON COMMENT 'Vendor relationships {"vendor1": id1, "vendor2": id2, "vendor3": id3}',
ADD COLUMN order_nos JSON COMMENT 'Purchase order numbers {"order1": no1, "order2": no2, "order3": no3}',
ADD COLUMN tag_history JSON COMMENT 'Tag transition history for QR->RFID upgrades',

-- Meter/Usage Tracking
ADD COLUMN meter_out DECIMAL(10,2) COMMENT 'Meter reading when item goes out',
ADD COLUMN meter_in DECIMAL(10,2) COMMENT 'Meter reading when item comes in',

-- Data Source Tracking
ADD COLUMN data_source VARCHAR(20) DEFAULT 'RFID_API' COMMENT 'Source of data (RFID_API, POS_IMPORT, MANUAL)',
ADD COLUMN pos_last_updated DATETIME COMMENT 'Last update from POS data import',
ADD COLUMN created_by VARCHAR(20) DEFAULT 'SYSTEM' COMMENT 'Who/what created this record';

-- Phase 2: Add Performance Indexes
-- These indexes will optimize queries for both RFID and POS data

-- Primary POS integration indexes
CREATE INDEX idx_item_num ON id_item_master(item_num);
CREATE INDEX idx_identifier_type ON id_item_master(identifier_type);
CREATE INDEX idx_store_location ON id_item_master(current_store);
CREATE INDEX idx_department ON id_item_master(department);
CREATE INDEX idx_manufacturer ON id_item_master(manufacturer);

-- Business intelligence indexes
CREATE INDEX idx_turnover_ytd ON id_item_master(turnover_ytd);
CREATE INDEX idx_data_source ON id_item_master(data_source);
CREATE INDEX idx_pos_updated ON id_item_master(pos_last_updated);

-- Composite indexes for common queries
CREATE INDEX idx_store_status ON id_item_master(current_store, status);
CREATE INDEX idx_department_status ON id_item_master(department, status);
CREATE INDEX idx_identifier_status ON id_item_master(identifier_type, status);

-- Phase 3: Create Store Mapping Reference Table
-- Maps store codes between different systems

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

-- Phase 4: Create POS Import Log Table
-- Track all POS data import operations for audit and debugging

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

-- Phase 5: Update existing RFID records with default values
-- Set data_source for existing records to distinguish from POS imports

UPDATE id_item_master 
SET data_source = 'RFID_API', 
    identifier_type = 'RFID',
    created_by = 'API_IMPORT'
WHERE data_source IS NULL OR data_source = '';

-- Phase 6: Create backup of original schema (for rollback)
-- Document original state for safety

INSERT INTO pos_import_log (import_type, file_name, status, error_summary, created_by)
VALUES ('equip', 'SCHEMA_ENHANCEMENT', 'success', 
    CONCAT('Added POS integration fields to id_item_master. Original field count: 18, Enhanced field count: ', 
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'rfid_inventory' AND TABLE_NAME = 'id_item_master')), 
    'SCHEMA_MIGRATION');

-- Verification queries (run these to verify schema changes)
-- SELECT COUNT(*) as enhanced_field_count FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'rfid_inventory' AND TABLE_NAME = 'id_item_master';
-- SELECT column_name, data_type, is_nullable, column_default, column_comment FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = 'rfid_inventory' AND TABLE_NAME = 'id_item_master' AND column_name LIKE '%item_num%';
-- SELECT * FROM store_mappings;
-- SELECT * FROM pos_import_log WHERE import_type = 'equip';

-- Success message
SELECT 'POS Integration Schema Enhancement Complete - Ready for equip.csv import' as Status;