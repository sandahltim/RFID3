# 🎯 DEPLOYMENT SIDE QUESTS & REQUIREMENTS
*Critical tasks that must be completed for hardcode fixes to work in production*

## 🚨 CRITICAL DATABASE MIGRATIONS NEEDED

### **1. labor_cost_configuration Table - MISSING**
**Status:** ❌ NOT CREATED  
**Required For:** Labor cost configuration system to work  
**Priority:** CRITICAL - System will fallback but won't save user configurations

```sql
CREATE TABLE labor_cost_configuration (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL DEFAULT 'default_user',
    config_name VARCHAR(100) NOT NULL DEFAULT 'default',
    high_labor_cost_threshold DECIMAL(5,2) DEFAULT 35.0,
    labor_cost_warning_level DECIMAL(5,2) DEFAULT 30.0,
    target_labor_cost_ratio DECIMAL(5,2) DEFAULT 25.0,
    efficiency_baseline DECIMAL(5,2) DEFAULT 100.0,
    store_specific_thresholds JSON DEFAULT NULL,
    minimum_hours_for_analysis DECIMAL(5,2) DEFAULT 1.0,
    labor_efficiency_weight DECIMAL(3,2) DEFAULT 0.6,
    cost_control_weight DECIMAL(3,2) DEFAULT 0.4,
    batch_processing_size INT DEFAULT 100,
    progress_checkpoint_interval INT DEFAULT 500,
    query_timeout_seconds INT DEFAULT 30,
    enable_high_cost_alerts BOOLEAN DEFAULT TRUE,
    enable_trend_alerts BOOLEAN DEFAULT TRUE,
    alert_frequency VARCHAR(20) DEFAULT 'weekly',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_config (user_id, config_name)
);
```

### **2. business_analytics_configuration Table - CREATED**
**Status:** ✅ CREATED  
**Required For:** Business analytics threshold configuration system  
**Priority:** COMPLETED - Table created with proper column names

```sql
CREATE TABLE business_analytics_configuration (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL DEFAULT 'default_user',
    config_name VARCHAR(100) NOT NULL DEFAULT 'default',
    equipment_underperformer_threshold DECIMAL(10,2) DEFAULT 50.0,
    low_turnover_threshold DECIMAL(10,2) DEFAULT 25.0,
    high_value_threshold DECIMAL(10,2) DEFAULT 500.0,
    low_usage_threshold DECIMAL(10,2) DEFAULT 100.0,
    resale_priority_threshold DECIMAL(10,2) DEFAULT 10.0,
    ar_aging_low_threshold DECIMAL(5,2) DEFAULT 5.0,
    ar_aging_medium_threshold DECIMAL(5,2) DEFAULT 15.0,
    revenue_concentration_risk_threshold DECIMAL(5,3) DEFAULT 0.400,
    declining_trend_threshold DECIMAL(5,3) DEFAULT -0.100,
    minimum_data_points_correlation INT DEFAULT 10,
    confidence_threshold DECIMAL(5,3) DEFAULT 0.950,
    store_specific_thresholds JSON DEFAULT NULL,
    enable_underperformance_alerts BOOLEAN DEFAULT TRUE,
    enable_high_value_alerts BOOLEAN DEFAULT TRUE,
    enable_ar_aging_alerts BOOLEAN DEFAULT TRUE,
    enable_concentration_risk_alerts BOOLEAN DEFAULT TRUE,
    alert_frequency VARCHAR(20) DEFAULT 'weekly',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_config (user_id, config_name)
);
```

### **3. executive_dashboard_configuration Table - CREATED**
**Status:** ✅ CREATED  
**Required For:** Executive dashboard health scoring and forecasting configuration  
**Priority:** COMPLETED - Table created with comprehensive health scoring parameters

```sql
CREATE TABLE executive_dashboard_configuration (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL DEFAULT 'default_user',
    config_name VARCHAR(100) NOT NULL DEFAULT 'default',
    base_health_score DECIMAL(5,2) DEFAULT 75.0,
    min_health_score DECIMAL(5,2) DEFAULT 0.0,
    max_health_score DECIMAL(5,2) DEFAULT 100.0,
    strong_positive_trend_threshold DECIMAL(5,2) DEFAULT 5.0,
    strong_positive_trend_points INT DEFAULT 15,
    weak_positive_trend_points INT DEFAULT 5,
    strong_negative_trend_threshold DECIMAL(5,2) DEFAULT -5.0,
    strong_negative_trend_points INT DEFAULT -15,
    weak_negative_trend_points INT DEFAULT -5,
    strong_growth_threshold DECIMAL(5,2) DEFAULT 10.0,
    strong_growth_points INT DEFAULT 10,
    weak_growth_points INT DEFAULT 5,
    strong_decline_threshold DECIMAL(5,2) DEFAULT -10.0,
    strong_decline_points INT DEFAULT -15,
    weak_decline_points INT DEFAULT -5,
    default_forecast_horizon_weeks INT DEFAULT 12,
    default_confidence_level DECIMAL(5,3) DEFAULT 0.950,
    min_forecast_horizon INT DEFAULT 1,
    max_forecast_horizon INT DEFAULT 52,
    store_specific_thresholds JSON DEFAULT NULL,
    enable_health_score_alerts BOOLEAN DEFAULT TRUE,
    enable_trend_alerts BOOLEAN DEFAULT TRUE,
    enable_growth_alerts BOOLEAN DEFAULT TRUE,
    alert_frequency VARCHAR(20) DEFAULT 'weekly',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_config (user_id, config_name)
);
```

