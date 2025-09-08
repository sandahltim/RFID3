-- Create Combined Inventory View
-- Uses the 533 equipment correlations established between POS and RFID systems
-- Date: 2025-09-03

-- Drop existing view if it exists
DROP VIEW IF EXISTS combined_inventory;

-- Create comprehensive combined inventory view
CREATE VIEW combined_inventory AS
SELECT 
    -- Primary identifiers
    pe.item_num as equipment_id,
    pe.name as equipment_name,
    pe.category as category,
    pe.current_store as store_code,
    
    -- Equipment details from POS
    pe.qty as pos_quantity,
    pe.rate_1 as rental_rate,
    pe.period_1 as rental_period,
    pe.inactive as is_inactive,
    pe.home_store as home_store_code,
    
    -- RFID correlation data
    erc.confidence_score as correlation_confidence,
    erc.quantity_difference as qty_discrepancy,
    erc.name_match_type as name_match_quality,
    
    -- RFID inventory status (aggregated from individual tags)
    COALESCE(rfid_agg.total_tags, 0) as rfid_tag_count,
    COALESCE(rfid_agg.on_rent_count, 0) as on_rent_count,
    COALESCE(rfid_agg.available_count, 0) as available_count,
    COALESCE(rfid_agg.maintenance_count, 0) as maintenance_count,
    
    -- Calculated availability metrics
    CASE 
        WHEN pe.qty > 0 THEN 
            GREATEST(0, pe.qty - COALESCE(rfid_agg.on_rent_count, 0))
        ELSE 0 
    END as calculated_available,
    
    -- Status determination logic
    CASE 
        WHEN pe.inactive = 1 THEN 'inactive'
        WHEN COALESCE(rfid_agg.maintenance_count, 0) > 0 THEN 'maintenance'
        WHEN COALESCE(rfid_agg.on_rent_count, 0) >= pe.qty THEN 'fully_rented'
        WHEN COALESCE(rfid_agg.on_rent_count, 0) > 0 THEN 'partially_rented'
        ELSE 'available'
    END as status,
    
    -- Revenue and utilization calculations
    pe.rate_1 * COALESCE(rfid_agg.on_rent_count, 0) as current_rental_revenue,
    CASE 
        WHEN pe.qty > 0 THEN 
            ROUND((COALESCE(rfid_agg.on_rent_count, 0) / pe.qty) * 100, 1)
        ELSE 0 
    END as utilization_percentage,
    
    -- Data quality flags
    CASE 
        WHEN erc.item_num IS NULL THEN 'no_rfid_correlation'
        WHEN ABS(COALESCE(erc.quantity_difference, 0)) > 2 THEN 'quantity_mismatch'
        WHEN erc.confidence_score < 0.8 THEN 'low_confidence_match'
        ELSE 'good_quality'
    END as data_quality_flag,
    
    -- Timestamps for freshness tracking
    erc.created_at as correlation_date,
    NOW() as view_generated_at

FROM pos_equipment pe

-- Join with equipment correlations (our 533 correlations)
LEFT JOIN equipment_rfid_correlations erc 
    ON CAST(pe.item_num AS UNSIGNED) = CAST(erc.item_num AS UNSIGNED)

-- Aggregate RFID data by rental class
LEFT JOIN (
    SELECT 
        rental_class_num,
        COUNT(*) as total_tags,
        SUM(CASE WHEN status = 'On Rent' THEN 1 ELSE 0 END) as on_rent_count,
        SUM(CASE WHEN status = 'Delivered' OR status = 'Available' THEN 1 ELSE 0 END) as available_count,
        SUM(CASE WHEN status = 'Maintenance' OR status = 'Repair' THEN 1 ELSE 0 END) as maintenance_count
    FROM id_item_master 
    WHERE identifier_type = 'RFID'
    GROUP BY rental_class_num
) rfid_agg ON CAST(pe.item_num AS UNSIGNED) = CAST(rfid_agg.rental_class_num AS UNSIGNED)

-- Filter for active equipment categories
WHERE pe.category NOT IN ('UNUSED', 'NON CURRENT ITEMS', 'Parts - Internal Repair/Maint')
  AND pe.inactive = 0;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_combined_inventory_store ON pos_equipment(current_store);
CREATE INDEX IF NOT EXISTS idx_combined_inventory_category ON pos_equipment(category);
CREATE INDEX IF NOT EXISTS idx_combined_inventory_status ON pos_equipment(inactive);

-- Note: Grant permissions manually if needed
-- GRANT SELECT ON combined_inventory TO 'rfid_user'@'localhost';

-- Performance analysis query
SELECT 
    'Combined Inventory View Created' as status,
    COUNT(*) as total_equipment_items,
    SUM(CASE WHEN data_quality_flag = 'good_quality' THEN 1 ELSE 0 END) as high_quality_correlations,
    COUNT(DISTINCT store_code) as stores_covered,
    COUNT(DISTINCT category) as categories_covered
FROM combined_inventory;