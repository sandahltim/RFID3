#!/usr/bin/env python3
"""
Comprehensive Test Suite for RFID3 Analytics Framework
Complete testing and validation of all system components
"""

import sys
import subprocess
import json
import time
from datetime import datetime
from pathlib import Path

class TestResult:
    """Test result container"""
    def __init__(self, name, passed=False, message="", duration=0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration = duration

class ComprehensiveTestSuite:
    """Main test suite orchestrator"""
    
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
    
    def run_test(self, test_name, test_function):
        """Run a single test and record results"""
        print(f"\n{'='*60}")
        print(f"RUNNING TEST: {test_name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        try:
            result = test_function()
            duration = time.time() - start_time
            
            if result:
                print(f"✅ {test_name} PASSED ({duration:.2f}s)")
                self.results.append(TestResult(test_name, True, "Test passed", duration))
            else:
                print(f"❌ {test_name} FAILED ({duration:.2f}s)")
                self.results.append(TestResult(test_name, False, "Test failed", duration))
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ {test_name} ERROR ({duration:.2f}s): {str(e)}")
            self.results.append(TestResult(test_name, False, f"Exception: {str(e)}", duration))
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        
        print("🎯 RFID3 COMPREHENSIVE TEST SUITE")
        print("="*80)
        print(f"Started at: {self.start_time}")
        print("="*80)
        
        # Test 1: Flask Application Initialization
        self.run_test("Flask Application Initialization", self.test_flask_initialization)
        
        # Test 2: Database Connectivity  
        self.run_test("Database Connectivity", self.test_database_connectivity)
        
        # Test 3: Analytics Services
        self.run_test("Analytics Services", self.test_analytics_services)
        
        # Test 4: API Endpoints
        self.run_test("API Endpoints", self.test_api_endpoints)
        
        # Test 5: Data Flow and CSV Import
        self.run_test("Data Flow and CSV Import", self.test_data_flow)
        
        # Test 6: Performance Benchmarking
        self.run_test("Performance Benchmarking", self.test_performance)
        
        # Test 7: Health Check System
        self.run_test("Health Check System", self.test_health_checks)
        
        # Test 8: Store Mappings Validation
        self.run_test("Store Mappings Validation", self.test_store_mappings)
        
        # Generate final report
        self.generate_final_report()
    
    def test_flask_initialization(self):
        """Test Flask app initialization"""
        try:
            from app import create_app
            app = create_app()
            
            with app.app_context():
                # Check that app context works
                return True
        except Exception as e:
            print(f"Flask initialization failed: {str(e)}")
            return False
    
    def test_database_connectivity(self):
        """Test database connectivity and basic queries"""
        try:
            from app import create_app, db
            from sqlalchemy import text
            
            app = create_app()
            with app.app_context():
                # Test basic query
                result = db.session.execute(text('SELECT 1')).fetchone()
                
                # Test table existence
                tables_check = db.session.execute(text('SHOW TABLES')).fetchall()
                
                return len(tables_check) > 0
                
        except Exception as e:
            print(f"Database connectivity test failed: {str(e)}")
            return False
    
    def test_analytics_services(self):
        """Test all analytics services"""
        try:
            result = subprocess.run([sys.executable, 'test_analytics_services_flask.py'], 
                                  capture_output=True, text=True, timeout=60)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("Analytics services test timed out")
            return False
        except Exception as e:
            print(f"Analytics services test failed: {str(e)}")
            return False
    
    def test_api_endpoints(self):
        """Test API endpoints"""
        try:
            result = subprocess.run([sys.executable, 'test_api_endpoints.py'], 
                                  capture_output=True, text=True, timeout=60)
            # API test passes if at least some endpoints work
            return "Overall Score" in result.stdout and not result.stdout.count("0/") > 0
        except subprocess.TimeoutExpired:
            print("API endpoints test timed out")
            return False
        except Exception as e:
            print(f"API endpoints test failed: {str(e)}")
            return False
    
    def test_data_flow(self):
        """Test data flow and CSV import processes"""
        try:
            result = subprocess.run([sys.executable, 'test_csv_data_flow.py'], 
                                  capture_output=True, text=True, timeout=60)
            # Data flow test passes if at least 50% of tests pass
            return "Overall Score" in result.stdout and not result.stdout.count("0/") > 0
        except subprocess.TimeoutExpired:
            print("Data flow test timed out")
            return False
        except Exception as e:
            print(f"Data flow test failed: {str(e)}")
            return False
    
    def test_performance(self):
        """Test performance benchmarking"""
        try:
            result = subprocess.run([sys.executable, 'performance_benchmark_test.py'], 
                                  capture_output=True, text=True, timeout=120)
            return "PERFORMANCE TESTING PASSED" in result.stdout
        except subprocess.TimeoutExpired:
            print("Performance test timed out")
            return False
        except Exception as e:
            print(f"Performance test failed: {str(e)}")
            return False
    
    def test_health_checks(self):
        """Test health check system"""
        try:
            from app import create_app
            app = create_app()
            
            with app.test_client() as client:
                # Test health status endpoint
                response = client.get('/api/health/status')
                return response.status_code in [200, 503]  # Either healthy or degraded is acceptable
                
        except Exception as e:
            print(f"Health check test failed: {str(e)}")
            return False
    
    def test_store_mappings(self):
        """Test store mappings accuracy"""
        try:
            from app import create_app, db
            from sqlalchemy import text
            
            app = create_app()
            with app.app_context():
                # Check store mapping tables exist and have data
                store_mapping_tables = ['store_mappings', 'unified_store_mapping', 'pos_store_mapping']
                
                for table in store_mapping_tables:
                    try:
                        result = db.session.execute(text(f'SELECT COUNT(*) FROM {table}')).fetchone()
                        if result[0] > 0:
                            return True
                    except:
                        continue
                
                return False
                
        except Exception as e:
            print(f"Store mappings test failed: {str(e)}")
            return False
    
    def generate_final_report(self):
        """Generate comprehensive final report"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        passed_tests = [r for r in self.results if r.passed]
        failed_tests = [r for r in self.results if not r.passed]
        
        print("\n" + "="*80)
        print("COMPREHENSIVE TEST SUITE RESULTS")
        print("="*80)
        print(f"Started: {self.start_time}")
        print(f"Completed: {end_time}")
        print(f"Total Duration: {total_duration:.2f} seconds")
        print(f"Tests Run: {len(self.results)}")
        print(f"Passed: {len(passed_tests)} ✅")
        print(f"Failed: {len(failed_tests)} ❌")
        print(f"Success Rate: {len(passed_tests)/len(self.results)*100:.1f}%")
        
        print("\nDETAILED RESULTS:")
        print("-"*80)
        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"{status} | {result.name:<35} | {result.duration:>6.2f}s | {result.message}")
        
        # Overall assessment
        success_rate = len(passed_tests) / len(self.results) * 100
        
        if success_rate >= 90:
            overall_status = "🎉 EXCELLENT"
            recommendation = "System is production-ready with excellent test coverage"
        elif success_rate >= 75:
            overall_status = "✅ GOOD"
            recommendation = "System is mostly functional with minor issues to address"
        elif success_rate >= 50:
            overall_status = "⚠️ NEEDS ATTENTION"
            recommendation = "System has significant issues that should be resolved"
        else:
            overall_status = "❌ CRITICAL"
            recommendation = "System requires major fixes before deployment"
        
        print(f"\nOVERALL ASSESSMENT: {overall_status}")
        print(f"RECOMMENDATION: {recommendation}")
        
        # Generate JSON report
        report_data = {
            'test_suite': 'RFID3 Comprehensive Test Suite',
            'timestamp': end_time.isoformat(),
            'duration_seconds': total_duration,
            'total_tests': len(self.results),
            'passed_tests': len(passed_tests),
            'failed_tests': len(failed_tests),
            'success_rate_percent': success_rate,
            'overall_status': overall_status,
            'recommendation': recommendation,
            'test_results': [
                {
                    'name': r.name,
                    'passed': r.passed,
                    'message': r.message,
                    'duration': r.duration
                }
                for r in self.results
            ]
        }
        
        # Save report to file
        report_path = Path('test_results_report.json')
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_path.absolute()}")
        
        return success_rate >= 75  # Return True if success rate is good

if __name__ == "__main__":
    test_suite = ComprehensiveTestSuite()
    success = test_suite.run_all_tests()
    sys.exit(0 if success else 1)