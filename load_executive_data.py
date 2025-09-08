#!/usr/bin/env python3
"""
Load historical payroll and scorecard data into executive dashboard tables.
Usage: python load_executive_data.py
"""

import pandas as pd
import mysql.connector
from datetime import datetime, date
import re
from decimal import Decimal
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import DB_CONFIG

def clean_currency_value(value):
    """Clean currency values by removing $ and , characters."""
    if pd.isna(value) or value == '':
        return None
    # Remove $ and , characters, handle parentheses for negative values
    cleaned = str(value).replace('$', '').replace(',', '').strip()
    if cleaned.startswith('(') and cleaned.endswith(')'):
        cleaned = '-' + cleaned[1:-1]
    try:
        return Decimal(cleaned)
    except:
        return None

def clean_numeric_value(value):
    """Clean numeric values."""
    if pd.isna(value) or value == '':
        return None
    try:
        # Remove commas and convert
        cleaned = str(value).replace(',', '').strip()
        return Decimal(cleaned)
    except:
        return None

def parse_date(date_str):
    """Parse various date formats."""
    if pd.isna(date_str):
        return None
    try:
        # Try parsing MM/DD/YYYY format
        return datetime.strptime(str(date_str), '%m/%d/%Y').date()
    except:
        try:
            # Try parsing M/D/YYYY format
            return datetime.strptime(str(date_str), '%m/%d/%Y').date()
        except:
            return None

def load_payroll_trends(conn):
    """Load payroll trends data from CSV."""
    print("Loading Payroll Trends data...")
    
    # Read the CSV file
    df = pd.read_csv('/home/tim/RFID3/shared/POR/Payroll Trends.csv')
    
    # Parse the header to understand the structure
    # Format: "2 WEEK ENDING SUN, Rental Revenue 6800, All Revenue 6800, Payroll 6800, Wage Hours 6800, ..."
    
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM executive_payroll_trends")
    
    records_inserted = 0
    
    for index, row in df.iterrows():
        week_ending = parse_date(row[0])  # First column is the date
        if not week_ending:
            continue
        
        # Process each store's data
        stores = [
            ('6800', 1, 2, 3, 4),   # Columns for store 6800
            ('3607', 5, 6, 7, 8),   # Columns for store 3607
            ('8101', 9, 10, 11, 12), # Columns for store 8101
            ('728', 13, 14, 15, 16)  # Columns for store 728
        ]
        
        for store_id, rental_col, revenue_col, payroll_col, hours_col in stores:
            # Get values with proper indexing
            rental_revenue = clean_currency_value(row.iloc[rental_col] if rental_col < len(row) else None)
            total_revenue = clean_currency_value(row.iloc[revenue_col] if revenue_col < len(row) else None)
            payroll_cost = clean_currency_value(row.iloc[payroll_col] if payroll_col < len(row) else None)
            wage_hours = clean_numeric_value(row.iloc[hours_col] if hours_col < len(row) else None)
            
            # Skip if no data for this store/week
            if not total_revenue:
                continue
            
            # Calculate derived metrics
            labor_efficiency = None
            revenue_per_hour = None
            
            if total_revenue and payroll_cost:
                labor_efficiency = (payroll_cost / total_revenue * 100)
            
            if total_revenue and wage_hours and wage_hours > 0:
                revenue_per_hour = total_revenue / wage_hours
            
            # Insert record
            sql = """
                INSERT INTO executive_payroll_trends 
                (week_ending, store_id, rental_revenue, total_revenue, payroll_cost, 
                 wage_hours, labor_efficiency_ratio, revenue_per_hour, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """
            
            cursor.execute(sql, (
                week_ending, store_id, rental_revenue, total_revenue, 
                payroll_cost, wage_hours, labor_efficiency, revenue_per_hour
            ))
            
            records_inserted += 1
    
    conn.commit()
    print(f"Inserted {records_inserted} payroll trend records")

