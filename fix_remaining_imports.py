#!/usr/bin/env python3
"""
Fix remaining CSV imports - customers and transactions
"""

import pandas as pd
from sqlalchemy import create_engine
import os
from datetime import datetime

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'user': 'rfid_user', 
    'password': 'rfid_user_password',
    'database': 'rfid_inventory'
}

CSV_BASE_PATH = "/home/tim/RFID3/shared/POR"
MAX_RECORDS = 25000

def create_connection():
    db_url = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset=utf8mb4"
    return create_engine(db_url)

def import_customer_data_fixed(engine):
    """Import customer data with correct column names"""
    print("IMPORTING CUSTOMER DATA (FIXED)")
    print("=" * 50)
    
    csv_path = os.path.join(CSV_BASE_PATH, "customer8.26.25.csv")
    
    try:
        print(f"📁 Reading CSV: {csv_path}")
        df = pd.read_csv(csv_path, encoding='utf-8', low_memory=False, nrows=MAX_RECORDS)
        print(f"✓ Read {len(df):,} records from CSV")
        
        # Clean data - use correct column name CNUM
        print("🧹 Cleaning data...")
        df['CNUM'] = df['CNUM'].astype(str).str.strip()
        df['Name'] = df['Name'].fillna('').astype(str).str.strip()
        df['YTD Payments'] = pd.to_numeric(df['YTD Payments'].astype(str).str.replace(',', '', regex=False).str.replace('$', '', regex=False), 
                                          errors='coerce').fillna(0)
        df['No of Contracts'] = pd.to_numeric(df['No of Contracts'], errors='coerce').fillna(0)
        
        # Filter valid records
        df = df[df['CNUM'].str.len() > 0]
        df = df[df['CNUM'] != 'nan']
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
                        'cnum': str(row.get('CNUM', ''))[:20],  # Use CNUM
                        'name': str(row.get('Name', ''))[:200],
                        'ytd_payments': float(row.get('YTD Payments', 0)),
                        'no_of_contracts': int(row.get('No of Contracts', 0))
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

def import_transaction_data_fixed(engine):
    """Import transaction data with proper import_date handling"""
    print("IMPORTING TRANSACTION DATA (FIXED)")
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
            
            # Prepare records - don't include import_date, let default handle it
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
                        # import_date will use DEFAULT CURRENT_TIMESTAMP
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

def main():
    engine = create_connection()
    
    print("🔧 FIXING REMAINING CSV IMPORTS")
    print(f"⏰ Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success_count = 0
    
    # Import customers with fix
    if import_customer_data_fixed(engine):
        success_count += 1
    
    # Import transactions with fix  
    if import_transaction_data_fixed(engine):
        success_count += 1
    
    print(f"\n✅ Fixed imports completed: {success_count}/2 successful")

if __name__ == "__main__":
    main()