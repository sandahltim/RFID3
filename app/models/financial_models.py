from app import db
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func
from decimal import Decimal


class PayrollTrendsData(db.Model):
    __tablename__ = 'payroll_trends_data'
    
    id = db.Column(db.Integer, primary_key=True)
    week_ending = db.Column(db.Date)
    location_code = db.Column(db.String(20))
    rental_revenue = db.Column(db.Numeric(15, 2))
    all_revenue = db.Column(db.Numeric(15, 2))
    payroll_amount = db.Column(db.Numeric(15, 2))
    wage_hours = db.Column(db.Numeric(10, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PayrollTrendsData {self.location_code} {self.week_ending}: Rev={self.rental_revenue}, Payroll={self.payroll_amount}>'
    
    @hybrid_property
    def labor_cost_ratio(self):
        """Calculate labor cost as percentage of all revenue"""
        if self.all_revenue and self.payroll_amount:
            return (float(self.payroll_amount) / float(self.all_revenue)) * 100
        return 0
    
    @hybrid_property
    def revenue_per_hour(self):
        """Calculate revenue per labor hour"""
        if self.wage_hours and self.wage_hours > 0:
            return float(self.all_revenue or 0) / float(self.wage_hours)
        return 0
    
    @hybrid_property
    def avg_hourly_rate(self):
        """Calculate average hourly wage rate"""
        if self.wage_hours and self.wage_hours > 0:
            return float(self.payroll_amount or 0) / float(self.wage_hours)
        return 0
    
    @hybrid_property
    def gross_profit(self):
        """Calculate gross profit (revenue - payroll)"""
        return float(self.all_revenue or 0) - float(self.payroll_amount or 0)
    
    @hybrid_property
    def rental_revenue_ratio(self):
        """Calculate rental revenue as percentage of all revenue"""
        if self.all_revenue and self.rental_revenue:
            return (float(self.rental_revenue) / float(self.all_revenue)) * 100
        return 0

class ScorecardMetricsDefinition(db.Model):
    """Metadata definitions for scorecard metrics"""
    __tablename__ = 'scorecard_metrics_definitions'
    
    id = db.Column(db.Integer, primary_key=True)
    row_number = db.Column(db.Integer, unique=True)  # CSV row number
    metric_code = db.Column(db.String(100), unique=True)  # e.g., 'total_weekly_revenue'
    title = db.Column(db.Text)  # Full metric title
    description = db.Column(db.Text)  # How to calculate/find this metric
    owner = db.Column(db.String(100))  # Person responsible
    goal = db.Column(db.String(100))  # Target goal (changes quarterly)
    status = db.Column(db.String(50))  # at-risk, on-track, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ScorecardMetric {self.metric_code}: {self.title}>'

class ScorecardTrendsData(db.Model):
    __tablename__ = 'scorecard_trends_data'
    
    id = db.Column(db.Integer, primary_key=True)
    week_ending = db.Column(db.Date)
    total_weekly_revenue = db.Column(db.Numeric(15, 2))
    revenue_3607 = db.Column(db.Numeric(15, 2))
    revenue_6800 = db.Column(db.Numeric(15, 2))
    revenue_728 = db.Column(db.Numeric(15, 2))
    revenue_8101 = db.Column(db.Numeric(15, 2))
    new_contracts_3607 = db.Column(db.Integer)
    new_contracts_6800 = db.Column(db.Integer)
    new_contracts_728 = db.Column(db.Integer)
    new_contracts_8101 = db.Column(db.Integer)
    deliveries_scheduled_8101 = db.Column(db.Integer)
    reservation_next14_3607 = db.Column(db.Numeric(15, 2))
    reservation_next14_6800 = db.Column(db.Numeric(15, 2))
    reservation_next14_728 = db.Column(db.Numeric(15, 2))
    reservation_next14_8101 = db.Column(db.Numeric(15, 2))
    total_reservation_3607 = db.Column(db.Numeric(15, 2))
    total_reservation_6800 = db.Column(db.Numeric(15, 2))
    total_reservation_728 = db.Column(db.Numeric(15, 2))
    total_reservation_8101 = db.Column(db.Numeric(15, 2))
    ar_over_45_days_percent = db.Column(db.Numeric(5, 2))
    total_discount = db.Column(db.Numeric(15, 2))
    week_number = db.Column(db.Integer)
    open_quotes_8101 = db.Column(db.Integer)
    total_ar_cash_customers = db.Column(db.Numeric(15, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ScorecardTrendsData {self.week_ending}: Total Rev={self.total_weekly_revenue}>'
    
    @hybrid_property
    def total_calculated_revenue(self):
        """Calculate total revenue from store-specific revenues"""
        return (float(self.revenue_3607 or 0) + float(self.revenue_6800 or 0) + 
                float(self.revenue_728 or 0) + float(self.revenue_8101 or 0))
    
    @hybrid_property
    def total_contracts(self):
        """Calculate total new contracts across all stores"""
        return ((self.new_contracts_3607 or 0) + (self.new_contracts_6800 or 0) + 
                (self.new_contracts_728 or 0) + (self.new_contracts_8101 or 0))
    
    @hybrid_property
    def avg_contract_value(self):
        """Calculate average contract value"""
        total_contracts = self.total_contracts
        if total_contracts > 0:
            return self.total_calculated_revenue / total_contracts
        return 0
    
    @hybrid_property
    def total_reservation_pipeline(self):
        """Calculate total reservation pipeline value"""
        return (float(self.reservation_next14_3607 or 0) + float(self.reservation_next14_6800 or 0) + 
                float(self.reservation_next14_728 or 0) + float(self.reservation_next14_8101 or 0))
    
    @hybrid_property
    def revenue_concentration_risk(self):
        """Calculate revenue concentration (highest store % of total)"""
        total_rev = self.total_calculated_revenue
        if total_rev > 0:
            store_revenues = [
                float(self.revenue_3607 or 0),
                float(self.revenue_6800 or 0), 
                float(self.revenue_728 or 0),
                float(self.revenue_8101 or 0)
            ]
            return (max(store_revenues) / total_rev) * 100
        return 0
    
    def get_store_metrics(self):
        """Get detailed metrics for each store"""
        return {
            'Wayzata': {
                'code': '3607',
                'revenue': float(self.revenue_3607 or 0),
                'contracts': self.new_contracts_3607 or 0,
                'pipeline': float(self.reservation_next14_3607 or 0),
                'total_reservations': float(self.total_reservation_3607 or 0)
            },
            'Brooklyn Park': {
                'code': '6800',
                'revenue': float(self.revenue_6800 or 0),
                'contracts': self.new_contracts_6800 or 0,
                'pipeline': float(self.reservation_next14_6800 or 0),
                'total_reservations': float(self.total_reservation_6800 or 0)
            },
            'Fridley': {
                'code': '8101',
                'revenue': float(self.revenue_8101 or 0),
                'contracts': self.new_contracts_8101 or 0,
                'pipeline': float(self.reservation_next14_8101 or 0),
                'total_reservations': float(self.total_reservation_8101 or 0)
            },
            'Elk River': {
                'code': '728',
                'revenue': float(self.revenue_728 or 0),
                'contracts': self.new_contracts_728 or 0,
                'pipeline': float(self.reservation_next14_728 or 0),
                'total_reservations': float(self.total_reservation_728 or 0),
                'deliveries_scheduled': self.deliveries_scheduled_8101 or 0,
                'open_quotes': self.open_quotes_8101 or 0
            }
        }


class FinancialMetrics(db.Model):
    """Store calculated financial metrics with rolling averages and YoY comparisons"""
    __tablename__ = 'financial_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    calculation_date = db.Column(db.Date, nullable=False)
    metric_name = db.Column(db.String(100), nullable=False)  # revenue, contracts, utilization, etc.
    metric_category = db.Column(db.String(50))  # rolling_avg, yoy_comparison, forecast
    store_code = db.Column(db.String(10))  # null for company-wide metrics
    
    # Core metric values
    current_value = db.Column(db.Numeric(15, 2))
    rolling_3wk_avg = db.Column(db.Numeric(15, 2))
    rolling_3wk_forward = db.Column(db.Numeric(15, 2))
    rolling_3wk_backward = db.Column(db.Numeric(15, 2))
    
    # Year-over-year comparison
    previous_year_value = db.Column(db.Numeric(15, 2))
    yoy_growth_rate = db.Column(db.Numeric(8, 4))  # Percentage with 4 decimal places
    yoy_absolute_change = db.Column(db.Numeric(15, 2))
    
    # Trend analysis
    trend_direction = db.Column(db.String(20))  # increasing, decreasing, stable
    trend_strength = db.Column(db.String(20))   # strong, moderate, weak
    volatility_score = db.Column(db.Numeric(8, 4))
    
    # Seasonal adjustments
    seasonal_factor = db.Column(db.Numeric(6, 4))
    seasonally_adjusted_value = db.Column(db.Numeric(15, 2))
    
    # Quality and metadata
    data_quality_score = db.Column(db.Numeric(3, 2))  # 0.00 to 1.00
    confidence_level = db.Column(db.Numeric(3, 2))    # 0.00 to 1.00
    calculation_method = db.Column(db.String(100))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_fin_metrics_date_metric', 'calculation_date', 'metric_name'),
        db.Index('idx_fin_metrics_store_metric', 'store_code', 'metric_name'),
        db.Index('idx_fin_metrics_category', 'metric_category'),
    )
    
    def __repr__(self):
        return f'<FinancialMetrics {self.metric_name} {self.calculation_date}: {self.current_value}>'
    
    @hybrid_property
    def trend_momentum(self):
        """Calculate trend momentum based on rolling averages"""
        if self.rolling_3wk_forward and self.rolling_3wk_backward and self.rolling_3wk_backward != 0:
            return ((float(self.rolling_3wk_forward) - float(self.rolling_3wk_backward)) / 
                   float(self.rolling_3wk_backward)) * 100
        return 0
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.calculation_date.strftime('%Y-%m-%d'),
            'metric_name': self.metric_name,
            'store_code': self.store_code,
            'current_value': float(self.current_value) if self.current_value else 0,
            'rolling_3wk_avg': float(self.rolling_3wk_avg) if self.rolling_3wk_avg else 0,
            'yoy_growth_rate': float(self.yoy_growth_rate) if self.yoy_growth_rate else 0,
            'trend_direction': self.trend_direction,
            'trend_momentum': self.trend_momentum,
            'confidence_level': float(self.confidence_level) if self.confidence_level else 0
        }


class FinancialForecasts(db.Model):
    """Store financial forecasting data with confidence intervals"""
    __tablename__ = 'financial_forecasts'
    
    id = db.Column(db.Integer, primary_key=True)
    forecast_date = db.Column(db.Date, nullable=False)  # Date forecast was made
    target_date = db.Column(db.Date, nullable=False)    # Date forecast is for
    metric_name = db.Column(db.String(100), nullable=False)
    store_code = db.Column(db.String(10))  # null for company-wide forecasts
    
    # Forecast values
    forecast_value = db.Column(db.Numeric(15, 2), nullable=False)
    confidence_low = db.Column(db.Numeric(15, 2))   # Lower confidence bound
    confidence_high = db.Column(db.Numeric(15, 2))  # Upper confidence bound
    confidence_level = db.Column(db.Numeric(3, 2))  # 0.90, 0.95, 0.99
    
    # Forecast components
    trend_component = db.Column(db.Numeric(15, 2))
    seasonal_component = db.Column(db.Numeric(15, 2))
    cyclical_component = db.Column(db.Numeric(15, 2))
    irregular_component = db.Column(db.Numeric(15, 2))
    
    # Model performance
    forecast_method = db.Column(db.String(50))      # trend_seasonal, arima, etc.
    model_accuracy = db.Column(db.Numeric(5, 4))   # Historical accuracy score
    forecast_horizon_days = db.Column(db.Integer)   # Days into future
    
    # Actual vs forecast (filled after actual data available)
    actual_value = db.Column(db.Numeric(15, 2))
    forecast_error = db.Column(db.Numeric(15, 2))
    absolute_percentage_error = db.Column(db.Numeric(5, 2))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_forecasts_target_metric', 'target_date', 'metric_name'),
        db.Index('idx_forecasts_store_target', 'store_code', 'target_date'),
        db.Index('idx_forecasts_method', 'forecast_method'),
    )
    
    def __repr__(self):
        return f'<FinancialForecasts {self.metric_name} {self.target_date}: {self.forecast_value}>'
    
    @hybrid_property
    def forecast_accuracy_pct(self):
        """Calculate forecast accuracy as percentage (if actual value available)"""
        if self.actual_value and self.forecast_value and self.actual_value != 0:
            error_rate = abs(float(self.actual_value) - float(self.forecast_value)) / float(self.actual_value)
            return max(0, (1 - error_rate) * 100)
        return None
    
    @hybrid_property
    def days_ahead(self):
        """Calculate days between forecast date and target date"""
        if self.forecast_date and self.target_date:
            return (self.target_date - self.forecast_date).days
        return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'forecast_date': self.forecast_date.strftime('%Y-%m-%d'),
            'target_date': self.target_date.strftime('%Y-%m-%d'),
            'metric_name': self.metric_name,
            'store_code': self.store_code,
            'forecast_value': float(self.forecast_value) if self.forecast_value else 0,
            'confidence_low': float(self.confidence_low) if self.confidence_low else 0,
            'confidence_high': float(self.confidence_high) if self.confidence_high else 0,
            'confidence_level': float(self.confidence_level) if self.confidence_level else 0,
            'forecast_method': self.forecast_method,
            'days_ahead': self.days_ahead,
            'forecast_accuracy_pct': self.forecast_accuracy_pct
        }


