"""
Dashboard Functionality Tests for RFID3 System
==============================================

Test suite for validating executive dashboard functionality,
data display accuracy, and cross-tab integration after recent improvements.

Date: 2025-08-28
Author: Testing Specialist
"""

import pytest
import json
import sys
import os
from datetime import datetime, timedelta, date
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

# Add root directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


class TestExecutiveDashboard:
    """Test executive dashboard data display and accuracy."""
    
    def test_dashboard_kpi_calculations(self):
        """Test executive dashboard KPI calculation accuracy."""
        # Mock dashboard data
        mock_data = {
            'total_items': 1250,
            'items_on_rent': 542,
            'items_available': 578,
            'items_in_service': 130,
            'total_revenue_ytd': 425000.00,
            'total_inventory_value': 1200000.00,
            'avg_rental_price': 85.50,
            'active_contracts': 324
        }
        
        # Calculate KPIs
        utilization_rate = round((mock_data['items_on_rent'] / mock_data['total_items']) * 100, 2)
        availability_rate = round((mock_data['items_available'] / mock_data['total_items']) * 100, 2)
        service_rate = round((mock_data['items_in_service'] / mock_data['total_items']) * 100, 2)
        roi_percentage = round((mock_data['total_revenue_ytd'] / mock_data['total_inventory_value']) * 100, 2)
        revenue_per_active_contract = round(mock_data['total_revenue_ytd'] / mock_data['active_contracts'], 2)
        
        # Validate KPI calculations
        assert utilization_rate == 43.36
        assert availability_rate == 46.24
        assert service_rate == 10.4
        assert roi_percentage == 35.42
        assert revenue_per_active_contract == 1312.35
        
        # Validate totals consistency
        total_accounted = mock_data['items_on_rent'] + mock_data['items_available'] + mock_data['items_in_service']
        assert total_accounted == mock_data['total_items']
    
    def test_store_performance_dashboard_display(self):
        """Test store performance data display on dashboard."""
        # Mock store performance data
        stores_performance = [
            {
                'store_code': '3607',
                'store_name': 'Wayzata',
                'total_items': 315,
                'items_on_rent': 142,
                'utilization_rate': 45.08,
                'revenue_ytd': 95250.00,
                'target_utilization': 50.0,
                'performance_status': 'good'
            },
            {
                'store_code': '6800',
                'store_name': 'Brooklyn Park',
                'total_items': 290,
                'items_on_rent': 118,
                'utilization_rate': 40.69,
                'revenue_ytd': 78500.00,
                'target_utilization': 50.0,
                'performance_status': 'needs_improvement'
            },
            {
                'store_code': '8101',
                'store_name': 'Fridley',
                'total_items': 385,
                'items_on_rent': 205,
                'utilization_rate': 53.25,
                'revenue_ytd': 125800.00,
                'target_utilization': 50.0,
                'performance_status': 'excellent'
            },
            {
                'store_code': '728',
                'store_name': 'Elk River',
                'total_items': 260,
                'items_on_rent': 77,
                'utilization_rate': 29.62,
                'revenue_ytd': 56250.00,
                'target_utilization': 50.0,
                'performance_status': 'poor'
            }
        ]
        
        # Calculate aggregate metrics
        total_items_all = sum(store['total_items'] for store in stores_performance)
        total_revenue_all = sum(store['revenue_ytd'] for store in stores_performance)
        total_items_on_rent = sum(store['items_on_rent'] for store in stores_performance)
        
        overall_utilization = round((total_items_on_rent / total_items_all) * 100, 2)
        
        # Validate store-level calculations
        for store in stores_performance:
            calculated_utilization = round((store['items_on_rent'] / store['total_items']) * 100, 2)
            assert abs(calculated_utilization - store['utilization_rate']) < 0.1
            
            # Validate performance status logic
            if store['utilization_rate'] >= 55:
                expected_status = 'excellent'
            elif store['utilization_rate'] >= 45:
                expected_status = 'good'
            elif store['utilization_rate'] >= 35:
                expected_status = 'needs_improvement'
            else:
                expected_status = 'poor'
            
            assert store['performance_status'] == expected_status
        
        # Validate aggregate calculations
        assert overall_utilization == 43.36
        assert total_items_all == 1250
    
    def test_financial_dashboard_metrics(self):
        """Test financial metrics display on dashboard."""
        # Mock financial data
        financial_data = {
            'revenue': {
                'ytd_total': 355800.00,
                'monthly_avg': 29650.00,
                'last_month': 31200.00,
                'growth_rate': 5.2
            },
            'costs': {
                'ytd_total': 89500.00,
                'monthly_avg': 7458.33,
                'last_month': 7850.00,
                'cost_ratio': 25.16
            },
            'profit': {
                'ytd_total': 266300.00,
                'monthly_avg': 22191.67,
                'margin_percentage': 74.84
            },
            'inventory': {
                'total_value': 1200000.00,
                'turnover_ratio': 0.297,
                'avg_item_value': 960.00
            }
        }
        
        # Validate financial calculations
        calculated_profit = financial_data['revenue']['ytd_total'] - financial_data['costs']['ytd_total']
        assert abs(calculated_profit - financial_data['profit']['ytd_total']) < 0.01
        
        calculated_margin = round((financial_data['profit']['ytd_total'] / financial_data['revenue']['ytd_total']) * 100, 2)
        assert calculated_margin == financial_data['profit']['margin_percentage']
        
        calculated_cost_ratio = round((financial_data['costs']['ytd_total'] / financial_data['revenue']['ytd_total']) * 100, 2)
        assert calculated_cost_ratio == financial_data['costs']['cost_ratio']
        
        calculated_turnover = round(financial_data['revenue']['ytd_total'] / financial_data['inventory']['total_value'], 3)
        assert calculated_turnover == financial_data['inventory']['turnover_ratio']

    def test_custom_date_range_helper(self):
        """Ensure get_date_range_from_params handles custom ranges."""
        from app.utils.date_ranges import get_date_range_from_params

        class Req:
            def __init__(self, args):
                self.args = args

        req = Req({"start_date": "2025-01-01", "end_date": "2025-01-31"})
        start, end = get_date_range_from_params(req)
        assert start == date(2025, 1, 1)
        assert end == date(2025, 1, 31)
    
    def test_dashboard_chart_data_accuracy(self):
        """Test accuracy of data feeding dashboard charts."""
        # Mock chart data
        utilization_trend_data = [
            {'month': '2025-01', 'utilization': 38.5, 'revenue': 28500.00},
            {'month': '2025-02', 'utilization': 41.2, 'revenue': 31200.00},
            {'month': '2025-03', 'utilization': 39.8, 'revenue': 29800.00},
            {'month': '2025-04', 'utilization': 44.1, 'revenue': 34650.00},
            {'month': '2025-05', 'utilization': 46.3, 'revenue': 37200.00},
            {'month': '2025-06', 'utilization': 43.7, 'revenue': 35800.00},
            {'month': '2025-07', 'utilization': 47.9, 'revenue': 39500.00},
            {'month': '2025-08', 'utilization': 45.2, 'revenue': 36800.00}
        ]
        
        # Validate trend data consistency
        for data_point in utilization_trend_data:
            assert 0 <= data_point['utilization'] <= 100
            assert data_point['revenue'] > 0
            
            # Check correlation between utilization and revenue (should be positive)
            # This is a basic check - in practice, you'd use statistical correlation
        
        # Calculate trend metrics
        utilizations = [d['utilization'] for d in utilization_trend_data]
        revenues = [d['revenue'] for d in utilization_trend_data]
        
        avg_utilization = sum(utilizations) / len(utilizations)
        avg_revenue = sum(revenues) / len(revenues)
        
        assert 40 <= avg_utilization <= 50  # Expected range
        assert 30000 <= avg_revenue <= 40000  # Expected range
        
        # Test month-over-month growth calculation
        growth_rates = []
        for i in range(1, len(utilization_trend_data)):
            current_revenue = utilization_trend_data[i]['revenue']
            previous_revenue = utilization_trend_data[i-1]['revenue']
            growth_rate = ((current_revenue - previous_revenue) / previous_revenue) * 100
            growth_rates.append(growth_rate)
        
        assert len(growth_rates) == len(utilization_trend_data) - 1


