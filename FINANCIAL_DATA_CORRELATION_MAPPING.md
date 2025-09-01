# 📊 Financial Data Correlation Mapping for Minnesota Equipment Rental Business

**Created**: August 31, 2025  
**Business Context**: A1 Rent It (Construction - 70%) + Broadway Tent & Event (Events - 30%)

---

## 🏢 **Store Location Mapping**

### **Store Code Identification**
- **3607** = Wayzata (Lake Minnetonka area, upscale events, sailing season)
- **6800** = Brooklyn Park (Mixed residential/commercial, diverse demographics)
- **728** = Fridley (Industrial corridor, construction projects)  
- **8101** = Elk River (Rural/suburban, outdoor events, agricultural support)

---

## 📈 **Financial Database Structure Analysis**

### **1. ScorecardTrendsData (Executive KPIs - Weekly)**

**Primary Revenue Metrics:**
- `total_weekly_revenue` - **Company-wide weekly revenue across all stores**
- `revenue_3607` - **Wayzata weekly revenue** (tent/event focused)
- `revenue_6800` - **Brooklyn Park weekly revenue** (mixed market)
- `revenue_728` - **Fridley weekly revenue** (construction focused)
- `revenue_8101` - **Elk River weekly revenue** (rural/agricultural)

**Business Activity Indicators:**
- `new_contracts_3607/6800/728/8101` - **New contract volume by store** (demand indicator)
- `deliveries_scheduled_8101` - **Elk River delivery logistics** (operational efficiency)
- `open_quotes_8101` - **Elk River sales pipeline** (future revenue predictor)

**Forward-Looking Revenue (Predictive Indicators):**
- `reservation_next14_3607/6800/728/8101` - **Next 14 days booked revenue by store**
- `total_reservation_3607/6800/728/8101` - **Total future bookings by store**

**Financial Health Indicators:**
- `ar_over_45_days_percent` - **Accounts receivable aging** (cash flow risk)
- `total_discount` - **Company-wide discounting** (margin pressure indicator)
- `total_ar_cash_customers` - **Cash customer receivables** (collection efficiency)

### **2. PayrollTrendsData (Labor Efficiency - Weekly by Store)**

**Revenue Performance:**
- `rental_revenue` - **Pure equipment rental income** (core business metric)
- `all_revenue` - **Total revenue including sales, fees, extras**

**Labor Cost Structure:**
- `payroll_amount` - **Total weekly payroll cost per store**
- `wage_hours` - **Total labor hours worked per store**

**Calculated Performance Ratios (Already Implemented):**
- `labor_cost_ratio` - **Payroll as % of all revenue** (efficiency metric)
- `revenue_per_hour` - **Revenue generated per labor hour**
- `avg_hourly_rate` - **Average wage rate per store**
- `gross_profit` - **Revenue minus payroll costs**
- `rental_revenue_ratio` - **Equipment rental % of total revenue**

### **3. PLData (Profit & Loss - Monthly)**

**Chart of Accounts Structure:**
- `account_code` - **GL account identifier** (revenue, expense, asset categories)
- `account_name` - **Account description** (specific revenue/expense types)
- `period_month` - **Accounting period** (monthly P&L breakdown)
- `period_year` - **Fiscal year**
- `amount` - **Dollar amount for the account**
- `percentage` - **Percentage of total revenue/expenses**
- `category` - **High-level grouping** (Revenue, COGS, Operating Expenses, etc.)

---

## 🔗 **Database Correlation Mapping**

### **Revenue Correlation Chain**

**Executive Scorecard → POS → RFID → Actual Equipment**
```
ScorecardTrendsData.revenue_3607 
    ↓ correlates with
POSTransaction.rent_amt (WHERE store_no = '3607')
    ↓ correlates with  
POSTransactionItem.price × qty (filtered by due_date)
    ↓ correlates with
POSEquipment.turnover_ytd (WHERE current_store = '3607')
    ↓ correlates with
ItemMaster.turnover_ytd (WHERE current_store = '3607')
```

**Key Correlation Points:**
- **Weekly scorecard revenue** should match **sum of POS transaction totals**
- **POS equipment turnover** should align with **RFID item turnover**
- **Reservation amounts** predict **future POS transaction volume**

