# app/models/config_models.py
# User Configuration System Models
# Version: 2025-08-29 - Fortune 500 Configuration Management

from app import db
from datetime import datetime
import json
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, JSON


class UserConfiguration(db.Model):
    """Main user configuration table for system-wide settings"""
    __tablename__ = 'user_configurations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False, default='default_user')
    config_type = db.Column(db.String(50), nullable=False)  # prediction, correlation, bi, integration, preferences
    config_name = db.Column(db.String(100), nullable=False)
    config_data = db.Column(db.JSON, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'config_type', 'config_name'),
    )


class PredictionParameters(db.Model):
    """Prediction parameters configuration for predictive analytics"""
    __tablename__ = 'prediction_parameters'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False, default='default_user')
    parameter_set_name = db.Column(db.String(100), nullable=False, default='default')
    
    # Forecast Horizons
    forecast_weekly_enabled = db.Column(db.Boolean, default=True)
    forecast_monthly_enabled = db.Column(db.Boolean, default=True)
    forecast_quarterly_enabled = db.Column(db.Boolean, default=True)
    forecast_yearly_enabled = db.Column(db.Boolean, default=False)
    
    # Confidence Intervals
    confidence_80_enabled = db.Column(db.Boolean, default=True)
    confidence_90_enabled = db.Column(db.Boolean, default=True)
    confidence_95_enabled = db.Column(db.Boolean, default=False)
    default_confidence_level = db.Column(db.Float, default=90.0)
    
    # External Factor Weights
    seasonality_weight = db.Column(db.Float, default=0.3)
    trend_weight = db.Column(db.Float, default=0.4)
    economic_weight = db.Column(db.Float, default=0.2)
    promotional_weight = db.Column(db.Float, default=0.1)
    
    # Alert Thresholds
    low_stock_threshold = db.Column(db.Float, default=0.2)  # 20% of avg inventory
    high_stock_threshold = db.Column(db.Float, default=2.0)  # 200% of avg inventory
    demand_spike_threshold = db.Column(db.Float, default=1.5)  # 150% of avg demand
    
    # Store-specific settings
    store_specific_enabled = db.Column(db.Boolean, default=True)
    store_mappings = db.Column(db.JSON, default={})
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'parameter_set_name'),
    )


class CorrelationSettings(db.Model):
    """Correlation analysis configuration settings"""
    __tablename__ = 'correlation_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False, default='default_user')
    setting_name = db.Column(db.String(100), nullable=False, default='default')
    
    # Minimum correlation thresholds
    min_correlation_weak = db.Column(db.Float, default=0.3)
    min_correlation_moderate = db.Column(db.Float, default=0.5)
    min_correlation_strong = db.Column(db.Float, default=0.7)
    
    # Statistical significance levels
    p_value_threshold = db.Column(db.Float, default=0.05)
    confidence_level = db.Column(db.Float, default=0.95)
    
    # Lag periods for time-series analysis
    max_lag_periods = db.Column(db.Integer, default=12)
    min_lag_periods = db.Column(db.Integer, default=1)
    default_lag_period = db.Column(db.Integer, default=3)
    
    # Factor selection preferences
    economic_factors_enabled = db.Column(db.Boolean, default=True)
    seasonal_factors_enabled = db.Column(db.Boolean, default=True)
    promotional_factors_enabled = db.Column(db.Boolean, default=True)
    weather_factors_enabled = db.Column(db.Boolean, default=False)
    
    # Analysis preferences
    auto_correlation_enabled = db.Column(db.Boolean, default=True)
    cross_correlation_enabled = db.Column(db.Boolean, default=True)
    partial_correlation_enabled = db.Column(db.Boolean, default=False)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'setting_name'),
    )


