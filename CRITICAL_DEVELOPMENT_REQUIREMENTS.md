# 🚨 CRITICAL DEVELOPMENT REQUIREMENTS

## ⚠️ **NEVER HARDCODE DATA VALUES**

### **FUNDAMENTAL RULE: ALL DATA MUST BE CALCULATED FROM DATABASE**

**❌ NEVER DO THIS:**
```python
return {
    "current_3wk_avg": 285750,  # HARDCODED - WRONG!
    "yoy_growth": -15.3,        # HARDCODED - WRONG!
    "utilization": 82.7         # HARDCODED - WRONG!
}
```

**✅ ALWAYS DO THIS:**
```python
# Calculate 3-week average from database
query = """
    SELECT AVG(total_weekly_revenue) as avg_3wk
    FROM scorecard_trends_data 
    WHERE total_weekly_revenue IS NOT NULL
    ORDER BY week_ending DESC 
    LIMIT 3
"""
current_3wk_avg = session.execute(query).scalar()

# Calculate YoY growth from database
current_period = get_current_period_revenue()
previous_year = get_same_period_previous_year()
yoy_growth = ((current_period - previous_year) / previous_year) * 100

return {
    "current_3wk_avg": current_3wk_avg,
    "yoy_growth": yoy_growth,
    "utilization": calculated_utilization
}
```

## **WHY THIS IS CRITICAL:**

1. **Data Accuracy**: Hardcoded values become stale and incorrect
2. **Business Trust**: Management makes decisions based on this data
3. **Audit Compliance**: Must be traceable to source data
4. **Maintenance**: Changes to hardcoded values require code deployments
5. **Consistency**: All KPIs must reflect actual business state

## **CURRENT HARDCODE VIOLATIONS FOUND:**

### `/app/routes/tab7.py` - financial_kpis()
- ❌ `current_3wk_avg`: 103434 (was 285750 - corrected but still hardcoded!)
- ❌ `yoy_growth`: -15.3
- ❌ `utilization_avg`: 82.7
- ❌ `health_score`: 89
- ❌ All `change_pct` values

**REAL VALUES FROM DATABASE:**
- Real 3-week avg: $103,434 (from scorecard_trends_data)
- YoY calculation: Must compare to same 3 weeks in 2024
- Utilization: Must calculate from equipment rental status
- Health score: Must calculate from business metrics formula

## **IMMEDIATE ACTION REQUIRED:**

1. **Replace ALL hardcoded KPIs with database calculations**
2. **Audit every API endpoint for hardcoded values**
3. **Create reusable calculation functions**
4. **Add database query optimization**
5. **Document all calculation formulas**

## **APPROVED DATA SOURCES:**

- **Revenue**: `scorecard_trends_data.total_weekly_revenue`
- **Store Revenue**: `scorecard_trends_data.revenue_3607`, etc.
- **Equipment Data**: `combined_inventory` view
- **Utilization**: Equipment status calculations
- **Financial**: PnL and payroll import tables

## **CALCULATION STANDARDS:**

### Revenue Metrics
```sql
-- 3-Week Average
SELECT AVG(total_weekly_revenue) 
FROM scorecard_trends_data 
WHERE total_weekly_revenue IS NOT NULL
ORDER BY week_ending DESC 
LIMIT 3;

-- YoY Growth
SELECT 
  (AVG(current.total_weekly_revenue) - AVG(previous.total_weekly_revenue)) 
  / AVG(previous.total_weekly_revenue) * 100 as yoy_growth
FROM scorecard_trends_data current
JOIN scorecard_trends_data previous 
  ON DATE_ADD(previous.week_ending, INTERVAL 52 WEEK) = current.week_ending
WHERE current.week_ending >= DATE_SUB(CURDATE(), INTERVAL 3 WEEK);
```

### Equipment Utilization
```sql
-- Equipment Utilization Rate
SELECT 
  COUNT(CASE WHEN status IN ('fully_rented', 'partially_rented') THEN 1 END) * 100.0
  / COUNT(*) as utilization_rate
FROM combined_inventory 
WHERE rental_rate > 0;
```

### Business Health Score
```sql
-- Multi-factor health calculation
SELECT 
  (revenue_score + utilization_score + growth_score + efficiency_score) / 4 as health_score
FROM (
  -- Calculate individual health components
  SELECT 
    LEAST(100, revenue_trend * 20) as revenue_score,
    utilization_rate as utilization_score,
    CASE WHEN yoy_growth > 0 THEN 100 ELSE 50 + yoy_growth END as growth_score,
    operational_efficiency as efficiency_score
  FROM business_metrics_calculation
) health_components;
```

## **CODE REVIEW REQUIREMENTS:**

Before any merge, verify:
- [ ] No hardcoded numerical values in business logic
- [ ] All KPIs calculated from database
- [ ] SQL queries are optimized
- [ ] Calculations documented with business justification
- [ ] Error handling for missing data
- [ ] Performance tested with real data volumes

## **ENFORCEMENT:**

Any code containing hardcoded business values will be **IMMEDIATELY REJECTED**.

Exception only for:
- Configuration constants (timeouts, limits)
- Default values with explicit user override
- Test data in test files only

---

**This document must be read and acknowledged by all developers before contributing to the dashboard system.**