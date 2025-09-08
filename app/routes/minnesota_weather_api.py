"""
Minnesota Weather Analytics API Routes
API endpoints for weather-rental correlation data and Minnesota-specific analytics
"""

from flask import Blueprint, request, jsonify, render_template
from app import db, cache
from app.services.minnesota_weather_service import MinnesotaWeatherService
from app.services.minnesota_industry_analytics import MinnesotaIndustryAnalytics
from app.services.minnesota_seasonal_service import MinnesotaSeasonalService
from app.services.weather_correlation_service import WeatherCorrelationService
from app.services.multi_store_analytics_service import MultiStoreAnalyticsService
from app.services.weather_predictive_service import WeatherPredictiveService
from app.services.logger import get_logger
from app.utils.exceptions import handle_api_error
from datetime import datetime, date, timedelta
import json
import logging

logger = get_logger(__name__)

mn_weather_api = Blueprint('mn_weather_api', __name__, url_prefix='/api/minnesota-weather')

# Initialize services
weather_service = MinnesotaWeatherService()
industry_service = MinnesotaIndustryAnalytics()
seasonal_service = MinnesotaSeasonalService()
correlation_service = WeatherCorrelationService()
multi_store_service = MultiStoreAnalyticsService()
predictive_service = WeatherPredictiveService()

