-- Complete pos_equipment table with professional naming
-- All 171 columns from equipPOS CSV with proper conventions

USE rfid_inventory;

-- Clean approach: ALTER existing table with remaining columns
-- Using proper snake_case naming conventions

ALTER TABLE pos_equipment
ADD COLUMN qyot INT COMMENT 'Quantity on order',
ADD COLUMN dep DECIMAL(10,2) COMMENT 'Deposit amount',
ADD COLUMN dmg DECIMAL(10,2) COMMENT 'Damage waiver',
ADD COLUMN msg TEXT COMMENT 'Internal message',
ADD COLUMN sdate DATE COMMENT 'Service date',
ADD COLUMN tax_code VARCHAR(50) COMMENT 'Tax code',
ADD COLUMN inst TEXT COMMENT 'Instructions',
ADD COLUMN fuel VARCHAR(100) COMMENT 'Fuel requirements',
ADD COLUMN addt TEXT COMMENT 'Additional details',

-- Rental structure
ADD COLUMN per1 DECIMAL(10,2) COMMENT 'Period 1 hours',
ADD COLUMN per2 DECIMAL(10,2) COMMENT 'Period 2 hours',
ADD COLUMN per3 DECIMAL(10,2) COMMENT 'Period 3 hours',
ADD COLUMN per4 DECIMAL(10,2) COMMENT 'Period 4 hours',
ADD COLUMN per5 DECIMAL(10,2) COMMENT 'Period 5 hours',
ADD COLUMN per6 DECIMAL(10,2) COMMENT 'Period 6 hours',
ADD COLUMN per7 DECIMAL(10,2) COMMENT 'Period 7 hours',
ADD COLUMN per8 DECIMAL(10,2) COMMENT 'Period 8 hours',
ADD COLUMN per9 DECIMAL(10,2) COMMENT 'Period 9 hours',
ADD COLUMN per10 DECIMAL(10,2) COMMENT 'Period 10 hours',

-- Rates
ADD COLUMN rate1 DECIMAL(10,2) COMMENT 'Rate 1',
ADD COLUMN rate2 DECIMAL(10,2) COMMENT 'Rate 2',
ADD COLUMN rate3 DECIMAL(10,2) COMMENT 'Rate 3',
ADD COLUMN rate4 DECIMAL(10,2) COMMENT 'Rate 4',
ADD COLUMN rate5 DECIMAL(10,2) COMMENT 'Rate 5',
ADD COLUMN rate6 DECIMAL(10,2) COMMENT 'Rate 6',
ADD COLUMN rate7 DECIMAL(10,2) COMMENT 'Rate 7',
ADD COLUMN rate8 DECIMAL(10,2) COMMENT 'Rate 8',
ADD COLUMN rate9 DECIMAL(10,2) COMMENT 'Rate 9',
ADD COLUMN rate10 DECIMAL(10,2) COMMENT 'Rate 10',

-- Equipment details
ADD COLUMN rcod VARCHAR(50) COMMENT 'Rental code',
ADD COLUMN subr DECIMAL(10,2) COMMENT 'Subrent amount',
ADD COLUMN num VARCHAR(50) COMMENT 'Number field',
ADD COLUMN dstn VARCHAR(255) COMMENT 'Description',
ADD COLUMN dstp VARCHAR(255) COMMENT 'Description part';

-- Verify
SELECT COUNT(*) as total_columns FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'pos_equipment' AND TABLE_SCHEMA = 'rfid_inventory';