#!/usr/bin/env python3

from app import create_app, db
from sqlalchemy import text
from datetime import datetime, timedelta

# Create app and connect to DB within app context
app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        print("=== YoY DATE RANGE DEBUGGING ===")
        
        # Simulate the logic from tab7.py
        latest_data_date = datetime.now().date()
        end_date = latest_data_date
        current_year_start = end_date.replace(month=1, day=1)
        
        # Previous year
        prev_year_start = current_year_start.replace(year=current_year_start.year - 1)
        prev_year_end = end_date.replace(year=end_date.year - 1)
        
        print(f"Latest data date: {latest_data_date}")
        print(f"Current year range: {current_year_start} to {end_date}")
        print(f"Previous year range: {prev_year_start} to {prev_year_end}")
        
        print("\n=== CURRENT YEAR DATA CHECK ===")
        current_result = conn.execute(text("""
            SELECT COUNT(*) as count, SUM(total_revenue) as total, MIN(week_ending) as min_date, MAX(week_ending) as max_date
            FROM executive_payroll_trends 
            WHERE week_ending >= :start_date AND week_ending <= :end_date
        """), {'start_date': current_year_start, 'end_date': end_date})
        
        current_data = current_result.fetchone()
        print(f"Records: {current_data.count}")
        print(f"Total Revenue: ${current_data.total}")
        print(f"Date Range: {current_data.min_date} to {current_data.max_date}")
        
        print("\n=== PREVIOUS YEAR DATA CHECK ===")
        prev_result = conn.execute(text("""
            SELECT COUNT(*) as count, SUM(total_revenue) as total, MIN(week_ending) as min_date, MAX(week_ending) as max_date
            FROM executive_payroll_trends 
            WHERE week_ending >= :start_date AND week_ending <= :end_date
        """), {'start_date': prev_year_start, 'end_date': prev_year_end})
        
        prev_data = prev_result.fetchone()
        print(f"Records: {prev_data.count}")
        print(f"Total Revenue: ${prev_data.total}")
        print(f"Date Range: {prev_data.min_date} to {prev_data.max_date}")
        
        print("\n=== ALL AVAILABLE DATA IN EXECUTIVE_PAYROLL_TRENDS ===")
        all_result = conn.execute(text("""
            SELECT MIN(week_ending) as min_date, MAX(week_ending) as max_date, COUNT(*) as total_records
            FROM executive_payroll_trends
        """))
        
        all_data = all_result.fetchone()
        print(f"Total records: {all_data.total_records}")
        print(f"Date range available: {all_data.min_date} to {all_data.max_date}")
        
        print("\n=== 2025 DATA AVAILABILITY ===")
        current_year_result = conn.execute(text("""
            SELECT week_ending, total_revenue, store_id
            FROM executive_payroll_trends
            WHERE YEAR(week_ending) = 2025
            ORDER BY week_ending DESC
            LIMIT 10
        """))
        
        print("Recent 2025 data:")
        for row in current_year_result:
            print(f"{row.week_ending}: ${row.total_revenue} (Store: {row.store_id})")