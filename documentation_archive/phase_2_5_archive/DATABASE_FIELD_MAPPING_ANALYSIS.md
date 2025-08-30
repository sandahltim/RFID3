# RFID3 Database Field Mapping Analysis
## Comprehensive Database Structure and Relationship Documentation

Generated: 2025-08-30

---

## Executive Summary

The RFID3 inventory management system uses a MySQL database (`rfid_inventory`) with 46 tables managing inventory tracking, transactions, and business intelligence. The core system tracks 65,942 unique items across multiple identifier types (RFID, QR, Sticker, Bulk) with comprehensive transaction history and health monitoring.

### Key Statistics
- **Total Items Tracked**: 65,942
- **Total Transactions**: 26,590
- **Active Tables**: 46 (9 core tables analyzed in detail)
- **Primary Identifier Types**: QR (64%), None (19%), Bulk (15%), Sticker (2%), RFID (<1%)

---

## 1. Complete Field Mapping Documentation

### 1.1 ItemMaster Table (`id_item_master`)
**Purpose**: Central inventory item registry tracking all physical assets
**Records**: 65,942 items
**Primary Key**: `tag_id` (varchar 255)

| Field | Type | Constraints | Purpose | Data Quality |
|-------|------|------------|---------|--------------|
| tag_id | varchar(255) | PK, NOT NULL | Unique item identifier | 100% populated, unique |
| uuid_accounts_fk | varchar(255) | NULL | External account reference | 100% NULL (unused) |
| serial_number | varchar(255) | NULL | Item serial number | 100% NULL (unused) |
| client_name | varchar(255) | NULL | Customer/client association | 4.6% populated, 229 distinct |
| rental_class_num | varchar(255) | NULL, INDEXED | Equipment category code | 18.9% populated, 489 distinct |
| common_name | varchar(255) | NULL | Human-readable item name | 100% populated, 28,277 distinct |
| quality | varchar(50) | NULL | Item condition grade (A+, A, A-, B+, B, B-, C, C-) | 17.3% populated |
| bin_location | varchar(255) | NULL, INDEXED | Physical storage location | 18.9% populated, 35 locations |
| status | varchar(50) | NULL, INDEXED | Current item state | 18.9% populated, 7 states |
| last_contract_num | varchar(255) | NULL | Most recent rental contract | 15.8% populated |
| last_scanned_by | varchar(255) | NULL | User who last scanned | 17.9% populated |
| notes | text | NULL | General notes | 3.5% populated |
| status_notes | text | NULL | Status-specific notes | 84.8% populated (mostly empty strings) |
| longitude | decimal(9,6) | NULL | GPS longitude | 84.5% populated |
| latitude | decimal(9,6) | NULL | GPS latitude | 84.5% populated |
| date_last_scanned | datetime | NULL, INDEXED | Last scan timestamp | 18.1% populated |
| date_created | datetime | NULL | Record creation date | 0% populated (unused) |
| date_updated | datetime | NULL | Record update date | 0% populated (unused) |
| item_num | int(11) | UNIQUE, NULL | Alternative numeric ID | 0% populated (unused) |
| identifier_type | enum | NULL, INDEXED | Type of identifier (RFID/QR/Sticker/Barcode/Bulk/None) | 100% populated |
| department | varchar(100) | NULL | Department assignment | 0% populated (unused) |
| turnover_ytd | decimal(10,2) | NULL, INDEXED | Year-to-date revenue | 0% populated (unused) |
| manufacturer | varchar(100) | NULL, INDEXED | Item manufacturer | 0% populated (unused) |
| type_desc | varchar(50) | NULL | Item type description | 0% populated (unused) |
| turnover_ltd | decimal(10,2) | NULL | Lifetime revenue | 0% populated (unused) |
| repair_cost_ltd | decimal(10,2) | NULL | Lifetime repair costs | 0% populated (unused) |
| sell_price | decimal(10,2) | NULL | Sale price | 0% populated (unused) |
| retail_price | decimal(10,2) | NULL | Retail price | 0% populated (unused) |
| home_store | varchar(10) | NULL | Home store location | 0% populated (unused) |
| current_store | varchar(10) | NULL, INDEXED | Current store location | 0% populated (unused) |
| quantity | int(11) | DEFAULT 1 | Item quantity (for bulk) | 100% populated (all = 1) |
| reorder_min | int(11) | NULL | Minimum reorder level | 0% populated (unused) |
| reorder_max | int(11) | NULL | Maximum reorder level | 0% populated (unused) |
| data_source | varchar(20) | DEFAULT 'RFID_API' | Data origin system | 100% populated |
| pos_last_updated | datetime | NULL | POS system sync timestamp | 0% populated (unused) |
| rental_rates | longtext | NULL | JSON rental pricing | 0% populated (unused) |
| vendor_ids | longtext | NULL | JSON vendor references | 0% populated (unused) |
| tag_history | longtext | NULL | JSON tag change history | 0% populated (unused) |

