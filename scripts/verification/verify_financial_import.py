#!/usr/bin/env python3
"""
Verify Financial Data Import
Quick script to check what financial data has been imported
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from sqlalchemy import text

def verify_imports():
    app = create_app()
    
    with app.app_context():
        from app import db
        
        print("\n" + "=" * 70)
        print("    FINANCIAL DATA IMPORT VERIFICATION")
        print("=" * 70)
        
        tables_to_check = [
            ('pos_customers', 'Customer Data'),
            ('pos_scorecard_trends', 'Scorecard Business Metrics'),
            ('pos_payroll_trends', 'Payroll Analytics'),
            ('pos_profit_loss', 'Profit & Loss Data'),
            ('pos_equipment', 'Equipment Inventory')
        ]
        
        total_records = 0
        
        for table_name, description in tables_to_check:
            try:
                # Get record count
                result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                total_records += count
                
                # Get sample data
                sample_result = db.session.execute(text(f"SELECT * FROM {table_name} LIMIT 1"))
                has_data = sample_result.fetchone() is not None
                
                # Get column count
                col_result = db.session.execute(text(f"SHOW COLUMNS FROM {table_name}"))
                col_count = len(col_result.fetchall())
                
                status = "✅" if count > 0 else "⚠️"
                print(f"\n{status} {description} ({table_name}):")
                print(f"   Records: {count:,}")
                print(f"   Columns: {col_count}")
                
                if table_name == 'pos_scorecard_trends' and count > 0:
                    # Get date range
                    date_result = db.session.execute(text("""
                        SELECT MIN(week_ending_sunday), MAX(week_ending_sunday)
                        FROM pos_scorecard_trends
                        WHERE week_ending_sunday IS NOT NULL
                    """))
                    dates = date_result.fetchone()
                    if dates and dates[0]:
                        print(f"   Date Range: {dates[0]} to {dates[1]}")
                
                if table_name == 'pos_profit_loss' and count > 0:
                    # Get unique periods
                    period_result = db.session.execute(text("""
                        SELECT COUNT(DISTINCT period), COUNT(DISTINCT account_line)
                        FROM pos_profit_loss
                    """))
                    periods = period_result.fetchone()
                    print(f"   Periods: {periods[0]}, Accounts: {periods[1]}")
                
            except Exception as e:
                print(f"\n❌ {description} ({table_name}):")
                print(f"   Error: {str(e)[:100]}")
        
        print("\n" + "-" * 70)
        print(f"📊 Total Records Across All Tables: {total_records:,}")
        
        # Check import batches
        try:
            batch_result = db.session.execute(text("""
                SELECT id, import_type, started_at, status, 
                       records_processed, records_imported
                FROM import_batches
                WHERE import_type = 'financial_csv'
                ORDER BY id DESC
                LIMIT 5
            """))
            batches = batch_result.fetchall()
            
            if batches:
                print("\n📋 Recent Import Batches:")
                for batch in batches:
                    print(f"   Batch {batch[0]}: {batch[3]} - {batch[5]}/{batch[4]} records")
        except:
            pass
        
        print("\n" + "=" * 70)
        
        # Provide analysis summary
        if total_records > 0:
            print("\n✅ Financial data is available for analysis!")
            print("   You can now use the executive dashboard and analytics features.")
        else:
            print("\n⚠️ No financial data found. Please run the import script.")

if __name__ == "__main__":
    verify_imports()