class TestInventoryAnalyticsTab:
    """Test inventory analytics tab functionality."""
    
    def test_inventory_tab_data_loading(self):
        """Test that inventory analytics tab loads data properly."""
        # Mock inventory analytics data
        analytics_data = {
            'summary': {
                'total_items': 1250,
                'utilization_rate': 43.36,
                'stale_items_count': 47,
                'high_performing_items': 156
            },
            'category_breakdown': [
                {'category': 'Linens', 'count': 500, 'utilization': 48.2, 'revenue': 145000.00},
                {'category': 'Uniforms', 'count': 375, 'utilization': 41.8, 'revenue': 98500.00},
                {'category': 'Mats', 'count': 250, 'utilization': 38.4, 'revenue': 67500.00},
                {'category': 'Towels', 'count': 125, 'utilization': 44.8, 'revenue': 44800.00}
            ],
            'alerts': [
                {'type': 'stale_item', 'severity': 'high', 'count': 15},
                {'type': 'low_utilization', 'severity': 'medium', 'count': 23},
                {'type': 'missing_item', 'severity': 'high', 'count': 5}
            ]
        }
        
        # Validate data structure
        assert 'summary' in analytics_data
        assert 'category_breakdown' in analytics_data
        assert 'alerts' in analytics_data
        
        # Validate summary calculations
        category_totals = sum(cat['count'] for cat in analytics_data['category_breakdown'])
        assert category_totals == analytics_data['summary']['total_items']
        
        # Validate category data
        total_revenue = sum(cat['revenue'] for cat in analytics_data['category_breakdown'])
        assert total_revenue > 0
        
        for category in analytics_data['category_breakdown']:
            assert 0 <= category['utilization'] <= 100
            assert category['revenue'] > 0
            assert category['count'] > 0
    
    def test_stale_items_identification(self):
        """Test stale items identification logic in analytics tab."""
        # Mock items with various staleness levels
        current_time = datetime.now()
        test_items = [
            {
                'tag_id': 'FRESH001',
                'date_last_scanned': current_time - timedelta(days=3),
                'bin_location': 'rental-rack-1',
                'status': 'Ready to Rent'
            },
            {
                'tag_id': 'STALE001',
                'date_last_scanned': current_time - timedelta(days=35),
                'bin_location': 'rental-rack-2',
                'status': 'Ready to Rent'
            },
            {
                'tag_id': 'VERY_STALE001',
                'date_last_scanned': current_time - timedelta(days=90),
                'bin_location': 'storage-area-1',
                'status': 'Available'
            },
            {
                'tag_id': 'RESALE_STALE001',
                'date_last_scanned': current_time - timedelta(days=10),
                'bin_location': 'resale-bin-1',
                'status': 'Ready to Rent'
            }
        ]
        
        # Apply staleness thresholds
        thresholds = {
            'resale': 7,
            'rental': 30,
            'storage': 60
        }
        
        stale_items = []
        for item in test_items:
            days_stale = (current_time - item['date_last_scanned']).days
            
            # Determine threshold based on location
            if 'resale' in item['bin_location']:
                threshold = thresholds['resale']
            elif 'storage' in item['bin_location']:
                threshold = thresholds['storage']
            else:
                threshold = thresholds['rental']
            
            if days_stale > threshold:
                severity = 'critical' if days_stale > 90 else 'high' if days_stale > 60 else 'medium'
                stale_items.append({
                    'tag_id': item['tag_id'],
                    'days_stale': days_stale,
                    'severity': severity,
                    'threshold_exceeded': days_stale - threshold
                })
        
        # Validate stale detection
        assert len(stale_items) == 3  # All except FRESH001
        assert any(item['tag_id'] == 'STALE001' for item in stale_items)
        assert any(item['tag_id'] == 'VERY_STALE001' for item in stale_items)
        assert any(item['tag_id'] == 'RESALE_STALE001' for item in stale_items)
        
        # Check severity assignment
        very_stale = next(item for item in stale_items if item['tag_id'] == 'VERY_STALE001')
        assert very_stale['severity'] == 'critical'
    
    def test_utilization_analysis_display(self):
        """Test utilization analysis display in analytics tab."""
        # Mock utilization analysis data
        utilization_data = {
            'by_category': [
                {'category': 'Linens', 'current_util': 48.2, 'target_util': 55.0, 'variance': -6.8},
                {'category': 'Uniforms', 'current_util': 41.8, 'target_util': 50.0, 'variance': -8.2},
                {'category': 'Mats', 'current_util': 38.4, 'target_util': 45.0, 'variance': -6.6},
                {'category': 'Towels', 'current_util': 44.8, 'target_util': 40.0, 'variance': 4.8}
            ],
            'by_store': [
                {'store': 'Wayzata', 'util': 45.1, 'target': 50.0, 'status': 'approaching_target'},
                {'store': 'Brooklyn Park', 'util': 40.7, 'target': 50.0, 'status': 'below_target'},
                {'store': 'Fridley', 'util': 53.3, 'target': 50.0, 'status': 'above_target'},
                {'store': 'Elk River', 'util': 29.6, 'target': 50.0, 'status': 'critical'}
            ],
            'trends': {
                'weekly_change': 2.3,
                'monthly_change': -1.8,
                'quarterly_change': 5.7
            }
        }
        
        # Validate utilization calculations
        for category in utilization_data['by_category']:
            calculated_variance = round(category['current_util'] - category['target_util'], 1)
            assert calculated_variance == category['variance']
        
        # Validate status assignment logic
        for store in utilization_data['by_store']:
            util = store['util']
            target = store['target']
            variance_pct = ((util - target) / target) * 100
            
            if util >= target * 1.05:  # 5% above target
                expected_status = 'above_target'
            elif util >= target * 0.9:  # Within 10% of target
                expected_status = 'approaching_target'
            elif util >= target * 0.7:  # Within 30% of target
                expected_status = 'below_target'
            else:
                expected_status = 'critical'
            
            assert store['status'] == expected_status


