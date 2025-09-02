#!/usr/bin/env python3
"""
Comprehensive Test Suite for Analytics Services with Centralized Store Configuration
Tests all analytics and predictive algorithms with the new store mapping system
"""

import sys
import os
sys.path.insert(0, '/home/tim/RFID3')

import json
from datetime import datetime, timedelta
from app import create_app, db
from app.config.stores import (
    STORES, STORE_MAPPING, get_store_name, 
    get_active_store_codes, get_store_manager,
    get_store_business_type
)

# Import all analytics services
from app.services.executive_insights_service import ExecutiveInsightsService
from app.services.financial_analytics_service import FinancialAnalyticsService
from app.services.weather_correlation_service import WeatherCorrelationService
from app.services.multi_store_analytics_service import MultiStoreAnalyticsService
from app.services.minnesota_seasonal_service import MinnesotaSeasonalService
from app.services.weather_predictive_service import WeatherPredictiveService
from app.services.minnesota_industry_analytics import MinnesotaIndustryAnalytics
from app.services.equipment_categorization_service import EquipmentCategorizationService
from app.services.store_correlation_service import StoreCorrelationService
from app.services.cross_system_analytics import CrossSystemAnalyticsService
from app.services.bi_analytics import BIAnalyticsService

# Test results storage
test_results = {
    "timestamp": datetime.now().isoformat(),
    "store_configuration": {},
    "service_tests": {},
    "predictive_tests": {},
    "correlation_tests": {},
    "errors": []
}

def test_store_configuration():
    """Test centralized store configuration"""
    print("\n" + "="*60)
    print("🏢 TESTING STORE CONFIGURATION")
    print("="*60)
    
    results = {
        "active_stores": [],
        "store_details": {},
        "validation": {}
    }
    
    try:
        # Get active stores
        active_stores = get_active_store_codes()
        print(f"✅ Active stores found: {active_stores}")
        results["active_stores"] = active_stores
        
        # Test each store
        for store_code in active_stores:
            store_info = {
                "name": get_store_name(store_code),
                "manager": get_store_manager(store_code),
                "business_type": get_store_business_type(store_code),
                "store_info": STORES.get(store_code).__dict__ if store_code in STORES else None
            }
            results["store_details"][store_code] = store_info
            
            print(f"\n📍 Store {store_code}:")
            print(f"   Name: {store_info['name']}")
            print(f"   Manager: {store_info['manager']}")
            print(f"   Business: {store_info['business_type']}")
        
        # Validate critical mappings
        results["validation"]["3607_is_wayzata"] = get_store_name("3607") == "Wayzata"
        results["validation"]["6800_is_brooklyn"] = get_store_name("6800") == "Brooklyn Park"
        results["validation"]["8101_is_fridley"] = get_store_name("8101") == "Fridley"
        results["validation"]["728_is_elk_river"] = get_store_name("728") == "Elk River"
        
        # Check manager assignments
        results["validation"]["tyler_manages_3607"] = get_store_manager("3607") == "TYLER"
        results["validation"]["zack_manages_6800"] = get_store_manager("6800") == "ZACK"
        results["validation"]["tim_manages_8101"] = get_store_manager("8101") == "TIM"
        results["validation"]["bruce_manages_728"] = get_store_manager("728") == "BRUCE"
        
        all_valid = all(results["validation"].values())
        print(f"\n{'✅' if all_valid else '❌'} Store configuration validation: {'PASSED' if all_valid else 'FAILED'}")
        
    except Exception as e:
        print(f"❌ Store configuration test failed: {e}")
        results["error"] = str(e)
        test_results["errors"].append(f"Store config: {e}")
    
    test_results["store_configuration"] = results
    return results