### 1.2 Transaction Table (`id_transactions`)
**Purpose**: Records all item scanning and movement events
**Records**: 26,590 transactions
**Primary Key**: `id` (bigint auto-increment)

| Field | Type | Constraints | Purpose | Data Quality |
|-------|------|------------|---------|--------------|
| id | bigint(20) | PK, AUTO_INCREMENT | Transaction ID | 100% unique |
| contract_number | varchar(255) | NULL | Associated contract | 3.2% populated |
| tag_id | varchar(255) | NOT NULL, INDEXED | Item identifier | 100% populated |
| scan_type | varchar(50) | NOT NULL | Type of scan event | 100% populated, 5 types |
| scan_date | datetime | NOT NULL, INDEXED | Event timestamp | 100% populated |
| client_name | varchar(255) | NULL | Customer name | 26.4% populated |
| common_name | varchar(255) | NOT NULL | Item name | 100% populated |
| bin_location | varchar(255) | NULL | Storage location | 10.8% populated |
| status | varchar(50) | NULL, INDEXED | Transaction status | 100% populated, 11 states |
| scan_by | varchar(255) | NULL | User performing scan | 100% populated |
| location_of_repair | varchar(255) | NULL | Repair location | 79.7% populated |
| quality | varchar(50) | NULL | Quality assessment | 100% populated |
| dirty_or_mud | tinyint(1) | NULL | Condition flag | 79.7% populated |
| leaves | tinyint(1) | NULL | Condition flag | 79.7% populated |
| oil | tinyint(1) | NULL | Condition flag | 79.7% populated |
| mold | tinyint(1) | NULL | Condition flag | 79.7% populated |
| stain | tinyint(1) | NULL | Condition flag | 79.7% populated |
| oxidation | tinyint(1) | NULL | Condition flag | 79.7% populated |
| other | text | NULL | Other conditions | 79.7% populated |
| rip_or_tear | tinyint(1) | NULL | Damage flag | 79.7% populated |
| sewing_repair_needed | tinyint(1) | NULL | Repair flag | 79.7% populated |
| grommet | tinyint(1) | NULL | Component flag | 79.7% populated |
| rope | tinyint(1) | NULL | Component flag | 79.7% populated |
| buckle | tinyint(1) | NULL | Component flag | 79.7% populated |
| date_created | datetime | NULL | Record creation | 100% populated |
| date_updated | datetime | NULL | Record update | 100% populated |
| uuid_accounts_fk | varchar(255) | NULL | External reference | 0% populated |
| serial_number | varchar(255) | NULL | Serial number | 100% populated (empty strings) |
| rental_class_num | varchar(255) | NULL | Equipment category | 100% populated |
| longitude | decimal(9,6) | NULL | GPS longitude | 0% populated |
| latitude | decimal(9,6) | NULL | GPS latitude | 0% populated |
| wet | tinyint(1) | NULL | Condition flag | 79.7% populated |
| service_required | tinyint(1) | NULL | Service flag | 79.7% populated |
| notes | text | NULL | Transaction notes | 100% populated (mostly empty) |

### 1.3 RFIDTag Table (`id_rfidtag`)
**Purpose**: Dedicated RFID tag tracking (currently unused)
**Records**: 0 (empty table)
**Primary Key**: `tag_id`

*Table structure mirrors ItemMaster but specifically for RFID-tagged items. Currently not in use.*

### 1.4 SeedRentalClass Table (`seed_rental_classes`)
**Purpose**: Master list of equipment categories
**Records**: 909 classes
**Primary Key**: `rental_class_id`

| Field | Type | Purpose | Sample Values |
|-------|------|---------|---------------|
| rental_class_id | varchar(255) | Category code | "00001", "61825", "61839" |
| common_name | varchar(255) | Category name | "90 ROUND WHITE LINEN", "6FT TABLE" |
| bin_location | varchar(255) | Default storage | "NR5x2", "resale", "pack" |

