-- Migration script to add the HandCountedItems table
-- Added on 2025-04-21 for tracking hand-counted items on contracts

CREATE TABLE IF NOT EXISTS id_hand_counted_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    contract_number VARCHAR(50) NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    action VARCHAR(50) NOT NULL,
    timestamp DATETIME NOT NULL,
    user VARCHAR(50) NOT NULL
);

-- Add indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_hand_counted_items_contract_number ON id_hand_counted_items (contract_number);
CREATE INDEX IF NOT EXISTS idx_hand_counted_items_timestamp ON id_hand_counted_items (timestamp);

-- Table for catalog of common hand-counted items
CREATE TABLE IF NOT EXISTS hand_counted_catalog (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rental_class_id VARCHAR(50),
    item_name VARCHAR(255) NOT NULL UNIQUE
);

-- Add index for hand_counted_catalog
CREATE INDEX IF NOT EXISTS idx_hand_counted_catalog_rental_class_id ON hand_counted_catalog (rental_class_id);