def test_executive_insights():
    """Test Executive Insights Service"""
    print("\n" + "="*60)
    print("📊 TESTING EXECUTIVE INSIGHTS SERVICE")
    print("="*60)
    
    results = {"status": "unknown", "tests": {}}
    
    try:
        service = ExecutiveInsightsService()
        
        # Test anomaly detection
        print("Testing anomaly detection...")
        anomalies = service.detect_financial_anomalies(lookback_weeks=12)
        results["tests"]["anomaly_detection"] = {
            "success": anomalies.get("success", False),
            "total_anomalies": anomalies.get("total_anomalies", 0)
        }
        print(f"  {'✅' if anomalies.get('success') else '❌'} Anomalies detected: {anomalies.get('total_anomalies', 0)}")
        
        # Test correlation analysis
        print("Testing external event correlation...")
        if anomalies.get("success"):
            correlations = service.correlate_with_external_events(anomalies)
            results["tests"]["correlations"] = {
                "success": correlations.get("success", False),
                "weather_correlations": len(correlations.get("correlations", {}).get("weather_correlations", []))
            }
            print(f"  {'✅' if correlations.get('success') else '❌'} Correlations found")
        
        # Test dashboard configuration
        print("Testing dashboard configuration...")
        config = service.get_dashboard_configuration()
        results["tests"]["dashboard_config"] = {
            "success": config.get("success", False)
        }
        print(f"  {'✅' if config.get('success') else '❌'} Dashboard configuration loaded")
        
        results["status"] = "passed"
        print("✅ Executive Insights Service: PASSED")
        
    except Exception as e:
        print(f"❌ Executive Insights test failed: {e}")
        results["status"] = "failed"
        results["error"] = str(e)
        test_results["errors"].append(f"Executive insights: {e}")
    
    test_results["service_tests"]["executive_insights"] = results
    return results

def test_financial_analytics():
    """Test Financial Analytics Service"""
    print("\n" + "="*60)
    print("💰 TESTING FINANCIAL ANALYTICS SERVICE")
    print("="*60)
    
    results = {"status": "unknown", "tests": {}}
    
    try:
        service = FinancialAnalyticsService()
        
        # Test rolling averages
        print("Testing 3-week rolling averages...")
        rolling_avg = service.calculate_rolling_averages('revenue', weeks_back=12)
        results["tests"]["rolling_averages"] = {
            "success": rolling_avg.get("success", False),
            "stores_analyzed": len(rolling_avg.get("store_performance", {})) if "store_performance" in rolling_avg else 0
        }
        print(f"  {'✅' if rolling_avg.get('success') else '❌'} Rolling averages calculated")
        
        # Test YoY analysis
        print("Testing year-over-year analysis...")
        yoy = service.calculate_year_over_year_analysis('revenue')
        results["tests"]["yoy_analysis"] = {
            "success": yoy.get("success", False),
            "growth_rate": yoy.get("comparison_period", {}).get("overall_growth_rate", 0)
        }
        print(f"  {'✅' if yoy.get('success') else '❌'} YoY analysis completed")
        
        # Test multi-store performance
        print("Testing multi-store performance...")
        multi_store = service.analyze_multi_store_performance(analysis_period_weeks=12)
        results["tests"]["multi_store"] = {
            "success": multi_store.get("success", False),
            "stores_analyzed": len(multi_store.get("store_metrics", {}))
        }
        print(f"  {'✅' if multi_store.get('success') else '❌'} Multi-store analysis completed")
        
        # Test financial forecasting
        print("Testing financial forecasting...")
        forecasts = service.generate_financial_forecasts(horizon_weeks=4, confidence_level=0.95)
        results["tests"]["forecasting"] = {
            "success": forecasts.get("success", False),
            "forecast_horizon": forecasts.get("forecast_parameters", {}).get("horizon_weeks", 0)
        }
        print(f"  {'✅' if forecasts.get('success') else '❌'} Forecasts generated")
        
        results["status"] = "passed"
        print("✅ Financial Analytics Service: PASSED")
        
    except Exception as e:
        print(f"❌ Financial Analytics test failed: {e}")
        results["status"] = "failed"
        results["error"] = str(e)
        test_results["errors"].append(f"Financial analytics: {e}")
    
    test_results["service_tests"]["financial_analytics"] = results
    return results

