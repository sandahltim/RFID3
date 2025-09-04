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


class LaborCostConfiguration(db.Model):
    """Labor cost analysis configuration with store-specific thresholds"""
    __tablename__ = 'labor_cost_configuration'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False, default='default_user')
    config_name = db.Column(db.String(100), nullable=False, default='default')
    
    # Global labor cost thresholds (defaults for all stores)
    high_labor_cost_threshold = db.Column(db.Float, default=35.0)  # 35% - stores flagged as high cost
    labor_cost_warning_level = db.Column(db.Float, default=30.0)   # 30% - warning before high threshold  
    target_labor_cost_ratio = db.Column(db.Float, default=25.0)    # 25% - target labor cost percentage
    efficiency_baseline = db.Column(db.Float, default=100.0)       # 100 - efficiency calculation baseline
    
    # Store-specific threshold overrides (JSON format)
    # Example: {"3607": {"high_threshold": 40.0, "target": 30.0}, "6800": {"high_threshold": 32.0}}
    store_specific_thresholds = db.Column(db.JSON, default={})
    
    # Performance analysis settings
    minimum_hours_for_analysis = db.Column(db.Float, default=1.0)  # Minimum hours to include in analysis
    labor_efficiency_weight = db.Column(db.Float, default=0.6)     # Weight for efficiency vs cost in scoring
    cost_control_weight = db.Column(db.Float, default=0.4)         # Weight for cost control in scoring
    
    # Processing and performance settings
    batch_processing_size = db.Column(db.Integer, default=100)     # Batch size (max 200 per user requirement)
    progress_checkpoint_interval = db.Column(db.Integer, default=500)  # Progress reporting interval
    query_timeout_seconds = db.Column(db.Integer, default=30)      # Query timeout
    
    # Alert and notification settings
    enable_high_cost_alerts = db.Column(db.Boolean, default=True)
    enable_trend_alerts = db.Column(db.Boolean, default=True)
    alert_frequency = db.Column(db.String(20), default='weekly')   # daily, weekly, monthly
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'config_name'),
    )
    
    def get_store_threshold(self, store_code: str, threshold_type: str = 'high_threshold'):
        """
        Get store-specific threshold or fall back to global default.
        
        Args:
            store_code: Store code to get threshold for
            threshold_type: 'high_threshold', 'warning_level', or 'target'
            
        Returns:
            Threshold value for the store
        """
        store_overrides = self.store_specific_thresholds or {}
        
        if store_code in store_overrides:
            store_config = store_overrides[store_code]
            if threshold_type == 'high_threshold' and 'high_threshold' in store_config:
                return store_config['high_threshold']
            elif threshold_type == 'warning_level' and 'warning_level' in store_config:
                return store_config['warning_level'] 
            elif threshold_type == 'target' and 'target' in store_config:
                return store_config['target']
        
        # Fall back to global defaults
        if threshold_type == 'high_threshold':
            return self.high_labor_cost_threshold
        elif threshold_type == 'warning_level':
            return self.labor_cost_warning_level
        elif threshold_type == 'target':
            return self.target_labor_cost_ratio
        else:
            return self.high_labor_cost_threshold
    
    def get_safe_batch_size(self):
        """Get batch size capped at maximum of 200 per user requirement."""
        return min(self.batch_processing_size or 100, 200)


def get_default_labor_cost_config():
    """Get default labor cost configuration settings"""
    return {
        'global_thresholds': {
            'high_cost_threshold': 35.0,      # 35% - flag as high cost
            'warning_level': 30.0,            # 30% - warning level
            'target_ratio': 25.0,             # 25% - target labor cost
            'efficiency_baseline': 100.0      # 100 - baseline for efficiency calc
        },
        'store_specific': {
            # Example store-specific overrides (empty by default)
            # '3607': {'high_threshold': 40.0, 'target': 30.0},  # Wayzata - higher threshold
            # '6800': {'high_threshold': 32.0, 'target': 24.0}   # Brooklyn Park - lower threshold  
        },
        'analysis_settings': {
            'minimum_hours': 1.0,             # Minimum hours for analysis
            'efficiency_weight': 0.6,         # 60% efficiency, 40% cost control
            'cost_weight': 0.4
        },
        'performance_settings': {
            'batch_size': 100,                # Max 200 per user requirement
            'checkpoint_interval': 500,
            'query_timeout': 30
        },
        'alerts': {
            'high_cost_enabled': True,
            'trend_alerts_enabled': True, 
            'frequency': 'weekly'
        }
    }


