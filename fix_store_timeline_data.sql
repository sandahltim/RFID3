-- ================================================================================
-- STORE TIMELINE DATA CORRECTION SCRIPT
-- Purpose: Fix data quality issues and establish proper store correlations
-- Date: 2025-09-01
-- ================================================================================

-- Step 1: Create master store reference table with correct timeline
-- --------------------------------------------------------------------------------
DROP TABLE IF EXISTS store_master;
CREATE TABLE store_master (
    store_id VARCHAR(10) PRIMARY KEY,
    store_name VARCHAR(100) NOT NULL,
    location VARCHAR(100),
    opened_date DATE NOT NULL,
    pos_code VARCHAR(10) UNIQUE,
    gl_code VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_opened_date (opened_date),
    INDEX idx_pos_code (pos_code),
    INDEX idx_active (is_active)
);

-- Insert correct store data with proper timeline
INSERT INTO store_master (store_id, store_name, location, opened_date, pos_code, gl_code, is_active, notes) VALUES
('3607', 'Wayzata', 'Wayzata, MN', '2008-01-01', '1', '3607', TRUE, 'Original store, longest history'),
('6800', 'Brooklyn Park', 'Brooklyn Park, MN', '2022-01-01', '2', '6800', TRUE, 'Added in 2022'),
('8101', 'Fridley', 'Fridley, MN', '2022-01-01', '3', '8101', TRUE, 'Added in 2022'),
('728', 'Elk River', 'Elk River, MN', '2024-01-01', '4', '728', TRUE, 'Newest store, added in 2024');

-- Step 2: Add store_master_id to POS transactions for proper correlation
-- --------------------------------------------------------------------------------
ALTER TABLE pos_transactions ADD COLUMN IF NOT EXISTS store_master_id VARCHAR(10);
ALTER TABLE pos_transactions ADD INDEX IF NOT EXISTS idx_store_master_id (store_master_id);

-- Update store_master_id based on store_no mapping
UPDATE pos_transactions pt
JOIN store_master sm ON sm.pos_code = pt.store_no
SET pt.store_master_id = sm.store_id;

-- Step 3: Create data quality audit table
-- --------------------------------------------------------------------------------
DROP TABLE IF EXISTS data_quality_audit_log;
CREATE TABLE data_quality_audit_log (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(100),
    store_id VARCHAR(10),
    issue_type VARCHAR(50),
    records_affected INT,
    original_value TEXT,
    corrected_value TEXT,
    correction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_table_store (table_name, store_id),
    INDEX idx_issue_type (issue_type),
    INDEX idx_correction_date (correction_date)
);

-- Step 4: Identify and log problematic POS transactions
-- --------------------------------------------------------------------------------
-- Log transactions that predate store openings
INSERT INTO data_quality_audit_log (table_name, store_id, issue_type, records_affected, original_value)
SELECT 
    'pos_transactions' as table_name,
    sm.store_id,
    'DATA_BEFORE_STORE_OPENING' as issue_type,
    COUNT(*) as records_affected,
    CONCAT('Dates from ', MIN(pt.contract_date), ' to ', MAX(pt.contract_date)) as original_value
FROM pos_transactions pt
JOIN store_master sm ON sm.pos_code = pt.store_no
WHERE pt.contract_date < sm.opened_date
GROUP BY sm.store_id;

-- Log future-dated transactions (more than 1 year in future)
INSERT INTO data_quality_audit_log (table_name, store_id, issue_type, records_affected, original_value)
SELECT 
    'pos_transactions' as table_name,
    sm.store_id,
    'FUTURE_DATE' as issue_type,
    COUNT(*) as records_affected,
    CONCAT('Future dates found: ', MIN(pt.contract_date), ' to ', MAX(pt.contract_date)) as original_value
FROM pos_transactions pt
JOIN store_master sm ON sm.pos_code = pt.store_no
WHERE pt.contract_date > DATE_ADD(CURDATE(), INTERVAL 1 YEAR)
GROUP BY sm.store_id;

-- Step 5: Fix date issues - Add 10 years to dates that are too old
-- --------------------------------------------------------------------------------
-- Fix Wayzata (store 1/3607) dates from 2000-2007 (should be 2010-2017)
UPDATE pos_transactions pt
JOIN store_master sm ON sm.pos_code = pt.store_no
SET pt.contract_date = DATE_ADD(pt.contract_date, INTERVAL 10 YEAR)
WHERE sm.store_id = '3607' 
    AND pt.contract_date < '2008-01-01'
    AND pt.contract_date >= '2000-01-01';

-- Fix Brooklyn Park dates before 2022
UPDATE pos_transactions pt
JOIN store_master sm ON sm.pos_code = pt.store_no
SET pt.contract_date = DATE_ADD(pt.contract_date, INTERVAL 1 YEAR)
WHERE sm.store_id = '6800' 
    AND pt.contract_date < '2022-01-01'
    AND pt.contract_date >= '2021-01-01';

-- Fix Fridley dates before 2022
UPDATE pos_transactions pt
JOIN store_master sm ON sm.pos_code = pt.store_no
SET pt.contract_date = DATE_ADD(pt.contract_date, INTERVAL 20 YEAR)
WHERE sm.store_id = '8101' 
    AND pt.contract_date < '2022-01-01'
    AND pt.contract_date >= '2002-01-01';

