-- EXECUTIVE DASHBOARD DATA CORRELATION QUERIES
-- Enhanced analytics for KVC Companies executive insights
-- Generated: 2025-09-01

-- ================================================================
-- 1. STORE PERFORMANCE CORRELATION
-- ================================================================

-- 1.1 Unified Store Revenue with RFID Transaction Correlation
CREATE VIEW IF NOT EXISTS v_store_revenue_correlation AS
WITH rfid_activity AS (
    SELECT 
        CASE 
            WHEN im.home_store = '3607' THEN 'TYLER'
            WHEN im.home_store = '6800' THEN 'ZACK'
            WHEN im.home_store = '728' THEN 'BRUCE'
            WHEN im.home_store = '8101' THEN 'TIM'
            ELSE im.home_store
        END as store_name,
        im.home_store as store_code,
        DATE(t.scan_date, 'start of week') as week_start,
        COUNT(DISTINCT t.contract_number) as rfid_contracts,
        COUNT(DISTINCT t.tag_id) as items_transacted,
        COUNT(CASE WHEN t.scan_type = 'Rental' THEN 1 END) as rental_count,
        COUNT(CASE WHEN t.scan_type = 'Delivery' THEN 1 END) as delivery_count,
        COUNT(CASE WHEN t.scan_type = 'Return' THEN 1 END) as return_count
    FROM id_transactions t
    JOIN id_item_master im ON t.tag_id = im.tag_id
    WHERE t.scan_date >= DATE('now', '-6 months')
    GROUP BY im.home_store, DATE(t.scan_date, 'start of week')
),
pos_revenue AS (
    SELECT 
        store_code,
        DATE(transaction_date, 'start of week') as week_start,
        COUNT(DISTINCT contract_number) as pos_contracts,
        SUM(amount) as weekly_revenue,
        AVG(amount) as avg_transaction_value
    FROM pos_transactions
    WHERE transaction_date >= DATE('now', '-6 months')
    GROUP BY store_code, DATE(transaction_date, 'start of week')
),
financial_metrics AS (
    SELECT 
        store_code,
        week_start,
        SUM(revenue) as pl_revenue,
        SUM(gross_profit) as pl_gross_profit,
        SUM(expenses) as pl_expenses,
        (SUM(gross_profit) / NULLIF(SUM(revenue), 0)) * 100 as profit_margin_pct
    FROM pl_data
    WHERE week_start >= DATE('now', '-6 months')
    GROUP BY store_code, week_start
)
SELECT 
    COALESCE(r.store_name, p.store_code, f.store_code) as store_name,
    COALESCE(r.store_code, p.store_code, f.store_code) as store_code,
    COALESCE(r.week_start, p.week_start, f.week_start) as week_start,
    -- RFID Metrics
    r.rfid_contracts,
    r.items_transacted,
    r.rental_count,
    r.delivery_count,
    r.return_count,
    -- POS Metrics
    p.pos_contracts,
    p.weekly_revenue as pos_revenue,
    p.avg_transaction_value,
    -- Financial Metrics
    f.pl_revenue,
    f.pl_gross_profit,
    f.pl_expenses,
    f.profit_margin_pct,
    -- Calculated KPIs
    CASE 
        WHEN r.rfid_contracts > 0 
        THEN p.weekly_revenue / r.rfid_contracts 
        ELSE NULL 
    END as revenue_per_rfid_contract,
    CASE 
        WHEN r.items_transacted > 0 
        THEN p.weekly_revenue / r.items_transacted 
        ELSE NULL 
    END as revenue_per_item,
    CASE 
        WHEN p.pos_contracts > 0 AND r.rfid_contracts > 0
        THEN (r.rfid_contracts * 100.0) / p.pos_contracts
        ELSE NULL
    END as rfid_coverage_pct
FROM rfid_activity r
FULL OUTER JOIN pos_revenue p 
    ON r.store_code = p.store_code 
    AND r.week_start = p.week_start
FULL OUTER JOIN financial_metrics f 
    ON COALESCE(r.store_code, p.store_code) = f.store_code 
    AND COALESCE(r.week_start, p.week_start) = f.week_start
ORDER BY week_start DESC, store_name;

-- ================================================================
-- 2. EQUIPMENT UTILIZATION ANALYTICS
-- ================================================================