class BusinessIntelligenceConfig(db.Model):
    """Business Intelligence configuration for KPIs and targets"""
    __tablename__ = 'business_intelligence_config'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False, default='default_user')
    config_name = db.Column(db.String(100), nullable=False, default='default')
    
    # KPI targets and goals
    revenue_target_monthly = db.Column(db.Float, default=100000.0)
    revenue_target_quarterly = db.Column(db.Float, default=300000.0)
    revenue_target_yearly = db.Column(db.Float, default=1200000.0)
    
    inventory_turnover_target = db.Column(db.Float, default=6.0)
    profit_margin_target = db.Column(db.Float, default=0.25)
    customer_satisfaction_target = db.Column(db.Float, default=0.85)
    
    # Performance benchmarks
    benchmark_industry_avg_enabled = db.Column(db.Boolean, default=True)
    benchmark_historical_enabled = db.Column(db.Boolean, default=True)
    benchmark_competitor_enabled = db.Column(db.Boolean, default=False)
    
    # ROI calculation parameters
    roi_calculation_period = db.Column(db.String(20), default='quarterly')  # monthly, quarterly, yearly
    roi_include_overhead = db.Column(db.Boolean, default=True)
    roi_include_labor_costs = db.Column(db.Boolean, default=True)
    roi_discount_rate = db.Column(db.Float, default=0.08)
    
    # Resale recommendation criteria
    resale_min_profit_margin = db.Column(db.Float, default=0.15)
    resale_max_age_months = db.Column(db.Integer, default=24)
    resale_condition_threshold = db.Column(db.Float, default=7.0)  # 1-10 scale
    resale_demand_threshold = db.Column(db.Float, default=0.3)
    
    # Alert thresholds
    performance_alert_threshold = db.Column(db.Float, default=0.8)  # 80% of target
    critical_alert_threshold = db.Column(db.Float, default=0.6)  # 60% of target
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'config_name'),
    )


class DataIntegrationSettings(db.Model):
    """Data integration settings for CSV imports and APIs"""
    __tablename__ = 'data_integration_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False, default='default_user')
    setting_name = db.Column(db.String(100), nullable=False, default='default')
    
    # CSV import schedules and automation
    csv_auto_import_enabled = db.Column(db.Boolean, default=False)
    csv_import_frequency = db.Column(db.String(20), default='daily')  # hourly, daily, weekly
    csv_import_time = db.Column(db.String(8), default='02:00:00')  # HH:MM:SS format
    csv_backup_enabled = db.Column(db.Boolean, default=True)
    csv_validation_strict = db.Column(db.Boolean, default=True)
    
    # External API configurations
    api_timeout_seconds = db.Column(db.Integer, default=30)
    api_retry_attempts = db.Column(db.Integer, default=3)
    api_rate_limit_enabled = db.Column(db.Boolean, default=True)
    api_rate_limit_requests = db.Column(db.Integer, default=100)
    api_rate_limit_window = db.Column(db.Integer, default=3600)  # seconds
    
    # Data refresh intervals
    real_time_refresh_enabled = db.Column(db.Boolean, default=False)
    refresh_interval_minutes = db.Column(db.Integer, default=15)
    background_refresh_enabled = db.Column(db.Boolean, default=True)
    
    # Quality check parameters
    data_quality_checks_enabled = db.Column(db.Boolean, default=True)
    missing_data_threshold = db.Column(db.Float, default=0.1)  # 10% max missing data
    outlier_detection_enabled = db.Column(db.Boolean, default=True)
    outlier_detection_method = db.Column(db.String(20), default='iqr')  # iqr, zscore, isolation
    
    # File processing settings
    max_file_size_mb = db.Column(db.Integer, default=50)
    supported_formats = db.Column(db.JSON, default=['csv', 'xlsx', 'json'])
    archive_processed_files = db.Column(db.Boolean, default=True)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'setting_name'),
    )


