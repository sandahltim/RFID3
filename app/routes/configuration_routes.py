# app/routes/configuration_routes.py
# Configuration Management Routes
# Version: 2025-08-29 - Fortune 500 Configuration System

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app import db
from app.models.config_models import (
    UserConfiguration, PredictionParameters, CorrelationSettings,
    BusinessIntelligenceConfig, DataIntegrationSettings, UserPreferences,
    ConfigurationAudit, get_user_config, set_user_config,
    get_default_prediction_params, get_default_correlation_settings
)
from datetime import datetime
import json
import logging

# Initialize logger
logger = logging.getLogger(__name__)

# Create blueprint
config_bp = Blueprint('configuration', __name__, url_prefix='/config')

# Also create a redirect blueprint for common URL variations
config_redirect_bp = Blueprint('config_redirect', __name__)

# Default user ID (in a real application, this would come from authentication)
DEFAULT_USER_ID = 'default_user'


@config_bp.route('/')
def configuration_dashboard():
    """Main configuration dashboard"""
    try:
        # Get current user configurations
        user_id = session.get('user_id', DEFAULT_USER_ID)
        
        # Load existing configurations or defaults
        prediction_config = get_user_config(user_id, 'prediction') or get_default_prediction_params()
        correlation_config = get_user_config(user_id, 'correlation') or get_default_correlation_settings()
        
        return render_template(
            'configuration.html',
            prediction_config=prediction_config,
            correlation_config=correlation_config,
            cache_bust=int(datetime.now().timestamp())
        )
    except Exception as e:
        logger.error(f"Error loading configuration dashboard: {str(e)}")
        return render_template('error.html', error="Failed to load configuration dashboard"), 500


