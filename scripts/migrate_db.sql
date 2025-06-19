-- scripts/migrate_db.sql
-- migrate_db.sql version: 2025-06-19-v3

-- Drop existing tables if they exist
DROP TABLE IF EXISTS id_transactions;
DROP TABLE IF EXISTS id_item_master;
DROP TABLE IF EXISTS id_rfidtag;
DROP TABLE IF EXISTS seed_rental_classes;
DROP TABLE IF EXISTS refresh_state;
DROP TABLE IF EXISTS rental_class_mappings;
DROP TABLE IF EXISTS id_hand_counted_items;
DROP TABLE IF EXISTS user_rental_class_mappings;

-- Create id_transactions table
CREATE TABLE id_transactions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contract_number VARCHAR(255),
    tag_id VARCHAR(255) NOT NULL,
    scan_type VARCHAR(50) NOT NULL,
    scan_date DATETIME NOT NULL,
    client_name VARCHAR(255),
    common_name VARCHAR(255) NOT NULL,
    bin_location VARCHAR(255),
    status VARCHAR(50),
    scan_by VARCHAR(255),
    location_of_repair VARCHAR(255),
    quality VARCHAR(50),
    dirty_or_mud BOOLEAN,
    leaves BOOLEAN,
    oil BOOLEAN,
    mold BOOLEAN,
    stain BOOLEAN,
    oxidation BOOLEAN,
    other TEXT,
    rip_or_tear BOOLEAN,
    sewing_repair_needed BOOLEAN,
    grommet BOOLEAN,
    rope BOOLEAN,
    buckle BOOLEAN,
    date_created DATETIME,
    date_updated DATETIME,
    uuid_accounts_fk VARCHAR(255),
    serial_number VARCHAR(255),
    rental_class_num VARCHAR(255),
    longitude DECIMAL(9,6),
    latitude DECIMAL(9,6),
    wet BOOLEAN,
    service_required BOOLEAN,
    notes TEXT
);

-- Create id_item_master table
CREATE TABLE id_item_master (
    tag_id VARCHAR(255) PRIMARY KEY,
    uuid_accounts_fk VARCHAR(255),
    serial_number VARCHAR(255),
    client_name VARCHAR(255),
    rental_class_num VARCHAR(255),
    common_name VARCHAR(255),
    quality VARCHAR(50),
    bin_location VARCHAR(255),
    status VARCHAR(50),
    last_contract_num VARCHAR(255),
    last_scanned_by VARCHAR(255),
    notes TEXT,
    status_notes TEXT,
    longitude DECIMAL(9,6),
    latitude DECIMAL(9,6),
    date_last_scanned DATETIME,
    date_created DATETIME,
    date_updated DATETIME
);

-- Create id_rfidtag table
CREATE TABLE id_rfidtag (
    tag_id VARCHAR(255) PRIMARY KEY,
    uuid_accounts_fk VARCHAR(255),
    category VARCHAR(255),
    serial_number VARCHAR(255),
    client_name VARCHAR(255),
    rental_class_num VARCHAR(255),
    common_name VARCHAR(255),
    quality VARCHAR(50),
    bin_location VARCHAR(255),
    status VARCHAR(50),
    last_contract_num VARCHAR(255),
    last_scanned_by VARCHAR(255),
    notes TEXT,
    status_notes TEXT,
    longitude DECIMAL(9,6),
    latitude DECIMAL(9,6),
    date_last_scanned DATETIME,
    date_created DATETIME,
    date_updated DATETIME
);

-- Create seed_rental_classes table
CREATE TABLE seed_rental_classes (
    rental_class_id VARCHAR(255) PRIMARY KEY,
    common_name VARCHAR(255),
    bin_location VARCHAR(255)
);

-- Create refresh_state table
CREATE TABLE refresh_state (
    id INT PRIMARY KEY AUTO_INCREMENT,
    last_refresh DATETIME,  -- Changed to DATETIME
    state_type VARCHAR(50)  -- Added state_type
);

-- Create rental_class_mappings table
CREATE TABLE rental_class_mappings (
    rental_class_id VARCHAR(50) PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100) NOT NULL,
    short_common_name VARCHAR(50)
);

-- Create id_hand_counted_items table
CREATE TABLE id_hand_counted_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    contract_number VARCHAR(50) NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    action VARCHAR(50) NOT NULL,
    timestamp DATETIME NOT NULL,
    user VARCHAR(50) NOT NULL
);

-- Create user_rental_class_mappings table
CREATE TABLE user_rental_class_mappings (
    rental_class_id VARCHAR(50) PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100) NOT NULL,
    short_common_name VARCHAR(50),
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);