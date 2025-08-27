-- POS Schema Enhancement - Step 2: Financial and Business Metrics

-- Financial metrics
ALTER TABLE id_item_master
ADD COLUMN IF NOT EXISTS turnover_mtd DECIMAL(10,2) COMMENT 'Month-to-date turnover revenue',
ADD COLUMN IF NOT EXISTS turnover_ytd DECIMAL(10,2) COMMENT 'Year-to-date turnover revenue', 
ADD COLUMN IF NOT EXISTS turnover_ltd DECIMAL(10,2) COMMENT 'Life-to-date turnover revenue',
ADD COLUMN IF NOT EXISTS repair_cost_mtd DECIMAL(10,2) COMMENT 'Month-to-date repair costs',
ADD COLUMN IF NOT EXISTS repair_cost_ltd DECIMAL(10,2) COMMENT 'Life-to-date repair costs';

-- Pricing fields
ALTER TABLE id_item_master
ADD COLUMN IF NOT EXISTS sell_price DECIMAL(10,2) COMMENT 'Selling/resale price',
ADD COLUMN IF NOT EXISTS retail_price DECIMAL(10,2) COMMENT 'Retail rental price',
ADD COLUMN IF NOT EXISTS deposit DECIMAL(10,2) COMMENT 'Required deposit amount',
ADD COLUMN IF NOT EXISTS damage_waiver_pct DECIMAL(5,2) COMMENT 'Damage waiver percentage';