#!/usr/bin/env python3
"""
Create Missing POS Database Tables
Phase 2.5: Database preparation for comprehensive CSV import
"""

import pymysql
import sys
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'rfid_user',
    'password': 'rfid_user_password',
    'database': 'rfid_inventory',
    'charset': 'utf8mb4',
}

def create_pos_scorecard_trends():
    """Create pos_scorecard_trends table with properly named columns"""
    return """
CREATE TABLE IF NOT EXISTS pos_scorecard_trends (
    id INT AUTO_INCREMENT PRIMARY KEY,
    week_ending DATE NOT NULL UNIQUE,
    total_weekly_revenue DECIMAL(15,2),
    
    -- Store-specific metrics
    new_open_contracts_3607 INT,
    new_open_contracts_6800 INT,
    new_open_contracts_8101 INT,
    
    -- Reservations by store
    total_on_reservation_3607 DECIMAL(15,2),
    total_on_reservation_6800 DECIMAL(15,2),
    total_on_reservation_8101 DECIMAL(15,2),
    
    -- Deliveries and quotes
    deliveries_scheduled_next_7_days INT,
    open_quotes_8101 INT,
    
    -- AR metrics
    total_ar_45_days DECIMAL(15,2),
    
    -- Performance indicators
    week_number INT,
    revenue_growth_pct DECIMAL(10,2),
    contract_growth_pct DECIMAL(10,2),
    
    -- Store comparisons
    store_3607_revenue DECIMAL(15,2),
    store_6800_revenue DECIMAL(15,2),
    store_8101_revenue DECIMAL(15,2),
    
    -- Utilization metrics
    equipment_utilization_pct DECIMAL(10,2),
    rental_yield DECIMAL(15,2),
    
    -- Customer metrics
    new_customers INT,
    repeat_customers INT,
    customer_retention_pct DECIMAL(10,2),
    
    -- Operational metrics
    average_contract_value DECIMAL(15,2),
    average_rental_duration DECIMAL(10,2),
    damage_waiver_revenue DECIMAL(15,2),
    
    -- Inventory metrics
    total_equipment_count INT,
    equipment_on_rent INT,
    equipment_available INT,
    equipment_in_maintenance INT,
    
    -- Import metadata
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    import_batch VARCHAR(50),
    file_source VARCHAR(100),
    data_quality_score DECIMAL(5,2),
    
    -- Indexes for performance
    INDEX idx_week_ending (week_ending),
    INDEX idx_week_number (week_number),
    INDEX idx_import_date (import_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Weekly scorecard trends and KPIs by store';
"""

def create_pos_payroll_trends():
    """Create pos_payroll_trends table with proper column names"""
    return """
CREATE TABLE IF NOT EXISTS pos_payroll_trends (
    id INT AUTO_INCREMENT PRIMARY KEY,
    week_ending DATE NOT NULL UNIQUE,
    
    -- Store 6800 metrics
    rental_revenue_6800 DECIMAL(15,2),
    all_revenue_6800 DECIMAL(15,2),
    payroll_6800 DECIMAL(15,2),
    wage_hours_6800 DECIMAL(10,2),
    payroll_pct_6800 DECIMAL(10,2),
    
    -- Store 3607 metrics
    rental_revenue_3607 DECIMAL(15,2),
    all_revenue_3607 DECIMAL(15,2),
    payroll_3607 DECIMAL(15,2),
    wage_hours_3607 DECIMAL(10,2),
    payroll_pct_3607 DECIMAL(10,2),
    
    -- Store 8101 metrics
    rental_revenue_8101 DECIMAL(15,2),
    all_revenue_8101 DECIMAL(15,2),
    payroll_8101 DECIMAL(15,2),
    wage_hours_8101 DECIMAL(10,2),
    payroll_pct_8101 DECIMAL(10,2),
    
    -- Store 728 metrics (if applicable)
    rental_revenue_728 DECIMAL(15,2),
    all_revenue_728 DECIMAL(15,2),
    payroll_728 DECIMAL(15,2),
    wage_hours_728 DECIMAL(10,2),
    payroll_pct_728 DECIMAL(10,2),
    
    -- Aggregate metrics
    total_rental_revenue DECIMAL(15,2),
    total_all_revenue DECIMAL(15,2),
    total_payroll DECIMAL(15,2),
    total_wage_hours DECIMAL(10,2),
    overall_payroll_pct DECIMAL(10,2),
    
    -- Efficiency metrics
    revenue_per_hour DECIMAL(15,2),
    payroll_efficiency_ratio DECIMAL(10,2),
    
    -- Import metadata
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    import_batch VARCHAR(50),
    file_source VARCHAR(100),
    
    -- Indexes for performance
    INDEX idx_week_ending (week_ending),
    INDEX idx_import_date (import_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Bi-weekly payroll and revenue trends by store';
"""

