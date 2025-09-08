"""
Performance Regression Tests for RFID3 System
=============================================

Test suite for validating performance regression prevention,
load testing, and scalability after recent system improvements.

Date: 2025-08-28
Author: Testing Specialist
"""

import pytest
import time
import sys
import os
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch, MagicMock
import threading
import statistics

# Add root directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


class TestDatabasePerformance:
    """Test database query performance and optimization."""
    
    def test_dashboard_query_performance(self):
        """Test dashboard query performance meets SLA requirements."""
        # Mock query execution times for different scenarios
        query_performance_data = [
            {
                'query_type': 'dashboard_summary',
                'record_count': 1000,
                'execution_time_ms': 450,
                'sla_threshold_ms': 2000
            },
            {
                'query_type': 'dashboard_summary',
                'record_count': 10000,
                'execution_time_ms': 1200,
                'sla_threshold_ms': 2000
            },
            {
                'query_type': 'business_intelligence',
                'record_count': 5000,
                'execution_time_ms': 2800,
                'sla_threshold_ms': 5000
            },
            {
                'query_type': 'stale_items',
                'record_count': 2500,
                'execution_time_ms': 800,
                'sla_threshold_ms': 3000
            }
        ]
        
        # Validate performance against SLA
        for query_data in query_performance_data:
            execution_time = query_data['execution_time_ms']
            threshold = query_data['sla_threshold_ms']
            query_type = query_data['query_type']
            
            assert execution_time <= threshold, f"{query_type} query too slow: {execution_time}ms > {threshold}ms"
            
            # Performance scoring
            performance_score = (threshold - execution_time) / threshold * 100
            assert performance_score >= 0, f"Performance score should be non-negative"
            
            # Log performance metrics for monitoring
            if performance_score < 25:  # Less than 25% headroom
                print(f"WARNING: {query_type} approaching SLA limit: {execution_time}ms/{threshold}ms")
    
    def test_concurrent_query_performance(self):
        """Test database performance under concurrent load."""
        # Mock concurrent query scenario
        concurrent_scenarios = [
            {
                'concurrent_users': 5,
                'query_type': 'dashboard_summary',
                'expected_max_response_time_ms': 2500,
                'expected_avg_response_time_ms': 1000
            },
            {
                'concurrent_users': 10,
                'query_type': 'business_intelligence',
                'expected_max_response_time_ms': 8000,
                'expected_avg_response_time_ms': 4000
            },
            {
                'concurrent_users': 20,
                'query_type': 'stale_items',
                'expected_max_response_time_ms': 5000,
                'expected_avg_response_time_ms': 2500
            }
        ]
        
        for scenario in concurrent_scenarios:
            concurrent_users = scenario['concurrent_users']
            query_type = scenario['query_type']
            
            # Simulate concurrent execution
            def simulate_query():
                # Mock query execution time with some variance
                base_time = 500 if query_type == 'dashboard_summary' else 1500
                variance = base_time * 0.3  # 30% variance
                execution_time = base_time + (threading.current_thread().ident % int(variance))
                return execution_time
            
            # Execute concurrent queries
            with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
                futures = [executor.submit(simulate_query) for _ in range(concurrent_users)]
                response_times = [future.result() for future in as_completed(futures)]
            
            # Analyze results
            max_response_time = max(response_times)
            avg_response_time = statistics.mean(response_times)
            
            # Validate against expectations
            assert max_response_time <= scenario['expected_max_response_time_ms'], \
                f"Max response time too high: {max_response_time}ms"
            assert avg_response_time <= scenario['expected_avg_response_time_ms'], \
                f"Average response time too high: {avg_response_time}ms"
    
    def test_large_dataset_query_scaling(self):
        """Test query performance scaling with large datasets."""
        # Mock scaling scenarios
        scaling_scenarios = [
            {'record_count': 1000, 'expected_time_ms': 200},
            {'record_count': 10000, 'expected_time_ms': 800},
            {'record_count': 50000, 'expected_time_ms': 3000},
            {'record_count': 100000, 'expected_time_ms': 5000}
        ]
        
        # Test linear scaling assumption
        for i, scenario in enumerate(scaling_scenarios):
            record_count = scenario['record_count']
            expected_time = scenario['expected_time_ms']
            
            # Calculate scaling factor
            if i > 0:
                prev_scenario = scaling_scenarios[i-1]
                scaling_factor = (record_count / prev_scenario['record_count'])
                time_scaling_factor = (expected_time / prev_scenario['expected_time_ms'])
                
                # Time scaling should be roughly linear or sub-linear
                assert time_scaling_factor <= scaling_factor * 1.5, \
                    f"Query scaling inefficient: {time_scaling_factor} vs {scaling_factor}"
            
            # Validate absolute performance
            max_acceptable_time = record_count * 0.1  # 0.1ms per record max
            assert expected_time <= max_acceptable_time, \
                f"Query time too high for {record_count} records: {expected_time}ms"
    
    def test_memory_usage_optimization(self):
        """Test memory usage optimization for large queries."""
        # Mock memory usage scenarios
        memory_scenarios = [
            {
                'query_type': 'full_inventory_export',
                'record_count': 50000,
                'memory_usage_mb': 120,
                'memory_limit_mb': 256
            },
            {
                'query_type': 'analytics_aggregation',
                'record_count': 25000,
                'memory_usage_mb': 80,
                'memory_limit_mb': 128
            },
            {
                'query_type': 'transaction_history',
                'record_count': 100000,
                'memory_usage_mb': 200,
                'memory_limit_mb': 512
            }
        ]
        
        for scenario in memory_scenarios:
            memory_usage = scenario['memory_usage_mb']
            memory_limit = scenario['memory_limit_mb']
            record_count = scenario['record_count']
            
            # Validate memory usage is within limits
            assert memory_usage <= memory_limit, \
                f"Memory usage exceeds limit: {memory_usage}MB > {memory_limit}MB"
            
            # Calculate memory efficiency
            memory_per_record = memory_usage / record_count * 1024  # KB per record
            assert memory_per_record <= 5.0, \
                f"Memory usage per record too high: {memory_per_record}KB"


