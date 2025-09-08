# app/routes/manager_dashboards.py
# Manager-Specific Dashboard Views - Version: 2025-09-02-v1
"""
Manager dashboard routes providing personalized views for each store manager.
Each manager gets a customized dashboard based on their store's business type,
performance metrics, and operational focus areas.
"""

from flask import Blueprint, render_template, request, jsonify
from sqlalchemy import text, and_, func
from app import db
from app.config.stores import STORES, ACTIVE_STORES, get_store_manager, get_store_business_type
from app.services.manager_analytics_service import ManagerAnalyticsService
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Manager dashboards blueprint
manager_bp = Blueprint('manager_dashboards', __name__, url_prefix='/manager')

@manager_bp.route('/')
def manager_home():
    """Manager dashboard home - shows all available manager views."""
    try:
        managers_data = []
        for store_code, store_info in ACTIVE_STORES.items():
            managers_data.append({
                'store_code': store_code,
                'store_name': store_info.name,
                'manager': store_info.manager,
                'location': store_info.location,
                'business_type': store_info.business_type,
                'emoji': store_info.emoji,
                'approximate_items': store_info.approximate_items,
                'opened_date': store_info.opened_date
            })
        
        return render_template('manager/manager_home.html', 
                               managers=managers_data,
                               page_title="Manager Dashboards")
    
    except Exception as e:
        logger.error(f"Error in manager home: {str(e)}")
        return f"<h1>Error</h1><p>Failed to load manager dashboards: {str(e)}</p>", 500


@manager_bp.route('/<store_code>')
def manager_dashboard(store_code):
    """Individual manager dashboard for specific store."""
    try:
        # Validate store code
        if store_code not in ACTIVE_STORES:
            return f"<h1>404 Not Found</h1><p>Invalid store code: {store_code}</p>", 404
        
        store_info = STORES[store_code]
        
        # Get manager analytics service
        analytics_service = ManagerAnalyticsService(store_code)
        
        # Get comprehensive analytics data
        dashboard_data = analytics_service.get_manager_dashboard_data()
        
        # Template selection based on business type
        template_map = {
            '90% DIY/10% Events': 'manager/diy_manager_dashboard.html',
            '100% Construction': 'manager/construction_manager_dashboard.html', 
            '100% Events (Broadway Tent & Event)': 'manager/events_manager_dashboard.html'
        }
        
        template = template_map.get(store_info.business_type, 'manager/general_manager_dashboard.html')
        
        return render_template(template,
                               store_code=store_code,
                               store_info=store_info,
                               dashboard_data=dashboard_data,
                               page_title=f"{store_info.manager}'s Dashboard - {store_info.name}")
    
    except Exception as e:
        logger.error(f"Error in manager dashboard for store {store_code}: {str(e)}")
        return f"<h1>Error</h1><p>Failed to load dashboard for {store_code}: {str(e)}</p>", 500


@manager_bp.route('/<store_code>/api/kpis')
def get_manager_kpis(store_code):
    """API endpoint for manager-specific KPIs."""
    try:
        if store_code not in ACTIVE_STORES:
            return jsonify({'error': 'Invalid store code'}), 404
        
        analytics_service = ManagerAnalyticsService(store_code)
        kpis = analytics_service.get_manager_kpis()
        
        return jsonify(kpis)
    
    except Exception as e:
        logger.error(f"Error getting KPIs for store {store_code}: {str(e)}")
        return jsonify({'error': 'Failed to fetch KPIs'}), 500