def create_pos_profit_loss():
    """Create pos_profit_loss table with structured P&L columns"""
    return """
CREATE TABLE IF NOT EXISTS pos_profit_loss (
    id INT AUTO_INCREMENT PRIMARY KEY,
    period_ending DATE NOT NULL,
    store_code VARCHAR(20),
    
    -- Revenue section
    rental_revenue DECIMAL(15,2),
    sales_revenue DECIMAL(15,2),
    service_revenue DECIMAL(15,2),
    damage_waiver_revenue DECIMAL(15,2),
    other_revenue DECIMAL(15,2),
    total_revenue DECIMAL(15,2),
    
    -- Cost of Goods Sold
    rental_cogs DECIMAL(15,2),
    sales_cogs DECIMAL(15,2),
    service_cogs DECIMAL(15,2),
    total_cogs DECIMAL(15,2),
    gross_profit DECIMAL(15,2),
    gross_margin_pct DECIMAL(10,2),
    
    -- Operating Expenses - Personnel
    salaries_wages DECIMAL(15,2),
    payroll_taxes DECIMAL(15,2),
    employee_benefits DECIMAL(15,2),
    workers_comp DECIMAL(15,2),
    total_personnel_expense DECIMAL(15,2),
    
    -- Operating Expenses - Facilities
    rent_expense DECIMAL(15,2),
    utilities DECIMAL(15,2),
    property_tax DECIMAL(15,2),
    insurance DECIMAL(15,2),
    maintenance_repairs DECIMAL(15,2),
    total_facilities_expense DECIMAL(15,2),
    
    -- Operating Expenses - Equipment
    equipment_rental DECIMAL(15,2),
    equipment_maintenance DECIMAL(15,2),
    depreciation DECIMAL(15,2),
    total_equipment_expense DECIMAL(15,2),
    
    -- Operating Expenses - Vehicle
    vehicle_fuel DECIMAL(15,2),
    vehicle_maintenance DECIMAL(15,2),
    vehicle_insurance DECIMAL(15,2),
    vehicle_lease DECIMAL(15,2),
    total_vehicle_expense DECIMAL(15,2),
    
    -- Operating Expenses - Administrative
    office_supplies DECIMAL(15,2),
    telephone_internet DECIMAL(15,2),
    professional_fees DECIMAL(15,2),
    advertising_marketing DECIMAL(15,2),
    bank_fees DECIMAL(15,2),
    credit_card_fees DECIMAL(15,2),
    bad_debt_expense DECIMAL(15,2),
    miscellaneous_expense DECIMAL(15,2),
    total_admin_expense DECIMAL(15,2),
    
    -- Summary metrics
    total_operating_expenses DECIMAL(15,2),
    operating_income DECIMAL(15,2),
    operating_margin_pct DECIMAL(10,2),
    
    -- Other Income/Expense
    interest_income DECIMAL(15,2),
    interest_expense DECIMAL(15,2),
    other_income DECIMAL(15,2),
    other_expense DECIMAL(15,2),
    
    -- Net Income
    income_before_tax DECIMAL(15,2),
    income_tax DECIMAL(15,2),
    net_income DECIMAL(15,2),
    net_margin_pct DECIMAL(10,2),
    
    -- EBITDA calculation fields
    ebitda DECIMAL(15,2),
    ebitda_margin_pct DECIMAL(10,2),
    
    -- Year-over-year comparisons
    revenue_yoy_pct DECIMAL(10,2),
    expense_yoy_pct DECIMAL(10,2),
    net_income_yoy_pct DECIMAL(10,2),
    
    -- Budget variance
    revenue_budget_variance DECIMAL(15,2),
    expense_budget_variance DECIMAL(15,2),
    net_income_budget_variance DECIMAL(15,2),
    
    -- Import metadata
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    import_batch VARCHAR(50),
    file_source VARCHAR(100),
    fiscal_year INT,
    fiscal_period INT,
    
    -- Indexes for performance
    INDEX idx_period_ending (period_ending),
    INDEX idx_store_code (store_code),
    INDEX idx_fiscal_year_period (fiscal_year, fiscal_period),
    INDEX idx_import_date (import_date),
    UNIQUE KEY uk_period_store (period_ending, store_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Profit and Loss statements by store and period';
"""

