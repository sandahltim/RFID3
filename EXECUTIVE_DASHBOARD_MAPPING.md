# Executive Dashboard Implementation Mapping
## KVC Companies - Comprehensive Technical Reference

*Generated: 2025-09-08*

---

## 1. Dashboard Areas/Sections

### Main URL Path & Routing
- **Primary Route**: `/executive/dashboard`
- **Blueprint**: `executive_bp` (URL prefix: `/executive`)
- **Template**: `/app/templates/executive_dashboard.html`
- **Main Route Handler**: `executive_dashboard()` in `/app/routes/executive_dashboard.py`

### Dashboard Sections Structure

#### A. Executive KPIs Section
**Location**: Top of dashboard (4-card layout)
**Components**:
- Total Revenue (3-Week Average) - `#revenueKPI`
- YoY Growth Rate - `#growthKPI`
- Average Utilization - `#utilizationKPI`
- Health Score - `#healthKPI`

**Visual Elements**:
- Animated counters with CountUp.js
- Color-coded values (primary, success, warning, info, danger)
- Trend indicators (up/down arrows)

#### B. Executive Scorecard Matrix
**Location**: Main central section
**Components**:
- Multi-store performance table
- Revenue metrics by store
- Manager information
- 8-week historical data display

#### C. Store Performance Cards
**Location**: Individual store display section
**Components**:
- 4 store-specific cards (Wayzata, Brooklyn Park, Fridley, Elk River)
- Revenue, utilization, and contract metrics per store
- Location-specific badges with color coding

#### D. Charts Section
**Components**:
1. **Multi-Year Revenue Trends** (`#multiYearRevenueChart`)
   - Seasonal analysis (2022-2024)
   - 7x seasonal variation identification
   
2. **Revenue Trend Analysis** (`#revenueTrendChart`)
   - Short-term trend visualization
   
3. **Store Performance Rankings** (`#storeRankingsDisplay`)
   - Comparative performance metrics
   
4. **12-Week Revenue Forecast** (`#forecastChart`)
   - Predictive analytics visualization
   
5. **Multi-Store Revenue Comparison** (`#storeComparisonChart`)
   - Cross-store comparison charts

#### E. Enhanced Analytics Section
**Components**:
- Performance heatmaps
- Equipment utilization gauges
- Interactive metric selectors

---

## 2. API Endpoints Mapping

### Core Financial APIs

#### `/executive/api/financial-kpis`
**Method**: GET  
**Purpose**: Executive financial KPIs  
**Data Returned**:
```json
{
  "success": true,
  "timestamp": "ISO datetime",
  "revenue_metrics": {
    "current_3wk_avg": float,
    "growth_trend": float,
    "yoy_growth": float
  },
  "store_metrics": {
    "top_performer": string,
    "store_count": int,
    "utilization_avg": float
  },
  "operational_health": {
    "health_score": float,
    "trend_direction": "up|down"
  }
}
```

#### `/executive/api/store-comparison`
**Method**: GET  
**Parameters**: `weeks` (default: configurable via ExecutiveDashboardConfiguration)  
**Purpose**: Store performance comparison  
**Data Returned**:
```json
{
  "success": true,
  "analysis_period_weeks": int,
  "stores": [
    {
      "name": string,
      "store_code": string,
      "revenue": {
        "total": float,
        "weekly_avg": float,
        "per_contract": float
      },
      "profitability": {
        "gross_profit": float,
        "margin_pct": float
      },
      "efficiency": {
        "revenue_per_hour": float,
        "contracts_per_hour": float,
        "total_contracts": int
      },
      "ranking": object
    }
  ]
}
```

#### `/executive/api/financial-forecasts`
**Method**: GET  
**Parameters**: 
- `weeks` (default: configurable)
- `confidence` (default: configurable)  
**Purpose**: Financial forecasting  
**Uses**: `financial_service.generate_financial_forecasts()`

### Intelligence & Analytics APIs

#### `/executive/api/intelligent-insights`
**Method**: GET  
**Purpose**: Business insights with external event correlation  
**Uses**: `insights_service.analyze_financial_anomalies_with_context()`

