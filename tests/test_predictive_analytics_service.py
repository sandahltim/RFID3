"""
Comprehensive tests for PredictiveAnalyticsService
Tests forecasting, demand prediction, and trend analysis
Created: September 3, 2025
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.predictive_analytics_service import PredictiveAnalyticsService


class TestPredictiveAnalyticsService:
    """Test suite for PredictiveAnalyticsService"""
    
    @pytest.fixture
    def service(self):
        """Create a PredictiveAnalyticsService instance for testing"""
        return PredictiveAnalyticsService()
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        mock_session = MagicMock()
        return mock_session
    
    @pytest.fixture
    def sample_revenue_data(self):
        """Sample historical revenue data for forecasting"""
        dates = pd.date_range(start='2024-01-01', end='2025-08-31', freq='W')
        revenue_data = []
        for i, week in enumerate(dates):
            # Simulate seasonal pattern with trend
            seasonal_factor = 1 + 0.3 * np.sin(2 * np.pi * i / 52)  # Annual seasonality
            base_revenue = 25000 + (i * 100)  # Growing trend
            revenue = base_revenue * seasonal_factor + np.random.normal(0, 1000)
            revenue_data.append({
                'week_date': week.date(),
                'total_revenue': max(revenue, 0),
                'target_revenue': base_revenue * seasonal_factor * 1.1
            })
        return pd.DataFrame(revenue_data)
    
    @pytest.fixture
    def sample_equipment_data(self):
        """Sample equipment utilization data"""
        return [
            {
                'category': 'Power Tools',
                'total_count': 500,
                'on_rent_count': 380,
                'utilization_rate': 76.0,
                'avg_rental_rate': 45.50,
                'seasonal_demand': 'spring_summer_peak'
            },
            {
                'category': 'Generators', 
                'total_count': 150,
                'on_rent_count': 135,
                'utilization_rate': 90.0,
                'avg_rental_rate': 125.00,
                'seasonal_demand': 'winter_peak'
            },
            {
                'category': 'Lawn Equipment',
                'total_count': 200,
                'on_rent_count': 120,
                'utilization_rate': 60.0,
                'avg_rental_rate': 35.00,
                'seasonal_demand': 'spring_summer_peak'
            }
        ]
    
    @pytest.fixture
    def sample_trend_data(self):
        """Sample business trend data"""
        return {
            'revenue_growth': {
                'monthly': [2.5, 3.1, 1.8, 4.2, 2.9, 3.5, 2.1, 3.8, 2.7, 3.2, 1.9, 4.1],
                'quarterly': [8.5, 12.3, 9.7, 11.2],
                'yearly': 42.1
            },
            'utilization_trends': {
                'q1': 72.5,
                'q2': 78.3,
                'q3': 81.2,
                'q4': 69.8
            },
            'demand_patterns': {
                'spring': {'power_tools': 85, 'lawn_equipment': 95, 'generators': 45},
                'summer': {'power_tools': 80, 'lawn_equipment': 90, 'generators': 40},
                'fall': {'power_tools': 75, 'lawn_equipment': 60, 'generators': 70},
                'winter': {'power_tools': 70, 'lawn_equipment': 30, 'generators': 95}
            }
        }
    
    # Predictive Dashboard Tests
    
    def test_get_predictive_dashboard_data(self, service):
        """Test predictive dashboard data aggregation"""
        # Mock all component methods
        revenue_forecast = {'next_12_weeks': [{'week': 1, 'predicted_revenue': 28500}]}
        equipment_demand = {'high_demand_categories': ['Power Tools', 'Generators']}
        utilization_opportunities = {'underutilized_categories': ['Lawn Equipment']}
        seasonal_patterns = {'current_season': 'fall', 'peak_categories': ['Generators']}
        business_trends = {'revenue_growth_rate': 3.2, 'trend_direction': 'positive'}
        predictive_alerts = [{'type': 'demand_spike', 'category': 'Generators', 'urgency': 'high'}]
        
        with patch.object(service, 'generate_revenue_forecasts', return_value=revenue_forecast):
            with patch.object(service, 'predict_equipment_demand', return_value=equipment_demand):
                with patch.object(service, 'analyze_utilization_opportunities', return_value=utilization_opportunities):
                    with patch.object(service, 'analyze_seasonal_patterns', return_value=seasonal_patterns):
                        with patch.object(service, 'analyze_business_trends', return_value=business_trends):
                            with patch.object(service, 'generate_predictive_alerts', return_value=predictive_alerts):
                                
                                result = service.get_predictive_dashboard_data()
                                
                                # Verify structure
                                assert 'revenue_forecasts' in result
                                assert 'equipment_demand_predictions' in result
                                assert 'utilization_opportunities' in result
                                assert 'seasonal_analysis' in result
                                assert 'business_trends' in result
                                assert 'predictive_alerts' in result
                                assert 'data_freshness' in result
                                
                                # Verify data freshness timestamp
                                assert isinstance(result['data_freshness']['generated_at'], str)
    
    # Revenue Forecasting Tests
    
    @patch('app.services.predictive_analytics_service.db.session')
    def test_generate_revenue_forecasts_success(self, mock_db, service, sample_revenue_data):
        """Test successful revenue forecast generation"""
        mock_db.execute.return_value.fetchall.return_value = sample_revenue_data.to_dict('records')
        
        result = service.generate_revenue_forecasts(horizon_weeks=8)
        
        # Verify structure
        assert 'forecasting_period' in result
        assert 'forecasts' in result
        assert 'confidence_metrics' in result
        assert 'methodology' in result
        
        # Verify forecast period
        forecast_period = result['forecasting_period']
        assert forecast_period['horizon_weeks'] == 8
        assert 'start_date' in forecast_period
        assert 'end_date' in forecast_period
        
        # Verify forecasts contain required data
        forecasts = result['forecasts']
        assert 'weekly_predictions' in forecasts
        assert len(forecasts['weekly_predictions']) == 8
        
        # Verify each prediction has required fields
        for prediction in forecasts['weekly_predictions']:
            assert 'week_date' in prediction
            assert 'predicted_revenue' in prediction
            assert 'confidence_interval' in prediction
            assert 'seasonal_factor' in prediction
        
        # Verify confidence metrics
        confidence = result['confidence_metrics']
        assert 'model_accuracy' in confidence
        assert 'prediction_reliability' in confidence
        assert confidence['model_accuracy'] >= 0.0
        assert confidence['model_accuracy'] <= 100.0
    
    def test_generate_revenue_forecasts_with_seasonal_adjustment(self, service, sample_revenue_data):
        """Test revenue forecasting with seasonal adjustment"""
        with patch('app.services.predictive_analytics_service.db.session') as mock_db:
            mock_db.execute.return_value.fetchall.return_value = sample_revenue_data.to_dict('records')
            
            result = service.generate_revenue_forecasts(horizon_weeks=12)
            
            # Verify seasonal factors are applied
            forecasts = result['forecasts']['weekly_predictions']
            seasonal_factors = [f['seasonal_factor'] for f in forecasts]
            
            # Should have variation in seasonal factors
            assert min(seasonal_factors) != max(seasonal_factors)
            assert all(factor > 0 for factor in seasonal_factors)
    
    def test_revenue_forecasting_insufficient_data(self, service):
        """Test revenue forecasting with insufficient historical data"""
        # Simulate insufficient data (less than 12 weeks)
        insufficient_data = [
            {'week_date': '2025-08-01', 'total_revenue': 25000},
            {'week_date': '2025-08-08', 'total_revenue': 26000}
        ]
        
        with patch('app.services.predictive_analytics_service.db.session') as mock_db:
            mock_db.execute.return_value.fetchall.return_value = insufficient_data
            
            result = service.generate_revenue_forecasts()
            
            # Should handle gracefully with lower confidence
            assert 'confidence_metrics' in result
            assert result['confidence_metrics']['prediction_reliability'] == 'low'
            assert 'data_limitation_warning' in result
    
    # Equipment Demand Prediction Tests
    
    @patch('app.services.predictive_analytics_service.db.session')
    def test_predict_equipment_demand_success(self, mock_db, service, sample_equipment_data):
        """Test successful equipment demand prediction"""
        mock_db.execute.return_value.fetchall.return_value = sample_equipment_data
        
        result = service.predict_equipment_demand()
        
        # Verify structure
        assert 'demand_predictions' in result
        assert 'category_analysis' in result
        assert 'procurement_recommendations' in result
        assert 'market_insights' in result
        
        # Verify category analysis
        category_analysis = result['category_analysis']
        assert len(category_analysis) == len(sample_equipment_data)
        
        for analysis in category_analysis:
            assert 'category' in analysis
            assert 'current_utilization' in analysis
            assert 'predicted_demand' in analysis
            assert 'recommendation' in analysis
            
            # Verify utilization is percentage
            assert 0 <= analysis['current_utilization'] <= 100
    
    def test_predict_equipment_demand_high_utilization_categories(self, service, sample_equipment_data):
        """Test identification of high utilization categories"""
        with patch('app.services.predictive_analytics_service.db.session') as mock_db:
            mock_db.execute.return_value.fetchall.return_value = sample_equipment_data
            
            result = service.predict_equipment_demand()
            
            # Should identify Generators as high utilization (90%)
            category_analysis = result['category_analysis']
            generators_analysis = next((cat for cat in category_analysis if cat['category'] == 'Generators'), None)
            
            assert generators_analysis is not None
            assert generators_analysis['current_utilization'] == 90.0
            assert generators_analysis['predicted_demand'] == 'high'
            assert 'increase inventory' in generators_analysis['recommendation'].lower()
    
    def test_equipment_demand_seasonal_considerations(self, service, sample_equipment_data):
        """Test seasonal demand considerations in equipment prediction"""
        with patch('app.services.predictive_analytics_service.db.session') as mock_db:
            mock_db.execute.return_value.fetchall.return_value = sample_equipment_data
            
            # Mock current season as winter
            with patch('app.services.predictive_analytics_service.datetime') as mock_datetime:
                mock_datetime.now.return_value = datetime(2025, 12, 15)  # Winter
                mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)
                
                result = service.predict_equipment_demand()
                
                # Should highlight winter peak items (Generators)
                market_insights = result['market_insights']
                assert 'seasonal_considerations' in market_insights
                assert any('winter' in insight.lower() for insight in market_insights['seasonal_considerations'])
    
    # Utilization Opportunity Analysis Tests
    
    @patch('app.services.predictive_analytics_service.db.session')
    def test_analyze_utilization_opportunities_success(self, mock_db, service):
        """Test utilization opportunity analysis"""
        mock_utilization_data = [
            {'category': 'Power Tools', 'utilization_rate': 76.0, 'inventory_count': 500, 'revenue_potential': 2500},
            {'category': 'Lawn Equipment', 'utilization_rate': 60.0, 'inventory_count': 200, 'revenue_potential': 1200},
            {'category': 'Generators', 'utilization_rate': 90.0, 'inventory_count': 150, 'revenue_potential': 500}
        ]
        
        mock_db.execute.return_value.fetchall.return_value = mock_utilization_data
        
        result = service.analyze_utilization_opportunities()
        
        # Verify structure
        assert 'optimization_opportunities' in result
        assert 'utilization_analysis' in result
        assert 'revenue_impact_projections' in result
        assert 'implementation_recommendations' in result
        
        # Verify identifies underutilized categories
        opportunities = result['optimization_opportunities']
        underutilized = [opp for opp in opportunities if opp['opportunity_type'] == 'underutilized']
        assert len(underutilized) > 0
        
        # Should identify Lawn Equipment as underutilized (60%)
        lawn_equipment_opp = next((opp for opp in underutilized if 'Lawn Equipment' in opp['category']), None)
        assert lawn_equipment_opp is not None
    
    def test_utilization_revenue_impact_calculation(self, service):
        """Test revenue impact calculations for utilization improvements"""
        mock_data = [
            {'category': 'Test Category', 'utilization_rate': 65.0, 'inventory_count': 100, 'avg_rental_rate': 50.0}
        ]
        
        with patch('app.services.predictive_analytics_service.db.session') as mock_db:
            mock_db.execute.return_value.fetchall.return_value = mock_data
            
            result = service.analyze_utilization_opportunities()
            
            # Should calculate potential revenue increase
            revenue_projections = result['revenue_impact_projections']
            assert 'total_potential_increase' in revenue_projections
            assert 'category_breakdown' in revenue_projections
            
            # Verify calculations are positive for underutilized items
            assert revenue_projections['total_potential_increase'] >= 0
    
    # Seasonal Pattern Analysis Tests
    
    @patch('app.services.predictive_analytics_service.db.session')
    def test_analyze_seasonal_patterns_success(self, mock_db, service):
        """Test seasonal pattern analysis"""
        # Mock seasonal data across multiple years
        mock_seasonal_data = []
        for year in [2023, 2024, 2025]:
            for month in range(1, 13):
                seasonal_factor = 1 + 0.3 * np.sin(2 * np.pi * month / 12)
                mock_seasonal_data.append({
                    'year': year,
                    'month': month,
                    'revenue': 25000 * seasonal_factor,
                    'utilization_rate': 75 * seasonal_factor
                })
        
        mock_db.execute.return_value.fetchall.return_value = mock_seasonal_data
        
        result = service.analyze_seasonal_patterns()
        
        # Verify structure
        assert 'seasonal_insights' in result
        assert 'current_season_analysis' in result
        assert 'upcoming_trends' in result
        assert 'historical_patterns' in result
        
        # Verify current season analysis
        current_analysis = result['current_season_analysis']
        assert 'season' in current_analysis
        assert 'revenue_pattern' in current_analysis
        assert 'utilization_pattern' in current_analysis
        
        # Verify upcoming trends
        upcoming = result['upcoming_trends']
        assert 'next_quarter_outlook' in upcoming
        assert 'preparation_recommendations' in upcoming
    
    def test_seasonal_pattern_peak_identification(self, service):
        """Test identification of seasonal peaks and valleys"""
        # Create data with clear seasonal pattern (winter peak)
        mock_data = [
            {'month': 1, 'revenue': 35000, 'utilization_rate': 85},  # Winter peak
            {'month': 4, 'revenue': 28000, 'utilization_rate': 75},  # Spring
            {'month': 7, 'revenue': 25000, 'utilization_rate': 70},  # Summer valley
            {'month': 10, 'revenue': 32000, 'utilization_rate': 80}  # Fall
        ]
        
        with patch('app.services.predictive_analytics_service.db.session') as mock_db:
            mock_db.execute.return_value.fetchall.return_value = mock_data
            
            result = service.analyze_seasonal_patterns()
            
            # Should identify winter as peak season
            insights = result['seasonal_insights']
            assert 'peak_seasons' in insights
            assert 'valley_seasons' in insights
            
            # Verify pattern recognition
            peak_seasons = insights['peak_seasons']
            assert any('winter' in season.lower() for season in peak_seasons)
    
    # Business Trend Analysis Tests
    
    @patch('app.services.predictive_analytics_service.db.session')
    def test_analyze_business_trends_success(self, mock_db, service, sample_trend_data):
        """Test business trend analysis"""
        # Mock trend calculation data
        mock_revenue_trends = [
            {'period': '2024-Q1', 'revenue': 300000, 'growth_rate': 5.2},
            {'period': '2024-Q2', 'revenue': 315000, 'growth_rate': 5.0},
            {'period': '2024-Q3', 'revenue': 325000, 'growth_rate': 3.2},
            {'period': '2024-Q4', 'revenue': 340000, 'growth_rate': 4.6}
        ]
        
        mock_db.execute.return_value.fetchall.return_value = mock_revenue_trends
        
        result = service.analyze_business_trends()
        
        # Verify structure
        assert 'trend_analysis' in result
        assert 'growth_metrics' in result
        assert 'performance_indicators' in result
        assert 'strategic_insights' in result
        
        # Verify growth metrics
        growth_metrics = result['growth_metrics']
        assert 'revenue_growth_rate' in growth_metrics
        assert 'trend_direction' in growth_metrics
        assert 'momentum' in growth_metrics
        
        # Verify trend direction calculation
        assert growth_metrics['trend_direction'] in ['positive', 'negative', 'stable']
    
    def test_business_trends_performance_indicators(self, service):
        """Test performance indicator calculations"""
        mock_kpi_data = [
            {'metric': 'utilization_rate', 'current_value': 78.5, 'previous_value': 76.2, 'target': 80.0},
            {'metric': 'revenue_per_unit', 'current_value': 145.50, 'previous_value': 142.00, 'target': 150.00},
            {'metric': 'customer_satisfaction', 'current_value': 4.2, 'previous_value': 4.1, 'target': 4.5}
        ]
        
        with patch('app.services.predictive_analytics_service.db.session') as mock_db:
            mock_db.execute.return_value.fetchall.return_value = mock_kpi_data
            
            result = service.analyze_business_trends()
            
            # Verify performance indicators
            indicators = result['performance_indicators']
            assert 'key_metrics' in indicators
            assert 'target_progress' in indicators
            
            # Should track progress toward targets
            key_metrics = indicators['key_metrics']
            assert len(key_metrics) > 0
            for metric in key_metrics:
                assert 'current_vs_previous' in metric
                assert 'target_gap' in metric
    
    # Predictive Alert Generation Tests
    
    @patch('app.services.predictive_analytics_service.db.session')
    def test_generate_predictive_alerts_success(self, mock_db, service):
        """Test predictive alert generation"""
        # Mock data that should trigger various alerts
        mock_alert_data = {
            'high_utilization': [{'category': 'Generators', 'utilization_rate': 95.0}],
            'low_utilization': [{'category': 'Lawn Equipment', 'utilization_rate': 45.0}],
            'inventory_shortage': [{'category': 'Power Tools', 'available_count': 15, 'typical_demand': 100}],
            'seasonal_demand_spike': [{'category': 'Generators', 'predicted_increase': 35.0}]
        }
        
        # Setup mock to return different data for different queries
        def mock_execute_side_effect(*args, **kwargs):
            mock_result = MagicMock()
            query = str(args[0])
            if 'utilization_rate > 90' in query:
                mock_result.fetchall.return_value = mock_alert_data['high_utilization']
            elif 'utilization_rate < 50' in query:
                mock_result.fetchall.return_value = mock_alert_data['low_utilization']
            elif 'inventory' in query.lower():
                mock_result.fetchall.return_value = mock_alert_data['inventory_shortage']
            else:
                mock_result.fetchall.return_value = []
            return mock_result
        
        mock_db.execute.side_effect = mock_execute_side_effect
        
        result = service.generate_predictive_alerts()
        
        # Verify alerts are generated
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Verify alert structure
        for alert in result:
            assert 'type' in alert
            assert 'category' in alert
            assert 'message' in alert
            assert 'urgency' in alert
            assert 'recommended_action' in alert
            assert 'priority_score' in alert
            
            # Verify urgency levels
            assert alert['urgency'] in ['low', 'medium', 'high', 'critical']
            
            # Verify priority score is numeric
            assert isinstance(alert['priority_score'], (int, float))
            assert 0 <= alert['priority_score'] <= 100
    
    def test_predictive_alerts_urgency_prioritization(self, service):
        """Test alert urgency and prioritization logic"""
        # Mock critical situation data
        critical_data = [{'category': 'Emergency Equipment', 'utilization_rate': 98.0, 'available_count': 2}]
        
        with patch('app.services.predictive_analytics_service.db.session') as mock_db:
            mock_db.execute.return_value.fetchall.return_value = critical_data
            
            result = service.generate_predictive_alerts()
            
            if result:  # If alerts are generated
                # Should have high priority alerts
                high_priority_alerts = [alert for alert in result if alert['urgency'] == 'critical']
                assert len(high_priority_alerts) > 0
                
                # Critical alerts should have high priority scores
                for alert in high_priority_alerts:
                    assert alert['priority_score'] >= 80
    
    # Model Performance and Validation Tests
    
    def test_get_model_performance_metrics(self, service):
        """Test model performance metrics calculation"""
        # Mock historical prediction accuracy data
        with patch.object(service, '_calculate_prediction_accuracy', return_value=85.2):
            with patch.object(service, '_calculate_forecast_reliability', return_value=78.9):
                
                result = service.get_model_performance_metrics()
                
                # Verify structure
                assert 'accuracy_metrics' in result
                assert 'reliability_scores' in result
                assert 'model_confidence' in result
                assert 'validation_results' in result
                
                # Verify accuracy metrics
                accuracy = result['accuracy_metrics']
                assert 'prediction_accuracy' in accuracy
                assert 'forecast_reliability' in accuracy
                assert 0 <= accuracy['prediction_accuracy'] <= 100
                assert 0 <= accuracy['forecast_reliability'] <= 100
    
    # Helper Method Tests
    
    def test_generate_single_revenue_forecast(self, service, sample_revenue_data):
        """Test single revenue forecast generation"""
        result = service._generate_single_revenue_forecast(
            sample_revenue_data, 'total_revenue', horizon_weeks=4
        )
        
        # Verify structure
        assert 'predictions' in result
        assert 'confidence' in result
        assert 'seasonal_factors' in result
        
        # Verify predictions
        predictions = result['predictions']
        assert len(predictions) == 4
        
        for prediction in predictions:
            assert prediction >= 0  # Revenue should be non-negative
    
    def test_calculate_seasonal_factors(self, service):
        """Test seasonal factor calculation"""
        # Create test data with clear seasonal pattern
        test_data = pd.DataFrame({
            'week_date': pd.date_range(start='2024-01-01', periods=52, freq='W'),
            'total_revenue': [25000 + 5000 * np.sin(2 * np.pi * i / 52) for i in range(52)]
        })
        
        result = service._calculate_seasonal_factors(test_data)
        
        # Verify seasonal factors
        assert 'monthly_factors' in result
        assert 'quarterly_factors' in result
        
        monthly_factors = result['monthly_factors']
        assert len(monthly_factors) == 12
        
        # Should have variation (not all the same)
        assert min(monthly_factors.values()) != max(monthly_factors.values())
    
    # Integration and Performance Tests
    
    def test_full_predictive_pipeline(self, service):
        """Test complete predictive analytics pipeline"""
        # Mock all dependencies
        with patch('app.services.predictive_analytics_service.db.session') as mock_db:
            mock_db.execute.return_value.fetchall.return_value = [
                {'week_date': '2025-08-01', 'total_revenue': 25000, 'utilization_rate': 75}
            ]
            
            # Run full pipeline
            dashboard_data = service.get_predictive_dashboard_data()
            
            # Verify all components are present
            required_components = [
                'revenue_forecasts', 'equipment_demand_predictions', 
                'utilization_opportunities', 'seasonal_analysis', 
                'business_trends', 'predictive_alerts'
            ]
            
            for component in required_components:
                assert component in dashboard_data
    
    @patch('app.services.predictive_analytics_service.db.session')
    def test_performance_with_large_dataset(self, mock_db, service):
        """Test performance with large datasets"""
        # Simulate large dataset
        large_dataset = []
        for i in range(1000):  # 1000 weeks of data
            large_dataset.append({
                'week_date': f'2020-01-01',
                'total_revenue': 25000 + np.random.normal(0, 2000),
                'utilization_rate': 75 + np.random.normal(0, 10)
            })
        
        mock_db.execute.return_value.fetchall.return_value = large_dataset
        
        # Should handle large datasets without errors
        result = service.generate_revenue_forecasts(horizon_weeks=12)
        
        # Verify results are still generated
        assert 'forecasts' in result
        assert len(result['forecasts']['weekly_predictions']) == 12
    
    # Error Handling and Edge Cases
    
    def test_no_historical_data_handling(self, service):
        """Test handling when no historical data is available"""
        with patch('app.services.predictive_analytics_service.db.session') as mock_db:
            mock_db.execute.return_value.fetchall.return_value = []
            
            result = service.generate_revenue_forecasts()
            
            # Should return appropriate response for no data
            assert 'error' in result or 'warning' in result or 'data_limitation_warning' in result
            if 'forecasts' in result:
                assert result['forecasts']['weekly_predictions'] == []
    
    def test_database_connection_error_handling(self, service):
        """Test database connection error handling"""
        with patch('app.services.predictive_analytics_service.db.session') as mock_db:
            mock_db.execute.side_effect = Exception("Database connection failed")
            
            # Should handle database errors gracefully
            with pytest.raises(Exception):
                service.generate_revenue_forecasts()
    
    def test_invalid_date_range_handling(self, service):
        """Test handling of invalid date ranges"""
        with patch('app.services.predictive_analytics_service.db.session') as mock_db:
            mock_db.execute.return_value.fetchall.return_value = [
                {'week_date': 'invalid-date', 'total_revenue': 25000}
            ]
            
            # Should handle invalid dates gracefully
            result = service.generate_revenue_forecasts()
            
            # Should either filter out invalid data or return error
            assert 'error' in result or 'forecasts' in result
    
    # RFID Coverage Integration Tests
    
    def test_predictive_analytics_with_limited_rfid_coverage(self, service):
        """Test predictive analytics accounting for 1.78% RFID coverage"""
        # Mock data that reflects limited RFID correlation
        mock_equipment_data = [
            {'category': 'Power Tools', 'total_count': 500, 'rfid_tracked': 9, 'utilization_rate': 76.0},  # 1.8%
            {'category': 'Generators', 'total_count': 150, 'rfid_tracked': 3, 'utilization_rate': 90.0},   # 2.0%
            {'category': 'Lawn Equipment', 'total_count': 200, 'rfid_tracked': 3, 'utilization_rate': 60.0} # 1.5%
        ]
        
        with patch('app.services.predictive_analytics_service.db.session') as mock_db:
            mock_db.execute.return_value.fetchall.return_value = mock_equipment_data
            
            result = service.predict_equipment_demand()
            
            # Should acknowledge RFID limitations in confidence metrics
            if 'confidence_metrics' in result:
                confidence = result['confidence_metrics']
                assert 'rfid_coverage_limitation' in confidence or 'data_quality_note' in confidence
            
            # Should provide appropriate confidence levels
            category_analysis = result['category_analysis']
            for analysis in category_analysis:
                # With limited RFID coverage, confidence should be moderate at best
                if 'confidence_level' in analysis:
                    assert analysis['confidence_level'] in ['low', 'medium']