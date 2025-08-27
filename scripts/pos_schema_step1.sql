-- POS Schema Enhancement - Step 1: Core Identification Fields
-- Execute in smaller batches to avoid MySQL statement limits

-- Core identification fields
ALTER TABLE id_item_master 
ADD COLUMN IF NOT EXISTS identifier_type ENUM('RFID','Sticker','QR','Barcode','Bulk','None') DEFAULT 'None' COMMENT 'Type of identifier on physical item',
ADD COLUMN IF NOT EXISTS identifier_value VARCHAR(255) COMMENT 'Value of non-RFID identifier',
ADD COLUMN IF NOT EXISTS is_bulk BOOLEAN DEFAULT FALSE COMMENT 'True for bulk/quantity items';

-- POS categorization fields  
ALTER TABLE id_item_master
ADD COLUMN IF NOT EXISTS department VARCHAR(100) COMMENT 'POS Department categorization',
ADD COLUMN IF NOT EXISTS type_desc VARCHAR(50) COMMENT 'POS Type Description',
ADD COLUMN IF NOT EXISTS manufacturer VARCHAR(100) COMMENT 'Equipment manufacturer',
ADD COLUMN IF NOT EXISTS model_no VARCHAR(50) COMMENT 'Model number',
ADD COLUMN IF NOT EXISTS part_no VARCHAR(50) COMMENT 'Part number',
ADD COLUMN IF NOT EXISTS alt_key VARCHAR(50) COMMENT 'Alternative POS key/reference';