class BusinessAnalyticsConfiguration(db.Model):
    """Business analytics thresholds and performance evaluation configuration"""
    __tablename__ = 'business_analytics_configuration'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False, default='default_user')
    config_name = db.Column(db.String(100), nullable=False, default='default')
    
    # Equipment Performance Thresholds
    equipment_underperformer_threshold = db.Column(db.Float, default=50.0)      # $50 YTD turnover threshold
    low_turnover_threshold = db.Column(db.Float, default=25.0)                  # $25 low turnover threshold
    high_value_threshold = db.Column(db.Float, default=500.0)                   # $500 high value threshold
    low_usage_threshold = db.Column(db.Float, default=100.0)                    # $100 low usage threshold
    resale_priority_threshold = db.Column(db.Float, default=10.0)               # >10 high priority resale
    
    # AR Aging Thresholds (percentages)
    ar_aging_low_threshold = db.Column(db.Float, default=5.0)                   # <5% considered low AR aging
    ar_aging_medium_threshold = db.Column(db.Float, default=15.0)               # <15% considered medium AR aging
    # >15% is automatically high AR aging
    
    # Revenue Risk Analysis
    revenue_concentration_risk_threshold = db.Column(db.Float, default=0.4)     # 40% concentration risk threshold
    declining_trend_threshold = db.Column(db.Float, default=-0.1)               # -10% declining trend threshold
    
    # Data Quality and Analysis Requirements
    minimum_data_points_correlation = db.Column(db.Integer, default=10)         # Minimum data points for valid analysis
    confidence_threshold = db.Column(db.Float, default=0.95)                    # Statistical confidence level
    
    # Store-specific business analytics overrides (JSON format)
    # Example: {"3607": {"underperformer_threshold": 75.0}, "6800": {"high_value_threshold": 750.0}}
    store_specific_thresholds = db.Column(db.JSON, default={})
    
    # Alert and reporting settings
    enable_underperformance_alerts = db.Column(db.Boolean, default=True)
    enable_high_value_alerts = db.Column(db.Boolean, default=True)
    enable_ar_aging_alerts = db.Column(db.Boolean, default=True)
    enable_concentration_risk_alerts = db.Column(db.Boolean, default=True)
    alert_frequency = db.Column(db.String(20), default='weekly')               # daily, weekly, monthly
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'config_name'),
    )
    
    def get_store_threshold(self, store_code: str, threshold_type: str):
        """
        Get store-specific business analytics threshold or fall back to global default.
        
        Args:
            store_code: Store code to get threshold for
            threshold_type: Type of threshold (e.g., 'underperformer_threshold', 'high_value_threshold')
            
        Returns:
            Threshold value for the store
        """
        store_overrides = self.store_specific_thresholds or {}
        
        if store_code in store_overrides and threshold_type in store_overrides[store_code]:
            return store_overrides[store_code][threshold_type]
        
        # Fall back to global defaults
        threshold_map = {
            'underperformer_threshold': self.equipment_underperformer_threshold,
            'low_turnover_threshold': self.low_turnover_threshold,
            'high_value_threshold': self.high_value_threshold,
            'low_usage_threshold': self.low_usage_threshold,
            'resale_priority_threshold': self.resale_priority_threshold,
            'ar_low_threshold': self.ar_aging_low_threshold,
            'ar_medium_threshold': self.ar_aging_medium_threshold,
            'concentration_risk_threshold': self.revenue_concentration_risk_threshold,
            'declining_trend_threshold': self.declining_trend_threshold
        }
        
        return threshold_map.get(threshold_type, 50.0)  # Safe fallback


def get_default_business_analytics_config():
    """Get default business analytics configuration settings"""
    return {
        'equipment_thresholds': {
            'underperformer_ytd': 50.0,           # $50 YTD turnover threshold
            'low_turnover': 25.0,                 # $25 low turnover threshold
            'high_value': 500.0,                  # $500 high value threshold
            'low_usage': 100.0,                   # $100 low usage threshold
            'resale_priority': 10.0               # >10 high priority for resale
        },
        'financial_risk': {
            'ar_aging_low': 5.0,                  # <5% low AR aging
            'ar_aging_medium': 15.0,              # <15% medium AR aging (>15% is high)
            'concentration_risk': 0.4,            # 40% revenue concentration risk
            'declining_trend': -0.1               # -10% declining trend threshold
        },
        'analysis_quality': {
            'min_data_points': 10,                # Minimum data points for correlations
            'confidence_level': 0.95              # Statistical confidence threshold
        },
        'store_specific': {
            # Example store-specific overrides (empty by default)
            # '3607': {'underperformer_threshold': 75.0},    # Wayzata - higher threshold
            # '6800': {'high_value_threshold': 750.0}        # Brooklyn Park - higher value threshold
        },
        'alerts': {
            'underperformance_enabled': True,
            'high_value_enabled': True,
            'ar_aging_enabled': True,
            'concentration_risk_enabled': True,
            'frequency': 'weekly'
        }
    }


