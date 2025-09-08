# Inventory Data Correlation System Documentation

## System Overview

The Inventory Data Correlation System bridges multiple inventory tracking systems (RFID, POS, QR/Barcode) to provide unified inventory intelligence, migration management, and predictive analytics.

## Architecture Components

### 1. Database Schema

#### Core Tables

- **inventory_correlation_master**: Central hub linking all inventory systems
- **pos_data_staging**: Temporary storage for POS CSV imports
- **rfid_pos_mapping**: Many-to-many relationships between RFID tags and POS items
- **migration_tracking**: Manages transition from bulk to individual tracking
- **data_quality_metrics**: Tracks and resolves data quality issues
- **inventory_intelligence**: Aggregated business intelligence metrics
- **correlation_audit_log**: Complete audit trail of all changes

#### Key Features

- **Multi-System Support**: RFID, QR, Barcode, Bulk tracking
- **Migration Management**: Track items transitioning between tracking methods
- **Data Quality**: Automatic conflict detection and resolution
- **Intelligence**: Predictive analytics and utilization metrics

### 2. POS Integration Service

Located in: `/app/services/pos_integration.py`

#### Key Functions

```python
# Process CSV file import
process_csv_file(file_path, file_type='equipment')

# Auto-process all new files
auto_process_new_files()

# Create manual correlations
correlate_rfid_pos(rfid_tag, pos_item_num, confidence)

# Get system status
get_correlation_status()
```

#### CSV Column Mappings

**Equipment CSV**:
- ItemNum → item_num
- Name → name
- Qty → quantity
- T/O YTD → turnover_ytd

**ItemList CSV**:
- tag_id → tag_id
- common_name → common_name
- rental_class_num → rental_class_num

### 3. Data Validation Service

Located in: `/app/services/data_validation.py`

#### Key Functions

```python
# Validate RFID tag format
validate_rfid_tag(tag_id)

# Detect conflicts between systems
detect_conflicts(correlation_id)

# Resolve data conflicts
resolve_conflict(correlation_id, conflict, resolution)

# Calculate confidence scores
calculate_confidence_score(correlation_id)

# Detect and merge duplicates
detect_duplicates()
merge_duplicates(correlation_ids, master_id)
```

#### Conflict Resolution Methods

- **USE_RFID**: Prefer RFID data (confidence: 0.90)
- **USE_POS**: Prefer POS data (confidence: 0.85)
- **MANUAL**: Manual override by user
- **IGNORE**: Mark as reviewed, reduce confidence

### 4. API Endpoints

Base URL: `/api/correlation`

#### Status & Monitoring

- `GET /status` - Overall correlation system status
- `GET /quality/issues` - Open data quality issues
- `GET /duplicates` - Detect duplicate items

#### POS Integration

- `GET /pos/scan` - Scan for new CSV files
- `POST /pos/import` - Import specific CSV file
- `POST /pos/auto-import` - Auto-import all new files

#### Correlation Management

- `POST /correlate` - Create manual correlation
- `GET /validate/<id>` - Validate correlation
- `POST /resolve-conflict` - Resolve data conflict
- `POST /merge-duplicates` - Merge duplicate records

#### Migration Tracking

- `GET /migrations` - Active migration plans
- `POST /migration/create` - Create migration plan

#### Intelligence

- `GET /intelligence/<id>` - Get inventory intelligence
- `POST /search` - Search correlations with filters

## Data Flow

### 1. POS CSV Import Flow

```
CSV File → Staging Table → Correlation Matching → Quality Check → Master Table
```

1. CSV file detected in `/shared/POR/`
2. Data loaded to `pos_data_staging`
3. Automatic correlation matching:
   - Exact match on serial/tag: 100% confidence
   - Item number match: 90% confidence
   - Name similarity match: 70% confidence
   - No match: Create orphaned record (50% confidence)
4. Quality issues logged to `data_quality_metrics`
5. Successfully correlated items update `inventory_correlation_master`

### 2. Migration Flow

```
Bulk Item → Migration Plan → Tagging → Hybrid Tracking → Individual Tracking
```

1. Identify high-value bulk items (revenue > $10k/year)
2. Create migration plan with ROI estimate
3. Begin tagging process (RFID/QR/Barcode)
4. Hybrid phase: Some tagged, some bulk
5. Complete migration to individual tracking

### 3. Conflict Resolution Flow

```
Detect → Analyze → Prioritize → Resolve → Verify
```

1. Automatic conflict detection during import
2. Severity classification (CRITICAL/HIGH/MEDIUM/LOW)
3. Business impact assessment
4. Resolution via API or manual intervention
5. Confidence score adjustment

## Business Intelligence Features

### Utilization Metrics

- **Utilization Rate**: Percentage of days used in period
- **Demand Trend**: INCREASING/STABLE/DECREASING
- **Seasonality Factor**: Peak vs average usage
- **Days Since Last Use**: Identify idle inventory

### Financial Metrics