@mn_weather_api.route('/current-weather/<location_code>')
@handle_api_error
def get_current_weather(location_code):
    """Get current weather conditions for a Minnesota location"""
    cache_key = f"current_weather_{location_code}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return jsonify(json.loads(cached_data))
    
    try:
        weather_data = weather_service.fetch_current_weather(location_code)
        
        if weather_data:
            # Cache for 30 minutes
            cache.set(cache_key, json.dumps(weather_data), timeout=1800)
            return jsonify({
                'status': 'success',
                'location_code': location_code,
                'weather_data': weather_data,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'status': 'error',
                'error': f'Weather data not available for location {location_code}'
            }), 404
            
    except Exception as e:
        logger.error(f"Current weather API error for {location_code}: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@mn_weather_api.route('/forecast/<location_code>')
@handle_api_error
def get_weather_forecast(location_code):
    """Get weather forecast for a Minnesota location"""
    days_ahead = int(request.args.get('days', 7))
    days_ahead = min(14, max(1, days_ahead))  # Limit to 1-14 days
    
    cache_key = f"weather_forecast_{location_code}_{days_ahead}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return jsonify(json.loads(cached_data))
    
    try:
        forecast_data = weather_service.fetch_forecast_data(location_code, days_ahead)
        
        if forecast_data:
            result = {
                'status': 'success',
                'location_code': location_code,
                'forecast_days': days_ahead,
                'forecasts': forecast_data,
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache for 2 hours
            cache.set(cache_key, json.dumps(result), timeout=7200)
            return jsonify(result)
        else:
            return jsonify({
                'status': 'error',
                'error': f'Forecast data not available for location {location_code}'
            }), 404
            
    except Exception as e:
        logger.error(f"Weather forecast API error for {location_code}: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@mn_weather_api.route('/weather-correlations')
@handle_api_error
def get_weather_correlations():
    """Get weather-rental correlations analysis"""
    store_code = request.args.get('store_code')
    industry_segment = request.args.get('industry_segment', 'all')
    days_back = int(request.args.get('days_back', 365))
    include_forecasts = request.args.get('include_forecasts', 'false').lower() == 'true'
    
    cache_key = f"weather_correlations_{store_code}_{industry_segment}_{days_back}_{include_forecasts}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return jsonify(json.loads(cached_data))
    
    try:
        correlation_results = correlation_service.analyze_weather_rental_correlations(
            store_code=store_code,
            industry_segment=industry_segment,
            days_back=days_back,
            include_forecasts=include_forecasts
        )
        
        # Cache for 4 hours
        cache.set(cache_key, json.dumps(correlation_results), timeout=14400)
        return jsonify(correlation_results)
        
    except Exception as e:
        logger.error(f"Weather correlations API error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@mn_weather_api.route('/equipment-categorization')
@handle_api_error
def get_equipment_categorization():
    """Get equipment categorization analysis"""
    store_code = request.args.get('store_code')
    
    cache_key = f"equipment_categorization_{store_code}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return jsonify(json.loads(cached_data))
    
    try:
        if store_code:
            categorization_results = industry_service.analyze_store_industry_mix(store_code)
        else:
            categorization_results = industry_service.compare_stores_by_industry()
        
        # Cache for 6 hours
        cache.set(cache_key, json.dumps(categorization_results), timeout=21600)
        return jsonify({
            'status': 'success',
            'store_code': store_code,
            'categorization_data': categorization_results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Equipment categorization API error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@mn_weather_api.route('/categorization-settings')
@handle_api_error
def get_categorization_settings():
    """Get current categorization settings and thresholds"""
    cache_key = "categorization_settings"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return jsonify(json.loads(cached_data))
    
    try:
        settings = industry_service.get_categorization_settings()
        
        # Cache for 1 hour
        cache.set(cache_key, json.dumps(settings), timeout=3600)
        return jsonify({
            'status': 'success',
            'settings': settings,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Categorization settings API error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@mn_weather_api.route('/categorize-equipment', methods=['POST'])
@handle_api_error
def run_equipment_categorization():
    """Run equipment categorization process"""
    batch_size = int(request.json.get('batch_size', 1000))
    
    try:
        results = industry_service.categorize_all_equipment(batch_size=batch_size)
        
        return jsonify({
            'status': 'success',
            'categorization_results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Equipment categorization process error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@mn_weather_api.route('/seasonal-analysis')
@handle_api_error
def get_seasonal_analysis():
    """Get Minnesota seasonal pattern analysis"""
    years_back = int(request.args.get('years_back', 3))
    store_code = request.args.get('store_code')
    
    cache_key = f"seasonal_analysis_{years_back}_{store_code}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return jsonify(json.loads(cached_data))
    
    try:
        seasonal_results = seasonal_service.analyze_seasonal_patterns(
            years_back=years_back,
            store_code=store_code
        )
        
        # Cache for 8 hours
        cache.set(cache_key, json.dumps(seasonal_results), timeout=28800)
        return jsonify(seasonal_results)
        
    except Exception as e:
        logger.error(f"Seasonal analysis API error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@mn_weather_api.route('/seasonal-forecast/<store_code>/<industry_segment>')
@handle_api_error
def get_seasonal_forecast(store_code, industry_segment):
    """Get seasonal demand forecast"""
    forecast_months = int(request.args.get('months', 6))
    forecast_months = min(12, max(1, forecast_months))  # Limit to 1-12 months
    
    cache_key = f"seasonal_forecast_{store_code}_{industry_segment}_{forecast_months}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return jsonify(json.loads(cached_data))
    
    try:
        forecast_results = industry_service.generate_seasonal_forecast(
            store_code=store_code,
            industry_segment=industry_segment,
            forecast_months=forecast_months
        )
        
        # Cache for 4 hours
        cache.set(cache_key, json.dumps(forecast_results), timeout=14400)
        return jsonify({
            'status': 'success',
            'forecast_data': forecast_results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Seasonal forecast API error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@mn_weather_api.route('/multi-store-analysis')
@handle_api_error
def get_multi_store_analysis():
    """Get comprehensive multi-store analysis"""
    analysis_period_days = int(request.args.get('days', 365))
    
    cache_key = f"multi_store_analysis_{analysis_period_days}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return jsonify(json.loads(cached_data))
    
    try:
        analysis_results = multi_store_service.analyze_regional_demand_patterns(
            analysis_period_days=analysis_period_days
        )
        
        # Cache for 6 hours
        cache.set(cache_key, json.dumps(analysis_results), timeout=21600)
        return jsonify(analysis_results)
        
    except Exception as e:
        logger.error(f"Multi-store analysis API error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@mn_weather_api.route('/demand-forecast')
@handle_api_error
def get_demand_forecast():
    """Get weather-based demand forecast"""
    store_code = request.args.get('store_code')
    forecast_days = int(request.args.get('days', 14))
    include_confidence = request.args.get('confidence', 'true').lower() == 'true'
    
    forecast_days = min(14, max(1, forecast_days))  # Limit to 1-14 days
    
    cache_key = f"demand_forecast_{store_code}_{forecast_days}_{include_confidence}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return jsonify(json.loads(cached_data))
    
    try:
        forecast_results = predictive_service.generate_comprehensive_demand_forecast(
            store_code=store_code,
            forecast_days=forecast_days,
            include_confidence_intervals=include_confidence
        )
        
        # Cache for 2 hours
        cache.set(cache_key, json.dumps(forecast_results), timeout=7200)
        return jsonify(forecast_results)
        
    except Exception as e:
        logger.error(f"Demand forecast API error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@mn_weather_api.route('/weather-dashboard-data')
@handle_api_error
def get_weather_dashboard_data():
    """Get comprehensive data for weather analytics dashboard"""
    store_code = request.args.get('store_code')
    days_back = int(request.args.get('days_back', 90))
    
    cache_key = f"weather_dashboard_{store_code}_{days_back}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return jsonify(json.loads(cached_data))
    
    try:
        dashboard_data = correlation_service.get_weather_impact_dashboard_data(
            store_code=store_code,
            days_back=days_back
        )
        
        # Cache for 1 hour
        cache.set(cache_key, json.dumps(dashboard_data), timeout=3600)
        return jsonify(dashboard_data)
        
    except Exception as e:
        logger.error(f"Weather dashboard API error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@mn_weather_api.route('/update-weather-data', methods=['POST'])
@handle_api_error
def update_weather_data():
    """Update weather data for all Minnesota locations"""
    try:
        update_results = weather_service.update_all_locations()
        
        # Clear related caches
        cache.delete_many('current_weather_*', 'weather_forecast_*')
        
        return jsonify({
            'status': 'success',
            'update_results': update_results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Weather data update API error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@mn_weather_api.route('/weather-summary')
@handle_api_error
def get_weather_summary():
    """Get weather summary for date range"""
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    location_code = request.args.get('location_code', 'MSP')
    
    if not start_date_str or not end_date_str:
        return jsonify({
            'status': 'error',
            'error': 'start_date and end_date parameters required'
        }), 400
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({
            'status': 'error',
            'error': 'Invalid date format. Use YYYY-MM-DD'
        }), 400
    
    cache_key = f"weather_summary_{start_date}_{end_date}_{location_code}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return jsonify(json.loads(cached_data))
    
    try:
        summary = weather_service.get_weather_summary_for_date_range(
            start_date, end_date, location_code
        )
        
        # Cache for 4 hours
        cache.set(cache_key, json.dumps(summary), timeout=14400)
        return jsonify({
            'status': 'success',
            'weather_summary': summary,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Weather summary API error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@mn_weather_api.route('/historical-correlations')
@handle_api_error
def get_historical_correlations():
    """Get historical weather-business correlations"""
    store_code = request.args.get('store_code')
    industry_segment = request.args.get('industry_segment', 'mixed')
    days_back = int(request.args.get('days_back', 365))
    
    cache_key = f"historical_correlations_{store_code}_{industry_segment}_{days_back}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return jsonify(json.loads(cached_data))
    
    try:
        correlation_data = weather_service.analyze_historical_correlations(
            store_code=store_code,
            industry_segment=industry_segment,
            days_back=days_back
        )
        
        # Cache for 6 hours
        cache.set(cache_key, json.dumps(correlation_data), timeout=21600)
        return jsonify(correlation_data)
        
    except Exception as e:
        logger.error(f"Historical correlations API error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


# Weather Analytics Dashboard Route
@mn_weather_api.route('/dashboard')
@handle_api_error
def weather_analytics_dashboard():
    """Render the weather analytics dashboard"""
    return render_template('weather_analytics_dashboard.html',
                         title="Minnesota Weather Analytics Dashboard")


# Store comparison endpoints
@mn_weather_api.route('/store-comparison')
@handle_api_error
def get_store_comparison():
    """Get detailed store comparison data"""
    cache_key = "store_comparison_data"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return jsonify(json.loads(cached_data))
    
    try:
        comparison_data = industry_service.compare_stores_by_industry()
        
        # Cache for 4 hours
        cache.set(cache_key, json.dumps(comparison_data), timeout=14400)
        return jsonify({
            'status': 'success',
            'comparison_data': comparison_data,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Store comparison API error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@mn_weather_api.route('/transfer-recommendations')
@handle_api_error
def get_transfer_recommendations():
    """Get equipment transfer recommendations"""
    cache_key = "transfer_recommendations"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return jsonify(json.loads(cached_data))
    
    try:
        # Get multi-store analysis which includes transfer recommendations
        analysis_results = multi_store_service.analyze_regional_demand_patterns()
        
        recommendations = analysis_results.get('transfer_recommendations', [])
        
        result = {
            'status': 'success',
            'transfer_recommendations': recommendations,
            'timestamp': datetime.now().isoformat()
        }
        
        # Cache for 2 hours
        cache.set(cache_key, json.dumps(result), timeout=7200)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Transfer recommendations API error: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


# Health check and status endpoints
@mn_weather_api.route('/status')
@handle_api_error
def get_api_status():
    """Get API health status and available endpoints"""
    return jsonify({
        'status': 'operational',
        'service': 'Minnesota Weather Analytics API',
        'version': '1.0.0',
        'endpoints': {
            'weather': [
                'GET /current-weather/<location_code>',
                'GET /forecast/<location_code>',
                'GET /weather-summary',
                'POST /update-weather-data'
            ],
            'analytics': [
                'GET /weather-correlations',
                'GET /historical-correlations',
                'GET /weather-dashboard-data'
            ],
            'equipment': [
                'GET /equipment-categorization',
                'GET /categorization-settings',
                'POST /categorize-equipment'
            ],
            'forecasting': [
                'GET /demand-forecast',
                'GET /seasonal-forecast/<store_code>/<industry_segment>'
            ],
            'multi-store': [
                'GET /multi-store-analysis',
                'GET /store-comparison',
                'GET /transfer-recommendations'
            ],
            'seasonal': [
                'GET /seasonal-analysis'
            ]
        },
        'locations': list(weather_service.MINNESOTA_LOCATIONS.keys()),
        'industry_segments': ['party_event', 'construction_diy', 'landscaping', 'mixed'],
        'stores': ['3607', '6800', '728', '8101'],
        'timestamp': datetime.now().isoformat()
    })


# Error handlers
@mn_weather_api.errorhandler(400)
def bad_request(error):
    return jsonify({
        'status': 'error',
        'error': 'Bad request',
        'message': str(error.description)
    }), 400


@mn_weather_api.errorhandler(404)
def not_found(error):
    return jsonify({
        'status': 'error',
        'error': 'Resource not found',
        'message': str(error.description)
    }), 404


@mn_weather_api.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500