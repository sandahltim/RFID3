# Store Timeline Correlation Analysis Report

## Executive Summary

A comprehensive analysis of the database revealed significant data quality issues related to store timelines and correlations. The primary issue is that POS transaction data contains dates that predate actual store opening dates, suggesting either data corruption, incorrect date imports, or legacy data migration issues.

## Key Findings

### 1. Store Timeline Discrepancies

| Store ID | Store Name | Actual Opening | POS Data From | Data Quality Issue |
|----------|------------|---------------|---------------|-------------------|
| 3607 | Wayzata | 2008-01-01 | 2000-01-07 | 47,998 transactions before opening |
| 6800 | Brooklyn Park | 2022-01-01 | 2021-06-08 | 83 transactions before opening |
| 8101 | Fridley | 2022-01-01 | 2002-12-06 | 3 transactions before opening |
| 728 | Elk River | 2024-01-01 | 2014-06-28 | 1 transaction before opening |

### 2. Store Numbering Inconsistency

The system uses multiple store identification schemes:
- **POS System**: Uses numeric codes (1, 2, 3, 4)
- **Financial System**: Uses actual store IDs (3607, 6800, 8101, 728)
- **Mapping Tables**: Attempt to bridge but not consistently applied

### 3. Data Source Reliability

| Data Source | Timeline Accuracy | Notes |
|-------------|------------------|-------|
| POS Transactions | Poor | Contains impossible historical dates |
| Payroll Trends | Good | Aligns with actual store openings |
| Scorecard Trends | Good | Consistent with business operations |
| Financial P&L | Mixed | Uses store IDs as account lines |

## Database Structure Analysis

### Tables with Store Data

1. **Primary Store Tables**
   - `store_master` (newly created) - Single source of truth
   - `store_mappings` - Legacy mapping table
   - `unified_store_mapping` - Attempt at consolidation
   - `pos_store_mapping` - POS-specific mappings

2. **Transaction Tables**
   - `pos_transactions` - 246,361 records with date issues
   - `pos_transaction_items` - Line item details
   - `id_transactions` - RFID transaction data

3. **Financial Tables**
   - `executive_payroll_trends` - Weekly payroll data
   - `executive_scorecard_trends` - Performance metrics
   - `pos_profit_loss` - P&L data with store as account line

4. **Analytics Tables**
   - `bi_store_performance` - Business intelligence metrics
   - `store_correlations` - Cross-store analysis
   - `v_store_performance` - Aggregated view

## Data Quality Issues

### Critical Issues

1. **Historical Data Corruption**
   - Wayzata: 24% of transactions predate store opening
   - Likely caused by year truncation (2010→2000) during import

2. **Future Dates**
   - Multiple transactions dated 2025-2027
   - Indicates date parsing or timezone issues

3. **Missing Relationships**
   - POS transactions use numeric codes not linked to store IDs
   - No foreign key constraints enforcing referential integrity

### Data Integrity Scores

| Store | Data Quality Score | Issue Count |
|-------|-------------------|-------------|
| 3607 (Wayzata) | 76% | 47,998 |
| 6800 (Brooklyn Park) | 99.7% | 83 |
| 8101 (Fridley) | 99.98% | 3 |
| 728 (Elk River) | 99.99% | 1 |

## Correlation Mappings

### Store ID Correlation Matrix

```
POS Code → Store ID → Store Name → Location
1        → 3607     → Wayzata    → Wayzata, MN
2        → 6800     → Brooklyn Park → Brooklyn Park, MN
3        → 8101     → Fridley    → Fridley, MN
4        → 728      → Elk River  → Elk River, MN
```

### Field Correlations Across Tables

| Field Purpose | Table.Column Variations |
|---------------|------------------------|
| Store Identifier | `pos_transactions.store_no`, `payroll_trends.store_id`, `pos_profit_loss.account_line` |
| Transaction Date | `contract_date`, `week_ending`, `import_date`, `created_at` |
| Revenue | `total`, `total_revenue`, `rental_revenue`, `amount` |
| Customer ID | `customer_no`, `contact`, `ordered_by` |

## Recommendations

### Immediate Actions (Priority: HIGH)

1. **Execute Data Cleaning Script**
   ```sql
   -- Run: fix_store_timeline_data.sql
   -- This will correct 48,085 problematic date records
   ```