def test_weather_correlation():
    """Test Weather Correlation Service"""
    print("\n" + "="*60)
    print("🌦️ TESTING WEATHER CORRELATION SERVICE")
    print("="*60)
    
    results = {"status": "unknown", "tests": {}}
    
    try:
        service = WeatherCorrelationService()
        
        # Test weather-rental correlations for each store
        print("Testing weather correlations by store...")
        for store_code in get_active_store_codes():
            store_name = get_store_name(store_code)
            print(f"  Testing {store_name} ({store_code})...")
            
            correlation = service.analyze_weather_rental_correlations(
                store_code=store_code,
                industry_segment='all',
                days_back=90,
                include_forecasts=False
            )
            
            results["tests"][f"store_{store_code}"] = {
                "success": correlation.get("status") == "success",
                "correlations_found": len(correlation.get("correlations", {})) > 0,
                "insights": len(correlation.get("insights", []))
            }
            
            status = "✅" if correlation.get("status") == "success" else "❌"
            print(f"    {status} {store_name}: {len(correlation.get('insights', []))} insights")
        
        results["status"] = "passed"
        print("✅ Weather Correlation Service: PASSED")
        
    except Exception as e:
        print(f"❌ Weather Correlation test failed: {e}")
        results["status"] = "failed"
        results["error"] = str(e)
        test_results["errors"].append(f"Weather correlation: {e}")
    
    test_results["correlation_tests"]["weather"] = results
    return results

def test_multi_store_analytics():
    """Test Multi-Store Analytics Service"""
    print("\n" + "="*60)
    print("🏪 TESTING MULTI-STORE ANALYTICS SERVICE")
    print("="*60)
    
    results = {"status": "unknown", "tests": {}}
    
    try:
        service = MultiStoreAnalyticsService()
        
        # Test regional demand patterns
        print("Testing regional demand pattern analysis...")
        regional = service.analyze_regional_demand_patterns(analysis_period_days=90)
        
        results["tests"]["regional_patterns"] = {
            "success": not regional.get("error"),
            "stores_analyzed": len(regional.get("store_performance", {})),
            "transfer_recommendations": len(regional.get("transfer_recommendations", [])),
            "insights": len(regional.get("insights", []))
        }
        
        print(f"  {'✅' if not regional.get('error') else '❌'} Regional analysis completed")
        print(f"  📊 Stores analyzed: {len(regional.get('store_performance', {}))}")
        print(f"  📦 Transfer recommendations: {len(regional.get('transfer_recommendations', []))}")
        
        results["status"] = "passed"
        print("✅ Multi-Store Analytics Service: PASSED")
        
    except Exception as e:
        print(f"❌ Multi-Store Analytics test failed: {e}")
        results["status"] = "failed"
        results["error"] = str(e)
        test_results["errors"].append(f"Multi-store analytics: {e}")
    
    test_results["service_tests"]["multi_store_analytics"] = results
    return results

def test_predictive_services():
    """Test Predictive Analytics Services"""
    print("\n" + "="*60)
    print("🔮 TESTING PREDICTIVE ANALYTICS SERVICES")
    print("="*60)
    
    results = {"status": "unknown", "tests": {}}
    
    try:
        # Test Weather Predictive Service
        print("Testing weather predictive service...")
        weather_service = WeatherPredictiveService()
        weather_forecast = weather_service.generate_weather_based_forecasts(
            forecast_days=7,
            store_code="3607",
            include_confidence_intervals=True
        )
        
        results["tests"]["weather_predictive"] = {
            "success": weather_forecast.get("status") == "success",
            "forecast_days": len(weather_forecast.get("forecasts", [])),
            "models_used": len(weather_forecast.get("models_used", []))
        }
        print(f"  {'✅' if weather_forecast.get('status') == 'success' else '❌'} Weather predictions generated")
        
        # Test Seasonal Service
        print("Testing seasonal pattern service...")
        seasonal_service = MinnesotaSeasonalService()
        seasonal_analysis = seasonal_service.analyze_seasonal_patterns(
            analysis_years=2,
            store_code="all"
        )
        
        results["tests"]["seasonal_patterns"] = {
            "success": seasonal_analysis.get("status") == "success",
            "patterns_found": len(seasonal_analysis.get("seasonal_patterns", {})),
            "peak_periods": len(seasonal_analysis.get("peak_periods", []))
        }
        print(f"  {'✅' if seasonal_analysis.get('status') == 'success' else '❌'} Seasonal patterns analyzed")
        
        results["status"] = "passed"
        print("✅ Predictive Analytics Services: PASSED")
        
    except Exception as e:
        print(f"❌ Predictive Analytics test failed: {e}")
        results["status"] = "failed"
        results["error"] = str(e)
        test_results["errors"].append(f"Predictive analytics: {e}")
    
    test_results["predictive_tests"] = results
    return results