### 1.5 RentalClassMapping Table (`rental_class_mappings`)
**Purpose**: Maps rental classes to categories/subcategories
**Records**: 0 (empty - use user_rental_class_mappings instead)
**Primary Key**: `rental_class_id`

### 1.6 UserRentalClassMapping Table (`user_rental_class_mappings`)
**Purpose**: Active rental class categorization
**Records**: 909 mappings
**Primary Key**: `rental_class_id`

| Field | Type | Purpose | Sample Values |
|-------|------|---------|---------------|
| rental_class_id | varchar(50) | Class code | Links to ItemMaster.rental_class_num |
| category | varchar(100) | Main category | "Rectangle Linen", "Concession Machines" |
| subcategory | varchar(100) | Subcategory | "90X132 Linen", "Fountain Machines" |
| short_common_name | varchar(50) | Abbreviated name | Mostly "N/A" |
| created_at | datetime | Creation timestamp | Tracking |
| updated_at | datetime | Update timestamp | Tracking |

### 1.7 HandCountedItems Table (`id_hand_counted_items`)
**Purpose**: Manual inventory counts
**Records**: 0 (currently unused)
**Primary Key**: `id`

### 1.8 InventoryHealthAlert Table (`inventory_health_alerts`)
**Purpose**: System-generated inventory health warnings
**Records**: 95 alerts
**Primary Key**: `id`

| Field | Type | Purpose | Current Usage |
|-------|------|---------|---------------|
| id | bigint(20) | Alert ID | Auto-increment |
| tag_id | varchar(255) | Item reference | Links to ItemMaster |
| rental_class_id | varchar(255) | Category reference | Links to rental classes |
| common_name | varchar(255) | Item name | Denormalized for performance |
| category | varchar(100) | Main category | From rental class mapping |
| subcategory | varchar(100) | Subcategory | From rental class mapping |
| alert_type | enum | Alert classification | 'stale_item' (100% currently) |
| severity | enum | Priority level | 'critical' (81%), 'high' (19%) |
| days_since_last_scan | int(11) | Staleness metric | Average: 251 days |
| last_scan_date | datetime | Last activity | Reference date |
| suggested_action | text | Recommended action | System-generated text |
| status | enum | Alert status | 'resolved' (100% currently) |
| created_at | timestamp | Alert creation | Tracking |
| acknowledged_at | datetime | Acknowledgment time | Workflow tracking |
| acknowledged_by | varchar(255) | User acknowledgment | Audit trail |
| resolved_at | datetime | Resolution time | Workflow tracking |
| resolved_by | varchar(255) | User resolution | Audit trail |

### 1.9 RefreshState Table (`refresh_state`)
**Purpose**: Tracks data synchronization state
**Records**: 1 (singleton)
**Primary Key**: `id`

| Field | Type | Purpose | Current Value |
|-------|------|---------|---------------|
| id | int(11) | Singleton key | 1 |
| last_refresh | datetime | Last sync time | "2025-08-30 02:00:37" |
| state_type | varchar(50) | Refresh type | "incremental_refresh" |

### 1.10 InventoryConfig Table (`inventory_config`)
**Purpose**: System configuration storage
**Records**: 3 configurations
**Primary Key**: `id`

| Field | Type | Purpose | Current Configs |
|-------|------|---------|-----------------|
| id | int(11) | Config ID | Auto-increment |
| config_key | varchar(100) | Setting name | "alert_thresholds", "business_rules", "category_mappings" |
| config_value | longtext | JSON configuration | Complex nested JSON |
| description | text | Config description | Human-readable |
| category | varchar(50) | Config category | "alerting", "business" |
| created_at | timestamp | Creation time | Audit |
| updated_at | timestamp | Update time | Audit |

---

## 2. Data Relationship Analysis

### 2.1 Primary Relationships

#### ItemMaster ↔ Transaction (One-to-Many)
- **Relationship**: `ItemMaster.tag_id` → `Transaction.tag_id`
- **Cardinality**: 1 ItemMaster : N Transactions
- **Coverage**: 10,388 items have transactions (15.7% of inventory)
- **Orphaned**: 974 transactions have no matching ItemMaster (3.7%)

#### ItemMaster ↔ ContractSnapshot (One-to-Many)
- **Relationship**: `ItemMaster.tag_id` → `ContractSnapshot.tag_id`
- **Cardinality**: 1 ItemMaster : N Snapshots
- **Coverage**: 291 items have snapshots (0.4% of inventory)
- **Orphaned**: 0 orphaned snapshots

