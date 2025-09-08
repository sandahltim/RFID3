#!/usr/bin/env python3
"""
Scorecard Data Correlation Analysis
Comprehensive analysis of business metrics relationships
"""

from app import create_app, db
from app.models.financial_models import (
    ScorecardTrendsData, 
    ScorecardMetricsDefinition,
    PayrollTrendsData,
    FinancialMetrics,
    StorePerformanceBenchmarks
)
from sqlalchemy import func, distinct, and_, or_, case
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from decimal import Decimal

def analyze_data_quality():
    """Comprehensive data quality assessment"""
    print("\n" + "="*80)
    print("DATA QUALITY ASSESSMENT")
    print("="*80)
    
    # Basic statistics
    scorecard_count = db.session.query(func.count(ScorecardTrendsData.id)).scalar()
    metrics_def_count = db.session.query(func.count(ScorecardMetricsDefinition.id)).scalar()
    payroll_count = db.session.query(func.count(PayrollTrendsData.id)).scalar()
    
    # Date coverage
    min_date = db.session.query(func.min(ScorecardTrendsData.week_ending)).scalar()
    max_date = db.session.query(func.max(ScorecardTrendsData.week_ending)).scalar()
    
    print(f"\n Current State Assessment:")
    print(f"  - Scorecard Records: {scorecard_count}")
    print(f"  - Metrics Definitions: {metrics_def_count}")
    print(f"  - Payroll Records: {payroll_count}")
    print(f"  - Date Range: {min_date} to {max_date}")
    
    if min_date and max_date:
        weeks_covered = (max_date - min_date).days // 7
        print(f"  - Weeks Covered: {weeks_covered}")
    
    # Data completeness analysis
    print(f"\n Data Completeness Analysis:")
    
    # Check for null values in critical fields
    critical_fields = [
        ('total_weekly_revenue', 'Total Revenue'),
        ('ar_over_45_days_percent', 'AR Over 45 Days %'),
        ('total_discount', 'Total Discount'),
        ('total_ar_cash_customers', 'Total AR Cash Customers')
    ]
    
    for field, label in critical_fields:
        null_count = db.session.query(func.count(ScorecardTrendsData.id)).filter(
            getattr(ScorecardTrendsData, field).is_(None)
        ).scalar()
        completeness = ((scorecard_count - null_count) / scorecard_count * 100) if scorecard_count > 0 else 0
        print(f"  - {label}: {completeness:.1f}% complete ({null_count} nulls)")
    
    # Check for data consistency
    print(f"\n Data Consistency Issues:")
    
    # Find weeks with mismatched revenue totals
    mismatched_revenue = db.session.query(ScorecardTrendsData).filter(
        func.abs(
            ScorecardTrendsData.total_weekly_revenue - 
            (func.coalesce(ScorecardTrendsData.revenue_3607, 0) +
             func.coalesce(ScorecardTrendsData.revenue_6800, 0) +
             func.coalesce(ScorecardTrendsData.revenue_728, 0) +
             func.coalesce(ScorecardTrendsData.revenue_8101, 0))
        ) > 1
    ).count()
    
    print(f"  - Revenue Total Mismatches: {mismatched_revenue}")
    
    # Check for duplicate weeks
    duplicates = db.session.query(
        ScorecardTrendsData.week_ending,
        func.count(ScorecardTrendsData.id).label('count')
    ).group_by(ScorecardTrendsData.week_ending).having(
        func.count(ScorecardTrendsData.id) > 1
    ).all()
    
    print(f"  - Duplicate Week Entries: {len(duplicates)}")
    if duplicates:
        for week, count in duplicates[:5]:  # Show first 5
            print(f"    - {week}: {count} entries")
    
    # Check for data gaps
    if min_date and max_date:
        expected_weeks = set()
        current_date = min_date
        while current_date <= max_date:
            expected_weeks.add(current_date)
            current_date += timedelta(days=7)
        
        actual_weeks = set([r[0] for r in db.session.query(ScorecardTrendsData.week_ending).distinct().all()])
        missing_weeks = expected_weeks - actual_weeks
        
        print(f"  - Missing Week Entries: {len(missing_weeks)}")
        if missing_weeks:
            for week in sorted(list(missing_weeks))[:5]:  # Show first 5
                print(f"    - {week}")
    
    return scorecard_count > 0

