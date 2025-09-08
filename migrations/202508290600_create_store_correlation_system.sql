-- Migration: Create Store Correlation System
-- Date: 2025-08-29
-- Purpose: Add store correlation fields and infrastructure for cross-system data queries
-- Maintains RFID Pro API compatibility by separating correlation logic from API fields

-- 1. Add correlation fields to existing tables (never sent to RFID Pro API)
-- These fields are for internal correlation only and will never be sent to RFID Pro API

-- Add correlation fields to id_item_master
ALTER TABLE id_item_master 
ADD COLUMN IF NOT EXISTS rfid_store_code VARCHAR(10) COMMENT 'RFID system store code (3607, 6800, 728, 8101)',
ADD COLUMN IF NOT EXISTS pos_store_code VARCHAR(10) COMMENT 'POS system store code (1, 2, 3, 4)',
ADD COLUMN IF NOT EXISTS correlation_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last correlation update',
ADD INDEX IF NOT EXISTS idx_rfid_store_code (rfid_store_code),
ADD INDEX IF NOT EXISTS idx_pos_store_code (pos_store_code),
ADD INDEX IF NOT EXISTS idx_correlation_updated (correlation_updated_at);

-- Add correlation fields to pos_transactions
ALTER TABLE pos_transactions 
ADD COLUMN IF NOT EXISTS rfid_store_code VARCHAR(10) COMMENT 'Correlated RFID system store code',
ADD COLUMN IF NOT EXISTS correlation_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last correlation update',
ADD INDEX IF NOT EXISTS idx_rfid_store_corr (rfid_store_code),
ADD INDEX IF NOT EXISTS idx_pos_correlation_updated (correlation_updated_at);

-- Add correlation fields to pos_customers (if they have store associations)
ALTER TABLE pos_customers 
ADD COLUMN IF NOT EXISTS primary_rfid_store_code VARCHAR(10) COMMENT 'Primary RFID store for analytics correlation',
ADD COLUMN IF NOT EXISTS correlation_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last correlation update',
ADD INDEX IF NOT EXISTS idx_customer_rfid_store (primary_rfid_store_code);

-- Add correlation fields to pos_equipment
ALTER TABLE pos_equipment 
ADD COLUMN IF NOT EXISTS rfid_home_store VARCHAR(10) COMMENT 'Correlated RFID home store code',
ADD COLUMN IF NOT EXISTS rfid_current_store VARCHAR(10) COMMENT 'Correlated RFID current store code', 
ADD COLUMN IF NOT EXISTS correlation_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Last correlation update',
ADD INDEX IF NOT EXISTS idx_equip_rfid_home (rfid_home_store),
ADD INDEX IF NOT EXISTS idx_equip_rfid_current (rfid_current_store);

-- 2. Create store correlation mapping table (master reference)
CREATE TABLE IF NOT EXISTS store_correlations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rfid_store_code VARCHAR(10) NOT NULL UNIQUE COMMENT 'RFID system store code',
    pos_store_code VARCHAR(10) NOT NULL COMMENT 'POS system store code',
    store_name VARCHAR(100) NOT NULL COMMENT 'Human readable store name',
    store_location VARCHAR(200) COMMENT 'Store location/address',
    is_active BOOLEAN DEFAULT TRUE COMMENT 'Whether correlation is active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_rfid_code (rfid_store_code),
    INDEX idx_pos_code (pos_store_code),
    INDEX idx_active (is_active),
    
    UNIQUE KEY unique_pos_code (pos_store_code)
) COMMENT='Store correlation mapping between RFID and POS systems';

-- 3. Insert store correlation mappings from existing config
INSERT INTO store_correlations (rfid_store_code, pos_store_code, store_name, store_location) VALUES
('3607', '1', 'Wayzata', 'Wayzata, MN'),
('6800', '2', 'Brooklyn Park', 'Brooklyn Park, MN'), 
('728', '3', 'Elk River', 'Elk River, MN'),
('8101', '4', 'Fridley', 'Fridley, MN'),
('000', '0', 'Legacy/Unassigned', 'Multiple Locations')
ON DUPLICATE KEY UPDATE
store_name = VALUES(store_name),
store_location = VALUES(store_location),
updated_at = CURRENT_TIMESTAMP;

-- 4. Create correlation audit table for tracking updates
CREATE TABLE IF NOT EXISTS store_correlation_audit (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL COMMENT 'Table that was updated',
    record_id VARCHAR(255) NOT NULL COMMENT 'ID of record that was updated',
    old_rfid_code VARCHAR(10) COMMENT 'Previous RFID store code',
    new_rfid_code VARCHAR(10) COMMENT 'New RFID store code',
    old_pos_code VARCHAR(10) COMMENT 'Previous POS store code',
    new_pos_code VARCHAR(10) COMMENT 'New POS store code',
    update_reason VARCHAR(255) COMMENT 'Reason for correlation update',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_table_record (table_name, record_id),
    INDEX idx_created_at (created_at)
) COMMENT='Audit trail for store correlation updates';