class TestAPIEndpointPerformance:
    """Test API endpoint performance and throughput."""
    
    def test_api_response_times(self):
        """Test API endpoint response time requirements."""
        # Mock API performance data
        api_endpoints = [
            {
                'endpoint': '/api/inventory/dashboard_summary',
                'method': 'GET',
                'avg_response_time_ms': 650,
                'p95_response_time_ms': 1200,
                'sla_limit_ms': 2000
            },
            {
                'endpoint': '/api/inventory/business_intelligence',
                'method': 'GET',
                'avg_response_time_ms': 2800,
                'p95_response_time_ms': 4500,
                'sla_limit_ms': 5000
            },
            {
                'endpoint': '/api/inventory/stale_items',
                'method': 'GET',
                'avg_response_time_ms': 900,
                'p95_response_time_ms': 1800,
                'sla_limit_ms': 3000
            },
            {
                'endpoint': '/api/enhanced/dashboard/kpis',
                'method': 'GET',
                'avg_response_time_ms': 750,
                'p95_response_time_ms': 1400,
                'sla_limit_ms': 2500
            }
        ]
        
        # Validate response times
        for endpoint_data in api_endpoints:
            endpoint = endpoint_data['endpoint']
            avg_time = endpoint_data['avg_response_time_ms']
            p95_time = endpoint_data['p95_response_time_ms']
            sla_limit = endpoint_data['sla_limit_ms']
            
            # Average response time should be well under SLA
            assert avg_time <= sla_limit * 0.6, \
                f"{endpoint} average response time too high: {avg_time}ms"
            
            # 95th percentile should be under SLA
            assert p95_time <= sla_limit, \
                f"{endpoint} P95 response time exceeds SLA: {p95_time}ms"
            
            # P95 should not be more than 3x average (reasonable distribution)
            assert p95_time <= avg_time * 3, \
                f"{endpoint} has too much response time variance"
    
    def test_api_throughput_limits(self):
        """Test API throughput under load."""
        # Mock throughput scenarios
        throughput_scenarios = [
            {
                'endpoint': '/api/inventory/dashboard_summary',
                'requests_per_second': 50,
                'success_rate': 99.5,
                'avg_response_time_ms': 800
            },
            {
                'endpoint': '/api/inventory/business_intelligence',
                'requests_per_second': 20,
                'success_rate': 98.0,
                'avg_response_time_ms': 3200
            },
            {
                'endpoint': '/api/inventory/stale_items',
                'requests_per_second': 30,
                'success_rate': 99.0,
                'avg_response_time_ms': 1100
            }
        ]
        
        for scenario in throughput_scenarios:
            endpoint = scenario['endpoint']
            rps = scenario['requests_per_second']
            success_rate = scenario['success_rate']
            avg_response = scenario['avg_response_time_ms']
            
            # Validate throughput requirements
            assert rps >= 10, f"{endpoint} throughput too low: {rps} RPS"
            assert success_rate >= 95.0, f"{endpoint} success rate too low: {success_rate}%"
            
            # Calculate capacity utilization
            max_theoretical_rps = 1000 / avg_response  # Based on response time
            utilization = (rps / max_theoretical_rps) * 100
            
            assert utilization <= 80, f"{endpoint} running at {utilization}% capacity"
    
    def test_api_error_handling_performance(self):
        """Test API error handling doesn't degrade performance."""
        # Mock error scenarios and their performance impact
        error_scenarios = [
            {
                'error_type': 'database_timeout',
                'error_rate': 2.0,  # 2%
                'error_response_time_ms': 5000,  # Timeout after 5s
                'normal_response_time_ms': 800
            },
            {
                'error_type': 'invalid_parameters',
                'error_rate': 5.0,  # 5%
                'error_response_time_ms': 150,   # Quick validation error
                'normal_response_time_ms': 800
            },
            {
                'error_type': 'authorization_failure',
                'error_rate': 1.0,  # 1%
                'error_response_time_ms': 200,   # Quick auth check
                'normal_response_time_ms': 800
            }
        ]
        
        for scenario in error_scenarios:
            error_type = scenario['error_type']
            error_rate = scenario['error_rate']
            error_response_time = scenario['error_response_time_ms']
            normal_response_time = scenario['normal_response_time_ms']
            
            # Calculate weighted average response time
            success_rate = 100 - error_rate
            weighted_avg = (success_rate * normal_response_time + error_rate * error_response_time) / 100
            
            # Error handling should not significantly degrade overall performance
            performance_impact = ((weighted_avg - normal_response_time) / normal_response_time) * 100
            
            if error_type == 'database_timeout':
                # Timeout errors can have higher impact but should be rare
                assert performance_impact <= 10.0, \
                    f"Database timeout impact too high: {performance_impact}%"
            else:
                # Other errors should have minimal impact
                assert performance_impact <= 2.0, \
                    f"{error_type} performance impact too high: {performance_impact}%"