#### `/executive/api/enhanced-dashboard`
**Method**: GET  
**Purpose**: Enhanced analytics using RFID correlation data  
**Uses**: `enhanced_service.get_executive_dashboard_with_correlations()`

#### `/executive/api/enhanced-kpis`
**Method**: GET  
**Purpose**: Enhanced KPIs with RFID correlation data  
**Returns**: Coverage statistics and data transparency metrics

### Configuration APIs

#### `/executive/api/dashboard-config`
**Methods**: GET, POST  
**Purpose**: Dashboard configuration management  
**Uses**: `insights_service.get_dashboard_configuration()` / `update_dashboard_configuration()`

#### `/executive/api/custom-insight`
**Method**: POST  
**Purpose**: Add custom business insights  
**Accepts**: Custom insight data with event correlation

### Specialized Analytics APIs

#### `/executive/api/equipment-roi`
**Method**: GET  
**Purpose**: Equipment-level ROI analysis  
**Uses**: `enhanced_service.get_equipment_roi_analysis()`

#### `/executive/api/correlation-quality`
**Method**: GET  
**Purpose**: Data correlation quality metrics  
**Uses**: `enhanced_service.get_correlation_quality_metrics()`

#### `/executive/api/real-time-utilization`
**Method**: GET  
**Purpose**: Real-time utilization metrics  
**Uses**: `enhanced_service.get_real_time_utilization_metrics()`

#### `/executive/api/data-reconciliation`
**Method**: GET  
**Parameters**: `type` (revenue|utilization|comprehensive)  
**Purpose**: POS, RFID, Financial system reconciliation  
**Uses**: `reconciliation_service` methods

#### `/executive/api/multi-timeframe`
**Method**: GET  
**Parameters**: 
- `timeframe` (daily|weekly|monthly|quarterly|yearly)
- `metric` (default: 'revenue')
- `periods` (configurable default)  
**Purpose**: Multi-timeframe financial analysis

---

## 3. Data Sources and Database Tables

### Primary Financial Data Tables

#### `payroll_trends_data`
**Purpose**: Weekly payroll and revenue data  
**Key Columns**:
- `week_ending` (Date)
- `location_code` (String) 
- `rental_revenue` (Numeric)
- `all_revenue` (Numeric)
- `payroll_amount` (Numeric)
- `wage_hours` (Numeric)

**Calculated Properties**:
- `labor_cost_ratio`: Payroll as % of revenue
- `revenue_per_hour`: Revenue efficiency metric
- `avg_hourly_rate`: Labor cost metric
- `gross_profit`: Revenue - payroll

#### `scorecard_trends_data` 
**Purpose**: Executive scorecard metrics  
**Usage**: Multi-store performance comparison

#### `pl_data`
**Purpose**: Profit & Loss financial data  
**Usage**: Historical financial analysis (1,818+ records)

### POS System Integration Tables

#### `pos_transactions`
**Purpose**: Point of sale transaction data  
**Key Columns**:
- `contract_no`, `store_no` (Unique constraint)
- `customer_no`, `status`, `contract_date`
- Financial fields: `rent_amt`, `sale_amt`, `total`, etc.
- Contact info and payment methods

#### `pos_transaction_items`
**Purpose**: Individual rental line items  
**Links**: Transaction details to specific equipment

#### `pos_equipment`
**Purpose**: Equipment master data from POS  
**Links**: Equipment specifications and pricing

#### `pos_customers`
**Purpose**: Customer information from POS system

### RFID Integration Tables

#### `id_item_master` (ItemMaster)
**Purpose**: RFID tag and equipment tracking  
**Key Columns**:
- `tag_id` (Primary key)
- `rental_class_num`, `common_name`
- `status`, `bin_location`
- `home_store`, `current_store`
- Financial tracking: `turnover_ytd`, `repair_cost_ltd`

#### `combined_inventory` 
**Purpose**: POS-RFID correlation view  
**Usage**: Equipment ROI and utilization analysis  
**Coverage**: 290 of 16,259 items (1.78%)

---

