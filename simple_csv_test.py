#!/usr/bin/env python3
"""
Simple CSV import test - direct database connection
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import os

# Database connection - using same config as app
DB_CONFIG = {
    'host': 'localhost',
    'user': 'rfid_user', 
    'password': 'rfid_user_password',
    'database': 'rfid_inventory'
}

def test_equipment_import():
    """Test importing equipment data directly"""
    
    # Create database engine
    db_url = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset=utf8mb4"
    engine = create_engine(db_url)
    
    print("Starting equipment CSV import test...")
    
    # Read CSV file
    csv_path = "/home/tim/RFID3/shared/POR/equip8.26.25.csv"
    
    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        return
        
    print(f"Reading CSV file: {csv_path}")
    df = pd.read_csv(csv_path, encoding='utf-8', low_memory=False)
    print(f"Read {len(df)} records from CSV")
    
    # Clean data
    print("Cleaning data...")
    df['ItemNum'] = df['ItemNum'].astype(str).str.strip()
    df['Name'] = df['Name'].fillna('').astype(str).str.strip()
    df['Category'] = df['Category'].fillna('').astype(str).str.strip()
    
    # Convert financial columns
    financial_cols = ['T/O YTD', 'T/O LTD', 'RepairCost MTD', 'RepairCost LTD', 'Sell Price']
    for col in financial_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.replace('$', ''), 
                                  errors='coerce').fillna(0)
    
    # Filter valid records
    df = df[df['ItemNum'].str.len() > 0]
    df = df[df['ItemNum'] != 'nan']
    print(f"After cleaning: {len(df)} valid records")
    
    # Prepare for database import
    records = []
    for _, row in df.head(5000).iterrows():  # Import first 5000 for testing
        try:
            record = {
                'item_num': str(row.get('ItemNum', '')),
                'name': str(row.get('Name', ''))[:300],
                'category': str(row.get('Category', ''))[:100], 
                'turnover_ytd': float(row.get('T/O YTD', 0)),
                'turnover_ltd': float(row.get('T/O LTD', 0)),
                'sell_price': float(row.get('Sell Price', 0)),
                'inactive': bool(row.get('Inactive', False))
            }
            records.append(record)
        except Exception as e:
            print(f"Skipping invalid record: {e}")
            continue
    
    print(f"Prepared {len(records)} records for import")
    
    if records:
        # Import to database
        try:
            records_df = pd.DataFrame(records)
            imported_count = records_df.to_sql(
                'pos_equipment', 
                con=engine, 
                if_exists='append', 
                index=False,
                method='multi'
            )
            
            print(f"Successfully imported {len(records)} equipment records")
            
            # Check results
            with engine.connect() as conn:
                count_result = conn.execute(text("SELECT COUNT(*) as count FROM pos_equipment")).fetchone()
                print(f"Total equipment records in database: {count_result[0]}")
                
                # Show sample
                sample_result = conn.execute(text("""
                    SELECT item_num, name, category, turnover_ytd, sell_price 
                    FROM pos_equipment 
                    ORDER BY id DESC 
                    LIMIT 5
                """)).fetchall()
                
                print("\nSample imported equipment records:")
                for row in sample_result:
                    print(f"Item: {row[0]} | Name: {row[1][:40]} | Category: {row[2]} | Turnover: ${row[3]:.2f} | Price: ${row[4]:.2f}")
                    
        except Exception as e:
            print(f"Import failed: {e}")
    
    print("Test completed!")

if __name__ == "__main__":
    test_equipment_import()