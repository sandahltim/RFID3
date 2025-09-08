
-- RFID3 Phase 3 Database Optimization Script
-- Created: 2025-08-31 15:12:39
-- Purpose: Minnesota Equipment Rental Business Intelligence Enhancement

-- 1. Equipment Categorization Columns
ALTER TABLE id_item_master 
ADD COLUMN equipment_category VARCHAR(50) DEFAULT 'Uncategorized',
ADD COLUMN business_line VARCHAR(30) DEFAULT 'Mixed',
ADD COLUMN category_confidence DECIMAL(3,2) DEFAULT 0.50,
ADD COLUMN subcategory VARCHAR(50) DEFAULT 'General',
ADD COLUMN last_categorized DATETIME DEFAULT NULL;

-- 2. Enhanced Indexing for Analytics
CREATE INDEX idx_item_master_analytics ON id_item_master(
    current_store, equipment_category, business_line, status, turnover_ytd
);

CREATE INDEX idx_transactions_analytics ON id_transactions(
    tag_id, scan_date, scan_type, status
);

CREATE INDEX idx_scorecard_trends_analytics ON scorecard_trends_data(
    week_ending, total_weekly_revenue
);

CREATE INDEX idx_payroll_trends_analytics ON payroll_trends_data(
    week_ending, location_code, rental_revenue, payroll_amount
);

-- 3. Store Performance View
CREATE VIEW store_performance_summary AS
SELECT 
    im.current_store,
    COUNT(*) as total_items,
    SUM(CASE WHEN im.equipment_category = 'A1_RentIt_Construction' THEN 1 ELSE 0 END) as construction_items,
    SUM(CASE WHEN im.equipment_category = 'Broadway_TentEvent' THEN 1 ELSE 0 END) as event_items,
    AVG(im.turnover_ytd) as avg_turnover,
    SUM(im.turnover_ytd) as total_turnover,
    MAX(im.date_last_scanned) as last_activity
FROM id_item_master im
WHERE im.status != 'Retired'
GROUP BY im.current_store;

-- 4. Financial Analytics Helper View
CREATE VIEW weekly_financial_summary AS
SELECT 
    std.week_ending,
    std.total_weekly_revenue,
    std.revenue_3607 + std.revenue_6800 + std.revenue_728 + std.revenue_8101 as calculated_total,
    (std.new_contracts_3607 + std.new_contracts_6800 + std.new_contracts_728 + std.new_contracts_8101) as total_new_contracts,
    (std.reservation_next14_3607 + std.reservation_next14_6800 + std.reservation_next14_728 + std.reservation_next14_8101) as total_future_bookings,
    std.ar_over_45_days_percent,
    std.total_discount
FROM scorecard_trends_data std
ORDER BY std.week_ending DESC;

-- 5. Equipment Utilization Analytics
CREATE VIEW equipment_utilization_analysis AS
SELECT 
    im.rental_class_num,
    im.common_name,
    im.current_store,
    im.equipment_category,
    im.business_line,
    im.turnover_ytd,
    pe.turnover_ytd as pos_turnover_ytd,
    COUNT(t.id) as scan_count,
    MAX(t.scan_date) as last_scan,
    AVG(CASE WHEN t.scan_type = 'On Rent' THEN 1 ELSE 0 END) as utilization_rate
FROM id_item_master im
LEFT JOIN pos_rfid_correlations prc ON im.rental_class_num = prc.rfid_rental_class_num
LEFT JOIN pos_equipment pe ON prc.pos_item_num = pe.item_num
LEFT JOIN id_transactions t ON im.tag_id = t.tag_id
WHERE im.status != 'Retired'
GROUP BY im.tag_id, im.rental_class_num, im.common_name, im.current_store, 
         im.equipment_category, im.business_line, im.turnover_ytd, pe.turnover_ytd;

-- 6. Minnesota Seasonal Analytics Preparation
CREATE TABLE IF NOT EXISTS minnesota_seasonal_patterns (
    id INT AUTO_INCREMENT PRIMARY KEY,
    season VARCHAR(20) NOT NULL,
    equipment_category VARCHAR(50) NOT NULL,
    demand_multiplier DECIMAL(4,2) DEFAULT 1.00,
    peak_weeks VARCHAR(100),
    weather_sensitivity DECIMAL(3,2) DEFAULT 0.50,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Insert Minnesota seasonal patterns
INSERT INTO minnesota_seasonal_patterns (season, equipment_category, demand_multiplier, peak_weeks, weather_sensitivity, notes) VALUES
('Spring', 'A1_RentIt_Construction', 1.30, '12-20', 0.80, 'Construction season startup, frost thaw impact'),
('Summer', 'Broadway_TentEvent', 1.50, '22-35', 0.90, 'Peak wedding and event season'),
('Summer', 'A1_RentIt_Construction', 1.20, '20-35', 0.60, 'Continued construction activity'),
('Fall', 'A1_RentIt_Construction', 1.10, '35-45', 0.70, 'Project completion rush'),
('Fall', 'Broadway_TentEvent', 0.80, '35-45', 0.85, 'Outdoor event season wind-down'),
('Winter', 'A1_RentIt_Construction', 0.70, '48-10', 0.60, 'Indoor work focus, heating equipment'),
('Winter', 'Broadway_TentEvent', 0.90, '48-10', 0.40, 'Holiday events, indoor venues');

-- 7. Performance Monitoring
CREATE TABLE IF NOT EXISTS system_performance_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,4),
    store_code VARCHAR(10),
    measurement_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- 8. Correlation Tracking
CREATE TABLE IF NOT EXISTS business_correlations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    correlation_type VARCHAR(50) NOT NULL,
    factor_a VARCHAR(100) NOT NULL,
    factor_b VARCHAR(100) NOT NULL,
    correlation_strength DECIMAL(4,3),
    statistical_significance DECIMAL(4,3),
    date_range_start DATE,
    date_range_end DATE,
    store_code VARCHAR(10),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100) DEFAULT 'system'
);

COMMIT;
