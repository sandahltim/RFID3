-- Migration: Add hand_counted_name field to hand_counted_catalog table
-- Date: 2025-08-25
-- Purpose: Allow custom display names for hand counted items in manage categories

USE rfid3;

-- Add the hand_counted_name column
ALTER TABLE hand_counted_catalog 
ADD COLUMN hand_counted_name VARCHAR(255) NULL 
COMMENT 'Custom display name for hand counted items, overrides item_name when present';

-- Add index for better performance when searching by hand counted name
CREATE INDEX idx_hand_counted_catalog_hand_counted_name 
ON hand_counted_catalog(hand_counted_name);

-- Log the migration
INSERT INTO migration_log (script_name, executed_at, description) 
VALUES ('add_hand_counted_name.sql', NOW(), 'Added hand_counted_name field to hand_counted_catalog table')
ON DUPLICATE KEY UPDATE executed_at = NOW();

SELECT 'Hand counted name field added successfully' AS result;