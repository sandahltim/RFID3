-- POS Schema Enhancement - Step 4: Complex Data and Tracking

-- Complex data (JSON)
ALTER TABLE id_item_master
ADD COLUMN IF NOT EXISTS rental_rates JSON COMMENT 'Rental rates structure',
ADD COLUMN IF NOT EXISTS vendor_ids JSON COMMENT 'Vendor relationships',
ADD COLUMN IF NOT EXISTS order_nos JSON COMMENT 'Purchase order numbers',
ADD COLUMN IF NOT EXISTS tag_history JSON COMMENT 'Tag transition history';

-- Meter/usage tracking
ALTER TABLE id_item_master
ADD COLUMN IF NOT EXISTS meter_out DECIMAL(10,2) COMMENT 'Meter reading when item goes out',
ADD COLUMN IF NOT EXISTS meter_in DECIMAL(10,2) COMMENT 'Meter reading when item comes in';

-- Data source tracking
ALTER TABLE id_item_master
ADD COLUMN IF NOT EXISTS data_source VARCHAR(20) DEFAULT 'RFID_API' COMMENT 'Source of data',
ADD COLUMN IF NOT EXISTS pos_last_updated DATETIME COMMENT 'Last update from POS data import',
ADD COLUMN IF NOT EXISTS created_by VARCHAR(20) DEFAULT 'SYSTEM' COMMENT 'Who/what created this record';