def analyze_correlations():
    """Identify key correlations in the data"""
    print("\n" + "="*80)
    print("RELATIONSHIP MAPPINGS & CORRELATIONS")
    print("="*80)
    
    # Get all scorecard data for correlation analysis
    data = db.session.query(ScorecardTrendsData).order_by(ScorecardTrendsData.week_ending).all()
    
    if not data:
        print("No data available for correlation analysis")
        return
    
    # Convert to pandas DataFrame for easier analysis
    df_data = []
    for row in data:
        df_data.append({
            'week_ending': row.week_ending,
            'total_revenue': float(row.total_weekly_revenue or 0),
            'revenue_3607': float(row.revenue_3607 or 0),
            'revenue_6800': float(row.revenue_6800 or 0),
            'revenue_728': float(row.revenue_728 or 0),
            'revenue_8101': float(row.revenue_8101 or 0),
            'contracts_3607': row.new_contracts_3607 or 0,
            'contracts_6800': row.new_contracts_6800 or 0,
            'contracts_728': row.new_contracts_728 or 0,
            'contracts_8101': row.new_contracts_8101 or 0,
            'ar_over_45_pct': float(row.ar_over_45_days_percent or 0),
            'discount': float(row.total_discount or 0),
            'deliveries_8101': row.deliveries_scheduled_8101 or 0,
            'reservation_14d_total': float((row.reservation_next14_3607 or 0) + 
                                         (row.reservation_next14_6800 or 0) +
                                         (row.reservation_next14_728 or 0) +
                                         (row.reservation_next14_8101 or 0))
        })
    
    df = pd.DataFrame(df_data)
    
    print("\n Key Correlations Identified:")
    
    # 1. Revenue vs Contracts correlation by store
    print("\n1. Store Revenue vs New Contracts Correlation:")
    stores = [
        ('3607', 'Wayzata'),
        ('6800', 'Brooklyn Park'),
        ('728', 'Elk River'),
        ('8101', 'Fridley')
    ]
    
    for code, name in stores:
        if f'revenue_{code}' in df.columns and f'contracts_{code}' in df.columns:
            # Filter out zero values for better correlation
            mask = (df[f'revenue_{code}'] > 0) & (df[f'contracts_{code}'] > 0)
            if mask.any():
                corr = df[mask][f'revenue_{code}'].corr(df[mask][f'contracts_{code}'])
                avg_contract_value = df[mask][f'revenue_{code}'].sum() / df[mask][f'contracts_{code}'].sum()
                print(f"  - {name} ({code}): {corr:.3f} correlation, ${avg_contract_value:,.0f} avg contract")
    
    # 2. AR Aging vs Revenue Performance
    print("\n2. AR Aging Impact on Revenue:")
    if 'ar_over_45_pct' in df.columns and 'total_revenue' in df.columns:
        # Categorize AR aging
        df['ar_category'] = pd.cut(df['ar_over_45_pct'], 
                                   bins=[0, 5, 10, 20, 100],
                                   labels=['Low (<5%)', 'Moderate (5-10%)', 'High (10-20%)', 'Critical (>20%)'])
        
        ar_impact = df.groupby('ar_category').agg({
            'total_revenue': ['mean', 'count']
        })
        
        print("  Revenue by AR Aging Category:")
        for category in ar_impact.index:
            if pd.notna(category):
                mean_rev = ar_impact.loc[category, ('total_revenue', 'mean')]
                count = ar_impact.loc[category, ('total_revenue', 'count')]
                print(f"    - {category}: ${mean_rev:,.0f} avg revenue ({count} weeks)")
    
    # 3. Seasonality Analysis
    print("\n3. Seasonal Patterns:")
    df['month'] = pd.to_datetime(df['week_ending']).dt.month
    df['quarter'] = pd.to_datetime(df['week_ending']).dt.quarter
    
    monthly_avg = df.groupby('month')['total_revenue'].mean()
    quarterly_avg = df.groupby('quarter')['total_revenue'].mean()
    
    print("  Monthly Revenue Averages:")
    for month in sorted(monthly_avg.index):
        print(f"    - Month {month:02d}: ${monthly_avg[month]:,.0f}")
    
    # 4. Store Performance Concentration
    print("\n4. Revenue Concentration Risk:")
    high_concentration_weeks = 0
    for _, row in df.iterrows():
        store_revenues = [row['revenue_3607'], row['revenue_6800'], 
                         row['revenue_728'], row['revenue_8101']]
        total = sum(store_revenues)
        if total > 0:
            max_concentration = max(store_revenues) / total * 100
            if max_concentration > 40:  # Flag high concentration
                high_concentration_weeks += 1
                if high_concentration_weeks <= 3:  # Show first 3
                    dominant_store = stores[store_revenues.index(max(store_revenues))][1]
                    print(f"  WARNING: {row['week_ending']}: {dominant_store} = {max_concentration:.1f}% of revenue")
    
    if high_concentration_weeks > 3:
        print(f"  ... and {high_concentration_weeks - 3} more weeks with high concentration")
    
    # 5. Pipeline to Revenue Conversion
    print("\n5. Reservation Pipeline Analysis:")
    if 'reservation_14d_total' in df.columns:
        # Shift reservation data by 2 weeks to see conversion
        df['future_revenue'] = df['total_revenue'].shift(-2)
        
        mask = (df['reservation_14d_total'] > 0) & (df['future_revenue'].notna())
        if mask.any():
            conversion_rate = df[mask]['future_revenue'].sum() / df[mask]['reservation_14d_total'].sum()
            print(f"  - Pipeline Conversion Rate: {conversion_rate:.2%}")
            
            corr = df[mask]['reservation_14d_total'].corr(df[mask]['future_revenue'])
            print(f"  - Pipeline-to-Revenue Correlation: {corr:.3f}")

