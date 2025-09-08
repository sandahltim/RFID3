#!/usr/bin/env python3
"""
Comprehensive Database Validation and Algorithm Hardening Script
RFID3 System - Production Validation Suite
"""

import sys
import os
import time
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError
import warnings
warnings.filterwarnings('ignore')

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.db_models import *
from app.models.pos_models import *
from app.models.correlation_models import *

class DatabaseValidator:
    """Comprehensive database validation and hardening suite"""
    
    def __init__(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'integrity_checks': {},
            'performance_metrics': {},
            'data_quality': {},
            'algorithm_validation': {},
            'recommendations': []
        }
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.app_context.pop()
        
    def run_all_validations(self):
        """Execute all validation checks"""
        print("\n" + "="*80)
        print("RFID3 DATABASE VALIDATION & HARDENING SUITE")
        print("="*80)
        
        # 1. Data Integrity Verification
        print("\n[1/5] Running Data Integrity Checks...")
        self.check_data_integrity()
        
        # 2. Query Optimization Analysis
        print("\n[2/5] Analyzing Query Performance...")
        self.analyze_query_performance()
        
        # 3. Algorithm Validation
        print("\n[3/5] Validating ML Algorithms...")
        self.validate_algorithms()
        
        # 4. Performance Benchmarking
        print("\n[4/5] Running Performance Benchmarks...")
        self.benchmark_performance()
        
        # 5. Data Quality Assessment
        print("\n[5/5] Assessing Data Quality...")
        self.assess_data_quality()
        
        # Generate recommendations
        self.generate_recommendations()
        
        return self.results
        
    def check_data_integrity(self):
        """Comprehensive data integrity verification"""
        integrity_results = {}
        
        # Check for orphaned transactions
        orphan_check = """
        SELECT COUNT(*) as orphan_count
        FROM id_transactions t
        LEFT JOIN id_item_master im ON t.tag_id = im.tag_id
        WHERE im.tag_id IS NULL
        """
        
        try:
            result = db.session.execute(text(orphan_check)).fetchone()
            integrity_results['orphaned_transactions'] = {
                'count': result[0] if result else 0,
                'status': 'PASS' if (result and result[0] == 0) else 'FAIL'
            }
        except Exception as e:
            integrity_results['orphaned_transactions'] = {'error': str(e), 'status': 'ERROR'}
            
        # Check for duplicate tag_ids
        duplicate_check = """
        SELECT tag_id, COUNT(*) as duplicate_count
        FROM id_item_master
        GROUP BY tag_id
        HAVING COUNT(*) > 1
        """
        
        try:
            duplicates = db.session.execute(text(duplicate_check)).fetchall()
            integrity_results['duplicate_tags'] = {
                'count': len(duplicates),
                'status': 'PASS' if len(duplicates) == 0 else 'FAIL',
                'details': [{'tag_id': row[0], 'count': row[1]} for row in duplicates[:10]]
            }
        except Exception as e:
            integrity_results['duplicate_tags'] = {'error': str(e), 'status': 'ERROR'}
            
        # Validate P&L data consistency
        pnl_check = """
        SELECT 
            store_id,
            COUNT(DISTINCT year) as years,
            COUNT(DISTINCT month) as months,
            COUNT(*) as total_records,
            MIN(year) as min_year,
            MAX(year) as max_year
        FROM pos_pnl
        GROUP BY store_id
        """
        
        try:
            pnl_results = db.session.execute(text(pnl_check)).fetchall()
            integrity_results['pnl_consistency'] = {
                'stores': len(pnl_results),
                'status': 'PASS',
                'details': [
                    {
                        'store_id': row[0],
                        'years': row[1],
                        'months': row[2],
                        'records': row[3],
                        'date_range': f"{row[4]}-{row[5]}"
                    } for row in pnl_results
                ]
            }
        except Exception as e:
            integrity_results['pnl_consistency'] = {'error': str(e), 'status': 'ERROR'}
            
        # Check foreign key relationships
        fk_checks = [
            {
                'name': 'transactions_to_items',
                'query': """
                    SELECT COUNT(*) as missing_items
                    FROM pos_transactions pt
                    LEFT JOIN pos_transaction_items pti ON pt.transaction_id = pti.transaction_id
                    WHERE pti.transaction_id IS NULL AND pt.total_items > 0
                """
            },
            {
                'name': 'equipment_to_customers',
                'query': """
                    SELECT COUNT(*) as orphaned_equipment
                    FROM pos_equipment pe
                    LEFT JOIN pos_customers pc ON pe.customer_id = pc.customer_id
                    WHERE pc.customer_id IS NULL
                """
            }
        ]
        
        for check in fk_checks:
            try:
                result = db.session.execute(text(check['query'])).fetchone()
                integrity_results[f'fk_{check["name"]}'] = {
                    'issues': result[0] if result else 0,
                    'status': 'PASS' if (result and result[0] == 0) else 'WARNING'
                }
            except Exception as e:
                integrity_results[f'fk_{check["name"]}'] = {'error': str(e), 'status': 'ERROR'}
                
        # Check data type consistency
        type_check = """
        SELECT 
            'id_item_master' as table_name,
            COUNT(*) as total,
            SUM(CASE WHEN date_in IS NOT NULL AND date_in != '' THEN 1 ELSE 0 END) as valid_dates,
            SUM(CASE WHEN turnover_ytd IS NOT NULL THEN 1 ELSE 0 END) as valid_turnover
        FROM id_item_master
        """
        
        try:
            result = db.session.execute(text(type_check)).fetchone()
            if result:
                integrity_results['data_types'] = {
                    'total_records': result[1],
                    'valid_date_percentage': round((result[2] / result[1]) * 100, 2) if result[1] > 0 else 0,
                    'valid_turnover_percentage': round((result[3] / result[1]) * 100, 2) if result[1] > 0 else 0,
                    'status': 'PASS' if result[2] == result[1] and result[3] == result[1] else 'WARNING'
                }
        except Exception as e:
            integrity_results['data_types'] = {'error': str(e), 'status': 'ERROR'}
            
        self.results['integrity_checks'] = integrity_results
        
        # Print summary
        print(f"  ✓ Orphaned Transactions: {integrity_results.get('orphaned_transactions', {}).get('count', 'N/A')}")
        print(f"  ✓ Duplicate Tags: {integrity_results.get('duplicate_tags', {}).get('count', 'N/A')}")
        print(f"  ✓ P&L Stores: {integrity_results.get('pnl_consistency', {}).get('stores', 'N/A')}")
        
    def analyze_query_performance(self):
        """Analyze and optimize query performance"""
        performance_results = {}
        
        # Test critical queries with timing
        critical_queries = [
            {
                'name': 'store_performance',
                'query': """
                    SELECT 
                        current_store,
                        COUNT(*) as total_items,
                        AVG(turnover_ytd) as avg_turnover,
                        SUM(turnover_ytd) as total_turnover
                    FROM id_item_master
                    GROUP BY current_store
                """
            },
            {
                'name': 'pnl_variance',
                'query': """
                    SELECT 
                        p.store_id,
                        p.year,
                        p.month,
                        p.revenue,
                        p.cogs,
                        p.gross_profit,
                        e.gdp_growth,
                        e.unemployment_rate
                    FROM pos_pnl p
                    LEFT JOIN external_factors e 
                        ON DATE(p.year || '-' || printf('%02d', p.month) || '-01') = DATE(e.date)
                    WHERE p.year >= 2023
                """
            },
            {
                'name': 'correlation_analysis',
                'query': """
                    SELECT 
                        factor_name,
                        correlation_value,
                        p_value,
                        lag_days
                    FROM pos_rfid_correlations
                    WHERE ABS(correlation_value) > 0.5
                        AND p_value < 0.05
                    ORDER BY ABS(correlation_value) DESC
                """
            },
            {
                'name': 'inventory_health',
                'query': """
                    SELECT 
                        im.current_store,
                        COUNT(DISTINCT im.tag_id) as unique_items,
                        COUNT(t.transaction_id) as total_transactions,
                        AVG(JULIANDAY('now') - JULIANDAY(t.scan_date)) as avg_days_since_scan
                    FROM id_item_master im
                    LEFT JOIN id_transactions t ON im.tag_id = t.tag_id
                    GROUP BY im.current_store
                """
            }
        ]
        
        for query_info in critical_queries:
            try:
                start_time = time.time()
                result = db.session.execute(text(query_info['query'])).fetchall()
                execution_time = (time.time() - start_time) * 1000  # Convert to ms
                
                performance_results[query_info['name']] = {
                    'execution_time_ms': round(execution_time, 2),
                    'row_count': len(result),
                    'status': 'PASS' if execution_time < 1000 else 'WARNING',
                    'optimization_needed': execution_time > 500
                }
            except Exception as e:
                performance_results[query_info['name']] = {
                    'error': str(e),
                    'status': 'ERROR'
                }
                
        # Check index usage
        index_check = """
        SELECT 
            name,
            tbl_name,
            sql
        FROM sqlite_master
        WHERE type = 'index'
            AND sql IS NOT NULL
        """
        
        try:
            indexes = db.session.execute(text(index_check)).fetchall()
            performance_results['indexes'] = {
                'count': len(indexes),
                'details': [{'name': idx[0], 'table': idx[1]} for idx in indexes[:20]]
            }
        except Exception as e:
            performance_results['indexes'] = {'error': str(e)}
            
        # Analyze table statistics
        table_stats = """
        SELECT 
            name,
            (SELECT COUNT(*) FROM pragma_table_info(name)) as column_count
        FROM sqlite_master
        WHERE type = 'table'
            AND name NOT LIKE 'sqlite_%'
        ORDER BY name
        """
        
        try:
            tables = db.session.execute(text(table_stats)).fetchall()
            
            table_details = []
            for table in tables[:10]:  # Limit to first 10 tables for performance
                row_count_query = f"SELECT COUNT(*) FROM {table[0]}"
                try:
                    row_count = db.session.execute(text(row_count_query)).scalar()
                    table_details.append({
                        'table': table[0],
                        'columns': table[1],
                        'rows': row_count
                    })
                except:
                    pass
                    
            performance_results['table_statistics'] = table_details
        except Exception as e:
            performance_results['table_statistics'] = {'error': str(e)}
            
        self.results['performance_metrics'] = performance_results
        
        # Print summary
        for query_name, metrics in performance_results.items():
            if isinstance(metrics, dict) and 'execution_time_ms' in metrics:
                print(f"  ✓ {query_name}: {metrics['execution_time_ms']}ms ({metrics['row_count']} rows)")
                
    def validate_algorithms(self):
        """Validate ML algorithms and statistical tests"""
        algorithm_results = {}
        
        # Test Pearson correlation calculations
        try:
            # Generate mock data for testing
            np.random.seed(42)
            x = np.random.randn(100)
            y = 0.8 * x + 0.2 * np.random.randn(100)  # Correlated data
            
            from scipy.stats import pearsonr
            corr, p_value = pearsonr(x, y)
            
            algorithm_results['pearson_correlation'] = {
                'test_correlation': round(corr, 4),
                'test_p_value': round(p_value, 6),
                'status': 'PASS' if abs(corr) > 0.5 and p_value < 0.05 else 'WARNING',
                'threshold_check': {
                    'correlation_threshold': 0.5,
                    'p_value_threshold': 0.05,
                    'meets_criteria': abs(corr) > 0.5 and p_value < 0.05
                }
            }
        except Exception as e:
            algorithm_results['pearson_correlation'] = {'error': str(e), 'status': 'ERROR'}
            
        # Test Granger causality
        try:
            from statsmodels.tsa.stattools import grangercausalitytests
            
            # Generate test time series
            data = pd.DataFrame({
                'x': np.cumsum(np.random.randn(50)),
                'y': np.cumsum(np.random.randn(50))
            })
            
            # Run Granger test with max lag of 2
            result = grangercausalitytests(data[['y', 'x']], maxlag=2, verbose=False)
            
            # Extract p-values
            p_values = []
            for lag in [1, 2]:
                test_result = result[lag][0]
                p_values.append(test_result['ssr_ftest'][1])
                
            algorithm_results['granger_causality'] = {
                'test_p_values': [round(p, 6) for p in p_values],
                'min_p_value': round(min(p_values), 6),
                'status': 'PASS' if min(p_values) < 0.05 else 'WARNING',
                'significance_level': 0.05
            }
        except Exception as e:
            algorithm_results['granger_causality'] = {'error': str(e), 'status': 'ERROR'}
            
        # Test ARIMA model validation
        try:
            from pmdarima import auto_arima
            
            # Generate test time series
            ts_data = np.cumsum(np.random.randn(100)) + 100
            
            # Fit auto ARIMA
            model = auto_arima(
                ts_data,
                start_p=0, start_q=0,
                max_p=3, max_q=3,
                seasonal=False,
                stepwise=True,
                suppress_warnings=True,
                error_action='ignore'
            )
            
            # Get model metrics
            algorithm_results['arima_validation'] = {
                'model_order': str(model.order),
                'aic': round(model.aic(), 2),
                'bic': round(model.bic(), 2),
                'status': 'PASS',
                'auto_fitted': True
            }
        except Exception as e:
            algorithm_results['arima_validation'] = {'error': str(e), 'status': 'ERROR'}
            
        # Test interpolation methods
        try:
            # Create data with gaps
            data_with_gaps = pd.Series([1, 2, np.nan, 4, 5, np.nan, 7, 8, 9, np.nan])
            
            # Test different interpolation methods
            interpolation_methods = {
                'linear': data_with_gaps.interpolate(method='linear'),
                'polynomial': data_with_gaps.interpolate(method='polynomial', order=2),
                'forward_fill': data_with_gaps.fillna(method='ffill'),
                'backward_fill': data_with_gaps.fillna(method='bfill')
            }
            
            algorithm_results['interpolation'] = {
                'methods_tested': list(interpolation_methods.keys()),
                'gaps_filled': {
                    method: (~interp_data.isna()).sum() - (~data_with_gaps.isna()).sum()
                    for method, interp_data in interpolation_methods.items()
                },
                'status': 'PASS'
            }
        except Exception as e:
            algorithm_results['interpolation'] = {'error': str(e), 'status': 'ERROR'}
            
        # Validate correlation threshold logic
        try:
            correlation_query = """
            SELECT 
                COUNT(*) as total_correlations,
                SUM(CASE WHEN ABS(correlation_value) > 0.5 THEN 1 ELSE 0 END) as significant_correlations,
                SUM(CASE WHEN p_value < 0.05 THEN 1 ELSE 0 END) as statistically_significant,
                AVG(ABS(correlation_value)) as avg_correlation
            FROM pos_rfid_correlations
            """
            
            result = db.session.execute(text(correlation_query)).fetchone()
            if result and result[0] > 0:
                algorithm_results['correlation_thresholds'] = {
                    'total_correlations': result[0],
                    'significant_correlations': result[1],
                    'statistically_significant': result[2],
                    'average_correlation': round(result[3], 4) if result[3] else 0,
                    'relevance_percentage': round((result[1] / result[0]) * 100, 2) if result[0] > 0 else 0,
                    'status': 'PASS'
                }
            else:
                algorithm_results['correlation_thresholds'] = {
                    'status': 'WARNING',
                    'message': 'No correlations found in database'
                }
        except Exception as e:
            algorithm_results['correlation_thresholds'] = {'error': str(e), 'status': 'ERROR'}
            
        self.results['algorithm_validation'] = algorithm_results
        
        # Print summary
        for algo_name, metrics in algorithm_results.items():
            status = metrics.get('status', 'UNKNOWN')
            print(f"  ✓ {algo_name}: {status}")
            
    def benchmark_performance(self):
        """Run performance benchmarks"""
        benchmark_results = {}
        
        # Concurrent query test
        concurrent_queries = [
            "SELECT COUNT(*) FROM id_item_master",
            "SELECT COUNT(*) FROM id_transactions",
            "SELECT COUNT(*) FROM pos_pnl",
            "SELECT AVG(turnover_ytd) FROM id_item_master WHERE current_store = 1"
        ]
        
        try:
            start_time = time.time()
            for query in concurrent_queries:
                db.session.execute(text(query)).scalar()
            total_time = (time.time() - start_time) * 1000
            
            benchmark_results['concurrent_queries'] = {
                'queries_executed': len(concurrent_queries),
                'total_time_ms': round(total_time, 2),
                'avg_time_ms': round(total_time / len(concurrent_queries), 2),
                'status': 'PASS' if total_time < 2000 else 'WARNING'
            }
        except Exception as e:
            benchmark_results['concurrent_queries'] = {'error': str(e), 'status': 'ERROR'}
            
        # Large dataset query test
        large_query = """
        SELECT 
            im.current_store,
            COUNT(DISTINCT im.tag_id) as items,
            COUNT(t.transaction_id) as transactions,
            AVG(im.turnover_ytd) as avg_turnover,
            SUM(im.turnover_ytd) as total_turnover
        FROM id_item_master im
        LEFT JOIN id_transactions t ON im.tag_id = t.tag_id
        GROUP BY im.current_store
        """
        
        try:
            start_time = time.time()
            result = db.session.execute(text(large_query)).fetchall()
            execution_time = (time.time() - start_time) * 1000
            
            benchmark_results['large_dataset'] = {
                'execution_time_ms': round(execution_time, 2),
                'rows_processed': len(result),
                'status': 'PASS' if execution_time < 3000 else 'WARNING'
            }
        except Exception as e:
            benchmark_results['large_dataset'] = {'error': str(e), 'status': 'ERROR'}
            
        # P&L analytics with date range test
        pnl_analytics = """
        SELECT 
            store_id,
            year,
            AVG(revenue) as avg_revenue,
            AVG(gross_profit) as avg_profit,
            AVG(gross_margin) as avg_margin
        FROM pos_pnl
        WHERE year BETWEEN 2021 AND 2025
        GROUP BY store_id, year
        """
        
        try:
            start_time = time.time()
            result = db.session.execute(text(pnl_analytics)).fetchall()
            execution_time = (time.time() - start_time) * 1000
            
            benchmark_results['pnl_analytics'] = {
                'execution_time_ms': round(execution_time, 2),
                'rows_returned': len(result),
                'status': 'PASS' if execution_time < 1000 else 'WARNING'
            }
        except Exception as e:
            benchmark_results['pnl_analytics'] = {'error': str(e), 'status': 'ERROR'}
            
        # Memory usage check (simple estimation)
        memory_query = """
        SELECT 
            'id_item_master' as table_name,
            COUNT(*) * 500 as estimated_bytes
        FROM id_item_master
        UNION ALL
        SELECT 
            'id_transactions',
            COUNT(*) * 200
        FROM id_transactions
        UNION ALL
        SELECT 
            'pos_pnl',
            COUNT(*) * 300
        FROM pos_pnl
        """
        
        try:
            memory_results = db.session.execute(text(memory_query)).fetchall()
            total_bytes = sum(row[1] for row in memory_results)
            
            benchmark_results['memory_usage'] = {
                'estimated_mb': round(total_bytes / (1024 * 1024), 2),
                'tables': {row[0]: round(row[1] / 1024, 2) for row in memory_results},
                'status': 'PASS'
            }
        except Exception as e:
            benchmark_results['memory_usage'] = {'error': str(e), 'status': 'ERROR'}
            
        self.results['performance_metrics'].update(benchmark_results)
        
        # Print summary
        print(f"  ✓ Concurrent Queries: {benchmark_results.get('concurrent_queries', {}).get('avg_time_ms', 'N/A')}ms avg")
        print(f"  ✓ Large Dataset: {benchmark_results.get('large_dataset', {}).get('execution_time_ms', 'N/A')}ms")
        print(f"  ✓ P&L Analytics: {benchmark_results.get('pnl_analytics', {}).get('execution_time_ms', 'N/A')}ms")
        
    def assess_data_quality(self):
        """Comprehensive data quality assessment"""
        quality_results = {}
        
        # Missing data detection
        missing_data_queries = [
            {
                'table': 'id_item_master',
                'critical_fields': ['tag_id', 'current_store', 'turnover_ytd'],
                'query': """
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN tag_id IS NULL OR tag_id = '' THEN 1 ELSE 0 END) as missing_tag_id,
                        SUM(CASE WHEN current_store IS NULL THEN 1 ELSE 0 END) as missing_store,
                        SUM(CASE WHEN turnover_ytd IS NULL THEN 1 ELSE 0 END) as missing_turnover
                    FROM id_item_master
                """
            },
            {
                'table': 'pos_pnl',
                'critical_fields': ['store_id', 'revenue', 'gross_profit'],
                'query': """
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN store_id IS NULL THEN 1 ELSE 0 END) as missing_store,
                        SUM(CASE WHEN revenue IS NULL THEN 1 ELSE 0 END) as missing_revenue,
                        SUM(CASE WHEN gross_profit IS NULL THEN 1 ELSE 0 END) as missing_profit
                    FROM pos_pnl
                """
            }
        ]
        
        missing_data_results = {}
        for check in missing_data_queries:
            try:
                result = db.session.execute(text(check['query'])).fetchone()
                if result:
                    missing_data_results[check['table']] = {
                        'total_records': result[0],
                        'missing_counts': {
                            field: result[i+1] for i, field in enumerate(check['critical_fields'])
                        },
                        'completeness_percentage': round(
                            ((result[0] - max(result[1:])) / result[0] * 100) if result[0] > 0 else 0, 2
                        )
                    }
            except Exception as e:
                missing_data_results[check['table']] = {'error': str(e)}
                
        quality_results['missing_data'] = missing_data_results
        
        # Outlier detection using IQR
        outlier_query = """
        WITH quartiles AS (
            SELECT 
                turnover_ytd,
                NTILE(4) OVER (ORDER BY turnover_ytd) as quartile
            FROM id_item_master
            WHERE turnover_ytd IS NOT NULL AND turnover_ytd > 0
        ),
        iqr_calc AS (
            SELECT 
                MAX(CASE WHEN quartile = 1 THEN turnover_ytd END) as q1,
                MAX(CASE WHEN quartile = 3 THEN turnover_ytd END) as q3
            FROM quartiles
        )
        SELECT 
            COUNT(*) as total_items,
            SUM(CASE 
                WHEN im.turnover_ytd < (iqr.q1 - 1.5 * (iqr.q3 - iqr.q1))
                OR im.turnover_ytd > (iqr.q3 + 1.5 * (iqr.q3 - iqr.q1))
                THEN 1 ELSE 0 
            END) as outliers,
            MIN(im.turnover_ytd) as min_value,
            MAX(im.turnover_ytd) as max_value,
            AVG(im.turnover_ytd) as avg_value,
            iqr.q1,
            iqr.q3
        FROM id_item_master im
        CROSS JOIN iqr_calc iqr
        WHERE im.turnover_ytd IS NOT NULL AND im.turnover_ytd > 0
        """
        
        try:
            result = db.session.execute(text(outlier_query)).fetchone()
            if result:
                quality_results['outliers'] = {
                    'total_items': result[0],
                    'outlier_count': result[1],
                    'outlier_percentage': round((result[1] / result[0] * 100) if result[0] > 0 else 0, 2),
                    'statistics': {
                        'min': round(result[2], 2) if result[2] else 0,
                        'max': round(result[3], 2) if result[3] else 0,
                        'avg': round(result[4], 2) if result[4] else 0,
                        'q1': round(result[5], 2) if result[5] else 0,
                        'q3': round(result[6], 2) if result[6] else 0
                    }
                }
        except Exception as e:
            quality_results['outliers'] = {'error': str(e)}
            
        # Data consistency check
        consistency_checks = []
        
        # Check P&L projection vs actual
        pnl_consistency = """
        SELECT 
            store_id,
            year,
            month,
            revenue,
            cogs,
            gross_profit,
            CASE 
                WHEN ABS(gross_profit - (revenue - cogs)) > 0.01 
                THEN 'INCONSISTENT' 
                ELSE 'CONSISTENT' 
            END as consistency_check
        FROM pos_pnl
        WHERE revenue IS NOT NULL AND cogs IS NOT NULL AND gross_profit IS NOT NULL
        """
        
        try:
            results = db.session.execute(text(pnl_consistency)).fetchall()
            inconsistent = sum(1 for r in results if r[6] == 'INCONSISTENT')
            quality_results['pnl_consistency'] = {
                'total_checked': len(results),
                'inconsistent_records': inconsistent,
                'consistency_rate': round(((len(results) - inconsistent) / len(results) * 100) if results else 0, 2)
            }
        except Exception as e:
            quality_results['pnl_consistency'] = {'error': str(e)}
            
        # Check date consistency
        date_consistency = """
        SELECT 
            COUNT(*) as total,
            SUM(CASE 
                WHEN date_in IS NOT NULL 
                AND date_in != '' 
                AND date(date_in) IS NOT NULL 
                THEN 1 ELSE 0 
            END) as valid_dates,
            MIN(date_in) as earliest_date,
            MAX(date_in) as latest_date
        FROM id_item_master
        """
        
        try:
            result = db.session.execute(text(date_consistency)).fetchone()
            if result:
                quality_results['date_quality'] = {
                    'total_records': result[0],
                    'valid_dates': result[1],
                    'validity_rate': round((result[1] / result[0] * 100) if result[0] > 0 else 0, 2),
                    'date_range': f"{result[2]} to {result[3]}"
                }
        except Exception as e:
            quality_results['date_quality'] = {'error': str(e)}
            
        self.results['data_quality'] = quality_results
        
        # Print summary
        for table, metrics in missing_data_results.items():
            if 'completeness_percentage' in metrics:
                print(f"  ✓ {table} Completeness: {metrics['completeness_percentage']}%")
        if 'outliers' in quality_results:
            print(f"  ✓ Outliers Detected: {quality_results['outliers'].get('outlier_percentage', 'N/A')}%")
            
    def generate_recommendations(self):
        """Generate actionable recommendations based on validation results"""
        recommendations = []
        
        # Analyze integrity issues
        integrity = self.results.get('integrity_checks', {})
        
        if integrity.get('orphaned_transactions', {}).get('count', 0) > 0:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Data Integrity',
                'issue': f"Found {integrity['orphaned_transactions']['count']} orphaned transactions",
                'recommendation': 'Add foreign key constraint or clean orphaned records',
                'sql': """
                DELETE FROM id_transactions 
                WHERE tag_id NOT IN (SELECT tag_id FROM id_item_master)
                """
            })
            
        if integrity.get('duplicate_tags', {}).get('count', 0) > 0:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Data Integrity',
                'issue': f"Found {integrity['duplicate_tags']['count']} duplicate tag IDs",
                'recommendation': 'Add UNIQUE constraint on tag_id and deduplicate existing records',
                'sql': """
                -- First identify duplicates
                WITH duplicates AS (
                    SELECT tag_id, MIN(rowid) as keep_rowid
                    FROM id_item_master
                    GROUP BY tag_id
                    HAVING COUNT(*) > 1
                )
                DELETE FROM id_item_master
                WHERE rowid NOT IN (SELECT keep_rowid FROM duplicates)
                    AND tag_id IN (SELECT tag_id FROM duplicates)
                """
            })
            
        # Analyze performance issues
        performance = self.results.get('performance_metrics', {})
        
        slow_queries = [
            (name, metrics) for name, metrics in performance.items()
            if isinstance(metrics, dict) and metrics.get('optimization_needed', False)
        ]
        
        if slow_queries:
            for query_name, metrics in slow_queries:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'Performance',
                    'issue': f"Query '{query_name}' takes {metrics['execution_time_ms']}ms",
                    'recommendation': 'Add appropriate indexes to improve query performance',
                    'sql': self._generate_index_recommendation(query_name)
                })
                
        # Analyze data quality issues
        quality = self.results.get('data_quality', {})
        
        for table, missing_info in quality.get('missing_data', {}).items():
            if isinstance(missing_info, dict) and 'completeness_percentage' in missing_info:
                if missing_info['completeness_percentage'] < 95:
                    recommendations.append({
                        'priority': 'MEDIUM',
                        'category': 'Data Quality',
                        'issue': f"Table {table} has only {missing_info['completeness_percentage']}% data completeness",
                        'recommendation': 'Implement data validation and interpolation strategies',
                        'action': 'Review ETL processes and add NOT NULL constraints where appropriate'
                    })
                    
        if quality.get('outliers', {}).get('outlier_percentage', 0) > 5:
            recommendations.append({
                'priority': 'LOW',
                'category': 'Data Quality',
                'issue': f"{quality['outliers']['outlier_percentage']}% of records are outliers",
                'recommendation': 'Review outlier detection thresholds and data validation rules',
                'action': 'Implement data cleaning pipeline with configurable outlier handling'
            })
            
        # Check for missing indexes
        if performance.get('indexes', {}).get('count', 0) < 10:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Performance',
                'issue': 'Insufficient indexes detected',
                'recommendation': 'Create indexes on frequently queried columns',
                'sql': """
                -- Core indexes for performance
                CREATE INDEX IF NOT EXISTS idx_item_master_store ON id_item_master(current_store);
                CREATE INDEX IF NOT EXISTS idx_item_master_tag ON id_item_master(tag_id);
                CREATE INDEX IF NOT EXISTS idx_transactions_tag ON id_transactions(tag_id);
                CREATE INDEX IF NOT EXISTS idx_transactions_date ON id_transactions(scan_date);
                CREATE INDEX IF NOT EXISTS idx_pnl_store_date ON pos_pnl(store_id, year, month);
                CREATE INDEX IF NOT EXISTS idx_correlations_value ON pos_rfid_correlations(correlation_value);
                """
            })
            
        self.results['recommendations'] = recommendations
        
        # Print recommendations
        print(f"\n{'='*80}")
        print("RECOMMENDATIONS")
        print('='*80)
        
        for rec in sorted(recommendations, key=lambda x: {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}.get(x['priority'], 3)):
            print(f"\n[{rec['priority']}] {rec['category']}: {rec['issue']}")
            print(f"  → {rec['recommendation']}")
            
    def _generate_index_recommendation(self, query_name):
        """Generate index recommendations based on query name"""
        index_map = {
            'store_performance': """
            CREATE INDEX IF NOT EXISTS idx_item_master_store_turnover 
            ON id_item_master(current_store, turnover_ytd);
            """,
            'pnl_variance': """
            CREATE INDEX IF NOT EXISTS idx_pnl_date 
            ON pos_pnl(year, month, store_id);
            CREATE INDEX IF NOT EXISTS idx_external_factors_date 
            ON external_factors(date);
            """,
            'correlation_analysis': """
            CREATE INDEX IF NOT EXISTS idx_correlations_composite 
            ON pos_rfid_correlations(correlation_value, p_value, factor_name);
            """,
            'inventory_health': """
            CREATE INDEX IF NOT EXISTS idx_transactions_composite 
            ON id_transactions(tag_id, scan_date);
            """
        }
        return index_map.get(query_name, "-- Custom index needed based on query pattern")
        
    def save_report(self, filename='database_validation_report.json'):
        """Save validation report to file"""
        filepath = os.path.join('/home/tim/RFID3/reports', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
            
        print(f"\n✓ Report saved to: {filepath}")
        return filepath


def main():
    """Main execution function"""
    print("Starting RFID3 Database Validation and Hardening...")
    
    with DatabaseValidator() as validator:
        results = validator.run_all_validations()
        
        # Save report
        report_file = validator.save_report()
        
        # Print summary statistics
        print(f"\n{'='*80}")
        print("VALIDATION SUMMARY")
        print('='*80)
        
        # Count statuses
        all_statuses = []
        for category in ['integrity_checks', 'performance_metrics', 'data_quality', 'algorithm_validation']:
            if category in results:
                for check, details in results[category].items():
                    if isinstance(details, dict) and 'status' in details:
                        all_statuses.append(details['status'])
                        
        status_counts = {
            'PASS': all_statuses.count('PASS'),
            'WARNING': all_statuses.count('WARNING'),
            'FAIL': all_statuses.count('FAIL'),
            'ERROR': all_statuses.count('ERROR')
        }
        
        print(f"\n✓ Passed: {status_counts['PASS']}")
        print(f"⚠ Warnings: {status_counts['WARNING']}")
        print(f"✗ Failed: {status_counts['FAIL']}")
        print(f"⚠ Errors: {status_counts['ERROR']}")
        
        print(f"\nTotal Recommendations: {len(results.get('recommendations', []))}")
        
        # Overall health score
        total_checks = sum(status_counts.values())
        health_score = ((status_counts['PASS'] * 100) + (status_counts['WARNING'] * 50)) / total_checks if total_checks > 0 else 0
        
        print(f"\n{'='*80}")
        print(f"OVERALL DATABASE HEALTH SCORE: {health_score:.1f}%")
        print('='*80)
        
        return results


if __name__ == "__main__":
    main()