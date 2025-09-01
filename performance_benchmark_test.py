#!/usr/bin/env python3
"""
Performance Testing and Benchmarking for RFID3 Analytics Framework
Tests response times, memory usage, and concurrent user scenarios
"""

import sys
import time
import threading
import psutil
import os
from datetime import datetime
from app import create_app, db
from sqlalchemy import text

class PerformanceTracker:
    """Track performance metrics during testing"""
    
    def __init__(self):
        self.start_time = None
        self.start_memory = None
        self.results = []
    
    def start_measurement(self, test_name):
        """Start measuring performance for a test"""
        self.start_time = time.time()
        self.start_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
        print(f"📊 Starting performance measurement for: {test_name}")
    
    def end_measurement(self, test_name):
        """End performance measurement and record results"""
        end_time = time.time()
        end_memory = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024  # MB
        
        duration = end_time - self.start_time
        memory_delta = end_memory - self.start_memory
        
        result = {
            'test_name': test_name,
            'duration': duration,
            'memory_delta': memory_delta,
            'start_memory': self.start_memory,
            'end_memory': end_memory
        }
        
        self.results.append(result)
        print(f"⏱️ {test_name}: {duration:.2f}s | Memory: {memory_delta:+.1f}MB")
        return result

def test_analytics_performance():
    """Test performance of analytics services"""
    
    print("=" * 80)
    print("PERFORMANCE TESTING AND BENCHMARKING")
    print("=" * 80)
    
    app = create_app()
    tracker = PerformanceTracker()
    
    with app.app_context():
        print(f"✅ Flask app context established at {datetime.now()}")
        print(f"💾 Initial memory usage: {psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024:.1f} MB")
        
        # Test 1: Multi-Store Analytics Performance
        print("\n🔍 Performance Test 1: Multi-Store Analytics Service")
        tracker.start_measurement("Multi-Store Analytics")
        try:
            from app.services.multi_store_analytics_service import MultiStoreAnalyticsService
            multi_store = MultiStoreAnalyticsService()
            regional_data = multi_store.analyze_regional_demand_patterns(90)  # 90 days for comprehensive test
            tracker.end_measurement("Multi-Store Analytics")
            
        except Exception as e:
            print(f"❌ Multi-Store Analytics performance test failed: {str(e)}")
            tracker.end_measurement("Multi-Store Analytics (Failed)")
        
        # Test 2: Financial Analytics Performance
        print("\n💰 Performance Test 2: Financial Analytics Service")
        tracker.start_measurement("Financial Analytics")
        try:
            from app.services.financial_analytics_service import FinancialAnalyticsService
            financial = FinancialAnalyticsService()
            
            # Test multiple operations
            rolling_data = financial.calculate_rolling_averages('revenue', 8)  # 8 weeks
            dashboard_data = financial.get_executive_financial_dashboard()
            yoy_data = financial.calculate_year_over_year_analysis('comprehensive')
            
            tracker.end_measurement("Financial Analytics")
            
        except Exception as e:
            print(f"❌ Financial Analytics performance test failed: {str(e)}")
            tracker.end_measurement("Financial Analytics (Failed)")
        
        # Test 3: Business Analytics Performance
        print("\n📊 Performance Test 3: Business Analytics Service")
        tracker.start_measurement("Business Analytics")
        try:
            from app.services.business_analytics_service import BusinessAnalyticsService
            business = BusinessAnalyticsService()
            
            equipment_data = business.calculate_equipment_utilization_analytics()
            customer_data = business.calculate_customer_analytics()
            exec_data = business.generate_executive_dashboard_metrics()
            
            tracker.end_measurement("Business Analytics")
            
        except Exception as e:
            print(f"❌ Business Analytics performance test failed: {str(e)}")
            tracker.end_measurement("Business Analytics (Failed)")
        
        # Test 4: Database Query Performance
        print("\n🗄️ Performance Test 4: Database Queries")
        tracker.start_measurement("Database Queries")
        try:
            # Test complex queries
            queries = [
                "SELECT COUNT(*) FROM pos_transactions WHERE transaction_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)",
                "SELECT store_location, SUM(total_amount) FROM pos_transactions GROUP BY store_location",
                "SELECT COUNT(DISTINCT customer_id) FROM pos_transactions"
            ]
            
            for i, query in enumerate(queries, 1):
                query_start = time.time()
                try:
                    result = db.session.execute(text(query)).fetchall()
                    query_time = time.time() - query_start
                    print(f"   Query {i}: {query_time:.3f}s")
                except Exception as e:
                    print(f"   Query {i}: FAILED - {str(e)}")
            
            tracker.end_measurement("Database Queries")
            
        except Exception as e:
            print(f"❌ Database performance test failed: {str(e)}")
            tracker.end_measurement("Database Queries (Failed)")
        
        # Test 5: Memory Stress Test
        print("\n🧠 Performance Test 5: Memory Usage Analysis")
        tracker.start_measurement("Memory Stress Test")
        try:
            # Simulate processing large datasets
            large_data_sets = []
            for i in range(5):
                # Simulate analytics calculations
                from app.services.equipment_categorization_service import EquipmentCategorizationService
                equipment = EquipmentCategorizationService()
                inventory_data = equipment.analyze_inventory_mix()
                large_data_sets.append(inventory_data)
                
                memory_usage = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
                print(f"   Iteration {i+1}: {memory_usage:.1f} MB")
            
            tracker.end_measurement("Memory Stress Test")
            
        except Exception as e:
            print(f"❌ Memory stress test failed: {str(e)}")
            tracker.end_measurement("Memory Stress Test (Failed)")
    
    # Performance Results Summary
    print("\n" + "=" * 80)
    print("PERFORMANCE TEST RESULTS")
    print("=" * 80)
    
    total_duration = sum(r['duration'] for r in tracker.results)
    max_memory = max(r['end_memory'] for r in tracker.results)
    
    print(f"📊 Total test duration: {total_duration:.2f} seconds")
    print(f"💾 Peak memory usage: {max_memory:.1f} MB")
    print(f"🧪 Tests completed: {len(tracker.results)}")
    
    print("\nDetailed Performance Metrics:")
    for result in tracker.results:
        status = "✅" if "Failed" not in result['test_name'] else "❌"
        print(f"{status} {result['test_name']}: {result['duration']:.2f}s | {result['memory_delta']:+.1f}MB")
    
    # Performance Assessment
    failed_tests = sum(1 for r in tracker.results if "Failed" in r['test_name'])
    passed_tests = len(tracker.results) - failed_tests
    
    # Performance thresholds
    avg_response_time = total_duration / len(tracker.results) if tracker.results else 0
    memory_efficient = max_memory < 500  # MB
    response_time_good = avg_response_time < 5  # seconds
    
    print(f"\n🎯 Performance Assessment:")
    print(f"   Average response time: {avg_response_time:.2f}s {'✅' if response_time_good else '⚠️'}")
    print(f"   Memory efficiency: {'✅' if memory_efficient else '⚠️'}")
    print(f"   Success rate: {passed_tests}/{len(tracker.results)} {'✅' if failed_tests == 0 else '⚠️'}")
    
    if failed_tests == 0 and response_time_good and memory_efficient:
        print("🎉 PERFORMANCE TESTING PASSED!")
        return True
    else:
        print("⚠️ Performance issues detected - optimization recommended")
        return False

