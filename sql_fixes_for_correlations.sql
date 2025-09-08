-- SQL Fixes for RFID3 Database Correlation Issues
-- Generated: 2025-09-03
-- Purpose: Resolve discrepancies between documented and actual correlation state

-- ============================================================================
-- PART 1: DIAGNOSTIC QUERIES
-- ============================================================================

-- Check current state of correlations
SELECT 'Current Correlation State' as Analysis;
SELECT 
    'equipment_rfid_correlations' as table_name,
    COUNT(*) as total_correlations,
    SUM(CASE WHEN rfid_match.rental_class_num IS NOT NULL THEN 1 ELSE 0 END) as matching_rfid,
    SUM(CASE WHEN rfid_match.rental_class_num IS NULL THEN 1 ELSE 0 END) as orphaned_correlations
FROM equipment_rfid_correlations erc
LEFT JOIN (
    SELECT DISTINCT rental_class_num 
    FROM id_item_master 
    WHERE identifier_type = 'RFID'
) rfid_match ON erc.rfid_rental_class_num = rfid_match.rental_class_num;

-- Identify RFID classes without correlations
SELECT 'Uncorrelated RFID Classes' as Analysis;
SELECT 
    iim.rental_class_num,
    MIN(iim.common_name) as sample_name,
    COUNT(*) as tag_count
FROM id_item_master iim
WHERE iim.identifier_type = 'RFID'
AND NOT EXISTS (
    SELECT 1 FROM equipment_rfid_correlations erc 
    WHERE erc.rfid_rental_class_num = iim.rental_class_num
)
GROUP BY iim.rental_class_num
ORDER BY COUNT(*) DESC
LIMIT 20;

-- ============================================================================
-- PART 2: FIX COMBINED INVENTORY VIEW
-- ============================================================================

-- The issue: The combined_inventory view is joining on rental_class_num directly
-- but the correlation is stored with pos_item_num mapping
-- We need to fix the JOIN logic

DROP VIEW IF EXISTS combined_inventory_fixed;

CREATE VIEW combined_inventory_fixed AS
SELECT 
    pe.item_num AS equipment_id,
    pe.name AS equipment_name,
    pe.category AS category,
    pe.current_store AS store_code,
    pe.qty AS pos_quantity,
    pe.rate_1 AS rental_rate,
    pe.period_1 AS rental_period,
    pe.inactive AS is_inactive,
    pe.home_store AS home_store_code,
    erc.confidence_score AS correlation_confidence,
    erc.rfid_tag_count AS tag_count_from_correlation,
    erc.correlation_type AS correlation_method,
    COALESCE(rfid_agg.total_tags, 0) AS rfid_tag_count,
    COALESCE(rfid_agg.on_rent_count, 0) AS on_rent_count,
    COALESCE(rfid_agg.available_count, 0) AS available_count,
    COALESCE(rfid_agg.maintenance_count, 0) AS maintenance_count,
    CASE 
        WHEN pe.qty > 0 
        THEN GREATEST(0, pe.qty - COALESCE(rfid_agg.on_rent_count, 0))
        ELSE 0 
    END AS calculated_available,
    CASE 
        WHEN pe.inactive = 1 THEN 'inactive'
        WHEN COALESCE(rfid_agg.maintenance_count, 0) > 0 THEN 'maintenance'
        WHEN COALESCE(rfid_agg.on_rent_count, 0) >= pe.qty THEN 'fully_rented'
        WHEN COALESCE(rfid_agg.on_rent_count, 0) > 0 THEN 'partially_rented'
        ELSE 'available'
    END AS status,
    COALESCE(pe.rate_1, 0) * COALESCE(rfid_agg.on_rent_count, 0) AS current_rental_revenue,
    CASE 
        WHEN pe.qty > 0 
        THEN ROUND(COALESCE(rfid_agg.on_rent_count, 0) / pe.qty * 100, 1)
        ELSE 0 
    END AS utilization_percentage,
    CASE 
        WHEN erc.pos_item_num IS NULL THEN 'no_rfid_correlation'
        WHEN ABS(pe.qty - COALESCE(rfid_agg.total_tags, 0)) > 2 THEN 'quantity_mismatch'
        WHEN erc.confidence_score < 0.8 THEN 'low_confidence_match'
        ELSE 'good_quality'
    END AS data_quality_flag,
    erc.created_at AS correlation_date,
    CURRENT_TIMESTAMP AS view_generated_at
