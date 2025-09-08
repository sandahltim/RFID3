# app/models/weather_models.py
# Weather and Industry Analytics Models for Minnesota Rental Business
# Created: 2025-08-31

from app import db
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Index, UniqueConstraint, func, text
from enum import Enum
import json

class WeatherData(db.Model):
    """Store weather data for Twin Cities metro area and Minnesota regions"""
    __tablename__ = "weather_data"
    __table_args__ = (
        db.Index("ix_weather_data_date", "observation_date"),
        db.Index("ix_weather_data_location", "location_code"),
        db.Index("ix_weather_data_source", "data_source"),
        UniqueConstraint("observation_date", "location_code", "data_source", 
                        name="uq_weather_observation"),
    )

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    observation_date = db.Column(db.Date, nullable=False)
    location_code = db.Column(db.String(20), nullable=False)  # MSP, KMSP, etc.
    location_name = db.Column(db.String(100))  # "Minneapolis-St. Paul", "Wayzata", etc.
    data_source = db.Column(db.String(50), nullable=False)  # "NWS", "WeatherAPI", etc.
    
    # Temperature data (Fahrenheit)
    temperature_high = db.Column(db.DECIMAL(5, 2))
    temperature_low = db.Column(db.DECIMAL(5, 2))
    temperature_avg = db.Column(db.DECIMAL(5, 2))
    feels_like_high = db.Column(db.DECIMAL(5, 2))
    feels_like_low = db.Column(db.DECIMAL(5, 2))
    
    # Precipitation data (inches)
    precipitation = db.Column(db.DECIMAL(6, 3))  # Up to 999.999 inches
    precipitation_type = db.Column(db.String(20))  # "rain", "snow", "mixed", "none"
    snow_depth = db.Column(db.DECIMAL(6, 2))
    
    # Wind data
    wind_speed_avg = db.Column(db.DECIMAL(5, 2))  # mph
    wind_speed_max = db.Column(db.DECIMAL(5, 2))
    wind_direction = db.Column(db.String(10))  # "NW", "SSE", etc.
    
    # Atmospheric conditions
    humidity_avg = db.Column(db.Integer)  # percentage
    barometric_pressure = db.Column(db.DECIMAL(6, 2))  # inHg
    visibility = db.Column(db.DECIMAL(4, 1))  # miles
    cloud_cover = db.Column(db.Integer)  # percentage
    
    # Weather conditions
    weather_condition = db.Column(db.String(50))  # "sunny", "cloudy", "rainy", etc.
    severe_weather_alerts = db.Column(db.JSON)  # Array of alert types
    
    # Quality and metadata
    data_quality_score = db.Column(db.DECIMAL(3, 2), default=1.00)  # 0.00 to 1.00
    is_forecast = db.Column(db.Boolean, default=False)
    forecast_days_ahead = db.Column(db.Integer)  # For forecast data
    
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            "id": self.id,
            "date": self.observation_date.isoformat() if self.observation_date else None,
            "location": self.location_name,
            "temperature_high": float(self.temperature_high) if self.temperature_high else None,
            "temperature_low": float(self.temperature_low) if self.temperature_low else None,
            "precipitation": float(self.precipitation) if self.precipitation else None,
            "wind_speed_avg": float(self.wind_speed_avg) if self.wind_speed_avg else None,
            "weather_condition": self.weather_condition,
            "is_forecast": self.is_forecast
        }


