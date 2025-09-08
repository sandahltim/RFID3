
# RFID3 Analytics System - Service Method Reference

## BusinessAnalyticsService

### Main Methods:
- `calculate_equipment_utilization_analytics()` - Comprehensive equipment metrics
- `calculate_customer_analytics()` - Customer-based analytics
- `generate_executive_dashboard_metrics()` - Executive dashboard data

### Internal Methods:
- `_identify_high_performers(df)` - Identify top performing equipment
- `_identify_underperformers(df)` - Identify underperforming equipment
- `_analyze_by_category(df)` - Category-based analysis
- `_analyze_by_store(df)` - Store-based analysis

## MLCorrelationService

### Main Methods:
- `run_full_correlation_analysis()` - Complete correlation analysis
- `get_business_time_series()` - Get business metrics time series
- `get_external_factors_time_series()` - Get external factors data

### Analysis Methods:
- `calculate_correlations(df)` - Calculate standard correlations
- `calculate_lagged_correlations(df, max_lag=4)` - Calculate time-lagged correlations
- `generate_correlation_insights(correlations, lagged_correlations)` - Generate insights

## DataFetchService

### Methods:
- `fetch_weather_data(start_date, end_date)` - Fetch weather data
- `fetch_economic_indicators()` - Fetch economic indicators
- `store_external_factors(factors_data)` - Store external factors

## Database Views Created

### equipment_performance_view
- Provides pre-calculated ROI and performance tiers
- Columns: item_num, name, category, roi_percentage, performance_tier

### store_summary_view
- Aggregated store-level metrics
- Columns: current_store, total_items, active_items, avg_turnover_ytd, total_turnover_ytd
