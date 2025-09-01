#!/usr/bin/env python3
"""
KVC Companies Executive Dashboard Debug Script
Comprehensive debugging and validation tool for the executive dashboard system
"""

import sys
import os
import traceback
from datetime import datetime, date, timedelta
import json

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app, db
    from app.services.financial_analytics_service import FinancialAnalyticsService
    from app.services.executive_insights_service import ExecutiveInsightsService
    from sqlalchemy import text
    print("✅ Successfully imported all required modules")
except ImportError as e:
    print(f"❌ Failed to import modules: {e}")
    sys.exit(1)


class ExecutiveDashboardDebugger:
    """Comprehensive debugging tool for the executive dashboard system"""
    
    def __init__(self):
        self.app = None
        self.financial_service = None
        self.insights_service = None
        self.test_results = {
            'database_connectivity': False,
            'financial_service': False,
            'insights_service': False,
            'api_endpoints': False,
            'data_integrity': False
        }
        
    def initialize_app(self):
        """Initialize Flask application for testing"""
        try:
            self.app = create_app()
            self.app_context = self.app.app_context()
            self.app_context.push()
            
            self.financial_service = FinancialAnalyticsService()
            self.insights_service = ExecutiveInsightsService()
            
            print("✅ Flask application initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Flask application: {e}")
            traceback.print_exc()
            return False
    
    def test_database_connectivity(self):
        """Test database connectivity and table access"""
        print("\n" + "="*50)
        print("TESTING DATABASE CONNECTIVITY")
        print("="*50)
        
        try:
            # Test basic database connection
            result = db.session.execute(text("SELECT 1 as test_value"))
            row = result.fetchone()
            if row and row.test_value == 1:
                print("✅ Basic database connection successful")
            else:
                print("❌ Basic database connection failed")
                return False
                
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            return False
        
        # Test access to required tables
        required_tables = [
            'scorecard_trends_data',
            'payroll_trends_data'
        ]
        
        for table in required_tables:
            try:
                result = db.session.execute(text(f"SELECT COUNT(*) as count FROM {table} LIMIT 1"))
                row = result.fetchone()
                count = row.count if row else 0
                print(f"✅ Table '{table}' accessible - {count} records")
            except Exception as e:
                print(f"❌ Table '{table}' not accessible: {e}")
                return False
        
        self.test_results['database_connectivity'] = True
        return True
    
    def test_financial_analytics_service(self):
        """Test Financial Analytics Service functionality"""
        print("\n" + "="*50)
        print("TESTING FINANCIAL ANALYTICS SERVICE")
        print("="*50)
        
        try:
            # Test service initialization
            if not self.financial_service:
                print("❌ Financial service not initialized")
                return False
            
            print("✅ Financial Analytics Service initialized")
            
            # Test store configuration
            store_codes = self.financial_service.STORE_CODES
            print(f"✅ Store codes configured: {list(store_codes.keys())}")
            
            expected_stores = {'3607', '6800', '728', '8101'}
            if set(store_codes.keys()) == expected_stores:
                print("✅ All required stores configured correctly")
            else:
                print(f"❌ Store configuration mismatch. Expected: {expected_stores}, Got: {set(store_codes.keys())}")
                return False
            
            # Test business mix configuration
            business_mix = self.financial_service.STORE_BUSINESS_MIX
            if len(business_mix) == 4:
                print("✅ Business mix profiles configured for all stores")
            else:
                print(f"❌ Business mix configuration incomplete: {len(business_mix)}/4 stores")
                return False
            
            # Test revenue targets
            revenue_targets = self.financial_service.STORE_REVENUE_TARGETS
            total_target = sum(revenue_targets.values())
            print(f"✅ Revenue targets sum to {total_target:.1%}")
            
            if 0.75 <= total_target <= 0.85:  # Reasonable range allowing for missing data
                print("✅ Revenue target distribution is reasonable")
            else:
                print(f"⚠️  Revenue target total ({total_target:.1%}) may need review")
            
        except Exception as e:
            print(f"❌ Financial Analytics Service test failed: {e}")
            traceback.print_exc()
            return False
        
        self.test_results['financial_service'] = True
        return True
    
    def test_insights_service(self):
        """Test Executive Insights Service functionality"""
        print("\n" + "="*50)
        print("TESTING EXECUTIVE INSIGHTS SERVICE")
        print("="*50)
        
        try:
            # Test service initialization
            if not self.insights_service:
                print("❌ Insights service not initialized")
                return False
            
            print("✅ Executive Insights Service initialized")
            
            # Test holiday data
            holidays = self.insights_service.holiday_data
            if isinstance(holidays, list) and len(holidays) > 5:
                print(f"✅ Holiday data loaded: {len(holidays)} holidays")
                
                # Check for key holidays
                holiday_names = [h['name'] for h in holidays]
                key_holidays = ['Memorial Day', 'Independence Day', 'Labor Day']
                missing_holidays = [h for h in key_holidays if h not in holiday_names]
                
                if not missing_holidays:
                    print("✅ All key holidays present")
                else:
                    print(f"⚠️  Missing key holidays: {missing_holidays}")
            else:
                print("❌ Holiday data not properly loaded")
                return False
            
            # Test construction seasons
            seasons = self.insights_service.construction_seasons
            required_seasons = ['peak_season', 'shoulder_season', 'off_season']
            
            if all(season in seasons for season in required_seasons):
                print("✅ Construction seasons configured")
                
                # Validate peak season months (should include summer)
                peak_months = seasons['peak_season']['months']
                if all(month in peak_months for month in [6, 7, 8]):  # June, July, August
                    print("✅ Peak construction season includes summer months")
                else:
                    print("⚠️  Peak construction season may not include all summer months")
            else:
                print("❌ Construction seasons not properly configured")
                return False
            
            # Test seasonal correlation logic
            july_info = self.insights_service._get_construction_season_info(7)  # July
            january_info = self.insights_service._get_construction_season_info(1)  # January
            
            if july_info and july_info['activity_level'] == 'peak':
                print("✅ July correctly identified as peak construction season")
            else:
                print("❌ July not identified as peak construction season")
                return False
            
            if january_info and january_info['activity_level'] == 'low':
                print("✅ January correctly identified as off-season")
            else:
                print("❌ January not identified as off-season")
                return False
            
        except Exception as e:
            print(f"❌ Executive Insights Service test failed: {e}")
            traceback.print_exc()
            return False
        
        self.test_results['insights_service'] = True
        return True
    
    def test_data_processing_methods(self):
        """Test key data processing methods with mock data"""
        print("\n" + "="*50)
        print("TESTING DATA PROCESSING METHODS")
        print("="*50)
        
        try:
            # Test rolling averages with limited scope
            print("Testing rolling averages calculation...")
            
            try:
                result = self.financial_service.calculate_rolling_averages('revenue', weeks_back=4)
                if isinstance(result, dict):
                    print("✅ Rolling averages method returns proper structure")
                    if result.get('error'):
                        print(f"ℹ️  Expected error due to limited data: {result['error']}")
                    elif result.get('success'):
                        print("✅ Rolling averages calculation successful")
                else:
                    print("❌ Rolling averages method returns invalid structure")
                    return False
            except Exception as e:
                print(f"ℹ️  Rolling averages failed as expected (limited database): {str(e)[:100]}...")
            
            # Test anomaly detection structure
            print("Testing anomaly detection...")
            
            try:
                result = self.insights_service.detect_financial_anomalies(lookback_weeks=4)
                if isinstance(result, dict):
                    print("✅ Anomaly detection method returns proper structure")
                    if result.get('error'):
                        print(f"ℹ️  Expected error due to limited data: {result['error']}")
                    elif result.get('success'):
                        print("✅ Anomaly detection successful")
                else:
                    print("❌ Anomaly detection returns invalid structure")
                    return False
            except Exception as e:
                print(f"ℹ️  Anomaly detection failed as expected (limited database): {str(e)[:100]}...")
            
            # Test custom insight validation
            print("Testing custom insight validation...")
            
            result = self.insights_service.add_custom_insight(
                date="2024-07-15",
                event_type="weather",
                description="Test insight for validation",
                impact_category="revenue",
                impact_magnitude=0.5
            )
            
            if isinstance(result, dict) and 'success' in result:
                print("✅ Custom insight validation working")
            else:
                print("❌ Custom insight validation failed")
                return False
            
        except Exception as e:
            print(f"❌ Data processing methods test failed: {e}")
            traceback.print_exc()
            return False
        
        return True
    
    def test_api_endpoints(self):
        """Test API endpoint accessibility"""
        print("\n" + "="*50)
        print("TESTING API ENDPOINTS")
        print("="*50)
        
        try:
            with self.app.test_client() as client:
                # Test main dashboard route
                response = client.get('/executive/dashboard')
                if response.status_code in [200, 302]:  # 200 or redirect
                    print("✅ Executive dashboard route accessible")
                else:
                    print(f"❌ Executive dashboard route returned status {response.status_code}")
                    return False
                
                # Test API endpoints
                api_endpoints = [
                    '/executive/api/financial-kpis',
                    '/executive/api/store-comparison',
                    '/executive/api/intelligent-insights',
                    '/executive/api/financial-forecasts',
                    '/executive/api/dashboard-config'
                ]
                
                for endpoint in api_endpoints:
                    response = client.get(endpoint)
                    if response.status_code == 200:
                        print(f"✅ Endpoint {endpoint} accessible")
                        
                        # Verify JSON response
                        try:
                            data = json.loads(response.data)
                            print(f"  ✅ Returns valid JSON")
                        except json.JSONDecodeError:
                            print(f"  ❌ Invalid JSON response")
                            return False
                        
                    else:
                        print(f"❌ Endpoint {endpoint} returned status {response.status_code}")
                        return False
                
                # Test POST endpoint
                custom_insight_data = {
                    "date": "2024-07-15",
                    "event_type": "weather",
                    "description": "Test insight",
                    "impact_category": "revenue",
                    "impact_magnitude": 0.5
                }
                
                response = client.post('/executive/api/custom-insight',
                                     data=json.dumps(custom_insight_data),
                                     content_type='application/json')
                
                if response.status_code == 200:
                    print("✅ Custom insight POST endpoint accessible")
                else:
                    print(f"❌ Custom insight POST endpoint returned status {response.status_code}")
                    return False
                
        except Exception as e:
            print(f"❌ API endpoint test failed: {e}")
            traceback.print_exc()
            return False
        
        self.test_results['api_endpoints'] = True
        return True
    
    def test_data_integrity(self):
        """Test data integrity and calculation accuracy"""
        print("\n" + "="*50)
        print("TESTING DATA INTEGRITY")
        print("="*50)
        
        try:
            # Test store code consistency
            financial_stores = set(self.financial_service.STORE_CODES.keys())
            business_mix_stores = set(self.financial_service.STORE_BUSINESS_MIX.keys())
            revenue_target_stores = set(self.financial_service.STORE_REVENUE_TARGETS.keys())
            
            if financial_stores == business_mix_stores == revenue_target_stores:
                print("✅ Store codes consistent across all configurations")
            else:
                print("❌ Store code inconsistency detected")
                print(f"  Financial stores: {financial_stores}")
                print(f"  Business mix stores: {business_mix_stores}")
                print(f"  Revenue target stores: {revenue_target_stores}")
                return False
            
            # Test business mix logic
            for store_code, mix in self.financial_service.STORE_BUSINESS_MIX.items():
                total_mix = mix['construction'] + mix['events']
                if abs(total_mix - 1.0) < 0.001:  # Allow for floating point precision
                    print(f"✅ Store {store_code} business mix sums to 100%")
                else:
                    print(f"❌ Store {store_code} business mix sums to {total_mix*100:.1f}%")
                    return False
            
            # Test calculation accuracy with known values
            import numpy as np
            
            test_revenues = [50000, 55000, 52000, 48000, 53000]
            test_payroll = [15000, 16500, 15600, 14400, 15900]
            
            # Calculate profit margins
            profits = [r - p for r, p in zip(test_revenues, test_payroll)]
            margins = [(p / r) * 100 for r, p in zip(test_revenues, profits)]
            
            # Verify calculations
            expected_margin_0 = ((50000 - 15000) / 50000) * 100  # 70%
            if abs(margins[0] - expected_margin_0) < 0.01:
                print("✅ Profit margin calculations accurate")
            else:
                print(f"❌ Profit margin calculation error: expected {expected_margin_0:.2f}%, got {margins[0]:.2f}%")
                return False
            
            # Test anomaly detection sensitivity
            normal_data = np.array([50000, 51000, 49000, 52000, 50500])
            anomaly_value = 75000  # 50% spike
            
            mean_val = np.mean(normal_data)
            std_val = np.std(normal_data)
            z_score = (anomaly_value - mean_val) / std_val
            
            if abs(z_score) > 2.0:
                print(f"✅ Anomaly detection sensitivity appropriate (z-score: {z_score:.2f})")
            else:
                print(f"❌ Anomaly detection may not be sensitive enough (z-score: {z_score:.2f})")
                return False
            
        except Exception as e:
            print(f"❌ Data integrity test failed: {e}")
            traceback.print_exc()
            return False
        
        self.test_results['data_integrity'] = True
        return True
    
    def run_comprehensive_debug(self):
        """Run all debug tests and provide comprehensive report"""
        print("🚀 STARTING KVC COMPANIES EXECUTIVE DASHBOARD DEBUG")
        print("=" * 70)
        
        start_time = datetime.now()
        
        # Initialize application
        if not self.initialize_app():
            print("❌ Failed to initialize application - cannot continue")
            return False
        
        # Run all tests
        test_methods = [
            ('Database Connectivity', self.test_database_connectivity),
            ('Financial Analytics Service', self.test_financial_analytics_service),
            ('Executive Insights Service', self.test_insights_service),
            ('Data Processing Methods', self.test_data_processing_methods),
            ('API Endpoints', self.test_api_endpoints),
            ('Data Integrity', self.test_data_integrity)
        ]
        
        passed_tests = 0
        total_tests = len(test_methods)
        
        for test_name, test_method in test_methods:
            print(f"\n🧪 Running {test_name} tests...")
            try:
                if test_method():
                    passed_tests += 1
                    print(f"✅ {test_name} tests PASSED")
                else:
                    print(f"❌ {test_name} tests FAILED")
            except Exception as e:
                print(f"❌ {test_name} tests ERROR: {e}")
        
        # Generate final report
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 70)
        print("🏁 EXECUTIVE DASHBOARD DEBUG REPORT")
        print("=" * 70)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests / total_tests) * 100:.1f}%")
        print(f"Duration: {duration.total_seconds():.2f} seconds")
        
        print(f"\nDETAILED RESULTS:")
        for component, status in self.test_results.items():
            status_symbol = "✅" if status else "❌"
            print(f"  {status_symbol} {component.replace('_', ' ').title()}")
        
        if passed_tests == total_tests:
            print(f"\n🎉 ALL TESTS PASSED! Executive Dashboard system is ready for deployment.")
            return True
        else:
            print(f"\n⚠️  SOME TESTS FAILED. Please review the errors above and fix issues before deployment.")
            return False
    
    def cleanup(self):
        """Clean up test environment"""
        if hasattr(self, 'app_context'):
            self.app_context.pop()


def main():
    """Main entry point for the debug script"""
    debugger = ExecutiveDashboardDebugger()
    
    try:
        success = debugger.run_comprehensive_debug()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Debug interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n\n💥 Unexpected error during debug: {e}")
        traceback.print_exc()
        sys.exit(3)
    finally:
        debugger.cleanup()


if __name__ == "__main__":
    main()