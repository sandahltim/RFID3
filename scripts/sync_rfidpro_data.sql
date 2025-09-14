-- RFID Pro to RFID Inventory Data Sync Script
-- Ensures all data from the legacy rfidpro database is migrated to rfid_inventory

USE rfid_inventory;

-- Sync equipment_items (the table with missing records)
INSERT IGNORE INTO rfid_inventory.equipment_items
SELECT * FROM rfidpro.equipment_items;

-- Sync other key tables that might have data differences
INSERT IGNORE INTO rfid_inventory.combined_inventory
SELECT * FROM rfidpro.combined_inventory;

INSERT IGNORE INTO rfid_inventory.bi_executive_kpis
SELECT * FROM rfidpro.bi_executive_kpis;

INSERT IGNORE INTO rfid_inventory.configuration_audit
SELECT * FROM rfidpro.configuration_audit;

INSERT IGNORE INTO rfid_inventory.contract_snapshots
SELECT * FROM rfidpro.contract_snapshots;

INSERT IGNORE INTO rfid_inventory.custom_insights
SELECT * FROM rfidpro.custom_insights;

INSERT IGNORE INTO rfid_inventory.equipment_import_logs
SELECT * FROM rfidpro.equipment_import_logs;

-- Report final counts
SELECT
    'equipment_items' as table_name,
    (SELECT COUNT(*) FROM rfidpro.equipment_items) as rfidpro_count,
    (SELECT COUNT(*) FROM rfid_inventory.equipment_items) as rfid_inventory_count,
    (SELECT COUNT(*) FROM rfid_inventory.equipment_items) - (SELECT COUNT(*) FROM rfidpro.equipment_items) as difference;

SELECT
    'combined_inventory' as table_name,
    (SELECT COUNT(*) FROM rfidpro.combined_inventory) as rfidpro_count,
    (SELECT COUNT(*) FROM rfid_inventory.combined_inventory) as rfid_inventory_count,
    (SELECT COUNT(*) FROM rfid_inventory.combined_inventory) - (SELECT COUNT(*) FROM rfidpro.combined_inventory) as difference;