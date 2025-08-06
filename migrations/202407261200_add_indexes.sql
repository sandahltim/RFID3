CREATE INDEX IF NOT EXISTS ix_item_master_rental_class_num ON id_item_master (rental_class_num);
CREATE INDEX IF NOT EXISTS ix_item_master_status ON id_item_master (status);
CREATE INDEX IF NOT EXISTS ix_item_master_bin_location ON id_item_master (bin_location);
CREATE INDEX IF NOT EXISTS ix_rfidtag_rental_class_num ON id_rfidtag (rental_class_num);
CREATE INDEX IF NOT EXISTS ix_rfidtag_status ON id_rfidtag (status);
CREATE INDEX IF NOT EXISTS ix_rfidtag_bin_location ON id_rfidtag (bin_location);
