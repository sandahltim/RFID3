"""
P&L Analytics Dashboard Routes
Provides routes for the enhanced P&L analytics dashboard with weather correlation
and predictive insights.
"""

from flask import Blueprint, render_template, request, jsonify
from ..services.pnl_import_service import PnLImportService
from ..services.logger import get_logger
import traceback
from datetime import datetime, timedelta
import json

logger = get_logger(__name__)

pnl_analytics_bp = Blueprint('pnl_analytics', __name__, url_prefix='/pnl')

@pnl_analytics_bp.route('/dashboard')
def pnl_dashboard():
    """Render the enhanced P&L analytics dashboard"""
    try:
        return render_template('pnl_analytics_dashboard.html')
    except Exception as e:
        logger.error(f"Error rendering P&L dashboard: {e}")
        return f"Error loading P&L dashboard: {str(e)}", 500

@pnl_analytics_bp.route('/api/data')
def get_pnl_data():
    """Get P&L data for the dashboard with optional filtering"""
    try:
        # Get query parameters
        store_code = request.args.get('store', 'all')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date') 
        metric_focus = request.args.get('metric', 'revenue')
        external_factors = request.args.get('factors', 'none')
        
        logger.info(f"P&L data request: store={store_code}, metric={metric_focus}, factors={external_factors}")
        
        # Initialize P&L service
        pnl_service = PnLImportService()
        
        # Get P&L analytics data
        analytics_data = pnl_service.get_pnl_analytics(store_code, metric_focus)
        
        # Enhance with mock weather and external factor data
        enhanced_data = enhance_with_external_factors(analytics_data, external_factors)
        
        return jsonify({
            'success': True,
            'data': enhanced_data,
            'meta': {
                'store_filter': store_code,
                'date_range': f"{start_date} to {end_date}" if start_date and end_date else "All available data",
                'external_factors': external_factors.split(',') if external_factors != 'none' else [],
                'last_updated': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting P&L data: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pnl_analytics_bp.route('/api/correlations')
def get_correlations():
    """Get correlation analysis between P&L metrics and external factors"""
    try:
        factor_type = request.args.get('type', 'weather')
        store_code = request.args.get('store', 'all')
        
        # Mock correlation data - in production this would come from ML analysis
        correlations = generate_mock_correlations(factor_type, store_code)
        
        return jsonify({
            'success': True,
            'correlations': correlations,
            'meta': {
                'factor_type': factor_type,
                'store_filter': store_code,
                'confidence_level': 0.95,
                'sample_size': 247
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting correlations: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pnl_analytics_bp.route('/api/forecast')
def get_forecast():
    """Get revenue forecast with confidence intervals"""
    try:
        store_code = request.args.get('store', 'all')
        periods = int(request.args.get('periods', 6))  # Default 6 months
        confidence_level = float(request.args.get('confidence', 0.90))
        
        # Generate mock forecast data
        forecast_data = generate_mock_forecast(store_code, periods, confidence_level)
        
        return jsonify({
            'success': True,
            'forecast': forecast_data,
            'meta': {
                'store_filter': store_code,
                'forecast_periods': periods,
                'confidence_level': confidence_level,
                'model_accuracy': 0.847
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting forecast: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@pnl_analytics_bp.route('/api/variance-analysis')
def get_variance_analysis():
    """Get detailed variance analysis between actual and projected P&L"""
    try:
        store_code = request.args.get('store', 'all')
        period = request.args.get('period', 'monthly')
        
        # Generate mock variance analysis
        variance_data = generate_mock_variance_analysis(store_code, period)
        
        return jsonify({
            'success': True,
            'variance_analysis': variance_data,
            'meta': {
                'store_filter': store_code,
                'analysis_period': period,
                'threshold_warning': 10.0,
                'threshold_critical': 20.0
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting variance analysis: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def enhance_with_external_factors(base_data, factors):
    """Enhance P&L data with external factor correlations"""
    enhanced = base_data.copy() if base_data else {}
    
    if factors == 'none':
        return enhanced
        
    factor_list = factors.split(',') if factors != 'all' else ['weather', 'economic', 'seasonal', 'events']
    
    # Add mock external factor data
    external_data = {}
    
    if 'weather' in factor_list:
        external_data['weather'] = {
            'temperature_correlation': 0.73,
            'precipitation_correlation': -0.41,
            'seasonal_factor': 0.67,
            'current_impact': 'High positive correlation detected'
        }
    
    if 'economic' in factor_list:
        external_data['economic'] = {
            'consumer_confidence_correlation': 0.82,
            'unemployment_correlation': -0.64,
            'gas_price_correlation': -0.38,
            'current_impact': 'Strong positive economic indicators'
        }
    
    if 'seasonal' in factor_list:
        external_data['seasonal'] = {
            'holiday_effect': 1.45,
            'tax_season_effect': 0.87,
            'back_to_school_effect': 1.23,
            'current_impact': 'Moderate seasonal uptrend expected'
        }
    
    if 'events' in factor_list:
        external_data['events'] = {
            'election_lag_weeks': 4,
            'local_event_impact': 0.15,
            'promotional_effectiveness': 1.32,
            'current_impact': 'No significant events detected'
        }
    
    enhanced['external_factors'] = external_data
    return enhanced

def generate_mock_correlations(factor_type, store_code):
    """Generate mock correlation data for different factor types"""
    correlations = {}
    
    if factor_type == 'weather':
        correlations = {
            'temperature': {
                'coefficient': 0.73,
                'p_value': 0.001,
                'significance': 'Strong',
                'description': 'Higher temperatures strongly correlate with increased revenue'
            },
            'precipitation': {
                'coefficient': -0.41,
                'p_value': 0.032,
                'significance': 'Moderate',
                'description': 'Heavy precipitation moderately reduces foot traffic and sales'
            },
            'humidity': {
                'coefficient': -0.28,
                'p_value': 0.087,
                'significance': 'Weak',
                'description': 'High humidity shows weak negative correlation with revenue'
            }
        }
    elif factor_type == 'economic':
        correlations = {
            'consumer_confidence': {
                'coefficient': 0.82,
                'p_value': 0.0001,
                'significance': 'Very Strong',
                'description': 'Consumer confidence is the strongest economic predictor'
            },
            'unemployment': {
                'coefficient': -0.64,
                'p_value': 0.003,
                'significance': 'Strong',
                'description': 'Local unemployment negatively impacts revenue with 4-week lag'
            },
            'gas_prices': {
                'coefficient': -0.38,
                'p_value': 0.041,
                'significance': 'Moderate',
                'description': 'Rising gas prices moderately reduce discretionary spending'
            }
        }
    
    return correlations

def generate_mock_forecast(store_code, periods, confidence_level):
    """Generate mock forecast data with confidence intervals"""
    import random
    from datetime import datetime, timedelta
    
    base_revenue = 125000 if store_code == 'all' else {
        '6800': 145000,  # Brooklyn Park
        '3607': 160000,  # Wayzata
        '8101': 115000,  # Fridley
        '728': 95000     # Elk River
    }.get(store_code, 125000)
    
    forecast = []
    current_date = datetime.now()
    
    for i in range(periods):
        month_date = current_date + timedelta(days=30 * (i + 1))
        
        # Add some randomness and seasonal trends
        seasonal_factor = 1.0 + 0.2 * (i % 4 - 2) / 4  # Simple seasonal pattern
        growth_trend = 1.0 + (i * 0.02)  # 2% monthly growth trend
        random_factor = 1.0 + (random.random() - 0.5) * 0.1  # ±5% randomness
        
        predicted_value = base_revenue * seasonal_factor * growth_trend * random_factor
        
        # Calculate confidence intervals
        margin_of_error = predicted_value * (1 - confidence_level) * 0.5
        
        forecast.append({
            'date': month_date.strftime('%Y-%m'),
            'predicted_value': round(predicted_value),
            'lower_bound': round(predicted_value - margin_of_error),
            'upper_bound': round(predicted_value + margin_of_error),
            'confidence_level': confidence_level,
            'factors': {
                'seasonal': round(seasonal_factor, 2),
                'trend': round(growth_trend, 2),
                'uncertainty': round(random_factor, 2)
            }
        })
    
    return forecast

def generate_mock_variance_analysis(store_code, period):
    """Generate mock variance analysis data"""
    import random
    from datetime import datetime, timedelta
    
    # Mock historical data for variance analysis
    variance_data = []
    current_date = datetime.now()
    
    for i in range(12):  # Last 12 periods
        period_date = current_date - timedelta(days=30 * (12 - i))
        
        # Mock actual vs projected values
        projected = 125000 + random.randint(-15000, 15000)
        variance_pct = (random.random() - 0.5) * 40  # ±20% variance
        actual = projected * (1 + variance_pct / 100)
        
        variance_data.append({
            'period': period_date.strftime('%Y-%m'),
            'actual': round(actual),
            'projected': round(projected),
            'variance_amount': round(actual - projected),
            'variance_percent': round(variance_pct, 1),
            'variance_category': 'Positive' if variance_pct > 5 else 'Negative' if variance_pct < -5 else 'Normal',
            'explanation': get_variance_explanation(variance_pct)
        })
    
    return variance_data

def get_variance_explanation(variance_pct):
    """Get explanation for variance based on percentage"""
    if variance_pct > 15:
        return "Exceptional performance - likely due to successful promotions or seasonal surge"
    elif variance_pct > 5:
        return "Above expectations - positive market conditions or operational improvements"
    elif variance_pct > -5:
        return "Within normal range - performance aligned with projections"
    elif variance_pct > -15:
        return "Below expectations - may indicate market challenges or operational issues"
    else:
        return "Significant underperformance - requires immediate investigation and corrective action"