class MinnesotaSeasonalPattern(db.Model):
    """Track Minnesota-specific seasonal patterns for different industries"""
    __tablename__ = "mn_seasonal_patterns"
    __table_args__ = (
        db.Index("ix_seasonal_pattern_type", "pattern_type"),
        db.Index("ix_seasonal_season", "season"),
        db.Index("ix_seasonal_industry", "industry_segment"),
    )

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    pattern_type = db.Column(db.String(50), nullable=False)  # "peak_season", "weather_dependent", etc.
    industry_segment = db.Column(
        db.Enum('party_event', 'construction_diy', 'landscaping', 'mixed'),
        nullable=False
    )
    
    season = db.Column(db.String(20))  # "spring", "summer", "fall", "winter"
    month = db.Column(db.Integer)  # 1-12
    week_of_year = db.Column(db.Integer)  # 1-53
    
    # Pattern characteristics
    demand_multiplier = db.Column(db.DECIMAL(4, 2), default=1.00)  # 0.00 to 99.99
    weather_sensitivity = db.Column(db.DECIMAL(3, 2))  # 0.00 to 1.00
    lead_time_days = db.Column(db.Integer)  # How many days in advance bookings typically occur
    
    # Specific Minnesota events/patterns
    event_type = db.Column(db.String(100))  # "wedding_season", "graduation", "state_fair", etc.
    temperature_threshold_min = db.Column(db.DECIMAL(5, 2))  # Minimum temp for activity
    temperature_threshold_max = db.Column(db.DECIMAL(5, 2))  # Maximum temp for activity
    precipitation_sensitivity = db.Column(db.DECIMAL(3, 2))  # How much rain affects demand
    
    description = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            "id": self.id,
            "pattern_type": self.pattern_type,
            "industry_segment": self.industry_segment,
            "season": self.season,
            "demand_multiplier": float(self.demand_multiplier) if self.demand_multiplier else 1.0,
            "weather_sensitivity": float(self.weather_sensitivity) if self.weather_sensitivity else None,
            "event_type": self.event_type,
            "description": self.description
        }


class WeatherRentalCorrelation(db.Model):
    """Store correlations between weather patterns and rental demand"""
    __tablename__ = "weather_rental_correlations"
    __table_args__ = (
        db.Index("ix_weather_corr_date", "analysis_date"),
        db.Index("ix_weather_corr_store", "store_code"),
        db.Index("ix_weather_corr_category", "equipment_category"),
        db.Index("ix_weather_corr_strength", "correlation_strength"),
    )

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    analysis_date = db.Column(db.Date, nullable=False)
    analysis_period_start = db.Column(db.Date)
    analysis_period_end = db.Column(db.Date)
    
    # Correlation parameters
    store_code = db.Column(db.String(10))  # "3607", "6800", etc., null for all stores
    equipment_category = db.Column(db.String(100))  # Equipment category or "all"
    industry_segment = db.Column(
        db.Enum('party_event', 'construction_diy', 'landscaping', 'mixed'),
        nullable=False
    )
    
    # Weather factors
    weather_factor = db.Column(db.String(50), nullable=False)  # "temperature_high", "precipitation", etc.
    
    # Correlation results
    correlation_coefficient = db.Column(db.DECIMAL(4, 3))  # -1.000 to 1.000
    p_value = db.Column(db.DECIMAL(8, 6))
    correlation_strength = db.Column(
        db.Enum('very_strong', 'strong', 'moderate', 'weak', 'very_weak', 'none'),
        nullable=False
    )
    
    # Lag analysis
    optimal_lag_days = db.Column(db.Integer, default=0)  # Weather leads rental by X days
    lag_correlation_coefficient = db.Column(db.DECIMAL(4, 3))
    
    # Business metrics affected
    revenue_correlation = db.Column(db.DECIMAL(4, 3))
    quantity_correlation = db.Column(db.DECIMAL(4, 3))
    booking_frequency_correlation = db.Column(db.DECIMAL(4, 3))
    
    # Statistical metadata
    data_points_analyzed = db.Column(db.Integer)
    confidence_interval_lower = db.Column(db.DECIMAL(4, 3))
    confidence_interval_upper = db.Column(db.DECIMAL(4, 3))
    r_squared = db.Column(db.DECIMAL(4, 3))
    
    # Insights
    business_insight = db.Column(db.Text)
    forecasting_value = db.Column(
        db.Enum('high', 'medium', 'low', 'none'),
        default='low'
    )
    
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            "id": self.id,
            "analysis_date": self.analysis_date.isoformat() if self.analysis_date else None,
            "store_code": self.store_code,
            "equipment_category": self.equipment_category,
            "industry_segment": self.industry_segment,
            "weather_factor": self.weather_factor,
            "correlation_coefficient": float(self.correlation_coefficient) if self.correlation_coefficient else None,
            "correlation_strength": self.correlation_strength,
            "optimal_lag_days": self.optimal_lag_days,
            "business_insight": self.business_insight,
            "forecasting_value": self.forecasting_value
        }