def verify_existing_tables():
    """Verify structure of existing POS tables"""
    queries = {
        'pos_customers': "DESCRIBE pos_customers",
        'pos_transactions': "DESCRIBE pos_transactions", 
        'pos_transaction_items': "DESCRIBE pos_transaction_items"
    }
    
    results = {}
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        for table_name, query in queries.items():
            cursor.execute(query)
            columns = cursor.fetchall()
            results[table_name] = len(columns)
            print(f"\n✅ Table {table_name} exists with {len(columns)} columns")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        
    return results

def create_tables():
    """Create the missing POS tables"""
    
    tables_to_create = [
        ('pos_scorecard_trends', create_pos_scorecard_trends()),
        ('pos_payroll_trends', create_pos_payroll_trends()),
        ('pos_profit_loss', create_pos_profit_loss())
    ]
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\n" + "="*60)
        print("CREATING MISSING POS TABLES")
        print("="*60)
        
        for table_name, create_sql in tables_to_create:
            try:
                # Check if table exists
                cursor.execute(f"""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = '{DB_CONFIG['database']}' 
                    AND table_name = '{table_name}'
                """)
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    print(f"\n⚠️  Table {table_name} already exists - skipping")
                else:
                    print(f"\n🔨 Creating table: {table_name}")
                    cursor.execute(create_sql)
                    conn.commit()
                    
                    # Verify creation
                    cursor.execute(f"DESCRIBE {table_name}")
                    columns = cursor.fetchall()
                    print(f"   ✅ Created with {len(columns)} columns")
                    
            except Exception as e:
                print(f"   ❌ Error creating {table_name}: {e}")
                conn.rollback()
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("TABLE CREATION COMPLETE")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Database connection error: {e}")
        sys.exit(1)

def verify_all_tables():
    """Final verification of all 6 required tables"""
    required_tables = [
        'pos_customers',
        'pos_transactions', 
        'pos_transaction_items',
        'pos_scorecard_trends',
        'pos_payroll_trends',
        'pos_profit_loss'
    ]
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("\n" + "="*60)
        print("FINAL TABLE VERIFICATION")
        print("="*60)
        
        all_present = True
        for table_name in required_tables:
            cursor.execute(f"""
                SELECT COUNT(*) as col_count
                FROM information_schema.columns 
                WHERE table_schema = '{DB_CONFIG['database']}' 
                AND table_name = '{table_name}'
            """)
            result = cursor.fetchone()
            
            if result and result[0] > 0:
                print(f"✅ {table_name:<25} - {result[0]} columns")
            else:
                print(f"❌ {table_name:<25} - MISSING")
                all_present = False
        
        cursor.close()
        conn.close()
        
        if all_present:
            print("\n✅ All required POS tables are present and ready for import!")
        else:
            print("\n⚠️  Some tables are missing. Please review and fix.")
            
        return all_present
        
    except Exception as e:
        print(f"\n❌ Error during verification: {e}")
        return False

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("POS DATABASE TABLE CREATION - PHASE 2.5")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Step 1: Verify existing tables
    print("\n📋 Step 1: Verifying existing tables...")
    verify_existing_tables()
    
    # Step 2: Create missing tables
    print("\n📋 Step 2: Creating missing tables...")
    create_tables()
    
    # Step 3: Final verification
    print("\n📋 Step 3: Final verification...")
    success = verify_all_tables()
    
    if success:
        print("\n" + "="*60)
        print("SUCCESS: Database ready for comprehensive CSV import!")
        print("="*60)
        print("\nNext steps:")
        print("1. Review table structures with database viewer")
        print("2. Test CSV import with sample data")
        print("3. Schedule automated Tuesday imports")
        print("4. Implement data quality monitoring")
    else:
        print("\n⚠️  Please address any issues before proceeding with CSV import.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())