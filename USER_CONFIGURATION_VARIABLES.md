# 🎛️ USER CONFIGURATION VARIABLES REFERENCE
*Comprehensive guide to all configurable parameters in RFID3 system*

---

## 📊 **EXECUTIVE DASHBOARD CONFIGURATION**

### **Health Score Parameters**
| Parameter | Current Value | Description | Range | Table |
|-----------|---------------|-------------|-------|-------|
| `base_health_score` | 75.0 | Starting health score before modifiers | 0-100 | executive_dashboard_configuration |
| `revenue_tier_1_threshold` | $100,000 | Tier 1 revenue threshold (excellent) | >0 | executive_dashboard_configuration |
| `revenue_tier_2_threshold` | $75,000 | Tier 2 revenue threshold (good) | >0 | executive_dashboard_configuration |
| `revenue_tier_3_threshold` | $50,000 | Tier 3 revenue threshold (fair) | >0 | executive_dashboard_configuration |
| `yoy_excellent_threshold` | 10.0% | YoY growth threshold for excellent rating | Any % | executive_dashboard_configuration |
| `yoy_good_threshold` | 5.0% | YoY growth threshold for good rating | Any % | executive_dashboard_configuration |
| `yoy_fair_threshold` | 0.0% | YoY growth threshold for fair rating | Any % | executive_dashboard_configuration |
| `utilization_excellent_threshold` | 85.0% | Utilization threshold for excellent rating | 0-100% | executive_dashboard_configuration |
| `utilization_good_threshold` | 75.0% | Utilization threshold for good rating | 0-100% | executive_dashboard_configuration |
| `utilization_fair_threshold` | 65.0% | Utilization threshold for fair rating | 0-100% | executive_dashboard_configuration |
| `utilization_poor_threshold` | 50.0% | Utilization threshold for poor rating | 0-100% | executive_dashboard_configuration |

### **Analysis Periods**
| Parameter | Current Value | Description | Range | Impact |
|-----------|---------------|-------------|-------|--------|
| `dashboard_query_limit` | 3 | Number of recent periods for KPI calculation | 1-12 | Query performance |
| `historical_weeks_limit` | 12 | Weeks of historical data for trend analysis | 4-52 | Trend accuracy |
| `forecast_weeks_limit` | 24 | Weeks of data for forecasting calculations | 12-52 | Forecast accuracy |
| `max_historical_weeks` | 52 | Maximum weeks for year-over-year comparisons | 26-104 | Comparison depth |
| `analysis_period_weeks` | 52 | Default analysis period for comprehensive views | 12-104 | Analysis scope |
| `rolling_window_size` | 12 | Rolling window for smoothed trend calculations | 3-26 | Trend smoothing |

---

## 📈 **BUSINESS ANALYTICS CONFIGURATION**

### **Performance Thresholds**
| Parameter | Current Value | Description | Range | Usage |
|-----------|---------------|-------------|-------|-------|
| `decline_threshold_pct` | 90% (0.9) | Threshold for identifying revenue decline | 70-95% | Alerting |
| `growth_threshold_pct` | 110% (1.1) | Threshold for identifying significant growth | 105-150% | Alerting |
| `performance_gap_multiplier` | 2.0 | Multiplier for identifying underperforming stores | 1.5-5.0 | Comparison |
| `low_utilization_threshold` | 40% | Threshold for low equipment utilization alerts | 20-60% | Alerting |
| `high_utilization_threshold` | 85% | Threshold for high utilization opportunities | 70-95% | Optimization |

### **Data Filtering & Quality**
| Parameter | Current Value | Description | Range | Purpose |
|-----------|---------------|-------------|-------|---------|
| `max_equipment_price` | $5,000 | Upper limit for equipment price filtering | >$0 | Data quality |
| `max_inventory_qty` | 10,000 | Upper limit for inventory quantity filtering | >0 | Data quality |
| `min_rental_rate` | $0.01 | Minimum rental rate for active equipment | ≥$0 | Active filtering |
| `min_forecast_data_points` | 12 | Minimum data points required for forecasting | 6-26 | Forecast reliability |

---