-- Fix Elk River dates before 2024
UPDATE pos_transactions pt
JOIN store_master sm ON sm.pos_code = pt.store_no
SET pt.contract_date = DATE_ADD(pt.contract_date, INTERVAL 10 YEAR)
WHERE sm.store_id = '728' 
    AND pt.contract_date < '2024-01-01'
    AND pt.contract_date >= '2014-01-01';

-- Step 6: Create unified views for clean data access
-- --------------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_pos_transactions_clean AS
SELECT 
    pt.*,
    sm.store_id as unified_store_id,
    sm.store_name,
    sm.location as store_location,
    sm.opened_date as store_opened_date,
    CASE 
        WHEN pt.contract_date < sm.opened_date THEN 'INVALID_DATE'
        WHEN pt.contract_date > DATE_ADD(CURDATE(), INTERVAL 1 YEAR) THEN 'FUTURE_DATE'
        ELSE 'VALID'
    END as date_validity
FROM pos_transactions pt
LEFT JOIN store_master sm ON sm.pos_code = pt.store_no;

-- Step 7: Create store performance correlation view
-- --------------------------------------------------------------------------------
CREATE OR REPLACE VIEW v_store_performance_correlation AS
SELECT 
    sm.store_id,
    sm.store_name,
    sm.location,
    sm.opened_date,
    -- POS Metrics
    COUNT(DISTINCT pt.contract_no) as total_pos_transactions,
    MIN(pt.contract_date) as earliest_pos_date,
    MAX(pt.contract_date) as latest_pos_date,
    SUM(pt.total) as total_pos_revenue,
    -- Payroll Metrics
    MIN(ept.week_ending) as earliest_payroll_date,
    MAX(ept.week_ending) as latest_payroll_date,
    AVG(ept.total_revenue) as avg_weekly_revenue,
    AVG(ept.labor_efficiency_ratio) as avg_labor_efficiency,
    -- Data Quality Metrics
    SUM(CASE WHEN pt.contract_date < sm.opened_date THEN 1 ELSE 0 END) as invalid_date_count,
    SUM(CASE WHEN pt.contract_date > DATE_ADD(CURDATE(), INTERVAL 1 YEAR) THEN 1 ELSE 0 END) as future_date_count
FROM store_master sm
LEFT JOIN pos_transactions pt ON pt.store_no = sm.pos_code
LEFT JOIN executive_payroll_trends ept ON ept.store_id = sm.store_id
GROUP BY sm.store_id, sm.store_name, sm.location, sm.opened_date;

-- Step 8: Create triggers to prevent future data quality issues
-- --------------------------------------------------------------------------------
DELIMITER //

DROP TRIGGER IF EXISTS trg_validate_pos_dates//
CREATE TRIGGER trg_validate_pos_dates
BEFORE INSERT ON pos_transactions
FOR EACH ROW
BEGIN
    DECLARE store_open_date DATE;
    
    -- Get store opening date
    SELECT opened_date INTO store_open_date
    FROM store_master
    WHERE pos_code = NEW.store_no;
    
    -- Validate date is not before store opening
    IF NEW.contract_date < store_open_date THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Contract date cannot be before store opening date';
    END IF;
    
    -- Validate date is not too far in future
    IF NEW.contract_date > DATE_ADD(CURDATE(), INTERVAL 1 YEAR) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Contract date cannot be more than 1 year in the future';
    END IF;
END//

DELIMITER ;

-- Step 9: Create store correlation analysis function
-- --------------------------------------------------------------------------------
DELIMITER //

DROP FUNCTION IF EXISTS get_store_data_quality_score//
CREATE FUNCTION get_store_data_quality_score(p_store_id VARCHAR(10))
RETURNS DECIMAL(5,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE total_records INT;
    DECLARE valid_records INT;
    DECLARE quality_score DECIMAL(5,2);
    
    SELECT 
        COUNT(*),
        SUM(CASE 
            WHEN pt.contract_date >= sm.opened_date 
                AND pt.contract_date <= DATE_ADD(CURDATE(), INTERVAL 1 YEAR) 
            THEN 1 
            ELSE 0 
        END)
    INTO total_records, valid_records
    FROM pos_transactions pt
    JOIN store_master sm ON sm.pos_code = pt.store_no
    WHERE sm.store_id = p_store_id;
    
    IF total_records = 0 THEN
        RETURN 0;
    END IF;
    
    SET quality_score = (valid_records / total_records) * 100;
    RETURN quality_score;
END//

DELIMITER ;

-- Step 10: Generate summary report
-- --------------------------------------------------------------------------------
SELECT 
    'STORE DATA QUALITY REPORT' as report_title,
    NOW() as generated_at;

SELECT 
    sm.store_id,
    sm.store_name,
    sm.opened_date,
    get_store_data_quality_score(sm.store_id) as data_quality_score,
    COUNT(DISTINCT pt.contract_no) as total_transactions,
    MIN(pt.contract_date) as earliest_transaction,
    MAX(pt.contract_date) as latest_transaction
FROM store_master sm
LEFT JOIN pos_transactions pt ON pt.store_no = sm.pos_code
GROUP BY sm.store_id, sm.store_name, sm.opened_date
ORDER BY sm.store_id;

-- Show data quality issues summary
SELECT 
    issue_type,
    COUNT(*) as issue_count,
    SUM(records_affected) as total_records_affected
FROM data_quality_audit_log
GROUP BY issue_type;

-- ================================================================================
-- END OF SCRIPT
-- ================================================================================