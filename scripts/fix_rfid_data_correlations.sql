-- ============================================================================
-- RFID DATA CORRELATION FIX SCRIPT
-- Purpose: Fix incorrect RFID store assignments and identifier classifications
-- Date: 2025-08-30
-- ============================================================================

-- Safety backup tables first
CREATE TABLE IF NOT EXISTS id_item_master_backup_20250830 AS SELECT * FROM id_item_master;
CREATE TABLE IF NOT EXISTS store_correlations_backup_20250830 AS SELECT * FROM store_correlations;
CREATE TABLE IF NOT EXISTS pos_equipment_backup_20250830 AS SELECT * FROM pos_equipment;

-- ============================================================================
-- PHASE 1: ANALYZE CURRENT DATA ISSUES
-- ============================================================================

-- Show current incorrect RFID assignments
SELECT 'CURRENT RFID MISASSIGNMENTS' as Analysis;
SELECT 
    current_store,
    COUNT(*) as total_items,
    SUM(CASE WHEN identifier_type = 'RFID' THEN 1 ELSE 0 END) as rfid_items,
    SUM(CASE WHEN rental_class_num IS NOT NULL AND rental_class_num != '' THEN 1 ELSE 0 END) as has_rental_class
FROM id_item_master
GROUP BY current_store
ORDER BY current_store;

-- Show tag patterns that need classification
SELECT 'TAG PATTERNS FOR CLASSIFICATION' as Analysis;
SELECT 
    CASE 
        WHEN tag_id LIKE '%-1' THEN 'Ends with -1 (Bulk Store 1)'
        WHEN tag_id LIKE '%-2' THEN 'Ends with -2 (Bulk Store 2)'
        WHEN tag_id LIKE '%-3' THEN 'Ends with -3 (Bulk Store 3)'
        WHEN tag_id LIKE '%-4' THEN 'Ends with -4 (Bulk Store 4)'
        WHEN tag_id LIKE '%#%' THEN 'Contains # (Sticker/Serialized)'
        ELSE 'Other Pattern'
    END as pattern,
    COUNT(*) as count,
    GROUP_CONCAT(DISTINCT current_store) as stores
FROM id_item_master
WHERE tag_id IS NOT NULL
GROUP BY pattern;

-- ============================================================================
-- PHASE 2: FIX STORE CORRELATIONS
-- ============================================================================

-- Update store correlations to reflect reality
-- Only Fridley (8101) should be mapped as RFID test store
UPDATE store_correlations SET is_active = 0 WHERE 1=1; -- Deactivate all first

-- Insert correct store mappings
INSERT INTO store_correlations (rfid_store_code, pos_store_code, store_name, store_location, is_active)
VALUES 
    ('8101', '4', 'Fridley (RFID Test)', 'Fridley, MN', 1),
    ('3607', '1', 'Wayzata (POS Only)', 'Wayzata, MN', 1),
    ('6800', '2', 'Brooklyn Park (POS Only)', 'Brooklyn Park, MN', 1),
    ('728', '3', 'Elk River (POS Only)', 'Elk River, MN', 1),
    ('000', '0', 'Header/Noise Data', 'System Generated', 1)
ON DUPLICATE KEY UPDATE
    store_name = VALUES(store_name),
    store_location = VALUES(store_location),
    is_active = VALUES(is_active);

-- ============================================================================
-- PHASE 3: CORRECT RFID STORE ASSIGNMENTS
-- ============================================================================

-- First, preserve legitimate RFID data from NULL store items with rental_class
CREATE TEMPORARY TABLE temp_legitimate_rfid AS
SELECT tag_id
FROM id_item_master
WHERE current_store IS NULL 
    AND rental_class_num IS NOT NULL 
    AND rental_class_num != ''
    AND identifier_type = 'RFID';

-- Reset all identifier_type to None first
UPDATE id_item_master 
SET identifier_type = 'None',
    date_updated = NOW()
WHERE identifier_type != 'None' OR identifier_type IS NULL;

-- ============================================================================
-- PHASE 4: CORRECTLY CLASSIFY IDENTIFIER TYPES
-- ============================================================================

-- Mark Bulk items (ending with -1, -2, -3, -4)
UPDATE id_item_master 
SET identifier_type = 'Bulk',
    date_updated = NOW()
WHERE (tag_id LIKE '%-1' OR tag_id LIKE '%-2' OR tag_id LIKE '%-3' OR tag_id LIKE '%-4')
    AND tag_id IS NOT NULL;

