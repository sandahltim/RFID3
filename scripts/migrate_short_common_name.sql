-- migrate_short_common_name.sql version: 2025-06-19-v1
-- Add short_common_name column to rental_class_mappings table
ALTER TABLE rental_class_mappings
ADD COLUMN short_common_name VARCHAR(50);

-- Add short_common_name column to user_rental_class_mappings table
ALTER TABLE user_rental_class_mappings
ADD COLUMN short_common_name VARCHAR(50);

-- Populate short_common_name in rental_class_mappings by truncating common_name to 20 characters
UPDATE rental_class_mappings rcm
JOIN seed_rental_classes src ON rcm.rental_class_id = src.rental_class_id
SET rcm.short_common_name = LEFT(src.common_name, 20);

-- Populate short_common_name in user_rental_class_mappings by truncating common_name to 20 characters
UPDATE user_rental_class_mappings urcm
JOIN seed_rental_classes src ON urcm.rental_class_id = src.rental_class_id
SET urcm.short_common_name = LEFT(src.common_name, 20);