def load_scorecard_trends(conn):
    """Load scorecard trends data from CSV."""
    print("Loading Scorecard Trends data...")
    
    # Read the CSV file - note it has many columns
    df = pd.read_csv('/home/tim/RFID3/shared/POR/Scorecard Trends.csv', low_memory=False)
    
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM executive_scorecard_trends")
    
    records_inserted = 0
    
    # Map the important columns (based on the header inspection)
    # Column indices based on the actual CSV structure
    for index, row in df.iterrows():
        week_ending = parse_date(row.iloc[0])  # First column is week ending
        if not week_ending:
            continue
        
        # Extract key metrics
        try:
            # Company-wide metrics
            total_weekly_revenue = clean_currency_value(row.iloc[1] if len(row) > 1 else None)
            
            # Store revenues
            revenue_3607 = clean_currency_value(row.iloc[2] if len(row) > 2 else None)
            revenue_6800 = clean_currency_value(row.iloc[3] if len(row) > 3 else None)
            revenue_728 = clean_currency_value(row.iloc[4] if len(row) > 4 else None)
            revenue_8101 = clean_currency_value(row.iloc[5] if len(row) > 5 else None)
            
            # Contract metrics (company-wide)
            new_contracts_3607 = clean_numeric_value(row.iloc[6] if len(row) > 6 else None)
            new_contracts_6800 = clean_numeric_value(row.iloc[7] if len(row) > 7 else None)
            new_contracts_728 = clean_numeric_value(row.iloc[8] if len(row) > 8 else None)
            new_contracts_8101 = clean_numeric_value(row.iloc[9] if len(row) > 9 else None)
            
            # Deliveries scheduled
            deliveries_8101 = clean_numeric_value(row.iloc[10] if len(row) > 10 else None)
            
            # Reservation values
            reservation_14d_3607 = clean_currency_value(row.iloc[11] if len(row) > 11 else None)
            reservation_14d_6800 = clean_currency_value(row.iloc[12] if len(row) > 12 else None)
            reservation_14d_728 = clean_currency_value(row.iloc[13] if len(row) > 13 else None)
            reservation_14d_8101 = clean_currency_value(row.iloc[14] if len(row) > 14 else None)
            
            # AR metrics
            ar_over_45_percent = clean_numeric_value(row.iloc[19] if len(row) > 19 else None)
            total_discount = clean_currency_value(row.iloc[20] if len(row) > 20 else None)
            week_number = clean_numeric_value(row.iloc[21] if len(row) > 21 else None)
            
            # Insert company-wide record
            if total_weekly_revenue:
                sql = """
                    INSERT INTO executive_scorecard_trends 
                    (week_ending, store_id, total_weekly_revenue, new_contracts_count,
                     deliveries_scheduled_next_7_days, ar_over_45_days_percent, 
                     total_discount_amount, week_number, created_at, updated_at)
                    VALUES (%s, NULL, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                """
                
                total_new_contracts = sum(filter(None, [new_contracts_3607, new_contracts_6800, 
                                                        new_contracts_728, new_contracts_8101]))
                
                cursor.execute(sql, (
                    week_ending, total_weekly_revenue, 
                    total_new_contracts if total_new_contracts else None,
                    deliveries_8101, ar_over_45_percent, total_discount, week_number
                ))
                records_inserted += 1
            
            # Insert store-specific records
            stores = [
                ('3607', revenue_3607, new_contracts_3607, reservation_14d_3607),
                ('6800', revenue_6800, new_contracts_6800, reservation_14d_6800),
                ('728', revenue_728, new_contracts_728, reservation_14d_728),
                ('8101', revenue_8101, new_contracts_8101, reservation_14d_8101)
            ]
            
            for store_id, revenue, contracts, reservation in stores:
                if revenue:
                    sql = """
                        INSERT INTO executive_scorecard_trends 
                        (week_ending, store_id, total_weekly_revenue, new_contracts_count,
                         reservation_value_next_14_days, week_number, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                    """
                    
                    cursor.execute(sql, (
                        week_ending, store_id, revenue, contracts, 
                        reservation, week_number
                    ))
                    records_inserted += 1
                    
        except Exception as e:
            print(f"Error processing row {index}: {e}")
            continue
    
    conn.commit()
    print(f"Inserted {records_inserted} scorecard trend records")

def initialize_kpis(conn):
    """Initialize default executive KPIs."""
    print("Initializing Executive KPIs...")
    
    cursor = conn.cursor()
    
    # Clear existing KPIs
    cursor.execute("DELETE FROM executive_kpi")
    
    # Define default KPIs
    kpis = [
        ('Revenue Target', 'financial', 1000000, 1200000, 'monthly', None),
        ('Labor Cost Ratio', 'efficiency', 25, 20, 'weekly', None),
        ('Contract Growth', 'growth', 100, 150, 'monthly', None),
        ('Inventory Utilization', 'operational', 75, 85, 'weekly', None),
        ('AR Collection', 'financial', 95, 98, 'monthly', None),
        ('Customer Acquisition', 'growth', 50, 75, 'monthly', None),
    ]
    
    for kpi_name, category, current, target, period, store in kpis:
        variance = ((current - target) / target * 100) if target else 0
        trend = 'up' if variance > 0 else 'down' if variance < 0 else 'stable'
        
        sql = """
            INSERT INTO executive_kpi 
            (kpi_name, kpi_category, current_value, target_value, variance_percent,
             trend_direction, period, store_id, last_calculated, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW(), NOW())
        """
        
        cursor.execute(sql, (
            kpi_name, category, current, target, variance,
            trend, period, store
        ))
    
    conn.commit()
    print("Initialized executive KPIs")

def main():
    """Main function to load all executive data."""
    print("=" * 50)
    print("Executive Dashboard Data Loader")
    print("=" * 50)
    
    # Connect to database
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        print("Connected to database successfully")
        
        # Load data
        load_payroll_trends(conn)
        load_scorecard_trends(conn)
        initialize_kpis(conn)
        
        print("\n✓ All data loaded successfully!")
        print("You can now access the Executive Dashboard at /tab/7")
        
    except mysql.connector.Error as err:
        print(f"Database error: {err}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        if conn:
            conn.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