-- 2.1 Equipment Class Performance with Financial Correlation
CREATE VIEW IF NOT EXISTS v_equipment_class_performance AS
WITH equipment_inventory AS (
    SELECT 
        rental_class_num,
        home_store,
        COUNT(*) as total_units,
        SUM(CASE WHEN status = 'Available' THEN 1 ELSE 0 END) as available_units,
        SUM(CASE WHEN status IN ('Rented', 'On Contract') THEN 1 ELSE 0 END) as rented_units,
        SUM(CASE WHEN status = 'In Repair' THEN 1 ELSE 0 END) as repair_units,
        AVG(CAST(turnover_ytd AS FLOAT)) as avg_turnover_ytd,
        AVG(CAST(sell_price AS FLOAT)) as avg_sell_price,
        AVG(CAST(retail_price AS FLOAT)) as avg_retail_price
    FROM id_item_master
    WHERE rental_class_num IS NOT NULL
    GROUP BY rental_class_num, home_store
),
rental_activity AS (
    SELECT 
        im.rental_class_num,
        im.home_store,
        COUNT(DISTINCT t.contract_number) as rental_transactions,
        COUNT(DISTINCT DATE(t.scan_date)) as active_days,
        MIN(t.scan_date) as first_rental_date,
        MAX(t.scan_date) as last_rental_date,
        COUNT(DISTINCT t.tag_id) as unique_items_rented
    FROM id_transactions t
    JOIN id_item_master im ON t.tag_id = im.tag_id
    WHERE t.scan_type IN ('Rental', 'Delivery')
        AND t.scan_date >= DATE('now', '-3 months')
    GROUP BY im.rental_class_num, im.home_store
),
pos_equipment_revenue AS (
    SELECT 
        pe.rental_class,
        pt.store_code,
        SUM(pti.quantity * pti.unit_price) as equipment_revenue,
        COUNT(DISTINCT pt.contract_number) as pos_contracts,
        AVG(pti.unit_price) as avg_rental_rate
    FROM pos_transaction_items pti
    JOIN pos_transactions pt ON pti.transaction_id = pt.id
    JOIN pos_equipment pe ON pti.equipment_id = pe.id
    WHERE pt.transaction_date >= DATE('now', '-3 months')
    GROUP BY pe.rental_class, pt.store_code
)
SELECT 
    ei.rental_class_num,
    ei.home_store,
    -- Inventory Metrics
    ei.total_units,
    ei.available_units,
    ei.rented_units,
    ei.repair_units,
    (ei.rented_units * 100.0 / NULLIF(ei.total_units, 0)) as utilization_rate,
    -- Activity Metrics
    ra.rental_transactions,
    ra.active_days,
    ra.unique_items_rented,
    JULIANDAY('now') - JULIANDAY(ra.last_rental_date) as days_since_last_rental,
    -- Financial Metrics
    ei.avg_turnover_ytd,
    ei.avg_sell_price,
    ei.avg_retail_price,
    per.equipment_revenue,
    per.avg_rental_rate,
    -- Calculated KPIs
    CASE 
        WHEN ei.total_units > 0 AND ra.active_days > 0
        THEN (ra.rental_transactions * 1.0) / (ei.total_units * ra.active_days)
        ELSE 0
    END as daily_turnover_rate,
    CASE 
        WHEN ra.rental_transactions > 0
        THEN per.equipment_revenue / ra.rental_transactions
        ELSE 0
    END as revenue_per_rental,
    CASE 
        WHEN ei.avg_sell_price > 0
        THEN (per.equipment_revenue / NULLIF(ei.avg_sell_price * ei.total_units, 0)) * 100
        ELSE 0
    END as roi_percentage
FROM equipment_inventory ei
LEFT JOIN rental_activity ra 
    ON ei.rental_class_num = ra.rental_class_num 
    AND ei.home_store = ra.home_store
LEFT JOIN pos_equipment_revenue per 
    ON ei.rental_class_num = per.rental_class 
    AND ei.home_store = per.store_code
WHERE ei.total_units > 0
ORDER BY utilization_rate DESC, equipment_revenue DESC;

-- ================================================================
-- 3. CUSTOMER JOURNEY AND CONTRACT ANALYTICS
-- ================================================================

