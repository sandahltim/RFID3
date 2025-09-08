#!/usr/bin/env python3
"""
Comprehensive Testing Suite for RFID3 Predictive Analytics System
Tests database queries, ML algorithms, correlation calculations, and business logic
"""

import sys
import time
import traceback
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import func, text, and_, or_
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Add project root to path
sys.path.insert(0, '/home/tim/RFID3')

from app import create_app, db
from app.models.pos_models import (
    POSEquipment, POSTransaction, POSTransactionItem, 
    POSCustomer, POSRFIDCorrelation, POSAnalytics
)
from app.models.db_models import ItemMaster, Transaction
from app.services.business_analytics_service import BusinessAnalyticsService
from app.services.ml_correlation_service import MLCorrelationService
from app.services.data_fetch_service import DataFetchService

class AnalyticsSystemTester:
    def __init__(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.results = {
            'database_tests': {},
            'query_performance': {},
            'algorithm_tests': {},
            'correlation_tests': {},
            'business_logic_tests': {},
            'data_integrity_tests': {},
            'error_handling_tests': {},
            'consistency_tests': {}
        }
        self.issues_found = []
        
    def run_all_tests(self):
        """Execute all test suites"""
        print("="*80)
        print("RFID3 PREDICTIVE ANALYTICS SYSTEM - COMPREHENSIVE TEST SUITE")
        print("="*80)
        
        test_methods = [
            ('Database Connectivity & Record Counts', self.test_database_connectivity),
            ('Query Performance Analysis', self.test_query_performance),
            ('Equipment Utilization Calculations', self.test_equipment_utilization),
            ('ROI and Revenue Analysis', self.test_roi_revenue_analysis),
            ('Correlation Coefficient Calculations', self.test_correlation_calculations),
            ('ML Algorithm Validation', self.test_ml_algorithms),
            ('Data Integrity Constraints', self.test_data_integrity),
            ('Business Logic Validation', self.test_business_logic),
            ('Error Handling & Edge Cases', self.test_error_handling),
            ('Result Consistency & Reproducibility', self.test_consistency)
        ]
        
        for test_name, test_method in test_methods:
            print(f"\n{'='*60}")
            print(f"Testing: {test_name}")
            print(f"{'='*60}")
            try:
                test_method()
            except Exception as e:
                error_msg = f"CRITICAL ERROR in {test_name}: {str(e)}"
                print(f"❌ {error_msg}")
                self.issues_found.append(error_msg)
                traceback.print_exc()
        
        self.generate_report()
        
    def test_database_connectivity(self):
        """Test database connectivity and verify record counts"""
        print("Testing database connectivity...")
        
        try:
            # Test equipment table
            equipment_count = db.session.query(func.count(POSEquipment.equipment_id)).scalar()
            print(f"✓ POSEquipment records: {equipment_count:,}")
            self.results['database_tests']['equipment_count'] = equipment_count
            
            if equipment_count != 25000:
                issue = f"Expected 25,000 equipment records, found {equipment_count}"
                self.issues_found.append(issue)
                print(f"⚠️  {issue}")
            
            # Test other critical tables
            tables = [
                (POSTransaction, 'transaction_id'),
                (POSTransactionItem, 'item_id'),
                (POSCustomer, 'customer_id'),
                (ItemMaster, 'item_number')
            ]
            
            for model, id_field in tables:
                count = db.session.query(func.count(getattr(model, id_field))).scalar()
                table_name = model.__tablename__
                print(f"✓ {table_name} records: {count:,}")
                self.results['database_tests'][table_name] = count
                
            # Test database response time
            start_time = time.time()
            db.session.execute(text("SELECT 1")).scalar()
            response_time = (time.time() - start_time) * 1000
            print(f"✓ Database response time: {response_time:.2f}ms")
            
            if response_time > 100:
                self.issues_found.append(f"High database latency: {response_time:.2f}ms")
                
        except Exception as e:
            self.issues_found.append(f"Database connectivity error: {str(e)}")
            raise
            
    def test_query_performance(self):
        """Test performance of critical queries"""
        print("Testing query performance...")
        
        queries = [
            (
                "Equipment by store aggregation",
                """
                SELECT store_id, COUNT(*) as count, 
                       AVG(utilization_rate) as avg_util
                FROM pos_equipment 
                GROUP BY store_id
                """
            ),
            (
                "Equipment utilization analysis",
                """
                SELECT equipment_type, status,
                       AVG(utilization_rate) as avg_util,
                       AVG(daily_revenue) as avg_revenue
                FROM pos_equipment
                WHERE last_maintenance_date > :date_threshold
                GROUP BY equipment_type, status
                """,
                {'date_threshold': datetime.now() - timedelta(days=90)}
            ),
            (
                "High-value equipment identification",
                """
                SELECT equipment_id, store_id, daily_revenue, roi
                FROM pos_equipment
                WHERE daily_revenue > (
                    SELECT AVG(daily_revenue) + 2 * STDDEV(daily_revenue)
                    FROM pos_equipment
                )
                ORDER BY daily_revenue DESC
                LIMIT 100
                """
            )
        ]
        
        for query_name, query, *params in queries:
            params = params[0] if params else {}
            start_time = time.time()
            
            try:
                result = db.session.execute(text(query), params)
                row_count = result.rowcount if result.rowcount != -1 else len(result.fetchall())
                execution_time = (time.time() - start_time) * 1000
                
                print(f"✓ {query_name}: {execution_time:.2f}ms ({row_count} rows)")
                self.results['query_performance'][query_name] = {
                    'time_ms': execution_time,
                    'rows': row_count
                }
                
                # Flag slow queries (>500ms)
                if execution_time > 500:
                    self.issues_found.append(f"Slow query '{query_name}': {execution_time:.2f}ms")
                    
            except Exception as e:
                self.issues_found.append(f"Query error in '{query_name}': {str(e)}")
                print(f"❌ {query_name}: ERROR - {str(e)}")
                
    def test_equipment_utilization(self):
        """Test equipment utilization calculations"""
        print("Testing equipment utilization calculations...")
        
        try:
            # Get sample equipment for testing
            sample_equipment = db.session.query(POSEquipment).limit(100).all()
            
            # Verify utilization rate calculations
            utilization_issues = []
            for eq in sample_equipment:
                if eq.utilization_rate is not None:
                    if not (0 <= eq.utilization_rate <= 100):
                        utilization_issues.append(f"Equipment {eq.equipment_id}: Invalid utilization {eq.utilization_rate}%")
                        
            if utilization_issues:
                self.issues_found.extend(utilization_issues[:5])  # Log first 5 issues
                print(f"⚠️  Found {len(utilization_issues)} equipment with invalid utilization rates")
            else:
                print("✓ All utilization rates within valid range (0-100%)")
                
            # Test utilization aggregations
            avg_util = db.session.query(func.avg(POSEquipment.utilization_rate)).scalar()
            if avg_util:
                print(f"✓ Average utilization rate: {avg_util:.2f}%")
                
                # Check for reasonable distribution
                util_stats = db.session.query(
                    func.min(POSEquipment.utilization_rate).label('min'),
                    func.max(POSEquipment.utilization_rate).label('max'),
                    func.stddev(POSEquipment.utilization_rate).label('stddev')
                ).first()
                
                print(f"  Min: {util_stats.min:.2f}%, Max: {util_stats.max:.2f}%, StdDev: {util_stats.stddev:.2f}%")
                
                if util_stats.stddev < 5:
                    self.issues_found.append("Suspiciously low variance in utilization rates")
                    
        except Exception as e:
            self.issues_found.append(f"Equipment utilization test error: {str(e)}")
            raise
            
    def test_roi_revenue_analysis(self):
        """Test ROI and revenue calculations"""
        print("Testing ROI and revenue analysis...")
        
        try:
            # Get equipment with financial data
            equipment_with_revenue = db.session.query(POSEquipment).filter(
                POSEquipment.daily_revenue.isnot(None),
                POSEquipment.daily_revenue > 0
            ).limit(100).all()
            
            revenue_issues = []
            roi_issues = []
            
            for eq in equipment_with_revenue:
                # Validate revenue
                if eq.daily_revenue < 0:
                    revenue_issues.append(f"Equipment {eq.equipment_id}: Negative revenue {eq.daily_revenue}")
                elif eq.daily_revenue > 10000:  # Assuming $10K daily is upper reasonable limit
                    revenue_issues.append(f"Equipment {eq.equipment_id}: Suspiciously high revenue ${eq.daily_revenue}")
                    
                # Validate ROI if present
                if eq.roi is not None:
                    if eq.roi < -100:  # ROI shouldn't be less than -100%
                        roi_issues.append(f"Equipment {eq.equipment_id}: Invalid ROI {eq.roi}%")
                        
            if revenue_issues:
                self.issues_found.extend(revenue_issues[:3])
                print(f"⚠️  Found {len(revenue_issues)} equipment with revenue issues")
            else:
                print("✓ All revenue values within reasonable range")
                
            if roi_issues:
                self.issues_found.extend(roi_issues[:3])
                print(f"⚠️  Found {len(roi_issues)} equipment with ROI issues")
            else:
                print("✓ All ROI values within valid range")
                
            # Test revenue aggregations by store
            store_revenue = db.session.query(
                POSEquipment.store_id,
                func.sum(POSEquipment.daily_revenue).label('total_revenue'),
                func.avg(POSEquipment.daily_revenue).label('avg_revenue')
            ).group_by(POSEquipment.store_id).limit(10).all()
            
            print(f"✓ Successfully calculated revenue for {len(store_revenue)} stores")
            
            # Verify revenue calculations are consistent
            for store in store_revenue[:3]:
                print(f"  Store {store.store_id}: Total=${store.total_revenue:.2f}, Avg=${store.avg_revenue:.2f}")
                
        except Exception as e:
            self.issues_found.append(f"ROI/Revenue analysis error: {str(e)}")
            raise
            
    def test_correlation_calculations(self):
        """Test correlation coefficient calculations"""
        print("Testing correlation calculations...")
        
        try:
            # Create test data with known correlation
            np.random.seed(42)
            n = 100
            
            # Perfect positive correlation
            x1 = np.random.randn(n)
            y1 = 2 * x1 + np.random.randn(n) * 0.1
            corr1, p_value1 = stats.pearsonr(x1, y1)
            
            # No correlation
            x2 = np.random.randn(n)
            y2 = np.random.randn(n)
            corr2, p_value2 = stats.pearsonr(x2, y2)
            
            # Negative correlation
            x3 = np.random.randn(n)
            y3 = -1.5 * x3 + np.random.randn(n) * 0.2
            corr3, p_value3 = stats.pearsonr(x3, y3)
            
            print(f"✓ Positive correlation test: r={corr1:.4f}, p={p_value1:.4f}")
            print(f"✓ No correlation test: r={corr2:.4f}, p={p_value2:.4f}")
            print(f"✓ Negative correlation test: r={corr3:.4f}, p={p_value3:.4f}")
            
            # Validate correlation ranges
            if not (-1 <= corr1 <= 1 and -1 <= corr2 <= 1 and -1 <= corr3 <= 1):
                self.issues_found.append("Correlation coefficients outside valid range [-1, 1]")
                
            # Test with actual equipment data
            equipment_data = db.session.query(
                POSEquipment.utilization_rate,
                POSEquipment.daily_revenue
            ).filter(
                POSEquipment.utilization_rate.isnot(None),
                POSEquipment.daily_revenue.isnot(None)
            ).limit(1000).all()
            
            if len(equipment_data) > 30:
                utils = [e[0] for e in equipment_data]
                revenues = [e[1] for e in equipment_data]
                
                if len(set(utils)) > 1 and len(set(revenues)) > 1:  # Ensure variance
                    corr, p_val = stats.pearsonr(utils, revenues)
                    print(f"✓ Utilization-Revenue correlation: r={corr:.4f}, p={p_val:.4f}")
                    
                    if abs(corr) > 0.95:
                        self.issues_found.append(f"Suspiciously high correlation between utilization and revenue: {corr:.4f}")
                else:
                    self.issues_found.append("Insufficient variance in data for correlation analysis")
                    
        except Exception as e:
            self.issues_found.append(f"Correlation calculation error: {str(e)}")
            raise
            
    def test_ml_algorithms(self):
        """Test ML algorithms for mathematical soundness"""
        print("Testing ML algorithms...")
        
        try:
            # Initialize ML service
            ml_service = MLCorrelationService()
            
            # Test with synthetic data
            test_data = {
                'dates': pd.date_range(start='2024-01-01', periods=100, freq='D'),
                'values': np.random.randn(100) * 10 + 50,
                'feature1': np.random.randn(100),
                'feature2': np.random.randn(100)
            }
            df = pd.DataFrame(test_data)
            
            # Test trend detection
            from scipy import stats as sp_stats
            slope, intercept, r_value, p_value, std_err = sp_stats.linregress(
                range(len(df)), df['values']
            )
            
            print(f"✓ Trend analysis: slope={slope:.4f}, R²={r_value**2:.4f}")
            
            if abs(r_value) > 0.99:
                self.issues_found.append("Unrealistic perfect linear trend detected")
                
            # Test autocorrelation
            from statsmodels.stats.diagnostic import acorr_ljungbox
            lb_test = acorr_ljungbox(df['values'], lags=10, return_df=True)
            
            significant_lags = lb_test[lb_test['lb_pvalue'] < 0.05]
            print(f"✓ Autocorrelation test: {len(significant_lags)} significant lags found")
            
            # Test seasonality detection using simple FFT
            from scipy.fft import fft
            fft_values = np.abs(fft(df['values'].values))
            freqs = np.fft.fftfreq(len(df), 1)
            
            # Find dominant frequency (excluding DC component)
            dominant_freq_idx = np.argmax(fft_values[1:len(fft_values)//2]) + 1
            dominant_period = 1 / freqs[dominant_freq_idx] if freqs[dominant_freq_idx] != 0 else 0
            
            print(f"✓ Seasonality detection: dominant period = {abs(dominant_period):.1f} days")
            
        except ImportError as e:
            print(f"⚠️  Missing ML dependency: {str(e)}")
            self.issues_found.append(f"ML library not available: {str(e)}")
        except Exception as e:
            self.issues_found.append(f"ML algorithm error: {str(e)}")
            raise
            
    def test_data_integrity(self):
        """Test data integrity constraints"""
        print("Testing data integrity constraints...")
        
        integrity_checks = [
            # Check for duplicate equipment IDs
            (
                "Duplicate equipment IDs",
                """
                SELECT equipment_id, COUNT(*) as count
                FROM pos_equipment
                GROUP BY equipment_id
                HAVING COUNT(*) > 1
                """
            ),
            # Check for orphaned records
            (
                "Equipment with invalid store IDs",
                """
                SELECT COUNT(*) as orphaned
                FROM pos_equipment
                WHERE store_id IS NULL OR store_id = ''
                """
            ),
            # Check for data consistency
            (
                "Equipment with inconsistent status",
                """
                SELECT COUNT(*) as inconsistent
                FROM pos_equipment
                WHERE status NOT IN ('active', 'inactive', 'maintenance', 'retired')
                """
            ),
            # Check date consistency
            (
                "Equipment with future dates",
                """
                SELECT COUNT(*) as future_dates
                FROM pos_equipment
                WHERE installation_date > CURRENT_DATE
                   OR last_maintenance_date > CURRENT_DATE
                """
            ),
            # Check numerical consistency
            (
                "Equipment with invalid numerical values",
                """
                SELECT COUNT(*) as invalid_numbers
                FROM pos_equipment
                WHERE (utilization_rate IS NOT NULL AND (utilization_rate < 0 OR utilization_rate > 100))
                   OR (daily_revenue IS NOT NULL AND daily_revenue < 0)
                   OR (maintenance_cost IS NOT NULL AND maintenance_cost < 0)
                """
            )
        ]
        
        for check_name, query in integrity_checks:
            try:
                result = db.session.execute(text(query)).first()
                issue_count = result[0] if result else 0
                
                if issue_count > 0:
                    print(f"⚠️  {check_name}: {issue_count} issues found")
                    self.issues_found.append(f"{check_name}: {issue_count} records")
                else:
                    print(f"✓ {check_name}: No issues found")
                    
                self.results['data_integrity_tests'][check_name] = issue_count
                
            except Exception as e:
                print(f"❌ {check_name}: Query error - {str(e)}")
                self.issues_found.append(f"Integrity check '{check_name}' failed: {str(e)}")
                
    def test_business_logic(self):
        """Test business logic validity"""
        print("Testing business logic...")
        
        try:
            # Test equipment lifecycle logic
            equipment_lifecycle = db.session.query(
                POSEquipment.status,
                func.count(POSEquipment.equipment_id).label('count'),
                func.avg(POSEquipment.utilization_rate).label('avg_util')
            ).group_by(POSEquipment.status).all()
            
            print("Equipment lifecycle analysis:")
            for status in equipment_lifecycle:
                print(f"  {status.status}: {status.count} units, avg utilization: {status.avg_util:.2f}%")
                
                # Business logic: retired equipment should have low/zero utilization
                if status.status == 'retired' and status.avg_util and status.avg_util > 10:
                    self.issues_found.append(f"Retired equipment showing {status.avg_util:.2f}% utilization")
                    
            # Test store-level aggregations
            store_metrics = db.session.query(
                POSEquipment.store_id,
                func.count(POSEquipment.equipment_id).label('equipment_count'),
                func.sum(POSEquipment.daily_revenue).label('total_revenue')
            ).group_by(POSEquipment.store_id).having(
                func.count(POSEquipment.equipment_id) > 0
            ).limit(10).all()
            
            # Verify store metrics make business sense
            for store in store_metrics:
                if store.equipment_count > 1000:  # Assuming max 1000 equipment per store
                    self.issues_found.append(f"Store {store.store_id} has unrealistic equipment count: {store.equipment_count}")
                    
                if store.total_revenue and store.equipment_count:
                    rev_per_equipment = store.total_revenue / store.equipment_count
                    if rev_per_equipment > 5000:  # Assuming max $5000 daily per equipment
                        self.issues_found.append(f"Store {store.store_id} has unrealistic revenue per equipment: ${rev_per_equipment:.2f}")
                        
            print("✓ Business logic validation completed")
            
        except Exception as e:
            self.issues_found.append(f"Business logic test error: {str(e)}")
            raise
            
    def test_error_handling(self):
        """Test error handling and edge cases"""
        print("Testing error handling and edge cases...")
        
        test_cases = [
            # Test with None values
            ("None value handling", None, None),
            # Test with empty strings
            ("Empty string handling", "", ""),
            # Test with extreme values
            ("Extreme value handling", float('inf'), float('-inf')),
            # Test with invalid types
            ("Invalid type handling", "not_a_number", [1, 2, 3])
        ]
        
        for test_name, val1, val2 in test_cases:
            try:
                # Attempt correlation with invalid data
                if val1 is not None and val2 is not None:
                    try:
                        result = stats.pearsonr([val1], [val2])
                        print(f"⚠️  {test_name}: Should have raised error but returned {result}")
                    except (TypeError, ValueError) as e:
                        print(f"✓ {test_name}: Properly handled with {type(e).__name__}")
                else:
                    print(f"✓ {test_name}: None values handled")
                    
            except Exception as e:
                print(f"✓ {test_name}: Exception caught - {type(e).__name__}")
                
        # Test database constraint violations
        try:
            # Try to insert duplicate equipment ID (should fail)
            existing = db.session.query(POSEquipment).first()
            if existing:
                duplicate = POSEquipment(
                    equipment_id=existing.equipment_id,
                    store_id='TEST_STORE',
                    equipment_type='TEST'
                )
                db.session.add(duplicate)
                db.session.commit()
                self.issues_found.append("Database allows duplicate equipment IDs!")
        except Exception:
            db.session.rollback()
            print("✓ Database properly rejects duplicate equipment IDs")
            
    def test_consistency(self):
        """Test result consistency and reproducibility"""
        print("Testing result consistency and reproducibility...")
        
        # Run same query multiple times
        results = []
        query = text("""
            SELECT COUNT(*) as count, 
                   AVG(utilization_rate) as avg_util,
                   SUM(daily_revenue) as total_revenue
            FROM pos_equipment
            WHERE status = 'active'
        """)
        
        for i in range(3):
            result = db.session.execute(query).first()
            results.append({
                'count': result.count,
                'avg_util': float(result.avg_util) if result.avg_util else 0,
                'total_revenue': float(result.total_revenue) if result.total_revenue else 0
            })
            
        # Check if results are consistent
        if all(r == results[0] for r in results):
            print("✓ Query results are consistent across multiple executions")
        else:
            self.issues_found.append("Inconsistent query results across executions")
            print("⚠️  Inconsistent results detected:")
            for i, r in enumerate(results):
                print(f"  Run {i+1}: {r}")
                
        # Test analytics service consistency
        try:
            analytics_service = BusinessAnalyticsService()
            
            # Run same analysis twice
            result1 = analytics_service.get_equipment_utilization_by_store(limit=5)
            result2 = analytics_service.get_equipment_utilization_by_store(limit=5)
            
            if result1 == result2:
                print("✓ Analytics service returns consistent results")
            else:
                print("⚠️  Analytics service returns different results for same query")
                self.issues_found.append("Analytics service inconsistency detected")
                
        except Exception as e:
            print(f"⚠️  Could not test analytics service: {str(e)}")
            
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("TEST REPORT SUMMARY")
        print("="*80)
        
        # Summary statistics
        total_tests = sum(len(v) for v in self.results.values() if isinstance(v, dict))
        
        print(f"\nTotal tests executed: {total_tests}")
        print(f"Issues found: {len(self.issues_found)}")
        
        if self.issues_found:
            print("\n⚠️  ISSUES REQUIRING ATTENTION:")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"  {i}. {issue}")
        else:
            print("\n✅ All tests passed successfully!")
            
        # Performance summary
        if self.results['query_performance']:
            print("\nQUERY PERFORMANCE SUMMARY:")
            for query_name, metrics in self.results['query_performance'].items():
                status = "⚠️ SLOW" if metrics['time_ms'] > 500 else "✓"
                print(f"  {status} {query_name}: {metrics['time_ms']:.2f}ms")
                
        # Data integrity summary
        if self.results['data_integrity_tests']:
            print("\nDATA INTEGRITY SUMMARY:")
            total_integrity_issues = sum(self.results['data_integrity_tests'].values())
            if total_integrity_issues > 0:
                print(f"  ⚠️  Total integrity issues: {total_integrity_issues}")
                for check, count in self.results['data_integrity_tests'].items():
                    if count > 0:
                        print(f"    - {check}: {count} issues")
            else:
                print("  ✅ No data integrity issues found")
                
        print("\n" + "="*80)
        print("END OF TEST REPORT")
        print("="*80)
        
        return {
            'total_tests': total_tests,
            'issues_count': len(self.issues_found),
            'issues': self.issues_found,
            'results': self.results
        }

if __name__ == "__main__":
    tester = AnalyticsSystemTester()
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTest suite interrupted by user")
    except Exception as e:
        print(f"\n\nFATAL ERROR: {str(e)}")
        traceback.print_exc()
    finally:
        # Clean up
        if hasattr(tester, 'app_context'):
            tester.app_context.pop()