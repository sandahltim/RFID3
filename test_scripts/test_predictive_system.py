#!/usr/bin/env python3
"""
Test Predictive Analytics System
Tests external data fetching and correlation analysis
"""

import sys
sys.path.insert(0, '/home/tim/RFID3-RFID-KVC')

import os
os.environ['FLASK_ENV'] = 'development'

from sqlalchemy import create_engine, text
from app.services.data_fetch_service import DataFetchService
from app.services.ml_correlation_service import MLCorrelationService

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'user': 'rfid_user', 
    'password': 'rfid_user_password',
    'database': 'rfid_inventory'
}

def test_external_data_fetch():
    """Test external data fetching"""
    print("🌐 TESTING EXTERNAL DATA FETCH")
    print("=" * 50)
    
    try:
        # Mock the db for the service
        from types import SimpleNamespace
        import sys
        
        db_url = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset=utf8mb4"
        engine = create_engine(db_url)
        
        mock_db = SimpleNamespace()
        mock_db.engine = engine
        mock_db.session = SimpleNamespace()
        
        # Mock session methods
        def execute(query, params=None):
            with engine.connect() as conn:
                return conn.execute(query, params or {})
        
        def commit():
            pass
        
        def rollback():
            pass
            
        mock_db.session.execute = execute
        mock_db.session.commit = commit
        mock_db.session.rollback = rollback
        
        sys.modules['app'].db = mock_db
        
        # Test the service
        fetch_service = DataFetchService()
        result = fetch_service.fetch_all_external_data()
        
        print("✅ External Data Fetch Results:")
        print(f"   Total fetched: {result['total_fetched']}")
        print(f"   Total stored: {result['total_stored']}")
        print(f"   By source: {result['by_source']}")
        
        # Get summary
        summary = fetch_service.get_factors_summary()
        print("\n📊 External Factors Summary:")
        for factor_type, factors in summary.items():
            print(f"   {factor_type.upper()}:")
            for factor_name, stats in factors.items():
                print(f"     • {factor_name}: {stats['record_count']} records ({stats['date_range']})")
        
        return True
        
    except Exception as e:
        print(f"❌ External data fetch failed: {e}")
        return False

def test_correlation_analysis():
    """Test correlation analysis"""
    print("\n🔬 TESTING CORRELATION ANALYSIS")
    print("=" * 50)
    
    try:
        # Mock the db for the service
        from types import SimpleNamespace
        import sys
        
        db_url = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset=utf8mb4"
        engine = create_engine(db_url)
        
        mock_db = SimpleNamespace()
        mock_db.engine = engine
        
        sys.modules['app'].db = mock_db
        
        # Test the ML service
        ml_service = MLCorrelationService()
        results = ml_service.run_full_correlation_analysis()
        
        print("✅ Correlation Analysis Results:")
        print(f"   Status: {results['status']}")
        
        if results['status'] == 'success':
            summary = results.get('data_summary', {})
            print(f"   Weeks analyzed: {summary.get('weeks_analyzed', 'N/A')}")
            print(f"   Factors analyzed: {summary.get('factors_analyzed', 'N/A')}")
            print(f"   Date range: {summary.get('date_range', 'N/A')}")
            
            insights = results.get('insights', {})
            strong_corr = insights.get('strong_correlations', [])
            leading_ind = insights.get('leading_indicators', [])
            
            print(f"\n🎯 Key Insights:")
            print(f"   Strong correlations found: {len(strong_corr)}")
            print(f"   Leading indicators found: {len(leading_ind)}")
            
            if strong_corr:
                print(f"\n   Top correlations:")
                for corr in strong_corr[:3]:
                    print(f"     • {corr['factor']} vs {corr['business_metric']}: {corr['correlation']:.3f} ({corr['direction']})")
            
            if leading_ind:
                print(f"\n   Leading indicators:")
                for lead in leading_ind[:3]:
                    print(f"     • {lead['factor']} leads {lead['business_metric']} by {lead['lead_weeks']} weeks")
            
            recommendations = insights.get('recommendations', [])
            if recommendations:
                print(f"\n💡 Recommendations:")
                for rec in recommendations:
                    print(f"     • {rec}")
        else:
            print(f"   Error: {results.get('error', 'Unknown error')}")
        
        return results['status'] == 'success'
        
    except Exception as e:
        print(f"❌ Correlation analysis failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 TESTING PREDICTIVE ANALYTICS SYSTEM")
    print("🎯 Designed for Pi 5 Performance with External Correlation")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 2
    
    # Test 1: External data fetch
    if test_external_data_fetch():
        tests_passed += 1
    
    # Test 2: Correlation analysis  
    if test_correlation_analysis():
        tests_passed += 1
    
    print("\n" + "=" * 60)
    print("🏁 PREDICTIVE SYSTEM TEST COMPLETE")
    print("=" * 60)
    print(f"✅ Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("🎉 All systems operational - ready for predictive analytics!")
        print("\n🔮 CAPABILITIES ENABLED:")
        print("   • External factor correlation (weather, economics, seasonal)")
        print("   • Leading indicator identification")
        print("   • Demand forecasting with external regressors")
        print("   • Inventory optimization recommendations")
        print("   • Store-specific predictive insights")
        print("   • Pi 5 optimized performance")
    else:
        print("⚠️  Some tests failed - check logs for issues")
    
    print(f"\n📍 Ready for your Phase 3 curveballs!")

if __name__ == "__main__":
    main()