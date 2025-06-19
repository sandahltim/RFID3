-- scripts/fix_collation.sql
ALTER DATABASE rfid_inventory
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

ALTER TABLE rfid_inventory.rental_class_mappings
    CONVERT TO CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;