class ExecutiveDashboardConfiguration(db.Model):
    """Executive dashboard health scoring and display configuration"""
    __tablename__ = 'executive_dashboard_configuration'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False, default='default_user')
    config_name = db.Column(db.String(100), nullable=False, default='default')
    
    # Health Score Base Parameters
    base_health_score = db.Column(db.Float, default=75.0)                       # Starting health score (0-100)
    min_health_score = db.Column(db.Float, default=0.0)                         # Minimum possible score
    max_health_score = db.Column(db.Float, default=100.0)                       # Maximum possible score
    
    # Revenue Trend Scoring Thresholds
    strong_positive_trend_threshold = db.Column(db.Float, default=5.0)          # >5% strong upward trend
    strong_positive_trend_points = db.Column(db.Integer, default=15)            # +15 points bonus
    weak_positive_trend_points = db.Column(db.Integer, default=5)               # +5 points bonus (0 < trend < 5)
    strong_negative_trend_threshold = db.Column(db.Float, default=-5.0)         # <-5% strong downward trend  
    strong_negative_trend_points = db.Column(db.Integer, default=-15)           # -15 points penalty
    weak_negative_trend_points = db.Column(db.Integer, default=-5)              # -5 points penalty (-5 < trend < 0)
    
    # Growth Rate Scoring Thresholds  
    strong_growth_threshold = db.Column(db.Float, default=10.0)                 # >10% strong growth
    strong_growth_points = db.Column(db.Integer, default=10)                    # +10 points bonus
    weak_growth_points = db.Column(db.Integer, default=5)                       # +5 points bonus (0 < growth < 10)
    strong_decline_threshold = db.Column(db.Float, default=-10.0)               # <-10% strong decline
    strong_decline_points = db.Column(db.Integer, default=-15)                  # -15 points penalty
    weak_decline_points = db.Column(db.Integer, default=-5)                     # -5 points penalty (-10 < growth < 0)
    
    # Revenue-Based Health Score Thresholds (from tab7.py health scoring logic)
    revenue_tier_1_threshold = db.Column(db.Float, default=100000.0)            # Top tier revenue threshold
    revenue_tier_1_points = db.Column(db.Integer, default=25)                   # +25 points for top tier
    revenue_tier_2_threshold = db.Column(db.Float, default=75000.0)             # Second tier revenue threshold  
    revenue_tier_2_points = db.Column(db.Integer, default=20)                   # +20 points for second tier
    revenue_tier_3_threshold = db.Column(db.Float, default=50000.0)             # Third tier revenue threshold
    revenue_tier_3_points = db.Column(db.Integer, default=15)                   # +15 points for third tier
    revenue_tier_4_points = db.Column(db.Integer, default=10)                   # +10 points for below tier 3
    
    # YoY Growth-Based Health Score Thresholds (from tab7.py YoY scoring logic)  
    yoy_excellent_threshold = db.Column(db.Float, default=10.0)                 # >10% YoY growth (excellent)
    yoy_excellent_points = db.Column(db.Integer, default=25)                    # +25 points for excellent growth
    yoy_good_threshold = db.Column(db.Float, default=5.0)                       # 5-10% YoY growth (good) 
    yoy_good_points = db.Column(db.Integer, default=15)                         # +15 points for good growth
    yoy_fair_threshold = db.Column(db.Float, default=0.0)                       # 0-5% YoY growth (fair)
    yoy_fair_points = db.Column(db.Integer, default=10)                         # +10 points for fair growth
    yoy_poor_points = db.Column(db.Integer, default=5)                          # +5 points for negative growth
    
    # Margin-Based Health Score Thresholds (from tab7.py margin scoring logic)
    margin_excellent_threshold = db.Column(db.Float, default=15.0)              # >15% margin (excellent)
    margin_excellent_points = db.Column(db.Integer, default=25)                 # +25 points for excellent margin
    margin_good_threshold = db.Column(db.Float, default=10.0)                   # 10-15% margin (good)
    margin_good_points = db.Column(db.Integer, default=20)                      # +20 points for good margin  
    margin_fair_threshold = db.Column(db.Float, default=5.0)                    # 5-10% margin (fair)
    margin_fair_points = db.Column(db.Integer, default=15)                      # +15 points for fair margin
    margin_poor_points = db.Column(db.Integer, default=10)                      # +10 points for poor margin
    
    # Utilization-Based Health Score Thresholds (from tab7.py utilization scoring logic)
    utilization_excellent_threshold = db.Column(db.Float, default=85.0)         # >85% utilization (excellent) 
    utilization_excellent_points = db.Column(db.Integer, default=25)            # +25 points for excellent utilization
    utilization_good_threshold = db.Column(db.Float, default=75.0)              # 75-85% utilization (good)
    utilization_good_points = db.Column(db.Integer, default=20)                 # +20 points for good utilization
    utilization_fair_threshold = db.Column(db.Float, default=65.0)              # 65-75% utilization (fair)
    utilization_fair_points = db.Column(db.Integer, default=15)                 # +15 points for fair utilization
    utilization_poor_threshold = db.Column(db.Float, default=50.0)              # 50-65% utilization (poor)
    utilization_poor_points = db.Column(db.Integer, default=10)                 # +10 points for poor utilization
    
    # Forecasting Default Parameters
    default_forecast_horizon_weeks = db.Column(db.Integer, default=12)          # Default 12-week forecast
    default_confidence_level = db.Column(db.Float, default=0.95)                # Default 95% confidence
    min_forecast_horizon = db.Column(db.Integer, default=1)                     # Minimum 1 week
    max_forecast_horizon = db.Column(db.Integer, default=52)                    # Maximum 52 weeks
    
    # Analysis Period Parameters
    default_analysis_period_weeks = db.Column(db.Integer, default=26)           # Default 26-week analysis period
    
    # RFID Coverage Data Parameters  
    rfid_coverage_percentage = db.Column(db.Float, default=1.78)                # Current RFID correlation coverage %
    rfid_correlated_items = db.Column(db.Integer, default=290)                  # Number of RFID-correlated items
    total_equipment_items = db.Column(db.Integer, default=16259)                # Total equipment items in system
    
    # Store-specific dashboard overrides (JSON format)
    # Example: {"3607": {"base_health_score": 80.0}, "6800": {"strong_growth_threshold": 8.0}}
    store_specific_thresholds = db.Column(db.JSON, default={})
    
    # Display and Alert Settings
    enable_health_score_alerts = db.Column(db.Boolean, default=True)
    enable_trend_alerts = db.Column(db.Boolean, default=True) 
    enable_growth_alerts = db.Column(db.Boolean, default=True)
    alert_frequency = db.Column(db.String(20), default='weekly')                # daily, weekly, monthly
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'config_name'),
    )
    
    def get_store_threshold(self, store_code: str, threshold_type: str):
        """
        Get store-specific executive dashboard threshold or fall back to global default.
        
        Args:
            store_code (str): Store identifier (e.g., '3607', '6800')
            threshold_type (str): Type of threshold to retrieve
            
        Returns:
            float: Configured threshold value for the store or global default
        """
        # Check for store-specific override
        if self.store_specific_thresholds and store_code in self.store_specific_thresholds:
            store_config = self.store_specific_thresholds[store_code]
            if threshold_type in store_config:
                return store_config[threshold_type]
        
        # Fall back to global configuration
        threshold_map = {
            'base_health_score': self.base_health_score,
            'strong_positive_trend_threshold': self.strong_positive_trend_threshold,
            'strong_positive_trend_points': self.strong_positive_trend_points,
            'weak_positive_trend_points': self.weak_positive_trend_points,
            'strong_negative_trend_threshold': self.strong_negative_trend_threshold,
            'strong_negative_trend_points': self.strong_negative_trend_points,
            'weak_negative_trend_points': self.weak_negative_trend_points,
            'strong_growth_threshold': self.strong_growth_threshold,
            'strong_growth_points': self.strong_growth_points,
            'weak_growth_points': self.weak_growth_points,
            'strong_decline_threshold': self.strong_decline_threshold,
            'strong_decline_points': self.strong_decline_points,
            'weak_decline_points': self.weak_decline_points,
            # Revenue-based health scoring thresholds
            'revenue_tier_1_threshold': self.revenue_tier_1_threshold,
            'revenue_tier_1_points': self.revenue_tier_1_points,
            'revenue_tier_2_threshold': self.revenue_tier_2_threshold,
            'revenue_tier_2_points': self.revenue_tier_2_points,
            'revenue_tier_3_threshold': self.revenue_tier_3_threshold,
            'revenue_tier_3_points': self.revenue_tier_3_points,
            'revenue_tier_4_points': self.revenue_tier_4_points,
            # YoY growth-based health scoring thresholds  
            'yoy_excellent_threshold': self.yoy_excellent_threshold,
            'yoy_excellent_points': self.yoy_excellent_points,
            'yoy_good_threshold': self.yoy_good_threshold,
            'yoy_good_points': self.yoy_good_points,
            'yoy_fair_threshold': self.yoy_fair_threshold,
            'yoy_fair_points': self.yoy_fair_points,
            'yoy_poor_points': self.yoy_poor_points,
            # Margin-based health scoring thresholds
            'margin_excellent_threshold': self.margin_excellent_threshold,
            'margin_excellent_points': self.margin_excellent_points,
            'margin_good_threshold': self.margin_good_threshold,
            'margin_good_points': self.margin_good_points,
            'margin_fair_threshold': self.margin_fair_threshold,
            'margin_fair_points': self.margin_fair_points,
            'margin_poor_points': self.margin_poor_points,
            # Utilization-based health scoring thresholds
            'utilization_excellent_threshold': self.utilization_excellent_threshold,
            'utilization_excellent_points': self.utilization_excellent_points,
            'utilization_good_threshold': self.utilization_good_threshold,
            'utilization_good_points': self.utilization_good_points,
            'utilization_fair_threshold': self.utilization_fair_threshold,
            'utilization_fair_points': self.utilization_fair_points,
            'utilization_poor_threshold': self.utilization_poor_threshold,
            'utilization_poor_points': self.utilization_poor_points,
            # Other configuration parameters
            'default_forecast_horizon_weeks': self.default_forecast_horizon_weeks,
            'default_confidence_level': self.default_confidence_level,
            'default_analysis_period_weeks': self.default_analysis_period_weeks,
            'rfid_coverage_percentage': self.rfid_coverage_percentage,
            'rfid_correlated_items': self.rfid_correlated_items,
            'total_equipment_items': self.total_equipment_items
        }
        
        return threshold_map.get(threshold_type, 75.0)  # Safe fallback to base health score