def identify_integration_opportunities():
    """Identify opportunities for dashboard integration"""
    print("\n" + "="*80)
    print("INTEGRATION RECOMMENDATIONS")
    print("="*80)
    
    print("\n Dashboard Enhancement Opportunities:")
    
    # 1. Executive Dashboard (Tab 7)
    print("\n1. Executive Dashboard Enhancements:")
    print("  - Add rolling 4-week revenue trends with YoY comparison")
    print("  - Implement store performance heat map showing:")
    print("    - Revenue contribution %")
    print("    - Contract conversion rates")
    print("    - AR aging by location")
    print("  - Create predictive revenue forecast based on:")
    print("    - Historical patterns")
    print("    - Reservation pipeline")
    print("    - Seasonal adjustments")
    print("  - Add alerting for:")
    print("    - Revenue concentration > 40% in single store")
    print("    - AR aging > 15%")
    print("    - Contract volume drops > 20% week-over-week")
    
    # 2. Manager Dashboard
    print("\n2. Manager/Operations Dashboard:")
    print("  - Store-specific KPI scorecards with:")
    print("    - Weekly performance vs goals")
    print("    - Contract pipeline visualization")
    print("    - Delivery scheduling optimization")
    print("  - Comparative store analytics:")
    print("    - Peer store benchmarking")
    print("    - Best practice identification")
    print("    - Resource allocation recommendations")
    
    # 3. Financial Analytics
    print("\n3. Financial Analytics Integration:")
    print("  - Link scorecard metrics to payroll data for:")
    print("    - Revenue per labor hour")
    print("    - Labor efficiency scores")
    print("    - Optimal staffing recommendations")
    print("  - Implement cash flow forecasting using:")
    print("    - AR aging trends")
    print("    - Reservation pipeline")
    print("    - Historical collection patterns")