-- 3.1 Contract Lifecycle Analysis
CREATE VIEW IF NOT EXISTS v_contract_lifecycle_analysis AS
WITH contract_rfid_activity AS (
    SELECT 
        contract_number,
        MIN(scan_date) as contract_start,
        MAX(scan_date) as contract_end,
        COUNT(DISTINCT tag_id) as items_count,
        COUNT(DISTINCT scan_type) as interaction_types,
        SUM(CASE WHEN scan_type = 'Touch Scan' THEN 1 ELSE 0 END) as touch_scans,
        SUM(CASE WHEN scan_type = 'Rental' THEN 1 ELSE 0 END) as rentals,
        SUM(CASE WHEN scan_type = 'Return' THEN 1 ELSE 0 END) as returns,
        SUM(CASE WHEN scan_type = 'Delivery' THEN 1 ELSE 0 END) as deliveries,
        SUM(CASE WHEN scan_type = 'Pickup' THEN 1 ELSE 0 END) as pickups
    FROM id_transactions
    WHERE contract_number IS NOT NULL
    GROUP BY contract_number
),
contract_pos_data AS (
    SELECT 
        contract_number,
        store_code,
        MIN(transaction_date) as first_transaction,
        MAX(transaction_date) as last_transaction,
        COUNT(*) as transaction_count,
        SUM(amount) as total_revenue,
        AVG(amount) as avg_transaction_value,
        COUNT(DISTINCT customer_id) as customer_count
    FROM pos_transactions
    WHERE contract_number IS NOT NULL
    GROUP BY contract_number, store_code
),
contract_items AS (
    SELECT 
        t.contract_number,
        COUNT(DISTINCT im.rental_class_num) as equipment_classes,
        AVG(CAST(im.retail_price AS FLOAT)) as avg_item_value,
        STRING_AGG(DISTINCT im.common_name, ', ') as equipment_types
    FROM id_transactions t
    JOIN id_item_master im ON t.tag_id = im.tag_id
    WHERE t.contract_number IS NOT NULL
    GROUP BY t.contract_number
)
SELECT 
    COALESCE(cra.contract_number, cpd.contract_number) as contract_number,
    cpd.store_code,
    -- Timeline
    COALESCE(cra.contract_start, cpd.first_transaction) as contract_start_date,
    COALESCE(cra.contract_end, cpd.last_transaction) as contract_end_date,
    JULIANDAY(COALESCE(cra.contract_end, cpd.last_transaction)) - 
        JULIANDAY(COALESCE(cra.contract_start, cpd.first_transaction)) as contract_duration_days,
    -- RFID Activity
    cra.items_count as rfid_items_count,
    cra.interaction_types,
    cra.touch_scans,
    cra.rentals,
    cra.returns,
    cra.deliveries,
    cra.pickups,
    -- POS Data
    cpd.transaction_count as pos_transactions,
    cpd.total_revenue,
    cpd.avg_transaction_value,
    cpd.customer_count,
    -- Equipment Details
    ci.equipment_classes,
    ci.avg_item_value,
    ci.equipment_types,
    -- Calculated Metrics
    CASE 
        WHEN cra.rentals > 0 AND cra.returns > 0
        THEN 'Completed'
        WHEN cra.rentals > 0 AND cra.returns = 0
        THEN 'Active'
        ELSE 'Unknown'
    END as contract_status,
    CASE 
        WHEN cra.items_count > 0
        THEN cpd.total_revenue / cra.items_count
        ELSE NULL
    END as revenue_per_item,
    CASE 
        WHEN cra.deliveries > 0 OR cra.pickups > 0
        THEN 'Full Service'
        ELSE 'Self Service'
    END as service_type
FROM contract_rfid_activity cra
FULL OUTER JOIN contract_pos_data cpd 
    ON cra.contract_number = cpd.contract_number
LEFT JOIN contract_items ci 
    ON COALESCE(cra.contract_number, cpd.contract_number) = ci.contract_number
ORDER BY contract_start_date DESC;

-- ================================================================
-- 4. OPERATIONAL EFFICIENCY METRICS
-- ================================================================

-- 4.1 Cross-Store Equipment Movement Analysis
CREATE VIEW IF NOT EXISTS v_cross_store_movement AS
SELECT 
    tag_id,
    home_store,
    current_store,
    rental_class_num,
    common_name,
    date_last_scanned,
    CASE 
        WHEN home_store != current_store THEN 'Transferred'
        ELSE 'Home Location'
    END as movement_status,
    CASE 
        WHEN home_store = '3607' THEN 'TYLER'
        WHEN home_store = '6800' THEN 'ZACK'
        WHEN home_store = '728' THEN 'BRUCE'
        WHEN home_store = '8101' THEN 'TIM'
        ELSE home_store
    END as home_store_name,
    CASE 
        WHEN current_store = '3607' THEN 'TYLER'
        WHEN current_store = '6800' THEN 'ZACK'
        WHEN current_store = '728' THEN 'BRUCE'
        WHEN current_store = '8101' THEN 'TIM'
        ELSE current_store
    END as current_store_name