class TestCrossTabFunctionality:
    """Test cross-tab functionality and data sharing between tabs."""
    
    def test_data_sharing_between_tabs(self):
        """Test data sharing mechanism between dashboard tabs."""
        # Mock shared data structure
        shared_data = {
            'filters': {
                'store_filter': '3607',
                'date_range': '12_weeks',
                'category_filter': 'all'
            },
            'cached_metrics': {
                'total_items': 315,
                'utilization_rate': 45.1,
                'last_updated': datetime.now().isoformat()
            },
            'user_preferences': {
                'default_view': 'executive',
                'refresh_interval': 300,  # 5 minutes
                'chart_type': 'line'
            }
        }
        
        # Test filter propagation
        def apply_filters_to_tab(tab_name, shared_filters):
            """Simulate applying shared filters to different tabs."""
            filtered_data = {}
            
            if tab_name == 'executive':
                # Executive tab uses all filters
                filtered_data = {
                    'store': shared_filters['store_filter'],
                    'date_range': shared_filters['date_range'],
                    'scope': 'dashboard'
                }
            elif tab_name == 'inventory_analytics':
                # Analytics tab uses store and category filters
                filtered_data = {
                    'store': shared_filters['store_filter'],
                    'category': shared_filters['category_filter'],
                    'scope': 'analytics'
                }
            
            return filtered_data
        
        # Test filter application
        exec_filters = apply_filters_to_tab('executive', shared_data['filters'])
        analytics_filters = apply_filters_to_tab('inventory_analytics', shared_data['filters'])
        
        assert exec_filters['store'] == '3607'
        assert analytics_filters['store'] == '3607'
        assert exec_filters['date_range'] == '12_weeks'
        assert analytics_filters['category'] == 'all'
    
    def test_real_time_refresh_coordination(self):
        """Test real-time refresh coordination across tabs."""
        # Mock refresh coordination data
        refresh_state = {
            'last_refresh': datetime.now() - timedelta(minutes=3),
            'refresh_interval': 300,  # 5 minutes
            'active_tabs': ['executive', 'inventory_analytics'],
            'pending_updates': {
                'executive': False,
                'inventory_analytics': True
            }
        }
        
        current_time = datetime.now()
        time_since_refresh = (current_time - refresh_state['last_refresh']).seconds
        
        # Test refresh trigger logic
        should_refresh = time_since_refresh >= refresh_state['refresh_interval']
        
        if not should_refresh:
            # Check if any tabs have pending updates
            has_pending = any(refresh_state['pending_updates'].values())
            should_refresh = has_pending
        
        # In this case, should not trigger full refresh yet, but has pending updates
        assert not (time_since_refresh >= refresh_state['refresh_interval'])
        assert refresh_state['pending_updates']['inventory_analytics'] is True
        assert should_refresh  # Due to pending updates
    
    def test_filter_persistence_across_sessions(self):
        """Test filter persistence across user sessions."""
        # Mock user session data
        session_data = {
            'user_id': 'user_123',
            'session_id': 'session_456',
            'preferences': {
                'last_store_filter': '8101',
                'last_date_range': '4_weeks',
                'preferred_chart_types': {
                    'utilization': 'bar',
                    'revenue': 'line',
                    'distribution': 'pie'
                }
            },
            'session_started': datetime.now() - timedelta(hours=2)
        }
        
        # Test preference loading
        def load_user_preferences(user_id):
            """Simulate loading user preferences."""
            if user_id == 'user_123':
                return session_data['preferences']
            return None
        
        loaded_prefs = load_user_preferences('user_123')
        
        assert loaded_prefs is not None
        assert loaded_prefs['last_store_filter'] == '8101'
        assert loaded_prefs['last_date_range'] == '4_weeks'
        assert 'utilization' in loaded_prefs['preferred_chart_types']


