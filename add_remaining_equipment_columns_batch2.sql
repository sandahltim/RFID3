-- Add Remaining Equipment Columns - Batch 2
-- Fixing massive 95% data loss in pos_equipment table

USE rfid_inventory;

-- Add next 40 missing columns from Excel specification
ALTER TABLE pos_equipment
ADD COLUMN rcod VARCHAR(100) COMMENT 'RCOD - Rental code',
ADD COLUMN subr VARCHAR(100) COMMENT 'SUBR - Subrent information',
ADD COLUMN num_csv VARCHAR(50) COMMENT 'NUM - Item number from CSV',
ADD COLUMN dstn VARCHAR(255) COMMENT 'DSTN - Description',
ADD COLUMN dstp VARCHAR(255) COMMENT 'DSTP - Description part',
ADD COLUMN rmin_csv INT COMMENT 'RMIN - Reorder minimum',
ADD COLUMN rmax_csv INT COMMENT 'RMAX - Reorder maximum',
ADD COLUMN user_defined_1_csv VARCHAR(255) COMMENT 'UserDefined1 - Custom field 1',
ADD COLUMN user_defined_2_csv VARCHAR(255) COMMENT 'UserDefined2 - Custom field 2',
ADD COLUMN mtot VARCHAR(100) COMMENT 'MTOT - Meter total out',
ADD COLUMN mtin VARCHAR(100) COMMENT 'MTIN - Meter total in',
ADD COLUMN call_field VARCHAR(255) COMMENT 'CALL - Call information',
ADD COLUMN resb VARCHAR(255) COMMENT 'RESB - Reserved begin',
ADD COLUMN resd VARCHAR(255) COMMENT 'RESD - Reserved end',
ADD COLUMN queb VARCHAR(255) COMMENT 'QUEB - Queue begin',
ADD COLUMN qued VARCHAR(255) COMMENT 'QUED - Queue end',
ADD COLUMN ssn_field VARCHAR(100) COMMENT 'SSN - Serial service number',
ADD COLUMN cusn VARCHAR(100) COMMENT 'CUSN - Customer number',
ADD COLUMN cntr VARCHAR(100) COMMENT 'CNTR - Counter',
ADD COLUMN purd DATE COMMENT 'PURD - Purchase date',
ADD COLUMN purp DECIMAL(10,2) COMMENT 'PURP - Purchase price',
ADD COLUMN depm VARCHAR(50) COMMENT 'DEPM - Depreciation method',
ADD COLUMN depr DECIMAL(10,2) COMMENT 'DEPR - Depreciation rate',
ADD COLUMN slvg DECIMAL(10,2) COMMENT 'SLVG - Salvage value',
ADD COLUMN depa DECIMAL(10,2) COMMENT 'DEPA - Depreciation amount',
ADD COLUMN depp DECIMAL(10,2) COMMENT 'DEPP - Depreciation percentage',
ADD COLUMN curv DECIMAL(10,2) COMMENT 'CURV - Current value',
ADD COLUMN sold BOOLEAN COMMENT 'SOLD - Sold flag',
ADD COLUMN samt DECIMAL(10,2) COMMENT 'SAMT - Sale amount',
ADD COLUMN inc1 DECIMAL(10,2) COMMENT 'INC1 - Income 1',
ADD COLUMN inc2 DECIMAL(10,2) COMMENT 'INC2 - Income 2',
ADD COLUMN inc3 DECIMAL(10,2) COMMENT 'INC3 - Income 3',
ADD COLUMN repc1 DECIMAL(10,2) COMMENT 'REPC1 - Repair cost 1',
ADD COLUMN repc2 DECIMAL(10,2) COMMENT 'REPC2 - Repair cost 2',
ADD COLUMN tmot1 DECIMAL(10,2) COMMENT 'TMOT1 - Total meter out 1',
ADD COLUMN tmot2 DECIMAL(10,2) COMMENT 'TMOT2 - Total meter out 2',
ADD COLUMN tmot3 DECIMAL(10,2) COMMENT 'TMOT3 - Total meter out 3',
ADD COLUMN hrot1 DECIMAL(10,2) COMMENT 'HROT1 - Hours out 1',
ADD COLUMN hrot2 DECIMAL(10,2) COMMENT 'HROT2 - Hours out 2',
ADD COLUMN hrot3 DECIMAL(10,2) COMMENT 'HROT3 - Hours out 3',
ADD COLUMN ldate DATE COMMENT 'LDATE - Last date';

-- Check progress
SELECT COUNT(*) as column_count_after_batch2
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'pos_equipment'
AND TABLE_SCHEMA = 'rfid_inventory';