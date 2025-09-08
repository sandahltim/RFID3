-- Migration: Fix Health Alerts Duplicate Issues
-- Date: 2025-08-28
-- Purpose: Add unique constraints to prevent duplicate health alerts and clean existing duplicates

-- Clean up existing duplicate alerts before adding constraints
DELETE h1 FROM inventory_health_alerts h1
INNER JOIN inventory_health_alerts h2 
WHERE h1.id > h2.id
  AND h1.tag_id = h2.tag_id
  AND h1.alert_type = h2.alert_type
  AND h1.status = h2.status
  AND h1.tag_id IS NOT NULL;

-- Clean up duplicate category-based alerts
DELETE h1 FROM inventory_health_alerts h1
INNER JOIN inventory_health_alerts h2 
WHERE h1.id > h2.id
  AND h1.category = h2.category
  AND h1.subcategory = h2.subcategory
  AND h1.alert_type = h2.alert_type
  AND h1.status = h2.status
  AND h1.tag_id IS NULL
  AND h2.tag_id IS NULL;

-- Add unique constraint for tag-based alerts
ALTER TABLE inventory_health_alerts 
ADD CONSTRAINT uq_health_alert_tag_type_status 
UNIQUE (tag_id, alert_type, status);

-- Add unique constraint for category-based alerts
ALTER TABLE inventory_health_alerts 
ADD CONSTRAINT uq_health_alert_category_type_status 
UNIQUE (category, subcategory, alert_type, status);

-- Add performance indexes
CREATE INDEX IF NOT EXISTS ix_health_alert_tag_id_type ON inventory_health_alerts (tag_id, alert_type);
CREATE INDEX IF NOT EXISTS ix_health_alert_category_type ON inventory_health_alerts (category, alert_type);
CREATE INDEX IF NOT EXISTS ix_health_alert_status_created ON inventory_health_alerts (status, created_at);

-- Verify no duplicates remain
SELECT 
    'Tag-based duplicates' as type,
    COUNT(*) as remaining_duplicates
FROM (
    SELECT tag_id, alert_type, status, COUNT(*) as cnt
    FROM inventory_health_alerts 
    WHERE tag_id IS NOT NULL
    GROUP BY tag_id, alert_type, status
    HAVING COUNT(*) > 1
) as dups

UNION ALL

SELECT 
    'Category-based duplicates' as type,
    COUNT(*) as remaining_duplicates
FROM (
    SELECT category, subcategory, alert_type, status, COUNT(*) as cnt
    FROM inventory_health_alerts 
    WHERE tag_id IS NULL
    GROUP BY category, subcategory, alert_type, status
    HAVING COUNT(*) > 1
) as dups;