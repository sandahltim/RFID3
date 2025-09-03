"""
Predictive Analytics Routes for RFID3 Equipment Rental System
Routes for predictive analytics dashboard and API endpoints
"""

from flask import Blueprint, render_template, jsonify, request, current_app
from datetime import datetime, timedelta
import logging
import json

from app.services.predictive_analytics_service import PredictiveAnalyticsService
from app.services.ml_data_pipeline_service import MLDataPipelineService
from app.services.predictive_visualization_service import PredictiveVisualizationService
from app.services.enhanced_executive_service import EnhancedExecutiveService

# Create blueprint
predictive_bp = Blueprint('predictive_analytics', __name__)

# Initialize services
predictive_service = PredictiveAnalyticsService()
pipeline_service = MLDataPipelineService()
visualization_service = PredictiveVisualizationService()
executive_service = EnhancedExecutiveService()

logger = logging.getLogger(__name__)

@predictive_bp.route('/predictive-dashboard')
@predictive_bp.route('/predictive-dashboard/<int:store_id>')
def predictive_dashboard(store_id=None):
    """
    Main predictive analytics dashboard page
    """
    try:
        # Get basic store information for context
        store_context = _get_store_context(store_id)
        
        # Get predictive analytics data
        dashboard_data = visualization_service.get_executive_predictive_dashboard(store_id)
        
        if not dashboard_data.get('success'):
            current_app.logger.error(f"Failed to load predictive dashboard: {dashboard_data.get('error')}")
            return render_template('error.html', 
                                error="Unable to load predictive analytics dashboard",
                                details=dashboard_data.get('error', 'Unknown error'))
        
        return render_template('predictive_analytics/dashboard.html',
                             dashboard_data=dashboard_data['dashboard'],
                             metadata=dashboard_data.get('metadata', {}),
                             store_context=store_context,
                             page_title="Predictive Analytics Dashboard")
        
    except Exception as e:
        current_app.logger.error(f"Error loading predictive dashboard: {str(e)}")
        return render_template('error.html', 
                             error="Dashboard Error", 
                             details=str(e))