FROM id_item_master
WHERE home_store IS NOT NULL 
    AND current_store IS NOT NULL;

-- 4.2 Store Transfer Summary
CREATE VIEW IF NOT EXISTS v_store_transfer_summary AS
SELECT 
    home_store_name,
    current_store_name,
    COUNT(*) as items_transferred,
    COUNT(DISTINCT rental_class_num) as equipment_classes,
    STRING_AGG(DISTINCT common_name, ', ') as equipment_types
FROM v_cross_store_movement
WHERE movement_status = 'Transferred'
GROUP BY home_store_name, current_store_name
ORDER BY items_transferred DESC;

-- ================================================================
-- 5. FINANCIAL PERFORMANCE INDICATORS
-- ================================================================

-- 5.1 Store Financial Performance with Payroll Correlation
CREATE VIEW IF NOT EXISTS v_store_financial_performance AS
WITH weekly_revenue AS (
    SELECT 
        store_code,
        week_start,
        SUM(revenue) as weekly_revenue,
        SUM(gross_profit) as weekly_gross_profit,
        SUM(expenses) as weekly_expenses,
        (SUM(gross_profit) / NULLIF(SUM(revenue), 0)) * 100 as gross_margin_pct
    FROM pl_data
    WHERE week_start >= DATE('now', '-6 months')
    GROUP BY store_code, week_start
),
weekly_payroll AS (
    SELECT 
        store_id as store_code,
        week_end as week_start,
        regular_hours + overtime_hours as total_hours,
        regular_pay + overtime_pay as total_payroll,
        employee_count,
        (regular_pay + overtime_pay) / NULLIF(regular_hours + overtime_hours, 0) as avg_hourly_cost
    FROM payroll_trends
    WHERE week_end >= DATE('now', '-6 months')
),
operational_metrics AS (
    SELECT 
        im.home_store as store_code,
        DATE(t.scan_date, 'start of week') as week_start,
        COUNT(DISTINCT t.contract_number) as contracts_processed,
        COUNT(DISTINCT t.tag_id) as items_processed,
        COUNT(DISTINCT DATE(t.scan_date)) as operating_days
    FROM id_transactions t
    JOIN id_item_master im ON t.tag_id = im.tag_id
    WHERE t.scan_date >= DATE('now', '-6 months')
    GROUP BY im.home_store, DATE(t.scan_date, 'start of week')
)
SELECT 
    CASE 
        WHEN wr.store_code = '3607' THEN 'TYLER'
        WHEN wr.store_code = '6800' THEN 'ZACK'
        WHEN wr.store_code = '728' THEN 'BRUCE'
        WHEN wr.store_code = '8101' THEN 'TIM'
        ELSE wr.store_code
    END as store_name,
    wr.store_code,
    wr.week_start,
    -- Revenue Metrics
    wr.weekly_revenue,
    wr.weekly_gross_profit,
    wr.weekly_expenses,
    wr.gross_margin_pct,
    -- Payroll Metrics
    wp.total_hours,
    wp.total_payroll,
    wp.employee_count,
    wp.avg_hourly_cost,
    -- Operational Metrics
    om.contracts_processed,
    om.items_processed,
    om.operating_days,
    -- Efficiency KPIs
    CASE 
        WHEN wp.total_hours > 0
        THEN wr.weekly_revenue / wp.total_hours
        ELSE NULL
    END as revenue_per_labor_hour,
    CASE 
        WHEN wp.total_payroll > 0
        THEN (wp.total_payroll / wr.weekly_revenue) * 100
        ELSE NULL
    END as payroll_to_revenue_ratio,
    CASE 
        WHEN om.contracts_processed > 0
        THEN wr.weekly_revenue / om.contracts_processed
        ELSE NULL
    END as revenue_per_contract,
    CASE 
        WHEN wp.employee_count > 0 AND om.operating_days > 0
        THEN om.contracts_processed / (wp.employee_count * om.operating_days)
        ELSE NULL
    END as contracts_per_employee_day
FROM weekly_revenue wr
LEFT JOIN weekly_payroll wp 
    ON wr.store_code = wp.store_code 
    AND wr.week_start = wp.week_start