## 📋 VERIFICATION CHECKLIST

### **Completed Hardcode Removals:**
- ✅ Store revenue percentages (15.3%, 27.5%, etc.) → `calculate_actual_store_performance()`
- ✅ Rolling window sizes (window=3) → `get_config_value('rolling_window_weeks', 3)`
- ✅ Analysis periods (weeks_back=26) → `get_config_value('default_analysis_weeks', 26)`
- ✅ Labor cost thresholds (35%) → `get_store_labor_threshold(store_code, 'high_threshold')`
- ✅ Efficiency baseline (100) → `config.efficiency_baseline`
- ✅ Business analytics thresholds ($50, $500, etc.) → `config.get_threshold('equipment_underperformer_threshold')`
- ✅ AR aging thresholds (5%, 15%) → `config.get_threshold('ar_aging_low_threshold')`
- ✅ Revenue concentration risk (40%) → `config.get_threshold('revenue_concentration_risk_threshold')`
- ✅ Executive dashboard health scores (75, growth > 10, etc.) → `config.get_store_threshold('default', 'base_health_score')`
- ✅ Executive dashboard forecasting (12 weeks, 0.95 confidence) → configurable horizon and confidence

### **Still Need To Verify:**
- 🔍 Executive dashboard analysis periods (26 weeks) - newly discovered
- 🔍 RFID coverage data (1.78%, 290, 16259) - newly discovered  
- 🔍 Predictive analytics parameters (4, 12, 52 weeks)
- 🔍 Side quest hardcodes: window=3 in financial_analytics_service.py lines 455, 1456, 1480
- 🔍 Side quest hardcodes: batch_size=100 in payroll_import_service.py line 296
- 🔍 All batch sizes and query limits
- 🔍 Cache timeouts and intervals

## 🛠 AGENT SIDE QUESTS

### **general-purpose Agent:**
- **PRIORITY:** Systematic hardcode audit across all 60+ files identified
- Search for patterns: `window=3`, `batch_size=100`, `threshold > 35`, etc.
- Create comprehensive list of ALL remaining hardcoded business values

### **database-correlation-analyst Agent:**
- Review database schema for remaining hardcoded values
- Verify all FK relationships for new config tables
- Analyze query performance impact of config lookups

### **testing-agent Agent:**  
- Create comprehensive tests for all config systems
- Test fallback behavior when tables don't exist
- Validate store-specific threshold logic

### **deployment-agent Agent:**
- Create database migration scripts
- Plan rollout strategy for config table creation
- Document rollback procedures

### **ui-ux-evaluator Agent:**
- Create user interface for all configuration settings after hardcode removal is complete
- Design configuration management dashboard with tabs for different setting types
- Build forms for: Labor Cost Thresholds, Business Analytics Thresholds, Executive Dashboard Settings, Predictive Analytics Parameters

## 📋 REMAINING HARDCODE FIXES (Side Quests)

### **Priority A: Executive Dashboard Health Scores** *(COMPLETED)*
- ✅ Base health score: `score = 75` → `config.get_store_threshold('default', 'base_health_score')`
- ✅ Growth thresholds: `growth > 10`, `growth < -10` → configurable thresholds
- ✅ Trend thresholds: `trend > 5`, `trend < -5` → configurable thresholds
- ✅ Default forecast horizon: `horizon_weeks = 12` → configurable horizon
- ✅ Default confidence level: `confidence = 0.95` → configurable confidence

### **Priority A1: Executive Dashboard Analysis Periods** *(NEWLY DISCOVERED)*
- ❌ Analysis periods: `26` weeks hardcoded in multiple locations (lines 41, 79, 81, 128)
- ❌ RFID coverage data: `1.78%` correlation hardcoded (line 313)
- ❌ Equipment counts: `290 of 16,259 items` hardcoded (lines 315-316)
- ❌ Data transparency hardcodes need configurable data source tracking

### **Priority B: Predictive Analytics Parameters**
- ❌ Forecast horizons: `4, 12, 52` weeks (hardcoded in predictive_analytics_service.py)
- ❌ Data requirements: `len(results) < 10` minimum (hardcoded)
- ❌ Query limits: `LIMIT 100` records (hardcoded)
- ❌ Coverage threshold: `1.78%` RFID correlation (hardcoded)

### **Priority C: Comprehensive Hardcode Audit Results** *(tab7.py analysis)*

