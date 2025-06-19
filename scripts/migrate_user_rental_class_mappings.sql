-- migrate_user_rental_class_mappings.sql version: 2025-06-19-v1
-- Migration script to add the user_rental_class_mappings table
-- Added on 2025-04-23 to store user-defined mappings separately

CREATE TABLE IF NOT EXISTS user_rental_class_mappings (
    rental_class_id VARCHAR(50) PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Add indexes for faster lookups
CREATE INDEX idx_user_rental_class_mappings_rental_class_id ON user_rental_class_mappings (rental_class_id);