LEFT JOIN operational_metrics om 
    ON wr.store_code = om.store_code 
    AND wr.week_start = om.week_start
ORDER BY wr.week_start DESC, wr.store_code;

-- ================================================================
-- 6. PREDICTIVE ANALYTICS FEATURES
-- ================================================================

-- 6.1 Equipment Demand Forecasting Features
CREATE VIEW IF NOT EXISTS v_equipment_demand_features AS
WITH rental_history AS (
    SELECT 
        im.rental_class_num,
        im.home_store,
        DATE(t.scan_date, 'start of week') as week_start,
        COUNT(DISTINCT t.contract_number) as weekly_rentals,
        COUNT(DISTINCT t.tag_id) as unique_items_rented,
        AVG(JULIANDAY(t_return.scan_date) - JULIANDAY(t.scan_date)) as avg_rental_duration
    FROM id_transactions t
    JOIN id_item_master im ON t.tag_id = im.tag_id
    LEFT JOIN id_transactions t_return 
        ON t.tag_id = t_return.tag_id 
        AND t_return.scan_type = 'Return'
        AND t_return.scan_date > t.scan_date
    WHERE t.scan_type IN ('Rental', 'Delivery')
    GROUP BY im.rental_class_num, im.home_store, DATE(t.scan_date, 'start of week')
),
seasonal_patterns AS (
    SELECT 
        rental_class_num,
        home_store,
        CAST(strftime('%m', week_start) AS INTEGER) as month_num,
        AVG(weekly_rentals) as avg_monthly_rentals,
        STDEV(weekly_rentals) as rental_volatility,
        MAX(weekly_rentals) as peak_rentals,
        MIN(weekly_rentals) as min_rentals
    FROM rental_history
    GROUP BY rental_class_num, home_store, CAST(strftime('%m', week_start) AS INTEGER)
)
SELECT 
    rh.rental_class_num,
    rh.home_store,
    rh.week_start,
    -- Historical Features
    rh.weekly_rentals,
    rh.unique_items_rented,
    rh.avg_rental_duration,
    -- Lag Features
    LAG(rh.weekly_rentals, 1) OVER (PARTITION BY rh.rental_class_num, rh.home_store ORDER BY rh.week_start) as rentals_lag_1w,
    LAG(rh.weekly_rentals, 4) OVER (PARTITION BY rh.rental_class_num, rh.home_store ORDER BY rh.week_start) as rentals_lag_4w,
    -- Moving Averages
    AVG(rh.weekly_rentals) OVER (
        PARTITION BY rh.rental_class_num, rh.home_store 
        ORDER BY rh.week_start 
        ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
    ) as ma_4w,
    -- Seasonal Features
    sp.avg_monthly_rentals,
    sp.rental_volatility,
    sp.peak_rentals,
    -- Trend Features
    CASE 
        WHEN LAG(rh.weekly_rentals, 1) OVER (PARTITION BY rh.rental_class_num, rh.home_store ORDER BY rh.week_start) > 0
        THEN (rh.weekly_rentals - LAG(rh.weekly_rentals, 1) OVER (PARTITION BY rh.rental_class_num, rh.home_store ORDER BY rh.week_start)) 
             / LAG(rh.weekly_rentals, 1) OVER (PARTITION BY rh.rental_class_num, rh.home_store ORDER BY rh.week_start) * 100
        ELSE 0
    END as week_over_week_growth
FROM rental_history rh
LEFT JOIN seasonal_patterns sp 
    ON rh.rental_class_num = sp.rental_class_num 
    AND rh.home_store = sp.home_store
    AND CAST(strftime('%m', rh.week_start) AS INTEGER) = sp.month_num
ORDER BY rh.rental_class_num, rh.home_store, rh.week_start DESC;

-- ================================================================
-- 7. EXECUTIVE DASHBOARD SUMMARY VIEW
-- ================================================================

