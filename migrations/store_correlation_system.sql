-- Store Correlation System Migration
-- Date: 2025-08-29
-- Purpose: Enable correlation between RFID Pro API store codes and POS CSV store numbers

-- Create master store correlations table
CREATE TABLE IF NOT EXISTS store_correlations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rfid_store_code VARCHAR(10) NOT NULL COMMENT 'RFID Pro API store code (3607, 6800, 728, 8101)',
    pos_store_code VARCHAR(10) NOT NULL COMMENT 'POS system store number (1, 2, 3, 4)',
    store_name VARCHAR(100) NOT NULL,
    store_location VARCHAR(255),
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_rfid_code (rfid_store_code),
    UNIQUE KEY unique_pos_code (pos_store_code),
    INDEX idx_rfid_code (rfid_store_code),
    INDEX idx_pos_code (pos_store_code),
    INDEX idx_active (is_active)
) COMMENT='Master correlation table between RFID and POS store codes';

-- Insert the store correlations (never sent to RFID Pro API)
INSERT INTO store_correlations (rfid_store_code, pos_store_code, store_name, store_location) VALUES
('3607', '1', 'Wayzata', 'Wayzata, MN'),
('6800', '2', 'Brooklyn Park', 'Brooklyn Park, MN'), 
('728', '3', 'Elk River', 'Elk River, MN'),
('8101', '4', 'Fridley', 'Fridley, MN'),
('000', '0', 'Legacy/Unassigned', 'Unknown/Legacy')
ON DUPLICATE KEY UPDATE
    store_name = VALUES(store_name),
    store_location = VALUES(store_location),
    updated_at = CURRENT_TIMESTAMP;

-- Add correlation fields to POS tables (never sent to RFID Pro API)
ALTER TABLE pos_transactions 
ADD COLUMN IF NOT EXISTS rfid_store_code VARCHAR(10) COMMENT 'Correlated RFID store code - never sent to API',
ADD INDEX idx_pos_trans_rfid_store (rfid_store_code);

ALTER TABLE pos_customers
ADD COLUMN IF NOT EXISTS rfid_store_code VARCHAR(10) COMMENT 'Correlated RFID store code - never sent to API',
ADD INDEX idx_pos_cust_rfid_store (rfid_store_code);

-- Add correlation fields to equipment table
ALTER TABLE pos_equipment
ADD COLUMN IF NOT EXISTS pos_store_code VARCHAR(10) COMMENT 'Correlated POS store code - never sent to API',
ADD INDEX idx_pos_equip_pos_store (pos_store_code);

-- Create audit trail for correlation changes
CREATE TABLE IF NOT EXISTS store_correlation_audit (
    id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    record_id VARCHAR(100) NOT NULL,
    field_name VARCHAR(50) NOT NULL,
    old_value VARCHAR(50),
    new_value VARCHAR(50),
    correlation_type ENUM('rfid_to_pos', 'pos_to_rfid') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT 'system',
    INDEX idx_audit_table (table_name),
    INDEX idx_audit_type (correlation_type),
    INDEX idx_audit_date (created_at)
) COMMENT='Audit trail for store correlation changes';

-- Create unified store view for reporting
CREATE OR REPLACE VIEW v_store_unified AS
SELECT 
    sc.rfid_store_code,
    sc.pos_store_code, 
    sc.store_name,
    sc.store_location,
    sc.is_active,
    -- RFID system metrics
    (SELECT COUNT(*) FROM id_item_master WHERE home_store = sc.rfid_store_code) as rfid_items_home,
    (SELECT COUNT(*) FROM id_item_master WHERE current_store = sc.rfid_store_code) as rfid_items_current,
    -- POS system metrics  
    (SELECT COUNT(*) FROM pos_transactions WHERE store_no = sc.pos_store_code) as pos_transactions,
    (SELECT COUNT(*) FROM pos_customers WHERE store_no = sc.pos_store_code) as pos_customers
FROM store_correlations sc
WHERE sc.is_active = 1;

-- Update existing POS transactions with correlated RFID codes
UPDATE pos_transactions pt
JOIN store_correlations sc ON pt.store_no = sc.pos_store_code 
SET pt.rfid_store_code = sc.rfid_store_code
WHERE pt.rfid_store_code IS NULL;

-- Update existing POS customers with correlated RFID codes  
UPDATE pos_customers pc
JOIN store_correlations sc ON pc.store_no = sc.pos_store_code
SET pc.rfid_store_code = sc.rfid_store_code  
WHERE pc.rfid_store_code IS NULL;

-- Update existing POS equipment with correlated POS codes
UPDATE pos_equipment pe
JOIN store_correlations sc ON pe.current_store = sc.rfid_store_code
SET pe.pos_store_code = sc.pos_store_code
WHERE pe.pos_store_code IS NULL;

-- Create performance monitoring view
CREATE OR REPLACE VIEW v_store_correlation_health AS
SELECT 
    'pos_transactions' as table_name,
    COUNT(*) as total_records,
    COUNT(rfid_store_code) as correlated_records,
    ROUND(COUNT(rfid_store_code) / COUNT(*) * 100, 2) as correlation_percentage
FROM pos_transactions
UNION ALL
SELECT 
    'pos_customers' as table_name,
    COUNT(*) as total_records, 
    COUNT(rfid_store_code) as correlated_records,
    ROUND(COUNT(rfid_store_code) / COUNT(*) * 100, 2) as correlation_percentage
FROM pos_customers
UNION ALL
SELECT
    'pos_equipment' as table_name,
    COUNT(*) as total_records,
    COUNT(pos_store_code) as correlated_records, 
    ROUND(COUNT(pos_store_code) / COUNT(*) * 100, 2) as correlation_percentage
FROM pos_equipment;

-- Log successful migration
INSERT INTO store_correlation_audit (table_name, record_id, field_name, new_value, correlation_type, created_by)
VALUES ('migration', 'store_correlation_system', 'status', 'completed', 'rfid_to_pos', 'migration_script');

COMMIT;