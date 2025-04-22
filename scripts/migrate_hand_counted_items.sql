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
CREATE INDEX idx_hand_counted_items_contract_number ON id_hand_counted_items (contract_number);
CREATE INDEX idx_hand_counted_items_timestamp ON id_hand_counted_items (timestamp);