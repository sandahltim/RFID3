#!/usr/bin/env python3
"""
Fix Financial Data Correlation Issues
Implements critical fixes for data correlation problems
"""

import os
import sys
sys.path.insert(0, '/home/tim/RFID3')

from app import create_app, db
from sqlalchemy import text
from datetime import datetime

app = create_app()

def fix_data_correlations():
    """Apply critical fixes to resolve data correlation issues"""
    
    with app.app_context():
        print("\n" + "="*80)
        print(" APPLYING FINANCIAL DATA CORRELATION FIXES")
        print(" Started:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("="*80)
        
        fixes_applied = []
        fixes_failed = []
        
        # FIX 1: Remove future dates from scorecard data
        print("\n1. Fixing future dates in scorecard data...")
        try:
            # First check how many records need fixing
            future_count = db.session.execute(text("""
                SELECT COUNT(*) FROM pos_scorecard_trends 
                WHERE week_ending_sunday > CURRENT_DATE
            """)).scalar()
            
            if future_count > 0:
                print(f"   Found {future_count} records with future dates")
                
                # Update future dates to current date
                db.session.execute(text("""
                    UPDATE pos_scorecard_trends 
                    SET week_ending_sunday = CURRENT_DATE
                    WHERE week_ending_sunday > CURRENT_DATE
                """))
                db.session.commit()
                
                fixes_applied.append(f"Fixed {future_count} future-dated records")
                print(f"   ✅ Fixed {future_count} records")
            else:
                print("   ✅ No future dates found - data is clean")
                fixes_applied.append("No future dates to fix")
                
        except Exception as e:
            fixes_failed.append(f"Future dates fix failed: {str(e)}")
            print(f"   ❌ Error: {str(e)}")
            db.session.rollback()
        
        # FIX 2: Create unified store mapping table
        print("\n2. Creating unified store mapping table...")
        try:
            # Check if table exists
            table_exists = db.session.execute(text("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = 'unified_store_mapping'
            """)).scalar()
            
            if table_exists == 0:
                # Create the table
                db.session.execute(text("""
                    CREATE TABLE unified_store_mapping (
                        store_code VARCHAR(10) PRIMARY KEY,
                        store_name VARCHAR(100),
                        gl_account_code VARCHAR(20),
                        pos_location_code VARCHAR(20),
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                """))
                
                # Insert store mappings
                db.session.execute(text("""
                    INSERT INTO unified_store_mapping 
                    (store_code, store_name, gl_account_code, pos_location_code) 
                    VALUES
                        ('3607', 'Store 3607', '3607', '3607'),
                        ('6800', 'Store 6800', '6800', '6800'),
                        ('728', 'Store 728', '728', '728'),
                        ('8101', 'Store 8101', '8101', '8101')
                """))
                
                db.session.commit()
                fixes_applied.append("Created unified_store_mapping table with 4 stores")
                print("   ✅ Table created and populated with 4 stores")
            else:
                print("   ✅ Table already exists")
                fixes_applied.append("unified_store_mapping table already exists")
                
        except Exception as e:
            fixes_failed.append(f"Store mapping table creation failed: {str(e)}")
            print(f"   ❌ Error: {str(e)}")
            db.session.rollback()
        
        # FIX 3: Create standardized revenue view
        print("\n3. Creating standardized revenue view...")
        try:
            # Drop view if exists (MySQL doesn't support CREATE OR REPLACE VIEW)
            db.session.execute(text("DROP VIEW IF EXISTS v_unified_weekly_revenue"))
            
            # Create the view
            db.session.execute(text("""
                CREATE VIEW v_unified_weekly_revenue AS
                SELECT 
                    week_ending_sunday as week_ending,
                    total_weekly_revenue,
                    col_3607_revenue as revenue_3607,
                    col_6800_revenue as revenue_6800,
                    col_728_revenue as revenue_728,
                    col_8101_revenue as revenue_8101,
                    new_open_contracts_3607 as contracts_3607,
                    new_open_contracts_6800 as contracts_6800,
                    new_open_contracts_728 as contracts_728,
                    new_open_contracts_8101 as contracts_8101
                FROM pos_scorecard_trends
                WHERE week_ending_sunday <= CURRENT_DATE
            """))
            
            db.session.commit()
            fixes_applied.append("Created v_unified_weekly_revenue view")
            print("   ✅ View created successfully")
            
        except Exception as e:
            fixes_failed.append(f"Revenue view creation failed: {str(e)}")
            print(f"   ❌ Error: {str(e)}")
            db.session.rollback()
        
        # FIX 4: Create payroll data consolidation view
        print("\n4. Creating consolidated payroll view...")
        try:
            # Drop view if exists
            db.session.execute(text("DROP VIEW IF EXISTS v_unified_payroll"))
            
            # Create consolidated payroll view
            db.session.execute(text("""
                CREATE VIEW v_unified_payroll AS
                SELECT 
                    p.week_ending,
                    p.location_code as store_code,
                    p.rental_revenue,
                    p.all_revenue,
                    p.payroll_amount,
                    p.wage_hours,
                    CASE 
                        WHEN p.payroll_amount > 0 THEN p.rental_revenue / p.payroll_amount 
                        ELSE 0 
                    END as revenue_per_payroll_dollar,
                    CASE 
                        WHEN p.wage_hours > 0 THEN p.rental_revenue / p.wage_hours 
                        ELSE 0 
                    END as revenue_per_hour
                FROM payroll_trends_data p
                WHERE p.week_ending <= CURRENT_DATE
            """))
            
            db.session.commit()
            fixes_applied.append("Created v_unified_payroll view")
            print("   ✅ Payroll view created successfully")
            
        except Exception as e:
            fixes_failed.append(f"Payroll view creation failed: {str(e)}")
            print(f"   ❌ Error: {str(e)}")
            db.session.rollback()
        
        # FIX 5: Add data quality constraints
        print("\n5. Adding data quality constraints...")
        try:
            # Add constraint to prevent future dates
            constraint_count = 0
            
            # Check if we can add check constraints (MySQL 8.0.16+)
            try:
                db.session.execute(text("""
                    ALTER TABLE pos_scorecard_trends 
                    ADD CONSTRAINT chk_no_future_dates 
                    CHECK (week_ending_sunday <= CURRENT_DATE)
                """))
                db.session.commit()
                constraint_count += 1
                print("   ✅ Added future date prevention constraint")
            except:
                print("   ⚠️  Check constraints not supported in this MySQL version")
            
            # Add indexes for better performance
            try:
                db.session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_scorecard_week_ending 
                    ON pos_scorecard_trends(week_ending_sunday)
                """))
                
                db.session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_payroll_week_ending 
                    ON payroll_trends_data(week_ending)
                """))
                
                db.session.commit()
                constraint_count += 2
                print("   ✅ Added performance indexes")
            except:
                pass
            
            if constraint_count > 0:
                fixes_applied.append(f"Added {constraint_count} data quality improvements")
            
        except Exception as e:
            fixes_failed.append(f"Constraint addition failed: {str(e)}")
            print(f"   ❌ Error: {str(e)}")
            db.session.rollback()
        
        # Run validation query
        print("\n6. Running data validation checks...")
        try:
            validation_results = db.session.execute(text("""
                SELECT 
                    'Revenue Mismatch' as issue_type,
                    COUNT(*) as issue_count
                FROM pos_scorecard_trends
                WHERE ABS(total_weekly_revenue - 
                    (col_3607_revenue + col_6800_revenue + col_728_revenue + col_8101_revenue)) > 1
                
                UNION ALL
                
                SELECT 
                    'Future Dates',
                    COUNT(*)
                FROM pos_scorecard_trends
                WHERE week_ending_sunday > CURRENT_DATE
                
                UNION ALL
                
                SELECT 
                    'Null Revenue Values',
                    COUNT(*)
                FROM pos_scorecard_trends
                WHERE total_weekly_revenue IS NULL
            """)).fetchall()
            
            print("\n   Current Data Quality Status:")
            print("   " + "-"*40)
            for issue, count in validation_results:
                status = "✅" if count == 0 else "⚠️"
                print(f"   {status} {issue}: {count} issues")
            
        except Exception as e:
            print(f"   ❌ Validation check failed: {str(e)}")
        
        # Summary
        print("\n" + "="*80)
        print(" SUMMARY")
        print("="*80)
        
        print(f"\n✅ Successful Fixes ({len(fixes_applied)}):")
        for fix in fixes_applied:
            print(f"   • {fix}")
        
        if fixes_failed:
            print(f"\n❌ Failed Fixes ({len(fixes_failed)}):")
            for fail in fixes_failed:
                print(f"   • {fail}")
        
        print("\n" + "="*80)
        print(" NEXT STEPS")
        print("="*80)
        print("""
1. Update all queries to use the new standardized views:
   • v_unified_weekly_revenue (for revenue data)
   • v_unified_payroll (for payroll data)
   • unified_store_mapping (for store lookups)

2. Archive or drop duplicate tables:
   • pos_payroll_trends (empty - can be dropped)
   • executive_scorecard_trends (empty - can be dropped)
   
3. Update application code to use consistent column names

4. Schedule regular data quality checks using the validation query

5. Document the new data structure for all team members
        """)
        
        print("\n" + "="*80)
        print(" FIXES COMPLETED:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("="*80)

if __name__ == "__main__":
    fix_data_correlations()