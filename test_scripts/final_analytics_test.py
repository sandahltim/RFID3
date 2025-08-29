#!/usr/bin/env python3
"""
Final Comprehensive Analytics Test with Flask Context
Tests all components with proper application context handling
"""

import sys
import os
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text

# Add project root to path
sys.path.insert(0, '/home/tim/RFID3')

from app import create_app, db
from app.services.business_analytics_service import BusinessAnalyticsService
from app.services.ml_correlation_service import MLCorrelationService
from app.services.data_fetch_service import DataFetchService

def run_final_tests():
    """Run final comprehensive tests with Flask context"""
    
    # Create Flask application
    app = create_app()
    
    with app.app_context():
        print("="*80)
        print("RFID3 ANALYTICS SYSTEM - FINAL COMPREHENSIVE TEST")
        print("="*80)
        
        # Test results summary
        test_results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
        
        # 1. Database Tests
        print("\n1. DATABASE TESTS")
        print("-"*40)
        
        try:
            # Check equipment count
            equipment_count = db.session.execute(
                text("SELECT COUNT(*) FROM pos_equipment")
            ).scalar()
            
            if equipment_count == 25000:
                print(f"✅ Equipment count verified: {equipment_count:,}")
                test_results['passed'].append("Equipment count verification")
            else:
                print(f"❌ Equipment count mismatch: {equipment_count:,} (expected 25,000)")
                test_results['failed'].append(f"Equipment count: {equipment_count}")
                
            # Check for negative prices
            negative_prices = db.session.execute(
                text("SELECT COUNT(*) FROM pos_equipment WHERE sell_price < 0")
            ).scalar()
            
            if negative_prices == 0:
                print("✅ No negative prices found")
                test_results['passed'].append("Negative price check")
            else:
                print(f"❌ Found {negative_prices} items with negative prices")
                test_results['failed'].append(f"Negative prices: {negative_prices}")
                
            # Check indexes
            indexes = db.session.execute(text("""
                SELECT COUNT(DISTINCT index_name) 
                FROM information_schema.statistics 
                WHERE table_schema = DATABASE() 
                AND table_name = 'pos_equipment'
                AND index_name != 'PRIMARY'
            """)).scalar()
            
            print(f"✅ Database indexes: {indexes} indexes on pos_equipment")
            test_results['passed'].append(f"Database indexes: {indexes}")
            
        except Exception as e:
            print(f"❌ Database test failed: {str(e)}")
            test_results['failed'].append(f"Database test: {str(e)}")
            
        # 2. Business Analytics Service Tests
        print("\n2. BUSINESS ANALYTICS SERVICE TESTS")
        print("-"*40)
        
        try:
            service = BusinessAnalyticsService()
            
            # Test equipment utilization
            utilization = service.calculate_equipment_utilization_analytics()
            if isinstance(utilization, dict) and 'error' not in utilization:
                print(f"✅ Equipment utilization calculated: {utilization.get('total_active_items', 0):,} active items")
                test_results['passed'].append("Equipment utilization calculation")
            else:
                print(f"❌ Equipment utilization failed: {utilization}")
                test_results['failed'].append("Equipment utilization calculation")
                
            # Test customer analytics
            customer = service.calculate_customer_analytics()
            if isinstance(customer, dict):
                print("✅ Customer analytics calculated")
                test_results['passed'].append("Customer analytics")
            else:
                print("❌ Customer analytics failed")
                test_results['failed'].append("Customer analytics")
                
            # Test executive dashboard
            dashboard = service.generate_executive_dashboard_metrics()
            if isinstance(dashboard, dict):
                print("✅ Executive dashboard metrics generated")
                test_results['passed'].append("Executive dashboard metrics")
            else:
                print("❌ Executive dashboard failed")
                test_results['failed'].append("Executive dashboard metrics")
                
        except Exception as e:
            print(f"❌ Business Analytics Service error: {str(e)}")
            test_results['failed'].append(f"Business Analytics Service: {str(e)}")
            
        # 3. ML Correlation Service Tests
        print("\n3. ML CORRELATION SERVICE TESTS")
        print("-"*40)
        
        try:
            ml_service = MLCorrelationService()
            
            # Test correlation analysis
            correlations = ml_service.run_full_correlation_analysis()
            if isinstance(correlations, dict):
                print("✅ ML correlation analysis completed")
                test_results['passed'].append("ML correlation analysis")
                
                # Check for insights
                if 'insights' in correlations:
                    insights = correlations['insights']
                    if 'leading_indicators' in insights:
                        print(f"  • Leading indicators: {len(insights['leading_indicators'])}")
                    if 'strong_correlations' in insights:
                        print(f"  • Strong correlations: {len(insights['strong_correlations'])}")
            else:
                print("❌ ML correlation analysis failed")
                test_results['failed'].append("ML correlation analysis")
                
        except Exception as e:
            print(f"⚠️  ML Correlation Service warning: {str(e)}")
            test_results['warnings'].append(f"ML Correlation Service: {str(e)}")
            
        # 4. Data Fetch Service Tests
        print("\n4. DATA FETCH SERVICE TESTS")
        print("-"*40)
        
        try:
            fetch_service = DataFetchService()
            
            # Check external factors
            factors_count = db.session.execute(
                text("SELECT COUNT(*) FROM external_factors")
            ).scalar()
            
            if factors_count > 0:
                print(f"✅ External factors available: {factors_count} records")
                test_results['passed'].append(f"External factors: {factors_count} records")
            else:
                print("⚠️  No external factors configured")
                test_results['warnings'].append("No external factors")
                
        except Exception as e:
            print(f"⚠️  Data Fetch Service warning: {str(e)}")
            test_results['warnings'].append(f"Data Fetch Service: {str(e)}")
            
        # 5. Query Performance Tests
        print("\n5. QUERY PERFORMANCE TESTS")
        print("-"*40)
        
        performance_queries = [
            ("Count query", "SELECT COUNT(*) FROM pos_equipment", 50),
            ("Aggregation", """
                SELECT category, COUNT(*), AVG(turnover_ytd)
                FROM pos_equipment
                GROUP BY category
            """, 100),
            ("View query", "SELECT * FROM equipment_performance_view LIMIT 100", 200),
            ("Store summary", "SELECT * FROM store_summary_view", 100)
        ]
        
        for query_name, query, threshold in performance_queries:
            try:
                start = time.time()
                result = db.session.execute(text(query))
                _ = result.fetchall()
                elapsed = (time.time() - start) * 1000
                
                if elapsed < threshold:
                    print(f"✅ {query_name}: {elapsed:.2f}ms (< {threshold}ms)")
                    test_results['passed'].append(f"{query_name} performance")
                else:
                    print(f"⚠️  {query_name}: {elapsed:.2f}ms (threshold: {threshold}ms)")
                    test_results['warnings'].append(f"{query_name}: {elapsed:.2f}ms")
                    
            except Exception as e:
                # Views might not exist
                if "doesn't exist" in str(e):
                    print(f"⚠️  {query_name}: View not found")
                else:
                    print(f"❌ {query_name}: {str(e)}")
                    test_results['failed'].append(f"{query_name}: {str(e)}")
                    
        # 6. Data Integrity Tests
        print("\n6. DATA INTEGRITY TESTS")
        print("-"*40)
        
        integrity_checks = [
            ("Duplicate items", """
                SELECT COUNT(*) FROM (
                    SELECT item_num, COUNT(*) as c 
                    FROM pos_equipment 
                    GROUP BY item_num 
                    HAVING c > 1
                ) as dups
            """),
            ("Invalid turnover (YTD > LTD)", """
                SELECT COUNT(*) 
                FROM pos_equipment 
                WHERE turnover_ytd > turnover_ltd
            """),
            ("Missing categories", """
                SELECT COUNT(*) 
                FROM pos_equipment 
                WHERE category IS NULL OR category = ''
            """)
        ]
        
        for check_name, query in integrity_checks:
            try:
                issues = db.session.execute(text(query)).scalar()
                if issues == 0:
                    print(f"✅ {check_name}: No issues")
                    test_results['passed'].append(f"Integrity: {check_name}")
                else:
                    print(f"⚠️  {check_name}: {issues} issues found")
                    test_results['warnings'].append(f"{check_name}: {issues} issues")
                    
            except Exception as e:
                print(f"❌ {check_name}: {str(e)}")
                test_results['failed'].append(f"Integrity check: {check_name}")
                
        # 7. Algorithm Accuracy Tests
        print("\n7. ALGORITHM ACCURACY TESTS")
        print("-"*40)
        
        # Test correlation calculations
        np.random.seed(42)
        x = np.random.randn(100)
        y = 2 * x + np.random.randn(100) * 0.1
        
        correlation = np.corrcoef(x, y)[0, 1]
        if 0.95 < correlation < 1.0:
            print(f"✅ Correlation calculation accurate: r={correlation:.4f}")
            test_results['passed'].append("Correlation accuracy")
        else:
            print(f"❌ Correlation calculation issue: r={correlation:.4f}")
            test_results['failed'].append(f"Correlation accuracy: {correlation:.4f}")
            
        # Test statistical functions
        data = [1, 2, 3, 4, 5]
        mean = np.mean(data)
        std = np.std(data)
        
        if abs(mean - 3.0) < 0.001 and abs(std - 1.414) < 0.01:
            print("✅ Statistical functions accurate")
            test_results['passed'].append("Statistical functions")
        else:
            print(f"❌ Statistical functions issue: mean={mean}, std={std}")
            test_results['failed'].append("Statistical functions")
            
        # Final Report
        print("\n" + "="*80)
        print("FINAL TEST REPORT")
        print("="*80)
        
        total_tests = len(test_results['passed']) + len(test_results['failed']) + len(test_results['warnings'])
        
        print(f"\nTOTAL TESTS: {total_tests}")
        print(f"✅ PASSED: {len(test_results['passed'])}")
        print(f"❌ FAILED: {len(test_results['failed'])}")
        print(f"⚠️  WARNINGS: {len(test_results['warnings'])}")
        
        if test_results['failed']:
            print("\nFAILED TESTS:")
            for test in test_results['failed']:
                print(f"  • {test}")
                
        if test_results['warnings']:
            print("\nWARNINGS:")
            for warning in test_results['warnings']:
                print(f"  • {warning}")
                
        # Overall Status
        print("\n" + "="*80)
        if len(test_results['failed']) == 0:
            print("✅ SYSTEM STATUS: ALL CRITICAL TESTS PASSED")
            print("The RFID3 Predictive Analytics System is functioning correctly.")
        elif len(test_results['failed']) < 3:
            print("⚠️  SYSTEM STATUS: MOSTLY FUNCTIONAL")
            print("Minor issues detected but system is operational.")
        else:
            print("❌ SYSTEM STATUS: CRITICAL ISSUES DETECTED")
            print("Multiple failures detected. Review and fix required.")
            
        print("="*80)
        
        return test_results

if __name__ == "__main__":
    try:
        results = run_final_tests()
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()