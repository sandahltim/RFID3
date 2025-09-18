-- Complete All POS Tables - Final Clean Version
-- Date: 2025-09-18
-- Purpose: Complete all table schemas for zero data loss

USE rfid_inventory;

-- ============================================================================
-- Create new pos_transitems table (if not exists)
-- ============================================================================
CREATE TABLE IF NOT EXISTS pos_transitems_complete (
    id INT PRIMARY KEY AUTO_INCREMENT,
    contract_number VARCHAR(100) COMMENT 'CNTR - Contract number',
    sub_field VARCHAR(100) COMMENT 'SUBF - Sub field',
    item_number VARCHAR(100) COMMENT 'ITEM - Item number',
    quantity INT COMMENT 'QTY - Quantity',
    hrsc_field VARCHAR(100) COMMENT 'HRSC - Hours field',
    ddt_field VARCHAR(100) COMMENT 'DDT - DDT field',
    dtm_field TIME COMMENT 'DTM - Time field',
    txty_field VARCHAR(100) COMMENT 'TXTY - Transaction type',
    price_field DECIMAL(12,2) COMMENT 'PRIC - Price',
    description_field TEXT COMMENT 'Desc - Description (avoiding reserved word)',
    comments_field TEXT COMMENT 'Comments - Comments',
    damage_waiver DECIMAL(12,2) COMMENT 'DmgWvr - Damage waiver',
    item_percentage DECIMAL(12,2) COMMENT 'ItemPercentage - Item percentage',
    discount_percent DECIMAL(12,2) COMMENT 'DiscountPercent - Discount percentage',
    non_taxable BOOLEAN COMMENT 'Nontaxable - Non-taxable flag',
    non_discount BOOLEAN COMMENT 'Nondiscount - Non-discount flag',
    letter_sent VARCHAR(100) COMMENT 'LetterSent - Letter sent',
    sort_order INT COMMENT 'Sort - Sort order',
    discount_amount DECIMAL(12,2) COMMENT 'DiscountAmount - Discount amount',
    daily_amount DECIMAL(12,2) COMMENT 'DailyAmount - Daily rate',
    weekly_amount DECIMAL(12,2) COMMENT 'WeeklyAmount - Weekly rate',
    monthly_amount DECIMAL(12,2) COMMENT 'MonthlyAmount - Monthly rate',
    minimum_amount DECIMAL(12,2) COMMENT 'MinimumAmount - Minimum rate',
    reading_out VARCHAR(100) COMMENT 'ReadingOut - Meter reading out',
    reading_in VARCHAR(100) COMMENT 'ReadingIn - Meter reading in',
    rain_hours INT COMMENT 'RainHours - Rain hours',
    last_modified DATETIME COMMENT 'LastModified - Last modification',
    retail_price DECIMAL(12,2) COMMENT 'RetailPrice - Retail price',
    kit_field VARCHAR(100) COMMENT 'KitField - Kit reference',
    confirmed_date DATE COMMENT 'ConfirmedDate - Confirmation date',
    subrent_quantity DECIMAL(12,2) COMMENT 'SubrentQuantity - Subrent quantity',
    sub_status VARCHAR(100) COMMENT 'Substatus - Sub status',
    contract_link VARCHAR(255) COMMENT 'ContractLink - Contract link',
    line_number INT COMMENT 'LineNumber - Line number',
    rate_engine_id VARCHAR(100) COMMENT 'RateEngineId - Rate engine ID',
    base_rate DECIMAL(12,2) COMMENT 'BaseRate - Base rate',
    logistics_out VARCHAR(100) COMMENT 'LogisticsOUT - Logistics out',
    logistics_in VARCHAR(100) COMMENT 'LogisticsIN - Logistics in',
    archived BOOLEAN COMMENT 'Archived - Archived flag',
    out_date DATE COMMENT 'OutDate - Out date',
    trans_related VARCHAR(100) COMMENT 'TransRelated - Transaction related',
    special_rate_type_id VARCHAR(100) COMMENT 'SpecialRateTypeId - Special rate type',
    tax_amount DECIMAL(12,2) COMMENT 'TaxAmount - Tax amount',
    monthly_rate_date DATE COMMENT 'MonthlyRateDate - Monthly rate date',
    transitems_id VARCHAR(100) COMMENT 'Id - Transitems ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='Complete transitems data - 45 columns from CSV';

-- Verify table creation
SELECT COUNT(*) as transitems_columns
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'pos_transitems_complete';