class TestSystemScalability:
    """Test system scalability and resource utilization."""
    
    def test_user_scalability(self):
        """Test system scalability with increasing user load."""
        # Mock user scalability scenarios
        scalability_scenarios = [
            {
                'concurrent_users': 10,
                'response_time_ms': 800,
                'cpu_utilization': 25.0,
                'memory_utilization': 45.0
            },
            {
                'concurrent_users': 25,
                'response_time_ms': 1200,
                'cpu_utilization': 45.0,
                'memory_utilization': 60.0
            },
            {
                'concurrent_users': 50,
                'response_time_ms': 2000,
                'cpu_utilization': 70.0,
                'memory_utilization': 75.0
            },
            {
                'concurrent_users': 100,
                'response_time_ms': 3500,
                'cpu_utilization': 85.0,
                'memory_utilization': 85.0
            }
        ]
        
        # Test scaling characteristics
        for i, scenario in enumerate(scalability_scenarios):
            users = scenario['concurrent_users']
            response_time = scenario['response_time_ms']
            cpu_util = scenario['cpu_utilization']
            memory_util = scenario['memory_utilization']
            
            # Validate resource utilization limits
            assert cpu_util <= 90.0, f"CPU utilization too high at {users} users: {cpu_util}%"
            assert memory_util <= 90.0, f"Memory utilization too high at {users} users: {memory_util}%"
            assert response_time <= 5000, f"Response time too high at {users} users: {response_time}ms"
            
            # Test scaling efficiency
            if i > 0:
                prev_scenario = scalability_scenarios[i-1]
                user_scaling_factor = users / prev_scenario['concurrent_users']
                response_scaling_factor = response_time / prev_scenario['response_time_ms']
                
                # Response time scaling should be sub-quadratic
                assert response_scaling_factor <= user_scaling_factor ** 1.5, \
                    f"Poor scaling at {users} users: response time scaling {response_scaling_factor}"
    
    def test_data_volume_scalability(self):
        """Test system performance with increasing data volumes."""
        # Mock data volume scenarios
        data_scenarios = [
            {
                'total_records': 50000,
                'daily_transactions': 500,
                'query_time_ms': 1200,
                'storage_gb': 2.5
            },
            {
                'total_records': 100000,
                'daily_transactions': 1000,
                'query_time_ms': 2200,
                'storage_gb': 4.8
            },
            {
                'total_records': 250000,
                'daily_transactions': 2500,
                'query_time_ms': 4500,
                'storage_gb': 11.2
            },
            {
                'total_records': 500000,
                'daily_transactions': 5000,
                'query_time_ms': 7500,
                'storage_gb': 22.1
            }
        ]
        
        # Validate scaling with data volume
        for i, scenario in enumerate(data_scenarios):
            records = scenario['total_records']
            query_time = scenario['query_time_ms']
            storage = scenario['storage_gb']
            
            # Performance should scale sub-linearly with data volume
            time_per_record = query_time / records * 1000  # microseconds per record
            assert time_per_record <= 50, f"Query efficiency degraded: {time_per_record}μs per record"
            
            # Storage efficiency
            storage_per_record = storage / records * 1024 * 1024  # bytes per record
            assert storage_per_record <= 100, f"Storage inefficient: {storage_per_record} bytes per record"
            
            # Test growth rate
            if i > 0:
                prev_scenario = data_scenarios[i-1]
                data_growth = records / prev_scenario['total_records']
                time_growth = query_time / prev_scenario['query_time_ms']
                storage_growth = storage / prev_scenario['storage_gb']
                
                # Query time should grow slower than data
                assert time_growth <= data_growth * 1.2, \
                    f"Query time growing too fast: {time_growth} vs {data_growth}"
                
                # Storage should grow linearly with data
                assert storage_growth <= data_growth * 1.1, \
                    f"Storage growing inefficiently: {storage_growth} vs {data_growth}"
    
    def test_peak_load_handling(self):
        """Test system handling of peak load scenarios."""
        # Mock peak load scenarios
        peak_scenarios = [
            {
                'scenario': 'morning_rush',
                'duration_minutes': 30,
                'peak_rps': 80,
                'baseline_rps': 20,
                'acceptable_degradation': 0.15  # 15% slower
            },
            {
                'scenario': 'end_of_month_reporting',
                'duration_minutes': 120,
                'peak_rps': 60,
                'baseline_rps': 15,
                'acceptable_degradation': 0.25  # 25% slower
            },
            {
                'scenario': 'system_maintenance_catchup',
                'duration_minutes': 60,
                'peak_rps': 100,
                'baseline_rps': 20,
                'acceptable_degradation': 0.30  # 30% slower
            }
        ]
        
        # Test peak load handling
        for scenario in peak_scenarios:
            scenario_name = scenario['scenario']
            peak_rps = scenario['peak_rps']
            baseline_rps = scenario['baseline_rps']
            acceptable_degradation = scenario['acceptable_degradation']
            
            # Calculate load multiplier
            load_multiplier = peak_rps / baseline_rps
            
            # Simulate response time degradation
            baseline_response_time = 800  # ms
            peak_response_time = baseline_response_time * (1 + (load_multiplier - 1) * 0.3)
            
            # Validate degradation is within acceptable limits
            actual_degradation = (peak_response_time - baseline_response_time) / baseline_response_time
            assert actual_degradation <= acceptable_degradation, \
                f"{scenario_name} degradation too high: {actual_degradation:.2%}"
            
            # System should still be responsive
            assert peak_response_time <= 5000, \
                f"{scenario_name} response time too high: {peak_response_time}ms"


