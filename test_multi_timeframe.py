#!/usr/bin/env python3
"""
Test script for multi-timeframe analytics service
"""

import sys
import os
sys.path.insert(0, '/home/tim/RFID3')

from app import create_app

def test_multi_timeframe():
    """Test the multi-timeframe analytics service"""
    app = create_app()
    
    with app.app_context():
        try:
            from app.services.multi_timeframe_analytics_service import MultiTimeframeAnalyticsService, TimeframeType, ComparisonType
            
            service = MultiTimeframeAnalyticsService()
            
            print("🧪 Testing Multi-Timeframe Analytics Service")
            print("=" * 50)
            
            # Test timeframe calculations
            print("\n📅 Testing Timeframe Calculations:")
            period = service.get_timeframe_dates(TimeframeType.THREE_WEEK_AVG_FORWARD)
            print(f"✅ 3-Week Forward: {period.label}")
            print(f"   Period: {period.start_date.date()} to {period.end_date.date()}")
            print(f"   Business hours: {period.business_hours_total}")
            
            # Test revenue calculation
            print("\n💰 Testing Revenue Metrics:")
            revenue_result = service.calculate_revenue_metrics(
                TimeframeType.THREE_WEEK_AVG_FORWARD,
                ComparisonType.PREVIOUS_YEAR
            )
            print(f"✅ Revenue Analysis Complete")
            print(f"   Current: ${revenue_result.current_value:,.2f}")
            print(f"   Comparison: ${revenue_result.comparison_value:,.2f}")
            print(f"   Change: {revenue_result.change_percent:+.1f}%")
            
            # Test utilization calculation
            print("\n🏭 Testing Utilization Metrics:")
            util_result = service.calculate_utilization_metrics(
                TimeframeType.THREE_WEEK_AVG_FORWARD,
                ComparisonType.PREVIOUS_YEAR
            )
            print(f"✅ Utilization Analysis Complete")
            print(f"   Current: {util_result.current_value:.1f}%")
            print(f"   Comparison: {util_result.comparison_value:.1f}%")
            print(f"   Change: {util_result.change_percent:+.1f}%")
            
            # Test comprehensive KPIs
            print("\n📊 Testing Comprehensive KPIs:")
            kpi_result = service.get_financial_kpis(
                timeframe_type="3week_avg_forward",
                comparison_type="previous_year"
            )
            
            if kpi_result.get('success'):
                print(f"✅ Comprehensive KPIs Generated")
                print(f"   Timeframe: {kpi_result['timeframe']['type']}")
                print(f"   Revenue: ${kpi_result['revenue_metrics']['current_value']:,.0f}")
                print(f"   Utilization: {kpi_result['utilization_metrics']['current_value']:.1f}%")
                print(f"   Health Score: {kpi_result['operational_health']['health_score']}")
                print(f"   12-Month YoY: {kpi_result['enhanced_analytics']['yoy_12_month_analysis']['avg_yoy_growth']:+.1f}%")
            else:
                print(f"❌ KPI Generation Failed: {kpi_result.get('error')}")
            
            print("\n✅ All tests completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = test_multi_timeframe()
    sys.exit(0 if success else 1)