#### **Query Limits - SHOULD_BE_USER_CONFIG**
- ❌ Line 348: `LIMIT 3` → `top_performers_limit`
- ❌ Line 3109,3122,3258: `LIMIT 3` → `dashboard_query_limit`  
- ❌ Line 3533: `LIMIT 12` → `historical_weeks_limit`
- ❌ Line 3686: `LIMIT 24` → `forecast_weeks_limit`
- ❌ Line 1442: `limit(52)` → `max_historical_weeks`

#### **Business Thresholds - SHOULD_BE_USER_CONFIG**
- ❌ Lines 3074-3096: Health Score MockConfig fallback values
- ❌ Lines 3329-3350: Store Performance Configuration duplicates
- ❌ Line 3541: `* 0.9` (10% decline) → `decline_threshold_pct`
- ❌ Line 3550: `* 1.1` (10% growth) → `growth_threshold_pct`
- ❌ Line 3594: `* 2` (200% gap) → `performance_gap_multiplier`

#### **Time Periods & Rolling Windows - SHOULD_BE_USER_CONFIG**
- ❌ Line 2757: `weeks_back = 52` → `analysis_period_weeks`
- ❌ Line 2758,2761: `rolling_window = 12` → `rolling_window_size`
- ❌ Line 1461: `window=4` → `moving_average_window`
- ❌ Line 1447: `< 12` → `min_forecast_data_points`

#### **Data Filtering - SHOULD_BE_USER_CONFIG**
- ❌ Line 1258: `sell_price < 5000` → `max_equipment_price`
- ❌ Line 1259: `qty < 10000` → `max_inventory_qty`
- ❌ Line 3165,3615: `rental_rate > 0` → `min_rental_rate`

#### **Statistical Constants - SHOULD_BE_USER_CONFIG**
- ❌ Line 1510,3732: `* 1.96` → `confidence_z_score`
- ❌ Line 3623: `utilization < 40` → `low_utilization_threshold`
- ❌ Line 3635: `utilization > 85` → `high_utilization_threshold`

#### **Legacy Side Quest Hardcodes**
- ❌ Financial Analytics Service:
  - Line 455-456: `df[f'{col}_3wk_avg'] = df[col].rolling(window=3, center=True).mean()`
  - Line 1456-1457: `store_df['profit_3wk_avg'] = store_df['gross_profit'].rolling(window=3)`  
  - Line 1480: `company_df['profit_3wk_avg'] = company_df['gross_profit'].rolling(window=3)`
- ❌ Payroll Import Service:
  - Line 296: `batch_size = 100` (should use configurable value, capped at 200)

### **Priority D: Configuration User Interface** *(After all hardcodes fixed)*
- ❌ Create configuration management dashboard
- ❌ Build forms for all threshold settings
- ❌ Add store-specific override capabilities
- ❌ Implement configuration validation and testing
- ❌ Create configuration backup/restore functionality

### **Priority E: Data Lag Fix** *(NEWLY IDENTIFIED)*
**Status:** ❌ IDENTIFIED - Needs Implementation  
**Priority:** MEDIUM - Affects KPI accuracy but system functions  
**Impact:** Executive dashboard shows outdated data

**Issue Description:**
- Database has data through: 2025-08-31
- Current date: 2025-09-06
- Gap: ~6 days of missing recent data
- Total Revenue shows $103,434 (database) vs $109,955 (CSV with current data)
- Gap of $6,521 suggests newer data available but not imported

**Root Cause:**
- CSV import process not automated
- scorecard_trends_data table not updating with current week data
- Data pipeline lag between business operations and database

**Action Items:**
- ❌ Identify and fix data import automation
- ❌ Add data freshness indicators to dashboard  
- ❌ Create monitoring for data lag detection
- ❌ Update KPI calculations to handle data lag gracefully

### **Priority F: Store Selection Trend Consistency** *(NEWLY IDENTIFIED)*
**Status:** ✅ PARTIALLY FIXED - Revenue trend fixed, others need same treatment  
**Priority:** LOW-MEDIUM - Affects individual store view accuracy  
**Impact:** Store selection shows inconsistent trend data

**Issue Description:**
- Individual store selection uses different code path than "All Stores" view
- Some trends update correctly, others remain hardcoded when switching stores
- Functions: `updateKPIs()` vs `updateKPIDisplays()` inconsistency

**Action Items:**
- ✅ Fixed revenue trend for individual stores 
- ❌ Fix utilization trend (+2.1% hardcoded) for store selection
- ❌ Fix health trend ("Excellent" hardcoded) for store selection  
- ❌ Ensure all trend calculations use same logic across views

## 📊 IMPACT SUMMARY

**Fixed So Far:**
- ✅ 3 foundational calculation systems  
- ✅ 100+ individual hardcoded values replaced
- ✅ Store-specific configuration architecture

**Immediate Issues:**
- ❌ labor_cost_configuration table missing - prevents user config saves
- ❌ Database migrations not created
- ❌ No deployment documentation

**Next Steps:**
1. CREATE the missing table immediately
2. Test table creation and config system 
3. Continue hardcode audit for remaining values
4. Document all migration requirements