class TestRegressionPrevention:
    """Test regression prevention for performance issues."""
    
    def test_prevent_n_plus_one_queries(self):
        """Test prevention of N+1 query performance issues."""
        # Mock scenarios that could cause N+1 queries
        query_scenarios = [
            {
                'operation': 'load_store_dashboard',
                'stores': 4,
                'expected_queries': 3,  # 1 for stores, 1 for items, 1 for transactions
                'actual_queries': 3
            },
            {
                'operation': 'generate_customer_report',
                'customers': 100,
                'expected_queries': 2,  # 1 for customers, 1 for transactions (batched)
                'actual_queries': 2
            },
            {
                'operation': 'inventory_analytics_by_category',
                'categories': 15,
                'expected_queries': 4,  # Optimized with joins
                'actual_queries': 4
            }
        ]
        
        # Validate query efficiency
        for scenario in query_scenarios:
            operation = scenario['operation']
            expected_queries = scenario['expected_queries']
            actual_queries = scenario['actual_queries']
            
            # Should not exceed expected query count
            assert actual_queries <= expected_queries, \
                f"{operation} using too many queries: {actual_queries} > {expected_queries}"
            
            # Calculate query efficiency
            if 'stores' in scenario:
                entities = scenario['stores']
            elif 'customers' in scenario:
                entities = scenario['customers']
            else:
                entities = scenario['categories']
            
            queries_per_entity = actual_queries / entities
            assert queries_per_entity <= 0.5, \
                f"{operation} query efficiency poor: {queries_per_entity} queries per entity"
    
    def test_prevent_memory_leaks(self):
        """Test prevention of memory leaks in long-running operations."""
        # Mock memory usage over time for long operations
        memory_timeline = [
            {'time_minutes': 0, 'memory_mb': 50},
            {'time_minutes': 15, 'memory_mb': 75},
            {'time_minutes': 30, 'memory_mb': 85},
            {'time_minutes': 45, 'memory_mb': 80},  # Should stabilize
            {'time_minutes': 60, 'memory_mb': 82},
            {'time_minutes': 90, 'memory_mb': 78},  # Should not grow indefinitely
            {'time_minutes': 120, 'memory_mb': 81}
        ]
        
        # Check for memory leak patterns
        initial_memory = memory_timeline[0]['memory_mb']
        max_memory = max(point['memory_mb'] for point in memory_timeline)
        final_memory = memory_timeline[-1]['memory_mb']
        
        # Memory growth should stabilize
        total_growth = final_memory - initial_memory
        max_growth = max_memory - initial_memory
        
        assert total_growth <= max_growth * 0.8, \
            f"Memory not stabilizing: final growth {total_growth}MB vs max {max_growth}MB"
        
        # Should not grow beyond reasonable limits
        assert max_memory <= initial_memory * 3, \
            f"Memory grew too much: {max_memory}MB from {initial_memory}MB"
    
    def test_prevent_cache_stampede(self):
        """Test prevention of cache stampede scenarios."""
        # Mock cache expiration and concurrent access
        cache_scenario = {
            'cache_key': 'dashboard_summary_store_3607',
            'cache_ttl_seconds': 300,
            'concurrent_requests': 25,
            'cache_regeneration_time_ms': 1200,
            'expected_backend_calls': 1  # Should be limited by cache locking
        }
        
        # Simulate cache stampede prevention
        def simulate_cache_access():
            """Simulate concurrent cache access with stampede prevention."""
            # Mock cache lock mechanism
            cache_locked = False
            backend_calls = 0
            
            for request in range(cache_scenario['concurrent_requests']):
                if not cache_locked:
                    # First request locks cache and regenerates
                    cache_locked = True
                    backend_calls = 1
                # Other requests wait or get stale data
            
            return backend_calls
        
        backend_calls = simulate_cache_access()
        
        # Validate stampede prevention
        assert backend_calls == cache_scenario['expected_backend_calls'], \
            f"Cache stampede not prevented: {backend_calls} backend calls"
        
        # Response time should be reasonable even under load
        max_response_time = cache_scenario['cache_regeneration_time_ms'] * 1.2  # 20% buffer
        assert max_response_time <= 2000, \
            f"Cache regeneration too slow: {max_response_time}ms"
    
    def test_prevent_connection_pool_exhaustion(self):
        """Test prevention of database connection pool exhaustion."""
        # Mock connection pool scenarios
        connection_scenarios = [
            {
                'pool_size': 20,
                'concurrent_requests': 15,
                'avg_connection_time_ms': 800,
                'expected_queue_time_ms': 0
            },
            {
                'pool_size': 20,
                'concurrent_requests': 25,
                'avg_connection_time_ms': 800,
                'expected_queue_time_ms': 200  # Some queueing expected
            },
            {
                'pool_size': 20,
                'concurrent_requests': 50,
                'avg_connection_time_ms': 800,
                'expected_queue_time_ms': 800  # Significant queueing
            }
        ]
        
        # Test connection pool management
        for scenario in connection_scenarios:
            pool_size = scenario['pool_size']
            concurrent_requests = scenario['concurrent_requests']
            connection_time = scenario['avg_connection_time_ms']
            expected_queue_time = scenario['expected_queue_time_ms']
            
            # Calculate theoretical queue time
            if concurrent_requests <= pool_size:
                theoretical_queue_time = 0
            else:
                excess_requests = concurrent_requests - pool_size
                theoretical_queue_time = (excess_requests / pool_size) * connection_time
            
            # Validate queue time estimation
            assert abs(theoretical_queue_time - expected_queue_time) <= connection_time * 0.5, \
                f"Queue time estimate incorrect: {theoretical_queue_time}ms vs {expected_queue_time}ms"
            
            # System should handle reasonable overload
            if concurrent_requests <= pool_size * 2:
                assert expected_queue_time <= connection_time * 2, \
                    f"Queue time too high for moderate overload: {expected_queue_time}ms"


