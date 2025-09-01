#!/usr/bin/env python3
"""
API Endpoints Testing for RFID3 Analytics Framework
Tests key endpoints to validate functionality and data accuracy
"""

import sys
import requests
import json
import time
from threading import Thread
from app import create_app

def start_test_server():
    """Start Flask server for testing"""
    app = create_app()
    app.run(host='127.0.0.1', port=8102, debug=False, use_reloader=False)

def test_api_endpoints():
    """Test key API endpoints"""
    
    print("=" * 80)
    print("API ENDPOINTS TESTING")
    print("=" * 80)
    
    # Start server in background
    server_thread = Thread(target=start_test_server, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    print("⏳ Starting Flask test server...")
    time.sleep(5)
    
    base_url = "http://127.0.0.1:8102"
    test_results = {}
    
    # Test endpoints (using actual registered routes)
    endpoints_to_test = [
        ("/health", "Health Check"),
        ("/api/financial/dashboard", "Financial Dashboard API"),
        ("/api/financial/executive/dashboard", "Executive Financial Dashboard API"),
        ("/api/suggestions/list", "Suggestions List API"),
        ("/api/suggestions/analytics", "Suggestions Analytics API"),
        ("/executive/api/financial-kpis", "Executive Financial KPIs API"),
        ("/", "Home Page"),
    ]
    
    for endpoint, description in endpoints_to_test:
        print(f"\n🔍 Testing {description} ({endpoint})...")
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=30)
            
            if response.status_code == 200:
                print(f"✅ {description}: SUCCESS (200)")
                if endpoint.startswith('/api/'):
                    # Try to parse JSON response
                    try:
                        json_data = response.json()
                        print(f"   Response keys: {list(json_data.keys()) if isinstance(json_data, dict) else 'Non-dict response'}")
                    except:
                        print(f"   Response length: {len(response.text)} chars")
                else:
                    print(f"   Response length: {len(response.text)} chars")
                test_results[endpoint] = 'PASS'
            else:
                print(f"❌ {description}: HTTP {response.status_code}")
                test_results[endpoint] = f'FAIL: HTTP {response.status_code}'
                
        except requests.exceptions.ConnectionError:
            print(f"❌ {description}: CONNECTION ERROR")
            test_results[endpoint] = 'FAIL: CONNECTION ERROR'
        except requests.exceptions.Timeout:
            print(f"❌ {description}: TIMEOUT")
            test_results[endpoint] = 'FAIL: TIMEOUT'
        except Exception as e:
            print(f"❌ {description}: ERROR - {str(e)}")
            test_results[endpoint] = f'FAIL: {str(e)}'
    
    # Results Summary
    print("\n" + "=" * 80)
    print("API ENDPOINTS TEST RESULTS")
    print("=" * 80)
    
    passed = sum(1 for result in test_results.values() if result == 'PASS')
    total = len(test_results)
    
    for endpoint, result in test_results.items():
        status_icon = "✅" if result == 'PASS' else "❌"
        print(f"{status_icon} {endpoint}: {result}")
    
    print(f"\n📊 Overall Score: {passed}/{total} endpoints passed")
    
    if passed == total:
        print("🎉 ALL API ENDPOINTS PASSED!")
        return True
    else:
        print("⚠️ Some endpoints failed - see details above")
        return False

if __name__ == "__main__":
    success = test_api_endpoints()
    sys.exit(0 if success else 1)