@manager_bp.route('/<store_code>/api/performance-trends')
def get_performance_trends(store_code):
    """API endpoint for performance trend data."""
    try:
        if store_code not in ACTIVE_STORES:
            return jsonify({'error': 'Invalid store code'}), 404
        
        # OLD - HARDCODED (WRONG): days = request.args.get('days', 30, type=int)
        # NEW - CONFIGURABLE (CORRECT):
        from app.models.config_models import ManagerDashboardConfiguration, get_default_manager_dashboard_config
        try:
            config = ManagerDashboardConfiguration.query.filter_by(user_id='default_user', config_name='default').first()
            if config:
                default_days = config.get_store_threshold(store_code, 'default_trend_period_days')
            else:
                defaults = get_default_manager_dashboard_config()
                default_days = defaults['time_periods']['default_trend_days']
        except Exception:
            default_days = 30  # Safe fallback
        
        days = request.args.get('days', default_days, type=int)
        analytics_service = ManagerAnalyticsService(store_code)
        trends = analytics_service.get_performance_trends(days)
        
        return jsonify(trends)
    
    except Exception as e:
        logger.error(f"Error getting performance trends for store {store_code}: {str(e)}")
        return jsonify({'error': 'Failed to fetch performance trends'}), 500


@manager_bp.route('/<store_code>/api/inventory-insights')
def get_inventory_insights(store_code):
    """API endpoint for inventory-specific insights."""
    try:
        if store_code not in ACTIVE_STORES:
            return jsonify({'error': 'Invalid store code'}), 404
        
        analytics_service = ManagerAnalyticsService(store_code)
        insights = analytics_service.get_inventory_insights()
        
        return jsonify(insights)
    
    except Exception as e:
        logger.error(f"Error getting inventory insights for store {store_code}: {str(e)}")
        return jsonify({'error': 'Failed to fetch inventory insights'}), 500


@manager_bp.route('/<store_code>/api/financial-summary')
def get_financial_summary(store_code):
    """API endpoint for financial performance summary."""
    try:
        if store_code not in ACTIVE_STORES:
            return jsonify({'error': 'Invalid store code'}), 404
        
        period = request.args.get('period', 'month')  # month, quarter, year
        analytics_service = ManagerAnalyticsService(store_code)
        summary = analytics_service.get_financial_summary(period)
        
        return jsonify(summary)
    
    except Exception as e:
        logger.error(f"Error getting financial summary for store {store_code}: {str(e)}")
        return jsonify({'error': 'Failed to fetch financial summary'}), 500


@manager_bp.route('/executive')
def executive_overview():
    """Executive overview combining all store managers' data."""
    try:
        analytics_service = ManagerAnalyticsService()  # No specific store for executive view
        
        # Get cross-store executive data
        executive_data = analytics_service.get_executive_overview()
        
        return render_template('manager/executive_overview.html',
                               executive_data=executive_data,
                               stores=ACTIVE_STORES,
                               page_title="Executive Overview - All Managers")
    
    except Exception as e:
        logger.error(f"Error in executive overview: {str(e)}")
        return f"<h1>Error</h1><p>Failed to load executive overview: {str(e)}</p>", 500


@manager_bp.route('/api/store-comparison')
def get_store_comparison():
    """API endpoint for cross-store performance comparison."""
    try:
        metric = request.args.get('metric', 'revenue')  # revenue, inventory_turns, efficiency
        period = request.args.get('period', 'month')
        
        analytics_service = ManagerAnalyticsService()
        comparison = analytics_service.get_store_comparison(metric, period)
        
        return jsonify(comparison)
    
    except Exception as e:
        logger.error(f"Error getting store comparison: {str(e)}")
        return jsonify({'error': 'Failed to fetch store comparison'}), 500


@manager_bp.route('/api/manager-alerts')
def get_manager_alerts():
    """API endpoint for manager-specific alerts and notifications."""
    try:
        store_code = request.args.get('store_code')
        if store_code and store_code not in ACTIVE_STORES:
            return jsonify({'error': 'Invalid store code'}), 404
        
        analytics_service = ManagerAnalyticsService(store_code if store_code else None)
        alerts = analytics_service.get_manager_alerts()
        
        return jsonify(alerts)
    
    except Exception as e:
        logger.error(f"Error getting manager alerts: {str(e)}")
        return jsonify({'error': 'Failed to fetch alerts'}), 500


# Error handlers
@manager_bp.errorhandler(404)
def not_found_error(error):
    return "<h1>404 Not Found</h1><p>Manager dashboard not found</p>", 404

@manager_bp.errorhandler(500)
def internal_error(error):
    return "<h1>500 Server Error</h1><p>Internal server error in manager dashboard</p>", 500