2. **Implement Store Master Table**
   - Single source of truth for store information
   - Include opening dates as constraints
   - Enforce foreign key relationships

3. **Add Data Validation Triggers**
   - Prevent future dates beyond 1 year
   - Block transactions before store opening dates
   - Validate store codes on insert

### Short-term Actions (Priority: MEDIUM)

1. **Standardize Store References**
   - Migrate all tables to use store_id from store_master
   - Update import processes to map correctly
   - Add indexes for performance

2. **Create Data Quality Dashboard**
   - Monitor date anomalies
   - Track import success rates
   - Alert on validation failures

3. **Document Business Rules**
   - Store opening/closing dates
   - Valid date ranges for transactions
   - Store code mapping logic

### Long-term Actions (Priority: LOW)

1. **Implement CDC (Change Data Capture)**
   - Track all data modifications
   - Maintain audit trail
   - Enable rollback capabilities

2. **Create Data Lineage Documentation**
   - Map data flow from source systems
   - Document transformation rules
   - Identify golden record sources

## AI & Predictive Analytics Readiness

### Current State Assessment

| Criteria | Status | Score | Notes |
|----------|--------|-------|-------|
| Data Quality | Poor | 3/10 | Date issues compromise historical analysis |
| Data Volume | Good | 8/10 | 246K+ transactions sufficient for modeling |
| Feature Richness | Good | 7/10 | Multiple data points per transaction |
| Time Series Consistency | Poor | 2/10 | Broken timelines prevent trend analysis |
| Store Comparability | Fair | 5/10 | After fixing dates, cross-store analysis possible |

### Required Improvements for AI

1. **Data Cleaning** (Prerequisite)
   - Fix all date anomalies
   - Establish consistent store timeline
   - Remove duplicate records

2. **Feature Engineering**
   - Create derived time-based features
   - Calculate rolling averages
   - Normalize revenue by store age

3. **Target Variable Identification**
   - Revenue prediction
   - Customer churn
   - Inventory optimization
   - Seasonal patterns

## Implementation Plan

### Phase 1: Data Remediation (Week 1)
- [ ] Backup current database
- [ ] Execute fix_store_timeline_data.sql
- [ ] Verify data corrections
- [ ] Update documentation

### Phase 2: Structure Optimization (Week 2)
- [ ] Create store_master table
- [ ] Update foreign key relationships
- [ ] Implement validation triggers
- [ ] Test import processes

### Phase 3: Monitoring & Governance (Week 3)
- [ ] Deploy data quality dashboard
- [ ] Set up automated alerts
- [ ] Train team on new processes
- [ ] Document procedures

### Phase 4: Analytics Preparation (Week 4)
- [ ] Create analytical views
- [ ] Build feature engineering pipeline
- [ ] Develop predictive models
- [ ] Validate model accuracy

## Success Metrics

| Metric | Current | Target | Timeline |
|--------|---------|--------|----------|
| Data Quality Score | 76% | 99%+ | 2 weeks |
| Date Anomalies | 48,085 | <100 | 1 week |
| Store Mapping Accuracy | 60% | 100% | 1 week |
| Query Performance | Baseline | +50% faster | 3 weeks |
| AI Model Readiness | 30% | 90% | 4 weeks |

## Conclusion

The database contains valuable business data but requires significant cleanup to establish accurate store correlations and timelines. The primary issue of incorrect historical dates can be resolved through the provided SQL scripts. Once cleaned, the data will be suitable for advanced analytics and AI model development.

The establishment of a store_master reference table and implementation of data validation triggers will prevent future data quality issues. With these improvements, the system will provide reliable insights for business decision-making and predictive analytics.

## Appendix

### A. SQL Scripts
- `fix_store_timeline_data.sql` - Data correction and structure improvements
- `store_timeline_correlation_analysis.py` - Analysis and reporting tool

### B. Analysis Output Files
- `store_timeline_analysis_20250901_180727.json` - Detailed analysis results

### C. Technical Dependencies
- MySQL 8.0+ for JSON support and window functions
- Python 3.8+ with pandas, mysql-connector
- Minimum 4GB RAM for analysis operations

---
*Report Generated: 2025-09-01*
*Analyst: Database Correlation System*
*Version: 1.0*