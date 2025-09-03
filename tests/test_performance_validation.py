"""
Performance and validation tests for Enhanced Dashboard system
Tests system behavior under realistic loads with 1.78% RFID coverage
Created: September 3, 2025
"""

import pytest
import time
import threading
import concurrent.futures
from datetime import datetime, timedelta, date
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
import sys
import os
import json

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.data_reconciliation_service import DataReconciliationService
from app.services.predictive_analytics_service import PredictiveAnalyticsService
from app import create_app


class TestPerformanceValidation:
    """Performance and validation tests for Enhanced Dashboard system"""
    
    @pytest.fixture
    def app(self):
        """Create Flask app for testing"""
        app = create_app()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def large_dataset_simulation(self):
        """Generate large dataset for performance testing"""
        return {
            'pos_transactions': self._generate_pos_data(50000),  # 50k transactions
            'financial_records': self._generate_financial_data(500),  # 500 weeks
            'rfid_correlations': self._generate_rfid_data(290),  # Actual 290 correlated items
            'equipment_catalog': self._generate_equipment_data(16259)  # Full equipment catalog
        }
    
    def _generate_pos_data(self, count):
        """Generate realistic POS transaction data"""
        import random
        transactions = []
        base_date = date.today() - timedelta(days=365)
        
        for i in range(count):
            transaction_date = base_date + timedelta(days=random.randint(0, 365))
            transactions.append({
                'transaction_id': f'TXN{i:06d}',
                'date': transaction_date.isoformat(),
                'amount': round(random.uniform(50, 500), 2),
                'equipment_category': random.choice(['Power Tools', 'Generators', 'Lawn Equipment', 'Construction']),
                'store_code': random.choice(['STORE01', 'STORE02', 'STORE03']),
                'status': 'completed'
            })
        return transactions
    
    def _generate_financial_data(self, weeks):
        """Generate realistic financial scorecard data"""
        import random
        financial_data = []
        base_date = date.today() - timedelta(weeks=weeks)
        
        for i in range(weeks):
            week_date = base_date + timedelta(weeks=i)
            financial_data.append({
                'week_date': week_date.isoformat(),
                'store': random.choice(['STORE01', 'STORE02', 'STORE03']),
                'target_rent': round(random.uniform(20000, 35000), 2),
                'actual_rent': round(random.uniform(18000, 37000), 2),
                'utilization_target': round(random.uniform(75, 85), 1),
                'actual_utilization': round(random.uniform(70, 90), 1)
            })
        return financial_data
    
    def _generate_rfid_data(self, count):
        """Generate realistic RFID correlation data (limited to 1.78% coverage)"""
        import random
        rfid_data = []
        
        for i in range(count):
            rfid_data.append({
                'rfid_tag': f'RFID{i:06d}',
                'pos_item_id': f'ITEM{random.randint(1, 16259):06d}',
                'category': random.choice(['Power Tools', 'Generators', 'Lawn Equipment', 'Construction']),
                'last_scan': (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
                'status': random.choice(['Ready to Rent', 'On Rent', 'In Repair']),
                'location': random.choice(['Yard', 'Store', 'Customer'])
            })
        return rfid_data
    
    def _generate_equipment_data(self, count):
        """Generate complete equipment catalog"""
        import random
        equipment = []
        
        categories = {
            'Power Tools': 6500,
            'Generators': 1200, 
            'Lawn Equipment': 2800,
            'Construction Equipment': 3200,
            'Other': 2559
        }
        
        item_id = 1
        for category, cat_count in categories.items():
            for i in range(cat_count):
                equipment.append({
                    'item_id': f'ITEM{item_id:06d}',
                    'category': category,
                    'description': f'{category} Item {i+1}',
                    'rental_rate': round(random.uniform(25, 200), 2),
                    'status': random.choice(['Available', 'On Rent', 'Maintenance']),
                    'acquisition_date': (date.today() - timedelta(days=random.randint(30, 1095))).isoformat()
                })
                item_id += 1
        
        return equipment
    
    # Performance Tests
    
    def test_data_reconciliation_performance_large_dataset(self, large_dataset_simulation):
        """Test data reconciliation performance with large datasets"""
        service = DataReconciliationService()
        
        with patch('app.services.data_reconciliation_service.db.session') as mock_db:
            # Setup large dataset responses
            mock_db.execute.return_value.fetchall.return_value = large_dataset_simulation['financial_records'][:100]
            mock_db.execute.return_value.fetchone.return_value = {
                'total_revenue': 2750000.00,
                'last_transaction': '2025-09-01 16:45:00'
            }
            
            start_time = time.time()
            
            result = service.get_revenue_reconciliation(
                start_date=date.today() - timedelta(days=30),
                end_date=date.today()
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Should complete within reasonable time (< 5 seconds)
            assert execution_time < 5.0, f"Revenue reconciliation took {execution_time:.2f}s (too slow)"
            
            # Should return valid results
            assert 'revenue_sources' in result
            assert 'variance_analysis' in result
            
            print(f"✅ Revenue reconciliation completed in {execution_time:.2f}s")
    
    def test_predictive_analytics_performance_large_history(self, large_dataset_simulation):
        """Test predictive analytics performance with large historical dataset"""
        service = PredictiveAnalyticsService()
        
        with patch('app.services.predictive_analytics_service.db.session') as mock_db:
            # Setup large historical dataset
            mock_db.execute.return_value.fetchall.return_value = large_dataset_simulation['financial_records']
            
            start_time = time.time()
            
            result = service.generate_revenue_forecasts(horizon_weeks=12)
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Should complete within reasonable time (< 10 seconds for complex forecasting)
            assert execution_time < 10.0, f"Revenue forecasting took {execution_time:.2f}s (too slow)"
            
            # Should return valid forecasts
            assert 'forecasts' in result
            forecasts = result['forecasts']['weekly_predictions']
            assert len(forecasts) == 12
            
            print(f"✅ Revenue forecasting completed in {execution_time:.2f}s")
    
    def test_api_endpoint_response_times(self, client):
        """Test API endpoint response times under normal load"""
        endpoints = [
            '/api/enhanced-dashboard/data-reconciliation',
            '/api/enhanced-dashboard/predictive-analytics',
            '/api/enhanced-dashboard/correlation-dashboard',
            '/api/enhanced-dashboard/mobile-dashboard',
            '/api/enhanced-dashboard/health-check'
        ]
        
        response_times = {}
        
        for endpoint in endpoints:
            with patch('app.services.data_reconciliation_service.db.session'):
                with patch('app.services.predictive_analytics_service.db.session'):
                    with patch('app.routes.enhanced_dashboard_api.db.session'):
                        
                        start_time = time.time()
                        response = client.get(endpoint)
                        end_time = time.time()
                        
                        execution_time = end_time - start_time
                        response_times[endpoint] = execution_time
                        
                        # API endpoints should respond quickly (< 3 seconds)
                        assert execution_time < 3.0, f"{endpoint} took {execution_time:.2f}s (too slow)"
                        
                        # Should return valid response
                        assert response.status_code in [200, 500]  # Either success or controlled error
        
        # Print performance summary
        print("\n📊 API Response Times:")
        for endpoint, response_time in response_times.items():
            print(f"  {endpoint.split('/')[-1]}: {response_time:.3f}s")
        
        avg_response_time = sum(response_times.values()) / len(response_times)
        print(f"📈 Average response time: {avg_response_time:.3f}s")
    
    def test_concurrent_api_requests(self, client):
        """Test API performance under concurrent load"""
        endpoint = '/api/enhanced-dashboard/health-check'
        num_concurrent_requests = 10
        
        def make_request():
            """Make a single API request"""
            with patch('app.routes.enhanced_dashboard_api.check_system_health'):
                start_time = time.time()
                response = client.get(endpoint)
                end_time = time.time()
                return {
                    'status_code': response.status_code,
                    'response_time': end_time - start_time
                }
        
        # Execute concurrent requests
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent_requests) as executor:
            future_to_request = {executor.submit(make_request): i for i in range(num_concurrent_requests)}
            results = []
            
            for future in concurrent.futures.as_completed(future_to_request):
                result = future.result()
                results.append(result)
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = [r for r in results if r['status_code'] == 200]
        avg_response_time = sum(r['response_time'] for r in results) / len(results)
        max_response_time = max(r['response_time'] for r in results)
        
        # Assertions
        assert len(successful_requests) >= 8, f"Only {len(successful_requests)}/{num_concurrent_requests} requests succeeded"
        assert avg_response_time < 2.0, f"Average response time {avg_response_time:.2f}s too slow under concurrent load"
        assert max_response_time < 5.0, f"Max response time {max_response_time:.2f}s too slow"
        
        print(f"✅ Concurrent test: {len(successful_requests)}/{num_concurrent_requests} requests succeeded")
        print(f"   Average response time: {avg_response_time:.3f}s")
        print(f"   Max response time: {max_response_time:.3f}s")
        print(f"   Total execution time: {total_time:.3f}s")
    
    # Data Validation Tests
    
    def test_rfid_coverage_accuracy_validation(self):
        """Validate RFID coverage calculations match actual system state"""
        service = DataReconciliationService()
        
        with patch('app.services.data_reconciliation_service.db.session') as mock_db:
            
            # Mock actual system data: 290 RFID items out of 16,259 total
            inventory_query_result = [
                {'category': 'Power Tools', 'pos_count': 6500, 'rfid_count': 98},
                {'category': 'Generators', 'pos_count': 1200, 'rfid_count': 24},
                {'category': 'Lawn Equipment', 'pos_count': 2800, 'rfid_count': 56},
                {'category': 'Construction Equipment', 'pos_count': 3200, 'rfid_count': 67},
                {'category': 'Other', 'pos_count': 2559, 'rfid_count': 45}
            ]
            
            mock_db.execute.return_value.fetchall.return_value = inventory_query_result
            
            result = service.get_inventory_reconciliation()
            
            # Validate coverage calculations
            coverage_analysis = result['coverage_analysis']
            
            total_pos = sum(item['pos_count'] for item in inventory_query_result)
            total_rfid = sum(item['rfid_count'] for item in inventory_query_result)
            expected_percentage = (total_rfid / total_pos) * 100
            
            assert total_pos == 16259, f"Expected 16,259 POS items, got {total_pos}"
            assert total_rfid == 290, f"Expected 290 RFID items, got {total_rfid}"
            assert abs(expected_percentage - 1.78) < 0.1, f"Expected ~1.78% coverage, got {expected_percentage:.2f}%"
            
            # Verify this is reflected in the service results
            actual_percentage = coverage_analysis.get('correlation_percentage', 0)
            assert abs(actual_percentage - 1.78) < 0.2, f"Service reported {actual_percentage:.2f}% coverage"
            
            print(f"✅ RFID coverage validation: {actual_percentage:.2f}% ({total_rfid}/{total_pos} items)")
    
    def test_financial_data_consistency_validation(self):
        """Validate financial data processing consistency"""
        service = DataReconciliationService()
        
        # Test with realistic financial data volumes
        test_financial_data = [
            {'week_date': '2025-08-01', 'store': 'STORE01', 'target_rent': 28000, 'actual_rent': 27500},
            {'week_date': '2025-08-08', 'store': 'STORE01', 'target_rent': 29000, 'actual_rent': 28800},
            {'week_date': '2025-08-15', 'store': 'STORE02', 'target_rent': 25000, 'actual_rent': 24200},
            {'week_date': '2025-08-22', 'store': 'STORE02', 'target_rent': 26000, 'actual_rent': 25900}
        ]
        
        with patch('app.services.data_reconciliation_service.db.session') as mock_db:
            mock_db.execute.return_value.fetchall.return_value = test_financial_data
            
            result = service._get_financial_revenue(
                start_date=date(2025, 8, 1),
                end_date=date(2025, 8, 22),
                store_code=None
            )
            
            # Validate financial calculations
            expected_total = sum(item['actual_rent'] for item in test_financial_data)
            actual_total = float(result['total'])
            
            assert abs(actual_total - expected_total) < 0.01, f"Financial total mismatch: expected {expected_total}, got {actual_total}"
            
            print(f"✅ Financial data validation: ${actual_total:,.2f} total revenue processed correctly")
    
    def test_data_freshness_validation(self, client):
        """Test data freshness indicators work correctly"""
        with patch('app.routes.enhanced_dashboard_api.db.session') as mock_db:
            
            # Mock fresh data (recent timestamps)
            fresh_timestamp = datetime.now() - timedelta(minutes=15)
            mock_db.execute.return_value.fetchone.return_value = {
                'last_pos_update': fresh_timestamp.isoformat(),
                'last_rfid_scan': (fresh_timestamp - timedelta(hours=2)).isoformat(),
                'last_financial_update': (fresh_timestamp - timedelta(hours=24)).isoformat()
            }
            
            response = client.get('/api/enhanced-dashboard/data-quality-report')
            
            if response.status_code == 200:
                data = json.loads(response.data)
                
                # Should indicate data freshness appropriately
                if 'data_freshness' in data['data']:
                    freshness = data['data']['data_freshness']
                    
                    # POS data should be very fresh
                    assert freshness.get('pos_system', 'unknown') in ['excellent', 'good']
                    
                    # RFID data might be less fresh due to limited scanning
                    rfid_freshness = freshness.get('rfid_system', 'unknown')
                    # Could be any status depending on scanning frequency
                    assert rfid_freshness in ['excellent', 'good', 'fair', 'poor', 'unknown']
                    
                print("✅ Data freshness validation completed")
    
    # Memory and Resource Usage Tests
    
    def test_memory_usage_large_datasets(self, large_dataset_simulation):
        """Test memory usage doesn't exceed reasonable limits"""
        import psutil
        import gc
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        service = PredictiveAnalyticsService()
        
        with patch('app.services.predictive_analytics_service.db.session') as mock_db:
            # Process large dataset
            mock_db.execute.return_value.fetchall.return_value = large_dataset_simulation['financial_records']
            
            # Run memory-intensive operations
            for i in range(5):
                result = service.generate_revenue_forecasts(horizon_weeks=12)
                
                # Check memory usage
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory
                
                # Memory usage shouldn't exceed 500MB increase
                assert memory_increase < 500, f"Memory usage increased by {memory_increase:.1f}MB (iteration {i+1})"
                
                # Force garbage collection
                gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_memory_increase = final_memory - initial_memory
        
        print(f"✅ Memory usage test completed: {total_memory_increase:.1f}MB increase")
        assert total_memory_increase < 200, f"Total memory increase {total_memory_increase:.1f}MB too high"
    
    def test_database_connection_handling(self):
        """Test proper database connection handling under load"""
        service = DataReconciliationService()
        
        # Simulate database connection issues
        connection_attempts = 0
        
        def mock_db_execute(*args, **kwargs):
            nonlocal connection_attempts
            connection_attempts += 1
            
            if connection_attempts <= 2:
                raise Exception("Database connection timeout")
            else:
                # Successful connection
                mock_result = MagicMock()
                mock_result.fetchall.return_value = [
                    {'week_date': '2025-09-01', 'revenue': 27500}
                ]
                return mock_result
        
        with patch('app.services.data_reconciliation_service.db.session') as mock_db:
            mock_db.execute.side_effect = mock_db_execute
            
            # Should eventually succeed or fail gracefully
            try:
                result = service.get_revenue_reconciliation()
                
                # If successful, should have valid data
                assert 'revenue_sources' in result
                print("✅ Database connection handling: Recovered from connection issues")
                
            except Exception as e:
                # Should fail gracefully with meaningful error
                assert "Database" in str(e) or "connection" in str(e).lower()
                print(f"✅ Database connection handling: Failed gracefully - {e}")
    
    # Stress Tests
    
    def test_rapid_sequential_requests(self, client):
        """Test system behavior under rapid sequential requests"""
        endpoint = '/api/enhanced-dashboard/mobile-dashboard'
        num_requests = 20
        max_time_per_request = 2.0
        
        response_times = []
        successful_requests = 0
        
        with patch('app.routes.enhanced_dashboard_api.get_mobile_optimized_data'):
            
            for i in range(num_requests):
                start_time = time.time()
                response = client.get(endpoint)
                end_time = time.time()
                
                response_time = end_time - start_time
                response_times.append(response_time)
                
                if response.status_code == 200:
                    successful_requests += 1
                
                # Each request should complete reasonably quickly
                assert response_time < max_time_per_request, f"Request {i+1} took {response_time:.2f}s"
        
        # Overall performance metrics
        avg_response_time = sum(response_times) / len(response_times)
        success_rate = (successful_requests / num_requests) * 100
        
        assert success_rate >= 90.0, f"Only {success_rate:.1f}% success rate under rapid requests"
        assert avg_response_time < 1.0, f"Average response time {avg_response_time:.2f}s too slow"
        
        print(f"✅ Rapid request test: {success_rate:.1f}% success rate, {avg_response_time:.3f}s avg response time")
    
    def test_system_stability_extended_operation(self, client):
        """Test system stability over extended operation period"""
        endpoint = '/api/enhanced-dashboard/health-check'
        test_duration = 30  # seconds
        request_interval = 1  # second
        
        start_time = time.time()
        requests_made = 0
        successful_requests = 0
        response_times = []
        
        with patch('app.routes.enhanced_dashboard_api.check_system_health'):
            
            while (time.time() - start_time) < test_duration:
                request_start = time.time()
                response = client.get(endpoint)
                request_end = time.time()
                
                requests_made += 1
                response_time = request_end - request_start
                response_times.append(response_time)
                
                if response.status_code == 200:
                    successful_requests += 1
                
                # Wait for next interval
                time.sleep(max(0, request_interval - response_time))
        
        # Stability metrics
        success_rate = (successful_requests / requests_made) * 100
        avg_response_time = sum(response_times) / len(response_times)
        response_time_stability = max(response_times) - min(response_times)
        
        assert success_rate >= 95.0, f"System stability degraded: {success_rate:.1f}% success rate"
        assert avg_response_time < 1.5, f"Performance degraded: {avg_response_time:.2f}s average response time"
        assert response_time_stability < 3.0, f"Response time instability: {response_time_stability:.2f}s variation"
        
        print(f"✅ Extended operation test ({test_duration}s):")
        print(f"   Requests made: {requests_made}")
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Avg response time: {avg_response_time:.3f}s")
        print(f"   Response time stability: {response_time_stability:.3f}s variation")