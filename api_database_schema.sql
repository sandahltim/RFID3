-- RFID API Database Schema v1.0
-- Date: 2025-09-17
-- Purpose: Self-hosted API database matching current id_item_master + id_transactions + POS correlation

CREATE DATABASE IF NOT EXISTS rfid_api_v1 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE rfid_api_v1;

-- ============================================================================
-- 1. ITEMS MASTER TABLE (Mirrors id_item_master exactly)
-- ============================================================================
CREATE TABLE api_items (
    tag_id VARCHAR(255) PRIMARY KEY COMMENT 'RFID tag identifier (24-char HEX for RFID items)',
    uuid_accounts_fk VARCHAR(255) COMMENT 'Account foreign key',
    serial_number VARCHAR(255) COMMENT 'Manufacturer serial number',
    client_name VARCHAR(255) COMMENT 'Current/last customer',
    rental_class_num VARCHAR(255) COMMENT 'Equipment classification (links to POS via correlation)',
    common_name VARCHAR(255) COMMENT 'Human-readable item name',
    quality VARCHAR(50) COMMENT 'Condition grade',
    bin_location VARCHAR(255) COMMENT 'Physical storage location',
    status VARCHAR(50) COMMENT 'Current item status',
    last_contract_num VARCHAR(255) COMMENT 'Most recent rental contract',
    last_scanned_by VARCHAR(255) COMMENT 'Last scanner user ID',
    notes TEXT COMMENT 'General notes',
    status_notes TEXT COMMENT 'Status-specific notes',
    longitude DECIMAL(9,6) COMMENT 'GPS longitude',
    latitude DECIMAL(9,6) COMMENT 'GPS latitude',
    date_last_scanned DATETIME COMMENT 'Last scan timestamp',
    date_created DATETIME COMMENT 'Item creation date',
    date_updated DATETIME COMMENT 'Last modification date',
    home_store VARCHAR(10) COMMENT 'Original store assignment (3607,6800,728,8101)',
    current_store VARCHAR(10) COMMENT 'Current location store',
    identifier_type VARCHAR(10) COMMENT '"None" for RFID, "QR", "Sticker", "Bulk"',
    item_num INTEGER UNIQUE COMMENT 'Sequential item number',
    turnover_ytd DECIMAL(10,2) COMMENT 'Year-to-date revenue',
    turnover_ltd DECIMAL(10,2) COMMENT 'Lifetime revenue',
    repair_cost_ltd DECIMAL(10,2) COMMENT 'Lifetime repair costs',
    sell_price DECIMAL(10,2) COMMENT 'Sale price',
    retail_price DECIMAL(10,2) COMMENT 'Retail/rental price',
    manufacturer VARCHAR(100) COMMENT 'Equipment manufacturer',

    -- Indexes for performance
    INDEX ix_api_items_rental_class (rental_class_num),
    INDEX ix_api_items_status (status),
    INDEX ix_api_items_store (current_store),
    INDEX ix_api_items_identifier_type (identifier_type),
    INDEX ix_api_items_date_scanned (date_last_scanned)
) ENGINE=InnoDB COMMENT='RFID items master table - mirrors id_item_master';

