#!/usr/bin/env python3
"""
Executive Summary: Database Correlation Analysis for RFID3
Focused on scorecard trends data and executive dashboard integration
"""

import json
from datetime import datetime
from app import create_app
from app.models.db_models import db
from sqlalchemy import text
import pandas as pd
import numpy as np

def run_analysis():
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*80)
        print("RFID3 DATABASE CORRELATION ANALYSIS - EXECUTIVE SUMMARY")
        print("="*80)
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 1. Database Overview
        print("1. DATABASE OVERVIEW")
        print("-" * 40)
        
        tables_info = db.session.execute(text('''
            SELECT 
                COUNT(*) as total_tables,
                SUM(DATA_LENGTH)/1024/1024 as total_size_mb,
                SUM(CASE WHEN TABLE_ROWS = 0 OR TABLE_ROWS IS NULL THEN 1 ELSE 0 END) as empty_tables
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = DATABASE()
        ''')).fetchone()
        
        print(f"Total Tables: {tables_info[0]}")
        print(f"Database Size: {tables_info[1]:.1f} MB")
        print(f"Empty Tables: {tables_info[2]} (candidates for removal)")
        
        # Get key table sizes
        key_tables = db.session.execute(text('''
            SELECT TABLE_NAME, TABLE_ROWS, ROUND(DATA_LENGTH/1024/1024, 2) as size_mb
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_ROWS > 0
            ORDER BY DATA_LENGTH DESC
            LIMIT 10
        ''')).fetchall()
        
        print("\nLargest Tables:")
        for table in key_tables[:5]:
            print(f"  • {table[0]}: {table[1]:,} rows ({table[2]} MB)")
        
        # 2. Scorecard Trends Analysis
        print("\n2. SCORECARD TRENDS DATA ANALYSIS")
        print("-" * 40)
        
        # Get scorecard data sample
        scorecard_sample = db.session.execute(text('''
            SELECT * FROM scorecard_trends_data 
            ORDER BY week_ending DESC 
            LIMIT 20
        ''')).fetchall()
        
        columns = db.session.execute(text('''
            SELECT COLUMN_NAME 
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'scorecard_trends_data'
            ORDER BY ORDINAL_POSITION
        ''')).fetchall()
        
        col_names = [col[0] for col in columns]
        
        if scorecard_sample:
            df = pd.DataFrame(scorecard_sample, columns=col_names)
            
            print(f"Total Records: {len(df)}")
            print(f"Date Range: {df['week_ending'].min()} to {df['week_ending'].max()}")
            print(f"Stores Tracked: 3607, 6800, 728, 8101")
            
            # Calculate key metrics
            print("\nKey Metrics by Store:")
            stores = ['3607', '6800', '728', '8101']
            for store in stores:
                revenue_col = f'revenue_{store}'
                if revenue_col in df.columns:
                    avg_revenue = df[revenue_col].mean()
                    if pd.notna(avg_revenue):
                        print(f"  Store {store}:")
                        print(f"    • Avg Weekly Revenue: ${avg_revenue:,.0f}")
                        
                        # Check for reservation data
                        res_col = f'reservation_next14_{store}'
                        if res_col in df.columns:
                            avg_res = df[res_col].mean()
                            if pd.notna(avg_res):
                                print(f"    • Avg 14-day Pipeline: ${avg_res:,.0f}")
                        
                        # Check for new contracts
                        contract_col = f'new_contracts_{store}'
                        if contract_col in df.columns:
                            avg_contracts = df[contract_col].mean()
                            if pd.notna(avg_contracts):
                                print(f"    • Avg New Contracts/Week: {avg_contracts:.1f}")
            
            # Analyze correlations
            print("\nCorrelation Insights:")
            correlations_found = []
            
            for store in stores:
                revenue_col = f'revenue_{store}'
                reservation_col = f'reservation_next14_{store}'
                
                if revenue_col in df.columns and reservation_col in df.columns:
                    # Clean data for correlation
                    df_clean = df[[revenue_col, reservation_col]].dropna()
                    if len(df_clean) > 3:
                        try:
                            corr = df_clean[revenue_col].corr(df_clean[reservation_col])
                            if abs(corr) > 0.3:
                                correlations_found.append({
                                    'store': store,
                                    'correlation': corr,
                                    'type': 'Revenue vs Reservation Pipeline'
                                })
                        except:
                            pass
            
            if correlations_found:
                for item in correlations_found:
                    print(f"  • Store {item['store']}: {item['type']}")
                    print(f"    Correlation: {item['correlation']:.3f}")
                    if item['correlation'] > 0.5:
                        print(f"    → Strong positive correlation - reservation pipeline is a good predictor")
            else:
                print("  • Limited correlation data available - more historical data needed")
        
        # 3. Database Cleanup Recommendations
        print("\n3. DATABASE CLEANUP RECOMMENDATIONS")
        print("-" * 40)
        
        # Get empty tables
        empty_tables = db.session.execute(text('''
            SELECT TABLE_NAME
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = DATABASE()
            AND (TABLE_ROWS = 0 OR TABLE_ROWS IS NULL)
            ORDER BY TABLE_NAME
        ''')).fetchall()
        
        print(f"Empty Tables to Remove ({len(empty_tables)} tables):")
        priority_removals = [
            'bi_operational_scorecard',
            'bi_store_performance', 
            'executive_scorecard_trends',
            'correlation_audit_log',
            'data_quality_metrics',
            'feedback_analytics',
            'pos_analytics',
            'pos_data_staging'
        ]
        
        for table in empty_tables[:8]:
            table_name = table[0]
            if table_name in priority_removals:
                print(f"  ✓ {table_name} (HIGH PRIORITY)")
            else:
                print(f"  • {table_name}")
        
        if len(empty_tables) > 8:
            print(f"  ... and {len(empty_tables) - 8} more")
        
        # Check for duplicate scorecard tables
        scorecard_tables = db.session.execute(text('''
            SELECT TABLE_NAME, TABLE_ROWS
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME LIKE '%scorecard%'
            ORDER BY TABLE_NAME
        ''')).fetchall()
        
        print("\nScorecard Table Consolidation:")
        for table in scorecard_tables:
            print(f"  • {table[0]}: {table[1] or 0} rows")
        print("  → Recommendation: Keep only 'scorecard_trends_data', remove others")
        
        # 4. Integration Strategies
        print("\n4. EXECUTIVE DASHBOARD INTEGRATION STRATEGIES")
        print("-" * 40)
        
        print("A. Immediate Implementation Opportunities:")
        print("  1. Store Performance Comparison Widget")
        print("     • Side-by-side revenue metrics for all 4 stores")
        print("     • Color-coded performance indicators (green/yellow/red)")
        print("     • Weekly trend sparklines")
        print()
        print("  2. Revenue Prediction Module") 
        print("     • Use reservation_next14 data for 2-week forecasts")
        print("     • Display confidence intervals based on historical accuracy")
        print("     • Alert when forecast deviates >15% from target")
        print()
        print("  3. Contract Pipeline Analytics")
        print("     • Track new_contracts trend by store")
        print("     • Calculate contract-to-revenue conversion rates")
        print("     • Identify high-performing stores for best practices")
        print()
        print("  4. Financial Health Dashboard")
        print("     • Monitor ar_over_45_days_percent trend")
        print("     • Track total_discount impact on margins")
        print("     • Create composite financial health score")
        
        print("\nB. Data Quality Improvements:")
        print("  • Add data validation for weekly imports")
        print("  • Implement anomaly detection for outliers")
        print("  • Create audit trail for data changes")
        print("  • Standardize store identifiers across all tables")
        
        # 5. SQL Optimization Queries
        print("\n5. DATABASE OPTIMIZATION ACTIONS")
        print("-" * 40)
        
        print("Execute these queries in order (after backup):")
        print()
        print("-- Step 1: Remove empty tables")
        print("DROP TABLE IF EXISTS bi_operational_scorecard;")
        print("DROP TABLE IF EXISTS executive_scorecard_trends;")
        print("DROP TABLE IF EXISTS pos_analytics;")
        print()
        print("-- Step 2: Add performance indexes")
        print("ALTER TABLE scorecard_trends_data ADD INDEX idx_week (week_ending);")
        print("ALTER TABLE scorecard_trends_data ADD INDEX idx_stores (revenue_3607, revenue_6800, revenue_728, revenue_8101);")
        print()
        print("-- Step 3: Create unified view")
        print("CREATE VIEW v_executive_metrics AS")
        print("SELECT week_ending, week_number,")
        print("       revenue_3607 + revenue_6800 + revenue_728 + revenue_8101 as total_revenue,")
        print("       new_contracts_3607 + new_contracts_6800 + new_contracts_728 + new_contracts_8101 as total_contracts")
        print("FROM scorecard_trends_data;")
        
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)
        
        # Generate summary statistics
        summary = {
            'database_size_mb': float(tables_info[1]) if tables_info[1] else 0,
            'total_tables': tables_info[0],
            'empty_tables': tables_info[2],
            'cleanup_potential_mb': round(float(tables_info[2]) * 0.016, 2) if tables_info[2] else 0,
            'scorecard_records': len(scorecard_sample) if scorecard_sample else 0,
            'stores_analyzed': stores,
            'correlations_found': len(correlations_found),
            'timestamp': datetime.now().isoformat()
        }
        
        # Save summary to file
        with open('database_analysis_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        print("\nNext Steps:")
        print("1. Review and execute cleanup queries (25 empty tables)")
        print("2. Implement store performance comparison in executive dashboard")
        print("3. Add revenue prediction based on reservation pipeline")
        print("4. Monitor performance improvements after optimization")
        print(f"\nDetailed summary saved to: database_analysis_summary.json")
        
        return summary

if __name__ == "__main__":
    try:
        results = run_analysis()
    except Exception as e:
        print(f"Analysis error: {str(e)}")
        import traceback
        traceback.print_exc()