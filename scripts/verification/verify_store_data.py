#!/usr/bin/env python3
"""
Verify the imported store data and check for actual revenue values
"""

import sys
sys.path.append('/home/tim/RFID3')

from sqlalchemy import create_engine, text
from config import DB_CONFIG

def check_store_data():
    """Check the imported store data"""
    
    database_url = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
    engine = create_engine(database_url, pool_pre_ping=True)
    
    with engine.connect() as conn:
        print("=== STORE REVENUE DATA VERIFICATION ===")
        
        # Check for non-null store revenue data
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(CASE WHEN store_3607_revenue IS NOT NULL AND store_3607_revenue > 0 THEN 1 END) as store_3607_data,
                COUNT(CASE WHEN store_6800_revenue IS NOT NULL AND store_6800_revenue > 0 THEN 1 END) as store_6800_data,
                COUNT(CASE WHEN store_728_revenue IS NOT NULL AND store_728_revenue > 0 THEN 1 END) as store_728_data,
                COUNT(CASE WHEN store_8101_revenue IS NOT NULL AND store_8101_revenue > 0 THEN 1 END) as store_8101_data
            FROM pos_scorecard_trends
        """))
        
        store_counts = result.fetchone()
        print(f"Total Rows: {store_counts[0]}")
        print(f"Store 3607 Revenue Records: {store_counts[1]}")
        print(f"Store 6800 Revenue Records: {store_counts[2]}")
        print(f"Store 728 Revenue Records: {store_counts[3]}")
        print(f"Store 8101 Revenue Records: {store_counts[4]}")
        print()
        
        # Get some sample records with store data
        print("=== SAMPLE RECORDS WITH STORE REVENUE ===")
        result = conn.execute(text("""
            SELECT 
                week_ending_sunday,
                total_weekly_revenue,
                store_3607_revenue,
                store_6800_revenue,
                store_728_revenue,
                store_8101_revenue,
                total_ar_45_days
            FROM pos_scorecard_trends 
            WHERE store_3607_revenue IS NOT NULL 
               OR store_6800_revenue IS NOT NULL 
               OR store_728_revenue IS NOT NULL 
               OR store_8101_revenue IS NOT NULL
            ORDER BY week_ending_sunday DESC
            LIMIT 5
        """))
        
        samples = result.fetchall()
        print(f"Found {len(samples)} records with store revenue data")
        
        for i, sample in enumerate(samples):
            print(f"\nSample {i+1}:")
            print(f"  Date: {sample[0]}")
            print(f"  Total Revenue: ${sample[1]:,.2f}")
            print(f"  Store 3607: ${sample[2]:,.2f}" if sample[2] else f"  Store 3607: None")
            print(f"  Store 6800: ${sample[3]:,.2f}" if sample[3] else f"  Store 6800: None")
            print(f"  Store 728: ${sample[4]:,.2f}" if sample[4] else f"  Store 728: None")
            print(f"  Store 8101: ${sample[5]:,.2f}" if sample[5] else f"  Store 8101: None")
            print(f"  AR >45 days: {sample[6]*100:.1f}%" if sample[6] else f"  AR >45 days: None")
        
        # Check total weekly revenue data
        print("\n=== TOTAL WEEKLY REVENUE VERIFICATION ===")
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total_rows,
                COUNT(CASE WHEN total_weekly_revenue IS NOT NULL AND total_weekly_revenue > 0 THEN 1 END) as revenue_records,
                AVG(total_weekly_revenue) as avg_revenue,
                MIN(total_weekly_revenue) as min_revenue,
                MAX(total_weekly_revenue) as max_revenue
            FROM pos_scorecard_trends
            WHERE total_weekly_revenue IS NOT NULL
        """))
        
        revenue_stats = result.fetchone()
        print(f"Total Rows: {revenue_stats[0]}")
        print(f"Revenue Records: {revenue_stats[1]}")
        print(f"Average Revenue: ${revenue_stats[2]:,.2f}" if revenue_stats[2] else "Average Revenue: N/A")
        print(f"Min Revenue: ${revenue_stats[3]:,.2f}" if revenue_stats[3] else "Min Revenue: N/A")
        print(f"Max Revenue: ${revenue_stats[4]:,.2f}" if revenue_stats[4] else "Max Revenue: N/A")
        
        # Check percentage data
        print("\n=== PERCENTAGE DATA VERIFICATION ===")
        result = conn.execute(text("""
            SELECT 
                COUNT(CASE WHEN total_ar_45_days IS NOT NULL THEN 1 END) as percentage_records,
                AVG(total_ar_45_days * 100) as avg_percentage,
                MIN(total_ar_45_days * 100) as min_percentage,
                MAX(total_ar_45_days * 100) as max_percentage
            FROM pos_scorecard_trends
            WHERE total_ar_45_days IS NOT NULL
        """))
        
        pct_stats = result.fetchone()
        print(f"Percentage Records: {pct_stats[0]}")
        print(f"Average AR >45 days: {pct_stats[1]:.1f}%" if pct_stats[1] else "Average AR >45 days: N/A")
        print(f"Min AR >45 days: {pct_stats[2]:.1f}%" if pct_stats[2] else "Min AR >45 days: N/A")
        print(f"Max AR >45 days: {pct_stats[3]:.1f}%" if pct_stats[3] else "Max AR >45 days: N/A")

if __name__ == "__main__":
    check_store_data()