class StorePerformanceBenchmarks(db.Model):
    """Store benchmark metrics for multi-store comparison"""
    __tablename__ = 'store_performance_benchmarks'
    
    id = db.Column(db.Integer, primary_key=True)
    calculation_date = db.Column(db.Date, nullable=False)
    store_code = db.Column(db.String(10), nullable=False)
    store_name = db.Column(db.String(100))
    
    # Financial performance metrics
    total_revenue = db.Column(db.Numeric(15, 2))
    revenue_per_sqft = db.Column(db.Numeric(10, 2))  # If square footage available
    profit_margin_pct = db.Column(db.Numeric(5, 2))
    
    # Operational efficiency metrics
    revenue_per_employee = db.Column(db.Numeric(12, 2))
    revenue_per_hour = db.Column(db.Numeric(10, 2))
    contracts_per_employee = db.Column(db.Numeric(8, 2))
    avg_contract_value = db.Column(db.Numeric(10, 2))
    
    # Customer metrics
    customer_acquisition_rate = db.Column(db.Numeric(8, 4))
    customer_retention_rate = db.Column(db.Numeric(5, 2))
    customer_satisfaction_score = db.Column(db.Numeric(3, 2))  # 1-5 scale
    
    # Asset utilization
    equipment_utilization_rate = db.Column(db.Numeric(5, 2))
    inventory_turnover_rate = db.Column(db.Numeric(8, 4))
    asset_roi_pct = db.Column(db.Numeric(8, 4))
    
    # Market position
    market_share_local_pct = db.Column(db.Numeric(5, 2))
    competitive_advantage_score = db.Column(db.Numeric(3, 2))  # 1-5 scale
    
    # Ranking metrics (calculated)
    revenue_rank = db.Column(db.Integer)
    efficiency_rank = db.Column(db.Integer)
    profitability_rank = db.Column(db.Integer)
    overall_performance_rank = db.Column(db.Integer)
    performance_tier = db.Column(db.String(20))  # top, high, moderate, low
    
    # Growth metrics
    revenue_growth_rate = db.Column(db.Numeric(8, 4))
    efficiency_improvement_rate = db.Column(db.Numeric(8, 4))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_store_benchmarks_date', 'calculation_date'),
        db.Index('idx_store_benchmarks_store', 'store_code'),
        db.Index('idx_store_benchmarks_rank', 'overall_performance_rank'),
    )
    
    def __repr__(self):
        return f'<StorePerformanceBenchmarks {self.store_name} {self.calculation_date}: Rank {self.overall_performance_rank}>'
    
    @hybrid_property
    def overall_performance_score(self):
        """Calculate overall performance score from multiple metrics"""
        revenue_score = (5 - (self.revenue_rank or 5)) * 20  # 0-80 points
        efficiency_score = (5 - (self.efficiency_rank or 5)) * 15  # 0-60 points
        profitability_score = (5 - (self.profitability_rank or 5)) * 20  # 0-80 points
        return revenue_score + efficiency_score + profitability_score  # 0-160 total
    
    def to_dict(self):
        return {
            'id': self.id,
            'date': self.calculation_date.strftime('%Y-%m-%d'),
            'store_code': self.store_code,
            'store_name': self.store_name,
            'total_revenue': float(self.total_revenue) if self.total_revenue else 0,
            'profit_margin_pct': float(self.profit_margin_pct) if self.profit_margin_pct else 0,
            'revenue_per_hour': float(self.revenue_per_hour) if self.revenue_per_hour else 0,
            'overall_performance_rank': self.overall_performance_rank,
            'performance_tier': self.performance_tier,
            'performance_score': self.overall_performance_score
        }