-- 5. Create view for unified store information
CREATE OR REPLACE VIEW v_store_unified AS
SELECT 
    sc.rfid_store_code,
    sc.pos_store_code,
    sc.store_name,
    sc.store_location,
    sc.is_active,
    -- RFID inventory counts
    COALESCE(rfid_stats.total_items, 0) as rfid_total_items,
    COALESCE(rfid_stats.items_on_rent, 0) as rfid_items_on_rent,
    COALESCE(rfid_stats.items_available, 0) as rfid_items_available,
    -- POS transaction counts (last 30 days)
    COALESCE(pos_stats.recent_transactions, 0) as pos_recent_transactions,
    COALESCE(pos_stats.total_revenue_30d, 0) as pos_revenue_30d
FROM store_correlations sc
LEFT JOIN (
    SELECT 
        COALESCE(current_store, home_store, '000') as store_code,
        COUNT(*) as total_items,
        SUM(CASE WHEN status IN ('On Rent', 'Delivered', 'Out to Customer') THEN 1 ELSE 0 END) as items_on_rent,
        SUM(CASE WHEN status = 'Ready to Rent' THEN 1 ELSE 0 END) as items_available
    FROM id_item_master 
    GROUP BY COALESCE(current_store, home_store, '000')
) rfid_stats ON sc.rfid_store_code = rfid_stats.store_code
LEFT JOIN (
    SELECT 
        pt.store_no,
        COUNT(*) as recent_transactions,
        SUM(COALESCE(pt.total, 0)) as total_revenue_30d
    FROM pos_transactions pt 
    WHERE pt.contract_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
    GROUP BY pt.store_no
) pos_stats ON sc.pos_store_code = pos_stats.store_no
WHERE sc.is_active = TRUE;

-- 6. Create correlation update triggers (optional - for automated correlation)
DELIMITER ;;

-- Trigger to auto-correlate pos_transactions when store_no is updated
CREATE TRIGGER IF NOT EXISTS trg_pos_transactions_store_correlation
AFTER UPDATE ON pos_transactions
FOR EACH ROW
BEGIN
    DECLARE corr_rfid_code VARCHAR(10);
    
    -- Only update if store_no changed
    IF OLD.store_no != NEW.store_no OR (OLD.store_no IS NULL AND NEW.store_no IS NOT NULL) THEN
        -- Get correlated RFID store code
        SELECT rfid_store_code INTO corr_rfid_code 
        FROM store_correlations 
        WHERE pos_store_code = NEW.store_no AND is_active = TRUE
        LIMIT 1;
        
        -- Update correlation fields
        IF corr_rfid_code IS NOT NULL THEN
            UPDATE pos_transactions 
            SET 
                rfid_store_code = corr_rfid_code,
                correlation_updated_at = NOW()
            WHERE id = NEW.id;
            
            -- Log audit trail
            INSERT INTO store_correlation_audit 
            (table_name, record_id, old_rfid_code, new_rfid_code, old_pos_code, new_pos_code, update_reason)
            VALUES 
            ('pos_transactions', NEW.id, OLD.rfid_store_code, corr_rfid_code, OLD.store_no, NEW.store_no, 'Auto-correlation via trigger');
        END IF;
    END IF;
END;;

DELIMITER ;

-- 7. Performance optimization indexes for correlation queries
CREATE INDEX IF NOT EXISTS idx_item_master_correlation_query ON id_item_master(rfid_store_code, status, date_last_scanned);
CREATE INDEX IF NOT EXISTS idx_pos_trans_correlation_query ON pos_transactions(rfid_store_code, contract_date, total);
CREATE INDEX IF NOT EXISTS idx_pos_equip_correlation_query ON pos_equipment(rfid_current_store, category, turnover_ytd);

-- 8. Initial correlation population (run once)
-- Populate id_item_master correlation fields
UPDATE id_item_master im
JOIN store_correlations sc ON (
    COALESCE(im.current_store, im.home_store, '000') = sc.rfid_store_code
)
SET 
    im.rfid_store_code = sc.rfid_store_code,
    im.pos_store_code = sc.pos_store_code,
    im.correlation_updated_at = NOW()
WHERE im.rfid_store_code IS NULL;

-- Populate pos_transactions correlation fields  
UPDATE pos_transactions pt
JOIN store_correlations sc ON pt.store_no = sc.pos_store_code
SET 
    pt.rfid_store_code = sc.rfid_store_code,
    pt.correlation_updated_at = NOW()
WHERE pt.rfid_store_code IS NULL;

-- Populate pos_equipment correlation fields
UPDATE pos_equipment pe
JOIN store_correlations sc1 ON pe.home_store = sc1.pos_store_code
LEFT JOIN store_correlations sc2 ON pe.current_store = sc2.pos_store_code
SET 
    pe.rfid_home_store = sc1.rfid_store_code,
    pe.rfid_current_store = COALESCE(sc2.rfid_store_code, sc1.rfid_store_code),
    pe.correlation_updated_at = NOW()
WHERE pe.rfid_home_store IS NULL;

-- Create summary for verification
SELECT 
    'Migration Complete' as status,
    (SELECT COUNT(*) FROM store_correlations WHERE is_active = TRUE) as active_correlations,
    (SELECT COUNT(*) FROM id_item_master WHERE rfid_store_code IS NOT NULL) as correlated_rfid_items,
    (SELECT COUNT(*) FROM pos_transactions WHERE rfid_store_code IS NOT NULL) as correlated_pos_transactions;