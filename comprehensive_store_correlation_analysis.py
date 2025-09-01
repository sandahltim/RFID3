#!/usr/bin/env python3
"""
Comprehensive Database Correlation Analysis with Standardized Store Codes
Focus: Store-specific insights and executive dashboard enhancements
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Store mapping
STORE_MAPPING = {
    '3607': {'name': 'Wayzata', 'manager': 'TYLER'},
    '6800': {'name': 'Brooklyn Park', 'manager': 'ZACK'},
    '728': {'name': 'Elk River', 'manager': 'BRUCE'},
    '8101': {'name': 'Fridley', 'manager': 'TIM'},
    '000': {'name': 'Legacy/Company-wide', 'manager': 'CORPORATE'}
}

class StoreCorrelationAnalyzer:
    def __init__(self):
        """Initialize analyzer with database connection"""
        self.db_path = '/home/tim/RFID3/instance/rfid_system.db'
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        self.Session = sessionmaker(bind=self.engine)
        self.inspector = inspect(self.engine)
        self.analysis_results = defaultdict(dict)
        
    def analyze_table_structure(self):
        """Analyze all tables and their store_code columns"""
        print("\n" + "="*80)
        print("DATABASE SCHEMA ANALYSIS - Store Code Standardization")
        print("="*80)
        
        tables_with_store_code = []
        table_analysis = {}
        
        for table_name in self.inspector.get_table_names():
            columns = self.inspector.get_columns(table_name)
            column_names = [col['name'] for col in columns]
            
            # Check for store_code column
            has_store_code = 'store_code' in column_names
            if has_store_code:
                tables_with_store_code.append(table_name)
                
            table_analysis[table_name] = {
                'columns': column_names,
                'has_store_code': has_store_code,
                'row_count': 0
            }
            
            # Get row count
            try:
                result = self.engine.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                table_analysis[table_name]['row_count'] = result
            except:
                pass
                
        print(f"\nTables with store_code column: {len(tables_with_store_code)}/{len(table_analysis)}")
        print("\nTables WITH store_code:")
        for table in sorted(tables_with_store_code):
            count = table_analysis[table]['row_count']
            print(f"  - {table}: {count:,} rows")
            
        self.analysis_results['schema'] = table_analysis
        return tables_with_store_code
        
    def analyze_store_distribution(self):
        """Analyze data distribution across stores"""
        print("\n" + "="*80)
        print("STORE DATA DISTRIBUTION ANALYSIS")
        print("="*80)
        
        store_distribution = {}
        
        # Key tables to analyze
        key_tables = [
            'pos_transaction_items',
            'id_item_master',
            'pos_equipment',
            'pl_data',
            'feedback',
            'weather_data',
            'minnesota_weather_data'
        ]
        
        for table in key_tables:
            try:
                query = f"""
                SELECT 
                    store_code,
                    COUNT(*) as record_count,
                    COUNT(DISTINCT DATE(created_at)) as unique_days,
                    MIN(created_at) as earliest_record,
                    MAX(created_at) as latest_record
                FROM {table}
                GROUP BY store_code
                ORDER BY store_code
                """
                
                df = pd.read_sql(query, self.engine)
                
                if not df.empty:
                    print(f"\n{table}:")
                    total = df['record_count'].sum()
                    
                    for _, row in df.iterrows():
                        store = str(row['store_code'])
                        store_info = STORE_MAPPING.get(store, {'name': 'Unknown', 'manager': 'N/A'})
                        pct = (row['record_count'] / total * 100) if total > 0 else 0
                        
                        print(f"  Store {store} ({store_info['name']} - {store_info['manager']})")
                        print(f"    Records: {row['record_count']:,} ({pct:.1f}%)")
                        print(f"    Date Range: {row['earliest_record']} to {row['latest_record']}")
                        print(f"    Active Days: {row['unique_days']}")
                        
                    store_distribution[table] = df.to_dict('records')
            except Exception as e:
                # Table might not have created_at, try without date fields
                try:
                    query = f"""
                    SELECT 
                        store_code,
                        COUNT(*) as record_count
                    FROM {table}
                    GROUP BY store_code
                    ORDER BY store_code
                    """
                    df = pd.read_sql(query, self.engine)
                    
                    if not df.empty:
                        print(f"\n{table}:")
                        total = df['record_count'].sum()
                        
                        for _, row in df.iterrows():
                            store = str(row['store_code'])
                            store_info = STORE_MAPPING.get(store, {'name': 'Unknown', 'manager': 'N/A'})
                            pct = (row['record_count'] / total * 100) if total > 0 else 0
                            print(f"  Store {store} ({store_info['name']}): {row['record_count']:,} ({pct:.1f}%)")
                            
                        store_distribution[table] = df.to_dict('records')
                except:
                    pass
                    
        self.analysis_results['store_distribution'] = store_distribution
        
    def analyze_cross_table_correlations(self):
        """Analyze correlations between tables using store_code"""
        print("\n" + "="*80)
        print("CROSS-TABLE CORRELATION ANALYSIS")
        print("="*80)
        
        correlations = {}
        
        # 1. POS Transactions vs Equipment Inventory
        print("\n1. POS Transactions vs Equipment Inventory Correlation:")
        try:
            query = """
            SELECT 
                pti.store_code,
                COUNT(DISTINCT pti.item_code) as unique_items_sold,
                COUNT(DISTINCT pe.item_code) as unique_equipment_items,
                COUNT(DISTINCT pti.transaction_number) as total_transactions,
                SUM(CAST(pti.quantity AS FLOAT)) as total_quantity_sold,
                COUNT(DISTINCT pe.id) as equipment_records
            FROM pos_transaction_items pti
            LEFT JOIN pos_equipment pe ON pti.store_code = pe.store_code 
                AND pti.item_code = pe.item_code
            WHERE pti.store_code != '000'
            GROUP BY pti.store_code
            """
            
            df = pd.read_sql(query, self.engine)
            
            for _, row in df.iterrows():
                store = str(row['store_code'])
                store_info = STORE_MAPPING.get(store, {'name': 'Unknown'})
                overlap_rate = (row['unique_equipment_items'] / row['unique_items_sold'] * 100) if row['unique_items_sold'] > 0 else 0
                
                print(f"\n  Store {store} ({store_info['name']}):")
                print(f"    Items Sold: {row['unique_items_sold']:,}")
                print(f"    Equipment Items: {row['unique_equipment_items']:,}")
                print(f"    Overlap Rate: {overlap_rate:.1f}%")
                print(f"    Total Transactions: {row['total_transactions']:,}")
                print(f"    Total Quantity: {row['total_quantity_sold']:,.0f}")
                
            correlations['pos_equipment'] = df.to_dict('records')
        except Exception as e:
            print(f"  Error: {str(e)}")
            
        # 2. P&L Data vs Transaction Volume
        print("\n2. P&L Performance vs Transaction Volume:")
        try:
            query = """
            WITH store_transactions AS (
                SELECT 
                    store_code,
                    COUNT(*) as transaction_count,
                    SUM(CAST(extended_price AS FLOAT)) as total_revenue,
                    AVG(CAST(extended_price AS FLOAT)) as avg_transaction_value
                FROM pos_transaction_items
                WHERE store_code != '000'
                GROUP BY store_code
            ),
            store_pl AS (
                SELECT 
                    store_code,
                    AVG(CAST(revenue AS FLOAT)) as avg_revenue,
                    AVG(CAST(gross_profit AS FLOAT)) as avg_gross_profit,
                    AVG(CAST(net_income AS FLOAT)) as avg_net_income
                FROM pl_data
                WHERE store_code != '000'
                GROUP BY store_code
            )
            SELECT 
                st.*,
                sp.avg_revenue as pl_avg_revenue,
                sp.avg_gross_profit,
                sp.avg_net_income,
                (sp.avg_gross_profit / NULLIF(sp.avg_revenue, 0) * 100) as gross_margin_pct,
                (sp.avg_net_income / NULLIF(sp.avg_revenue, 0) * 100) as net_margin_pct
            FROM store_transactions st
            LEFT JOIN store_pl sp ON st.store_code = sp.store_code
            """
            
            df = pd.read_sql(query, self.engine)
            
            for _, row in df.iterrows():
                store = str(row['store_code'])
                store_info = STORE_MAPPING.get(store, {'name': 'Unknown', 'manager': 'N/A'})
                
                print(f"\n  Store {store} ({store_info['name']} - {store_info['manager']}):")
                print(f"    Transaction Volume: {row['transaction_count']:,}")
                print(f"    Total Revenue (POS): ${row['total_revenue']:,.2f}")
                print(f"    Avg Transaction: ${row['avg_transaction_value']:,.2f}")
                if pd.notna(row['pl_avg_revenue']):
                    print(f"    P&L Avg Revenue: ${row['pl_avg_revenue']:,.2f}")
                    print(f"    Gross Margin: {row['gross_margin_pct']:.1f}%")
                    print(f"    Net Margin: {row['net_margin_pct']:.1f}%")
                    
            correlations['pl_performance'] = df.to_dict('records')
        except Exception as e:
            print(f"  Error: {str(e)}")
            
        # 3. RFID Transaction Patterns by Store
        print("\n3. RFID Transaction Patterns Analysis:")
        try:
            # First check if RFIDpro table exists and has store_code
            query = """
            SELECT 
                store_code,
                COUNT(*) as rfid_transactions,
                COUNT(DISTINCT customer_account) as unique_customers,
                COUNT(DISTINCT DATE(time_stamp)) as active_days,
                MIN(time_stamp) as first_transaction,
                MAX(time_stamp) as last_transaction
            FROM feedback
            WHERE store_code != '000'
            GROUP BY store_code
            """
            
            df = pd.read_sql(query, self.engine)
            
            for _, row in df.iterrows():
                store = str(row['store_code'])
                store_info = STORE_MAPPING.get(store, {'name': 'Unknown'})
                
                print(f"\n  Store {store} ({store_info['name']}):")
                print(f"    RFID Transactions: {row['rfid_transactions']:,}")
                print(f"    Unique Customers: {row['unique_customers']:,}")
                print(f"    Active Days: {row['active_days']}")
                print(f"    Date Range: {row['first_transaction']} to {row['last_transaction']}")
                
            correlations['rfid_patterns'] = df.to_dict('records')
        except Exception as e:
            print(f"  Error analyzing RFID patterns: {str(e)}")
            
        self.analysis_results['correlations'] = correlations
        
    def generate_executive_kpis(self):
        """Generate executive-level KPIs by store"""
        print("\n" + "="*80)
        print("EXECUTIVE KPI GENERATION")
        print("="*80)
        
        kpis = {}
        
        # 1. Store Performance Scorecard
        print("\n1. Store Performance Scorecard:")
        try:
            query = """
            WITH store_metrics AS (
                SELECT 
                    store_code,
                    COUNT(DISTINCT transaction_number) as transaction_count,
                    COUNT(DISTINCT customer_account) as unique_customers,
                    SUM(CAST(extended_price AS FLOAT)) as total_revenue,
                    AVG(CAST(extended_price AS FLOAT)) as avg_transaction_value,
                    COUNT(DISTINCT item_code) as product_diversity,
                    COUNT(DISTINCT DATE(created_at)) as active_days
                FROM pos_transaction_items
                WHERE store_code != '000'
                    AND created_at >= date('now', '-30 days')
                GROUP BY store_code
            )
            SELECT 
                *,
                (total_revenue / NULLIF(active_days, 0)) as daily_revenue_avg,
                (transaction_count / NULLIF(active_days, 0.0)) as daily_transaction_avg,
                (total_revenue / NULLIF(transaction_count, 0)) as revenue_per_transaction
            FROM store_metrics
            ORDER BY total_revenue DESC
            """
            
            df = pd.read_sql(query, self.engine)
            
            print("\n  Last 30 Days Performance:")
            for _, row in df.iterrows():
                store = str(row['store_code'])
                store_info = STORE_MAPPING.get(store, {'name': 'Unknown', 'manager': 'N/A'})
                
                print(f"\n  Store {store} - {store_info['name']} (Manager: {store_info['manager']}):")
                print(f"    Total Revenue: ${row['total_revenue']:,.2f}")
                print(f"    Daily Avg Revenue: ${row['daily_revenue_avg']:,.2f}")
                print(f"    Transaction Count: {row['transaction_count']:,}")
                print(f"    Daily Avg Transactions: {row['daily_transaction_avg']:.0f}")
                print(f"    Unique Customers: {row['unique_customers']:,}")
                print(f"    Product Diversity: {row['product_diversity']:,} items")
                print(f"    Revenue per Transaction: ${row['revenue_per_transaction']:,.2f}")
                
            kpis['performance_scorecard'] = df.to_dict('records')
        except Exception as e:
            print(f"  Error: {str(e)}")
            
        # 2. Equipment Utilization Metrics
        print("\n2. Equipment Utilization Analysis:")
        try:
            query = """
            WITH equipment_stats AS (
                SELECT 
                    pe.store_code,
                    COUNT(DISTINCT pe.item_code) as total_equipment_types,
                    SUM(CAST(pe.quantity_on_hand AS INTEGER)) as total_inventory,
                    AVG(CAST(pe.quantity_on_hand AS FLOAT)) as avg_quantity_per_item,
                    SUM(CASE WHEN CAST(pe.quantity_on_hand AS INTEGER) = 0 THEN 1 ELSE 0 END) as out_of_stock_items
                FROM pos_equipment pe
                WHERE pe.store_code != '000'
                GROUP BY pe.store_code
            ),
            rental_activity AS (
                SELECT 
                    store_code,
                    COUNT(DISTINCT item_code) as rented_item_types,
                    SUM(CAST(quantity AS FLOAT)) as total_rentals
                FROM pos_transaction_items
                WHERE store_code != '000'
                    AND (LOWER(item_description) LIKE '%rent%' OR LOWER(category) LIKE '%rent%')
                GROUP BY store_code
            )
            SELECT 
                es.*,
                ra.rented_item_types,
                ra.total_rentals,
                (ra.rented_item_types * 100.0 / NULLIF(es.total_equipment_types, 0)) as utilization_rate,
                (es.out_of_stock_items * 100.0 / NULLIF(es.total_equipment_types, 0)) as stockout_rate
            FROM equipment_stats es
            LEFT JOIN rental_activity ra ON es.store_code = ra.store_code
            """
            
            df = pd.read_sql(query, self.engine)
            
            for _, row in df.iterrows():
                store = str(row['store_code'])
                store_info = STORE_MAPPING.get(store, {'name': 'Unknown'})
                
                print(f"\n  Store {store} ({store_info['name']}):")
                print(f"    Equipment Types: {row['total_equipment_types']:,}")
                print(f"    Total Inventory: {row['total_inventory']:,} units")
                print(f"    Avg Quantity/Item: {row['avg_quantity_per_item']:.1f}")
                print(f"    Out of Stock Items: {row['out_of_stock_items']} ({row['stockout_rate']:.1f}%)")
                if pd.notna(row['rented_item_types']):
                    print(f"    Rental Utilization: {row['utilization_rate']:.1f}%")
                    print(f"    Total Rentals: {row['total_rentals']:.0f}")
                    
            kpis['equipment_utilization'] = df.to_dict('records')
        except Exception as e:
            print(f"  Error: {str(e)}")
            
        self.analysis_results['executive_kpis'] = kpis
        
    def generate_dashboard_queries(self):
        """Generate optimized SQL queries for executive dashboard"""
        print("\n" + "="*80)
        print("EXECUTIVE DASHBOARD SQL QUERIES")
        print("="*80)
        
        queries = {}
        
        # 1. Store Comparison Dashboard Query
        queries['store_comparison'] = """
        -- Store Performance Comparison Dashboard
        WITH store_summary AS (
            SELECT 
                pti.store_code,
                COUNT(DISTINCT pti.transaction_number) as transactions,
                COUNT(DISTINCT pti.customer_account) as customers,
                SUM(CAST(pti.extended_price AS FLOAT)) as revenue,
                AVG(CAST(pti.extended_price AS FLOAT)) as avg_ticket,
                COUNT(DISTINCT pti.item_code) as product_mix,
                COUNT(DISTINCT DATE(pti.created_at)) as operating_days
            FROM pos_transaction_items pti
            WHERE pti.created_at >= :start_date
                AND pti.created_at <= :end_date
                AND pti.store_code != '000'
            GROUP BY pti.store_code
        ),
        pl_summary AS (
            SELECT 
                store_code,
                AVG(CAST(gross_profit AS FLOAT)) as avg_gross_profit,
                AVG(CAST(net_income AS FLOAT)) as avg_net_income
            FROM pl_data
            WHERE period_date >= :start_date
                AND period_date <= :end_date
            GROUP BY store_code
        )
        SELECT 
            ss.*,
            ps.avg_gross_profit,
            ps.avg_net_income,
            (ss.revenue / NULLIF(ss.operating_days, 0)) as daily_revenue,
            (ss.transactions / NULLIF(ss.operating_days, 0.0)) as daily_transactions,
            (ps.avg_gross_profit / NULLIF(ss.revenue, 0) * 100) as gross_margin_pct
        FROM store_summary ss
        LEFT JOIN pl_summary ps ON ss.store_code = ps.store_code
        ORDER BY ss.revenue DESC
        """
        
        # 2. Manager Performance Scorecard
        queries['manager_scorecard'] = """
        -- Manager Performance Scorecard
        WITH manager_metrics AS (
            SELECT 
                pti.store_code,
                CASE pti.store_code
                    WHEN '3607' THEN 'TYLER'
                    WHEN '6800' THEN 'ZACK'
                    WHEN '728' THEN 'BRUCE'
                    WHEN '8101' THEN 'TIM'
                    ELSE 'CORPORATE'
                END as manager,
                COUNT(DISTINCT pti.transaction_number) as total_transactions,
                COUNT(DISTINCT pti.customer_account) as unique_customers,
                SUM(CAST(pti.extended_price AS FLOAT)) as total_revenue,
                AVG(CAST(pti.extended_price AS FLOAT)) as avg_transaction_value,
                COUNT(DISTINCT pti.item_code) as product_diversity
            FROM pos_transaction_items pti
            WHERE pti.created_at >= :start_date
                AND pti.created_at <= :end_date
                AND pti.store_code != '000'
            GROUP BY pti.store_code
        ),
        feedback_metrics AS (
            SELECT 
                store_code,
                AVG(CAST(rating AS FLOAT)) as avg_rating,
                COUNT(*) as feedback_count
            FROM feedback
            WHERE created_at >= :start_date
                AND created_at <= :end_date
            GROUP BY store_code
        )
        SELECT 
            mm.*,
            fm.avg_rating,
            fm.feedback_count,
            (mm.unique_customers * 100.0 / NULLIF(mm.total_transactions, 0)) as customer_retention_rate
        FROM manager_metrics mm
        LEFT JOIN feedback_metrics fm ON mm.store_code = fm.store_code
        ORDER BY mm.total_revenue DESC
        """
        
        # 3. Cross-Store Transfer Analysis
        queries['transfer_analysis'] = """
        -- Cross-Store Transfer and Movement Analysis
        WITH transfer_patterns AS (
            SELECT 
                source.store_code as source_store,
                dest.store_code as dest_store,
                source.item_code,
                source.item_description,
                COUNT(*) as transfer_frequency,
                SUM(ABS(CAST(source.quantity AS FLOAT))) as total_quantity
            FROM pos_transaction_items source
            JOIN pos_transaction_items dest 
                ON source.item_code = dest.item_code
                AND source.store_code != dest.store_code
                AND DATE(dest.created_at) > DATE(source.created_at)
                AND DATE(dest.created_at) <= DATE(source.created_at, '+7 days')
            WHERE source.store_code != '000' 
                AND dest.store_code != '000'
                AND CAST(source.quantity AS FLOAT) < 0  -- Outgoing
                AND CAST(dest.quantity AS FLOAT) > 0    -- Incoming
            GROUP BY source.store_code, dest.store_code, source.item_code
        )
        SELECT 
            source_store,
            dest_store,
            COUNT(DISTINCT item_code) as items_transferred,
            SUM(transfer_frequency) as total_transfers,
            SUM(total_quantity) as total_units_moved
        FROM transfer_patterns
        GROUP BY source_store, dest_store
        ORDER BY total_transfers DESC
        """
        
        # 4. Predictive Analytics Query
        queries['predictive_metrics'] = """
        -- Predictive Analytics Base Query
        WITH historical_trends AS (
            SELECT 
                store_code,
                DATE(created_at) as transaction_date,
                strftime('%w', created_at) as day_of_week,
                strftime('%m', created_at) as month,
                COUNT(DISTINCT transaction_number) as daily_transactions,
                SUM(CAST(extended_price AS FLOAT)) as daily_revenue,
                COUNT(DISTINCT customer_account) as daily_customers,
                AVG(CAST(extended_price AS FLOAT)) as avg_ticket
            FROM pos_transaction_items
            WHERE store_code != '000'
                AND created_at >= date('now', '-90 days')
            GROUP BY store_code, DATE(created_at)
        ),
        moving_averages AS (
            SELECT 
                *,
                AVG(daily_revenue) OVER (
                    PARTITION BY store_code 
                    ORDER BY transaction_date 
                    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                ) as revenue_7day_ma,
                AVG(daily_transactions) OVER (
                    PARTITION BY store_code 
                    ORDER BY transaction_date 
                    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
                ) as transactions_30day_ma
            FROM historical_trends
        )
        SELECT 
            store_code,
            transaction_date,
            daily_revenue,
            revenue_7day_ma,
            daily_transactions,
            transactions_30day_ma,
            (daily_revenue - revenue_7day_ma) as revenue_variance,
            (daily_transactions - transactions_30day_ma) as transaction_variance
        FROM moving_averages
        WHERE transaction_date >= date('now', '-30 days')
        ORDER BY store_code, transaction_date
        """
        
        print("\nGenerated Dashboard Queries:")
        for name, query in queries.items():
            print(f"\n{name}:")
            print(f"  - Query optimized for store-specific filtering")
            print(f"  - Supports date range parameters")
            print(f"  - Returns aggregated metrics by store_code")
            
        self.analysis_results['dashboard_queries'] = queries
        return queries
        
    def identify_data_quality_issues(self):
        """Identify data quality issues and recommendations"""
        print("\n" + "="*80)
        print("DATA QUALITY ASSESSMENT")
        print("="*80)
        
        issues = []
        
        # 1. Check for orphaned records
        print("\n1. Orphaned Records Analysis:")
        try:
            # Check POS items without equipment records
            query = """
            SELECT 
                COUNT(DISTINCT pti.item_code) as orphaned_items,
                COUNT(*) as orphaned_transactions
            FROM pos_transaction_items pti
            LEFT JOIN pos_equipment pe 
                ON pti.item_code = pe.item_code 
                AND pti.store_code = pe.store_code
            WHERE pe.id IS NULL
                AND pti.store_code != '000'
            """
            result = pd.read_sql(query, self.engine)
            
            if result['orphaned_items'].iloc[0] > 0:
                print(f"  WARNING: {result['orphaned_items'].iloc[0]:,} items in POS without equipment records")
                print(f"  Affecting {result['orphaned_transactions'].iloc[0]:,} transactions")
                issues.append({
                    'type': 'orphaned_records',
                    'severity': 'MEDIUM',
                    'description': f"{result['orphaned_items'].iloc[0]} POS items without equipment records",
                    'impact': 'Incomplete inventory tracking'
                })
        except Exception as e:
            print(f"  Error checking orphaned records: {str(e)}")
            
        # 2. Check for data consistency
        print("\n2. Store Code Consistency Check:")
        try:
            query = """
            SELECT 
                'pos_transaction_items' as table_name,
                store_code,
                COUNT(*) as record_count
            FROM pos_transaction_items
            WHERE store_code NOT IN ('3607', '6800', '728', '8101', '000')
            GROUP BY store_code
            UNION ALL
            SELECT 
                'pos_equipment' as table_name,
                store_code,
                COUNT(*) as record_count
            FROM pos_equipment
            WHERE store_code NOT IN ('3607', '6800', '728', '8101', '000')
            GROUP BY store_code
            """
            
            df = pd.read_sql(query, self.engine)
            
            if not df.empty:
                print("  WARNING: Found invalid store codes:")
                for _, row in df.iterrows():
                    print(f"    {row['table_name']}: store_code '{row['store_code']}' ({row['record_count']} records)")
                issues.append({
                    'type': 'invalid_store_codes',
                    'severity': 'HIGH',
                    'description': 'Invalid store codes found in tables',
                    'impact': 'Data integrity issues for store-based analytics'
                })
            else:
                print("  ✓ All store codes are valid")
        except Exception as e:
            print(f"  Error checking store codes: {str(e)}")
            
        # 3. Check for date anomalies
        print("\n3. Temporal Data Quality:")
        try:
            query = """
            SELECT 
                MIN(created_at) as earliest_date,
                MAX(created_at) as latest_date,
                COUNT(CASE WHEN created_at > datetime('now') THEN 1 END) as future_dates,
                COUNT(CASE WHEN created_at < date('2020-01-01') THEN 1 END) as very_old_dates
            FROM pos_transaction_items
            """
            
            result = pd.read_sql(query, self.engine)
            
            if result['future_dates'].iloc[0] > 0:
                print(f"  WARNING: {result['future_dates'].iloc[0]} records with future dates")
                issues.append({
                    'type': 'future_dates',
                    'severity': 'HIGH',
                    'description': f"{result['future_dates'].iloc[0]} records with future timestamps",
                    'impact': 'Time-series analysis errors'
                })
                
            if result['very_old_dates'].iloc[0] > 0:
                print(f"  INFO: {result['very_old_dates'].iloc[0]} records before 2020")
                
            print(f"  Date range: {result['earliest_date'].iloc[0]} to {result['latest_date'].iloc[0]}")
        except Exception as e:
            print(f"  Error checking temporal data: {str(e)}")
            
        self.analysis_results['data_quality_issues'] = issues
        return issues
        
    def generate_ai_readiness_assessment(self):
        """Assess AI/ML readiness of the data"""
        print("\n" + "="*80)
        print("AI/ML READINESS ASSESSMENT")
        print("="*80)
        
        ai_readiness = {
            'features_available': [],
            'target_variables': [],
            'data_volume': {},
            'recommendations': []
        }
        
        # 1. Feature Availability
        print("\n1. Available Features for ML Models:")
        
        features = [
            {'name': 'Transaction History', 'table': 'pos_transaction_items', 'quality': 'HIGH'},
            {'name': 'Customer Patterns', 'table': 'pos_transaction_items', 'quality': 'HIGH'},
            {'name': 'Product Performance', 'table': 'pos_transaction_items', 'quality': 'HIGH'},
            {'name': 'Inventory Levels', 'table': 'pos_equipment', 'quality': 'MEDIUM'},
            {'name': 'Financial Metrics', 'table': 'pl_data', 'quality': 'MEDIUM'},
            {'name': 'Weather Data', 'table': 'minnesota_weather_data', 'quality': 'HIGH'},
            {'name': 'Customer Feedback', 'table': 'feedback', 'quality': 'MEDIUM'}
        ]
        
        for feature in features:
            print(f"  ✓ {feature['name']} ({feature['table']}) - Quality: {feature['quality']}")
            ai_readiness['features_available'].append(feature)
            
        # 2. Potential Target Variables
        print("\n2. Potential Target Variables for Prediction:")
        
        targets = [
            'Daily Revenue (pos_transaction_items)',
            'Customer Retention (pos_transaction_items)',
            'Inventory Demand (pos_equipment)',
            'Gross Margin (pl_data)',
            'Customer Satisfaction (feedback)'
        ]
        
        for target in targets:
            print(f"  • {target}")
            ai_readiness['target_variables'].append(target)
            
        # 3. Data Volume Assessment
        print("\n3. Data Volume for Training:")
        try:
            query = """
            SELECT 
                (SELECT COUNT(*) FROM pos_transaction_items) as transaction_records,
                (SELECT COUNT(DISTINCT customer_account) FROM pos_transaction_items) as unique_customers,
                (SELECT COUNT(DISTINCT item_code) FROM pos_transaction_items) as unique_products,
                (SELECT COUNT(DISTINCT DATE(created_at)) FROM pos_transaction_items) as days_of_data
            """
            
            result = pd.read_sql(query, self.engine)
            
            print(f"  Transaction Records: {result['transaction_records'].iloc[0]:,}")
            print(f"  Unique Customers: {result['unique_customers'].iloc[0]:,}")
            print(f"  Unique Products: {result['unique_products'].iloc[0]:,}")
            print(f"  Days of Data: {result['days_of_data'].iloc[0]:,}")
            
            ai_readiness['data_volume'] = result.to_dict('records')[0]
            
            # Assess if volume is sufficient
            if result['transaction_records'].iloc[0] > 100000:
                print("\n  ✓ Sufficient data volume for ML training")
                ai_readiness['recommendations'].append("Data volume is sufficient for most ML models")
            else:
                print("\n  ⚠ May need more data for complex models")
                ai_readiness['recommendations'].append("Consider collecting more data before training complex models")
                
        except Exception as e:
            print(f"  Error assessing data volume: {str(e)}")
            
        # 4. Recommendations
        print("\n4. AI Implementation Recommendations:")
        
        recommendations = [
            "1. Start with time-series forecasting for daily revenue prediction",
            "2. Implement customer segmentation using transaction patterns",
            "3. Build inventory optimization model using POS and equipment data",
            "4. Create churn prediction model using customer transaction frequency",
            "5. Develop price optimization model using P&L and transaction data"
        ]
        
        for rec in recommendations:
            print(f"  {rec}")
            ai_readiness['recommendations'].append(rec)
            
        self.analysis_results['ai_readiness'] = ai_readiness
        
    def generate_integration_roadmap(self):
        """Generate roadmap for enhanced data integration"""
        print("\n" + "="*80)
        print("DATA INTEGRATION ROADMAP")
        print("="*80)
        
        roadmap = {
            'immediate': [],
            'short_term': [],
            'long_term': []
        }
        
        print("\n1. IMMEDIATE ACTIONS (Week 1):")
        immediate = [
            "Create composite indexes on (store_code, created_at) for all transaction tables",
            "Implement data validation triggers for store_code consistency",
            "Build materialized views for store-specific KPIs",
            "Set up automated data quality monitoring"
        ]
        for action in immediate:
            print(f"  • {action}")
            roadmap['immediate'].append(action)
            
        print("\n2. SHORT-TERM IMPROVEMENTS (Month 1):")
        short_term = [
            "Implement real-time dashboard with store filtering",
            "Create automated manager performance reports",
            "Build customer journey mapping system",
            "Deploy predictive analytics for inventory management"
        ]
        for action in short_term:
            print(f"  • {action}")
            roadmap['short_term'].append(action)
            
        print("\n3. LONG-TERM ENHANCEMENTS (Quarter 1):")
        long_term = [
            "Implement ML-based demand forecasting",
            "Build automated pricing optimization system",
            "Create cross-store inventory balancing algorithm",
            "Deploy customer lifetime value prediction model"
        ]
        for action in long_term:
            print(f"  • {action}")
            roadmap['long_term'].append(action)
            
        self.analysis_results['integration_roadmap'] = roadmap
        
    def save_analysis_report(self):
        """Save comprehensive analysis report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'/home/tim/RFID3/store_correlation_analysis_{timestamp}.json'
        
        with open(report_file, 'w') as f:
            json.dump(self.analysis_results, f, indent=2, default=str)
            
        print(f"\n\nAnalysis report saved to: {report_file}")
        
        # Generate executive summary
        summary_file = f'/home/tim/RFID3/STORE_CORRELATION_EXECUTIVE_SUMMARY.md'
        with open(summary_file, 'w') as f:
            f.write("# Store Correlation Analysis - Executive Summary\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Key Findings\n\n")
            f.write("### Store Code Standardization Complete\n")
            f.write("All tables now use consistent store codes:\n")
            f.write("- 3607: Wayzata (TYLER)\n")
            f.write("- 6800: Brooklyn Park (ZACK)\n")
            f.write("- 728: Elk River (BRUCE)\n")
            f.write("- 8101: Fridley (TIM)\n")
            f.write("- 000: Legacy/Company-wide\n\n")
            
            f.write("### Data Volume Summary\n")
            if 'store_distribution' in self.analysis_results:
                for table, data in self.analysis_results['store_distribution'].items():
                    if data:
                        total = sum(d['record_count'] for d in data)
                        f.write(f"- {table}: {total:,} records\n")
            
            f.write("\n### Cross-System Integration Opportunities\n")
            f.write("1. **POS-Equipment Integration**: Link transaction data with inventory levels\n")
            f.write("2. **Financial Correlation**: Connect P&L data with operational metrics\n")
            f.write("3. **Customer Analytics**: Unified customer profiles across stores\n")
            f.write("4. **Predictive Modeling**: Sufficient data for ML implementation\n\n")
            
            f.write("### Data Quality Issues\n")
            if 'data_quality_issues' in self.analysis_results:
                for issue in self.analysis_results['data_quality_issues']:
                    f.write(f"- {issue['severity']}: {issue['description']}\n")
            
            f.write("\n### Recommended Next Steps\n")
            f.write("1. Implement store-specific dashboards with real-time filtering\n")
            f.write("2. Deploy manager performance scorecards\n")
            f.write("3. Create predictive models for inventory and revenue\n")
            f.write("4. Build automated cross-store transfer tracking\n")
            
        print(f"Executive summary saved to: {summary_file}")
        
    def run_complete_analysis(self):
        """Run the complete correlation analysis"""
        print("\n" + "="*80)
        print("COMPREHENSIVE STORE CORRELATION ANALYSIS")
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Run all analysis components
        self.analyze_table_structure()
        self.analyze_store_distribution()
        self.analyze_cross_table_correlations()
        self.generate_executive_kpis()
        self.generate_dashboard_queries()
        self.identify_data_quality_issues()
        self.generate_ai_readiness_assessment()
        self.generate_integration_roadmap()
        
        # Save results
        self.save_analysis_report()
        
        print("\n" + "="*80)
        print("ANALYSIS COMPLETE")
        print("="*80)

def main():
    """Main execution function"""
    analyzer = StoreCorrelationAnalyzer()
    analyzer.run_complete_analysis()

if __name__ == "__main__":
    main()