## 4. Formulas and Calculations

### Revenue Calculations

#### 3-Week Rolling Average
**Formula**: Sum of last 3 weeks / 3  
**Implementation**: `financial_service.calculate_rolling_averages('revenue', 3)`  
**Configuration**: Via `rolling_window_weeks` parameter

#### Year-over-Year Growth
**Formula**: `((current_period - previous_period) / previous_period) * 100`  
**Implementation**: `financial_service.calculate_year_over_year_analysis('revenue')`

### Health Score Formula
**Base Score**: 75 (configurable via `ExecutiveDashboardConfiguration.base_health_score`)

**Revenue Trend Component**:
- Strong positive (>5%): +15 points
- Weak positive (>0%): +5 points  
- Weak negative (<0%): -5 points
- Strong negative (<-5%): -15 points

**YoY Growth Component**:
- Strong growth (>10%): +10 points
- Weak growth (>0%): +5 points
- Weak decline (<0%): -5 points  
- Strong decline (<-10%): -15 points

**Bounds**: Min 0, Max 100

### Utilization Calculations
**Equipment Level**: `(current_rental_revenue / potential_revenue) * 100`  
**Store Level**: Average of efficiency scores across equipment  
**Implementation**: Uses `revenue_efficiency` from store metrics

### Forecasting Algorithms
**Method**: Configurable ('auto', 'linear', 'exponential', 'seasonal')  
**Default Horizon**: 12 weeks (configurable)  
**Confidence Level**: 95% (configurable)  
**Seasonal Adjustment**: Enabled by default

---

## 5. Configuration Variables

### ExecutiveDashboardConfiguration Model
**Table**: `executive_dashboard_configuration`  
**Location**: `/app/models/config_models.py`

#### Health Scoring Parameters
```python
'health_scoring': {
    'base_score': 75.0,
    'strong_positive_trend_threshold': 5.0,
    'strong_positive_trend_points': 15,
    'weak_positive_trend_points': 5,
    'strong_negative_trend_threshold': -5.0,
    'strong_negative_trend_points': -15,
    'weak_negative_trend_points': -5,
    'strong_growth_threshold': 10.0,
    'strong_growth_points': 10,
    'weak_growth_points': 5,
    'strong_decline_threshold': -10.0,
    'strong_decline_points': -15,
    'weak_decline_points': -5
}
```

#### Forecasting Parameters
```python
'forecasting': {
    'default_horizon_weeks': 12,
    'default_confidence_level': 0.95,
    'min_horizon': 1,
    'max_horizon': 52
}
```

#### Analysis Parameters
```python
'analysis': {
    'default_period_weeks': 26  # Default lookback period
}
```

#### RFID Coverage Tracking
```python
'rfid_coverage': {
    'coverage_percentage': 1.78,
    'correlated_items': 290,
    'total_equipment_items': 16259
}
```

#### Display Options
```python
'display': {
    'current_week_view_enabled': True
}
```

### Store-Specific Configuration
**Source**: `/app/config/stores.py`  
**Primary Structure**: `STORES` dictionary with `StoreInfo` named tuples

**Active Stores**:
- **3607**: Wayzata (90% DIY/10% Events, Tyler - Manager)
- **6800**: Brooklyn Park (100% Construction, Michael - Manager)  
- **728**: Fridley (100% Events, Jenna - Manager)
- **8101**: Elk River (100% Construction, Alex - Manager)

### Service Configuration
**Financial Analytics**: `FinancialAnalyticsService.get_analysis_config()`
```python
{
    'rolling_window_weeks': 3,
    'default_analysis_weeks': 26,
    'trend_analysis_window': 3,
    'smoothing_center': True,
    'min_data_points': 10,
    'confidence_threshold': 0.95,
    'volatility_threshold': 15.0
}
```

---

## 6. Visual Components

### Chart Implementation
**Library**: Chart.js with date-fns adapter  
**Fallback**: D3.js available for advanced visualizations