-- Mark Sticker/Serialized items (containing #)
UPDATE id_item_master 
SET identifier_type = 'Sticker',
    date_updated = NOW()
WHERE tag_id LIKE '%#%'
    AND tag_id IS NOT NULL;

-- Mark legitimate RFID items (only in Fridley store 8101)
UPDATE id_item_master 
SET identifier_type = 'RFID',
    date_updated = NOW()
WHERE current_store = '8101'
    AND rental_class_num IS NOT NULL 
    AND rental_class_num != ''
    AND tag_id NOT LIKE '%-1' 
    AND tag_id NOT LIKE '%-2'
    AND tag_id NOT LIKE '%-3'
    AND tag_id NOT LIKE '%-4'
    AND tag_id NOT LIKE '%#%';

-- Also mark the legitimate RFID items from NULL store
UPDATE id_item_master 
SET identifier_type = 'RFID',
    current_store = '8101',  -- Assign to Fridley since they're real RFID
    date_updated = NOW()
WHERE tag_id IN (SELECT tag_id FROM temp_legitimate_rfid);

-- ============================================================================
-- PHASE 5: CLEAN UP INCORRECT RFID ASSIGNMENTS
-- ============================================================================

-- Remove RFID identifier from non-Fridley stores
UPDATE id_item_master 
SET identifier_type = 'None',
    date_updated = NOW()
WHERE identifier_type = 'RFID'
    AND (current_store != '8101' OR current_store IS NULL)
    AND tag_id NOT IN (SELECT tag_id FROM temp_legitimate_rfid);

-- Mark store 000 items appropriately (header/noise data)
UPDATE id_item_master 
SET identifier_type = 'None',
    notes = CONCAT(IFNULL(notes, ''), ' [Header/Noise Data from Store 000]'),
    date_updated = NOW()
WHERE current_store = '000';

-- ============================================================================
-- PHASE 6: UPDATE POS_EQUIPMENT TABLE TO MATCH
-- ============================================================================

-- Clear all RFID rental class assignments first
UPDATE pos_equipment 
SET rfid_rental_class_num = NULL
WHERE rfid_rental_class_num IS NOT NULL;

-- Only assign RFID rental classes for Fridley items that are truly RFID
UPDATE pos_equipment pe
INNER JOIN id_item_master im ON pe.key_field = im.tag_id
SET pe.rfid_rental_class_num = im.rental_class_num,
    pe.updated_at = NOW()
WHERE im.identifier_type = 'RFID'
    AND im.current_store = '8101'
    AND im.rental_class_num IS NOT NULL;

-- ============================================================================
-- PHASE 7: CREATE SUMMARY VIEWS FOR VERIFICATION
-- ============================================================================

-- Drop and recreate the store summary view with correct logic
DROP VIEW IF EXISTS store_summary_view_corrected;
CREATE VIEW store_summary_view_corrected AS
SELECT 
    COALESCE(sc.store_name, CONCAT('Store ', im.current_store)) as store_name,
    im.current_store as store_code,
    COUNT(*) as total_items,
    SUM(CASE WHEN im.identifier_type = 'RFID' THEN 1 ELSE 0 END) as rfid_items,
    SUM(CASE WHEN im.identifier_type = 'Bulk' THEN 1 ELSE 0 END) as bulk_items,
    SUM(CASE WHEN im.identifier_type = 'Sticker' THEN 1 ELSE 0 END) as sticker_items,
    SUM(CASE WHEN im.identifier_type = 'QR' THEN 1 ELSE 0 END) as qr_items,
    SUM(CASE WHEN im.identifier_type = 'None' THEN 1 ELSE 0 END) as unidentified_items,
    SUM(CASE WHEN im.rental_class_num IS NOT NULL THEN 1 ELSE 0 END) as items_with_rental_class
FROM id_item_master im
LEFT JOIN store_correlations sc ON im.current_store = sc.rfid_store_code AND sc.is_active = 1
GROUP BY im.current_store, sc.store_name;

-- ============================================================================
-- PHASE 8: VERIFICATION QUERIES
-- ============================================================================

-- Show corrected RFID distribution
SELECT 'CORRECTED RFID DISTRIBUTION' as Verification;
SELECT * FROM store_summary_view_corrected ORDER BY store_code;

-- Verify Fridley is the only store with RFID
SELECT 'VERIFY FRIDLEY RFID EXCLUSIVITY' as Verification;
SELECT 
    current_store,
    identifier_type,
    COUNT(*) as count
FROM id_item_master
WHERE identifier_type = 'RFID'
GROUP BY current_store, identifier_type;

-- Show identifier type distribution
SELECT 'IDENTIFIER TYPE DISTRIBUTION' as Verification;
SELECT 
    identifier_type,
    COUNT(*) as total_items,
    COUNT(DISTINCT current_store) as unique_stores
FROM id_item_master
GROUP BY identifier_type
ORDER BY total_items DESC;

-- Verify bulk item classification
SELECT 'BULK ITEM VERIFICATION' as Verification;
SELECT 
    CASE 
        WHEN tag_id LIKE '%-1' THEN 'Store 1 Bulk'
        WHEN tag_id LIKE '%-2' THEN 'Store 2 Bulk'
        WHEN tag_id LIKE '%-3' THEN 'Store 3 Bulk'
        WHEN tag_id LIKE '%-4' THEN 'Store 4 Bulk'
    END as bulk_type,
    identifier_type,
    COUNT(*) as count
FROM id_item_master
WHERE tag_id LIKE '%-1' OR tag_id LIKE '%-2' OR tag_id LIKE '%-3' OR tag_id LIKE '%-4'
GROUP BY bulk_type, identifier_type;

-- Clean up temporary table
DROP TEMPORARY TABLE IF EXISTS temp_legitimate_rfid;

-- ============================================================================
-- FINAL STATUS REPORT
-- ============================================================================

SELECT 'DATA CORRELATION FIX COMPLETE' as Status;
SELECT 
    'Fixed RFID assignments - Only Fridley (8101) has RFID items' as Action,
    'All other stores marked as POS-only' as Result
UNION ALL
SELECT 
    'Classified identifier types based on tag patterns',
    'Bulk (-1,-2,-3,-4), Sticker (#), RFID, None'
UNION ALL
SELECT 
    'Cleaned store 000 data',
    'Marked as header/noise data'
UNION ALL
SELECT 
    'Preserved legitimate RFID data from NULL store',
    'Reassigned to Fridley (8101)'
UNION ALL
SELECT 
    'Updated store correlations table',
    'Correct mappings for all stores';