-- DATABASE EXPANSION PLAN: Add ALL Missing CSV Columns
-- Date: 2025-09-18
-- Critical Issue: 54% data loss in pos_equipment table

-- ============================================================================
-- EXPAND pos_equipment TABLE: Add 92 Missing Columns from equipPOS CSV
-- ============================================================================

-- Current table has 79 columns, CSV has 171 columns = 92 missing columns

USE rfid_inventory;

-- Add missing pricing and rental structure columns
ALTER TABLE pos_equipment
ADD COLUMN qyot INT COMMENT 'QYOT - Quantity on order',
ADD COLUMN sell_price DECIMAL(10,2) COMMENT 'SELL - Selling price',
ADD COLUMN dep_price DECIMAL(10,2) COMMENT 'DEP - Deposit required',
ADD COLUMN dmg_waiver DECIMAL(10,2) COMMENT 'DMG - Damage waiver fee',
ADD COLUMN msg VARCHAR(255) COMMENT 'Msg - Message/notes',
ADD COLUMN sdate DATE COMMENT 'SDATE - Service date',
ADD COLUMN tax_code VARCHAR(50) COMMENT 'TaxCode - Tax classification',
ADD COLUMN inst VARCHAR(255) COMMENT 'INST - Installation notes',
ADD COLUMN fuel VARCHAR(255) COMMENT 'FUEL - Fuel requirements',
ADD COLUMN addt TEXT COMMENT 'ADDT - Additional details';

-- Add rental periods (PER1-PER10) - NEED VERIFICATION OF MEANING
ALTER TABLE pos_equipment
ADD COLUMN per1 DECIMAL(10,2) COMMENT 'PER1 - Rental period 1 (need clarification)',
ADD COLUMN per2 DECIMAL(10,2) COMMENT 'PER2 - Rental period 2',
ADD COLUMN per3 DECIMAL(10,2) COMMENT 'PER3 - Rental period 3',
ADD COLUMN per4 DECIMAL(10,2) COMMENT 'PER4 - Rental period 4',
ADD COLUMN per5 DECIMAL(10,2) COMMENT 'PER5 - Rental period 5',
ADD COLUMN per6 DECIMAL(10,2) COMMENT 'PER6 - Rental period 6',
ADD COLUMN per7 DECIMAL(10,2) COMMENT 'PER7 - Rental period 7',
ADD COLUMN per8 DECIMAL(10,2) COMMENT 'PER8 - Rental period 8',
ADD COLUMN per9 DECIMAL(10,2) COMMENT 'PER9 - Rental period 9',
ADD COLUMN per10 DECIMAL(10,2) COMMENT 'PER10 - Rental period 10';

-- Add rental rates (RATE1-RATE10) - NEED VERIFICATION OF MEANING
ALTER TABLE pos_equipment
ADD COLUMN rate1 DECIMAL(10,2) COMMENT 'RATE1 - Rate 1 (need clarification)',
ADD COLUMN rate2 DECIMAL(10,2) COMMENT 'RATE2 - Rate 2',
ADD COLUMN rate3 DECIMAL(10,2) COMMENT 'RATE3 - Rate 3',
ADD COLUMN rate4 DECIMAL(10,2) COMMENT 'RATE4 - Rate 4',
ADD COLUMN rate5 DECIMAL(10,2) COMMENT 'RATE5 - Rate 5',
ADD COLUMN rate6 DECIMAL(10,2) COMMENT 'RATE6 - Rate 6',
ADD COLUMN rate7 DECIMAL(10,2) COMMENT 'RATE7 - Rate 7',
ADD COLUMN rate8 DECIMAL(10,2) COMMENT 'RATE8 - Rate 8',
ADD COLUMN rate9 DECIMAL(10,2) COMMENT 'RATE9 - Rate 9',
ADD COLUMN rate10 DECIMAL(10,2) COMMENT 'RATE10 - Rate 10';

-- Add equipment details and codes
ALTER TABLE pos_equipment
ADD COLUMN rcod VARCHAR(50) COMMENT 'RCOD - Rental code',
ADD COLUMN subr VARCHAR(50) COMMENT 'SUBR - Subrent information',
ADD COLUMN num_field VARCHAR(50) COMMENT 'NUM - Number field',
ADD COLUMN dstn VARCHAR(255) COMMENT 'DSTN - Description',
ADD COLUMN dstp VARCHAR(255) COMMENT 'DSTP - Description part',
ADD COLUMN rmin INT COMMENT 'RMIN - Reorder minimum',
ADD COLUMN rmax INT COMMENT 'RMAX - Reorder maximum',
ADD COLUMN user_defined_1 VARCHAR(255) COMMENT 'UserDefined1 - Custom field 1',
ADD COLUMN user_defined_2 VARCHAR(255) COMMENT 'UserDefined2 - Custom field 2';

-- NEED TO ADD 70+ MORE COLUMNS AFTER VERIFICATION
-- This is just the first batch to demonstrate the scope

-- ============================================================================
-- VERIFICATION QUERY: Check column count after expansion
-- ============================================================================
SELECT COUNT(*) as total_columns
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'pos_equipment'
AND TABLE_SCHEMA = 'rfid_inventory';

-- Should show 79 + added columns moving toward 171 total