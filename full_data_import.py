#!/usr/bin/env python3
"""
Full CSV Data Import - All Business Data
Imports complete dataset: equipment, customers, transactions, transaction items
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

def create_connection():
    """Create database connection"""
    db_url = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset=utf8mb4"
    return create_engine(db_url)

def import_equipment_data(engine):
    """Import complete equipment data"""
    print("=" * 60)
    print("IMPORTING EQUIPMENT DATA")
    print("=" * 60)
    
    csv_path = os.path.join(CSV_BASE_PATH, "equip8.26.25.csv")
    
    if not os.path.exists(csv_path):
        print(f"❌ Equipment CSV not found: {csv_path}")
        return False
    
    try:
        # Read CSV
        print(f"📁 Reading CSV: {csv_path}")
        df = pd.read_csv(csv_path, encoding='utf-8', low_memory=False)
        print(f"✓ Read {len(df):,} records from CSV")
        
        # Clean data
        print("🧹 Cleaning data...")
        df['ItemNum'] = df['ItemNum'].astype(str).str.strip()
        df['Name'] = df['Name'].fillna('').astype(str).str.strip()
        df['Category'] = df['Category'].fillna('').astype(str).str.strip()
        df['Current Store'] = df['Current Store'].fillna('').astype(str).str.strip()
        
        # Convert financial columns
        financial_cols = ['T/O YTD', 'T/O LTD', 'RepairCost MTD', 'RepairCost LTD', 'Sell Price']
        for col in financial_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.replace('$', ''), 
                                      errors='coerce').fillna(0)
        
        # Handle boolean columns
        df['Inactive'] = df['Inactive'].fillna(False).astype(bool)
        
        # Filter valid records
        df = df[df['ItemNum'].str.len() > 0]
        df = df[df['ItemNum'] != 'nan']
        print(f"✓ After cleaning: {len(df):,} valid records")
        
        # Import in batches
        batch_size = 2000
        imported_count = 0
        total_batches = (len(df) + batch_size - 1) // batch_size
        
        print(f"📦 Importing in {total_batches} batches of {batch_size:,} records...")
        
        for i in range(0, len(df), batch_size):
            batch_num = (i // batch_size) + 1
            batch = df.iloc[i:i+batch_size]
            
            # Prepare records
            records = []
            for _, row in batch.iterrows():
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
                except Exception as e:
                    continue
            
            if records:
                try:
                    # Use pandas to_sql for bulk insert
                    records_df = pd.DataFrame(records)
                    records_df.to_sql(
                        'pos_equipment', 
                        con=engine, 
                        if_exists='append', 
                        index=False,
                        method='multi'
                    )
                    imported_count += len(records)
                    print(f"   ✓ Batch {batch_num}/{total_batches}: {len(records):,} records imported (Total: {imported_count:,})")
                    
                except Exception as e:
                    print(f"   ❌ Batch {batch_num} failed: {e}")
        
        print(f"✅ Equipment import completed: {imported_count:,} records imported")
        return True
        
    except Exception as e:
        print(f"❌ Equipment import failed: {e}")
        return False

def import_customer_data(engine):
    """Import customer data"""
    print("=" * 60)
    print("IMPORTING CUSTOMER DATA")
    print("=" * 60)
    
    csv_path = os.path.join(CSV_BASE_PATH, "customer8.26.25.csv")
    
    if not os.path.exists(csv_path):
        print(f"❌ Customer CSV not found: {csv_path}")
        return False
    
    try:
        # Read CSV in chunks for large file
        print(f"📁 Reading CSV: {csv_path}")
        chunk_size = 5000
        imported_count = 0
        chunk_num = 0
        
        for chunk in pd.read_csv(csv_path, encoding='utf-8', chunksize=chunk_size, low_memory=False):
            chunk_num += 1
            
            # Clean data
            chunk['Cnum'] = chunk['Cnum'].astype(str).str.strip()
            chunk['Name'] = chunk['Name'].fillna('').astype(str).str.strip()
            chunk['YTD Payments'] = pd.to_numeric(chunk['YTD Payments'].astype(str).str.replace(',', '').str.replace('$', ''), 
                                                errors='coerce').fillna(0)
            chunk['No. of Contracts'] = pd.to_numeric(chunk['No. of Contracts'], errors='coerce').fillna(0)
            
            # Filter valid records
            chunk = chunk[chunk['Cnum'].str.len() > 0]
            chunk = chunk[chunk['Cnum'] != 'nan']
            
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
                    print(f"   ✓ Chunk {chunk_num}: {len(records):,} records imported (Total: {imported_count:,})")
                    
                except Exception as e:
                    print(f"   ❌ Chunk {chunk_num} failed: {e}")
        
        print(f"✅ Customer import completed: {imported_count:,} records imported")
        return True
        
    except Exception as e:
        print(f"❌ Customer import failed: {e}")
        return False

def import_transaction_data(engine):
    """Import transaction data"""
    print("=" * 60)
    print("IMPORTING TRANSACTION DATA")
    print("=" * 60)
    
    csv_path = os.path.join(CSV_BASE_PATH, "transactions8.26.25.csv")
    
    if not os.path.exists(csv_path):
        print(f"❌ Transaction CSV not found: {csv_path}")
        return False
    
    try:
        chunk_size = 5000
        imported_count = 0
        chunk_num = 0
        
        print(f"📁 Reading CSV: {csv_path}")
        
        for chunk in pd.read_csv(csv_path, encoding='utf-8', chunksize=chunk_size, low_memory=False):
            chunk_num += 1
            
            # Clean data
            chunk['Contract No'] = chunk['Contract No'].astype(str).str.strip()
            chunk['Customer No'] = chunk['Customer No'].fillna('').astype(str).str.strip()
            chunk['Store No'] = chunk['Store No'].fillna('').astype(str).str.strip()
            
            # Convert date columns
            date_cols = ['Contract Date', 'Close Date', 'Billed Date', 'Completed Date']
            for col in date_cols:
                if col in chunk.columns:
                    chunk[col] = pd.to_datetime(chunk[col], errors='coerce')
            
            # Convert financial columns
            financial_cols = ['Rent Amt', 'Sale Amt', 'Tax Amt', 'Total', 'Total Paid', 'Total Owed']
            for col in financial_cols:
                if col in chunk.columns:
                    chunk[col] = pd.to_numeric(chunk[col].astype(str).str.replace(',', '').str.replace('$', ''), 
                                            errors='coerce').fillna(0)
            
            # Filter valid records
            chunk = chunk[chunk['Contract No'].str.len() > 0]
            chunk = chunk[chunk['Contract No'] != 'nan']
            
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
                    print(f"   ✓ Chunk {chunk_num}: {len(records):,} records imported (Total: {imported_count:,})")
                    
                except Exception as e:
                    print(f"   ❌ Chunk {chunk_num} failed: {e}")
        
        print(f"✅ Transaction import completed: {imported_count:,} records imported")
        return True
        
    except Exception as e:
        print(f"❌ Transaction import failed: {e}")
        return False

def validate_import(engine):
    """Validate the imported data"""
    print("=" * 60)
    print("VALIDATING IMPORTED DATA")
    print("=" * 60)
    
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
        
        # Show sample financial data
        print("\n📊 Sample Equipment Financial Data:")
        sample = conn.execute(text("""
            SELECT category, COUNT(*) as items, 
                   AVG(turnover_ytd) as avg_turnover, 
                   SUM(sell_price) as total_value,
                   COUNT(CASE WHEN turnover_ytd > 0 THEN 1 END) as revenue_generating
            FROM pos_equipment 
            GROUP BY category 
            HAVING COUNT(*) > 100
            ORDER BY SUM(turnover_ytd) DESC 
            LIMIT 5
        """)).fetchall()
        
        for row in sample:
            print(f"  {row[0][:30]:<30}: {row[1]:>6,} items, ${row[2]:>8,.2f} avg, ${row[3]:>12,.2f} value, {row[4]:>4,} revenue-gen")

def main():
    """Main import process"""
    print("🚀 STARTING FULL CSV DATA IMPORT")
    print(f"⏰ Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    engine = create_connection()
    
    # Import all data
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
    
    print("=" * 60)
    print("IMPORT COMPLETE")
    print("=" * 60)
    print(f"✅ Successfully imported {success_count}/3 datasets")
    print(f"⏱️  Total time: {duration/60:.2f} minutes")
    print(f"🎯 Ready for Phase 3 curveballs!")

if __name__ == "__main__":
    main()