FROM pos_equipment pe
LEFT JOIN equipment_rfid_correlations erc ON pe.item_num = erc.pos_item_num
LEFT JOIN (
    SELECT 
        rental_class_num,
        COUNT(*) AS total_tags,
        SUM(CASE WHEN status = 'On Rent' THEN 1 ELSE 0 END) AS on_rent_count,
        SUM(CASE WHEN status IN ('Delivered', 'Available') THEN 1 ELSE 0 END) AS available_count,
        SUM(CASE WHEN status IN ('Maintenance', 'Repair') THEN 1 ELSE 0 END) AS maintenance_count
    FROM id_item_master
    WHERE identifier_type = 'RFID'
    GROUP BY rental_class_num
) rfid_agg ON erc.rfid_rental_class_num = rfid_agg.rental_class_num  -- Fixed: join through correlation table
WHERE pe.category NOT IN ('UNUSED', 'NON CURRENT ITEMS', 'Parts - Internal Repair/Maint')
    AND pe.inactive = 0;

-- ============================================================================
-- PART 3: CREATE MISSING CORRELATIONS (Intelligent Matching)
-- ============================================================================

-- Create temporary table for potential new correlations
DROP TABLE IF EXISTS temp_potential_correlations;

CREATE TEMPORARY TABLE temp_potential_correlations AS
SELECT 
    pe.item_num as pos_item_num,
    pe.name as pos_name,
    iim.rental_class_num as rfid_rental_class_num,
    MIN(iim.common_name) as rfid_name,
    COUNT(DISTINCT iim.item_id) as rfid_tag_count,
    -- Calculate similarity score
    CASE 
        -- Exact item number match
        WHEN pe.item_num = iim.rental_class_num THEN 100
        -- Normalized number match (remove leading zeros, etc)
        WHEN CAST(pe.item_num AS UNSIGNED) = CAST(iim.rental_class_num AS UNSIGNED) THEN 95
        -- Name similarity (basic keyword matching)
        WHEN UPPER(pe.name) LIKE CONCAT('%', UPPER(SUBSTRING_INDEX(iim.common_name, ' ', 2)), '%') THEN 70
        WHEN UPPER(iim.common_name) LIKE CONCAT('%', UPPER(SUBSTRING_INDEX(pe.name, ' ', 2)), '%') THEN 70
        ELSE 0
    END as confidence_score,
    CASE 
        WHEN pe.item_num = iim.rental_class_num THEN 'exact_match'
        WHEN CAST(pe.item_num AS UNSIGNED) = CAST(iim.rental_class_num AS UNSIGNED) THEN 'normalized_match'
        ELSE 'name_similarity'
    END as match_type
FROM pos_equipment pe
CROSS JOIN (
    SELECT DISTINCT rental_class_num, common_name, item_id
    FROM id_item_master
    WHERE identifier_type = 'RFID'
) iim
WHERE pe.inactive = 0
    AND pe.category NOT IN ('UNUSED', 'NON CURRENT ITEMS', 'Parts - Internal Repair/Maint')
    -- Only items not already correlated
    AND NOT EXISTS (
        SELECT 1 FROM equipment_rfid_correlations erc
        WHERE erc.pos_item_num = pe.item_num
    )
    -- Only RFID classes not already correlated
    AND NOT EXISTS (
        SELECT 1 FROM equipment_rfid_correlations erc
        WHERE erc.rfid_rental_class_num = iim.rental_class_num
    )
GROUP BY pe.item_num, iim.rental_class_num
HAVING confidence_score > 50  -- Only keep reasonable matches
ORDER BY confidence_score DESC;

-- Review potential correlations
SELECT 
    'Potential New Correlations' as Analysis,
    COUNT(*) as total_potential,
    SUM(CASE WHEN confidence_score >= 90 THEN 1 ELSE 0 END) as high_confidence,
    SUM(CASE WHEN confidence_score >= 70 AND confidence_score < 90 THEN 1 ELSE 0 END) as medium_confidence,
    SUM(CASE WHEN confidence_score < 70 THEN 1 ELSE 0 END) as low_confidence
FROM temp_potential_correlations;