- **Revenue Tracking**: 30d/90d/365d revenue per item
- **ROI Percentage**: Return on investment calculation
- **Turnover Rates**: MTD/YTD/LTD from POS

### Predictive Indicators

- **Reorder Point**: When to purchase more inventory
- **Recommended Quantity**: Optimal stock levels
- **Loss Risk Score**: Probability of item loss
- **Obsolescence Risk**: Items becoming outdated

### Tracking Recommendations

- **Should Add Tracking**: Boolean flag for bulk items
- **Recommended Type**: RFID/QR/Barcode suggestion
- **ROI Estimate**: Expected return from adding tracking

## Data Quality Management

### Quality Score Calculation

```
Base Score: 1.00
- Missing RFID: -0.20
- Missing POS: -0.10
- Missing Name: -0.15
- Per Issue: -0.05 (max 5)
+ Validated Mapping: +0.10
- Old Data (>90 days): -0.10
- Old Data (>30 days): -0.05
= Final Score (0.00 - 1.00)
```

### Issue Types

- **MISSING_DATA**: Required fields empty
- **DUPLICATE**: Same identifier multiple records
- **MISMATCH**: Conflicting values between systems
- **ORPHANED**: Records in one system only
- **STALE**: Data not updated recently
- **INCONSISTENT**: Logical inconsistencies

## Performance Optimization

### Database Indexes

- RFID tag lookups
- POS item number searches
- Tracking type filtering
- Migration phase queries
- Confidence score ranges

### Batch Processing

- Bulk CSV imports (up to 1M records)
- Async quality checks
- Scheduled intelligence calculations

### Caching Strategy

- Correlation mappings cached
- Intelligence metrics cached 24h
- Quality issues cached until resolved

## Security Considerations

### Access Control

- All endpoints require authentication
- Audit logging for all changes
- IP tracking for sensitive operations

### Data Validation

- Input sanitization for all fields
- RFID tag format validation
- Quantity range checks
- Confidence score bounds

## Migration Strategy Examples

### Example 1: Tent Stakes (Bulk → RFID)

```sql
-- Current State: 5000 stakes counted as bulk
-- Target State: Individual RFID tags

INSERT INTO migration_tracking (
    correlation_id,
    from_tracking_type,
    to_tracking_type,
    total_items_to_migrate,
    estimated_cost,
    estimated_roi_months
) VALUES (
    (SELECT correlation_id FROM inventory_correlation_master WHERE common_name = 'Tent Stakes'),
    'BULK',
    'RFID',
    5000,
    2500.00,  -- $0.50 per tag
    6         -- ROI in 6 months
);
```

### Example 2: Tables (Partial → Full RFID)

```sql
-- Current: 200 of 500 tables tagged
-- Target: All 500 tables tagged

UPDATE inventory_correlation_master
SET 
    migration_phase = 'TRANSITIONING',
    tagged_quantity = 200,
    untagged_quantity = 300
WHERE common_name LIKE '%Table%';
```

## Troubleshooting Guide

### Common Issues

1. **CSV Import Fails**
   - Check file permissions in `/shared/POR/`
   - Verify CSV column headers match mappings
   - Check for special characters in data

2. **Low Confidence Scores**
   - Run duplicate detection
   - Validate RFID tag formats
   - Check for stale data (>90 days)

3. **Orphaned Records**
   - Manual correlation via API
   - Fuzzy name matching
   - Check for data entry errors

4. **Migration Stalled**
   - Review error logs
   - Check for duplicate tags
   - Verify quantity counts

## API Usage Examples

### Import POS File

```bash
curl -X POST http://localhost:5000/api/correlation/pos/import \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/shared/POR/equip8.26.25.csv",
    "file_type": "equipment"
  }'
```

### Create Manual Correlation

```bash
curl -X POST http://localhost:5000/api/correlation/correlate \
  -H "Content-Type: application/json" \
  -d '{
    "rfid_tag": "393020535152205748495445",
    "pos_item_num": "62399",
    "confidence": 0.95
  }'
```

### Resolve Conflict

```bash
curl -X POST http://localhost:5000/api/correlation/resolve-conflict \
  -H "Content-Type: application/json" \
  -d '{
    "correlation_id": 123,
    "conflict": {"type": "NAME_MISMATCH"},
    "resolution": "USE_RFID"
  }'
```

## Maintenance Tasks

### Daily
- Auto-import new POS files
- Detect and log quality issues
- Calculate utilization metrics

### Weekly
- Resolve orphaned records
- Merge duplicate items
- Update confidence scores

### Monthly
- Migration progress review
- ROI analysis for completed migrations
- Archive old staging data

## Future Enhancements

1. **Machine Learning Integration**
   - Automatic conflict resolution
   - Demand forecasting
   - Anomaly detection

2. **Real-time Sync**
   - WebSocket updates
   - Live POS integration
   - Instant conflict alerts

3. **Advanced Analytics**
   - Predictive maintenance
   - Customer behavior analysis
   - Seasonal trend prediction

4. **Mobile Support**
   - Field correlation updates
   - Barcode/QR scanning
   - Offline sync capability