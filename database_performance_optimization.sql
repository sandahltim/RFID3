-- Database Performance Optimization for Tab 2
-- Recommended indexes to improve query performance

-- Index for contract number lookups (most common filter)
CREATE INDEX IF NOT EXISTS ix_item_master_contract_status 
ON id_item_master(last_contract_num, status);

-- Composite index for transaction lookups by contract and scan type
CREATE INDEX IF NOT EXISTS ix_transactions_contract_scan_type_date 
ON id_transactions(contract_number, scan_type, scan_date DESC);

-- Index for client name lookups in transactions
CREATE INDEX IF NOT EXISTS ix_transactions_client_name 
ON id_transactions(client_name);

-- Index for common name filtering in ItemMaster
CREATE INDEX IF NOT EXISTS ix_item_master_common_name 
ON id_item_master(common_name);

-- Composite index for store and type filtering (if these columns exist)
-- CREATE INDEX IF NOT EXISTS ix_item_master_store_type 
-- ON id_item_master(home_store, identifier_type);

-- Index for date-based filtering and sorting
CREATE INDEX IF NOT EXISTS ix_item_master_date_last_scanned 
ON id_item_master(date_last_scanned DESC);

-- Index for transaction date filtering and sorting
CREATE INDEX IF NOT EXISTS ix_transactions_scan_date_desc 
ON id_transactions(scan_date DESC);

-- Composite index for the most common Tab 2 query pattern
CREATE INDEX IF NOT EXISTS ix_item_master_status_contract_common 
ON id_item_master(status, last_contract_num, common_name);

-- Index to support the latest transaction subquery
CREATE INDEX IF NOT EXISTS ix_transactions_contract_scantype_date 
ON id_transactions(contract_number, scan_type, scan_date DESC);

-- Analyze tables to update statistics after creating indexes
ANALYZE id_item_master;
ANALYZE id_transactions;

-- Performance monitoring query to check index usage
-- Run this occasionally to ensure indexes are being used:
/*
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE tablename IN ('id_item_master', 'id_transactions')
ORDER BY idx_scan DESC;
*/