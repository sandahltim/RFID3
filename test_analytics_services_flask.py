#!/usr/bin/env python3
"""
Comprehensive Analytics Services Testing within Flask Context
Tests all 5 core analytics services for KVC Companies equipment rental
"""

import sys
import traceback
from datetime import datetime, timedelta
from app import create_app, db

def test_flask_analytics_services():
    """Test all analytics services within Flask application context"""
    
    print("=" * 80)
    print("COMPREHENSIVE ANALYTICS SERVICES TESTING - FLASK CONTEXT")
    print("=" * 80)
    
    app = create_app()
    results = {}
    
    with app.app_context():
        print(f"✅ Flask app context established at {datetime.now()}")
        
        # Test 1: Multi-Store Analytics Service
        print("\n🔍 Testing Multi-Store Analytics Service...")
        try:
            from app.services.multi_store_analytics_service import MultiStoreAnalyticsService
            multi_store = MultiStoreAnalyticsService()
            
            # Test regional demand analysis
            regional_data = multi_store.analyze_regional_demand_patterns(30)  # 30 days
            print(f"✅ Regional demand analysis: Generated analysis")
            print(f"   Data keys: {list(regional_data.keys()) if regional_data else 'None'}")
            
            results['multi_store_analytics'] = 'PASS'
            
        except Exception as e:
            print(f"❌ Multi-Store Analytics failed: {str(e)}")
            results['multi_store_analytics'] = f'FAIL: {str(e)}'
            
        # Test 2: Financial Analytics Service  
        print("\n💰 Testing Financial Analytics Service...")
        try:
            from app.services.financial_analytics_service import FinancialAnalyticsService
            financial = FinancialAnalyticsService()
            
            # Test rolling averages
            rolling_data = financial.calculate_rolling_averages('revenue', 4)  # 4 weeks
            print(f"✅ Rolling averages calculation: Generated analysis")
            
            # Test executive dashboard
            dashboard_data = financial.get_executive_financial_dashboard()
            print(f"✅ Executive dashboard: {len(dashboard_data) if dashboard_data else 0} metrics")
            
            results['financial_analytics'] = 'PASS'
            
        except Exception as e:
            print(f"❌ Financial Analytics failed: {str(e)}")
            results['financial_analytics'] = f'FAIL: {str(e)}'
            
        # Test 3: Business Analytics Service
        print("\n📊 Testing Business Analytics Service...")
        try:
            from app.services.business_analytics_service import BusinessAnalyticsService
            business = BusinessAnalyticsService()
            
            # Test equipment utilization analytics
            equipment_data = business.calculate_equipment_utilization_analytics()
            print(f"✅ Equipment utilization: Generated analytics")
            
            # Test customer analytics
            customer_data = business.calculate_customer_analytics()
            print(f"✅ Customer analytics: Generated insights")
            
            # Test executive dashboard
            exec_data = business.generate_executive_dashboard_metrics()
            print(f"✅ Executive dashboard metrics: Generated")
            
            results['business_analytics'] = 'PASS'
            
        except Exception as e:
            print(f"❌ Business Analytics failed: {str(e)}")
            results['business_analytics'] = f'FAIL: {str(e)}'
            
        # Test 4: Equipment Categorization Service
        print("\n🔧 Testing Equipment Categorization Service...")
        try:
            from app.services.equipment_categorization_service import EquipmentCategorizationService
            equipment = EquipmentCategorizationService()
            
            # Test inventory mix analysis
            inventory_data = equipment.analyze_inventory_mix()
            print(f"✅ Inventory mix analysis: Generated")
            
            # Test seasonal demand
            seasonal_data = equipment.get_seasonal_equipment_demand('current')
            print(f"✅ Seasonal demand analysis: Generated")
            
            results['equipment_categorization'] = 'PASS'
            
        except Exception as e:
            print(f"❌ Equipment Categorization failed: {str(e)}")
            results['equipment_categorization'] = f'FAIL: {str(e)}'
            
        # Test 5: Minnesota Industry Analytics
        print("\n🏔️ Testing Minnesota Industry Analytics Service...")
        try:
            from app.services.minnesota_industry_analytics import MinnesotaIndustryAnalytics
            minnesota = MinnesotaIndustryAnalytics()
            
            # Test store industry comparison
            store_comparison = minnesota.compare_stores_by_industry()
            print(f"✅ Store industry comparison: Generated")
            
            # Test specific store analysis (use first available store)
            store_analysis = minnesota.analyze_store_industry_mix('3607')  # Wayzata store
            print(f"✅ Store industry mix analysis: Generated")
            
            results['minnesota_industry'] = 'PASS'
            
        except Exception as e:
            print(f"❌ Minnesota Industry Analytics failed: {str(e)}")
            results['minnesota_industry'] = f'FAIL: {str(e)}'
    
    # Results Summary
    print("\n" + "=" * 80)
    print("ANALYTICS SERVICES TEST RESULTS")
    print("=" * 80)
    
    passed = sum(1 for result in results.values() if result == 'PASS')
    total = len(results)
    
    for service, result in results.items():
        status_icon = "✅" if result == 'PASS' else "❌"
        print(f"{status_icon} {service.replace('_', ' ').title()}: {result}")
    
    print(f"\n📊 Overall Score: {passed}/{total} services passed")
    
    if passed == total:
        print("🎉 ALL ANALYTICS SERVICES PASSED!")
        return True
    else:
        print("⚠️  Some services failed - see details above")
        return False

if __name__ == "__main__":
    success = test_flask_analytics_services()
    sys.exit(0 if success else 1)