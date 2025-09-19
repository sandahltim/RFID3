-- Raw CSV Import Tables - Professional Architecture
-- Date: 2025-09-18
-- Purpose: Raw data preservation with business transformation layer

USE rfid_inventory;

-- ============================================================================
-- Raw Equipment Table (171 columns from equipPOS CSV)
-- ============================================================================
CREATE TABLE equipment_csv_raw (
    id INT PRIMARY KEY AUTO_INCREMENT,
    import_batch_id VARCHAR(50) NOT NULL,
    import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_file VARCHAR(255) NOT NULL,

    -- Core equipment fields (exact CSV structure)
    equipment_key VARCHAR(50) COMMENT 'KEY - Equipment identifier',
    name VARCHAR(500) COMMENT 'Name - Equipment name',
    location_code VARCHAR(50) COMMENT 'LOC - Location code',
    quantity VARCHAR(20) COMMENT 'QTY - Available quantity',
    quantity_on_order VARCHAR(20) COMMENT 'QYOT - Quantity on order',
    sell_price VARCHAR(20) COMMENT 'SELL - Selling price',
    deposit VARCHAR(20) COMMENT 'DEP - Deposit amount',
    damage_waiver VARCHAR(20) COMMENT 'DMG - Damage waiver',
    message_text TEXT COMMENT 'Msg - Message field',
    service_date VARCHAR(50) COMMENT 'SDATE - Service date',
    category VARCHAR(100) COMMENT 'Category - Equipment category',
    type_desc VARCHAR(100) COMMENT 'TYPE - Type description',
    tax_code VARCHAR(50) COMMENT 'TaxCode - Tax classification',
    instructions TEXT COMMENT 'INST - Instructions',
    fuel VARCHAR(255) COMMENT 'FUEL - Fuel requirements',
    additional TEXT COMMENT 'ADDT - Additional details',

    -- Rental periods
    per1 VARCHAR(20) COMMENT 'PER1 - Period 1',
    per2 VARCHAR(20) COMMENT 'PER2 - Period 2',
    per3 VARCHAR(20) COMMENT 'PER3 - Period 3',
    per4 VARCHAR(20) COMMENT 'PER4 - Period 4',
    per5 VARCHAR(20) COMMENT 'PER5 - Period 5',

    -- Rental rates
    rate1 VARCHAR(20) COMMENT 'RATE1 - Rate 1',
    rate2 VARCHAR(20) COMMENT 'RATE2 - Rate 2',
    rate3 VARCHAR(20) COMMENT 'RATE3 - Rate 3',
    rate4 VARCHAR(20) COMMENT 'RATE4 - Rate 4',
    rate5 VARCHAR(20) COMMENT 'RATE5 - Rate 5',

    -- Manufacturer details
    manufacturer VARCHAR(100) COMMENT 'MANF - Manufacturer',
    model_number VARCHAR(100) COMMENT 'MODN - Model number',
    part_number VARCHAR(100) COMMENT 'PartNumber - Part number',

    -- Import tracking
    import_status ENUM('pending', 'processed', 'error') DEFAULT 'pending',
    processed_at TIMESTAMP NULL,

    -- Indexes
    INDEX idx_batch (import_batch_id),
    INDEX idx_equipment_key (equipment_key),
    INDEX idx_status (import_status)

) ENGINE=InnoDB COMMENT='Raw equipment CSV data';

-- ============================================================================
-- Raw Customer Table (108 columns from customer CSV)
-- ============================================================================
CREATE TABLE customers_csv_raw (
    id INT PRIMARY KEY AUTO_INCREMENT,
    import_batch_id VARCHAR(50) NOT NULL,
    import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_file VARCHAR(255) NOT NULL,

    -- Core customer fields
    customer_key VARCHAR(50) COMMENT 'KEY - Customer key',
    customer_name VARCHAR(255) COMMENT 'NAME - Customer name',
    cnum VARCHAR(50) COMMENT 'CNUM - Customer number',
    address VARCHAR(255) COMMENT 'Address - Street address',
    city VARCHAR(100) COMMENT 'CITY - City',
    zip VARCHAR(20) COMMENT 'ZIP - Zip code',
    phone VARCHAR(50) COMMENT 'Phone - Primary phone',
    email VARCHAR(255) COMMENT 'Email - Email address',

    -- Import tracking
    import_status ENUM('pending', 'processed', 'error') DEFAULT 'pending',
    processed_at TIMESTAMP NULL,

    INDEX idx_batch (import_batch_id),
    INDEX idx_customer_key (customer_key),
    INDEX idx_cnum (cnum)

) ENGINE=InnoDB COMMENT='Raw customer CSV data';

-- ============================================================================
-- Raw Transactions Table (119 columns from transactions CSV)
-- ============================================================================
CREATE TABLE transactions_csv_raw (
    id INT PRIMARY KEY AUTO_INCREMENT,
    import_batch_id VARCHAR(50) NOT NULL,
    import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_file VARCHAR(255) NOT NULL,

    -- Core transaction fields
    contract_number VARCHAR(50) COMMENT 'CNTR - Contract number',
    transaction_date VARCHAR(50) COMMENT 'DATE - Transaction date',
    customer_number VARCHAR(50) COMMENT 'CUSN - Customer number',
    store_number VARCHAR(10) COMMENT 'STR - Store number',

    -- Import tracking
    import_status ENUM('pending', 'processed', 'error') DEFAULT 'pending',
    processed_at TIMESTAMP NULL,

    INDEX idx_batch (import_batch_id),
    INDEX idx_contract (contract_number),
    INDEX idx_customer (customer_number)

) ENGINE=InnoDB COMMENT='Raw transactions CSV data';

-- Verify table creation
SELECT
    table_name,
    table_comment,
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = t.table_name) as columns
FROM information_schema.tables t
WHERE table_schema = 'rfid_inventory'
AND table_name LIKE '%_csv_raw';