class ExecutiveInsightsConfiguration(db.Model):
    """Executive insights and anomaly detection configuration"""
    __tablename__ = 'executive_insights_configuration'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False, default='default_user')
    config_name = db.Column(db.String(100), nullable=False, default='default')
    
    # Z-Score Anomaly Detection Thresholds
    revenue_anomaly_threshold = db.Column(db.Float, default=2.0)               # Revenue anomaly Z-score threshold
    revenue_high_severity_threshold = db.Column(db.Float, default=3.0)         # High severity revenue Z-score
    contract_anomaly_threshold = db.Column(db.Float, default=1.8)              # Contract anomaly Z-score threshold
    contract_high_severity_threshold = db.Column(db.Float, default=2.5)        # High severity contract Z-score  
    margin_anomaly_threshold = db.Column(db.Float, default=2.0)                # Margin anomaly Z-score threshold
    margin_high_severity_threshold = db.Column(db.Float, default=3.0)          # High severity margin Z-score
    store_performance_anomaly_threshold = db.Column(db.Float, default=2.0)     # Store performance anomaly Z-score
    store_performance_high_severity_threshold = db.Column(db.Float, default=3.0) # High severity store Z-score
    
    # Weather Correlation Thresholds
    freezing_temperature_threshold = db.Column(db.Float, default=32.0)         # Freezing temp threshold (°F)
    extreme_heat_threshold = db.Column(db.Float, default=95.0)                 # Extreme heat threshold (°F)
    heavy_precipitation_threshold = db.Column(db.Float, default=1.0)           # Heavy precipitation threshold (inches)
    weather_temp_low_default = db.Column(db.Float, default=50.0)               # Default low temp for missing data
    weather_temp_high_default = db.Column(db.Float, default=70.0)              # Default high temp for missing data
    
    # Holiday & Event Correlation Parameters  
    holiday_correlation_window_days = db.Column(db.Integer, default=3)         # Days around holiday to consider
    close_correlation_strength = db.Column(db.Float, default=0.8)              # Correlation strength for close events (<=1 day)
    medium_correlation_strength = db.Column(db.Float, default=0.6)             # Correlation strength for medium events (>1 day)
    
    # Impact & Priority Assessment Thresholds
    high_impact_threshold = db.Column(db.Float, default=0.7)                   # High impact magnitude threshold
    critical_magnitude_threshold = db.Column(db.Float, default=0.8)            # Critical magnitude threshold
    medium_magnitude_threshold = db.Column(db.Float, default=0.5)              # Medium magnitude threshold  
    strong_correlation_threshold = db.Column(db.Float, default=0.7)            # Strong correlation threshold
    
    # Correlation Significance Counts (minimum required for significance)
    min_weather_correlations = db.Column(db.Integer, default=2)                # Minimum weather correlations for significance
    min_seasonal_correlations = db.Column(db.Integer, default=3)               # Minimum seasonal correlations for significance  
    min_holiday_correlations = db.Column(db.Integer, default=2)                # Minimum holiday correlations for significance
    
    # Anomaly Counting & Alert Thresholds
    high_anomaly_count_threshold = db.Column(db.Integer, default=5)            # High anomaly count threshold
    medium_anomaly_count_threshold = db.Column(db.Integer, default=2)          # Medium anomaly count threshold
    high_severity_alert_threshold = db.Column(db.Integer, default=2)           # High severity count alert threshold
    
    # Store-specific insights overrides (JSON format)
    # Example: {"3607": {"revenue_anomaly_threshold": 2.5}, "6800": {"high_impact_threshold": 0.8}}
    store_specific_thresholds = db.Column(db.JSON, default={})
    
    # Alert and Processing Settings
    enable_anomaly_detection = db.Column(db.Boolean, default=True)
    enable_weather_correlations = db.Column(db.Boolean, default=True)
    enable_holiday_correlations = db.Column(db.Boolean, default=True)
    enable_seasonal_analysis = db.Column(db.Boolean, default=True)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'config_name'),
    )
    
    def get_store_threshold(self, store_code: str, threshold_type: str):
        """
        Get store-specific executive insights threshold or fall back to global default.
        
        Args:
            store_code (str): Store identifier (e.g., '3607', '6800')
            threshold_type (str): Type of threshold to retrieve
            
        Returns:
            float/int: Configured threshold value for the store or global default
        """
        # Check for store-specific override
        if self.store_specific_thresholds and store_code in self.store_specific_thresholds:
            store_config = self.store_specific_thresholds[store_code]
            if threshold_type in store_config:
                return store_config[threshold_type]
        
        # Fall back to global configuration
        threshold_map = {
            # Z-Score thresholds
            'revenue_anomaly_threshold': self.revenue_anomaly_threshold,
            'revenue_high_severity_threshold': self.revenue_high_severity_threshold,
            'contract_anomaly_threshold': self.contract_anomaly_threshold,
            'contract_high_severity_threshold': self.contract_high_severity_threshold,
            'margin_anomaly_threshold': self.margin_anomaly_threshold,
            'margin_high_severity_threshold': self.margin_high_severity_threshold,
            'store_performance_anomaly_threshold': self.store_performance_anomaly_threshold,
            'store_performance_high_severity_threshold': self.store_performance_high_severity_threshold,
            # Weather thresholds
            'freezing_temperature_threshold': self.freezing_temperature_threshold,
            'extreme_heat_threshold': self.extreme_heat_threshold,
            'heavy_precipitation_threshold': self.heavy_precipitation_threshold,
            'weather_temp_low_default': self.weather_temp_low_default,
            'weather_temp_high_default': self.weather_temp_high_default,
            # Correlation parameters
            'holiday_correlation_window_days': self.holiday_correlation_window_days,
            'close_correlation_strength': self.close_correlation_strength,
            'medium_correlation_strength': self.medium_correlation_strength,
            # Impact assessment
            'high_impact_threshold': self.high_impact_threshold,
            'critical_magnitude_threshold': self.critical_magnitude_threshold,
            'medium_magnitude_threshold': self.medium_magnitude_threshold,
            'strong_correlation_threshold': self.strong_correlation_threshold,
            # Significance counts
            'min_weather_correlations': self.min_weather_correlations,
            'min_seasonal_correlations': self.min_seasonal_correlations,
            'min_holiday_correlations': self.min_holiday_correlations,
            # Alert thresholds
            'high_anomaly_count_threshold': self.high_anomaly_count_threshold,
            'medium_anomaly_count_threshold': self.medium_anomaly_count_threshold,
            'high_severity_alert_threshold': self.high_severity_alert_threshold
        }
        
        return threshold_map.get(threshold_type, 2.0)  # Safe fallback for Z-score thresholds


