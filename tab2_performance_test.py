#!/usr/bin/env python3
"""
Tab 2 Performance Testing Script

This script tests the performance improvements made to Tab 2 rental inventory.
Run this script before and after applying optimizations to measure improvement.

Usage:
    python tab2_performance_test.py
"""

import time
import requests
import json
from datetime import datetime
import statistics

# Configuration
BASE_URL = "http://localhost:5000"  # Adjust as needed
TEST_ITERATIONS = 5
PAGINATION_SIZES = [10, 20, 50, 100]

def make_request(url, timeout=30):
    """Make a timed HTTP request."""
    start_time = time.time()
    try:
        response = requests.get(url, timeout=timeout)
        end_time = time.time()
        return {
            'success': True,
            'status_code': response.status_code,
            'response_time': end_time - start_time,
            'response_size': len(response.content),
            'url': url
        }
    except Exception as e:
        end_time = time.time()
        return {
            'success': False,
            'error': str(e),
            'response_time': end_time - start_time,
            'url': url
        }

def test_main_tab2_view():
    """Test the main Tab 2 view with different pagination sizes."""
    print("\\n=== Testing Main Tab 2 View ===")
    results = {}
    
    for per_page in PAGINATION_SIZES:
        print(f"\\nTesting with {per_page} items per page...")
        times = []
        
        for i in range(TEST_ITERATIONS):
            url = f"{BASE_URL}/tab/2?per_page={per_page}&page=1"
            result = make_request(url)
            
            if result['success']:
                times.append(result['response_time'])
                print(f"  Iteration {i+1}: {result['response_time']:.3f}s")
            else:
                print(f"  Iteration {i+1}: FAILED - {result['error']}")
        
        if times:
            results[per_page] = {
                'avg_time': statistics.mean(times),
                'min_time': min(times),
                'max_time': max(times),
                'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
                'success_rate': len(times) / TEST_ITERATIONS * 100
            }
            print(f"  Average: {results[per_page]['avg_time']:.3f}s")
            print(f"  Range: {results[per_page]['min_time']:.3f}s - {results[per_page]['max_time']:.3f}s")
    
    return results

def test_sorting_performance():
    """Test sorting performance with different sort columns."""
    print("\\n=== Testing Sorting Performance ===")
    results = {}
    sort_columns = ['contract_number', 'client', 'scan']
    
    for sort_col in sort_columns:
        print(f"\\nTesting {sort_col} sorting...")
        times = []
        
        for direction in ['asc', 'desc']:
            sort_param = f"{sort_col}_{direction}"
            
            for i in range(TEST_ITERATIONS):
                url = f"{BASE_URL}/tab/2/sort_contracts?sort={sort_param}&per_page=20"
                result = make_request(url)
                
                if result['success']:
                    times.append(result['response_time'])
                    print(f"  {sort_param} iteration {i+1}: {result['response_time']:.3f}s")
                else:
                    print(f"  {sort_param} iteration {i+1}: FAILED - {result['error']}")
        
        if times:
            results[sort_col] = {
                'avg_time': statistics.mean(times),
                'min_time': min(times),
                'max_time': max(times),
                'success_rate': len(times) / (TEST_ITERATIONS * 2) * 100
            }
    
    return results

def test_cache_performance():
    """Test cache effectiveness by making repeated requests."""
    print("\\n=== Testing Cache Performance ===")
    
    # Clear cache first
    print("Clearing cache...")
    requests.get(f"{BASE_URL}/tab/2/cache_clear")
    
    # First request (cache miss)
    print("\\nTesting cache miss (first request)...")
    url = f"{BASE_URL}/tab/2?per_page=20&page=1"
    first_result = make_request(url)
    
    if first_result['success']:
        print(f"Cache miss time: {first_result['response_time']:.3f}s")
        
        # Immediate second request (cache hit)
        print("Testing cache hit (second request)...")
        second_result = make_request(url)
        
        if second_result['success']:
            print(f"Cache hit time: {second_result['response_time']:.3f}s")
            improvement = ((first_result['response_time'] - second_result['response_time']) 
                          / first_result['response_time'] * 100)
            print(f"Cache improvement: {improvement:.1f}%")
            return {
                'cache_miss_time': first_result['response_time'],
                'cache_hit_time': second_result['response_time'],
                'improvement_percent': improvement
            }
    
    return {'error': 'Cache test failed'}

def get_performance_stats():
    """Get performance statistics from the application."""
    print("\\n=== Getting Performance Statistics ===")
    
    result = make_request(f"{BASE_URL}/tab/2/performance_stats")
    if result['success']:
        try:
            stats = requests.get(f"{BASE_URL}/tab/2/performance_stats").json()
            print(f"Contract count: {stats['contract_count']}")
            print(f"Total items on contract: {stats['total_items_on_contract']}")
            print(f"Average items per contract: {stats['average_items_per_contract']}")
            print(f"Optimization version: {stats['optimization_version']}")
            print("Features enabled:")
            for feature in stats['features']:
                print(f"  - {feature}")
            return stats
        except Exception as e:
            print(f"Failed to parse stats: {e}")
    else:
        print(f"Failed to get stats: {result['error']}")
    
    return None

def run_comprehensive_test():
    """Run all performance tests and generate a report."""
    print("🚀 Tab 2 Performance Testing Suite")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: {BASE_URL}")
    print(f"Test iterations per test: {TEST_ITERATIONS}")
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'base_url': BASE_URL,
        'test_iterations': TEST_ITERATIONS
    }
    
    # Get performance statistics
    report['performance_stats'] = get_performance_stats()
    
    # Test main view performance
    report['main_view_results'] = test_main_tab2_view()
    
    # Test sorting performance
    report['sorting_results'] = test_sorting_performance()
    
    # Test cache performance
    report['cache_results'] = test_cache_performance()
    
    # Generate summary
    print("\\n" + "=" * 50)
    print("📊 PERFORMANCE TEST SUMMARY")
    print("=" * 50)
    
    if report['main_view_results']:
        fastest_pagination = min(report['main_view_results'].keys(), 
                               key=lambda k: report['main_view_results'][k]['avg_time'])
        fastest_time = report['main_view_results'][fastest_pagination]['avg_time']
        print(f"✅ Fastest pagination: {fastest_pagination} items/page ({fastest_time:.3f}s avg)")
        
        # Check if any response is under 2 seconds (good performance threshold)
        fast_responses = [k for k, v in report['main_view_results'].items() if v['avg_time'] < 2.0]
        if fast_responses:
            print(f"✅ Fast responses (<2s): {fast_responses}")
        else:
            print("⚠️  No responses under 2 seconds - consider further optimization")
    
    if 'improvement_percent' in report['cache_results']:
        cache_improvement = report['cache_results']['improvement_percent']
        if cache_improvement > 50:
            print(f"✅ Excellent cache performance: {cache_improvement:.1f}% improvement")
        elif cache_improvement > 20:
            print(f"✅ Good cache performance: {cache_improvement:.1f}% improvement")
        else:
            print(f"⚠️  Moderate cache performance: {cache_improvement:.1f}% improvement")
    
    # Save detailed report
    report_filename = f"tab2_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"📝 Detailed report saved: {report_filename}")
    print("\\n🎉 Performance testing completed!")
    
    return report

if __name__ == "__main__":
    try:
        run_comprehensive_test()
    except KeyboardInterrupt:
        print("\\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()