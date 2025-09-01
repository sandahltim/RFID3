#!/usr/bin/env python3

from app import create_app, db
from sqlalchemy import text
from datetime import datetime, timedelta
from app.models.db_models import PayrollTrends

# Create app and connect to DB within app context
app = create_app()
with app.app_context():
    with db.engine.connect() as conn:
        # Check what tables exist first
        print('=== AVAILABLE TABLES ===')
        result = conn.execute(text('SHOW TABLES'))
        tables = [row[0] for row in result]
        print('Available tables:', tables)
        
        # Check recent payroll trends data for YoY calculation
        print('\n=== RECENT PAYROLL TRENDS DATA ===')
        if 'executive_payroll_trends' in tables:
            result = conn.execute(text('SELECT week_ending, total_revenue, store_id FROM executive_payroll_trends ORDER BY week_ending DESC LIMIT 10'))
            for row in result:
                print(f'{row.week_ending}: ${row.total_revenue} (Store: {row.store_id})')
        elif 'pos_payroll_trends' in tables:
            result = conn.execute(text('SELECT week_ending, total_revenue FROM pos_payroll_trends ORDER BY week_ending DESC LIMIT 10'))
            for row in result:
                print(f'{row.week_ending}: ${row.total_revenue}')
        else:
            print('No payroll trends table found')
        
        print()
        print('=== YEAR OVER YEAR COMPARISON SAMPLE ===')
        # Get current week
        current_date = datetime.now().date()
        current_week_start = current_date - timedelta(days=current_date.weekday())
        
        # Get last year same week
        prev_year_start = current_week_start.replace(year=current_week_start.year - 1)
        
        print(f'Current week start: {current_week_start}')
        print(f'Previous year week start: {prev_year_start}')
        
        # Use the correct table for YoY calculation
        payroll_table = 'executive_payroll_trends' if 'executive_payroll_trends' in tables else 'pos_payroll_trends'
        
        # Check current year data
        current_result = conn.execute(text(f'SELECT SUM(total_revenue) as revenue FROM {payroll_table} WHERE week_ending >= :start_date'), 
                                     {'start_date': current_week_start})
        current_revenue = current_result.fetchone().revenue or 0
        
        # Check previous year data  
        prev_result = conn.execute(text(f'SELECT SUM(total_revenue) as revenue FROM {payroll_table} WHERE week_ending >= :start_date AND week_ending < :end_date'), 
                                  {'start_date': prev_year_start, 'end_date': current_week_start.replace(year=current_week_start.year - 1, month=12, day=31)})
        prev_revenue = prev_result.fetchone().revenue or 0
        
        print(f'Current year revenue: ${current_revenue}')
        print(f'Previous year revenue: ${prev_revenue}')
        
        if prev_revenue > 0:
            growth = ((current_revenue - prev_revenue) / prev_revenue) * 100
            print(f'YoY Growth: {growth:.2f}%')
            print(f'Direction: {"UP" if growth > 0 else "DOWN"}')
        else:
            print('Cannot calculate YoY - no previous year data')

        print('\n=== CONTRACT DATA CHECK ===')
        # Check pos_scorecard_trends contracts data
        try:
            result = conn.execute(text('SELECT week_ending_sunday, new_open_contracts_3607, new_open_contracts_6800, new_open_contracts_8101 FROM pos_scorecard_trends ORDER BY week_ending_sunday DESC LIMIT 5'))
            print('Recent contract data:')
            for row in result:
                contracts_total = (row.new_open_contracts_3607 or 0) + (row.new_open_contracts_6800 or 0) + (row.new_open_contracts_8101 or 0)
                print(f'{row.week_ending_sunday}: Total contracts: {contracts_total} (3607: {row.new_open_contracts_3607}, 6800: {row.new_open_contracts_6800}, 8101: {row.new_open_contracts_8101})')
        except Exception as e:
            print(f'Error checking contract data: {e}')

        print('\n=== SCORECARD TRENDS MODEL MAPPING CHECK ===')
        # Check if executive_scorecard_trends has contract data
        try:
            result = conn.execute(text('SELECT week_ending, new_contracts_count FROM executive_scorecard_trends ORDER BY week_ending DESC LIMIT 5'))
            print('Executive scorecard contracts:')
            for row in result:
                print(f'{row.week_ending}: {row.new_contracts_count}')
        except Exception as e:
            print(f'Error checking executive scorecard: {e}')