def get_default_executive_dashboard_config():
    """Get default executive dashboard configuration settings"""
    return {
        'health_scoring': {
            'base_score': 75.0,                          # Starting health score
            'strong_positive_trend_threshold': 5.0,      # >5% strong upward trend
            'strong_positive_trend_points': 15,          # +15 points bonus
            'weak_positive_trend_points': 5,             # +5 points bonus
            'strong_negative_trend_threshold': -5.0,     # <-5% strong downward trend
            'strong_negative_trend_points': -15,         # -15 points penalty
            'weak_negative_trend_points': -5,            # -5 points penalty
            'strong_growth_threshold': 10.0,             # >10% strong growth
            'strong_growth_points': 10,                  # +10 points bonus
            'weak_growth_points': 5,                     # +5 points bonus
            'strong_decline_threshold': -10.0,           # <-10% strong decline
            'strong_decline_points': -15,                # -15 points penalty
            'weak_decline_points': -5                    # -5 points penalty
        },
        'forecasting': {
            'default_horizon_weeks': 12,                 # Default 12-week forecast
            'default_confidence_level': 0.95,            # Default 95% confidence
            'min_horizon': 1,                            # Minimum 1 week
            'max_horizon': 52                            # Maximum 52 weeks
        },
        'analysis': {
            'default_period_weeks': 26                   # Default 26-week analysis period
        },
        'rfid_coverage': {
            'coverage_percentage': 1.78,                 # Current RFID correlation coverage %
            'correlated_items': 290,                     # Number of RFID-correlated items  
            'total_equipment_items': 16259               # Total equipment items in system
        },
        'alerts': {
            'enable_health_alerts': True,
            'enable_trend_alerts': True,
            'enable_growth_alerts': True,
            'frequency': 'weekly'
        }
    }


