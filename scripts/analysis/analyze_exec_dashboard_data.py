#!/usr/bin/env python3
"""
Executive Dashboard Data Analysis
Analyze current data and identify calculation errors
"""

import sys
import os
sys.path.append('/home/tim/RFID3')

from app import create_app
from app.models.db_models import PayrollTrends, ScorecardTrends, ExecutiveKPI
from app.config.stores import STORE_MAPPING, STORES
from app import db
from sqlalchemy import func
from datetime import datetime

def main():
    app = create_app()
    with app.app_context():
        print("=== EXECUTIVE DASHBOARD DATA ANALYSIS ===\n")
        
        # 1. Check PayrollTrends data
        print("1. PAYROLL TRENDS DATA:")
        print("-" * 40)
        
        # Total records
        total_records = PayrollTrends.query.count()
        print(f"Total PayrollTrends records: {total_records}")
        
        # Store distribution
        print("\nStore Distribution:")
        stores = db.session.query(
            PayrollTrends.store_id, 
            func.count(PayrollTrends.id),
            func.sum(PayrollTrends.total_revenue),
            func.sum(PayrollTrends.payroll_cost)
        ).group_by(PayrollTrends.store_id).all()
        
        for store_id, count, total_rev, total_payroll in stores:
            store_name = STORE_MAPPING.get(store_id, f"Unknown({store_id})")
            print(f"  {store_id} ({store_name}): {count} records, Revenue: ${total_rev or 0:,.2f}, Payroll: ${total_payroll or 0:,.2f}")
        
        # Date range
        print("\nDate Range:")
        date_range = db.session.query(
            func.min(PayrollTrends.week_ending), 
            func.max(PayrollTrends.week_ending)
        ).first()
        print(f"  Data from {date_range[0]} to {date_range[1]}")
        
        # Sample recent data
        print("\nRecent Data (Last 5 records):")
        recent = PayrollTrends.query.order_by(PayrollTrends.week_ending.desc()).limit(5).all()
        for trend in recent:
            store_name = STORE_MAPPING.get(trend.store_id, f"Unknown({trend.store_id})")
            print(f"  {trend.week_ending} | {trend.store_id} ({store_name}) | Rev: ${trend.total_revenue or 0:,.2f} | Pay: ${trend.payroll_cost or 0:,.2f} | Eff: {trend.labor_efficiency_ratio or 0:.2f}%")
        
        # 2. Check ScorecardTrends data
        print("\n2. SCORECARD TRENDS DATA:")
        print("-" * 40)
        
        scorecard_records = ScorecardTrends.query.count()
        print(f"Total ScorecardTrends records: {scorecard_records}")
        
        if scorecard_records > 0:
            scorecard_stores = db.session.query(
                ScorecardTrends.store_id, 
                func.count(ScorecardTrends.id)
            ).group_by(ScorecardTrends.store_id).all()
            
            print("Store Distribution:")
            for store_id, count in scorecard_stores:
                store_name = STORE_MAPPING.get(store_id, f"Unknown({store_id})")
                print(f"  {store_id} ({store_name}): {count} records")
        
        # 3. Check ExecutiveKPI data
        print("\n3. EXECUTIVE KPI DATA:")
        print("-" * 40)
        
        kpi_records = ExecutiveKPI.query.count()
        print(f"Total ExecutiveKPI records: {kpi_records}")
        
        if kpi_records > 0:
            kpis = ExecutiveKPI.query.all()
            for kpi in kpis:
                print(f"  {kpi.kpi_name} ({kpi.kpi_category}): Current: {kpi.current_value}, Target: {kpi.target_value}")
        
        # 4. Analyze calculation issues
        print("\n4. CALCULATION ANALYSIS:")
        print("-" * 40)
        
        # Check for zero/null revenue records
        zero_revenue = PayrollTrends.query.filter(
            (PayrollTrends.total_revenue == 0) | (PayrollTrends.total_revenue.is_(None))
        ).count()
        print(f"Records with zero/null revenue: {zero_revenue}")
        
        # Check for invalid efficiency ratios
        invalid_efficiency = PayrollTrends.query.filter(
            PayrollTrends.labor_efficiency_ratio > 100
        ).count()
        print(f"Records with efficiency > 100%: {invalid_efficiency}")
        
        # Check for mismatched calculations
        print("\nChecking calculation accuracy...")
        calculation_errors = 0
        sample_records = PayrollTrends.query.filter(
            PayrollTrends.total_revenue > 0,
            PayrollTrends.payroll_cost > 0
        ).limit(20).all()
        
        for record in sample_records:
            if record.total_revenue and record.payroll_cost and record.labor_efficiency_ratio:
                expected_efficiency = float(record.payroll_cost / record.total_revenue) * 100
                actual_efficiency = float(record.labor_efficiency_ratio)
                
                if abs(expected_efficiency - actual_efficiency) > 1.0:  # Allow 1% tolerance
                    calculation_errors += 1
                    print(f"  ERROR: Week {record.week_ending}, Store {record.store_id}")
                    print(f"    Expected efficiency: {expected_efficiency:.2f}%, Stored: {actual_efficiency:.2f}%")
        
        if calculation_errors == 0:
            print("  All sampled efficiency calculations appear correct")
        else:
            print(f"  Found {calculation_errors} calculation errors in sample")
        
        # 5. Store mapping verification
        print("\n5. STORE MAPPING VERIFICATION:")
        print("-" * 40)
        
        db_stores = db.session.query(PayrollTrends.store_id).distinct().all()
        db_store_ids = [s[0] for s in db_stores]
        
        print("Configured stores in STORE_MAPPING:")
        for store_id, name in STORE_MAPPING.items():
            status = "✓ HAS DATA" if store_id in db_store_ids else "✗ NO DATA"
            print(f"  {store_id}: {name} - {status}")
        
        print("\nStores in database not in configuration:")
        for store_id in db_store_ids:
            if store_id not in STORE_MAPPING:
                print(f"  {store_id}: Unknown store (not configured)")
        
        # 6. Business logic verification
        print("\n6. BUSINESS LOGIC VERIFICATION:")
        print("-" * 40)
        
        print("Expected store characteristics based on user requirements:")
        expected_stores = {
            "3607": "Wayzata (A1 Rent It - 90% DIY/10% Events)",
            "6800": "Brooklyn Park (A1 Rent It - 100% Construction)",
            "728": "Elk River (A1 Rent It - 90% DIY/10% Events)",
            "8101": "Fridley (Broadway Tent & Event - 100% Events)"
        }
        
        for store_id, description in expected_stores.items():
            if store_id in STORE_MAPPING:
                configured_name = STORE_MAPPING[store_id]
                print(f"  {store_id}: Expected: {description}")
                print(f"        Configured: {configured_name}")
                if store_id in db_store_ids:
                    # Get recent revenue data for this store
                    recent_data = PayrollTrends.query.filter(
                        PayrollTrends.store_id == store_id,
                        PayrollTrends.total_revenue > 0
                    ).order_by(PayrollTrends.week_ending.desc()).limit(4).all()
                    
                    if recent_data:
                        avg_revenue = sum(r.total_revenue for r in recent_data) / len(recent_data)
                        print(f"        Recent avg revenue: ${avg_revenue:,.2f}")
                    else:
                        print(f"        No recent revenue data")
                else:
                    print(f"        ✗ NO DATA IN DATABASE")
                print()

if __name__ == "__main__":
    main()