#### ItemMaster ↔ InventoryHealthAlert (One-to-Many)
- **Relationship**: `ItemMaster.tag_id` → `InventoryHealthAlert.tag_id`
- **Cardinality**: 1 ItemMaster : N Alerts
- **Coverage**: 94 items have alerts (0.14% of inventory)
- **Orphaned**: 1 alert has no matching ItemMaster

#### ItemMaster/Transaction ↔ RentalClass (Many-to-One)
- **Relationship**: `rental_class_num` → `SeedRentalClass.rental_class_id`
- **Coverage**: 488 of 489 ItemMaster rental classes are mapped (99.8%)
- **Unmapped**: 210 items have rental_class_num not in mappings

### 2.2 Junction Table Relationships

#### UserRentalClassMapping
- **Purpose**: Categorizes rental classes into hierarchical structure
- **Relationships**:
  - Links `rental_class_id` to category/subcategory taxonomy
  - Provides business categorization for reporting
- **Coverage**: 909 mappings cover all seed rental classes

### 2.3 Data Flow Patterns

```
[External RFID System] 
    ↓ (API Import)
[ItemMaster] ← → [Transactions] → [ContractSnapshots]
    ↓              ↓                    ↓
[RentalClass] ← [UserRentalClassMapping]
    ↓
[InventoryHealthAlerts]
```

---

## 3. Actual Data Samples and Patterns

### 3.1 Status Distribution

#### ItemMaster Status
- **NULL**: 53,465 items (81.1%) - Legacy or incomplete data
- **Ready to Rent**: 11,330 items (17.2%)
- **Sold**: 593 items (0.9%)
- **On Rent**: 452 items (0.7%)
- **Needs to be Inspected**: 91 items (0.1%)
- **Wet**: 6 items
- **Repair**: 4 items
- **Missing**: 1 item

#### Transaction Status Types
- **Touch Scan**: 16,673 (62.7%)
- **Rental**: 6,890 (25.9%)
- **Return**: 2,885 (10.9%)
- **Delivery**: 94 (0.4%)
- **Pickup**: 48 (0.2%)

### 3.2 Quality Grades Distribution
- **Grade A**: 5,174 items (45.3% of graded)
- **Grade B+**: 2,469 items (21.6%)
- **Grade B**: 1,777 items (15.5%)
- **Grade A-**: 1,424 items (12.5%)
- **Grade A+**: 238 items (2.1%)
- **Lower Grades (C-, B-, C)**: 15 items total

### 3.3 Identifier Type Distribution
- **QR Code**: 42,224 items (64.0%)
- **None**: 12,477 items (18.9%)
- **Bulk**: 9,714 items (14.7%)
- **Sticker**: 1,480 items (2.2%)
- **RFID**: 47 items (0.07%)

### 3.4 Store Distribution (Top 5)
- Store 6800: 22,371 items
- Store 000: 19,567 items
- Store 3607: 4,338 items
- Store 8101: 3,048 items
- Store 728: 3,010 items

### 3.5 Data Freshness Metrics
- **ItemMaster Average**: 37.8 days since last scan
- **Transactions Average**: 63.2 days old
- **Oldest Active Data**: December 2024
- **Most Recent Activity**: August 29, 2025

---

## 4. Business Logic Relationships

### 4.1 Inventory Type Relationships

#### Identifier Type Hierarchy
1. **RFID Items** (47 items)
   - Full tracking capability
   - Real-time location updates
   - Automatic quality tracking

2. **QR Code Items** (42,224 items)
   - Semi-automated tracking
   - Manual scan required
   - Most common type (64%)

3. **Sticker Items** (1,480 items)
   - Basic barcode tracking
   - Legacy system items

4. **Bulk Items** (9,714 items)
   - Quantity-based tracking
   - No individual item tracking
   - Used for consumables

5. **None Type** (12,477 items)
   - Manual tracking only
   - Legacy or untagged items

### 4.2 Store Location Consistency

#### Cross-Table Store References
- ItemMaster: `current_store`, `home_store` (mostly NULL)
- POS Integration: `pos_store_mapping` table
- Store Correlations: `store_correlations` table
- Store Summary Views: `store_summary_view`, `v_store_performance`

#### Store Hierarchy
- Primary stores: 6800, 000, 3607, 8101, 728
- Total mapped stores: 5 in POS mapping
- Store performance tracking: 6 stores in views

### 4.3 Transaction Lifecycle