class UserPreferences(db.Model):
    """User interface preferences and personalization"""
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False, default='default_user')
    preference_name = db.Column(db.String(100), nullable=False, default='default')
    
    # Dashboard layouts and themes
    dashboard_theme = db.Column(db.String(20), default='executive')  # executive, minimal, detailed
    dashboard_layout = db.Column(db.String(20), default='grid')  # grid, list, cards
    chart_color_scheme = db.Column(db.String(20), default='professional')
    dark_mode_enabled = db.Column(db.Boolean, default=False)
    
    # Default views and filters
    default_time_range = db.Column(db.String(20), default='30_days')
    default_store_filter = db.Column(db.String(50), default='all')
    auto_refresh_enabled = db.Column(db.Boolean, default=True)
    auto_refresh_interval = db.Column(db.Integer, default=300)  # seconds
    
    # Notification preferences
    email_notifications_enabled = db.Column(db.Boolean, default=True)
    push_notifications_enabled = db.Column(db.Boolean, default=False)
    alert_frequency = db.Column(db.String(20), default='immediate')  # immediate, daily, weekly
    notification_types = db.Column(db.JSON, default=['critical', 'warning'])
    
    # Report formats and scheduling
    report_format = db.Column(db.String(10), default='pdf')  # pdf, excel, csv
    report_schedule_enabled = db.Column(db.Boolean, default=False)
    report_frequency = db.Column(db.String(20), default='weekly')
    report_recipients = db.Column(db.JSON, default=[])
    
    # Access permissions and roles
    role = db.Column(db.String(20), default='user')  # admin, manager, user, viewer
    accessible_tabs = db.Column(db.JSON, default=['tab1', 'tab2', 'tab3', 'tab4', 'tab5'])
    data_export_enabled = db.Column(db.Boolean, default=True)
    configuration_access = db.Column(db.Boolean, default=False)
    
    # UI/UX preferences
    show_tooltips = db.Column(db.Boolean, default=True)
    show_animations = db.Column(db.Boolean, default=True)
    compact_mode = db.Column(db.Boolean, default=False)
    keyboard_shortcuts_enabled = db.Column(db.Boolean, default=True)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'preference_name'),
    )


class ConfigurationAudit(db.Model):
    """Audit trail for configuration changes"""
    __tablename__ = 'configuration_audit'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False)
    config_type = db.Column(db.String(50), nullable=False)
    config_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(20), nullable=False)  # create, update, delete, activate, deactivate
    old_values = db.Column(db.JSON)
    new_values = db.Column(db.JSON)
    change_reason = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# Helper functions for configuration management
def get_user_config(user_id, config_type, config_name='default'):
    """Get user configuration by type and name"""
    config = UserConfiguration.query.filter_by(
        user_id=user_id,
        config_type=config_type,
        config_name=config_name,
        is_active=True
    ).first()
    return config.config_data if config else None


def set_user_config(user_id, config_type, config_name, config_data):
    """Set or update user configuration"""
    config = UserConfiguration.query.filter_by(
        user_id=user_id,
        config_type=config_type,
        config_name=config_name
    ).first()
    
    if config:
        config.config_data = config_data
        config.updated_at = datetime.utcnow()
    else:
        config = UserConfiguration(
            user_id=user_id,
            config_type=config_type,
            config_name=config_name,
            config_data=config_data
        )
        db.session.add(config)
    
    db.session.commit()
    return config


def get_default_prediction_params():
    """Get default prediction parameters"""
    return {
        'forecast_horizons': ['weekly', 'monthly', 'quarterly'],
        'confidence_levels': [80, 90, 95],
        'default_confidence': 90,
        'external_factors': {
            'seasonality': 0.3,
            'trend': 0.4,
            'economic': 0.2,
            'promotional': 0.1
        },
        'thresholds': {
            'low_stock': 0.2,
            'high_stock': 2.0,
            'demand_spike': 1.5
        }
    }


def get_default_correlation_settings():
    """Get default correlation analysis settings"""
    return {
        'thresholds': {
            'weak': 0.3,
            'moderate': 0.5,
            'strong': 0.7
        },
        'statistical': {
            'p_value': 0.05,
            'confidence': 0.95
        },
        'lag_periods': {
            'min': 1,
            'max': 12,
            'default': 3
        },
        'factors': {
            'economic': True,
            'seasonal': True,
            'promotional': True,
            'weather': False
        }
    }