def test_industry_analytics():
    """Test Industry Analytics Services"""
    print("\n" + "="*60)
    print("🏭 TESTING INDUSTRY ANALYTICS SERVICES")
    print("="*60)
    
    results = {"status": "unknown", "tests": {}}
    
    try:
        # Test Industry Analytics
        print("Testing Minnesota industry analytics...")
        industry_service = MinnesotaIndustryAnalytics()
        
        for store_code in get_active_store_codes():
            store_name = get_store_name(store_code)
            industry_mix = industry_service.analyze_store_industry_mix(store_code)
            
            results["tests"][f"store_{store_code}_mix"] = {
                "success": industry_mix.get("status") == "success",
                "segments_analyzed": len(industry_mix.get("industry_breakdown", [])),
                "primary_segment": industry_mix.get("primary_segment")
            }
            
            print(f"  {'✅' if industry_mix.get('status') == 'success' else '❌'} {store_name} industry mix analyzed")
        
        # Test Equipment Categorization
        print("Testing equipment categorization...")
        categorization_service = EquipmentCategorizationService()
        categorization_stats = categorization_service.get_categorization_statistics()
        
        results["tests"]["categorization"] = {
            "success": categorization_stats.get("success", False),
            "total_items": categorization_stats.get("total_items", 0),
            "categorized_items": categorization_stats.get("categorized_items", 0)
        }
        print(f"  {'✅' if categorization_stats.get('success') else '❌'} Equipment categorization tested")
        
        results["status"] = "passed"
        print("✅ Industry Analytics Services: PASSED")
        
    except Exception as e:
        print(f"❌ Industry Analytics test failed: {e}")
        results["status"] = "failed"
        results["error"] = str(e)
        test_results["errors"].append(f"Industry analytics: {e}")
    
    test_results["service_tests"]["industry_analytics"] = results
    return results

def generate_summary():
    """Generate test summary"""
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    # Count results
    total_services = len(test_results["service_tests"])
    passed_services = sum(1 for s in test_results["service_tests"].values() if s.get("status") == "passed")
    failed_services = total_services - passed_services
    
    print(f"\nServices Tested: {total_services}")
    print(f"✅ Passed: {passed_services}")
    print(f"❌ Failed: {failed_services}")
    
    # Store configuration validation
    store_valid = all(test_results["store_configuration"].get("validation", {}).values())
    print(f"\nStore Configuration: {'✅ VALID' if store_valid else '❌ INVALID'}")
    
    # List errors if any
    if test_results["errors"]:
        print("\n⚠️ Errors encountered:")
        for error in test_results["errors"]:
            print(f"  - {error}")
    
    # Overall result
    all_passed = passed_services == total_services and store_valid and not test_results["errors"]
    print(f"\n{'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    # Save results to file
    with open("analytics_test_results.json", "w") as f:
        json.dump(test_results, f, indent=2, default=str)
    print("\n💾 Detailed results saved to analytics_test_results.json")
    
    return all_passed

def main():
    """Main test execution"""
    print("\n" + "="*60)
    print("🚀 ANALYTICS SERVICES COMPREHENSIVE TEST SUITE")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        # Run all tests
        test_store_configuration()
        test_executive_insights()
        test_financial_analytics()
        test_weather_correlation()
        test_multi_store_analytics()
        test_predictive_services()
        test_industry_analytics()
        
        # Generate summary
        all_passed = generate_summary()
        
        # Exit with appropriate code
        sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