class EquipmentCategorization(db.Model):
    """Store automatic categorization of equipment into industry segments"""
    __tablename__ = "equipment_categorization"
    __table_args__ = (
        db.Index("ix_equip_cat_item_num", "item_num"),
        db.Index("ix_equip_cat_industry", "industry_segment"),
        db.Index("ix_equip_cat_confidence", "confidence_score"),
        UniqueConstraint("item_num", name="uq_item_categorization"),
    )

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    item_num = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(255))
    item_description = db.Column(db.Text)
    
    # Primary categorization
    industry_segment = db.Column(
        db.Enum('party_event', 'construction_diy', 'landscaping', 'mixed', 'uncategorized'),
        nullable=False
    )
    
    # Sub-categories
    party_event_type = db.Column(db.String(50))  # "tent", "table", "chair", "lighting", etc.
    construction_type = db.Column(db.String(50))  # "power_tool", "hand_tool", "scaffolding", etc.
    landscaping_type = db.Column(db.String(50))  # "mower", "trimmer", "aerator", etc.
    
    # Confidence and classification method
    confidence_score = db.Column(db.DECIMAL(3, 2), default=0.50)  # 0.00 to 1.00
    classification_method = db.Column(
        db.Enum('keyword_match', 'ml_classification', 'manual_override', 'rule_based'),
        nullable=False
    )
    
    # Weather sensitivity
    weather_dependent = db.Column(db.Boolean, default=True)
    optimal_weather_conditions = db.Column(db.JSON)  # Array of preferred conditions
    weather_cancellation_risk = db.Column(
        db.Enum('high', 'medium', 'low', 'none'),
        default='medium'
    )
    
    # Seasonal patterns
    peak_season_start = db.Column(db.Integer)  # Month (1-12)
    peak_season_end = db.Column(db.Integer)
    off_season_discount_eligible = db.Column(db.Boolean, default=False)
    
    # Business rules
    requires_weather_monitoring = db.Column(db.Boolean, default=True)
    lead_time_sensitivity = db.Column(db.Integer)  # Days
    
    # Classification keywords used
    classification_keywords = db.Column(db.JSON)  # Keywords that triggered classification
    
    # Manual override tracking
    manually_verified = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.String(100))
    verified_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            "id": self.id,
            "item_num": self.item_num,
            "item_name": self.item_name,
            "industry_segment": self.industry_segment,
            "party_event_type": self.party_event_type,
            "construction_type": self.construction_type,
            "confidence_score": float(self.confidence_score) if self.confidence_score else 0.5,
            "classification_method": self.classification_method,
            "weather_dependent": self.weather_dependent,
            "weather_cancellation_risk": self.weather_cancellation_risk,
            "manually_verified": self.manually_verified
        }


class StoreRegionalAnalytics(db.Model):
    """Store regional analytics for Minnesota stores with weather correlations"""
    __tablename__ = "store_regional_analytics"
    __table_args__ = (
        db.Index("ix_store_analytics_store", "store_code"),
        db.Index("ix_store_analytics_date", "analysis_date"),
        db.Index("ix_store_analytics_metric", "metric_name"),
        UniqueConstraint("store_code", "analysis_date", "metric_name", "industry_segment",
                        name="uq_store_metric_analysis"),
    )

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    store_code = db.Column(db.String(10), nullable=False)  # "3607", "6800", "728", "8101"
    store_name = db.Column(db.String(100))  # "Wayzata", "Brooklyn Park", etc.
    analysis_date = db.Column(db.Date, nullable=False)
    
    industry_segment = db.Column(
        db.Enum('party_event', 'construction_diy', 'landscaping', 'mixed', 'all'),
        nullable=False
    )
    
    metric_name = db.Column(db.String(100), nullable=False)  # "weather_adjusted_demand", etc.
    metric_value = db.Column(db.DECIMAL(15, 2))
    metric_unit = db.Column(db.String(20))  # "dollars", "units", "percentage"
    
    # Comparison metrics
    regional_average = db.Column(db.DECIMAL(15, 2))
    variance_from_regional = db.Column(db.DECIMAL(6, 2))  # Percentage
    rank_among_stores = db.Column(db.Integer)
    
    # Weather correlation factors
    weather_impact_factor = db.Column(db.DECIMAL(4, 2))  # How much weather affects this store
    primary_weather_driver = db.Column(db.String(50))  # Main weather factor affecting store
    seasonal_adjustment_factor = db.Column(db.DECIMAL(4, 2))
    
    # Geographic factors
    customer_drive_time_avg = db.Column(db.DECIMAL(4, 1))  # Average minutes customers drive
    competition_density = db.Column(
        db.Enum('high', 'medium', 'low'),
        default='medium'
    )
    market_saturation = db.Column(db.DECIMAL(3, 2))  # 0.00 to 1.00
    
    # Transfer recommendations
    recommended_transfers_to = db.Column(db.JSON)  # Array of {store_code, item_category, quantity}
    recommended_transfers_from = db.Column(db.JSON)
    transfer_opportunity_score = db.Column(db.DECIMAL(3, 2))
    
    confidence_level = db.Column(db.DECIMAL(3, 2), default=0.80)
    
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self):
        return {
            "id": self.id,
            "store_code": self.store_code,
            "store_name": self.store_name,
            "analysis_date": self.analysis_date.isoformat() if self.analysis_date else None,
            "industry_segment": self.industry_segment,
            "metric_name": self.metric_name,
            "metric_value": float(self.metric_value) if self.metric_value else None,
            "variance_from_regional": float(self.variance_from_regional) if self.variance_from_regional else None,
            "weather_impact_factor": float(self.weather_impact_factor) if self.weather_impact_factor else None,
            "primary_weather_driver": self.primary_weather_driver,
            "recommended_transfers_to": self.recommended_transfers_to,
            "transfer_opportunity_score": float(self.transfer_opportunity_score) if self.transfer_opportunity_score else None
        }


