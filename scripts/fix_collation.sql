-- scripts/fix_collation.sql
ALTER DATABASE rfid_inventory
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

ALTER TABLE rfid_inventory.id_transactions
    CONVERT TO CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

ALTER TABLE rfid_inventory.id_item_master
    CONVERT TO CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

ALTER TABLE rfid_inventory.id_rfidtag
    CONVERT TO CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

ALTER TABLE rfid_inventory.seed_rental_classes
    CONVERT TO CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

ALTER TABLE rfid_inventory.refresh_state
    CONVERT TO CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

ALTER TABLE rfid_inventory.rental_class_mappings
    CONVERT TO CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

ALTER TABLE rfid_inventory.id_hand_counted_items
    CONVERT TO CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

ALTER TABLE rfid_inventory.user_rental_class_mappings
    CONVERT TO CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;