#### Typical Item Journey
1. **Creation**: Item added to ItemMaster
2. **Ready to Rent**: Quality checked, bin assigned
3. **Rental**: Transaction created, status → "On Rent"
4. **Return**: Return transaction, quality reassessed
5. **Maintenance**: Repair/cleaning transactions if needed
6. **Ready to Rent**: Cycle repeats

#### Contract Lifecycle
1. **Contract Creation**: LaundryContractStatus entry
2. **Item Assignment**: ContractSnapshot created
3. **Finalization**: Status → "finalized"
4. **Return**: Status → "returned"
5. **Pickup**: Optional pickup tracking

### 4.4 Status Field Implications

#### ItemMaster Status States
- **Ready to Rent**: Available for rental
- **On Rent**: Currently rented out
- **Needs to be Inspected**: Quality check required
- **Repair**: Maintenance needed
- **Wet**: Drying required
- **Sold**: Removed from rental pool
- **Missing**: Location unknown

#### Transaction Status Meanings
- **Touch Scan**: Inventory verification
- **Rental**: Item going out
- **Return**: Item coming back
- **Delivery**: Transport to customer
- **Pickup**: Collection from customer

---

## 5. Integration Points

### 5.1 POS System Integration

#### Tables Involved
- `pos_transactions`: 246,361 records
- `pos_transaction_items`: 597,368 records
- `pos_customers`: 137,303 records
- `pos_equipment`: 21,000 records
- `pos_store_mapping`: 5 stores

#### Integration Fields
- Equipment mapping via `item_num` field
- Customer correlation via `client_name`
- Store synchronization via store IDs
- Financial data via turnover fields

### 5.2 RFID API Synchronization

#### Sync Points
- `RefreshState` table tracks last sync
- `data_source` field = 'RFID_API' for imported items
- Incremental refresh pattern (last: 2025-08-30 02:00:37)

#### Data Flow
1. API polls for changes
2. Updates ItemMaster records
3. Creates Transaction records for events
4. Updates RefreshState timestamp

### 5.3 External System Mappings

#### Executive Dashboards
- `bi_executive_kpis`: 3 KPIs
- `executive_payroll_trends`: 328 records
- `executive_kpi`: 6 metrics

#### Analytics Views
- `equipment_performance_view`: 21,000 items
- `store_summary_view`: 6 stores
- `v_store_performance`: 6 stores

---

## 6. Data Validation Rules

### 6.1 Field Validation Requirements

#### Required Fields
- **ItemMaster**: `tag_id` (PK)
- **Transaction**: `id`, `tag_id`, `scan_type`, `scan_date`, `common_name`
- **All Tables**: Primary keys must be unique

#### Format Validations
- **tag_id**: VARCHAR(255), typically 24-character hex
- **dates**: DATETIME format (YYYY-MM-DD HH:MM:SS)
- **quality**: Enum values (A+, A, A-, B+, B, B-, C+, C, C-)
- **status**: Predefined status values per table

### 6.2 Business Rule Constraints

#### Inventory Rules
1. Each tag_id must be unique across ItemMaster
2. rental_class_num should map to valid rental class
3. Quality degradation: A+ → A → A- → B+ → B → B- → C
4. Status transitions must follow lifecycle rules

#### Transaction Rules
1. scan_date cannot be future dated
2. Contract numbers should follow format patterns
3. Quality assessments require condition flags
4. Repair transactions need location_of_repair

### 6.3 Data Integrity Checks

#### Critical Validations
1. **Orphan Prevention**: Transactions should have matching ItemMaster
2. **Duplicate Prevention**: No duplicate tag_ids in ItemMaster
3. **Referential Integrity**: rental_class_num → rental_class_id
4. **Data Freshness**: Items not scanned > 360 days generate alerts

#### Quality Metrics
- **Tag Coverage**: 96.3% of transactions have valid ItemMaster
- **Class Coverage**: 99.8% of rental classes are mapped
- **Location Coverage**: 18.9% of items have bin locations
- **Quality Coverage**: 17.3% of items have quality grades

---

## 7. Recommendations for Improvement

### 7.1 Data Quality Improvements

#### High Priority
1. **Populate NULL status fields** (81% NULL in ItemMaster)
2. **Map unmapped rental classes** (210 items unmapped)
3. **Resolve orphaned transactions** (974 records)
4. **Standardize quality grading** (82.7% missing)

#### Medium Priority
1. Enable date_created/date_updated timestamps
2. Implement item_num as secondary identifier
3. Populate manufacturer and department fields
4. Enable financial tracking fields (turnover, costs)

