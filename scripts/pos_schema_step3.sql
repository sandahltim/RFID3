-- POS Schema Enhancement - Step 3: Store and Inventory Management

-- Store/location management
ALTER TABLE id_item_master
ADD COLUMN IF NOT EXISTS home_store VARCHAR(10) COMMENT 'Home store code',
ADD COLUMN IF NOT EXISTS current_store VARCHAR(10) COMMENT 'Current store location',
ADD COLUMN IF NOT EXISTS quantity INT DEFAULT 1 COMMENT 'Quantity for bulk items';

-- Inventory management
ALTER TABLE id_item_master
ADD COLUMN IF NOT EXISTS reorder_min INT COMMENT 'Minimum reorder level',
ADD COLUMN IF NOT EXISTS reorder_max INT COMMENT 'Maximum reorder level',
ADD COLUMN IF NOT EXISTS last_purchase_date DATETIME COMMENT 'Date of last purchase/acquisition',
ADD COLUMN IF NOT EXISTS last_purchase_price DECIMAL(10,2) COMMENT 'Price of last purchase';