-- ============================================================================
-- 2. TRANSACTIONS TABLE (Mirrors id_transactions exactly)
-- ============================================================================
CREATE TABLE api_transactions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT 'Unique transaction ID',
    contract_number VARCHAR(255) COMMENT 'Links to rental contracts',
    tag_id VARCHAR(255) NOT NULL COMMENT 'Links to api_items.tag_id',
    scan_type VARCHAR(50) NOT NULL COMMENT 'Transaction type (scan, update, etc.)',
    scan_date DATETIME NOT NULL COMMENT 'Transaction timestamp',
    client_name VARCHAR(255) COMMENT 'Customer name',
    common_name VARCHAR(255) NOT NULL COMMENT 'Equipment name',
    bin_location VARCHAR(255) COMMENT 'Location at scan time',
    status VARCHAR(50) COMMENT 'Status at scan time',
    scan_by VARCHAR(255) COMMENT 'User who performed scan',
    location_of_repair VARCHAR(255) COMMENT 'Repair location if applicable',
    quality VARCHAR(50) COMMENT 'Quality assessment',

    -- Condition assessment flags (matching current schema)
    dirty_or_mud BOOLEAN DEFAULT FALSE COMMENT 'Dirty or muddy condition',
    leaves BOOLEAN DEFAULT FALSE COMMENT 'Has leaves/debris',
    oil BOOLEAN DEFAULT FALSE COMMENT 'Oil stains present',
    mold BOOLEAN DEFAULT FALSE COMMENT 'Mold detected',
    stain BOOLEAN DEFAULT FALSE COMMENT 'General staining',
    oxidation BOOLEAN DEFAULT FALSE COMMENT 'Rust/oxidation present',
    other TEXT COMMENT 'Other condition notes',
    rip_or_tear BOOLEAN DEFAULT FALSE COMMENT 'Tears or rips detected',
    sewing_repair_needed BOOLEAN DEFAULT FALSE COMMENT 'Sewing repairs needed',
    grommet BOOLEAN DEFAULT FALSE COMMENT 'Grommet issues',
    rope BOOLEAN DEFAULT FALSE COMMENT 'Rope/tie issues',
    buckle BOOLEAN DEFAULT FALSE COMMENT 'Buckle problems',
    wet BOOLEAN DEFAULT FALSE COMMENT 'Item is wet',
    service_required BOOLEAN DEFAULT FALSE COMMENT 'General service required',

    -- Additional fields matching id_transactions
    date_created DATETIME COMMENT 'Transaction creation date',
    date_updated DATETIME COMMENT 'Transaction update date',
    uuid_accounts_fk VARCHAR(255) COMMENT 'Account foreign key',
    serial_number VARCHAR(255) COMMENT 'Item serial number at scan time',
    rental_class_num VARCHAR(255) COMMENT 'Equipment classification at scan time',
    longitude DECIMAL(9,6) COMMENT 'GPS longitude at scan',
    latitude DECIMAL(9,6) COMMENT 'GPS latitude at scan',
    notes TEXT COMMENT 'Transaction-specific notes',

    -- Foreign key and indexes
    FOREIGN KEY (tag_id) REFERENCES api_items(tag_id) ON DELETE CASCADE,
    INDEX ix_api_trans_tag_id (tag_id),
    INDEX ix_api_trans_scan_date (scan_date),
    INDEX ix_api_trans_status (status),
    INDEX ix_api_trans_scan_type (scan_type),
    INDEX ix_api_trans_contract (contract_number)
) ENGINE=InnoDB COMMENT='Transaction/scan history - mirrors id_transactions';