-- 7.1 Executive KPI Summary (Real-time calculation)
CREATE VIEW IF NOT EXISTS v_executive_kpi_summary AS
WITH current_period AS (
    SELECT 
        DATE('now', 'start of week', '-3 weeks') as period_start,
        DATE('now', 'start of week') as period_end
),
store_performance AS (
    SELECT 
        store_code,
        SUM(revenue) as total_revenue,
        SUM(gross_profit) as total_gross_profit,
        AVG((gross_profit / NULLIF(revenue, 0)) * 100) as avg_margin_pct,
        COUNT(DISTINCT week_start) as weeks_active
    FROM pl_data
    WHERE week_start >= (SELECT period_start FROM current_period)
        AND week_start <= (SELECT period_end FROM current_period)
    GROUP BY store_code
),
operational_metrics AS (
    SELECT 
        im.home_store as store_code,
        COUNT(DISTINCT t.contract_number) as total_contracts,
        COUNT(DISTINCT t.tag_id) as total_items,
        COUNT(DISTINCT DATE(t.scan_date)) as operating_days
    FROM id_transactions t
    JOIN id_item_master im ON t.tag_id = im.tag_id
    WHERE t.scan_date >= (SELECT period_start FROM current_period)
        AND t.scan_date <= (SELECT period_end FROM current_period)
    GROUP BY im.home_store
),
equipment_utilization AS (
    SELECT 
        home_store as store_code,
        AVG(CASE 
            WHEN status IN ('Rented', 'On Contract') AND total_units > 0
            THEN 100.0 
            ELSE 0 
        END) as avg_utilization_rate,
        COUNT(DISTINCT rental_class_num) as active_equipment_classes
    FROM (
        SELECT 
            home_store,
            rental_class_num,
            status,
            COUNT(*) as total_units
        FROM id_item_master
        GROUP BY home_store, rental_class_num, status
    )
    GROUP BY home_store
)
SELECT 
    CASE 
        WHEN sp.store_code = '3607' THEN 'TYLER'
        WHEN sp.store_code = '6800' THEN 'ZACK'
        WHEN sp.store_code = '728' THEN 'BRUCE'
        WHEN sp.store_code = '8101' THEN 'TIM'
        ELSE sp.store_code
    END as store_name,
    sp.store_code,
    -- Financial KPIs
    sp.total_revenue,
    sp.total_gross_profit,
    sp.avg_margin_pct,
    sp.total_revenue / NULLIF(sp.weeks_active, 0) as avg_weekly_revenue,
    -- Operational KPIs
    om.total_contracts,
    om.total_items,
    sp.total_revenue / NULLIF(om.total_contracts, 0) as revenue_per_contract,
    om.total_contracts / NULLIF(om.operating_days, 0) as contracts_per_day,
    -- Equipment KPIs
    eu.avg_utilization_rate,
    eu.active_equipment_classes,
    -- Performance Score (composite metric)
    (
        (sp.avg_margin_pct / 100 * 0.3) +  -- Margin weight: 30%
        (CASE 
            WHEN eu.avg_utilization_rate > 0 
            THEN eu.avg_utilization_rate / 100 * 0.3 
            ELSE 0 
        END) +  -- Utilization weight: 30%
        (CASE 
            WHEN om.total_contracts > 0 
            THEN MIN(1.0, om.total_contracts / 100.0) * 0.4 
            ELSE 0 
        END)  -- Volume weight: 40%
    ) * 100 as performance_score
FROM store_performance sp
LEFT JOIN operational_metrics om ON sp.store_code = om.store_code
LEFT JOIN equipment_utilization eu ON sp.store_code = eu.store_code
ORDER BY performance_score DESC;

-- ================================================================
-- INDEXES FOR QUERY OPTIMIZATION
-- ================================================================

-- Create indexes for correlation queries
CREATE INDEX IF NOT EXISTS idx_trans_contract_store 
    ON id_transactions(contract_number, scan_date);

CREATE INDEX IF NOT EXISTS idx_item_rental_store 
    ON id_item_master(rental_class_num, home_store, current_store);

CREATE INDEX IF NOT EXISTS idx_pos_trans_contract 
    ON pos_transactions(contract_number, store_code, transaction_date);

CREATE INDEX IF NOT EXISTS idx_pl_store_week 
    ON pl_data(store_code, week_start);

CREATE INDEX IF NOT EXISTS idx_payroll_store_week 
    ON payroll_trends(store_id, week_end);

-- ================================================================
-- MATERIALIZED VIEW REFRESH PROCEDURES (SQLite doesn't support, 
-- but these would be scheduled jobs in production)
-- ================================================================

-- Note: In production, these views should be refreshed on a schedule:
-- - v_executive_kpi_summary: Every 15 minutes
-- - v_store_revenue_correlation: Every hour
-- - v_equipment_class_performance: Every 4 hours
-- - v_contract_lifecycle_analysis: Daily
-- - v_equipment_demand_features: Daily