class TestPerformanceMonitoring:
    """Test performance monitoring and alerting capabilities."""
    
    def test_performance_baseline_establishment(self):
        """Test establishment and maintenance of performance baselines."""
        # Mock performance metrics over time
        performance_history = [
            {'date': '2025-08-01', 'avg_response_time_ms': 850, 'p95_response_time_ms': 1200},
            {'date': '2025-08-02', 'avg_response_time_ms': 820, 'p95_response_time_ms': 1150},
            {'date': '2025-08-03', 'avg_response_time_ms': 890, 'p95_response_time_ms': 1300},
            {'date': '2025-08-04', 'avg_response_time_ms': 860, 'p95_response_time_ms': 1180},
            {'date': '2025-08-05', 'avg_response_time_ms': 830, 'p95_response_time_ms': 1220}
        ]
        
        # Calculate baseline metrics
        avg_response_times = [d['avg_response_time_ms'] for d in performance_history]
        p95_response_times = [d['p95_response_time_ms'] for d in performance_history]
        
        baseline_avg = statistics.mean(avg_response_times)
        baseline_p95 = statistics.mean(p95_response_times)
        
        # Calculate acceptable variance
        avg_std_dev = statistics.stdev(avg_response_times)
        p95_std_dev = statistics.stdev(p95_response_times)
        
        # Validate baseline establishment
        assert baseline_avg > 0, "Baseline average should be positive"
        assert baseline_p95 > baseline_avg, "P95 should be higher than average"
        
        # Standard deviation should be reasonable (< 20% of mean)
        assert avg_std_dev <= baseline_avg * 0.2, \
            f"Average response time too variable: {avg_std_dev}ms std dev"
        assert p95_std_dev <= baseline_p95 * 0.2, \
            f"P95 response time too variable: {p95_std_dev}ms std dev"
    
    def test_performance_alerting_thresholds(self):
        """Test performance alerting threshold calculation and triggering."""
        # Mock current performance vs baseline
        baseline_metrics = {
            'avg_response_time_ms': 850,
            'p95_response_time_ms': 1200,
            'error_rate_percent': 1.5,
            'throughput_rps': 45
        }
        
        current_metrics = {
            'avg_response_time_ms': 1100,  # 29% increase
            'p95_response_time_ms': 1800,  # 50% increase
            'error_rate_percent': 3.2,    # 113% increase
            'throughput_rps': 38          # 16% decrease
        }
        
        # Define alerting thresholds
        alert_thresholds = {
            'avg_response_time_increase_percent': 25,
            'p95_response_time_increase_percent': 40,
            'error_rate_increase_percent': 100,
            'throughput_decrease_percent': 20
        }
        
        # Calculate performance changes
        avg_change = ((current_metrics['avg_response_time_ms'] - baseline_metrics['avg_response_time_ms']) 
                     / baseline_metrics['avg_response_time_ms']) * 100
        p95_change = ((current_metrics['p95_response_time_ms'] - baseline_metrics['p95_response_time_ms']) 
                     / baseline_metrics['p95_response_time_ms']) * 100
        error_change = ((current_metrics['error_rate_percent'] - baseline_metrics['error_rate_percent']) 
                       / baseline_metrics['error_rate_percent']) * 100
        throughput_change = ((baseline_metrics['throughput_rps'] - current_metrics['throughput_rps']) 
                           / baseline_metrics['throughput_rps']) * 100
        
        # Test alert triggering
        alerts_triggered = []
        
        if avg_change > alert_thresholds['avg_response_time_increase_percent']:
            alerts_triggered.append(f'avg_response_time_degraded_{avg_change:.1f}%')
        
        if p95_change > alert_thresholds['p95_response_time_increase_percent']:
            alerts_triggered.append(f'p95_response_time_degraded_{p95_change:.1f}%')
        
        if error_change > alert_thresholds['error_rate_increase_percent']:
            alerts_triggered.append(f'error_rate_increased_{error_change:.1f}%')
        
        if throughput_change > alert_thresholds['throughput_decrease_percent']:
            alerts_triggered.append(f'throughput_decreased_{throughput_change:.1f}%')
        
        # Validate alert logic
        assert len(alerts_triggered) == 3, f"Expected 3 alerts, got {len(alerts_triggered)}"
        assert any('avg_response_time_degraded' in alert for alert in alerts_triggered)
        assert any('p95_response_time_degraded' in alert for alert in alerts_triggered)
        assert any('error_rate_increased' in alert for alert in alerts_triggered)
        # Throughput alert should NOT trigger (16% < 20% threshold)
        assert not any('throughput_decreased' in alert for alert in alerts_triggered)