@predictive_bp.route('/api/forecasts')
@predictive_bp.route('/api/forecasts/<int:store_id>')
def api_demand_forecasts(store_id=None):
    """
    API endpoint for demand forecasts
    """
    try:
        horizon = request.args.get('horizon', 'short_term')
        category = request.args.get('category')
        
        forecasts = predictive_service.get_demand_forecasts(store_id)
        
        if category:
            # Filter by category if specified
            category_forecasts = forecasts.get('category_forecasts', {})
            if category in category_forecasts:
                forecasts = {'category_forecasts': {category: category_forecasts[category]}}
        
        if horizon != 'all':
            # Filter by horizon if specified
            overall_forecasts = forecasts.get('overall_forecasts', {})
            if horizon in overall_forecasts:
                forecasts['overall_forecasts'] = {horizon: overall_forecasts[horizon]}
        
        return jsonify({
            'success': True,
            'data': forecasts,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting demand forecasts: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@predictive_bp.route('/api/revenue-predictions')
@predictive_bp.route('/api/revenue-predictions/<int:store_id>')
def api_revenue_predictions(store_id=None):
    """
    API endpoint for revenue predictions
    """
    try:
        predictions = predictive_service.get_revenue_predictions(store_id)
        
        return jsonify({
            'success': True,
            'data': predictions,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting revenue predictions: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@predictive_bp.route('/api/utilization-recommendations')
@predictive_bp.route('/api/utilization-recommendations/<int:store_id>')
def api_utilization_recommendations(store_id=None):
    """
    API endpoint for utilization optimization recommendations
    """
    try:
        recommendations = predictive_service.get_utilization_recommendations(store_id)
        
        return jsonify({
            'success': True,
            'data': recommendations,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting utilization recommendations: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@predictive_bp.route('/api/seasonal-insights')
@predictive_bp.route('/api/seasonal-insights/<int:store_id>')
def api_seasonal_insights(store_id=None):
    """
    API endpoint for seasonal insights and predictions
    """
    try:
        insights = predictive_service.get_seasonal_analysis(store_id)
        
        return jsonify({
            'success': True,
            'data': insights,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting seasonal insights: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@predictive_bp.route('/api/risk-opportunities')
@predictive_bp.route('/api/risk-opportunities/<int:store_id>')
def api_risk_opportunities(store_id=None):
    """
    API endpoint for risk and opportunity alerts
    """
    try:
        alerts = predictive_service.get_risk_opportunity_alerts(store_id)
        
        return jsonify({
            'success': True,
            'data': alerts,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting risk/opportunity alerts: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@predictive_bp.route('/api/data-quality')
@predictive_bp.route('/api/data-quality/<int:store_id>')
def api_data_quality(store_id=None):
    """
    API endpoint for data quality assessment
    """
    try:
        quality_score = predictive_service.calculate_data_quality_score(store_id)
        
        return jsonify({
            'success': True,
            'data': quality_score,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting data quality score: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@predictive_bp.route('/api/model-performance')
def api_model_performance():
    """
    API endpoint for model performance metrics
    """
    try:
        performance = predictive_service.get_model_performance_metrics()
        
        return jsonify({
            'success': True,
            'data': performance,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting model performance: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@predictive_bp.route('/api/ml-dataset')
@predictive_bp.route('/api/ml-dataset/<int:store_id>')
def api_ml_dataset(store_id=None):
    """
    API endpoint for ML dataset preparation
    """
    try:
        dataset_type = request.args.get('type', 'demand_forecasting')
        target_days = int(request.args.get('target_days', 30))
        
        if dataset_type == 'demand_forecasting':
            dataset = pipeline_service.prepare_demand_forecasting_dataset(store_id, target_days)
        elif dataset_type == 'revenue_prediction':
            dataset = pipeline_service.prepare_revenue_prediction_dataset(store_id, target_days)
        elif dataset_type == 'utilization_optimization':
            dataset = pipeline_service.prepare_utilization_optimization_dataset(store_id)
        else:
            return jsonify({
                'success': False,
                'error': f'Unknown dataset type: {dataset_type}'
            }), 400
        
        # Convert DataFrame to JSON serializable format
        if 'dataset' in dataset and hasattr(dataset['dataset'], 'to_dict'):
            dataset_dict = dataset['dataset'].to_dict('records')
            dataset['dataset'] = {
                'data': dataset_dict[:100],  # Limit to first 100 rows for API response
                'shape': dataset['dataset'].shape,
                'columns': list(dataset['dataset'].columns)
            }
        
        return jsonify({
            'success': True,
            'data': dataset,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error preparing ML dataset: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@predictive_bp.route('/api/visualization-config')
@predictive_bp.route('/api/visualization-config/<int:store_id>')
def api_visualization_config(store_id=None):
    """
    API endpoint for chart configurations
    """
    try:
        chart_type = request.args.get('type', 'forecast')
        
        if chart_type == 'forecast':
            config = visualization_service.create_forecast_visualization(
                predictive_service.get_demand_forecasts(store_id)
            )
        elif chart_type == 'revenue':
            config = visualization_service.create_revenue_prediction_charts(
                predictive_service.get_revenue_predictions(store_id)
            )
        elif chart_type == 'utilization':
            config = visualization_service.create_utilization_heatmap(
                predictive_service.get_utilization_recommendations(store_id)
            )
        elif chart_type == 'seasonal':
            config = visualization_service.create_seasonal_insight_charts(
                predictive_service.get_seasonal_analysis(store_id)
            )
        else:
            return jsonify({
                'success': False,
                'error': f'Unknown chart type: {chart_type}'
            }), 400
        
        return jsonify({
            'success': True,
            'data': config,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting visualization config: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@predictive_bp.route('/equipment-lifecycle')
@predictive_bp.route('/equipment-lifecycle/<int:store_id>')
def equipment_lifecycle_page(store_id=None):
    """
    Equipment lifecycle analysis page
    """
    try:
        lifecycle_data = predictive_service.get_equipment_lifecycle_analysis(store_id)
        store_context = _get_store_context(store_id)
        
        return render_template('predictive_analytics/equipment_lifecycle.html',
                             lifecycle_data=lifecycle_data,
                             store_context=store_context,
                             page_title="Equipment Lifecycle Analysis")
        
    except Exception as e:
        current_app.logger.error(f"Error loading equipment lifecycle page: {str(e)}")
        return render_template('error.html', 
                             error="Equipment Lifecycle Error", 
                             details=str(e))

@predictive_bp.route('/model-monitoring')
def model_monitoring_page():
    """
    Model performance monitoring page
    """
    try:
        performance_data = predictive_service.get_model_performance_metrics()
        
        return render_template('predictive_analytics/model_monitoring.html',
                             performance_data=performance_data,
                             page_title="Model Performance Monitoring")
        
    except Exception as e:
        current_app.logger.error(f"Error loading model monitoring page: {str(e)}")
        return render_template('error.html', 
                             error="Model Monitoring Error", 
                             details=str(e))

@predictive_bp.route('/data-pipeline')
def data_pipeline_page():
    """
    Data pipeline management page
    """
    try:
        # Get sample dataset quality information
        dataset_info = pipeline_service.prepare_demand_forecasting_dataset()
        
        return render_template('predictive_analytics/data_pipeline.html',
                             dataset_info=dataset_info,
                             page_title="ML Data Pipeline")
        
    except Exception as e:
        current_app.logger.error(f"Error loading data pipeline page: {str(e)}")
        return render_template('error.html', 
                             error="Data Pipeline Error", 
                             details=str(e))

# Helper functions

def _get_store_context(store_id=None):
    """
    Get store context information
    """
    try:
        if store_id:
            # This would typically query the database for store information
            store_context = {
                'store_id': store_id,
                'store_name': f'Store {store_id}',
                'business_type': 'Equipment Rental',
                'is_multi_store': False
            }
        else:
            store_context = {
                'store_id': None,
                'store_name': 'All Stores',
                'business_type': 'Equipment Rental',
                'is_multi_store': True
            }
        
        return store_context
        
    except Exception as e:
        logger.error(f"Error getting store context: {str(e)}")
        return {
            'store_id': store_id,
            'store_name': 'Unknown Store',
            'business_type': 'Equipment Rental',
            'is_multi_store': False
        }

# Error handlers specific to predictive analytics

@predictive_bp.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors in predictive analytics routes"""
    return render_template('error.html', 
                          error="Page Not Found", 
                          details="The requested predictive analytics page was not found."), 404

@predictive_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors in predictive analytics routes"""
    return render_template('error.html', 
                          error="Internal Server Error", 
                          details="An error occurred while processing predictive analytics."), 500

# Template filters for predictive analytics

@predictive_bp.app_template_filter('format_confidence')
def format_confidence(value):
    """Format confidence values as percentages"""
    try:
        return f"{float(value) * 100:.1f}%"
    except (ValueError, TypeError):
        return "N/A"

@predictive_bp.app_template_filter('format_forecast_value')
def format_forecast_value(value):
    """Format forecast values"""
    try:
        return f"{float(value):,.0f}"
    except (ValueError, TypeError):
        return "N/A"

@predictive_bp.app_template_filter('format_currency')
def format_currency(value):
    """Format currency values"""
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"

@predictive_bp.app_template_filter('alert_priority_class')
def alert_priority_class(priority):
    """Get CSS class for alert priority"""
    priority_classes = {
        'critical': 'alert-danger',
        'high': 'alert-warning',
        'medium': 'alert-info',
        'low': 'alert-light'
    }
    return priority_classes.get(priority.lower(), 'alert-secondary')

@predictive_bp.app_template_filter('quality_score_class')
def quality_score_class(score):
    """Get CSS class for quality score"""
    try:
        score = float(score)
        if score >= 90:
            return 'text-success'
        elif score >= 75:
            return 'text-warning'
        elif score >= 50:
            return 'text-danger'
        else:
            return 'text-muted'
    except (ValueError, TypeError):
        return 'text-muted'