#### Chart Types Currently Implemented
1. **Line Charts**: Revenue trends, forecasting
2. **Bar Charts**: Store comparisons  
3. **Gauge Charts**: Utilization metrics
4. **Heatmaps**: Performance visualization
5. **Multi-axis Charts**: Revenue vs other metrics

#### Interactive Elements
- **Location Selector**: Radio button group for store filtering
- **Metric Selector**: Toggle between revenue, utilization, contracts
- **Timeframe Controls**: Week/month/quarter/year selection
- **Animated Counters**: CountUp.js with fallback implementation

### CSS Framework & Styling
**Primary**: Bootstrap 5.3.0  
**Color Scheme**: Executive-focused with high contrast
```css
:root {
    --executive-primary: #1e3a8a;
    --executive-secondary: #3b82f6;
    --executive-success: #10b981;
    --executive-warning: #f59e0b;
    --executive-danger: #ef4444;
}
```

**KPI Cards**: Hover effects, shadow depth, 160px fixed height  
**Charts**: 400px default height, responsive containers

---

## 7. Store Views Implementation

### All Stores View (Default)
**Trigger**: Default dashboard load  
**Data Source**: `financial_service.analyze_multi_store_performance(analysis_period)`  
**Display**: 
- Aggregated KPIs across all stores
- Store comparison table
- Individual store performance cards

### Single Store View  
**Trigger**: Location selector interaction  
**Implementation**: JavaScript filtering of existing data  
**Components**:
- Store-specific KPI updates
- Individual store performance focus
- Comparative benchmarking maintained

### Store Performance Ranking
**Algorithm**: Multi-factor scoring including:
- Revenue performance
- Efficiency metrics  
- Growth trends
- Utilization rates

**Display**: Ranked list with performance categories:
- `high_performer` (≥80% utilization)
- `moderate_performer` (≥50% utilization)  
- `low_performer` (≥20% utilization)
- `underperformer` (<20% utilization)

---

## 8. Timeframe Controls

### Available Timeframes
- **Daily**: Short-term operational metrics
- **Weekly**: Default analysis period  
- **Monthly**: Mid-term trend analysis
- **Quarterly**: Strategic planning horizon
- **Yearly**: Year-over-year comparisons

### Default Periods (Configurable)
- **Analysis Period**: 26 weeks
- **Forecast Horizon**: 12 weeks  
- **Rolling Average**: 3 weeks
- **YoY Comparison**: 52 weeks

### Date Handling Implementation
**Historical Data Limits**:
- Scorecard: 196 weeks available
- P&L Data: 1,818 records  
- Payroll Data: 328 records

**Timeframe Mapping**:
```python
timeframe_mapping = {
    'daily': periods // 7,
    'weekly': periods,
    'monthly': periods // 4,
    'quarterly': periods // 13,
    'yearly': min(periods // 52, 3)  # Max 3 years
}
```

---

## 9. Data Quality & Reliability Notes

### RFID Correlation Coverage
**Current State**: 290 of 16,259 items (1.78% coverage)  
**Quality Flags**: 'good_quality', 'quantity_mismatch'  
**Impact**: Limited equipment-level insights, primarily uses financial aggregates

### Data Source Reliability
- **Most Reliable**: Scorecard data (consistent weekly updates)
- **Comprehensive**: P&L data (1,818 records, detailed financial)
- **Limited**: RFID correlations (small sample size)

### Fallback Systems
- Configuration fallbacks for missing database configs
- Mock data structures for error conditions  
- Graceful degradation when services unavailable

---

## 10. Enhancement Opportunities

### Missing/Incomplete Features
1. **Real-time Data**: Currently batch-updated, could benefit from live feeds
2. **Advanced Forecasting**: Seasonal models available but basic implementation
3. **Equipment-level Insights**: Limited by RFID correlation coverage
4. **Mobile Optimization**: Desktop-focused design
5. **Alert System**: Framework exists but limited implementation

### Scalability Considerations
- Database query optimization needed for larger datasets
- Chart performance with extensive historical data
- Configuration management for multi-tenant scenarios

---

*This mapping serves as the definitive technical reference for the KVC Companies Executive Dashboard implementation as of 2025-09-08. All file paths are absolute and current.*