-- ============================================================================
-- 3. EQUIPMENT MASTER (Replaces seed_rental_classes with POS data)
-- ============================================================================
CREATE TABLE api_equipment (
    item_num VARCHAR(50) PRIMARY KEY COMMENT 'POS item_num (normalized, no .0 suffix)',
    pos_item_num VARCHAR(50) UNIQUE COMMENT 'Original POS format (e.g., "12345.0")',
    key_field VARCHAR(50) COMMENT 'Secondary key from POS',
    name VARCHAR(255) COMMENT 'Equipment name/description',
    loc VARCHAR(100) COMMENT 'Location code',
    category VARCHAR(100) COMMENT 'Equipment category',
    department VARCHAR(100) COMMENT 'Department assignment',
    type_desc VARCHAR(100) COMMENT 'Type description',
    qty INTEGER DEFAULT 0 COMMENT 'Available quantity',
    home_store VARCHAR(10) COMMENT 'Default store location',
    current_store VARCHAR(10) COMMENT 'Current store location',
    group_field VARCHAR(100) COMMENT 'Group classification',
    manf VARCHAR(100) COMMENT 'Manufacturer',
    model_no VARCHAR(100) COMMENT 'Model number',
    serial_no VARCHAR(100) COMMENT 'Serial number',
    part_no VARCHAR(100) COMMENT 'Part number',
    license_no VARCHAR(50) COMMENT 'License number',
    model_year VARCHAR(10) COMMENT 'Model year',

    -- Financial fields from POS system
    to_mtd DECIMAL(12,2) DEFAULT 0 COMMENT 'Month-to-date turnover',
    to_ytd DECIMAL(12,2) DEFAULT 0 COMMENT 'Year-to-date turnover',
    to_ltd DECIMAL(12,2) DEFAULT 0 COMMENT 'Lifetime turnover',
    repair_cost_mtd DECIMAL(10,2) DEFAULT 0 COMMENT 'Month-to-date repair costs',
    repair_cost_ltd DECIMAL(10,2) DEFAULT 0 COMMENT 'Lifetime repair costs',
    sell_price DECIMAL(10,2) DEFAULT 0 COMMENT 'Sale price',
    retail_price DECIMAL(10,2) DEFAULT 0 COMMENT 'Retail/rental price',
    deposit DECIMAL(10,2) DEFAULT 0 COMMENT 'Required deposit',
    damage_waiver_percent DECIMAL(5,2) DEFAULT 0 COMMENT 'Damage waiver percentage',

    -- Rental rate structure (first 5 periods for API)
    period_1 DECIMAL(10,2) COMMENT 'Rental period 1 rate',
    period_2 DECIMAL(10,2) COMMENT 'Rental period 2 rate',
    period_3 DECIMAL(10,2) COMMENT 'Rental period 3 rate',
    period_4 DECIMAL(10,2) COMMENT 'Rental period 4 rate',
    period_5 DECIMAL(10,2) COMMENT 'Rental period 5 rate',
    rate_1 DECIMAL(10,2) COMMENT 'Rate 1',
    rate_2 DECIMAL(10,2) COMMENT 'Rate 2',
    rate_3 DECIMAL(10,2) COMMENT 'Rate 3',
    rate_4 DECIMAL(10,2) COMMENT 'Rate 4',
    rate_5 DECIMAL(10,2) COMMENT 'Rate 5',

    -- Inventory management
    reorder_min INTEGER DEFAULT 0 COMMENT 'Minimum reorder quantity',
    reorder_max INTEGER DEFAULT 0 COMMENT 'Maximum reorder quantity',
    user_defined_1 VARCHAR(100) COMMENT 'Custom field 1',
    user_defined_2 VARCHAR(100) COMMENT 'Custom field 2',

    -- Purchase/vendor information
    last_purchase_date DATE COMMENT 'Last purchase date',
    last_purchase_price DECIMAL(10,2) COMMENT 'Last purchase price',
    vendor_no_1 VARCHAR(50) COMMENT 'Primary vendor number',
    vendor_no_2 VARCHAR(50) COMMENT 'Secondary vendor number',
    vendor_no_3 VARCHAR(50) COMMENT 'Tertiary vendor number',

    -- Status and metadata
    inactive BOOLEAN DEFAULT FALSE COMMENT 'Item is inactive',
    weight DECIMAL(10,3) COMMENT 'Item weight',
    setup_time DECIMAL(10,2) COMMENT 'Setup time required',
    non_taxable BOOLEAN DEFAULT FALSE COMMENT 'Tax exempt status',

    -- API-specific metadata
    rfid_rental_class_num VARCHAR(255) COMMENT 'Linked RFID classification',
    identifier_type ENUM('RFID', 'Sticker', 'QR', 'Barcode', 'Bulk', 'None') DEFAULT 'None',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Indexes for performance
    INDEX ix_api_equip_category (category),
    INDEX ix_api_equip_department (department),
    INDEX ix_api_equip_store (current_store),
    INDEX ix_api_equip_inactive (inactive),
    INDEX ix_api_equip_rfid_class (rfid_rental_class_num)
) ENGINE=InnoDB COMMENT='Equipment master - replaces seed_rental_classes with POS data';

