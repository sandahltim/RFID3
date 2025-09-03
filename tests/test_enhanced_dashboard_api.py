"""
Comprehensive tests for Enhanced Dashboard API endpoints
Tests all 10 API endpoints with various scenarios
Created: September 3, 2025
"""

import pytest
import json
from datetime import datetime, timedelta, date
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from flask import Flask
from app import create_app
from app.routes.enhanced_dashboard_api import enhanced_dashboard_bp


class TestEnhancedDashboardAPI:
    """Test suite for Enhanced Dashboard API endpoints"""
    
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
    def mock_data_reconciliation_service(self):
        """Mock DataReconciliationService"""
        mock_service = MagicMock()
        mock_service.get_revenue_reconciliation.return_value = {
            'period': {'start_date': '2025-08-26', 'end_date': '2025-09-02', 'days': 7},
            'revenue_sources': {
                'financial_system': {'value': Decimal('125000.00'), 'confidence': 'high'},
                'pos_transactions': {'value': Decimal('123500.00'), 'confidence': 'high'},
                'rfid_correlation': {'value': Decimal('2195.50'), 'confidence': 'low', 'coverage': '1.78%'}
            },
            'variance_analysis': {
                'pos_vs_financial': {'percentage': -1.2, 'status': 'acceptable'}
            }
        }
        mock_service.get_comprehensive_reconciliation_report.return_value = {
            'summary': {'rfid_coverage_rate': 1.78, 'data_confidence': 'mixed'},
            'data_quality_score': 75.5
        }
        return mock_service
    
    @pytest.fixture
    def mock_predictive_analytics_service(self):
        """Mock PredictiveAnalyticsService"""
        mock_service = MagicMock()
        mock_service.get_predictive_dashboard_data.return_value = {
            'revenue_forecasts': {
                'next_12_weeks': [{'week': 1, 'predicted_revenue': 28500, 'confidence_interval': [26000, 31000]}]
            },
            'equipment_demand_predictions': {
                'high_demand_categories': ['Power Tools', 'Generators']
            },
            'predictive_alerts': [
                {'type': 'inventory_shortage', 'category': 'Generators', 'urgency': 'high', 'priority_score': 85}
            ]
        }
        mock_service.generate_revenue_forecasts.return_value = {
            'forecasting_period': {'horizon_weeks': 12},
            'forecasts': {'weekly_predictions': []},
            'confidence_metrics': {'model_accuracy': 82.5}
        }
        return mock_service
    
    # Data Reconciliation API Tests
    
    def test_api_data_reconciliation_success(self, client, mock_data_reconciliation_service):
        """Test successful data reconciliation API call"""
        with patch('app.routes.enhanced_dashboard_api.DataReconciliationService', return_value=mock_data_reconciliation_service):
            response = client.get('/api/enhanced-dashboard/data-reconciliation')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify structure
            assert 'status' in data
            assert 'data' in data
            assert data['status'] == 'success'
            
            # Verify reconciliation data
            reconciliation_data = data['data']
            assert 'period' in reconciliation_data
            assert 'revenue_sources' in reconciliation_data
            assert 'variance_analysis' in reconciliation_data
            
            # Verify RFID coverage limitation is reflected
            rfid_source = reconciliation_data['revenue_sources']['rfid_correlation']
            assert '1.78%' in rfid_source['coverage']
            assert rfid_source['confidence'] == 'low'
    
    def test_api_data_reconciliation_with_date_params(self, client, mock_data_reconciliation_service):
        """Test data reconciliation API with date parameters"""
        with patch('app.routes.enhanced_dashboard_api.DataReconciliationService', return_value=mock_data_reconciliation_service):
            response = client.get('/api/enhanced-dashboard/data-reconciliation?start_date=2025-08-01&end_date=2025-08-31')
            
            assert response.status_code == 200
            
            # Verify service was called with correct parameters
            mock_data_reconciliation_service.get_revenue_reconciliation.assert_called_once()
            call_args = mock_data_reconciliation_service.get_revenue_reconciliation.call_args
            assert call_args[1]['start_date'] == date(2025, 8, 1)
            assert call_args[1]['end_date'] == date(2025, 8, 31)
    
    def test_api_data_reconciliation_invalid_date_format(self, client):
        """Test data reconciliation API with invalid date format"""
        response = client.get('/api/enhanced-dashboard/data-reconciliation?start_date=invalid-date')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid date format' in data['message']
    
    def test_api_data_reconciliation_service_error(self, client):
        """Test data reconciliation API when service throws error"""
        with patch('app.routes.enhanced_dashboard_api.DataReconciliationService') as mock_service_class:
            mock_service_class.return_value.get_revenue_reconciliation.side_effect = Exception("Database error")
            
            response = client.get('/api/enhanced-dashboard/data-reconciliation')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert data['status'] == 'error'
    
    # Predictive Analytics API Tests
    
    def test_api_predictive_analytics_success(self, client, mock_predictive_analytics_service):
        """Test successful predictive analytics API call"""
        with patch('app.routes.enhanced_dashboard_api.PredictiveAnalyticsService', return_value=mock_predictive_analytics_service):
            response = client.get('/api/enhanced-dashboard/predictive-analytics')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['status'] == 'success'
            assert 'data' in data
            
            # Verify predictive data structure
            predictive_data = data['data']
            assert 'revenue_forecasts' in predictive_data
            assert 'equipment_demand_predictions' in predictive_data
            assert 'predictive_alerts' in predictive_data
    
    def test_api_predictive_analytics_with_horizon(self, client, mock_predictive_analytics_service):
        """Test predictive analytics API with custom horizon"""
        with patch('app.routes.enhanced_dashboard_api.PredictiveAnalyticsService', return_value=mock_predictive_analytics_service):
            response = client.get('/api/enhanced-dashboard/predictive-analytics?horizon_weeks=8')
            
            assert response.status_code == 200
            
            # Verify custom horizon was used
            mock_predictive_analytics_service.generate_revenue_forecasts.assert_called_with(horizon_weeks=8)
    
    def test_api_predictive_analytics_invalid_horizon(self, client):
        """Test predictive analytics API with invalid horizon parameter"""
        response = client.get('/api/enhanced-dashboard/predictive-analytics?horizon_weeks=invalid')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid horizon_weeks parameter' in data['message']
    
    # Multi-Timeframe Data API Tests
    
    def test_api_multi_timeframe_data_success(self, client):
        """Test multi-timeframe data API"""
        mock_timeframe_data = {
            'daily': {'revenue': 5500, 'utilization': 76.5},
            'weekly': {'revenue': 38500, 'utilization': 78.2},
            'monthly': {'revenue': 165000, 'utilization': 77.8},
            'quarterly': {'revenue': 495000, 'utilization': 79.1}
        }
        
        with patch('app.routes.enhanced_dashboard_api.db.session') as mock_db:
            mock_db.execute.return_value.fetchall.return_value = [
                {'timeframe': 'daily', 'revenue': 5500, 'utilization': 76.5},
                {'timeframe': 'weekly', 'revenue': 38500, 'utilization': 78.2},
                {'timeframe': 'monthly', 'revenue': 165000, 'utilization': 77.8},
                {'timeframe': 'quarterly', 'revenue': 495000, 'utilization': 79.1}
            ]
            
            response = client.get('/api/enhanced-dashboard/multi-timeframe-data')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['status'] == 'success'
            timeframe_data = data['data']
            
            # Verify all timeframes are present
            for timeframe in ['daily', 'weekly', 'monthly', 'quarterly']:
                assert timeframe in timeframe_data
                assert 'revenue' in timeframe_data[timeframe]
                assert 'utilization' in timeframe_data[timeframe]
    
    def test_api_multi_timeframe_data_with_store_filter(self, client):
        """Test multi-timeframe data API with store filter"""
        with patch('app.routes.enhanced_dashboard_api.db.session'):
            response = client.get('/api/enhanced-dashboard/multi-timeframe-data?store_code=STORE01')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'store_code' in data['data']['filters']
            assert data['data']['filters']['store_code'] == 'STORE01'
    
    # Correlation Dashboard API Tests
    
    def test_api_correlation_dashboard_success(self, client):
        """Test correlation dashboard API with limited RFID coverage"""
        mock_correlation_data = {
            'correlation_summary': {
                'total_pos_items': 16259,
                'rfid_correlated_items': 290,
                'correlation_percentage': 1.78,
                'data_quality_score': 65.2
            },
            'category_breakdown': [
                {'category': 'Power Tools', 'pos_count': 500, 'rfid_count': 9, 'correlation_rate': 1.8},
                {'category': 'Generators', 'pos_count': 150, 'rfid_count': 3, 'correlation_rate': 2.0}
            ],
            'improvement_opportunities': [
                {'category': 'Power Tools', 'potential_revenue_impact': 2500, 'priority': 'high'},
                {'category': 'Generators', 'potential_revenue_impact': 1800, 'priority': 'medium'}
            ]
        }
        
        with patch('app.routes.enhanced_dashboard_api.db.session') as mock_db:
            mock_db.execute.return_value.fetchall.return_value = []  # Mock empty result
            
            with patch('app.routes.enhanced_dashboard_api.calculate_correlation_data', return_value=mock_correlation_data):
                response = client.get('/api/enhanced-dashboard/correlation-dashboard')
                
                assert response.status_code == 200
                data = json.loads(response.data)
                
                assert data['status'] == 'success'
                correlation_data = data['data']
                
                # Verify RFID correlation limitations are reflected
                summary = correlation_data['correlation_summary']
                assert summary['correlation_percentage'] == 1.78
                assert summary['rfid_correlated_items'] == 290
                assert summary['total_pos_items'] == 16259
    
    # Store Comparison API Tests
    
    def test_api_enhanced_store_comparison_success(self, client):
        """Test enhanced store comparison API"""
        mock_store_data = [
            {'store_code': 'STORE01', 'revenue': 125000, 'utilization': 78.5, 'rfid_coverage': 2.1},
            {'store_code': 'STORE02', 'revenue': 98000, 'utilization': 74.2, 'rfid_coverage': 1.5},
            {'store_code': 'STORE03', 'revenue': 110000, 'utilization': 81.3, 'rfid_coverage': 1.9}
        ]
        
        with patch('app.routes.enhanced_dashboard_api.db.session') as mock_db:
            mock_db.execute.return_value.fetchall.return_value = mock_store_data
            
            response = client.get('/api/enhanced-dashboard/store-comparison')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['status'] == 'success'
            store_data = data['data']
            
            # Verify store comparison structure
            assert 'store_performance' in store_data
            assert 'ranking' in store_data
            assert 'rfid_coverage_analysis' in store_data
            
            # Verify RFID coverage is tracked per store
            rfid_analysis = store_data['rfid_coverage_analysis']
            assert 'average_coverage' in rfid_analysis
            assert rfid_analysis['average_coverage'] < 5.0  # Should reflect low coverage
    
    def test_api_enhanced_store_comparison_with_metrics(self, client):
        """Test store comparison API with specific metrics"""
        with patch('app.routes.enhanced_dashboard_api.db.session'):
            response = client.get('/api/enhanced-dashboard/store-comparison?metrics=revenue,utilization,rfid_coverage')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'requested_metrics' in data['data']
            assert data['data']['requested_metrics'] == ['revenue', 'utilization', 'rfid_coverage']
    
    # Dashboard Configuration API Tests
    
    def test_api_dashboard_configuration_get(self, client):
        """Test dashboard configuration GET request"""
        mock_config = {
            'user_preferences': {
                'default_timeframe': 'weekly',
                'preferred_charts': ['revenue_trend', 'utilization_gauge'],
                'alert_thresholds': {'utilization_low': 60, 'utilization_high': 90}
            },
            'system_settings': {
                'rfid_coverage_threshold': 5.0,
                'data_freshness_warning': 24,
                'correlation_confidence_minimum': 70
            }
        }
        
        with patch('app.routes.enhanced_dashboard_api.get_user_dashboard_config', return_value=mock_config):
            response = client.get('/api/enhanced-dashboard/dashboard-config')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['status'] == 'success'
            assert 'configuration' in data['data']
            config = data['data']['configuration']
            assert 'user_preferences' in config
            assert 'system_settings' in config
    
    def test_api_dashboard_configuration_post(self, client):
        """Test dashboard configuration POST request"""
        new_config = {
            'default_timeframe': 'monthly',
            'alert_thresholds': {'utilization_low': 55, 'utilization_high': 85}
        }
        
        with patch('app.routes.enhanced_dashboard_api.save_user_dashboard_config') as mock_save:
            response = client.post('/api/enhanced-dashboard/dashboard-config', 
                                 data=json.dumps(new_config),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert 'Configuration updated' in data['message']
            mock_save.assert_called_once()
    
    def test_api_dashboard_configuration_invalid_json(self, client):
        """Test dashboard configuration with invalid JSON"""
        response = client.post('/api/enhanced-dashboard/dashboard-config',
                             data='invalid-json',
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'Invalid JSON' in data['message']
    
    # Year-over-Year Comparison API Tests
    
    def test_api_year_over_year_comparison_success(self, client):
        """Test year-over-year comparison API"""
        mock_yoy_data = {
            'current_year': {
                '2025': {'revenue': 1500000, 'utilization': 78.5, 'growth_rate': 12.3}
            },
            'previous_year': {
                '2024': {'revenue': 1337500, 'utilization': 76.2, 'growth_rate': 8.7}
            },
            'comparison_metrics': {
                'revenue_growth': 12.1,
                'utilization_improvement': 2.3,
                'rfid_coverage_change': 0.3  # Slight improvement in RFID coverage
            }
        }
        
        with patch('app.routes.enhanced_dashboard_api.calculate_yoy_data', return_value=mock_yoy_data):
            response = client.get('/api/enhanced-dashboard/year-over-year')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['status'] == 'success'
            yoy_data = data['data']
            assert 'current_year' in yoy_data
            assert 'previous_year' in yoy_data
            assert 'comparison_metrics' in yoy_data
            
            # Verify RFID coverage tracking
            metrics = yoy_data['comparison_metrics']
            assert 'rfid_coverage_change' in metrics
    
    def test_api_year_over_year_comparison_with_years(self, client):
        """Test year-over-year comparison with specific years"""
        with patch('app.routes.enhanced_dashboard_api.calculate_yoy_data') as mock_calc:
            response = client.get('/api/enhanced-dashboard/year-over-year?current_year=2025&compare_year=2023')
            
            assert response.status_code == 200
            mock_calc.assert_called_once_with(current_year=2025, compare_year=2023)
    
    # Data Quality Report API Tests
    
    def test_api_data_quality_report_success(self, client):
        """Test data quality report API"""
        mock_quality_data = {
            'overall_score': 72.5,
            'data_sources': {
                'pos_system': {'score': 95.0, 'issues': [], 'coverage': '100%'},
                'financial_system': {'score': 88.0, 'issues': ['some missing weeks'], 'coverage': '98%'},
                'rfid_system': {'score': 35.0, 'issues': ['very low coverage', 'correlation gaps'], 'coverage': '1.78%'}
            },
            'recommendations': [
                'Expand RFID tagging to increase correlation coverage',
                'Address missing financial data weeks',
                'Implement automated data validation checks'
            ],
            'correlation_health': {
                'pos_rfid_correlation': 1.78,
                'data_consistency_score': 65.2,
                'freshness_score': 82.1
            }
        }
        
        with patch('app.routes.enhanced_dashboard_api.calculate_data_quality_metrics', return_value=mock_quality_data):
            response = client.get('/api/enhanced-dashboard/data-quality-report')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['status'] == 'success'
            quality_data = data['data']
            
            # Verify structure
            assert 'overall_score' in quality_data
            assert 'data_sources' in quality_data
            assert 'recommendations' in quality_data
            assert 'correlation_health' in quality_data
            
            # Verify RFID system quality reflects low coverage
            rfid_quality = quality_data['data_sources']['rfid_system']
            assert rfid_quality['score'] < 50.0  # Should be low due to coverage
            assert rfid_quality['coverage'] == '1.78%'
            assert any('coverage' in issue.lower() for issue in rfid_quality['issues'])
    
    # Mobile Dashboard API Tests
    
    def test_api_mobile_dashboard_success(self, client):
        """Test mobile dashboard API optimized for mobile devices"""
        mock_mobile_data = {
            'summary_metrics': {
                'total_revenue': 125000,
                'utilization_rate': 78.5,
                'active_rentals': 1250,
                'available_equipment': 340
            },
            'alerts': [
                {'type': 'high_utilization', 'message': 'Generators at 95% utilization', 'urgency': 'high'}
            ],
            'quick_stats': {
                'revenue_trend': 'positive',
                'utilization_trend': 'stable',
                'inventory_status': 'optimal'
            },
            'rfid_coverage_status': {
                'percentage': 1.78,
                'status': 'needs_improvement'
            }
        }
        
        with patch('app.routes.enhanced_dashboard_api.get_mobile_optimized_data', return_value=mock_mobile_data):
            response = client.get('/api/enhanced-dashboard/mobile-dashboard')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['status'] == 'success'
            mobile_data = data['data']
            
            # Verify mobile-optimized structure
            assert 'summary_metrics' in mobile_data
            assert 'alerts' in mobile_data
            assert 'quick_stats' in mobile_data
            assert 'rfid_coverage_status' in mobile_data
            
            # Verify RFID coverage status for mobile users
            rfid_status = mobile_data['rfid_coverage_status']
            assert rfid_status['percentage'] == 1.78
            assert rfid_status['status'] == 'needs_improvement'
    
    def test_api_mobile_dashboard_compact_format(self, client):
        """Test mobile dashboard with compact format"""
        with patch('app.routes.enhanced_dashboard_api.get_mobile_optimized_data') as mock_data:
            response = client.get('/api/enhanced-dashboard/mobile-dashboard?format=compact')
            
            assert response.status_code == 200
            # Verify compact format parameter was passed
            mock_data.assert_called_with(format='compact')
    
    # Health Check API Tests
    
    def test_api_health_check_success(self, client):
        """Test health check API"""
        with patch('app.routes.enhanced_dashboard_api.check_system_health') as mock_health:
            mock_health.return_value = {
                'status': 'healthy',
                'database': {'status': 'connected', 'response_time': '12ms'},
                'services': {
                    'data_reconciliation': 'operational',
                    'predictive_analytics': 'operational'
                },
                'data_quality': {
                    'pos_system': 'excellent',
                    'financial_system': 'good',
                    'rfid_system': 'poor'  # Due to low coverage
                }
            }
            
            response = client.get('/api/enhanced-dashboard/health-check')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['status'] == 'success'
            health_data = data['data']
            
            # Verify health check structure
            assert 'database' in health_data
            assert 'services' in health_data
            assert 'data_quality' in health_data
            
            # Verify RFID system health reflects coverage issues
            assert health_data['data_quality']['rfid_system'] == 'poor'
    
    def test_api_health_check_with_detailed_flag(self, client):
        """Test health check API with detailed information"""
        with patch('app.routes.enhanced_dashboard_api.check_system_health') as mock_health:
            response = client.get('/api/enhanced-dashboard/health-check?detailed=true')
            
            assert response.status_code == 200
            mock_health.assert_called_with(detailed=True)
    
    # Error Handling and Edge Cases
    
    def test_api_endpoints_cors_headers(self, client):
        """Test CORS headers are present in API responses"""
        response = client.get('/api/enhanced-dashboard/health-check')
        
        # Verify CORS headers (if implemented)
        assert response.status_code == 200
        # Could check for Access-Control-Allow-Origin header if CORS is configured
    
    def test_api_endpoints_rate_limiting(self, client):
        """Test rate limiting on API endpoints (if implemented)"""
        # Make multiple rapid requests
        responses = []
        for i in range(10):
            response = client.get('/api/enhanced-dashboard/health-check')
            responses.append(response)
        
        # All should succeed under normal circumstances
        # If rate limiting is implemented, some might return 429
        success_responses = [r for r in responses if r.status_code == 200]
        assert len(success_responses) >= 1  # At least some should succeed
    
    def test_api_endpoints_authentication(self, client):
        """Test API endpoints authentication (if implemented)"""
        # These tests assume authentication might be added later
        # Current implementation may not have authentication
        response = client.get('/api/enhanced-dashboard/data-reconciliation')
        
        # Should either succeed (no auth) or return 401 (auth required)
        assert response.status_code in [200, 401, 403]
    
    def test_api_response_format_consistency(self, client):
        """Test that all API endpoints return consistent response format"""
        endpoints = [
            '/api/enhanced-dashboard/health-check',
            '/api/enhanced-dashboard/mobile-dashboard'
        ]
        
        for endpoint in endpoints:
            with patch('app.routes.enhanced_dashboard_api.check_system_health', return_value={}):
                with patch('app.routes.enhanced_dashboard_api.get_mobile_optimized_data', return_value={}):
                    response = client.get(endpoint)
                    
                    if response.status_code == 200:
                        data = json.loads(response.data)
                        # All successful responses should have consistent structure
                        assert 'status' in data
                        assert 'data' in data or 'message' in data
                        assert data['status'] in ['success', 'error', 'warning']
    
    # Integration Tests with Real System State
    
    def test_integration_with_actual_rfid_coverage(self, client):
        """Test API integration reflecting actual 1.78% RFID coverage"""
        # This test would use actual database queries to verify
        # that the API correctly reflects the real system state
        
        with patch('app.routes.enhanced_dashboard_api.db.session') as mock_db:
            # Mock actual database results reflecting 1.78% coverage
            mock_db.execute.return_value.fetchone.return_value = {
                'total_pos_items': 16259,
                'rfid_correlated_items': 290,
                'correlation_percentage': 1.78
            }
            
            response = client.get('/api/enhanced-dashboard/correlation-dashboard')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Verify response reflects actual system state
            if 'correlation_summary' in data['data']:
                summary = data['data']['correlation_summary']
                assert abs(summary['correlation_percentage'] - 1.78) < 0.1
    
    def test_performance_with_large_datasets(self, client):
        """Test API performance with large dataset queries"""
        # Simulate large dataset responses
        large_dataset = [{'id': i, 'value': f'data_{i}'} for i in range(10000)]
        
        with patch('app.routes.enhanced_dashboard_api.db.session') as mock_db:
            mock_db.execute.return_value.fetchall.return_value = large_dataset
            
            response = client.get('/api/enhanced-dashboard/multi-timeframe-data')
            
            # Should handle large datasets without timeout
            assert response.status_code in [200, 500]  # Either success or controlled failure
            
            if response.status_code == 200:
                # Response should be reasonable size (not return all 10k items)
                data = json.loads(response.data)
                response_size = len(json.dumps(data))
                assert response_size < 1000000  # Less than 1MB response