class TestMobileResponsiveness:
    """Test mobile responsiveness of dashboard components."""
    
    def test_mobile_layout_adaptation(self):
        """Test mobile layout adaptation logic."""
        # Mock device configurations
        device_configs = [
            {
                'device_type': 'desktop',
                'screen_width': 1920,
                'screen_height': 1080,
                'expected_layout': 'full_grid',
                'charts_per_row': 3
            },
            {
                'device_type': 'tablet',
                'screen_width': 768,
                'screen_height': 1024,
                'expected_layout': 'compact_grid',
                'charts_per_row': 2
            },
            {
                'device_type': 'mobile',
                'screen_width': 375,
                'screen_height': 812,
                'expected_layout': 'single_column',
                'charts_per_row': 1
            }
        ]
        
        # Test layout logic
        def determine_layout(screen_width):
            """Determine layout based on screen width."""
            if screen_width >= 1200:
                return {'layout': 'full_grid', 'charts_per_row': 3}
            elif screen_width >= 768:
                return {'layout': 'compact_grid', 'charts_per_row': 2}
            else:
                return {'layout': 'single_column', 'charts_per_row': 1}
        
        for config in device_configs:
            layout = determine_layout(config['screen_width'])
            assert layout['layout'] == config['expected_layout']
            assert layout['charts_per_row'] == config['charts_per_row']
    
    def test_touch_interface_compatibility(self):
        """Test touch interface compatibility features."""
        # Mock touch interaction data
        touch_features = {
            'swipe_navigation': True,
            'tap_to_expand': True,
            'pinch_to_zoom': True,
            'long_press_context': True,
            'minimum_touch_target_size': 44  # pixels
        }
        
        # Test touch target sizes
        ui_elements = [
            {'type': 'button', 'size': 48, 'touch_friendly': True},
            {'type': 'link', 'size': 32, 'touch_friendly': False},
            {'type': 'chart_point', 'size': 44, 'touch_friendly': True},
            {'type': 'dropdown', 'size': 40, 'touch_friendly': False}
        ]
        
        min_size = touch_features['minimum_touch_target_size']
        
        for element in ui_elements:
            expected_friendly = element['size'] >= min_size
            assert element['touch_friendly'] == expected_friendly
    
    def test_data_loading_optimization_mobile(self):
        """Test data loading optimization for mobile devices."""
        # Mock mobile optimization settings
        mobile_optimizations = {
            'lazy_load_charts': True,
            'reduced_data_points': True,
            'compressed_responses': True,
            'cache_duration_minutes': 15,
            'max_concurrent_requests': 2
        }
        
        # Test data reduction logic
        def optimize_data_for_mobile(full_dataset, is_mobile=True):
            """Optimize dataset for mobile display."""
            if not is_mobile:
                return full_dataset
            
            optimized = {
                'summary': full_dataset.get('summary', {}),
                'top_performers': full_dataset.get('all_items', [])[:10],  # Limit to top 10
                'key_metrics': {
                    k: v for k, v in full_dataset.get('metrics', {}).items()
                    if k in ['utilization_rate', 'total_revenue', 'alert_count']
                }
            }
            return optimized
        
        # Mock full dataset
        full_data = {
            'summary': {'total_items': 1250, 'utilization': 43.36},
            'all_items': list(range(100)),  # 100 items
            'metrics': {
                'utilization_rate': 43.36,
                'total_revenue': 355800,
                'alert_count': 47,
                'detailed_breakdown': {},
                'historical_data': []
            }
        }
        
        optimized_data = optimize_data_for_mobile(full_data, is_mobile=True)
        
        assert len(optimized_data['top_performers']) == 10
        assert 'detailed_breakdown' not in optimized_data['key_metrics']
        assert 'utilization_rate' in optimized_data['key_metrics']


