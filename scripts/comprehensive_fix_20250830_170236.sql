-- ============================================================================
-- COMPREHENSIVE RFID DATA FIX
-- Generated: 2025-08-30 17:02:36
-- ============================================================================

-- Create backup tables
CREATE TABLE IF NOT EXISTS id_item_master_backup_20250830_170236 AS SELECT * FROM id_item_master;
CREATE TABLE IF NOT EXISTS pos_equipment_backup_20250830_170236 AS SELECT * FROM pos_equipment;
CREATE TABLE IF NOT EXISTS store_correlations_backup_20250830_170236 AS SELECT * FROM store_correlations;

-- ============================================================================
-- FIX 1: CORRECT STORE CORRELATIONS
-- ============================================================================

-- Clear and reset store correlations
TRUNCATE TABLE store_correlations;

INSERT INTO store_correlations (rfid_store_code, pos_store_code, store_name, store_location, is_active) VALUES
('8101', '4', 'Fridley RFID Test', 'Fridley, MN', 1),
('3607', '1', 'Wayzata', 'Wayzata, MN', 1),
('6800', '2', 'Brooklyn Park', 'Brooklyn Park, MN', 1),
('728', '3', 'Elk River', 'Elk River, MN', 1),
('000', '0', 'Header/System', 'System Generated', 1);

-- ============================================================================
-- FIX 2: CORRECT RFID ASSIGNMENTS IN ID_ITEM_MASTER
-- ============================================================================

-- Reset all identifier types
UPDATE id_item_master SET identifier_type = 'None';

-- Mark NULL store RFID items and assign to Fridley
UPDATE id_item_master 
SET current_store = '8101',
    identifier_type = 'RFID'
WHERE current_store IS NULL 
    AND rental_class_num IS NOT NULL 
    AND rental_class_num != '';

-- Remove incorrect RFID assignments from other stores
UPDATE id_item_master 
SET identifier_type = 'None'
WHERE identifier_type = 'RFID' 
    AND current_store NOT IN ('8101');

-- ============================================================================
-- FIX 3: CREATE POS-RFID CORRELATIONS
-- ============================================================================

-- Clear existing correlations
TRUNCATE TABLE pos_rfid_correlations;

-- Create correlations for Fridley RFID items
INSERT INTO pos_rfid_correlations (
    pos_item_num,
    pos_item_desc,
    rfid_tag_id,
    rfid_rental_class_num,
    rfid_common_name,
    correlation_type,
    confidence_score,
    is_active,
    created_at,
    created_by
)
SELECT 
    pe.item_num,
    pe.name,
    im.tag_id,
    im.rental_class_num,
    im.common_name,
    'exact',
    1.00,
    1,
    NOW(),
    'system_fix'
FROM pos_equipment pe
INNER JOIN id_item_master im ON pe.current_store = '4.0' AND im.current_store = '8101'
WHERE im.identifier_type = 'RFID'
    AND im.rental_class_num IS NOT NULL
LIMIT 1000;  -- Start with first 1000 correlations

-- ============================================================================
-- FIX 4: CLASSIFY POS EQUIPMENT IDENTIFIERS
-- ============================================================================

-- Add identifier_type column to pos_equipment if not exists
ALTER TABLE pos_equipment 
ADD COLUMN IF NOT EXISTS identifier_type VARCHAR(20) DEFAULT 'None';

-- Classify bulk items in POS equipment
UPDATE pos_equipment 
SET identifier_type = 'Bulk'
WHERE key_field LIKE '%-1' 
   OR key_field LIKE '%-2' 
   OR key_field LIKE '%-3' 
   OR key_field LIKE '%-4';

-- Classify serialized items
UPDATE pos_equipment 
SET identifier_type = 'Sticker'
WHERE key_field LIKE '%#%';

-- Mark Fridley items with RFID correlations
UPDATE pos_equipment pe
SET pe.identifier_type = 'RFID'
WHERE pe.current_store = '4.0'
    AND EXISTS (
        SELECT 1 FROM pos_rfid_correlations prc 
        WHERE prc.pos_item_num = pe.item_num 
        AND prc.is_active = 1
    );

-- ============================================================================
-- FIX 5: CREATE PROPER VIEWS
-- ============================================================================

-- Drop and recreate corrected store summary view
DROP VIEW IF EXISTS v_store_summary_corrected;

CREATE VIEW v_store_summary_corrected AS
SELECT 
    sc.store_name,
    sc.rfid_store_code,
    sc.pos_store_code,
    COUNT(DISTINCT im.tag_id) as rfid_items,
    COUNT(DISTINCT pe.id) as pos_items,
    SUM(CASE WHEN im.identifier_type = 'RFID' THEN 1 ELSE 0 END) as active_rfid,
    SUM(CASE WHEN pe.identifier_type = 'Bulk' THEN 1 ELSE 0 END) as bulk_items,
    SUM(CASE WHEN pe.identifier_type = 'Sticker' THEN 1 ELSE 0 END) as sticker_items
FROM store_correlations sc
LEFT JOIN id_item_master im ON sc.rfid_store_code = im.current_store
LEFT JOIN pos_equipment pe ON sc.pos_store_code = pe.current_store
WHERE sc.is_active = 1
GROUP BY sc.store_name, sc.rfid_store_code, sc.pos_store_code;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

SELECT 'VERIFICATION RESULTS' as Status;

-- Verify RFID exclusivity to Fridley
SELECT 
    'RFID in Fridley Only' as Check_Item,
    CASE 
        WHEN COUNT(*) = 0 THEN 'PASS'
        ELSE CONCAT('FAIL: ', COUNT(*), ' items')
    END as Result
FROM id_item_master
WHERE identifier_type = 'RFID' AND current_store != '8101';

-- Verify bulk classification
SELECT 
    'Bulk Items Classified' as Check_Item,
    CONCAT(COUNT(*), ' items') as Result
FROM pos_equipment
WHERE identifier_type = 'Bulk';

-- Verify correlations created
SELECT 
    'Active Correlations' as Check_Item,
    CONCAT(COUNT(*), ' correlations') as Result
FROM pos_rfid_correlations
WHERE is_active = 1;

-- Show final summary
SELECT * FROM v_store_summary_corrected;
