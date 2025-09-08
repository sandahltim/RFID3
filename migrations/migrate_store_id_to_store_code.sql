-- Migration: Store ID to Store Code Standardization
-- Date: 2025-09-02
-- Description: Standardize all store_id columns to store_code throughout the database

-- Start transaction
START TRANSACTION;

-- 1. Update PayrollTrends table
ALTER TABLE executive_payroll_trends 
CHANGE COLUMN store_id store_code VARCHAR(10) NOT NULL;

-- Update indexes
DROP INDEX ix_payroll_trends_store_id ON executive_payroll_trends;
DROP INDEX ix_payroll_trends_week_store ON executive_payroll_trends;

CREATE INDEX ix_payroll_trends_store_code ON executive_payroll_trends(store_code);
CREATE INDEX ix_payroll_trends_week_store ON executive_payroll_trends(week_ending, store_code);

-- 2. Update ScorecardTrends table  
ALTER TABLE executive_scorecard_trends 
CHANGE COLUMN store_id store_code VARCHAR(10);

-- Update indexes
DROP INDEX ix_scorecard_trends_store_id ON executive_scorecard_trends;
CREATE INDEX ix_scorecard_trends_store_code ON executive_scorecard_trends(store_code);

-- 3. Update ExecutiveKPI table
ALTER TABLE executive_kpi 
CHANGE COLUMN store_id store_code VARCHAR(10);

-- 4. Update BusinessContextKnowledge table
ALTER TABLE business_context_knowledge 
CHANGE COLUMN store_id store_code VARCHAR(10);

-- Update indexes
DROP INDEX idx_context_store ON business_context_knowledge;
CREATE INDEX idx_context_store ON business_context_knowledge(store_code);

-- 5. Update any other tables with store_id references (if they exist)
-- This covers tables that might have been created with store_id

-- Update financial_metrics table if it exists
UPDATE INFORMATION_SCHEMA.COLUMNS 
SET COLUMN_NAME = 'store_code' 
WHERE TABLE_SCHEMA = DATABASE() 
AND COLUMN_NAME = 'store_id' 
AND TABLE_NAME = 'financial_metrics';

-- Update financial_forecasts table if it exists  
UPDATE INFORMATION_SCHEMA.COLUMNS 
SET COLUMN_NAME = 'store_code' 
WHERE TABLE_SCHEMA = DATABASE() 
AND COLUMN_NAME = 'store_id' 
AND TABLE_NAME = 'financial_forecasts';

-- Update store_performance_benchmarks table if it exists
UPDATE INFORMATION_SCHEMA.COLUMNS 
SET COLUMN_NAME = 'store_code' 
WHERE TABLE_SCHEMA = DATABASE() 
AND COLUMN_NAME = 'store_id' 
AND TABLE_NAME = 'store_performance_benchmarks';

-- 6. Validate data integrity after changes
-- Check that all store_code values are valid
SELECT DISTINCT store_code 
FROM executive_payroll_trends 
WHERE store_code NOT IN ('3607', '6800', '8101', '728', '000');

SELECT DISTINCT store_code 
FROM executive_scorecard_trends 
WHERE store_code IS NOT NULL 
AND store_code NOT IN ('3607', '6800', '8101', '728', '000');

-- 7. Update any triggers or stored procedures (if any exist)
-- This would be specific to any custom database objects

-- Log the migration
INSERT INTO migration_log (migration_name, applied_date, description) 
VALUES (
    'migrate_store_id_to_store_code', 
    NOW(), 
    'Standardized all store_id columns to store_code throughout the database'
) ON DUPLICATE KEY UPDATE applied_date = NOW();

-- Commit the transaction
COMMIT;

-- Create a rollback script as well
-- ROLLBACK SCRIPT (run only if rollback is needed):
/*
START TRANSACTION;

-- Revert PayrollTrends table
ALTER TABLE executive_payroll_trends 
CHANGE COLUMN store_code store_id VARCHAR(10) NOT NULL;

DROP INDEX ix_payroll_trends_store_code ON executive_payroll_trends;
DROP INDEX ix_payroll_trends_week_store ON executive_payroll_trends;
CREATE INDEX ix_payroll_trends_store_id ON executive_payroll_trends(store_id);
CREATE INDEX ix_payroll_trends_week_store ON executive_payroll_trends(week_ending, store_id);

-- Revert ScorecardTrends table  
ALTER TABLE executive_scorecard_trends 
CHANGE COLUMN store_code store_id VARCHAR(10);

DROP INDEX ix_scorecard_trends_store_code ON executive_scorecard_trends;
CREATE INDEX ix_scorecard_trends_store_id ON executive_scorecard_trends(store_id);

-- Revert ExecutiveKPI table
ALTER TABLE executive_kpi 
CHANGE COLUMN store_code store_id VARCHAR(10);

-- Revert BusinessContextKnowledge table
ALTER TABLE business_context_knowledge 
CHANGE COLUMN store_code store_id VARCHAR(10);

DROP INDEX idx_context_store ON business_context_knowledge;
CREATE INDEX idx_context_store ON business_context_knowledge(store_id);

COMMIT;
*/