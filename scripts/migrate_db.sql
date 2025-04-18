-- Schema for rfid_inventory database
CREATE TABLE id_item_master (
    tag_id VARCHAR(255) PRIMARY KEY,
    uuid_accounts_fk VARCHAR(255),
    serial_number VARCHAR(255),
    client_name VARCHAR(255),
    rental_class_num INT,
    common_name VARCHAR(255),
    quality VARCHAR(50),
    bin_location VARCHAR(255),
    status VARCHAR(50),
    last_contract_num VARCHAR(255),
    last_scanned_by VARCHAR(255),
    notes TEXT,
    status_notes TEXT,
    long FLOAT,
    lat FLOAT,
    date_last_scanned VARCHAR(50),
    date_created VARCHAR(50),
    date_updated VARCHAR(50)
);
CREATE INDEX idx_rental_class ON id_item_master (rental_class_num);
CREATE INDEX idx_status ON id_item_master (status);
CREATE INDEX idx_bin_location ON id_item_master (bin_location);

CREATE TABLE id_rfidtag (
    tag_id VARCHAR(255) PRIMARY KEY,
    item_type VARCHAR(255),
    common_name VARCHAR(255),
    category VARCHAR(255),
    status VARCHAR(50),
    last_contract_num VARCHAR(255),
    date_assigned VARCHAR(50),
    date_sold VARCHAR(50),
    date_discarded VARCHAR(50),
    reuse_count INT,
    last_updated VARCHAR(50)
);
CREATE INDEX idx_rfid_tag_id ON id_rfidtag (tag_id);

CREATE TABLE id_transactions (
    contract_number VARCHAR(255),
    tag_id VARCHAR(255),
    scan_type VARCHAR(50),
    scan_date VARCHAR(50),
    client_name VARCHAR(255),
    common_name VARCHAR(255),
    bin_location VARCHAR(255),
    status VARCHAR(50),
    scan_by VARCHAR(255),
    location_of_repair VARCHAR(255),
    quality VARCHAR(50),
    dirty_or_mud VARCHAR(50),
    leaves VARCHAR(50),
    oil VARCHAR(50),
    mold VARCHAR(50),
    stain VARCHAR(50),
    oxidation VARCHAR(50),
    other VARCHAR(255),
    rip_or_tear VARCHAR(50),
    sewing_repair_needed VARCHAR(50),
    grommet VARCHAR(50),
    rope VARCHAR(50),
    buckle VARCHAR(50),
    date_created VARCHAR(50),
    date_updated VARCHAR(50),
    uuid_accounts_fk VARCHAR(255),
    serial_number VARCHAR(255),
    rental_class_num INT,
    long FLOAT,
    lat FLOAT,
    wet VARCHAR(50),
    service_required VARCHAR(50),
    notes TEXT,
    PRIMARY KEY (contract_number, tag_id, scan_type, scan_date)
);

CREATE TABLE seed_rental_classes (
    rental_class_id INT AUTO_INCREMENT PRIMARY KEY,
    common_name VARCHAR(255),
    bin_location VARCHAR(255)
);

CREATE TABLE refresh_state (
    id INT AUTO_INCREMENT PRIMARY KEY,
    last_refresh VARCHAR(50)
);