class PredictiveAnalyticsConfiguration(db.Model):
    """Predictive analytics forecasting configuration"""
    __tablename__ = 'predictive_analytics_configuration'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False, default='default_user')
    config_name = db.Column(db.String(100), nullable=False, default='default')
    
    # Forecast Horizon Parameters
    short_term_horizon_weeks = db.Column(db.Integer, default=4)                 # Short term: 4 weeks
    medium_term_horizon_weeks = db.Column(db.Integer, default=12)               # Medium term: 12 weeks (quarterly)
    long_term_horizon_weeks = db.Column(db.Integer, default=52)                 # Long term: 52 weeks (yearly)
    default_forecast_horizon = db.Column(db.Integer, default=12)                # Default horizon when not specified
    
    # Data Quality Requirements
    minimum_data_points_required = db.Column(db.Integer, default=10)            # Minimum records for reliable analysis
    query_limit_records = db.Column(db.Integer, default=100)                    # Default query record limit
    historical_data_limit_weeks = db.Column(db.Integer, default=52)             # Last year of data (LIMIT 52)
    
    # Analysis Quality Thresholds
    minimum_trend_confidence = db.Column(db.Float, default=0.7)                 # 70% confidence for trend analysis
    seasonal_analysis_periods = db.Column(db.Integer, default=12)               # 12 periods for seasonal analysis
    forecast_accuracy_threshold = db.Column(db.Float, default=0.8)              # 80% accuracy threshold
    
    # Store-specific predictive overrides (JSON format)
    # Example: {"3607": {"short_term_horizon_weeks": 6}, "6800": {"minimum_data_points_required": 15}}
    store_specific_thresholds = db.Column(db.JSON, default={})
    
    # Predictive Analytics Settings
    enable_seasonal_adjustment = db.Column(db.Boolean, default=True)
    enable_trend_analysis = db.Column(db.Boolean, default=True)
    enable_outlier_detection = db.Column(db.Boolean, default=True)
    forecasting_method = db.Column(db.String(50), default='auto')               # auto, linear, exponential, seasonal
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'config_name'),
    )
    
    def get_store_threshold(self, store_code: str, threshold_type: str):
        """
        Get store-specific predictive analytics threshold or fall back to global default.
        
        Args:
            store_code (str): Store identifier (e.g., '3607', '6800')
            threshold_type (str): Type of threshold to retrieve
            
        Returns:
            float/int: Configured threshold value for the store or global default
        """
        # Check for store-specific override
        if self.store_specific_thresholds and store_code in self.store_specific_thresholds:
            store_config = self.store_specific_thresholds[store_code]
            if threshold_type in store_config:
                return store_config[threshold_type]
        
        # Fall back to global configuration
        threshold_map = {
            'short_term_horizon_weeks': self.short_term_horizon_weeks,
            'medium_term_horizon_weeks': self.medium_term_horizon_weeks,
            'long_term_horizon_weeks': self.long_term_horizon_weeks,
            'default_forecast_horizon': self.default_forecast_horizon,
            'minimum_data_points_required': self.minimum_data_points_required,
            'query_limit_records': self.query_limit_records,
            'historical_data_limit_weeks': self.historical_data_limit_weeks,
            'minimum_trend_confidence': self.minimum_trend_confidence,
            'seasonal_analysis_periods': self.seasonal_analysis_periods,
            'forecast_accuracy_threshold': self.forecast_accuracy_threshold
        }
        
        return threshold_map.get(threshold_type, 12)  # Safe fallback to 12 weeks


