CREATE INDEX IF NOT EXISTS ix_transactions_tag_id ON id_transactions (tag_id);
CREATE INDEX IF NOT EXISTS ix_transactions_scan_date ON id_transactions (scan_date);
CREATE INDEX IF NOT EXISTS ix_transactions_status ON id_transactions (status);

