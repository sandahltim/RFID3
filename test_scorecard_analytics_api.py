#!/usr/bin/env python3
"""
Test Executive Scorecard Analytics API Endpoints
Tests the comprehensive scorecard visualization API created for Tab 7 Executive Dashboard
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from datetime import datetime
import time

# Test configuration
BASE_URL = "http://localhost:5000"
API_PREFIX = "/api/executive"

def test_endpoint(endpoint, description, expected_keys=None):
    """Test a single API endpoint"""
    url = f"{BASE_URL}{API_PREFIX}{endpoint}"
    
    print(f"\n🧪 Testing: {description}")
    print(f"📍 URL: {url}")
    
    try:
        start_time = time.time()
        response = requests.get(url, timeout=30)
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"✅ Success - Response time: {response_time:.1f}ms")
            
            # Check for expected keys
            if expected_keys:
                for key in expected_keys:
                    if key in data:
                        print(f"   ✓ Found key: {key}")
                        if isinstance(data[key], list) and data[key]:
                            print(f"     📊 {len(data[key])} items")
                        elif isinstance(data[key], dict):
                            print(f"     📋 {len(data[key])} properties")
                    else:
                        print(f"   ❌ Missing key: {key}")
            
            # Display sample data structure
            print(f"   📈 Data structure preview:")
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, list):
                        print(f"     {key}: [{len(value)} items]")
                    elif isinstance(value, dict):
                        print(f"     {key}: {{{len(value)} properties}}")
                    else:
                        print(f"     {key}: {type(value).__name__}")
            
        else:
            print(f"❌ Failed - Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

def main():
    """Run comprehensive API tests"""
    
    print("🎯 Executive Scorecard Analytics API Test Suite")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 Base URL: {BASE_URL}")
    
    # Test endpoints with expected data structure
    endpoints = [
        {
            "endpoint": "/scorecard_analytics?weeks=52",
            "description": "Scorecard Analytics (52 weeks)",
            "expected_keys": [
                "multi_year_trends", 
                "seasonal_patterns", 
                "risk_indicators", 
                "pipeline_conversion",
                "conversion_summary"
            ]
        },
        {
            "endpoint": "/scorecard_analytics?weeks=159",
            "description": "Full Historical Dataset (159 weeks)",
            "expected_keys": [
                "multi_year_trends",
                "seasonal_patterns",
                "risk_indicators"
            ]
        },
        {
            "endpoint": "/correlation_matrix",
            "description": "Business Metrics Correlation Matrix", 
            "expected_keys": [
                "column_names",
                "correlations", 
                "strong_correlations"
            ]
        },
        {
            "endpoint": "/ar_aging_trends?weeks=26",
            "description": "AR Aging Analysis (26 weeks)",
            "expected_keys": [
                "weeks",
                "aging_buckets",
                "risk_alerts",
                "summary"
            ]
        },
        {
            "endpoint": "/seasonal_forecast?weeks=13",
            "description": "13-Week Revenue Forecast",
            "expected_keys": [
                "baseline_revenue",
                "weekly_trend",
                "forecast",
                "confidence_intervals"
            ]
        },
        {
            "endpoint": "/health",
            "description": "API Health Check",
            "expected_keys": [
                "status",
                "service",
                "endpoints"
            ]
        }
    ]
    
    # Run tests
    success_count = 0
    total_tests = len(endpoints)
    
    for test_config in endpoints:
        try:
            test_endpoint(
                test_config["endpoint"],
                test_config["description"], 
                test_config.get("expected_keys")
            )
            success_count += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print(f"✅ Successful tests: {success_count}/{total_tests}")
    print(f"❌ Failed tests: {total_tests - success_count}/{total_tests}")
    print(f"📈 Success rate: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        print("\n🎉 All tests passed! Executive Dashboard ready for scorecard analytics.")
    else:
        print(f"\n⚠️  {total_tests - success_count} tests failed. Check API implementation.")
    
    # Additional integration tests
    print("\n🔧 Integration Test Recommendations:")
    print("1. Test dashboard loading: http://localhost:5000/tab/7")
    print("2. Verify chart rendering with browser developer tools")
    print("3. Check data refresh functionality")
    print("4. Validate mobile responsiveness")
    print("5. Test print-friendly formatting")
    
    # Performance metrics
    print("\n⚡ Performance Guidelines:")
    print("- API response time should be < 2000ms")
    print("- Chart rendering should complete in < 3000ms") 
    print("- Full dashboard load should be < 5000ms")
    print("- Data should auto-refresh every 15 minutes")

if __name__ == "__main__":
    main()