def get_default_predictive_analytics_config():
    """Get default predictive analytics configuration settings"""
    return {
        'forecast_horizons': {
            'short_term_weeks': 4,                       # Short term forecasting horizon
            'medium_term_weeks': 12,                     # Medium term forecasting horizon (quarterly)
            'long_term_weeks': 52,                       # Long term forecasting horizon (yearly)
            'default_horizon_weeks': 12                  # Default when not specified
        },
        'data_quality': {
            'minimum_data_points': 10,                   # Minimum records for reliable analysis
            'query_limit_records': 100,                  # Default query record limit
            'historical_data_weeks': 52                  # Historical data lookback period
        },
        'analysis_quality': {
            'minimum_trend_confidence': 0.7,             # 70% confidence for trend analysis
            'seasonal_periods': 12,                      # Periods for seasonal analysis
            'forecast_accuracy_threshold': 0.8           # 80% accuracy threshold
        },
        'features': {
            'enable_seasonal_adjustment': True,
            'enable_trend_analysis': True,
            'enable_outlier_detection': True,
            'forecasting_method': 'auto'
        }
    }


class ManagerDashboardConfiguration(db.Model):
    """Manager dashboard configuration for store-specific analytics and alerts"""
    __tablename__ = 'manager_dashboard_configuration'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), nullable=False, default='default_user')
    config_name = db.Column(db.String(100), nullable=False, default='default')
    
    # Time Period Parameters
    recent_activity_period_days = db.Column(db.Integer, default=30)          # "Recent" activity definition (was days=30)
    comparison_period_days = db.Column(db.Integer, default=60)               # Month-over-month baseline (was days=60)
    default_trend_period_days = db.Column(db.Integer, default=30)            # Performance trends default (was days=30)
    recent_transaction_days = db.Column(db.Integer, default=7)               # Recent activity cutoff (was 7 days)
    quarter_comparison_days = db.Column(db.Integer, default=90)              # Quarter analysis period (was 90 days)
    
    # Display Limit Parameters
    max_categories_displayed = db.Column(db.Integer, default=10)             # Top categories limit (was LIMIT 10)
    max_high_value_items = db.Column(db.Integer, default=20)                 # High-value items limit (was LIMIT 20)
    max_trend_categories = db.Column(db.Integer, default=10)                 # Utilization trends limit (was LIMIT 10)
    max_opportunities_displayed = db.Column(db.Integer, default=10)          # Underutilized items limit (was LIMIT 10)
    default_activity_limit = db.Column(db.Integer, default=10)               # Recent activity display (was limit=10)
    diy_max_categories = db.Column(db.Integer, default=10)                   # DIY-specific categories (was LIMIT 10)
    
    # Business Threshold Parameters  
    high_value_threshold = db.Column(db.Float, default=100.0)                # High-value items threshold (was > 100)
    underutilized_value_threshold = db.Column(db.Float, default=50.0)        # Opportunity identification (was > 50)
    construction_heavy_equipment_threshold = db.Column(db.Float, default=200.0)  # Heavy equipment classification (was > 200)
    
    # Alert Threshold Parameters
    maintenance_backlog_threshold = db.Column(db.Integer, default=2)         # Maintenance backlog alert (was > 2)
    high_priority_maintenance_threshold = db.Column(db.Integer, default=5)   # High priority alert (was > 5)
    critical_maintenance_threshold = db.Column(db.Integer, default=10)       # Critical maintenance alert (was > 10)
    low_stock_threshold = db.Column(db.Integer, default=3)                   # Low stock alert (was < 3)
    min_category_size = db.Column(db.Integer, default=5)                     # Minimum category size (was > 5)
    
    # Store Classification Parameters
    new_store_threshold_months = db.Column(db.Integer, default=12)           # New store classification (was < 12)
    developing_store_threshold_months = db.Column(db.Integer, default=24)    # Developing store classification (was < 24)
    
    # Business Type Specific Parameters
    diy_weekend_percentage = db.Column(db.Float, default=70.0)               # DIY weekend usage pattern (was 70%)
    
    # Store-specific manager dashboard overrides (JSON format)
    # Example: {"3607": {"recent_activity_period_days": 45}, "6800": {"high_value_threshold": 150.0}}
    store_specific_thresholds = db.Column(db.JSON, default={})
    
    # Manager Dashboard Settings
    enable_maintenance_alerts = db.Column(db.Boolean, default=True)
    enable_inventory_alerts = db.Column(db.Boolean, default=True)
    enable_performance_alerts = db.Column(db.Boolean, default=True)
    alert_frequency = db.Column(db.String(20), default='daily')              # daily, weekly, monthly
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'config_name'),
    )
    
    def get_store_threshold(self, store_code: str, threshold_type: str):
        """
        Get store-specific manager dashboard threshold or fall back to global default.
        
        Args:
            store_code (str): Store identifier (e.g., '3607', '6800')
            threshold_type (str): Type of threshold to retrieve
            
        Returns:
            float/int: Configured threshold value for the store or global default
        """
        # Check for store-specific override
        if self.store_specific_thresholds and store_code in self.store_specific_thresholds:
            store_config = self.store_specific_thresholds[store_code]
            if threshold_type in store_config:
                return store_config[threshold_type]
        
        # Fall back to global configuration
        threshold_map = {
            'recent_activity_period_days': self.recent_activity_period_days,
            'comparison_period_days': self.comparison_period_days,
            'default_trend_period_days': self.default_trend_period_days,
            'recent_transaction_days': self.recent_transaction_days,
            'quarter_comparison_days': self.quarter_comparison_days,
            'max_categories_displayed': self.max_categories_displayed,
            'max_high_value_items': self.max_high_value_items,
            'max_trend_categories': self.max_trend_categories,
            'max_opportunities_displayed': self.max_opportunities_displayed,
            'default_activity_limit': self.default_activity_limit,
            'diy_max_categories': self.diy_max_categories,
            'high_value_threshold': self.high_value_threshold,
            'underutilized_value_threshold': self.underutilized_value_threshold,
            'construction_heavy_equipment_threshold': self.construction_heavy_equipment_threshold,
            'maintenance_backlog_threshold': self.maintenance_backlog_threshold,
            'high_priority_maintenance_threshold': self.high_priority_maintenance_threshold,
            'critical_maintenance_threshold': self.critical_maintenance_threshold,
            'low_stock_threshold': self.low_stock_threshold,
            'min_category_size': self.min_category_size,
            'new_store_threshold_months': self.new_store_threshold_months,
            'developing_store_threshold_months': self.developing_store_threshold_months,
            'diy_weekend_percentage': self.diy_weekend_percentage
        }
        
        return threshold_map.get(threshold_type, 30)  # Safe fallback