### **Labor Efficiency Correlations**

**Payroll → Revenue → Equipment Utilization**
```
PayrollTrendsData.payroll_amount (by store)
    ↓ efficiency measured by
PayrollTrendsData.revenue_per_hour
    ↓ driven by
POSTransaction volume and value
    ↓ supported by
ItemMaster equipment availability and utilization
    ↓ optimized through
RFID tracking of equipment status and location
```

### **Equipment Category Performance Mapping**

**Business Mix Analysis:**
```sql
-- A1 Rent It (Construction) Equipment Identification
SELECT im.*, pe.category, pe.department
FROM id_item_master im
JOIN pos_rfid_correlations prc ON im.rental_class_num = prc.rfid_rental_class_num
JOIN pos_equipment pe ON prc.pos_item_num = pe.item_num
WHERE pe.category IN ('Construction', 'Tools', 'Power Equipment', 'Excavation')
   OR pe.name LIKE '%excavator%' OR pe.name LIKE '%skid%' OR pe.name LIKE '%drill%'

-- Broadway Tent & Event Equipment Identification  
SELECT im.*, pe.category, pe.department
FROM id_item_master im
JOIN pos_rfid_correlations prc ON im.rental_class_num = prc.rfid_rental_class_num
JOIN pos_equipment pe ON prc.pos_item_num = pe.item_num
WHERE pe.category IN ('Tents', 'Tables', 'Chairs', 'Staging', 'Events')
   OR pe.name LIKE '%tent%' OR pe.name LIKE '%table%' OR pe.name LIKE '%chair%'
```

---

## 📊 **Financial Analysis Correlations**

### **Store Performance Analysis**

**Revenue Driver Identification:**
- **Wayzata (3607)**: High `reservation_next14` = strong event booking pipeline
- **Brooklyn Park (6800)**: High `new_contracts` = market penetration success  
- **Fridley (728)**: High `rental_revenue_ratio` = pure equipment focus
- **Elk River (8101)**: High `deliveries_scheduled` = logistics-dependent revenue

**Profitability Analysis:**
```sql
-- Store profitability comparison
SELECT 
    store_code,
    AVG(all_revenue) as avg_weekly_revenue,
    AVG(payroll_amount) as avg_weekly_payroll,
    AVG(labor_cost_ratio) as avg_labor_ratio,
    AVG(revenue_per_hour) as avg_revenue_per_hour
FROM (
    -- Combine scorecard and payroll data
    SELECT '3607' as store_code, std.revenue_3607 as all_revenue, 
           ptd.payroll_amount, ptd.labor_cost_ratio, ptd.revenue_per_hour
    FROM scorecard_trends_data std
    JOIN payroll_trends_data ptd ON std.week_ending = ptd.week_ending 
    WHERE ptd.location_code = '3607'
) store_metrics
GROUP BY store_code
```

### **Seasonal Pattern Correlation**

**Minnesota Business Cycles:**
- **Spring (March-May)**: Construction equipment demand rises with building season
- **Summer (June-August)**: Peak tent/event season + continued construction activity  
- **Fall (September-November)**: Event season wind-down, construction completion rush
- **Winter (December-February)**: Maintenance season, indoor event equipment

**Weather Impact Correlation:**
```sql
-- Weather correlation with revenue patterns
SELECT 
    MONTH(std.week_ending) as month,
    AVG(std.total_weekly_revenue) as avg_revenue,
    AVG(ptd.rental_revenue_ratio) as equipment_focus,
    -- Construction vs Event mix by season
    (std.revenue_728 + std.revenue_6800) / std.total_weekly_revenue as construction_ratio,
    (std.revenue_3607 + std.revenue_8101) / std.total_weekly_revenue as event_ratio
FROM scorecard_trends_data std
JOIN payroll_trends_data ptd ON std.week_ending = ptd.week_ending
GROUP BY MONTH(std.week_ending)
ORDER BY month
```

### **Leading vs Lagging Indicators**

**Leading Indicators (Predictive - 2-4 weeks ahead):**
- `reservation_next14_[store]` - **Direct revenue predictor**
- `new_contracts_[store]` - **Pipeline volume indicator**  
- `open_quotes_8101` - **Future sales potential**
- Building permits data - **Construction equipment demand**
- Event calendar data - **Tent/party equipment demand**

