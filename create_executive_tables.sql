-- Executive Dashboard Tables Creation Script
-- Run this to create the necessary tables for Tab 7 Executive Dashboard

-- Table: executive_payroll_trends
CREATE TABLE IF NOT EXISTS executive_payroll_trends (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    week_ending DATE NOT NULL,
    store_id VARCHAR(10) NOT NULL,
    rental_revenue DECIMAL(12, 2),
    total_revenue DECIMAL(12, 2),
    payroll_cost DECIMAL(12, 2),
    wage_hours DECIMAL(10, 2),
    labor_efficiency_ratio DECIMAL(5, 2),
    revenue_per_hour DECIMAL(10, 2),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX ix_payroll_trends_week_ending (week_ending),
    INDEX ix_payroll_trends_store_id (store_id),
    INDEX ix_payroll_trends_week_store (week_ending, store_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: executive_scorecard_trends
CREATE TABLE IF NOT EXISTS executive_scorecard_trends (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    week_ending DATE NOT NULL,
    store_id VARCHAR(10),
    total_weekly_revenue DECIMAL(12, 2),
    new_contracts_count INT,
    open_quotes_count INT,
    deliveries_scheduled_next_7_days INT,
    reservation_value_next_14_days DECIMAL(12, 2),
    total_reservation_value DECIMAL(12, 2),
    ar_over_45_days_percent DECIMAL(5, 2),
    total_ar_cash_customers DECIMAL(12, 2),
    total_discount_amount DECIMAL(12, 2),
    week_number INT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX ix_scorecard_trends_week_ending (week_ending),
    INDEX ix_scorecard_trends_store_id (store_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table: executive_kpi
CREATE TABLE IF NOT EXISTS executive_kpi (
    id INT AUTO_INCREMENT PRIMARY KEY,
    kpi_name VARCHAR(100) NOT NULL UNIQUE,
    kpi_category VARCHAR(50),
    current_value DECIMAL(15, 2),
    target_value DECIMAL(15, 2),
    variance_percent DECIMAL(5, 2),
    trend_direction VARCHAR(10),
    period VARCHAR(20),
    store_id VARCHAR(10),
    last_calculated DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX ix_kpi_name (kpi_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Grant permissions (adjust user as needed)
-- GRANT ALL PRIVILEGES ON executive_* TO 'your_db_user'@'localhost';

COMMIT;
