-- Step-by-step Health Alerts Fix
-- Execute each section separately to ensure success

-- STEP 1: Create backup
CREATE TABLE inventory_health_alerts_backup_20250828 AS 
SELECT * FROM inventory_health_alerts;

-- STEP 2: Verify backup
SELECT 'Backup created with', COUNT(*), 'records' FROM inventory_health_alerts_backup_20250828;