**Lagging Indicators (Historical - Performance measurement):**
- `total_weekly_revenue` - **Realized performance**
- `ar_over_45_days_percent` - **Collection efficiency**
- `labor_cost_ratio` - **Operational efficiency**
- `total_discount` - **Margin pressure trends**
- Equipment `turnover_ytd` - **Asset performance**

### **Financial Health Metrics**

**Cash Flow Indicators:**
- `total_ar_cash_customers` - **Immediate collection potential**
- `ar_over_45_days_percent` - **Collection risk assessment**
- `reservation_next14_[total]` - **Near-term cash flow prediction**

**Margin Analysis:**
- `total_discount / total_weekly_revenue` - **Discount pressure**
- `payroll_amount / all_revenue` - **Labor efficiency**
- `rental_revenue / all_revenue` - **Core business focus**

---

## 🎯 **Implementation Roadmap Integration**

### **Phase 3A: Data Correlation Engine (Day 1)**

**Morning Tasks:**
1. **Validate Financial Data Integrity**
   ```sql
   -- Check revenue reconciliation between scorecard and POS
   SELECT 
       std.week_ending,
       std.total_weekly_revenue as scorecard_revenue,
       SUM(pt.total) as pos_revenue,
       ABS(std.total_weekly_revenue - SUM(pt.total)) as variance
   FROM scorecard_trends_data std
   LEFT JOIN pos_transactions pt ON YEARWEEK(pt.contract_date) = YEARWEEK(std.week_ending)
   WHERE ABS(std.total_weekly_revenue - SUM(pt.total)) > 1000  -- Flag large variances
   ```

2. **Implement Equipment Categorization**
   ```python
   # Automatic A1 Rent It vs Broadway Tent & Event classification
   def categorize_equipment(item_name, category, department):
       construction_keywords = ['excavator', 'skid', 'drill', 'saw', 'compressor', 'generator']
       event_keywords = ['tent', 'table', 'chair', 'stage', 'lighting', 'sound']
       
       if any(keyword in item_name.lower() for keyword in construction_keywords):
           return 'A1_RentIt_Construction'
       elif any(keyword in item_name.lower() for keyword in event_keywords):
           return 'Broadway_TentEvent' 
       else:
           return 'Mixed_Category'
   ```

**Afternoon Tasks:**
1. **Create Store Performance Benchmarking**
2. **Implement 3-week Rolling Averages for Financial Smoothing**
3. **Build Revenue Correlation Dashboard**

### **Phase 3B: Advanced Analytics (Day 2)**

**Morning Tasks:**
1. **Implement Predictive Financial Models**
   - Reservation pipeline → Revenue forecasting
   - Labor hours → Capacity planning
   - Seasonal adjustments → Inventory optimization

2. **Minnesota-Specific Analytics**
   - Weather correlation with equipment demand
   - Event calendar integration with tent/staging bookings
   - Construction permit correlation with tool rentals

**Afternoon Tasks:**
1. **Business Intelligence Dashboard**
   - Store comparison analytics
   - Equipment category performance
   - Financial health scoring
   - Predictive alerts and recommendations

---

## 🏆 **Expected Business Insights**

### **Revenue Optimization**
- **Peak Performance Identification**: Which store/equipment combo generates highest revenue per hour
- **Seasonal Planning**: Equipment mix optimization by Minnesota weather patterns
- **Pricing Intelligence**: Optimal pricing by equipment type and demand patterns

### **Operational Excellence**
- **Labor Efficiency**: Revenue per hour benchmarking across all 4 stores
- **Equipment Utilization**: Turnover optimization by location and season
- **Cash Flow Management**: AR aging pattern analysis and collection optimization

### **Strategic Planning** 
- **Market Expansion**: Equipment category growth opportunities by store location
- **Investment Decisions**: ROI analysis for new equipment purchases
- **Competitive Positioning**: Performance benchmarking against industry standards

This comprehensive financial data correlation mapping provides the foundation for sophisticated business intelligence that will drive significant improvements in profitability, efficiency, and strategic decision-making across your Minnesota equipment rental operations. 🎯