-- ============================================================================
-- 4. CORRELATION TABLE (Critical bridge between RFID and POS)
-- ============================================================================
CREATE TABLE api_correlations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pos_item_num VARCHAR(50) NOT NULL COMMENT 'Original POS format (e.g., "12345.0")',
    normalized_item_num VARCHAR(50) NOT NULL COMMENT 'Normalized format (e.g., "12345")',
    rfid_rental_class_num VARCHAR(50) NOT NULL COMMENT 'Links to api_items.rental_class_num',
    pos_equipment_name VARCHAR(500) COMMENT 'POS equipment name',
    rfid_common_name VARCHAR(500) COMMENT 'RFID common name',
    rfid_tag_count INT DEFAULT 0 COMMENT 'Number of RFID tags for this class',
    confidence_score DECIMAL(5,2) DEFAULT 100.00 COMMENT 'Correlation confidence (0-100)',
    correlation_type VARCHAR(30) DEFAULT 'exact_match' COMMENT 'Type of correlation',
    seed_class_id VARCHAR(50) COMMENT 'Legacy seed_rental_classes ID',
    seed_category VARCHAR(200) COMMENT 'Legacy seed category',
    seed_subcategory VARCHAR(200) COMMENT 'Legacy seed subcategory',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    -- Foreign keys and indexes
    INDEX ix_api_corr_pos_item (pos_item_num),
    INDEX ix_api_corr_normalized (normalized_item_num),
    INDEX ix_api_corr_rfid_class (rfid_rental_class_num),
    INDEX ix_api_corr_confidence (confidence_score),
    UNIQUE KEY uk_pos_rfid (pos_item_num, rfid_rental_class_num)
) ENGINE=InnoDB COMMENT='RFID-POS correlation mapping - replaces equipment_rfid_correlations';

-- ============================================================================
-- 5. API USERS TABLE (for authentication)
-- ============================================================================
CREATE TABLE api_users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL COMMENT 'API username',
    password_hash VARCHAR(255) NOT NULL COMMENT 'Bcrypt password hash',
    api_key VARCHAR(255) UNIQUE COMMENT 'API key for token auth',
    role ENUM('admin', 'operator', 'readonly') DEFAULT 'operator' COMMENT 'User role',
    active BOOLEAN DEFAULT TRUE COMMENT 'User is active',
    last_login DATETIME COMMENT 'Last login timestamp',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX ix_api_users_username (username),
    INDEX ix_api_users_api_key (api_key),
    INDEX ix_api_users_active (active)
) ENGINE=InnoDB COMMENT='API authentication and authorization';

-- ============================================================================
-- 6. API SYNC LOG (for RFIDpro manual sync tracking)
-- ============================================================================
CREATE TABLE api_sync_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sync_type ENUM('manual', 'scheduled') NOT NULL COMMENT 'Type of sync operation',
    source_system VARCHAR(50) NOT NULL COMMENT 'Source system (e.g., RFIDpro)',
    table_name VARCHAR(50) NOT NULL COMMENT 'Target table synchronized',
    records_processed INT DEFAULT 0 COMMENT 'Number of records processed',
    records_inserted INT DEFAULT 0 COMMENT 'New records inserted',
    records_updated INT DEFAULT 0 COMMENT 'Existing records updated',
    records_failed INT DEFAULT 0 COMMENT 'Failed record count',
    sync_status ENUM('running', 'completed', 'failed') DEFAULT 'running',
    error_message TEXT COMMENT 'Error details if sync failed',
    started_by VARCHAR(100) COMMENT 'User who initiated sync',
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME COMMENT 'Sync completion timestamp',

    INDEX ix_sync_log_type (sync_type),
    INDEX ix_sync_log_status (sync_status),
    INDEX ix_sync_log_started_at (started_at)
) ENGINE=InnoDB COMMENT='Sync operation tracking for external data sources';

-- ============================================================================
-- 7. INITIAL DATA AND CONFIGURATION
-- ============================================================================

-- Insert default API user
INSERT INTO api_users (username, password_hash, api_key, role) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXwtO0S9oeA2', 'rfid_api_dev_key_2025', 'admin'),
('executive_system', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXwtO0S9oeA2', 'executive_readonly_key', 'readonly'),
('operations_user', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdXwtO0S9oeA2', 'operations_write_key', 'operator');

-- Create initial sync log entry
INSERT INTO api_sync_log (sync_type, source_system, table_name, sync_status, started_by) VALUES
('manual', 'initial_setup', 'database_creation', 'completed', 'system');

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify table creation
SELECT
    TABLE_NAME,
    TABLE_ROWS,
    TABLE_COMMENT
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = 'rfid_api_v1'
ORDER BY TABLE_NAME;

-- Verify indexes
SELECT
    TABLE_NAME,
    INDEX_NAME,
    COLUMN_NAME,
    INDEX_TYPE
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = 'rfid_api_v1'
ORDER BY TABLE_NAME, INDEX_NAME;

-- Show database size
SELECT
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 1) AS 'Database Size (MB)'
FROM information_schema.tables
WHERE table_schema = 'rfid_api_v1';

COMMIT;