def suggest_database_optimizations():
    """Suggest database schema and performance optimizations"""
    print("\n" + "="*80)
    print("DATABASE OPTIMIZATION RECOMMENDATIONS")
    print("="*80)
    
    print("\n Schema Enhancements:")
    
    print("\n1. Add Missing Relationships:")
    print("  - Create StoreLocationMaster table:")
    print("    - store_code (PK)")
    print("    - store_name")
    print("    - region")
    print("    - square_footage")
    print("    - employee_count")
    print("    - market_size")
    print("  - Link ScorecardTrendsData to StoreLocationMaster via foreign keys")
    print("  - Create junction table for multi-store metrics aggregation")
    
    print("\n2. Add Calculated Columns (via triggers or materialized views):")
    print("  - revenue_variance_pct (actual vs sum of stores)")
    print("  - contract_conversion_rate (contracts to revenue ratio)")
    print("  - pipeline_coverage_ratio (pipeline / avg weekly revenue)")
    print("  - ar_health_score (composite of AR metrics)")
    
    print("\n3. Implement Data Validation Constraints:")
    print("  - CHECK constraint: total_weekly_revenue = sum of store revenues")
    print("  - CHECK constraint: ar_over_45_days_percent BETWEEN 0 AND 100")
    print("  - UNIQUE constraint: week_ending (prevent duplicates)")
    print("  - NOT NULL constraints on critical metrics")
    
    print("\n4. Add Performance Indexes:")
    print("  - Composite index: (week_ending, store_code) for time-series queries")
    print("  - Partial index: WHERE ar_over_45_days_percent > 10 for risk queries")
    print("  - Covering index: (week_ending, total_weekly_revenue, all store revenues)")
    
    print("\n5. Data Archival Strategy:")
    print("  - Move data > 2 years to archive tables")
    print("  - Create summary tables for historical aggregates")
    print("  - Implement partitioning by year for large datasets")

def create_correlation_matrix():
    """Create comprehensive correlation matrix for predictive analytics"""
    print("\n" + "="*80)
    print("AI READINESS EVALUATION")
    print("="*80)
    
    # Get recent data for analysis
    recent_data = db.session.query(ScorecardTrendsData).filter(
        ScorecardTrendsData.week_ending >= datetime.now().date() - timedelta(days=365)
    ).all()
    
    if len(recent_data) < 20:
        print("\n WARNING: Insufficient data for robust AI modeling (need at least 52 weeks)")
        return
    
    print("\n AI & Predictive Analytics Readiness:")
    
    print("\n1. Available Features for ML Models:")
    print("  Time-series features:")
    print("    - Weekly revenue by store (4 features)")
    print("    - New contracts by store (4 features)")
    print("    - Reservation pipeline (8 features)")
    print("    - AR aging metrics (2 features)")
    print("    - Seasonal indicators (week number)")
    
    print("\n2. Potential Target Variables:")
    print("  - Next week revenue (regression)")
    print("  - Contract conversion probability (classification)")
    print("  - AR default risk (classification)")
    print("  - Store performance tier (multi-class)")
    
    print("\n3. Data Quality for AI:")
    data_points = len(recent_data)
    features = 20  # Approximate feature count
    samples_per_feature = data_points / features
    
    print(f"  - Data points: {data_points}")
    print(f"  - Features available: ~{features}")
    print(f"  - Samples per feature ratio: {samples_per_feature:.1f}")
    
    if samples_per_feature < 10:
        print("  WARNING: Need more data for robust models (aim for 10+ samples/feature)")
    else:
        print("  SUCCESS: Sufficient data for initial modeling")
    
    print("\n4. Recommended ML Applications:")
    print("  - Revenue Forecasting: ARIMA or Prophet for time-series")
    print("  - Store Classification: Random Forest for performance tiers")
    print("  - Anomaly Detection: Isolation Forest for outlier detection")
    print("  - Contract Optimization: Gradient Boosting for conversion prediction")
    
    print("\n5. Data Preparation Requirements:")
    print("  - Handle missing values (imputation strategy needed)")
    print("  - Create lag features (previous 4 weeks)")
    print("  - Generate rolling statistics (3-week, 13-week averages)")
    print("  - Encode categorical variables (store codes)")
    print("  - Normalize numerical features for neural networks")