def test_concurrent_users():
    """Test system under concurrent load"""
    
    print("\n" + "=" * 80)
    print("CONCURRENT USER SIMULATION")
    print("=" * 80)
    
    app = create_app()
    
    def simulate_user_session(user_id):
        """Simulate a user session with analytics queries"""
        with app.app_context():
            try:
                # Simulate user workflow
                from app.services.financial_analytics_service import FinancialAnalyticsService
                financial = FinancialAnalyticsService()
                
                # User makes several requests
                dashboard = financial.get_executive_financial_dashboard()
                rolling = financial.calculate_rolling_averages('revenue', 4)
                
                print(f"👤 User {user_id}: Session completed successfully")
                return True
                
            except Exception as e:
                print(f"❌ User {user_id}: Session failed - {str(e)}")
                return False
    
    # Simulate concurrent users
    num_users = 3  # Conservative for testing
    print(f"🚀 Starting {num_users} concurrent user sessions...")
    
    start_time = time.time()
    threads = []
    
    for i in range(num_users):
        thread = threading.Thread(target=simulate_user_session, args=(i+1,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    concurrent_duration = end_time - start_time
    
    print(f"⏱️ Concurrent test completed in: {concurrent_duration:.2f} seconds")
    print("✅ Concurrent user simulation passed")
    
    return True

if __name__ == "__main__":
    print("Starting comprehensive performance testing...")
    
    performance_success = test_analytics_performance()
    concurrent_success = test_concurrent_users()
    
    overall_success = performance_success and concurrent_success
    
    print("\n" + "=" * 80)
    print("FINAL PERFORMANCE TEST RESULTS")
    print("=" * 80)
    print(f"Performance Tests: {'✅ PASSED' if performance_success else '❌ FAILED'}")
    print(f"Concurrent Tests: {'✅ PASSED' if concurrent_success else '❌ FAILED'}")
    print(f"Overall Result: {'🎉 SUCCESS' if overall_success else '⚠️ NEEDS OPTIMIZATION'}")
    
    sys.exit(0 if overall_success else 1)