## 📊 **STATISTICAL & FORECASTING PARAMETERS**

### **Confidence & Precision**
| Parameter | Current Value | Description | Range | Statistical Meaning |
|-----------|---------------|-------------|-------|-------------------|
| `confidence_z_score` | 1.96 | Z-score for 95% confidence intervals | 1.28-2.58 | 90-99% confidence |
| `confidence_level_min` | 60% | Minimum confidence level for forecasts | 50-80% | Reliability floor |
| `confidence_level_max` | 90% | Maximum confidence level for forecasts | 80-99% | Reliability ceiling |
| `forecast_min_pct` | 50% | Minimum forecast as % of recent average | 20-80% | Forecast floor |
| `trend_forecast_factor` | 30% | Weight of trend component in forecasts | 10-50% | Trend influence |

### **Moving Averages & Windows**
| Parameter | Current Value | Description | Range | Smoothing Effect |
|-----------|---------------|-------------|-------|------------------|
| `moving_average_window` | 4 | Window size for moving average calculations | 3-12 | More/less smoothing |
| `rolling_analysis_window` | 12 | Rolling window for performance analysis | 6-26 | Analysis granularity |

---

## 🏪 **STORE-SPECIFIC CONFIGURATION**

### **Multi-Store Parameters**
| Parameter | Description | Inheritance | Override Level |
|-----------|-------------|-------------|----------------|
| `store_specific_thresholds` | JSON field for store-specific overrides | Global → Store | Individual stores |
| `regional_performance_weights` | Weight adjustments by region/store type | System → Region | Store groups |
| `seasonal_adjustment_factors` | Seasonal multipliers by store location | Global → Seasonal | Monthly/quarterly |

---

## 🔧 **SYSTEM PERFORMANCE PARAMETERS**

### **Query & Processing Limits**
| Parameter | Current Value | Description | Impact | Tuning Notes |
|-----------|---------------|-------------|--------|--------------|
| `top_performers_limit` | 3 | Number of top performers to display | UI performance | User experience |
| `batch_processing_size` | 100 | Records processed per batch | Memory usage | Balance speed/memory |
| `query_timeout_seconds` | 30 | Maximum query execution time | Reliability | Prevent hangs |
| `cache_refresh_minutes` | 60 | Minutes between cache refreshes | Performance | Balance speed/freshness |

---

## 📋 **CONFIGURATION MANAGEMENT**

### **Currently Available Tables**
- ✅ `executive_dashboard_configuration` - Executive dashboard settings
- ✅ `business_analytics_configuration` - Business analytics thresholds  
- ❌ `labor_cost_configuration` - **MISSING** (needs creation)
- ❌ `system_performance_configuration` - **MISSING** (future enhancement)

### **Configuration Hierarchy**
1. **System Defaults** → Hardcoded fallback values
2. **Global Configuration** → Database table defaults
3. **User Configuration** → User-specific overrides
4. **Store Configuration** → Store-specific overrides (JSON fields)

### **Configuration UI Status**
- ❌ **Configuration Management Dashboard** - Not built
- ❌ **Threshold Setting Forms** - Not built
- ❌ **Store-Specific Override Interface** - Not built
- ❌ **Configuration Testing & Validation** - Not built
- ❌ **Configuration Backup/Restore** - Not built

---

## 🎯 **IMPLEMENTATION PRIORITY**

### **Phase 1: Critical Business Parameters**
1. Health score thresholds (revenue tiers, YoY thresholds, utilization bands)
2. Analysis periods (query limits, historical weeks, rolling windows)
3. Performance alert thresholds (decline/growth percentages)

### **Phase 2: Statistical & Forecasting**
1. Confidence intervals and statistical parameters
2. Forecasting weights and minimum thresholds
3. Moving average windows and smoothing factors

### **Phase 3: System Performance**
1. Query limits and batch sizes
2. Cache refresh intervals
3. Timeout parameters

### **Phase 4: User Interface**
1. Configuration management dashboard
2. Real-time configuration testing
3. Store-specific override management

---

*Last Updated: September 6, 2025*  
*Status: Audit Complete - Implementation Pending*  
*Next: Build configuration management UI*