#!/usr/bin/env python3
"""
Limited CSV Data Import - First 25K records from each CSV
Optimized for testing Phase 3 capabilities without system overload
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import os
import time
from datetime import datetime

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'user': 'rfid_user', 
    'password': 'rfid_user_password',
    'database': 'rfid_inventory'
}

CSV_BASE_PATH = "/home/tim/RFID3/shared/POR"
MAX_RECORDS = 25000  # Limit per CSV file

def create_connection():
    """Create database connection"""
    db_url = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset=utf8mb4"
    return create_engine(db_url)

def clear_tables(engine):
    """Clear existing CSV tables"""
    print("🧹 Clearing existing CSV data...")
    with engine.connect() as conn:
        # Disable foreign key checks temporarily
        conn.execute(text('SET FOREIGN_KEY_CHECKS = 0'))
        
        # Clear all CSV data tables
        conn.execute(text('TRUNCATE TABLE pos_equipment'))
        conn.execute(text('TRUNCATE TABLE pos_customers'))
        conn.execute(text('TRUNCATE TABLE pos_transactions'))
        
        # Re-enable foreign key checks
        conn.execute(text('SET FOREIGN_KEY_CHECKS = 1'))
        
        conn.commit()
        print("✓ Cleared all CSV data tables")

def import_equipment_data(engine):
    """Import limited equipment data"""
    print("=" * 50)
    print("IMPORTING EQUIPMENT DATA (25K LIMIT)")
    print("=" * 50)
    
    csv_path = os.path.join(CSV_BASE_PATH, "equip8.26.25.csv")
    
    try:
        # Read CSV with limit
        print(f"📁 Reading CSV: {csv_path}")
        df = pd.read_csv(csv_path, encoding='utf-8', low_memory=False, nrows=MAX_RECORDS)
        print(f"✓ Read {len(df):,} records from CSV")
        
        # Clean data
        print("🧹 Cleaning data...")
        df['ItemNum'] = df['ItemNum'].astype(str).str.strip()
        df['Name'] = df['Name'].fillna('').astype(str).str.strip()
        df['Category'] = df['Category'].fillna('').astype(str).str.strip()
        df['Current Store'] = df['Current Store'].fillna('').astype(str).str.strip()
        
        # Convert financial columns with regex=False to avoid warning
        financial_cols = ['T/O YTD', 'T/O LTD', 'RepairCost MTD', 'RepairCost LTD', 'Sell Price']
        for col in financial_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '', regex=False).str.replace('$', '', regex=False), 
                                      errors='coerce').fillna(0)
        
        # Handle boolean columns
        df['Inactive'] = df['Inactive'].fillna(False).astype(bool)
        
        # Filter valid records
        df = df[df['ItemNum'].str.len() > 0]
        df = df[df['ItemNum'] != 'nan']
        print(f"✓ After cleaning: {len(df):,} valid records")
        
        # Import in smaller chunks
        chunk_size = 1000
        imported_count = 0
        total_chunks = (len(df) + chunk_size - 1) // chunk_size
        
        print(f"📦 Importing in {total_chunks} chunks of {chunk_size:,} records...")
        
        for i in range(0, len(df), chunk_size):
            chunk_num = (i // chunk_size) + 1
            chunk = df.iloc[i:i+chunk_size]
            
            # Prepare records
            records = []
            for _, row in chunk.iterrows():
                try:
                    record = {
                        'item_num': str(row.get('ItemNum', '')),
                        'name': str(row.get('Name', ''))[:300],
                        'category': str(row.get('Category', ''))[:100],
                        'turnover_ytd': float(row.get('T/O YTD', 0)),
                        'turnover_ltd': float(row.get('T/O LTD', 0)),
                        'repair_cost_ytd': float(row.get('RepairCost MTD', 0)),
                        'sell_price': float(row.get('Sell Price', 0)),
                        'current_store': str(row.get('Current Store', ''))[:10],
                        'inactive': bool(row.get('Inactive', False))
                    }
                    records.append(record)
                except Exception:
                    continue
            
            if records:
                try:
                    records_df = pd.DataFrame(records)
                    records_df.to_sql(
                        'pos_equipment', 
                        con=engine, 
                        if_exists='append', 
                        index=False,
                        method='multi'
                    )
                    imported_count += len(records)
                    if chunk_num % 5 == 0 or chunk_num == total_chunks:  # Progress every 5 chunks
                        print(f"   ✓ Chunk {chunk_num}/{total_chunks}: {imported_count:,} total records imported")
                    
                except Exception as e:
                    print(f"   ❌ Chunk {chunk_num} failed: {e}")
        
        print(f"✅ Equipment import completed: {imported_count:,} records")
        return True
        
    except Exception as e:
        print(f"❌ Equipment import failed: {e}")
        return False

def import_customer_data(engine):
    """Import limited customer data"""
    print("=" * 50)
    print("IMPORTING CUSTOMER DATA (25K LIMIT)")
    print("=" * 50)
    
    csv_path = os.path.join(CSV_BASE_PATH, "customer8.26.25.csv")
    
    try:
        print(f"📁 Reading CSV: {csv_path}")
        df = pd.read_csv(csv_path, encoding='utf-8', low_memory=False, nrows=MAX_RECORDS)
        print(f"✓ Read {len(df):,} records from CSV")
        
        # Clean data
        print("🧹 Cleaning data...")
        df['Cnum'] = df['Cnum'].astype(str).str.strip()
        df['Name'] = df['Name'].fillna('').astype(str).str.strip()
        df['YTD Payments'] = pd.to_numeric(df['YTD Payments'].astype(str).str.replace(',', '', regex=False).str.replace('$', '', regex=False), 
                                          errors='coerce').fillna(0)
        df['No. of Contracts'] = pd.to_numeric(df['No. of Contracts'], errors='coerce').fillna(0)
        
        # Filter valid records
        df = df[df['Cnum'].str.len() > 0]
        df = df[df['Cnum'] != 'nan']
        print(f"✓ After cleaning: {len(df):,} valid records")
        
        # Import in chunks
        chunk_size = 1000
        imported_count = 0
        total_chunks = (len(df) + chunk_size - 1) // chunk_size
        
        print(f"📦 Importing in {total_chunks} chunks...")
        
        for i in range(0, len(df), chunk_size):
            chunk_num = (i // chunk_size) + 1
            chunk = df.iloc[i:i+chunk_size]
            
            # Prepare records
            records = []
            for _, row in chunk.iterrows():
                try:
                    record = {
                        'cnum': str(row.get('Cnum', ''))[:20],
                        'name': str(row.get('Name', ''))[:200],
                        'ytd_payments': float(row.get('YTD Payments', 0)),
                        'no_of_contracts': int(row.get('No. of Contracts', 0))
                    }
                    records.append(record)
                except Exception:
                    continue
            
            if records:
                try:
                    records_df = pd.DataFrame(records)
                    records_df.to_sql(
                        'pos_customers', 
                        con=engine, 
                        if_exists='append', 
                        index=False,
                        method='multi'
                    )
                    imported_count += len(records)
                    if chunk_num % 5 == 0 or chunk_num == total_chunks:
                        print(f"   ✓ Chunk {chunk_num}/{total_chunks}: {imported_count:,} total records imported")
                    
                except Exception as e:
                    print(f"   ❌ Chunk {chunk_num} failed: {e}")
        
        print(f"✅ Customer import completed: {imported_count:,} records")
        return True
        
    except Exception as e:
        print(f"❌ Customer import failed: {e}")
        return False

def import_transaction_data(engine):
    """Import limited transaction data"""
    print("=" * 50)
    print("IMPORTING TRANSACTION DATA (25K LIMIT)")
    print("=" * 50)
    
    csv_path = os.path.join(CSV_BASE_PATH, "transactions8.26.25.csv")
    
    try:
        print(f"📁 Reading CSV: {csv_path}")
        df = pd.read_csv(csv_path, encoding='utf-8', low_memory=False, nrows=MAX_RECORDS)
        print(f"✓ Read {len(df):,} records from CSV")
        
        # Clean data
        print("🧹 Cleaning data...")
        df['Contract No'] = df['Contract No'].astype(str).str.strip()
        df['Customer No'] = df['Customer No'].fillna('').astype(str).str.strip()
        df['Store No'] = df['Store No'].fillna('').astype(str).str.strip()
        
        # Convert date columns
        date_cols = ['Contract Date', 'Close Date', 'Billed Date', 'Completed Date']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Convert financial columns
        financial_cols = ['Rent Amt', 'Sale Amt', 'Tax Amt', 'Total', 'Total Paid', 'Total Owed']
        for col in financial_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '', regex=False).str.replace('$', '', regex=False), 
                                      errors='coerce').fillna(0)
        
        # Filter valid records
        df = df[df['Contract No'].str.len() > 0]
        df = df[df['Contract No'] != 'nan']
        print(f"✓ After cleaning: {len(df):,} valid records")
        
        # Import in chunks
        chunk_size = 1000
        imported_count = 0
        total_chunks = (len(df) + chunk_size - 1) // chunk_size
        
        print(f"📦 Importing in {total_chunks} chunks...")
        
        for i in range(0, len(df), chunk_size):
            chunk_num = (i // chunk_size) + 1
            chunk = df.iloc[i:i+chunk_size]
            
            # Prepare records
            records = []
            for _, row in chunk.iterrows():
                try:
                    record = {
                        'contract_no': str(row.get('Contract No', ''))[:50],
                        'store_no': str(row.get('Store No', ''))[:10],
                        'customer_no': str(row.get('Customer No', ''))[:20],
                        'status': str(row.get('Status', ''))[:50],
                        'contract_date': row.get('Contract Date'),
                        'close_date': row.get('Close Date'),
                        'rent_amt': float(row.get('Rent Amt', 0)),
                        'total': float(row.get('Total', 0)),
                        'total_paid': float(row.get('Total Paid', 0))
                    }
                    records.append(record)
                except Exception:
                    continue
            
            if records:
                try:
                    records_df = pd.DataFrame(records)
                    records_df.to_sql(
                        'pos_transactions', 
                        con=engine, 
                        if_exists='append', 
                        index=False,
                        method='multi'
                    )
                    imported_count += len(records)
                    if chunk_num % 5 == 0 or chunk_num == total_chunks:
                        print(f"   ✓ Chunk {chunk_num}/{total_chunks}: {imported_count:,} total records imported")
                    
                except Exception as e:
                    print(f"   ❌ Chunk {chunk_num} failed: {e}")
        
        print(f"✅ Transaction import completed: {imported_count:,} records")
        return True
        
    except Exception as e:
        print(f"❌ Transaction import failed: {e}")
        return False

def validate_import(engine):
    """Validate the imported data"""
    print("=" * 50)
    print("VALIDATING IMPORTED DATA")
    print("=" * 50)
    
    with engine.connect() as conn:
        # Check counts
        tables = ['pos_equipment', 'pos_customers', 'pos_transactions']
        
        for table in tables:
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()
                count = result[0]
                print(f"✓ {table}: {count:,} records")
            except Exception as e:
                print(f"❌ {table}: Error - {e}")
        
        # Show sample business insights
        print("\n📊 Sample Business Intelligence:")
        
        # Equipment insights
        try:
            equipment_sample = conn.execute(text("""
                SELECT 
                    category, 
                    COUNT(*) as items, 
                    ROUND(AVG(turnover_ytd), 2) as avg_turnover,
                    ROUND(SUM(sell_price), 2) as total_value,
                    COUNT(CASE WHEN turnover_ytd > 0 THEN 1 END) as revenue_generating
                FROM pos_equipment 
                WHERE category != 'UNUSED' AND category != ''
                GROUP BY category 
                HAVING COUNT(*) >= 10
                ORDER BY SUM(turnover_ytd) DESC 
                LIMIT 8
            """)).fetchall()
            
            print("\n🏷️  Top Equipment Categories:")
            for row in equipment_sample:
                print(f"  {row[0][:35]:<35}: {row[1]:>5,} items, ${row[2]:>8,.2f} avg, ${row[3]:>12,.2f} value, {row[4]:>4,} revenue-gen")
        except Exception as e:
            print(f"   Equipment analysis failed: {e}")
        
        # Customer insights
        try:
            customer_sample = conn.execute(text("""
                SELECT 
                    'Top Customers' as metric,
                    COUNT(CASE WHEN ytd_payments > 1000 THEN 1 END) as high_value,
                    COUNT(CASE WHEN ytd_payments > 0 THEN 1 END) as active,
                    ROUND(AVG(ytd_payments), 2) as avg_payment,
                    ROUND(SUM(ytd_payments), 2) as total_payments
                FROM pos_customers
            """)).fetchone()
            
            print(f"\n👥 Customer Insights:")
            print(f"  High-value customers (>$1K): {customer_sample[1]:,}")
            print(f"  Active customers: {customer_sample[2]:,}")
            print(f"  Average YTD payment: ${customer_sample[3]:,.2f}")
            print(f"  Total YTD payments: ${customer_sample[4]:,.2f}")
        except Exception as e:
            print(f"   Customer analysis failed: {e}")

def main():
    """Main import process"""
    print("🚀 STARTING LIMITED CSV DATA IMPORT (25K EACH)")
    print(f"⏰ Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    engine = create_connection()
    
    # Clear existing data
    clear_tables(engine)
    
    # Import limited datasets
    success_count = 0
    
    if import_equipment_data(engine):
        success_count += 1
    
    if import_customer_data(engine):
        success_count += 1
    
    if import_transaction_data(engine):
        success_count += 1
    
    # Validate results
    validate_import(engine)
    
    # Summary
    end_time = time.time()
    duration = end_time - start_time
    
    print("=" * 50)
    print("LIMITED IMPORT COMPLETE")
    print("=" * 50)
    print(f"✅ Successfully imported {success_count}/3 datasets")
    print(f"⏱️  Total time: {duration/60:.2f} minutes")
    print(f"🎯 Ready for Phase 3 curveballs with substantial test data!")

if __name__ == "__main__":
    main()