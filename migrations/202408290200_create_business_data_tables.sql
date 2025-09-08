-- Migration: Create Business Data Tables for CSV Import
-- Date: 2025-08-29
-- Purpose: Add tables to import and store CSV business data for comprehensive analytics

-- Customers table (141,598 records from customer8.26.25.csv)
CREATE TABLE IF NOT EXISTS pos_customers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    cnum VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(200),
    address VARCHAR(200),
    city VARCHAR(100),
    zip VARCHAR(20),
    phone VARCHAR(50),
    open_date DATE,
    last_active_date DATE,
    last_contract VARCHAR(50),
    credit_limit DECIMAL(10,2) DEFAULT 0.00,
    ytd_payments DECIMAL(12,2) DEFAULT 0.00,
    ltd_payments DECIMAL(12,2) DEFAULT 0.00,
    last_year_payments DECIMAL(12,2) DEFAULT 0.00,
    no_of_contracts INT DEFAULT 0,
    current_balance DECIMAL(10,2) DEFAULT 0.00,
    email VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_cnum (cnum),
    INDEX idx_last_active_date (last_active_date),
    INDEX idx_ytd_payments (ytd_payments),
    INDEX idx_no_of_contracts (no_of_contracts)
);

-- Equipment/Inventory table (53,718 records from equip8.26.25.csv) 
CREATE TABLE IF NOT EXISTS pos_equipment (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    item_num VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(300),
    location VARCHAR(50),
    category VARCHAR(100),
    department VARCHAR(100),
    type_desc VARCHAR(100),
    qty INT DEFAULT 0,
    home_store VARCHAR(10),
    current_store VARCHAR(10),
    turnover_mtd DECIMAL(10,2) DEFAULT 0.00,
    turnover_ytd DECIMAL(10,2) DEFAULT 0.00,
    turnover_ltd DECIMAL(12,2) DEFAULT 0.00,
    repair_cost_mtd DECIMAL(10,2) DEFAULT 0.00,
    repair_cost_ltd DECIMAL(12,2) DEFAULT 0.00,
    sell_price DECIMAL(10,2) DEFAULT 0.00,
    retail_price DECIMAL(10,2) DEFAULT 0.00,
    deposit DECIMAL(10,2) DEFAULT 0.00,
    inactive BOOLEAN DEFAULT FALSE,
    last_purchase_date DATE,
    last_purchase_price DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_item_num (item_num),
    INDEX idx_category (category),
    INDEX idx_current_store (current_store),
    INDEX idx_turnover_ytd (turnover_ytd),
    INDEX idx_inactive (inactive)
);

-- Transactions table (246,362 records from transactions8.26.25.csv)
CREATE TABLE IF NOT EXISTS pos_transactions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contract_no VARCHAR(50) NOT NULL,
    store_no VARCHAR(10),
    customer_no VARCHAR(20),
    status VARCHAR(50),
    contract_date DATETIME,
    close_date DATETIME,
    billed_date DATETIME,
    completed_date DATETIME,
    rent_amt DECIMAL(10,2) DEFAULT 0.00,
    sale_amt DECIMAL(10,2) DEFAULT 0.00,
    tax_amt DECIMAL(10,2) DEFAULT 0.00,
    total DECIMAL(10,2) DEFAULT 0.00,
    total_paid DECIMAL(10,2) DEFAULT 0.00,
    total_owed DECIMAL(10,2) DEFAULT 0.00,
    deposit_paid_amt DECIMAL(10,2) DEFAULT 0.00,
    payment_method VARCHAR(50),
    contact VARCHAR(200),
    contact_phone VARCHAR(50),
    delivery_address VARCHAR(300),
    delivery_date DATETIME,
    pickup_date DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_contract_no (contract_no),
    INDEX idx_customer_no (customer_no),
    INDEX idx_store_no (store_no),
    INDEX idx_contract_date (contract_date),
    INDEX idx_status (status),
    INDEX idx_total (total)
);

-- Transaction Items table (597,389 records from transitems8.26.25.csv)
CREATE TABLE IF NOT EXISTS pos_transaction_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contract_no VARCHAR(50) NOT NULL,
    item_num VARCHAR(20) NOT NULL,
    qty INT DEFAULT 1,
    hours INT DEFAULT 0,
    due_date DATETIME,
    line_status VARCHAR(10),
    price DECIMAL(10,2) DEFAULT 0.00,
    description TEXT,
    discount_percent DECIMAL(5,2) DEFAULT 0.00,
    discount_amt DECIMAL(10,2) DEFAULT 0.00,
    retail_price DECIMAL(10,2) DEFAULT 0.00,
    line_number INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_contract_no (contract_no),
    INDEX idx_item_num (item_num),
    INDEX idx_due_date (due_date),
    INDEX idx_price (price),
    INDEX idx_line_status (line_status)
);

-- Payroll Trends table (from Payroll Trends.csv)
CREATE TABLE IF NOT EXISTS pos_payroll_trends (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    period_ending DATE NOT NULL,
    store_code VARCHAR(10) NOT NULL,
    rental_revenue DECIMAL(12,2) DEFAULT 0.00,
    all_revenue DECIMAL(12,2) DEFAULT 0.00,
    payroll DECIMAL(12,2) DEFAULT 0.00,
    wage_hours DECIMAL(8,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_period_ending (period_ending),
    INDEX idx_store_code (store_code),
    UNIQUE KEY unique_period_store (period_ending, store_code)
);

-- Enhanced resale analytics with business data integration
ALTER TABLE resale_analytics 
ADD COLUMN pos_item_num VARCHAR(20) AFTER tag_id,
ADD COLUMN business_turnover_ytd DECIMAL(12,2) DEFAULT 0.00,
ADD COLUMN business_repair_cost_ytd DECIMAL(12,2) DEFAULT 0.00,
ADD COLUMN contract_frequency INT DEFAULT 0,
ADD COLUMN avg_rental_price DECIMAL(10,2) DEFAULT 0.00,
ADD COLUMN last_business_activity DATE,
ADD INDEX idx_pos_item_num (pos_item_num),
ADD INDEX idx_business_turnover_ytd (business_turnover_ytd),
ADD INDEX idx_last_business_activity (last_business_activity);