### 7.2 Schema Optimizations

#### Suggested Indexes
1. Composite index on (status, quality, bin_location)
2. Date range index for transaction queries
3. Text search index on common_name fields

#### Denormalization Opportunities
1. Cache current rental status in ItemMaster
2. Maintain item location history
3. Pre-calculate utilization metrics

### 7.3 Integration Enhancements

#### API Improvements
1. Implement real-time event streaming
2. Add webhook notifications for status changes
3. Enable bulk update operations
4. Implement data validation webhooks

#### POS Integration
1. Sync financial data (turnover fields)
2. Map all equipment to POS items
3. Enable customer data correlation
4. Implement transaction reconciliation

---

## 8. AI and Predictive Analytics Readiness

### 8.1 Available Features for ML Models

#### High-Value Features
- **Temporal**: date_last_scanned, scan_date patterns
- **Categorical**: status, quality, identifier_type
- **Numerical**: days_since_scan, transaction_count
- **Location**: bin_location, store assignments

#### Derived Features
- Utilization rate (rental days / total days)
- Quality degradation rate
- Seasonal demand patterns
- Store performance metrics

### 8.2 Predictive Model Opportunities

1. **Demand Forecasting**: Predict rental demand by category
2. **Quality Prediction**: Forecast quality degradation
3. **Maintenance Scheduling**: Predict repair needs
4. **Inventory Optimization**: Recommend reorder points
5. **Customer Segmentation**: Identify rental patterns

### 8.3 Data Volume Assessment

- **Sufficient for**: Basic predictive models, trend analysis
- **Insufficient for**: Deep learning, complex NLP
- **Recommended minimum**: 100K+ transactions for robust models

---

## Appendix A: SQL Query Examples

### Find Orphaned Records
```sql
-- Orphaned transactions
SELECT t.* 
FROM id_transactions t
LEFT JOIN id_item_master im ON t.tag_id = im.tag_id
WHERE im.tag_id IS NULL;

-- Unmapped rental classes
SELECT DISTINCT im.rental_class_num
FROM id_item_master im
LEFT JOIN user_rental_class_mappings urcm 
  ON im.rental_class_num = urcm.rental_class_id
WHERE im.rental_class_num IS NOT NULL 
  AND urcm.rental_class_id IS NULL;
```

### Data Quality Analysis
```sql
-- Field completion rates
SELECT 
  COUNT(*) as total_items,
  COUNT(status) as with_status,
  COUNT(quality) as with_quality,
  COUNT(bin_location) as with_location,
  ROUND(COUNT(status) * 100.0 / COUNT(*), 2) as status_pct,
  ROUND(COUNT(quality) * 100.0 / COUNT(*), 2) as quality_pct,
  ROUND(COUNT(bin_location) * 100.0 / COUNT(*), 2) as location_pct
FROM id_item_master;
```

### Business Intelligence Queries
```sql
-- Item utilization by category
SELECT 
  urcm.category,
  urcm.subcategory,
  COUNT(DISTINCT im.tag_id) as total_items,
  SUM(CASE WHEN im.status = 'On Rent' THEN 1 ELSE 0 END) as on_rent,
  ROUND(SUM(CASE WHEN im.status = 'On Rent' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as utilization_pct
FROM id_item_master im
JOIN user_rental_class_mappings urcm ON im.rental_class_num = urcm.rental_class_id
WHERE im.rental_class_num IS NOT NULL
GROUP BY urcm.category, urcm.subcategory
ORDER BY utilization_pct DESC;
```

---

## Appendix B: Data Dictionary

### Common Abbreviations
- **PK**: Primary Key
- **FK**: Foreign Key
- **NULL**: Allows null values
- **YTD**: Year to Date
- **LTD**: Life to Date
- **POS**: Point of Sale
- **API**: Application Programming Interface

### Status Codes
- **Ready to Rent**: Available inventory
- **On Rent**: Currently rented
- **Repair**: Under maintenance
- **Sold**: Removed from inventory
- **Missing**: Location unknown

### Quality Grades
- **A+**: Excellent condition
- **A**: Very good condition
- **A-**: Good condition
- **B+**: Above average condition
- **B**: Average condition
- **B-**: Below average condition
- **C**: Poor condition

---

## Document Version History
- **v1.0** (2025-08-30): Initial comprehensive analysis
- Generated using live database analysis
- 65,942 items analyzed across 46 tables

---

*End of Document*