def generate_sql_examples():
    """Generate SQL queries for implementation"""
    print("\n" + "="*80)
    print("IMPLEMENTATION SQL QUERIES")
    print("="*80)
    
    print("\n-- 1. Create Store Master Table")
    print("""
CREATE TABLE store_location_master (
    store_code VARCHAR(10) PRIMARY KEY,
    store_name VARCHAR(100) NOT NULL,
    region VARCHAR(50),
    market_type VARCHAR(20),
    square_footage DECIMAL(10,2),
    employee_count INTEGER,
    opened_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert store data
INSERT INTO store_location_master (store_code, store_name, region, market_type) VALUES
('3607', 'Wayzata', 'West Metro', 'Suburban'),
('6800', 'Brooklyn Park', 'North Metro', 'Suburban'),
('728', 'Elk River', 'North', 'Rural'),
('8101', 'Fridley', 'North Metro', 'Urban');
""")
    
    print("\n-- 2. Create Materialized View for Analytics")
    print("""
CREATE MATERIALIZED VIEW mv_weekly_store_performance AS
SELECT 
    s.week_ending,
    s.week_number,
    -- Store performance metrics
    COALESCE(s.revenue_3607, 0) as wayzata_revenue,
    COALESCE(s.revenue_6800, 0) as brooklyn_park_revenue,
    COALESCE(s.revenue_728, 0) as elk_river_revenue,
    COALESCE(s.revenue_8101, 0) as fridley_revenue,
    -- Calculated metrics
    (COALESCE(s.revenue_3607,0) + COALESCE(s.revenue_6800,0) + 
     COALESCE(s.revenue_728,0) + COALESCE(s.revenue_8101,0)) as calculated_total,
    -- Risk indicators
    CASE 
        WHEN s.ar_over_45_days_percent > 20 THEN 'HIGH'
        WHEN s.ar_over_45_days_percent > 10 THEN 'MEDIUM'
        ELSE 'LOW'
    END as ar_risk_level
FROM scorecard_trends_data s
ORDER BY s.week_ending DESC;
""")
    
    print("\n-- 3. Correlation Analysis Query")
    print("""
-- Find correlations between contracts and revenue
WITH store_metrics AS (
    SELECT 
        week_ending,
        revenue_3607 as revenue,
        new_contracts_3607 as contracts,
        '3607' as store_code
    FROM scorecard_trends_data
    WHERE revenue_3607 > 0 AND new_contracts_3607 > 0
    
    UNION ALL
    
    SELECT 
        week_ending,
        revenue_6800,
        new_contracts_6800,
        '6800'
    FROM scorecard_trends_data
    WHERE revenue_6800 > 0 AND new_contracts_6800 > 0
)
SELECT 
    store_code,
    COUNT(*) as data_points,
    AVG(revenue / NULLIF(contracts, 0)) as avg_contract_value
FROM store_metrics
GROUP BY store_code;
""")

def main():
    """Run comprehensive correlation analysis"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*80)
        print(" SCORECARD DATA CORRELATION ANALYSIS REPORT")
        print(" Generated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("="*80)
        
        # Run analysis modules
        if analyze_data_quality():
            analyze_correlations()
            identify_integration_opportunities()
            suggest_database_optimizations()
            create_correlation_matrix()
            generate_sql_examples()
            
            print("\n" + "="*80)
            print("ACTIONABLE NEXT STEPS")
            print("="*80)
            
            print("\n Priority 1 (Immediate):")
            print("  1. Fix data quality issues (duplicates, nulls)")
            print("  2. Add unique constraints to prevent duplicates")
            print("  3. Implement data validation checks")
            
            print("\n Priority 2 (This Week):")
            print("  1. Create store master table and relationships")
            print("  2. Build materialized views for performance")
            print("  3. Integrate scorecard data into executive dashboard")
            
            print("\n Priority 3 (This Month):")
            print("  1. Develop predictive models for revenue forecasting")
            print("  2. Implement automated anomaly detection")
            print("  3. Create comprehensive BI dashboard suite")
            
            print("\n" + "="*80)
            print(" END OF REPORT")
            print("="*80)
        else:
            print("\n ERROR: No scorecard data found. Please import data first.")

if __name__ == "__main__":
    main()