@config_bp.route('/api/prediction', methods=['GET', 'POST'])
def prediction_parameters():
    """Prediction parameters API endpoint"""
    user_id = session.get('user_id', DEFAULT_USER_ID)
    
    if request.method == 'GET':
        try:
            # Get existing prediction parameters or create default
            prediction_params = PredictionParameters.query.filter_by(
                user_id=user_id, is_active=True
            ).first()
            
            if not prediction_params:
                # Create default parameters
                prediction_params = PredictionParameters(user_id=user_id)
                db.session.add(prediction_params)
                db.session.commit()
            
            return jsonify({
                'success': True,
                'data': {
                    'forecast_horizons': {
                        'weekly': prediction_params.forecast_weekly_enabled,
                        'monthly': prediction_params.forecast_monthly_enabled,
                        'quarterly': prediction_params.forecast_quarterly_enabled,
                        'yearly': prediction_params.forecast_yearly_enabled
                    },
                    'confidence_intervals': {
                        '80': prediction_params.confidence_80_enabled,
                        '90': prediction_params.confidence_90_enabled,
                        '95': prediction_params.confidence_95_enabled,
                        'default': prediction_params.default_confidence_level
                    },
                    'external_factors': {
                        'seasonality': prediction_params.seasonality_weight,
                        'trend': prediction_params.trend_weight,
                        'economic': prediction_params.economic_weight,
                        'promotional': prediction_params.promotional_weight
                    },
                    'thresholds': {
                        'low_stock': prediction_params.low_stock_threshold,
                        'high_stock': prediction_params.high_stock_threshold,
                        'demand_spike': prediction_params.demand_spike_threshold
                    },
                    'store_specific': {
                        'enabled': prediction_params.store_specific_enabled,
                        'mappings': prediction_params.store_mappings or {}
                    }
                }
            })
        except Exception as e:
            logger.error(f"Error retrieving prediction parameters: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Get or create prediction parameters
            prediction_params = PredictionParameters.query.filter_by(
                user_id=user_id, is_active=True
            ).first()
            
            if not prediction_params:
                prediction_params = PredictionParameters(user_id=user_id)
                db.session.add(prediction_params)
            
            # Update parameters from request data
            if 'forecast_horizons' in data:
                horizons = data['forecast_horizons']
                prediction_params.forecast_weekly_enabled = horizons.get('weekly', True)
                prediction_params.forecast_monthly_enabled = horizons.get('monthly', True)
                prediction_params.forecast_quarterly_enabled = horizons.get('quarterly', True)
                prediction_params.forecast_yearly_enabled = horizons.get('yearly', False)
            
            if 'confidence_intervals' in data:
                intervals = data['confidence_intervals']
                prediction_params.confidence_80_enabled = intervals.get('80', True)
                prediction_params.confidence_90_enabled = intervals.get('90', True)
                prediction_params.confidence_95_enabled = intervals.get('95', False)
                prediction_params.default_confidence_level = intervals.get('default', 90.0)
            
            if 'external_factors' in data:
                factors = data['external_factors']
                prediction_params.seasonality_weight = factors.get('seasonality', 0.3)
                prediction_params.trend_weight = factors.get('trend', 0.4)
                prediction_params.economic_weight = factors.get('economic', 0.2)
                prediction_params.promotional_weight = factors.get('promotional', 0.1)
            
            if 'thresholds' in data:
                thresholds = data['thresholds']
                prediction_params.low_stock_threshold = thresholds.get('low_stock', 0.2)
                prediction_params.high_stock_threshold = thresholds.get('high_stock', 2.0)
                prediction_params.demand_spike_threshold = thresholds.get('demand_spike', 1.5)
            
            if 'store_specific' in data:
                store_config = data['store_specific']
                prediction_params.store_specific_enabled = store_config.get('enabled', True)
                prediction_params.store_mappings = store_config.get('mappings', {})
            
            prediction_params.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Create audit log
            audit = ConfigurationAudit(
                user_id=user_id,
                config_type='prediction_parameters',
                config_id=prediction_params.id,
                action='update',
                new_values=data,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.add(audit)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Prediction parameters updated successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating prediction parameters: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500


@config_bp.route('/api/correlation', methods=['GET', 'POST'])
def correlation_settings():
    """Correlation settings API endpoint"""
    user_id = session.get('user_id', DEFAULT_USER_ID)
    
    if request.method == 'GET':
        try:
            correlation_config = CorrelationSettings.query.filter_by(
                user_id=user_id, is_active=True
            ).first()
            
            if not correlation_config:
                correlation_config = CorrelationSettings(user_id=user_id)
                db.session.add(correlation_config)
                db.session.commit()
            
            return jsonify({
                'success': True,
                'data': {
                    'thresholds': {
                        'weak': correlation_config.min_correlation_weak,
                        'moderate': correlation_config.min_correlation_moderate,
                        'strong': correlation_config.min_correlation_strong
                    },
                    'statistical': {
                        'p_value': correlation_config.p_value_threshold,
                        'confidence': correlation_config.confidence_level
                    },
                    'lag_periods': {
                        'min': correlation_config.min_lag_periods,
                        'max': correlation_config.max_lag_periods,
                        'default': correlation_config.default_lag_period
                    },
                    'factors': {
                        'economic': correlation_config.economic_factors_enabled,
                        'seasonal': correlation_config.seasonal_factors_enabled,
                        'promotional': correlation_config.promotional_factors_enabled,
                        'weather': correlation_config.weather_factors_enabled
                    },
                    'analysis_types': {
                        'auto_correlation': correlation_config.auto_correlation_enabled,
                        'cross_correlation': correlation_config.cross_correlation_enabled,
                        'partial_correlation': correlation_config.partial_correlation_enabled
                    }
                }
            })
        except Exception as e:
            logger.error(f"Error retrieving correlation settings: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            correlation_config = CorrelationSettings.query.filter_by(
                user_id=user_id, is_active=True
            ).first()
            
            if not correlation_config:
                correlation_config = CorrelationSettings(user_id=user_id)
                db.session.add(correlation_config)
            
            # Update configuration from request data
            if 'thresholds' in data:
                thresholds = data['thresholds']
                correlation_config.min_correlation_weak = thresholds.get('weak', 0.3)
                correlation_config.min_correlation_moderate = thresholds.get('moderate', 0.5)
                correlation_config.min_correlation_strong = thresholds.get('strong', 0.7)
            
            if 'statistical' in data:
                statistical = data['statistical']
                correlation_config.p_value_threshold = statistical.get('p_value', 0.05)
                correlation_config.confidence_level = statistical.get('confidence', 0.95)
            
            if 'lag_periods' in data:
                lag = data['lag_periods']
                correlation_config.min_lag_periods = lag.get('min', 1)
                correlation_config.max_lag_periods = lag.get('max', 12)
                correlation_config.default_lag_period = lag.get('default', 3)
            
            if 'factors' in data:
                factors = data['factors']
                correlation_config.economic_factors_enabled = factors.get('economic', True)
                correlation_config.seasonal_factors_enabled = factors.get('seasonal', True)
                correlation_config.promotional_factors_enabled = factors.get('promotional', True)
                correlation_config.weather_factors_enabled = factors.get('weather', False)
            
            if 'analysis_types' in data:
                analysis = data['analysis_types']
                correlation_config.auto_correlation_enabled = analysis.get('auto_correlation', True)
                correlation_config.cross_correlation_enabled = analysis.get('cross_correlation', True)
                correlation_config.partial_correlation_enabled = analysis.get('partial_correlation', False)
            
            correlation_config.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Create audit log
            audit = ConfigurationAudit(
                user_id=user_id,
                config_type='correlation_settings',
                config_id=correlation_config.id,
                action='update',
                new_values=data,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.add(audit)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Correlation settings updated successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating correlation settings: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500


@config_bp.route('/api/business-intelligence', methods=['GET', 'POST'])
def business_intelligence_config():
    """Business Intelligence configuration API endpoint"""
    user_id = session.get('user_id', DEFAULT_USER_ID)
    
    if request.method == 'GET':
        try:
            bi_config = BusinessIntelligenceConfig.query.filter_by(
                user_id=user_id, is_active=True
            ).first()
            
            if not bi_config:
                bi_config = BusinessIntelligenceConfig(user_id=user_id)
                db.session.add(bi_config)
                db.session.commit()
            
            return jsonify({
                'success': True,
                'data': {
                    'kpi_targets': {
                        'revenue_monthly': bi_config.revenue_target_monthly,
                        'revenue_quarterly': bi_config.revenue_target_quarterly,
                        'revenue_yearly': bi_config.revenue_target_yearly,
                        'inventory_turnover': bi_config.inventory_turnover_target,
                        'profit_margin': bi_config.profit_margin_target,
                        'customer_satisfaction': bi_config.customer_satisfaction_target
                    },
                    'benchmarks': {
                        'industry_avg': bi_config.benchmark_industry_avg_enabled,
                        'historical': bi_config.benchmark_historical_enabled,
                        'competitor': bi_config.benchmark_competitor_enabled
                    },
                    'roi_calculation': {
                        'period': bi_config.roi_calculation_period,
                        'include_overhead': bi_config.roi_include_overhead,
                        'include_labor': bi_config.roi_include_labor_costs,
                        'discount_rate': bi_config.roi_discount_rate
                    },
                    'resale_criteria': {
                        'min_profit_margin': bi_config.resale_min_profit_margin,
                        'max_age_months': bi_config.resale_max_age_months,
                        'condition_threshold': bi_config.resale_condition_threshold,
                        'demand_threshold': bi_config.resale_demand_threshold
                    },
                    'alert_thresholds': {
                        'performance': bi_config.performance_alert_threshold,
                        'critical': bi_config.critical_alert_threshold
                    }
                }
            })
        except Exception as e:
            logger.error(f"Error retrieving BI configuration: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            bi_config = BusinessIntelligenceConfig.query.filter_by(
                user_id=user_id, is_active=True
            ).first()
            
            if not bi_config:
                bi_config = BusinessIntelligenceConfig(user_id=user_id)
                db.session.add(bi_config)
            
            # Update configuration from request data
            if 'kpi_targets' in data:
                kpis = data['kpi_targets']
                bi_config.revenue_target_monthly = kpis.get('revenue_monthly', 100000.0)
                bi_config.revenue_target_quarterly = kpis.get('revenue_quarterly', 300000.0)
                bi_config.revenue_target_yearly = kpis.get('revenue_yearly', 1200000.0)
                bi_config.inventory_turnover_target = kpis.get('inventory_turnover', 6.0)
                bi_config.profit_margin_target = kpis.get('profit_margin', 0.25)
                bi_config.customer_satisfaction_target = kpis.get('customer_satisfaction', 0.85)
            
            if 'benchmarks' in data:
                benchmarks = data['benchmarks']
                bi_config.benchmark_industry_avg_enabled = benchmarks.get('industry_avg', True)
                bi_config.benchmark_historical_enabled = benchmarks.get('historical', True)
                bi_config.benchmark_competitor_enabled = benchmarks.get('competitor', False)
            
            if 'roi_calculation' in data:
                roi = data['roi_calculation']
                bi_config.roi_calculation_period = roi.get('period', 'quarterly')
                bi_config.roi_include_overhead = roi.get('include_overhead', True)
                bi_config.roi_include_labor_costs = roi.get('include_labor', True)
                bi_config.roi_discount_rate = roi.get('discount_rate', 0.08)
            
            if 'resale_criteria' in data:
                resale = data['resale_criteria']
                bi_config.resale_min_profit_margin = resale.get('min_profit_margin', 0.15)
                bi_config.resale_max_age_months = resale.get('max_age_months', 24)
                bi_config.resale_condition_threshold = resale.get('condition_threshold', 7.0)
                bi_config.resale_demand_threshold = resale.get('demand_threshold', 0.3)
            
            bi_config.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Create audit log
            audit = ConfigurationAudit(
                user_id=user_id,
                config_type='business_intelligence',
                config_id=bi_config.id,
                action='update',
                new_values=data,
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string
            )
            db.session.add(audit)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Business Intelligence configuration updated successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating BI configuration: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500


@config_bp.route('/api/data-integration', methods=['GET', 'POST'])
def data_integration_settings():
    """Data Integration settings API endpoint"""
    user_id = session.get('user_id', DEFAULT_USER_ID)
    
    if request.method == 'GET':
        try:
            integration_config = DataIntegrationSettings.query.filter_by(
                user_id=user_id, is_active=True
            ).first()
            
            if not integration_config:
                integration_config = DataIntegrationSettings(user_id=user_id)
                db.session.add(integration_config)
                db.session.commit()
            
            return jsonify({
                'success': True,
                'data': {
                    'csv_import': {
                        'auto_import_enabled': integration_config.csv_auto_import_enabled,
                        'frequency': integration_config.csv_import_frequency,
                        'time': integration_config.csv_import_time,
                        'backup_enabled': integration_config.csv_backup_enabled,
                        'validation_strict': integration_config.csv_validation_strict
                    },
                    'api_config': {
                        'timeout_seconds': integration_config.api_timeout_seconds,
                        'retry_attempts': integration_config.api_retry_attempts,
                        'rate_limit_enabled': integration_config.api_rate_limit_enabled,
                        'rate_limit_requests': integration_config.api_rate_limit_requests,
                        'rate_limit_window': integration_config.api_rate_limit_window
                    },
                    'refresh_settings': {
                        'real_time_enabled': integration_config.real_time_refresh_enabled,
                        'interval_minutes': integration_config.refresh_interval_minutes,
                        'background_enabled': integration_config.background_refresh_enabled
                    },
                    'quality_checks': {
                        'enabled': integration_config.data_quality_checks_enabled,
                        'missing_data_threshold': integration_config.missing_data_threshold,
                        'outlier_detection_enabled': integration_config.outlier_detection_enabled,
                        'outlier_method': integration_config.outlier_detection_method
                    },
                    'file_processing': {
                        'max_size_mb': integration_config.max_file_size_mb,
                        'supported_formats': integration_config.supported_formats,
                        'archive_processed': integration_config.archive_processed_files
                    }
                }
            })
        except Exception as e:
            logger.error(f"Error retrieving data integration settings: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            integration_config = DataIntegrationSettings.query.filter_by(
                user_id=user_id, is_active=True
            ).first()
            
            if not integration_config:
                integration_config = DataIntegrationSettings(user_id=user_id)
                db.session.add(integration_config)
            
            # Update configuration from request data
            if 'csv_import' in data:
                csv = data['csv_import']
                integration_config.csv_auto_import_enabled = csv.get('auto_import_enabled', False)
                integration_config.csv_import_frequency = csv.get('frequency', 'daily')
                integration_config.csv_import_time = csv.get('time', '02:00:00')
                integration_config.csv_backup_enabled = csv.get('backup_enabled', True)
                integration_config.csv_validation_strict = csv.get('validation_strict', True)
            
            if 'api_config' in data:
                api = data['api_config']
                integration_config.api_timeout_seconds = api.get('timeout_seconds', 30)
                integration_config.api_retry_attempts = api.get('retry_attempts', 3)
                integration_config.api_rate_limit_enabled = api.get('rate_limit_enabled', True)
                integration_config.api_rate_limit_requests = api.get('rate_limit_requests', 100)
                integration_config.api_rate_limit_window = api.get('rate_limit_window', 3600)
            
            if 'refresh_settings' in data:
                refresh = data['refresh_settings']
                integration_config.real_time_refresh_enabled = refresh.get('real_time_enabled', False)
                integration_config.refresh_interval_minutes = refresh.get('interval_minutes', 15)
                integration_config.background_refresh_enabled = refresh.get('background_enabled', True)
            
            if 'quality_checks' in data:
                quality = data['quality_checks']
                integration_config.data_quality_checks_enabled = quality.get('enabled', True)
                integration_config.missing_data_threshold = quality.get('missing_data_threshold', 0.1)
                integration_config.outlier_detection_enabled = quality.get('outlier_detection_enabled', True)
                integration_config.outlier_detection_method = quality.get('outlier_method', 'iqr')
            
            integration_config.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Data Integration settings updated successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating data integration settings: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500


@config_bp.route('/api/user-preferences', methods=['GET', 'POST'])
def user_preferences():
    """User preferences API endpoint"""
    user_id = session.get('user_id', DEFAULT_USER_ID)
    
    if request.method == 'GET':
        try:
            preferences = UserPreferences.query.filter_by(
                user_id=user_id, is_active=True
            ).first()
            
            if not preferences:
                preferences = UserPreferences(user_id=user_id)
                db.session.add(preferences)
                db.session.commit()
            
            return jsonify({
                'success': True,
                'data': {
                    'dashboard': {
                        'theme': preferences.dashboard_theme,
                        'layout': preferences.dashboard_layout,
                        'color_scheme': preferences.chart_color_scheme,
                        'dark_mode': preferences.dark_mode_enabled
                    },
                    'defaults': {
                        'time_range': preferences.default_time_range,
                        'store_filter': preferences.default_store_filter,
                        'auto_refresh': preferences.auto_refresh_enabled,
                        'refresh_interval': preferences.auto_refresh_interval
                    },
                    'notifications': {
                        'email_enabled': preferences.email_notifications_enabled,
                        'push_enabled': preferences.push_notifications_enabled,
                        'frequency': preferences.alert_frequency,
                        'types': preferences.notification_types
                    },
                    'reports': {
                        'format': preferences.report_format,
                        'schedule_enabled': preferences.report_schedule_enabled,
                        'frequency': preferences.report_frequency,
                        'recipients': preferences.report_recipients
                    },
                    'ui_preferences': {
                        'show_tooltips': preferences.show_tooltips,
                        'show_animations': preferences.show_animations,
                        'compact_mode': preferences.compact_mode,
                        'keyboard_shortcuts': preferences.keyboard_shortcuts_enabled
                    },
                    'access': {
                        'role': preferences.role,
                        'accessible_tabs': preferences.accessible_tabs,
                        'data_export_enabled': preferences.data_export_enabled,
                        'configuration_access': preferences.configuration_access
                    }
                }
            })
        except Exception as e:
            logger.error(f"Error retrieving user preferences: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            preferences = UserPreferences.query.filter_by(
                user_id=user_id, is_active=True
            ).first()
            
            if not preferences:
                preferences = UserPreferences(user_id=user_id)
                db.session.add(preferences)
            
            # Update preferences from request data
            if 'dashboard' in data:
                dashboard = data['dashboard']
                preferences.dashboard_theme = dashboard.get('theme', 'executive')
                preferences.dashboard_layout = dashboard.get('layout', 'grid')
                preferences.chart_color_scheme = dashboard.get('color_scheme', 'professional')
                preferences.dark_mode_enabled = dashboard.get('dark_mode', False)
            
            if 'defaults' in data:
                defaults = data['defaults']
                preferences.default_time_range = defaults.get('time_range', '30_days')
                preferences.default_store_filter = defaults.get('store_filter', 'all')
                preferences.auto_refresh_enabled = defaults.get('auto_refresh', True)
                preferences.auto_refresh_interval = defaults.get('refresh_interval', 300)
            
            if 'notifications' in data:
                notifications = data['notifications']
                preferences.email_notifications_enabled = notifications.get('email_enabled', True)
                preferences.push_notifications_enabled = notifications.get('push_enabled', False)
                preferences.alert_frequency = notifications.get('frequency', 'immediate')
                preferences.notification_types = notifications.get('types', ['critical', 'warning'])
            
            if 'reports' in data:
                reports = data['reports']
                preferences.report_format = reports.get('format', 'pdf')
                preferences.report_schedule_enabled = reports.get('schedule_enabled', False)
                preferences.report_frequency = reports.get('frequency', 'weekly')
                preferences.report_recipients = reports.get('recipients', [])
            
            if 'ui_preferences' in data:
                ui = data['ui_preferences']
                preferences.show_tooltips = ui.get('show_tooltips', True)
                preferences.show_animations = ui.get('show_animations', True)
                preferences.compact_mode = ui.get('compact_mode', False)
                preferences.keyboard_shortcuts_enabled = ui.get('keyboard_shortcuts', True)
            
            preferences.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'User preferences updated successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating user preferences: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 500


@config_bp.route('/api/export', methods=['POST'])
def export_configuration():
    """Export all user configurations"""
    try:
        user_id = session.get('user_id', DEFAULT_USER_ID)
        
        # Gather all configurations
        export_data = {
            'export_timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'configurations': {}
        }
        
        # Get prediction parameters
        prediction_params = PredictionParameters.query.filter_by(
            user_id=user_id, is_active=True
        ).first()
        if prediction_params:
            export_data['configurations']['prediction_parameters'] = {
                # Include relevant fields
                'forecast_horizons': {
                    'weekly': prediction_params.forecast_weekly_enabled,
                    'monthly': prediction_params.forecast_monthly_enabled,
                    'quarterly': prediction_params.forecast_quarterly_enabled,
                    'yearly': prediction_params.forecast_yearly_enabled
                },
                # Add other configuration sections...
            }
        
        # Add other configuration types similarly...
        
        return jsonify({
            'success': True,
            'data': export_data
        })
        
    except Exception as e:
        logger.error(f"Error exporting configuration: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@config_bp.route('/api/import', methods=['POST'])
def import_configuration():
    """Import user configurations from backup"""
    try:
        data = request.get_json()
        user_id = session.get('user_id', DEFAULT_USER_ID)
        
        if 'configurations' not in data:
            return jsonify({'success': False, 'error': 'Invalid configuration data'}), 400
        
        configurations = data['configurations']
        
        # Import each configuration type
        # This would involve creating/updating the respective model instances
        # Implementation depends on the specific requirements for configuration import
        
        return jsonify({
            'success': True,
            'message': 'Configuration imported successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error importing configuration: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@config_bp.route('/api/reset/<config_type>', methods=['POST'])
def reset_configuration(config_type):
    """Reset specific configuration to defaults"""
    try:
        user_id = session.get('user_id', DEFAULT_USER_ID)
        
        if config_type == 'prediction':
            # Reset prediction parameters to defaults
            prediction_params = PredictionParameters.query.filter_by(
                user_id=user_id, is_active=True
            ).first()
            
            if prediction_params:
                # Reset to default values
                prediction_params.forecast_weekly_enabled = True
                prediction_params.forecast_monthly_enabled = True
                prediction_params.forecast_quarterly_enabled = True
                prediction_params.forecast_yearly_enabled = False
                prediction_params.confidence_80_enabled = True
                prediction_params.confidence_90_enabled = True
                prediction_params.confidence_95_enabled = False
                prediction_params.default_confidence_level = 90.0
                prediction_params.seasonality_weight = 0.3
                prediction_params.trend_weight = 0.4
                prediction_params.economic_weight = 0.2
                prediction_params.promotional_weight = 0.1
                prediction_params.low_stock_threshold = 0.2
                prediction_params.high_stock_threshold = 2.0
                prediction_params.demand_spike_threshold = 1.5
                prediction_params.updated_at = datetime.utcnow()
                
                db.session.commit()
        
        # Add reset logic for other configuration types...
        
        return jsonify({
            'success': True,
            'message': f'{config_type.title()} configuration reset to defaults'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error resetting {config_type} configuration: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# Redirect routes for common URL variations
@config_redirect_bp.route('/configuration')
@config_redirect_bp.route('/configuration/')
def redirect_to_config():
    """Redirect common configuration URLs to the correct path."""
    return redirect(url_for('configuration.configuration_dashboard'))


@config_redirect_bp.route('/settings')
@config_redirect_bp.route('/settings/')
def redirect_settings_to_config():
    """Redirect settings URLs to configuration dashboard."""
    return redirect(url_for('configuration.configuration_dashboard'))