def get_default_manager_dashboard_config():
    """Get default manager dashboard configuration settings"""
    return {
        'time_periods': {
            'recent_activity_days': 30,                  # Recent activity definition
            'comparison_period_days': 60,                # Month-over-month baseline
            'default_trend_days': 30,                    # Performance trends default
            'recent_transaction_days': 7,                # Recent activity cutoff
            'quarter_comparison_days': 90                # Quarter analysis period
        },
        'display_limits': {
            'max_categories': 10,                        # Top categories displayed
            'max_high_value_items': 20,                  # High-value items shown
            'max_trend_categories': 10,                  # Utilization trends
            'max_opportunities': 10,                     # Underutilized items
            'default_activity_limit': 10,                # Recent activity count
            'diy_max_categories': 10                     # DIY-specific categories
        },
        'business_thresholds': {
            'high_value_threshold': 100.0,               # High-value items ($)
            'underutilized_threshold': 50.0,             # Opportunity identification ($)
            'construction_heavy_equipment': 200.0        # Heavy equipment classification ($)
        },
        'alert_thresholds': {
            'maintenance_backlog': 2,                    # Maintenance backlog trigger
            'high_priority_maintenance': 5,              # High priority alert
            'critical_maintenance': 10,                  # Critical maintenance alert
            'low_stock_threshold': 3,                    # Low stock alert
            'min_category_size': 5                       # Minimum category size
        },
        'store_classification': {
            'new_store_months': 12,                      # New store threshold
            'developing_store_months': 24                # Developing store threshold
        },
        'business_insights': {
            'diy_weekend_percentage': 70.0               # DIY weekend usage pattern
        },
        'features': {
            'enable_maintenance_alerts': True,
            'enable_inventory_alerts': True, 
            'enable_performance_alerts': True,
            'alert_frequency': 'daily'
        }
    }