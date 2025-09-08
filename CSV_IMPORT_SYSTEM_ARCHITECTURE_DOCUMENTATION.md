# CSV Import System Architecture Documentation

## Executive Summary

The RFID3 system implements a sophisticated CSV import architecture designed to handle store-specific vs company-wide data through intelligent column header parsing. This system processes weekly business data from 7 different CSV file types, automatically distinguishing between aggregated company data and individual store breakdowns based on column naming patterns.

## Table of Contents

1. [CSV Column Header Architecture](#csv-column-header-architecture)
2. [Store Data Model and Relationships](#store-data-model-and-relationships)
3. [Import Logic Flow and Decision Trees](#import-logic-flow-and-decision-trees)
4. [Database Schema and Constraints](#database-schema-and-constraints)
5. [Historical Data Evolution Patterns](#historical-data-evolution-patterns)
6. [Technical Implementation Details](#technical-implementation-details)
7. [Troubleshooting Guide](#troubleshooting-guide)

---

## CSV Column Header Architecture

### Core Pattern: Store Number Presence Detection

The system uses a fundamental pattern to distinguish data types:

**Company-Wide Data Columns:**
- Column headers WITHOUT store numbers
- Examples: `"Total Weekly Revenue"`, `"% -Total AR ($) > 45 days"`, `"Total Discount $ Company Wide"`
- Represents aggregated metrics across all locations

**Store-Specific Data Columns:**
- Column headers WITH store numbers (3607, 6800, 728, 8101)
- Examples: `"3607 Revenue"`, `"# New Open Contracts 6800"`, `"Total $ on Reservation 728"`
- Represents individual store performance

### Column Header Pattern Examples

```
Store-Specific Headers:
- "3607 Revenue" → Wayzata store revenue
- "6800 Revenue" → Brooklyn Park store revenue  
- "728 Revenue" → Elk River store revenue
- "8101 Revenue" → Fridley store revenue
- "# New Open Contracts 3607" → Wayzata contracts
- "Total $ on Reservation 8101" → Fridley reservations

Company-Wide Headers:
- "Total Weekly Revenue" → Sum of all store revenues
- "Total Discount $ Company Wide" → Company-wide discounts
- "% -Total AR ($) > 45 days" → Company-wide AR aging
- "WEEK NUMBER" → Universal week identifier
```

### CSV File Types and Header Patterns

1. **ScorecardTrends*.csv** - Business performance metrics
2. **PayrollTrends*.csv** - Labor cost and hour tracking
3. **PL*.csv** - Profit & Loss statements (matrix format)
4. **equip*.csv** - Equipment inventory data
5. **customer*.csv** - Customer database exports
6. **transactions*.csv** - Contract transaction records
7. **transitems*.csv** - Individual transaction line items

---

## Store Data Model and Relationships

### Store Code Mapping

```
Store Code | Location      | Business Focus
-----------|---------------|------------------------------------------
000        | Company-Wide  | Aggregated data across all locations
3607       | Wayzata       | Lake Minnetonka DIY/homeowners + events
6800       | Brooklyn Park | Pure construction/industrial
728        | Elk River     | Rural/suburban DIY + agricultural  
8101       | Fridley       | Pure events/weddings/corporate (Broadway Tent & Event)
```

### Data Hierarchy Structure

```
Company Level (store_code: "000")
├── Aggregated Revenue Totals
├── Company-Wide AR Aging
├── Total Discount Amounts
└── Cross-Store Performance Metrics

Store Level (store_code: 3607|6800|728|8101)
├── Store-Specific Revenue
├── Individual Contract Counts
├── Store Reservation Amounts
└── Location-Specific Operational Data
```

### Business Context by Store

**3607 - Wayzata (Lake Minnetonka)**
- Primary: DIY homeowners and weekend projects
- Secondary: Events and weddings (lakefront community)
- Revenue Pattern: Seasonal peaks in spring/summer

**6800 - Brooklyn Park**  
- Primary: Construction and industrial contracts
- Secondary: Commercial equipment rentals
- Revenue Pattern: Steady year-round with construction cycles

**728 - Elk River**
- Primary: Rural and suburban DIY projects  
- Secondary: Agricultural and farming equipment
- Revenue Pattern: Spring farming season peaks

**8101 - Fridley (Broadway Tent & Event)**
- Primary: Events, weddings, and corporate functions
- Secondary: Party and celebration equipment
- Revenue Pattern: Wedding season peaks (May-October)

---

## Import Logic Flow and Decision Trees

### High-Level Import Process

```
1. File Discovery
   ├── Scan /shared/POR/ directory
   ├── Pattern match CSV files by type
   └── Select most recent file by creation time

2. Column Analysis Phase
   ├── Parse CSV headers
   ├── Identify store number patterns (3607|6800|728|8101)
   ├── Classify as company-wide vs store-specific
   └── Build column mapping dictionary

3. Data Validation Phase
   ├── Check for business data presence
   ├── Validate date formats and numeric values
   ├── Filter out future dates with no data
   └── Clean financial formatting ($, commas)

4. Record Creation Phase
   ├── Always create company-wide record (store_code: "000")
   ├── Conditionally create store records if store data exists
   ├── Apply unique constraints (store_code, week_ending_sunday)
   └── Use ON DUPLICATE KEY UPDATE for safe re-imports
```

### Decision Tree: Store Record Creation

```
For each CSV row:
├── Has business data? 
│   ├── No → Skip row entirely
│   └── Yes → Continue
├── Create company-wide record (store_code: "000")
│   ├── Extract company-wide metrics
│   ├── Set total_weekly_revenue
│   └── Insert with duplicate handling
└── Has store-specific columns with data?
    ├── No → Company-wide record only  
    └── Yes → Create store records
        ├── For each store (3607, 6800, 728, 8101)
        ├── Extract store-specific metrics
        ├── Set store_code and revenue fields
        └── Insert with duplicate handling
```

### Key Logic Methods

**`_has_any_business_data(row, columns)`**
```python
# Checks for meaningful business indicators
business_indicators = [
    'total weekly revenue',
    '3607 revenue', '6800 revenue', '728 revenue', '8101 revenue',
    '# new open contracts',
    '$ on reservation',
    'total discount'
]
```

**`_has_store_specific_data_in_csv(row, columns)`**
```python
# Detects store numbers in column headers with non-zero data
store_indicators = ['3607', '6800', '728', '8101']
# Returns True if any column with store numbers has meaningful data
```

---

## Database Schema and Constraints

### Primary Table: pos_scorecard_trends

```sql
CREATE TABLE pos_scorecard_trends (
    id INT AUTO_INCREMENT PRIMARY KEY,
    week_ending_sunday DATE NOT NULL,
    store_code VARCHAR(10) NOT NULL DEFAULT '000',
    total_weekly_revenue DECIMAL(15,2),
    
    -- Store-specific revenue columns
    col_3607_revenue DECIMAL(15,2),
    col_6800_revenue DECIMAL(15,2), 
    col_728_revenue DECIMAL(15,2),
    col_8101_revenue DECIMAL(15,2),
    
    -- Store-specific contract metrics
    new_open_contracts_3607 INT,
    new_open_contracts_6800 INT,
    new_open_contracts_728 INT,
    new_open_contracts_8101 INT,
    
    -- Store-specific reservation metrics  
    total_on_reservation_3607 DECIMAL(15,2),
    total_on_reservation_6800 DECIMAL(15,2),
    total_on_reservation_728 DECIMAL(15,2),
    total_on_reservation_8101 DECIMAL(15,2),
    
    -- Operational metrics
    deliveries_scheduled_next_7_days_weds_tues_8101 INT,
    
    -- Company-wide metrics
    ar_over_45_days_percent DECIMAL(5,2),
    total_discount_company_wide DECIMAL(15,2),
    total_ar_cash_customers DECIMAL(15,2),
    
    -- Metadata
    import_batch_id VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE KEY unique_week_store (week_ending_sunday, store_code),
    INDEX idx_week_ending (week_ending_sunday),
    INDEX idx_store_code (store_code),
    INDEX idx_import_batch (import_batch_id)
);
```

### Key Constraints and Indexes

**Unique Constraint:** `(week_ending_sunday, store_code)`
- Prevents duplicate records for same week/store combination
- Enables safe re-imports with ON DUPLICATE KEY UPDATE

**Indexes for Performance:**
- `week_ending_sunday` - Time-based queries and reporting
- `store_code` - Store-specific filtering and analytics  
- `import_batch_id` - Tracking and rollback capabilities

### Data Integrity Rules

1. **Company-wide records** (store_code = "000") are ALWAYS created when business data exists
2. **Store records** are ONLY created when CSV has store-specific columns AND data
3. **Financial amounts** use DECIMAL(15,2) for precision in currency calculations
4. **Date standardization** converts all dates to MySQL DATE format
5. **Batch tracking** enables audit trails and import verification

---

## Historical Data Evolution Patterns

### Timeline of Business Data Tracking

**Phase 1: Company Totals Only (2022-early 2023)**
- CSV files contained only aggregated company-wide metrics
- Column headers: "Total Weekly Revenue", "Total Contracts"
- Database records: Only store_code "000" entries

**Phase 2: Store Breakdown Introduction (mid-2023)**
- Business added store-specific tracking capability
- Column headers expanded: "3607 Revenue", "6800 Revenue", etc.
- Database records: Both company-wide ("000") and store-specific entries

**Phase 3: Enhanced Metrics (late 2023-2024)**
- Additional operational metrics added
- Store-specific reservations, deliveries tracking
- Expanded business intelligence capabilities

**Phase 4: Current State (2024-present)**
- Full store-specific breakdown across all major metrics
- Real-time import automation with Tuesday scheduling
- Executive dashboard integration

### Data Availability Patterns

```
Early Historical Data:
├── Week ending: 1/16/22 - 12/31/22
├── Store columns: Empty or not present
├── Company totals: Available
└── Records created: Only store_code "000"

Transitional Period:
├── Week ending: 1/1/23 - 6/30/23  
├── Store columns: Partially populated
├── Mixed data availability
└── Records created: "000" + partial store records

Modern Data:
├── Week ending: 7/1/23 - Present
├── Store columns: Fully populated
├── Complete breakdown available
└── Records created: "000" + all store records (3607,6800,728,8101)
```

### Import Behavior by Data Period

The import system automatically adapts to data availability:

1. **Historical imports** create only company-wide records due to missing store columns
2. **Modern imports** create both company-wide and store-specific records
3. **Future planning** can accommodate new stores by adding store codes to mapping

---

## Technical Implementation Details

### Core Service Classes

**CSVImportService** (`app/services/csv_import_service.py`)
- Primary import orchestration
- Handles equipment, transactions, customers, scorecard data
- Implements store-specific detection logic

**FinancialCSVImportService** (`app/services/financial_csv_import_service.py`)  
- Specialized for financial data (P&L, payroll, advanced scorecard)
- Matrix format conversion (wide to normalized)
- Enhanced date and financial formatting

### Key Technical Patterns

**Column Header Pattern Matching:**
```python
def _has_store_specific_data_in_csv(self, row, columns):
    """Check if CSV row has store-specific data based on column headers with store numbers"""
    store_indicators = ['3607', '6800', '728', '8101']
    
    for col in columns:
        if any(store_num in col for store_num in store_indicators):
            value = row[col]
            if pd.notna(value) and value != 0 and str(value).strip() not in ['', '0', '$0']:
                return True
    return False
```

**Safe Database Operations:**
```python
INSERT INTO pos_scorecard_trends (columns...)
VALUES (values...)
ON DUPLICATE KEY UPDATE
    total_weekly_revenue = VALUES(total_weekly_revenue),
    import_batch_id = VALUES(import_batch_id)
```

**Data Type Conversion Pipeline:**
```python
# Financial columns: Remove $, commas, handle parentheses for negative values
df[col] = df[col].astype(str).str.replace(r'[$,()]', '', regex=True)
df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# Date columns: Smart parsing with 2-digit year handling  
df[col] = pd.to_datetime(df[col], errors='coerce')

# Integer columns: Contract counts, delivery numbers
df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
```

### Import Scheduling and Automation

**Tuesday 8am Automated Import:**
- Scheduled via `app/services/scheduler.py`
- Processes all 7 CSV file types automatically
- Generates comprehensive import reports
- Handles failures gracefully with detailed logging

**Manual Import Capabilities:**
- Web interface for on-demand imports
- Individual file type processing
- Import status monitoring and rollback

---

## Troubleshooting Guide

### Common Issues and Solutions

#### 1. Missing Store Data in Recent Weeks

**Symptoms:**
- Only company-wide records created despite expecting store breakdowns
- Store revenue columns showing NULL values

**Diagnosis:**
```python
# Check if CSV has store columns
df.columns.tolist()  # Look for "3607 Revenue", "6800 Revenue", etc.

# Check if columns have actual data
for col in df.columns:
    if any(store in col for store in ['3607', '6800', '728', '8101']):
        print(f"{col}: {df[col].notna().sum()} non-null values")
```

**Solutions:**
- Verify CSV export includes store breakdowns
- Check POS system configuration for store-specific reporting
- Confirm data entry completeness in source system

#### 2. Import Failures Due to Date Format Issues

**Symptoms:**
- "Date parsing failed" errors in logs
- Records skipped due to invalid week_ending_sunday values

**Diagnosis:**
```python
# Check date format patterns in CSV
df['Week ending Sunday'].head(10)  # Look for format consistency

# Test date parsing
pd.to_datetime(df['Week ending Sunday'], errors='coerce').isna().sum()
```

**Solutions:**
- Implement smart_date_parser for multiple format support
- Standardize CSV export date formatting
- Add manual date format specification in import configuration

#### 3. Duplicate Record Errors

**Symptoms:**
- "Duplicate entry" database errors
- Import process halting on constraint violations

**Diagnosis:**
```sql
-- Check for existing records
SELECT week_ending_sunday, store_code, COUNT(*) as count
FROM pos_scorecard_trends 
GROUP BY week_ending_sunday, store_code 
HAVING count > 1;
```

**Solutions:**
- Use ON DUPLICATE KEY UPDATE in all INSERT statements
- Implement proper unique constraints on (week_ending_sunday, store_code)
- Clear duplicate records before re-import if necessary

#### 4. Performance Issues with Large CSV Files

**Symptoms:**
- Import timeouts on files >50MB
- Memory usage spikes during processing

**Solutions:**
```python
# Implement chunked processing
chunk_size = 5000
for chunk in pd.read_csv(file_path, chunksize=chunk_size):
    process_chunk(chunk)

# Use batch database operations
df.to_sql('table_name', con=engine, if_exists='append', method='multi')
```

#### 5. Business Logic Validation Failures

**Symptoms:**
- Records with $0 revenue but positive contract counts
- Future dates with business data (data entry errors)

**Diagnosis:**
```python
# Validate business data consistency
def validate_business_logic(df):
    # Revenue/contract correlation check
    suspicious = df[(df['total_weekly_revenue'] == 0) & (df['new_contracts'] > 0)]
    
    # Future date check
    future_dates = df[df['week_ending_sunday'] > datetime.now().date()]
    
    return suspicious, future_dates
```

**Solutions:**
- Implement pre-import data validation
- Add business rule checks in import pipeline
- Create data quality reports for source system issues

### Monitoring and Maintenance

#### Log Analysis

**Key Log Patterns to Monitor:**
```bash
# Import success/failure rates
grep "import completed" /path/to/logs | wc -l
grep "import failed" /path/to/logs | wc -l

# Data quality issues
grep "Skipping.*no meaningful data" /path/to/logs
grep "Error processing.*row" /path/to/logs

# Performance metrics
grep "Processed.*records in" /path/to/logs
```

#### Database Health Checks

```sql
-- Weekly data completeness check
SELECT 
    YEAR(week_ending_sunday) as year,
    WEEK(week_ending_sunday) as week,
    COUNT(DISTINCT store_code) as stores_with_data,
    SUM(total_weekly_revenue) as total_revenue
FROM pos_scorecard_trends 
WHERE week_ending_sunday >= DATE_SUB(NOW(), INTERVAL 8 WEEK)
GROUP BY year, week
ORDER BY year DESC, week DESC;

-- Store data availability audit  
SELECT 
    store_code,
    COUNT(*) as weeks_of_data,
    MAX(week_ending_sunday) as latest_data,
    AVG(total_weekly_revenue) as avg_revenue
FROM pos_scorecard_trends
WHERE week_ending_sunday >= DATE_SUB(NOW(), INTERVAL 12 WEEK)
GROUP BY store_code;
```

### Emergency Recovery Procedures

#### 1. Failed Import Recovery

```python
# Rollback by import_batch_id
DELETE FROM pos_scorecard_trends 
WHERE import_batch_id = 'YYYYMMDD_HHMM';

# Re-run specific file import
service = CSVImportService()
result = service.import_scorecard_trends('/path/to/backup/file.csv')
```

#### 2. Data Corruption Recovery

```sql
-- Backup before recovery
CREATE TABLE pos_scorecard_trends_backup AS 
SELECT * FROM pos_scorecard_trends 
WHERE week_ending_sunday >= 'YYYY-MM-DD';

-- Restore from known good backup
LOAD DATA INFILE '/path/to/backup.csv' 
INTO TABLE pos_scorecard_trends_temp;

-- Validate and swap tables
RENAME TABLE pos_scorecard_trends TO pos_scorecard_trends_old,
             pos_scorecard_trends_temp TO pos_scorecard_trends;
```

---

## Appendices

### A. Complete Column Mapping Reference

**Scorecard Trends CSV Columns:**
```
Source Column → Database Column → Data Type
"Week ending Sunday" → week_ending_sunday → DATE
"Total Weekly Revenue" → total_weekly_revenue → DECIMAL(15,2)
"3607 Revenue" → col_3607_revenue → DECIMAL(15,2)
"6800 Revenue" → col_6800_revenue → DECIMAL(15,2)
"728 Revenue" → col_728_revenue → DECIMAL(15,2)
"8101 Revenue" → col_8101_revenue → DECIMAL(15,2)
"# New Open Contracts 3607" → new_open_contracts_3607 → INT
[... complete mapping table ...]
```

### B. Store Business Intelligence Profiles

**Detailed Store Characteristics:**
- Market demographics and customer types
- Seasonal patterns and peak periods  
- Equipment mix and specialization
- Revenue drivers and business focus
- Competitive landscape and positioning

### C. Import Performance Benchmarks

**Expected Processing Times:**
```
File Type          | Size   | Records | Time   | Memory
ScorecardTrends   | 2MB    | 500     | 15s    | 50MB
PayrollTrends     | 5MB    | 1,200   | 30s    | 80MB
Equipment         | 15MB   | 5,000   | 90s    | 200MB
Transactions      | 25MB   | 10,000  | 180s   | 350MB
Transaction Items | 53MB   | 597,000 | 600s   | 800MB
```

---

**Document Version:** 1.0  
**Last Updated:** September 1, 2025  
**Maintainer:** RFID3 System Architecture Team  
**Related Systems:** POS Integration, Executive Dashboard, Predictive Analytics Pipeline
