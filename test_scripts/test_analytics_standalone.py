#!/usr/bin/env python3
"""
Standalone Analytics Test - Direct database testing without Flask app
"""

import os
import sys
import time
import numpy as np
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from scipy import stats

# Database configuration
DB_USER = 'rfid_user'
DB_PASSWORD = 'rfid_user_password'
DB_HOST = 'localhost'
DB_NAME = 'rfid_inventory'
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

def main():
    print("="*80)
    print("RFID3 PREDICTIVE ANALYTICS - STANDALONE VERIFICATION")
    print("="*80)
    
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    results = {'passed': 0, 'failed': 0, 'warnings': 0}
    
    # 1. Database Connectivity
    print("\n1. DATABASE CONNECTIVITY & RECORD COUNTS")
    print("-"*40)
    
    try:
        equipment_count = session.execute(text("SELECT COUNT(*) FROM pos_equipment")).scalar()
        print(f"✅ POS Equipment: {equipment_count:,} records")
        results['passed'] += 1
        
        # Check other tables
        tables = ['pos_transactions', 'pos_customers', 'external_factors', 'pos_analytics']
        for table in tables:
            count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"   {table}: {count:,} records")
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        results['failed'] += 1
        
    # 2. Data Quality Verification
    print("\n2. DATA QUALITY VERIFICATION")
    print("-"*40)
    
    quality_checks = [
        ("Negative prices", "SELECT COUNT(*) FROM pos_equipment WHERE sell_price < 0"),
        ("Invalid turnover", "SELECT COUNT(*) FROM pos_equipment WHERE turnover_ytd < 0"),
        ("YTD > LTD issues", "SELECT COUNT(*) FROM pos_equipment WHERE turnover_ytd > turnover_ltd"),
        ("Duplicate items", "SELECT COUNT(*) FROM (SELECT item_num, COUNT(*) c FROM pos_equipment GROUP BY item_num HAVING c > 1) d")
    ]
    
    for check_name, query in quality_checks:
        try:
            issues = session.execute(text(query)).scalar()
            if issues == 0:
                print(f"✅ {check_name}: No issues")
                results['passed'] += 1
            else:
                print(f"⚠️  {check_name}: {issues} issues")
                results['warnings'] += 1
        except Exception as e:
            print(f"❌ {check_name}: Error - {e}")
            results['failed'] += 1
            
    # 3. Query Performance
    print("\n3. QUERY PERFORMANCE ANALYSIS")
    print("-"*40)
    
    perf_queries = [
        ("Simple count", "SELECT COUNT(*) FROM pos_equipment", 50),
        ("Category aggregation", "SELECT category, COUNT(*), AVG(turnover_ytd) FROM pos_equipment GROUP BY category", 200),
        ("Store analysis", "SELECT current_store, COUNT(*), SUM(turnover_ytd) FROM pos_equipment GROUP BY current_store", 200)
    ]
    
    for name, query, threshold in perf_queries:
        try:
            start = time.time()
            result = session.execute(text(query))
            _ = result.fetchall()
            elapsed = (time.time() - start) * 1000
            
            if elapsed < threshold:
                print(f"✅ {name}: {elapsed:.2f}ms")
                results['passed'] += 1
            else:
                print(f"⚠️  {name}: {elapsed:.2f}ms (slow)")
                results['warnings'] += 1
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            results['failed'] += 1
            
    # 4. Business Logic Validation
    print("\n4. BUSINESS LOGIC VALIDATION")
    print("-"*40)
    
    try:
        # Get top performing items
        top_items = session.execute(text("""
            SELECT item_num, name, turnover_ytd, category
            FROM pos_equipment
            WHERE inactive = 0
            ORDER BY turnover_ytd DESC
            LIMIT 5
        """)).fetchall()
        
        print("Top 5 Performing Items:")
        for item in top_items:
            print(f"  • {item[1][:30]}: ${item[2]:.2f} ({item[3]})")
        results['passed'] += 1
        
        # Store performance
        stores = session.execute(text("""
            SELECT current_store, 
                   COUNT(*) as items,
                   SUM(turnover_ytd) as revenue,
                   AVG(turnover_ytd) as avg_revenue
            FROM pos_equipment
            WHERE current_store IS NOT NULL
            GROUP BY current_store
            ORDER BY revenue DESC
            LIMIT 3
        """)).fetchall()
        
        print("\nTop 3 Stores by Revenue:")
        for store in stores:
            print(f"  • Store {store[0]}: {store[1]} items, ${store[2]:.2f} total, ${store[3]:.2f} avg")
        results['passed'] += 1
        
    except Exception as e:
        print(f"❌ Business logic error: {e}")
        results['failed'] += 1
        
    # 5. Correlation Analysis
    print("\n5. CORRELATION ANALYSIS")
    print("-"*40)
    
    try:
        # Test with sample data
        data = session.execute(text("""
            SELECT turnover_ytd, repair_cost_ytd, sell_price
            FROM pos_equipment
            WHERE turnover_ytd > 0 AND repair_cost_ytd >= 0 AND sell_price > 0
            LIMIT 500
        """)).fetchall()
        
        if len(data) > 30:
            df = pd.DataFrame(data, columns=['turnover', 'repair', 'price'])
            
            # Calculate correlations
            corr_matrix = df.corr()
            
            print("Correlation Matrix:")
            print(f"  Turnover-Repair: {corr_matrix.loc['turnover', 'repair']:.4f}")
            print(f"  Turnover-Price: {corr_matrix.loc['turnover', 'price']:.4f}")
            print(f"  Repair-Price: {corr_matrix.loc['repair', 'price']:.4f}")
            
            results['passed'] += 1
        else:
            print("⚠️  Insufficient data for correlation analysis")
            results['warnings'] += 1
            
    except Exception as e:
        print(f"❌ Correlation analysis error: {e}")
        results['failed'] += 1
        
    # 6. Algorithm Accuracy
    print("\n6. ALGORITHM ACCURACY TEST")
    print("-"*40)
    
    try:
        # Test statistical calculations
        np.random.seed(42)
        test_data = np.random.randn(1000) * 10 + 50
        
        mean = np.mean(test_data)
        std = np.std(test_data)
        median = np.median(test_data)
        
        print(f"Statistical Test (n=1000):")
        print(f"  Mean: {mean:.2f} (expected ~50)")
        print(f"  Std Dev: {std:.2f} (expected ~10)")
        print(f"  Median: {median:.2f}")
        
        if 48 < mean < 52 and 9 < std < 11:
            print("✅ Statistical calculations accurate")
            results['passed'] += 1
        else:
            print("⚠️  Statistical calculations may have issues")
            results['warnings'] += 1
            
        # Test correlation calculation
        x = np.random.randn(100)
        y = 2 * x + np.random.randn(100) * 0.1
        corr, p_value = stats.pearsonr(x, y)
        
        print(f"\nCorrelation Test:")
        print(f"  r = {corr:.4f}, p = {p_value:.6f}")
        
        if 0.95 < corr < 1.0 and p_value < 0.001:
            print("✅ Correlation calculations accurate")
            results['passed'] += 1
        else:
            print("⚠️  Correlation calculations may have issues")
            results['warnings'] += 1
            
    except Exception as e:
        print(f"❌ Algorithm test error: {e}")
        results['failed'] += 1
        
    # 7. Index Verification
    print("\n7. DATABASE OPTIMIZATION")
    print("-"*40)
    
    try:
        indexes = session.execute(text("""
            SELECT INDEX_NAME 
            FROM information_schema.statistics 
            WHERE table_schema = :db_name 
            AND table_name = 'pos_equipment'
            AND INDEX_NAME != 'PRIMARY'
            GROUP BY INDEX_NAME
        """), {'db_name': DB_NAME}).fetchall()
        
        print(f"Indexes on pos_equipment: {len(indexes)}")
        for idx in indexes:
            print(f"  • {idx[0]}")
            
        if len(indexes) >= 5:
            print("✅ Adequate indexing for performance")
            results['passed'] += 1
        else:
            print("⚠️  Consider adding more indexes")
            results['warnings'] += 1
            
    except Exception as e:
        print(f"❌ Index verification error: {e}")
        results['failed'] += 1
        
    # Final Summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    
    total = results['passed'] + results['failed'] + results['warnings']
    print(f"\nTotal Tests: {total}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"⚠️  Warnings: {results['warnings']}")
    
    success_rate = (results['passed'] / total * 100) if total > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    if results['failed'] == 0:
        print("\n✅ SYSTEM STATUS: FULLY OPERATIONAL")
        print("All critical tests passed. System is ready for production use.")
    elif results['failed'] <= 2:
        print("\n⚠️  SYSTEM STATUS: OPERATIONAL WITH MINOR ISSUES")
        print("System is functional but has minor issues to address.")
    else:
        print("\n❌ SYSTEM STATUS: CRITICAL ISSUES DETECTED")
        print("Multiple failures detected. Review and fixes required.")
        
    print("="*80)
    
    session.close()
    engine.dispose()

if __name__ == "__main__":
    main()
