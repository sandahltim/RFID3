#!/usr/bin/env python3
"""
Direct Database and Analytics Testing - Bypasses Flask app initialization
"""

import sys
import os
import time
import traceback
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import create_engine, func, text, and_, or_, inspect
from sqlalchemy.orm import sessionmaker
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Database configuration
DB_USER = os.getenv('DB_USER', 'rfid_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'rfid_user_password') 
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_DATABASE', 'rfid_inventory')
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

class DirectAnalyticsTester:
    def __init__(self):
        self.engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.results = {}
        self.issues = []
        
    def test_database_structure(self):
        """Test database structure and tables"""
        print("\n1. DATABASE STRUCTURE ANALYSIS")
        print("="*60)
        
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()
        
        print(f"Found {len(tables)} tables in database")
        
        # Focus on POS and analytics tables
        relevant_tables = [t for t in tables if 'pos' in t.lower() or 'analytics' in t.lower() or 'external' in t.lower()]
        
        for table in relevant_tables:
            columns = inspector.get_columns(table)
            indexes = inspector.get_indexes(table)
            pk = inspector.get_pk_constraint(table)
            fks = inspector.get_foreign_keys(table)
            
            print(f"\nTable: {table}")
            print(f"  Columns: {len(columns)}")
            print(f"  Indexes: {len(indexes)}")
            print(f"  Primary Key: {pk['constrained_columns'] if pk else 'None'}")
            print(f"  Foreign Keys: {len(fks)}")
            
            # Get row count
            try:
                count = self.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                print(f"  Row Count: {count:,}")
                
                if table == 'pos_equipment' and count != 25000:
                    self.issues.append(f"Expected 25,000 records in pos_equipment, found {count}")
            except Exception as e:
                print(f"  Row Count: ERROR - {str(e)}")
                
    def test_equipment_data_quality(self):
        """Test equipment data quality and integrity"""
        print("\n2. EQUIPMENT DATA QUALITY ANALYSIS")
        print("="*60)
        
        # Check for null values in critical fields
        null_checks = [
            ('equipment_id', 'Equipment without ID'),
            ('store_id', 'Equipment without store'),
            ('equipment_type', 'Equipment without type'),
            ('status', 'Equipment without status')
        ]
        
        for field, description in null_checks:
            query = text(f"""
                SELECT COUNT(*) FROM pos_equipment 
                WHERE {field} IS NULL OR {field} = ''
            """)
            null_count = self.session.execute(query).scalar()
            
            if null_count > 0:
                print(f"⚠️  {description}: {null_count} records")
                self.issues.append(f"{description}: {null_count} records")
            else:
                print(f"✓ {description}: No issues")
                
        # Check value distributions
        print("\nValue Distribution Analysis:")
        
        # Status distribution
        status_dist = self.session.execute(text("""
            SELECT status, COUNT(*) as count,
                   AVG(utilization_rate) as avg_util
            FROM pos_equipment
            GROUP BY status
            ORDER BY count DESC
        """)).fetchall()
        
        print("\nStatus Distribution:")
        for row in status_dist:
            print(f"  {row[0]}: {row[1]:,} records (avg util: {row[2]:.2f}%)" if row[2] else f"  {row[0]}: {row[1]:,} records")
            
        # Equipment type distribution
        type_dist = self.session.execute(text("""
            SELECT equipment_type, COUNT(*) as count
            FROM pos_equipment
            GROUP BY equipment_type
            ORDER BY count DESC
            LIMIT 10
        """)).fetchall()
        
        print("\nTop Equipment Types:")
        for row in type_dist:
            print(f"  {row[0]}: {row[1]:,} records")
            
    def test_utilization_calculations(self):
        """Test utilization rate calculations"""
        print("\n3. UTILIZATION RATE ANALYSIS")
        print("="*60)
        
        # Get utilization statistics
        util_stats = self.session.execute(text("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(utilization_rate) as records_with_util,
                MIN(utilization_rate) as min_util,
                MAX(utilization_rate) as max_util,
                AVG(utilization_rate) as avg_util,
                STDDEV(utilization_rate) as stddev_util
            FROM pos_equipment
        """)).first()
        
        print(f"Total Equipment: {util_stats[0]:,}")
        print(f"With Utilization Data: {util_stats[1]:,}")
        
        if util_stats[1] > 0:
            print(f"Min Utilization: {util_stats[2]:.2f}%")
            print(f"Max Utilization: {util_stats[3]:.2f}%")
            print(f"Avg Utilization: {util_stats[4]:.2f}%")
            print(f"Std Dev: {util_stats[5]:.2f}%")
            
            # Check for invalid values
            invalid_util = self.session.execute(text("""
                SELECT COUNT(*) FROM pos_equipment
                WHERE utilization_rate < 0 OR utilization_rate > 100
            """)).scalar()
            
            if invalid_util > 0:
                self.issues.append(f"Found {invalid_util} equipment with invalid utilization rates")
                print(f"\n⚠️  Invalid utilization rates: {invalid_util} records")
            else:
                print("\n✓ All utilization rates within valid range (0-100%)")
                
        # Test utilization by status
        util_by_status = self.session.execute(text("""
            SELECT status, 
                   AVG(utilization_rate) as avg_util,
                   COUNT(*) as count
            FROM pos_equipment
            WHERE utilization_rate IS NOT NULL
            GROUP BY status
        """)).fetchall()
        
        print("\nUtilization by Status:")
        for row in util_by_status:
            print(f"  {row[0]}: {row[1]:.2f}% (n={row[2]:,})")
            
            # Business logic check
            if row[0] == 'retired' and row[1] > 10:
                self.issues.append(f"Retired equipment showing {row[1]:.2f}% utilization")
                
    def test_revenue_roi_analysis(self):
        """Test revenue and ROI calculations"""
        print("\n4. REVENUE AND ROI ANALYSIS")
        print("="*60)
        
        # Revenue statistics
        revenue_stats = self.session.execute(text("""
            SELECT 
                COUNT(daily_revenue) as records_with_revenue,
                MIN(daily_revenue) as min_revenue,
                MAX(daily_revenue) as max_revenue,
                AVG(daily_revenue) as avg_revenue,
                SUM(daily_revenue) as total_revenue,
                STDDEV(daily_revenue) as stddev_revenue
            FROM pos_equipment
            WHERE daily_revenue IS NOT NULL
        """)).first()
        
        print(f"Equipment with Revenue Data: {revenue_stats[0]:,}")
        
        if revenue_stats[0] > 0:
            print(f"Min Daily Revenue: ${revenue_stats[1]:.2f}")
            print(f"Max Daily Revenue: ${revenue_stats[2]:.2f}")
            print(f"Avg Daily Revenue: ${revenue_stats[3]:.2f}")
            print(f"Total Daily Revenue: ${revenue_stats[4]:,.2f}")
            print(f"Std Dev: ${revenue_stats[5]:.2f}")
            
            # Check for negative revenue
            negative_revenue = self.session.execute(text("""
                SELECT COUNT(*) FROM pos_equipment
                WHERE daily_revenue < 0
            """)).scalar()
            
            if negative_revenue > 0:
                self.issues.append(f"Found {negative_revenue} equipment with negative revenue")
                print(f"\n⚠️  Negative revenue: {negative_revenue} records")
                
            # Check for outliers (> 3 std dev from mean)
            outlier_threshold = revenue_stats[3] + (3 * revenue_stats[5])
            outliers = self.session.execute(text("""
                SELECT COUNT(*) FROM pos_equipment
                WHERE daily_revenue > :threshold
            """), {'threshold': outlier_threshold}).scalar()
            
            if outliers > 0:
                print(f"⚠️  Revenue outliers (>3σ): {outliers} records")
                
        # ROI Analysis
        roi_stats = self.session.execute(text("""
            SELECT 
                COUNT(roi) as records_with_roi,
                MIN(roi) as min_roi,
                MAX(roi) as max_roi,
                AVG(roi) as avg_roi
            FROM pos_equipment
            WHERE roi IS NOT NULL
        """)).first()
        
        print(f"\nEquipment with ROI Data: {roi_stats[0]:,}")
        
        if roi_stats[0] > 0:
            print(f"Min ROI: {roi_stats[1]:.2f}%")
            print(f"Max ROI: {roi_stats[2]:.2f}%")
            print(f"Avg ROI: {roi_stats[3]:.2f}%")
            
            # Check for invalid ROI
            invalid_roi = self.session.execute(text("""
                SELECT COUNT(*) FROM pos_equipment
                WHERE roi < -100
            """)).scalar()
            
            if invalid_roi > 0:
                self.issues.append(f"Found {invalid_roi} equipment with ROI < -100%")
                
    def test_store_analytics(self):
        """Test store-level analytics"""
        print("\n5. STORE-LEVEL ANALYTICS")
        print("="*60)
        
        # Store summary
        store_summary = self.session.execute(text("""
            SELECT 
                store_id,
                COUNT(*) as equipment_count,
                AVG(utilization_rate) as avg_utilization,
                SUM(daily_revenue) as total_revenue,
                AVG(roi) as avg_roi
            FROM pos_equipment
            GROUP BY store_id
            ORDER BY total_revenue DESC NULLS LAST
            LIMIT 10
        """)).fetchall()
        
        print("Top 10 Stores by Revenue:")
        for i, row in enumerate(store_summary, 1):
            revenue = f"${row[3]:,.2f}" if row[3] else "N/A"
            util = f"{row[2]:.2f}%" if row[2] else "N/A"
            roi = f"{row[4]:.2f}%" if row[4] else "N/A"
            print(f"  {i}. Store {row[0]}: {row[1]} equipment, {util} util, {revenue} revenue, {roi} ROI")
            
            # Check for anomalies
            if row[1] > 1000:  # More than 1000 equipment in one store
                self.issues.append(f"Store {row[0]} has unusually high equipment count: {row[1]}")
                
    def test_correlations(self):
        """Test correlation calculations"""
        print("\n6. CORRELATION ANALYSIS")
        print("="*60)
        
        # Get data for correlation
        correlation_data = self.session.execute(text("""
            SELECT 
                utilization_rate,
                daily_revenue,
                maintenance_cost,
                roi
            FROM pos_equipment
            WHERE utilization_rate IS NOT NULL 
              AND daily_revenue IS NOT NULL
            LIMIT 1000
        """)).fetchall()
        
        if len(correlation_data) > 30:
            df = pd.DataFrame(correlation_data, columns=['utilization', 'revenue', 'maintenance', 'roi'])
            
            # Calculate correlations
            correlations = []
            pairs = [
                ('utilization', 'revenue', 'Utilization vs Revenue'),
                ('utilization', 'maintenance', 'Utilization vs Maintenance'),
                ('revenue', 'roi', 'Revenue vs ROI')
            ]
            
            for col1, col2, description in pairs:
                data1 = df[col1].dropna()
                data2 = df[col2].dropna()
                
                # Find common indices
                common_idx = data1.index.intersection(data2.index)
                
                if len(common_idx) > 30:
                    corr, p_value = stats.pearsonr(data1[common_idx], data2[common_idx])
                    print(f"{description}: r={corr:.4f}, p={p_value:.4f}")
                    
                    # Check for unrealistic correlations
                    if abs(corr) > 0.95:
                        self.issues.append(f"Suspiciously high correlation for {description}: {corr:.4f}")
                        
        else:
            print("Insufficient data for correlation analysis")
            
    def test_query_performance(self):
        """Test query performance"""
        print("\n7. QUERY PERFORMANCE TESTING")
        print("="*60)
        
        queries = [
            ("Simple count", "SELECT COUNT(*) FROM pos_equipment"),
            ("Aggregation", """
                SELECT store_id, COUNT(*), AVG(utilization_rate), SUM(daily_revenue)
                FROM pos_equipment
                GROUP BY store_id
            """),
            ("Complex join", """
                SELECT e1.store_id, COUNT(DISTINCT e1.equipment_id), AVG(e1.utilization_rate)
                FROM pos_equipment e1
                LEFT JOIN pos_equipment e2 ON e1.store_id = e2.store_id 
                    AND e1.equipment_type = e2.equipment_type
                WHERE e1.status = 'active'
                GROUP BY e1.store_id
                LIMIT 100
            """),
            ("Subquery", """
                SELECT equipment_id, daily_revenue
                FROM pos_equipment
                WHERE daily_revenue > (
                    SELECT AVG(daily_revenue) + STDDEV(daily_revenue)
                    FROM pos_equipment
                )
                LIMIT 100
            """)
        ]
        
        for query_name, query in queries:
            start_time = time.time()
            try:
                result = self.session.execute(text(query))
                _ = result.fetchall()  # Force execution
                execution_time = (time.time() - start_time) * 1000
                
                status = "⚠️ SLOW" if execution_time > 500 else "✓"
                print(f"{status} {query_name}: {execution_time:.2f}ms")
                
                if execution_time > 1000:
                    self.issues.append(f"Slow query '{query_name}': {execution_time:.2f}ms")
                    
            except Exception as e:
                print(f"❌ {query_name}: ERROR - {str(e)}")
                self.issues.append(f"Query error in '{query_name}': {str(e)}")
                
    def test_data_consistency(self):
        """Test data consistency"""
        print("\n8. DATA CONSISTENCY CHECKS")
        print("="*60)
        
        # Test for orphaned records
        orphan_checks = [
            ("Equipment with non-existent stores", """
                SELECT COUNT(DISTINCT pe.store_id) 
                FROM pos_equipment pe
                WHERE pe.store_id NOT IN (
                    SELECT DISTINCT store_id FROM pos_equipment WHERE store_id IS NOT NULL
                    )
                AND pe.store_id IS NOT NULL
            """),
            ("Duplicate equipment IDs", """
                SELECT equipment_id, COUNT(*) as count
                FROM pos_equipment
                GROUP BY equipment_id
                HAVING COUNT(*) > 1
            """),
            ("Inconsistent date fields", """
                SELECT COUNT(*)
                FROM pos_equipment
                WHERE last_maintenance_date < installation_date
                  AND last_maintenance_date IS NOT NULL
                  AND installation_date IS NOT NULL
            """)
        ]
        
        for check_name, query in orphan_checks:
            try:
                result = self.session.execute(text(query))
                rows = result.fetchall()
                
                if rows and rows[0][0] > 0:
                    count = rows[0][0] if len(rows[0]) == 1 else len(rows)
                    print(f"⚠️  {check_name}: {count} issues found")
                    self.issues.append(f"{check_name}: {count} issues")
                else:
                    print(f"✓ {check_name}: No issues")
                    
            except Exception as e:
                print(f"❌ {check_name}: ERROR - {str(e)}")
                
    def test_external_factors(self):
        """Test external factors table if exists"""
        print("\n9. EXTERNAL FACTORS ANALYSIS")
        print("="*60)
        
        # Check if external_factors table exists
        inspector = inspect(self.engine)
        if 'external_factors' in inspector.get_table_names():
            try:
                count = self.session.execute(text("SELECT COUNT(*) FROM external_factors")).scalar()
                print(f"External factors records: {count:,}")
                
                if count > 0:
                    # Get sample data
                    sample = self.session.execute(text("""
                        SELECT factor_type, COUNT(*) as count
                        FROM external_factors
                        GROUP BY factor_type
                        LIMIT 10
                    """)).fetchall()
                    
                    print("Factor types:")
                    for row in sample:
                        print(f"  {row[0]}: {row[1]:,} records")
                        
            except Exception as e:
                print(f"Error accessing external_factors: {str(e)}")
        else:
            print("external_factors table not found")
            
    def generate_report(self):
        """Generate final report"""
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST REPORT")
        print("="*80)
        
        if self.issues:
            print(f"\n⚠️  ISSUES FOUND: {len(self.issues)}")
            print("\nDetailed Issues:")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")
        else:
            print("\n✅ ALL TESTS PASSED - No critical issues found")
            
        print("\nRECOMMENDATIONS:")
        
        # Generate recommendations based on issues
        if any('utilization' in issue.lower() for issue in self.issues):
            print("  • Review utilization calculation logic")
            
        if any('revenue' in issue.lower() or 'roi' in issue.lower() for issue in self.issues):
            print("  • Validate financial calculations and data sources")
            
        if any('slow query' in issue.lower() for issue in self.issues):
            print("  • Add database indexes for frequently queried columns")
            print("  • Consider query optimization or caching strategies")
            
        if any('duplicate' in issue.lower() or 'orphan' in issue.lower() for issue in self.issues):
            print("  • Implement database constraints to prevent data integrity issues")
            print("  • Create data cleanup procedures")
            
        if not self.issues:
            print("  • System is functioning well")
            print("  • Consider adding more comprehensive monitoring")
            
        print("\n" + "="*80)
        
    def cleanup(self):
        """Clean up database connections"""
        self.session.close()
        self.engine.dispose()

def main():
    print("RFID3 PREDICTIVE ANALYTICS - DIRECT DATABASE TESTING")
    print("="*80)
    
    tester = DirectAnalyticsTester()
    
    try:
        # Run all tests
        tester.test_database_structure()
        tester.test_equipment_data_quality()
        tester.test_utilization_calculations()
        tester.test_revenue_roi_analysis()
        tester.test_store_analytics()
        tester.test_correlations()
        tester.test_query_performance()
        tester.test_data_consistency()
        tester.test_external_factors()
        
        # Generate report
        tester.generate_report()
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nCRITICAL ERROR: {str(e)}")
        traceback.print_exc()
    finally:
        tester.cleanup()
        print("\nTest completed.")

if __name__ == "__main__":
    main()