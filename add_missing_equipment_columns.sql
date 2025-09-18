-- Add ALL Missing Equipment Columns - Fix 95% Data Loss
-- Date: 2025-09-18
-- CRITICAL: pos_equipment missing 162 of 171 CSV columns

USE rfid_inventory;

-- Backup table before major changes
CREATE TABLE pos_equipment_backup_before_expansion AS SELECT * FROM pos_equipment;

-- Add missing core columns (avoiding duplicates)
ALTER TABLE pos_equipment
ADD COLUMN key_csv VARCHAR(50) COMMENT 'KEY - Item key from CSV',
ADD COLUMN qyot INT COMMENT 'QYOT - Quantity on order',
ADD COLUMN sell_csv DECIMAL(12,2) COMMENT 'SELL - Sell price from CSV',
ADD COLUMN dep DECIMAL(12,2) COMMENT 'DEP - Deposit required',
ADD COLUMN dmg DECIMAL(12,2) COMMENT 'DMG - Damage waiver fee',
ADD COLUMN msg_field VARCHAR(255) COMMENT 'Msg - Internal POS message',
ADD COLUMN sdate DATE COMMENT 'SDATE - Service/sold date',
ADD COLUMN type_csv VARCHAR(100) COMMENT 'TYPE - Type description from CSV',
ADD COLUMN tax_code_csv VARCHAR(50) COMMENT 'TaxCode - Tax classification',
ADD COLUMN inst VARCHAR(255) COMMENT 'INST - Instruction printout code',
ADD COLUMN fuel VARCHAR(255) COMMENT 'FUEL - Fuel charge reference',
ADD COLUMN addt TEXT COMMENT 'ADDT - Additive charge reference';

-- Add rental periods (hours-based per Excel)
ALTER TABLE pos_equipment
ADD COLUMN per1 DECIMAL(10,2) COMMENT 'PER1 - Rental period 1 in hours',
ADD COLUMN per2 DECIMAL(10,2) COMMENT 'PER2 - Rental period 2 in hours',
ADD COLUMN per3 DECIMAL(10,2) COMMENT 'PER3 - Rental period 3 in hours',
ADD COLUMN per4 DECIMAL(10,2) COMMENT 'PER4 - Rental period 4 in hours',
ADD COLUMN per5 DECIMAL(10,2) COMMENT 'PER5 - Rental period 5 in hours',
ADD COLUMN per6 DECIMAL(10,2) COMMENT 'PER6 - Rental period 6 in hours',
ADD COLUMN per7 DECIMAL(10,2) COMMENT 'PER7 - Rental period 7 in hours',
ADD COLUMN per8 DECIMAL(10,2) COMMENT 'PER8 - Rental period 8 in hours',
ADD COLUMN per9 DECIMAL(10,2) COMMENT 'PER9 - Rental period 9 in hours',
ADD COLUMN per10 DECIMAL(10,2) COMMENT 'PER10 - Rental period 10 in hours';

-- Add rental rates (dollar amounts per Excel)
ALTER TABLE pos_equipment
ADD COLUMN rate1 DECIMAL(10,2) COMMENT 'RATE1 - Dollar rate for period 1',
ADD COLUMN rate2 DECIMAL(10,2) COMMENT 'RATE2 - Dollar rate for period 2',
ADD COLUMN rate3 DECIMAL(10,2) COMMENT 'RATE3 - Dollar rate for period 3',
ADD COLUMN rate4 DECIMAL(10,2) COMMENT 'RATE4 - Dollar rate for period 4',
ADD COLUMN rate5 DECIMAL(10,2) COMMENT 'RATE5 - Dollar rate for period 5',
ADD COLUMN rate6 DECIMAL(10,2) COMMENT 'RATE6 - Dollar rate for period 6',
ADD COLUMN rate7 DECIMAL(10,2) COMMENT 'RATE7 - Dollar rate for period 7',
ADD COLUMN rate8 DECIMAL(10,2) COMMENT 'RATE8 - Dollar rate for period 8',
ADD COLUMN rate9 DECIMAL(10,2) COMMENT 'RATE9 - Dollar rate for period 9',
ADD COLUMN rate10 DECIMAL(10,2) COMMENT 'RATE10 - Dollar rate for period 10';

-- Verify column count
SELECT COUNT(*) as total_columns
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'pos_equipment'
AND TABLE_SCHEMA = 'rfid_inventory';

-- This should show progress toward 171 total columns