-- Show top potential matches for review
SELECT 
    pos_item_num,
    LEFT(pos_name, 40) as pos_name,
    rfid_rental_class_num,
    LEFT(rfid_name, 40) as rfid_name,
    rfid_tag_count,
    confidence_score,
    match_type
FROM temp_potential_correlations
ORDER BY confidence_score DESC
LIMIT 20;

-- ============================================================================
-- PART 4: INSERT HIGH-CONFIDENCE NEW CORRELATIONS
-- ============================================================================

-- Only insert correlations with confidence >= 90 (exact or normalized matches)
-- Comment out to prevent automatic execution - review first!
/*
INSERT INTO equipment_rfid_correlations (
    pos_item_num,
    normalized_item_num,
    rfid_rental_class_num,
    pos_equipment_name,
    rfid_common_name,
    rfid_tag_count,
    confidence_score,
    correlation_type,
    created_at
)
SELECT 
    pos_item_num,
    pos_item_num as normalized_item_num,
    rfid_rental_class_num,
    pos_name,
    rfid_name,
    rfid_tag_count,
    confidence_score,
    match_type,
    NOW()
FROM temp_potential_correlations
WHERE confidence_score >= 90
ON DUPLICATE KEY UPDATE
    confidence_score = VALUES(confidence_score),
    rfid_tag_count = VALUES(rfid_tag_count);
*/

-- ============================================================================
-- PART 5: UPDATE RFID TAG COUNTS IN CORRELATIONS
-- ============================================================================

UPDATE equipment_rfid_correlations erc
INNER JOIN (
    SELECT 
        rental_class_num,
        COUNT(*) as tag_count
    FROM id_item_master
    WHERE identifier_type = 'RFID'
    GROUP BY rental_class_num
) rfid_counts ON erc.rfid_rental_class_num = rfid_counts.rental_class_num
SET erc.rfid_tag_count = rfid_counts.tag_count
WHERE erc.rfid_tag_count != rfid_counts.tag_count OR erc.rfid_tag_count IS NULL;

-- ============================================================================
-- PART 6: VERIFY FIXES
-- ============================================================================

-- Check updated correlation statistics
SELECT 'Updated Correlation Statistics' as Analysis;
SELECT 
    COUNT(*) as total_correlations,
    SUM(CASE WHEN rfid_tag_count > 0 THEN 1 ELSE 0 END) as correlations_with_tags,
    ROUND(AVG(confidence_score), 2) as avg_confidence,
    ROUND(SUM(CASE WHEN rfid_tag_count > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as pct_with_tags
FROM equipment_rfid_correlations;

-- Check fixed view
SELECT 'Fixed Combined Inventory View' as Analysis;
SELECT 
    COUNT(*) as total_items,
    SUM(CASE WHEN rfid_tag_count > 0 THEN 1 ELSE 0 END) as items_with_rfid,
    SUM(CASE WHEN correlation_confidence IS NOT NULL THEN 1 ELSE 0 END) as correlated_items,
    ROUND(SUM(CASE WHEN rfid_tag_count > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as pct_with_rfid
FROM combined_inventory_fixed;

-- ============================================================================
-- PART 7: RECOMMENDATIONS
-- ============================================================================

SELECT '
RECOMMENDATIONS:

1. IMMEDIATE ACTIONS:
   - Replace combined_inventory view with combined_inventory_fixed
   - Review and insert high-confidence correlations (confidence >= 90)
   - Update rfid_tag_count in existing correlations

2. DATA QUALITY IMPROVEMENTS:
   - 290 of 533 correlations (54.4%) match actual RFID data
   - 243 correlations reference non-existent RFID classes
   - Consider removing or updating orphaned correlations

3. EXPAND CORRELATIONS:
   - Only 3.28% of active equipment has correlations
   - Use intelligent matching to find more correlations
   - Consider manual review for medium-confidence matches (70-90)

4. SYSTEM INTEGRATION:
   - Implement automated correlation discovery
   - Add data validation to prevent orphaned correlations
   - Create monitoring dashboard for correlation health

5. DOCUMENTATION UPDATE:
   - Current coverage is 3.28%, not 58.7% as documented
   - Combined inventory view exists but needs fixing
   - Cross-system analytics partially enabled (290 working correlations)
' as Recommendations;