class WeatherForecastDemand(db.Model):
    """Store weather-based demand forecasts for inventory planning"""
    __tablename__ = "weather_forecast_demand"
    __table_args__ = (
        db.Index("ix_forecast_date", "forecast_date"),
        db.Index("ix_forecast_store", "store_code"),
        db.Index("ix_forecast_category", "equipment_category"),
        db.Index("ix_forecast_confidence", "confidence_level"),
    )

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    forecast_date = db.Column(db.Date, nullable=False)
    forecast_generated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    forecast_horizon_days = db.Column(db.Integer, default=7)  # How many days ahead
    
    store_code = db.Column(db.String(10))  # Null for system-wide forecast
    equipment_category = db.Column(db.String(100))
    industry_segment = db.Column(
        db.Enum('party_event', 'construction_diy', 'landscaping', 'mixed'),
        nullable=False
    )
    
    # Forecast components
    base_demand = db.Column(db.DECIMAL(10, 2))  # Historical average
    weather_adjustment = db.Column(db.DECIMAL(8, 4))  # Multiplier: -1.0 to +1.0
    seasonal_adjustment = db.Column(db.DECIMAL(6, 4))  # Multiplier
    event_adjustment = db.Column(db.DECIMAL(6, 4))  # For known events
    
    # Final forecast
    predicted_demand_units = db.Column(db.Integer)
    predicted_demand_revenue = db.Column(db.DECIMAL(12, 2))
    demand_range_low = db.Column(db.Integer)
    demand_range_high = db.Column(db.Integer)
    
    # Weather forecast used
    expected_weather_conditions = db.Column(db.JSON)
    weather_uncertainty_factor = db.Column(db.DECIMAL(3, 2))
    
    # Model performance
    confidence_level = db.Column(db.DECIMAL(3, 2))  # 0.00 to 1.00
    model_version = db.Column(db.String(20))
    
    # Actual vs predicted (filled in later)
    actual_demand_units = db.Column(db.Integer)
    actual_demand_revenue = db.Column(db.DECIMAL(12, 2))
    forecast_accuracy = db.Column(db.DECIMAL(3, 2))  # Calculated after actual data
    
    def to_dict(self):
        return {
            "id": self.id,
            "forecast_date": self.forecast_date.isoformat() if self.forecast_date else None,
            "store_code": self.store_code,
            "equipment_category": self.equipment_category,
            "industry_segment": self.industry_segment,
            "predicted_demand_units": self.predicted_demand_units,
            "predicted_demand_revenue": float(self.predicted_demand_revenue) if self.predicted_demand_revenue else None,
            "confidence_level": float(self.confidence_level) if self.confidence_level else None,
            "expected_weather_conditions": self.expected_weather_conditions,
            "weather_adjustment": float(self.weather_adjustment) if self.weather_adjustment else None,
            "actual_demand_units": self.actual_demand_units,
            "forecast_accuracy": float(self.forecast_accuracy) if self.forecast_accuracy else None
        }