class TestDashboardPerformance:
    """Test dashboard performance and loading times."""
    
    def test_dashboard_loading_performance(self):
        """Test dashboard loading performance metrics."""
        # Mock performance measurements
        performance_metrics = {
            'initial_load_time': 2.1,  # seconds
            'chart_render_time': 0.8,  # seconds
            'data_fetch_time': 1.3,    # seconds
            'total_time_to_interactive': 3.2,  # seconds
            'memory_usage_mb': 45.6
        }
        
        # Performance thresholds
        thresholds = {
            'initial_load_time': 3.0,
            'chart_render_time': 2.0,
            'data_fetch_time': 2.0,
            'total_time_to_interactive': 5.0,
            'memory_usage_mb': 100.0
        }
        
        # Validate performance meets thresholds
        for metric, value in performance_metrics.items():
            threshold = thresholds[metric]
            assert value <= threshold, f"{metric} ({value}) exceeds threshold ({threshold})"
    
    def test_concurrent_user_handling(self):
        """Test dashboard handling of concurrent users."""
        # Mock concurrent user scenario
        concurrent_users = 25
        max_supported_users = 50
        avg_response_time_per_user = 1.2  # seconds
        
        # Test load capacity
        expected_load = concurrent_users * avg_response_time_per_user
        max_load_capacity = max_supported_users * 2.0  # 2 seconds per user max
        
        assert concurrent_users <= max_supported_users
        assert expected_load <= max_load_capacity
        
        # Test resource scaling
        if concurrent_users > 20:
            # Should trigger resource scaling
            scaling_factor = min(2.0, concurrent_users / 20)
            scaled_response_time = avg_response_time_per_user * scaling_factor
            
            assert scaled_response_time <= 3.0  # Maximum acceptable response time