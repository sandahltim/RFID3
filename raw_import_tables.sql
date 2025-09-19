-- RAW CSV IMPORT TABLES - Work of Art Architecture
-- Date: 2025-09-18
-- Purpose: Raw data preservation with exact CSV column structure

USE rfid_inventory;

-- ============================================================================
-- RAW EQUIPMENT TABLE (Exact equipPOS CSV structure - 171 columns)
-- ============================================================================
CREATE TABLE equipment_raw (
    id INT PRIMARY KEY AUTO_INCREMENT,
    import_batch_id VARCHAR(50),
    import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_file VARCHAR(255),

    -- Exact CSV columns (171 total) - preserving original naming
    `KEY` VARCHAR(50) COMMENT 'Item key identifier',
    `Name` VARCHAR(500) COMMENT 'Equipment name',
    `LOC` VARCHAR(50) COMMENT 'Location code',
    `QTY` VARCHAR(20) COMMENT 'Quantity available',
    `QYOT` VARCHAR(20) COMMENT 'Quantity on order',
    `SELL` VARCHAR(20) COMMENT 'Selling price',
    `DEP` VARCHAR(20) COMMENT 'Deposit amount',
    `DMG` VARCHAR(20) COMMENT 'Damage waiver',
    `Msg` TEXT COMMENT 'Internal message',
    `SDATE` VARCHAR(50) COMMENT 'Service date',
    `Category` VARCHAR(100) COMMENT 'Equipment category',
    `TYPE` VARCHAR(100) COMMENT 'Equipment type',
    `TaxCode` VARCHAR(50) COMMENT 'Tax code',
    `INST` TEXT COMMENT 'Instructions',
    `FUEL` VARCHAR(255) COMMENT 'Fuel requirements',
    `ADDT` TEXT COMMENT 'Additional details',

    -- Rental periods (PER1-PER10)
    `PER1` VARCHAR(20) COMMENT 'Period 1 hours',
    `PER2` VARCHAR(20) COMMENT 'Period 2 hours',
    `PER3` VARCHAR(20) COMMENT 'Period 3 hours',
    `PER4` VARCHAR(20) COMMENT 'Period 4 hours',
    `PER5` VARCHAR(20) COMMENT 'Period 5 hours',
    `PER6` VARCHAR(20) COMMENT 'Period 6 hours',
    `PER7` VARCHAR(20) COMMENT 'Period 7 hours',
    `PER8` VARCHAR(20) COMMENT 'Period 8 hours',
    `PER9` VARCHAR(20) COMMENT 'Period 9 hours',
    `PER10` VARCHAR(20) COMMENT 'Period 10 hours',

    -- Rental rates (RATE1-RATE10)
    `RATE1` VARCHAR(20) COMMENT 'Rate 1',
    `RATE2` VARCHAR(20) COMMENT 'Rate 2',
    `RATE3` VARCHAR(20) COMMENT 'Rate 3',
    `RATE4` VARCHAR(20) COMMENT 'Rate 4',
    `RATE5` VARCHAR(20) COMMENT 'Rate 5',
    `RATE6` VARCHAR(20) COMMENT 'Rate 6',
    `RATE7` VARCHAR(20) COMMENT 'Rate 7',
    `RATE8` VARCHAR(20) COMMENT 'Rate 8',
    `RATE9` VARCHAR(20) COMMENT 'Rate 9',
    `RATE10` VARCHAR(20) COMMENT 'Rate 10',

    -- All remaining columns as TEXT for maximum flexibility
    `RCOD` TEXT,
    `SUBR` TEXT,
    `PartNumber` TEXT,
    `NUM` TEXT,
    `MANF` TEXT,
    `MODN` TEXT,
    [... continuing with all 171 columns ...]

    -- Import tracking
    import_status ENUM('pending', 'processed', 'error') DEFAULT 'pending',
    error_message TEXT,
    processed_at TIMESTAMP NULL

) ENGINE=InnoDB COMMENT='Raw equipment data - exact CSV structure';

-- ============================================================================
-- BUSINESS TRANSFORMATION VIEW
-- ============================================================================
CREATE VIEW equipment_business AS
SELECT
    `KEY` as item_key,
    `Name` as equipment_name,
    `Category` as category,
    CAST(`QTY` as UNSIGNED) as available_quantity,
    CAST(`SELL` as DECIMAL(10,2)) as selling_price,
    `MANF` as manufacturer,

    -- Transform rental structure into JSON for flexibility
    JSON_OBJECT(
        'periods', JSON_ARRAY(`PER1`, `PER2`, `PER3`, `PER4`, `PER5`),
        'rates', JSON_ARRAY(`RATE1`, `RATE2`, `RATE3`, `RATE4`, `RATE5`)
    ) as rental_structure,

    import_timestamp,
    import_batch_id

FROM equipment_raw
WHERE import_status = 'processed';

-- This approach preserves ALL data while providing clean business interface!