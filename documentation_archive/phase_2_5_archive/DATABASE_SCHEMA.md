# RFID Database Schema Documentation

**Last Updated:** August 26, 2025  
**Database:** rfid_inventory (MariaDB)  
**Application:** RFID Dashboard - Broadway Tent and Event

This document provides a comprehensive overview of all database tables, their fields, relationships, and business purposes within the RFID inventory management system.

## 🏗️ Database Architecture Overview

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   CORE INVENTORY    │    │    TRANSACTIONS      │    │     ANALYTICS       │
│                     │    │                      │    │                     │
│ • id_item_master    │◄──►│ • id_transactions    │    │ • inventory_config  │
│ • id_rfidtag        │    │ • contract_snapshots │    │ • health_alerts     │
│ • seed_rental_class │    │ • hand_counted_items │    │ • item_usage_hist   │
└─────────────────────┘    └──────────────────────┘    │ • metrics_daily     │
           ▲                          ▲                └─────────────────────┘
           │                          │                
           ▼                          ▼                
┌─────────────────────┐    ┌──────────────────────┐    
│     MAPPINGS        │    │      UTILITIES       │    
│                     │    │                      │    
│ • rental_class_map  │    │ • refresh_state      │    
│ • user_rental_map   │    │ • laundry_status     │    
│ • hand_counted_cat  │    │                      │    
└─────────────────────┘    └──────────────────────┘    
```

---

## 📊 Core Inventory Tables

### 1. `id_item_master` - Master Inventory Dataset
**Purpose:** Primary inventory records - one record per RFID tag  
**Primary Key:** `tag_id`

| Field | Type | Nullable | Key | Description | Business Logic |
|-------|------|----------|-----|-------------|----------------|
| `tag_id` | VARCHAR(255) | NO | PRIMARY | RFID EPC code - unique identifier | Core business identifier |
| `uuid_accounts_fk` | VARCHAR(255) | YES |  | External system account reference | API integration |
| `serial_number` | VARCHAR(255) | YES |  | Manufacturer serial number | Asset tracking |
| `client_name` | VARCHAR(255) | YES |  | Client/customer name | Business relationship |
| `rental_class_num` | VARCHAR(255) | YES | INDEX | Links to seed_rental_classes | Category classification |
| `common_name` | VARCHAR(255) | YES |  | Human-readable item name | User interface display |
| `quality` | VARCHAR(50) | YES |  | Item condition (1-5 scale) | Pricing and availability logic |
| `bin_location` | VARCHAR(255) | YES | INDEX | Physical storage location | Warehouse management |
| `status` | VARCHAR(50) | YES | INDEX | Current item status | Business process control |
| `last_contract_num` | VARCHAR(255) | YES |  | Most recent rental contract | Revenue tracking |
| `last_scanned_by` | VARCHAR(255) | YES |  | Last person to scan item | Audit trail |
| `notes` | TEXT | YES |  | General notes and comments | Business context |
| `status_notes` | TEXT | YES |  | Status-specific notes | Operational details |
| `longitude` | DECIMAL(9,6) | YES |  | GPS longitude of last scan | Location tracking |
| `latitude` | DECIMAL(9,6) | YES |  | GPS latitude of last scan | Location tracking |
| `date_last_scanned` | DATETIME | YES | INDEX | When item was last scanned | Analytics foundation |
| `date_created` | DATETIME | YES |  | Record creation timestamp | Audit trail |
| `date_updated` | DATETIME | YES |  | Last update timestamp | Data freshness |

**Key Relationships:**
- `rental_class_num` → `seed_rental_classes.rental_class_id`
- `last_contract_num` → `id_transactions.contract_number`
- `tag_id` ← `id_transactions.tag_id` (one-to-many)

**Business Rules:**
- `status` values: "On Rent", "Ready to Rent", "Repair", "Needs to be Inspected"
- `bin_location` = "resale" triggers different business logic
- `date_last_scanned` drives stale item analysis in Tab 6

---

### 2. `id_rfidtag` - RFID Tag Metadata
**Purpose:** Extended RFID tag information and historical data  
**Primary Key:** `tag_id`

| Field | Type | Nullable | Description | Usage |
|-------|------|----------|-------------|-------|
| `tag_id` | VARCHAR(255) | NO | RFID EPC code | Links to id_item_master |
| `uuid_accounts_fk` | VARCHAR(255) | YES | Account reference | System integration |
| `category` | VARCHAR(255) | YES | Legacy category field | Superseded by rental_class mappings |
| `serial_number` | VARCHAR(255) | YES | Serial number | Duplicate of item_master data |
| `client_name` | VARCHAR(255) | YES | Client name | Historical data |
| `rental_class_num` | VARCHAR(255) | YES | Rental class | Cross-reference |
| `common_name` | VARCHAR(255) | YES | Item name | Display purposes |
| `quality` | VARCHAR(50) | YES | Condition rating | Historical tracking |
| `bin_location` | VARCHAR(255) | YES | Storage location | Historical data |
| `status` | VARCHAR(50) | YES | Item status | Historical tracking |
| `last_contract_num` | VARCHAR(255) | YES | Contract reference | Business tracking |
| `last_scanned_by` | VARCHAR(255) | YES | Scan operator | Audit trail |
| `notes` | TEXT | YES | General notes | Context |
| `status_notes` | TEXT | YES | Status notes | Operational info |
| `longitude` | DECIMAL(9,6) | YES | GPS longitude | Location data |
| `latitude` | DECIMAL(9,6) | YES | GPS latitude | Location data |
| `date_last_scanned` | DATETIME | YES | Last scan time | Temporal tracking |
| `date_created` | DATETIME | YES | Creation time | Historical record |
| `date_updated` | DATETIME | YES | Update time | Data freshness |

**Relationship:** Mirror/backup of `id_item_master` data

---

### 3. `seed_rental_classes` - Item Classification System
**Purpose:** Defines rental item categories and default settings  
**Primary Key:** `rental_class_id`

| Field | Type | Nullable | Description | Business Impact |
|-------|------|----------|-------------|----------------|
| `rental_class_id` | VARCHAR(255) | NO | Unique class identifier | Core classification system |
| `common_name` | VARCHAR(255) | YES | Standard item name | UI standardization |
| `bin_location` | VARCHAR(255) | YES | Default storage location | Warehouse efficiency |

**Key Relationships:**
- `rental_class_id` ← `id_item_master.rental_class_num` (one-to-many)
- `rental_class_id` ← `user_rental_class_mappings.rental_class_id` (one-to-one)

---

## 💼 Transaction Tables

### 4. `id_transactions` - Complete Transaction History
**Purpose:** All RFID scan events and business transactions  
**Primary Key:** `id` (auto-increment)

| Field | Type | Nullable | Key | Description | Analytics Value |
|-------|------|----------|-----|-------------|----------------|
| `id` | BIGINT | NO | PRIMARY | Unique transaction ID | System identifier |
| `contract_number` | VARCHAR(255) | YES | INDEX | Rental contract reference | Revenue correlation |
| `tag_id` | VARCHAR(255) | NO | INDEX | RFID tag scanned | Item correlation |
| `scan_type` | VARCHAR(50) | NO |  | "Touch", "Rental", "Return" | Business process tracking |
| `scan_date` | DATETIME | NO | INDEX | When scan occurred | Temporal analysis |
| `client_name` | VARCHAR(255) | YES |  | Customer name | Business intelligence |
| `common_name` | VARCHAR(255) | NO |  | Item name at time of scan | Historical accuracy |
| `bin_location` | VARCHAR(255) | YES |  | Location when scanned | Movement tracking |
| `status` | VARCHAR(50) | YES |  | Status when scanned | State change tracking |
| `scan_by` | VARCHAR(255) | YES |  | Operator who scanned | Audit and performance |
| `location_of_repair` | VARCHAR(255) | YES |  | Where repairs conducted | Service tracking |
| `quality` | VARCHAR(50) | YES |  | Condition at scan time | Degradation analysis |
| `dirty_or_mud` | BOOLEAN | YES |  | Cleaning required flag | Service scheduling |
| `leaves` | BOOLEAN | YES |  | Debris present | Condition tracking |
| `oil` | BOOLEAN | YES |  | Oil contamination | Specialized cleaning |
| `mold` | BOOLEAN | YES |  | Mold present | Health/safety concern |
| `stain` | BOOLEAN | YES |  | Stains present | Cleaning requirements |
| `oxidation` | BOOLEAN | YES |  | Rust/corrosion | Quality degradation |
| `other` | TEXT | YES |  | Other condition notes | Flexible condition tracking |
| `rip_or_tear` | BOOLEAN | YES |  | Physical damage | Repair scheduling |
| `sewing_repair_needed` | BOOLEAN | YES |  | Textile repair required | Service routing |
| `grommet` | BOOLEAN | YES |  | Grommet issues | Hardware repair |
| `rope` | BOOLEAN | YES |  | Rope/tie issues | Accessory maintenance |
| `buckle` | BOOLEAN | YES |  | Buckle problems | Hardware repair |
| `date_created` | DATETIME | YES |  | Record creation | Data provenance |
| `date_updated` | DATETIME | YES |  | Last modification | Data freshness |
| `uuid_accounts_fk` | VARCHAR(255) | YES |  | Account reference | System integration |
| `serial_number` | VARCHAR(255) | YES |  | Item serial number | Cross-validation |
| `rental_class_num` | VARCHAR(255) | YES |  | Item classification | Category analysis |
| `longitude` | DECIMAL(9,6) | YES |  | GPS longitude | Location intelligence |
| `latitude` | DECIMAL(9,6) | YES |  | GPS latitude | Geographic analysis |
| `wet` | BOOLEAN | YES |  | Wet condition flag | Drying requirements |
| `service_required` | BOOLEAN | YES |  | Service needed flag | Workflow automation |
| `notes` | TEXT | YES |  | Transaction notes | Context preservation |

**Key Relationships:**
- `tag_id` → `id_item_master.tag_id`
- `contract_number` → Contract management system
- `rental_class_num` → `seed_rental_classes.rental_class_id`

**Analytics Usage:**
- **Tab 6 Stale Items:** Compares `scan_date` with `id_item_master.date_last_scanned`
- **Usage Patterns:** Analyzes `scan_type` frequency and patterns
- **Data Discrepancies:** Identifies mismatches between master and transaction data

---

### 5. `contract_snapshots` - Contract State History
**Purpose:** Point-in-time snapshots of contract item states  
**Primary Key:** `id` (auto-increment)

| Field | Type | Nullable | Key | Description | Purpose |
|-------|------|----------|-----|-------------|---------|
| `id` | BIGINT | NO | PRIMARY | Unique snapshot ID | System identifier |
| `contract_number` | VARCHAR(255) | NO | INDEX | Contract reference | Business correlation |
| `tag_id` | VARCHAR(255) | NO | INDEX | Item identifier | Inventory correlation |
| `client_name` | VARCHAR(255) | YES |  | Customer name | Business context |
| `common_name` | VARCHAR(255) | YES |  | Item name | Display information |
| `rental_class_num` | VARCHAR(255) | YES |  | Item classification | Category tracking |
| `status` | VARCHAR(50) | YES |  | Item status | State tracking |
| `quality` | VARCHAR(50) | YES |  | Condition rating | Quality monitoring |
| `bin_location` | VARCHAR(255) | YES |  | Storage location | Location tracking |
| `serial_number` | VARCHAR(255) | YES |  | Serial number | Asset identification |
| `notes` | TEXT | YES |  | Snapshot notes | Context |
| `snapshot_date` | DATETIME | NO | INDEX | When snapshot taken | Temporal reference |
| `snapshot_type` | VARCHAR(255) | NO |  | Type of snapshot | Process classification |
| `created_by` | VARCHAR(255) | YES |  | Who created snapshot | Audit trail |
| `latitude` | DECIMAL(9,6) | YES |  | GPS latitude | Location data |
| `longitude` | DECIMAL(9,6) | YES |  | GPS longitude | Geographic reference |

**Business Use:** Contract lifecycle management and audit trail

---

### 6. `id_hand_counted_items` - Manual Item Tracking
**Purpose:** Non-RFID items manually added to contracts  
**Primary Key:** `id` (auto-increment)

| Field | Type | Nullable | Key | Description | Use Case |
|-------|------|----------|-----|-------------|----------|
| `id` | INT | NO | PRIMARY | Unique record ID | System identifier |
| `contract_number` | VARCHAR(50) | NO | INDEX | Associated contract | Business correlation |
| `item_name` | VARCHAR(255) | NO |  | Item description | Manual entry |
| `quantity` | INT | NO |  | Number of items | Quantity tracking |
| `action` | VARCHAR(50) | NO |  | "Added" or "Removed" | Transaction type |
| `timestamp` | DATETIME | NO | INDEX | When action occurred | Temporal tracking |
| `user` | VARCHAR(50) | NO |  | Who performed action | Audit trail |

**Primary Use:** Tab 4 - Laundry contracts with non-RFID items

---

## 🎯 Analytics Tables (Phase 1-2)

### 7. `inventory_health_alerts` - Health Monitoring System
**Purpose:** Automated inventory health alerts and monitoring  
**Primary Key:** `id` (auto-increment)

| Field | Type | Nullable | Key | Description | Analytics Function |
|-------|------|----------|-----|-------------|-------------------|
| `id` | BIGINT | NO | PRIMARY | Unique alert ID | System identifier |
| `tag_id` | VARCHAR(255) | YES | INDEX | Specific item (if applicable) | Item-level alerts |
| `rental_class_id` | VARCHAR(255) | YES | INDEX | Item category | Category-level alerts |
| `common_name` | VARCHAR(255) | YES |  | Item name | Display purposes |
| `category` | VARCHAR(100) | YES | INDEX | Business category | Filtering and grouping |
| `subcategory` | VARCHAR(100) | YES | INDEX | Business subcategory | Drill-down analysis |
| `alert_type` | ENUM | NO | INDEX | Alert classification | Business logic routing |
| `severity` | ENUM | NO | INDEX | Alert importance | Prioritization |
| `days_since_last_scan` | INT | YES |  | Staleness measure | Threshold comparison |
| `last_scan_date` | DATETIME | YES |  | When last scanned | Temporal reference |
| `suggested_action` | TEXT | YES |  | Recommended response | Workflow guidance |
| `status` | ENUM | NO | INDEX | Alert state | Workflow tracking |
| `created_at` | TIMESTAMP | NO | INDEX | Alert creation time | Alert lifecycle |
| `acknowledged_at` | DATETIME | YES |  | When acknowledged | Response tracking |
| `acknowledged_by` | VARCHAR(255) | YES |  | Who acknowledged | Responsibility tracking |
| `resolved_at` | DATETIME | YES |  | When resolved | Resolution tracking |
| `resolved_by` | VARCHAR(255) | YES |  | Who resolved | Resolution accountability |

**Enum Values:**
- `alert_type`: 'stale_item', 'high_usage', 'low_usage', 'missing', 'quality_decline', 'resale_restock', 'pack_status_review'
- `severity`: 'low', 'medium', 'high', 'critical'  
- `status`: 'active', 'acknowledged', 'resolved', 'dismissed'

**Tab 6 Integration:** Powers Health Alerts dashboard with filtering and pagination

---

### 8. `item_usage_history` - Comprehensive Lifecycle Tracking
**Purpose:** Detailed item lifecycle event tracking for analytics  
**Primary Key:** `id` (auto-increment)

| Field | Type | Nullable | Key | Description | Analytics Value |
|-------|------|----------|-----|-------------|----------------|
| `id` | BIGINT | NO | PRIMARY | Unique history ID | System identifier |
| `tag_id` | VARCHAR(255) | NO | INDEX | Item identifier | Item correlation |
| `event_type` | ENUM | NO | INDEX | Type of lifecycle event | Event classification |
| `contract_number` | VARCHAR(255) | YES | INDEX | Associated contract | Business correlation |
| `event_date` | DATETIME | NO | INDEX | When event occurred | Temporal analysis |
| `duration_days` | INT | YES |  | Duration on rent | Utilization metrics |
| `previous_status` | VARCHAR(50) | YES |  | Status before change | State transition tracking |
| `new_status` | VARCHAR(50) | YES |  | Status after change | Current state |
| `previous_location` | VARCHAR(255) | YES |  | Location before move | Movement analysis |
| `new_location` | VARCHAR(255) | YES |  | Current location | Location intelligence |
| `previous_quality` | VARCHAR(50) | YES |  | Quality before change | Degradation tracking |
| `new_quality` | VARCHAR(50) | YES |  | Current quality | Quality analytics |
| `utilization_score` | DECIMAL(5,2) | YES |  | Algorithm-calculated usage | Performance scoring |
| `notes` | TEXT | YES |  | Event notes | Context preservation |
| `created_at` | TIMESTAMP | NO |  | Record creation | Data provenance |

**Enum Values:**
- `event_type`: 'rental', 'return', 'service', 'status_change', 'location_change', 'quality_change'

**Future Analytics:** Foundation for predictive modeling and lifecycle optimization

---

### 9. `inventory_config` - Configuration Management
**Purpose:** Flexible configuration storage for analytics parameters  
**Primary Key:** `id` (auto-increment)

| Field | Type | Nullable | Key | Description | Configuration Type |
|-------|------|----------|-----|-------------|-------------------|
| `id` | INT | NO | PRIMARY | Unique config ID | System identifier |
| `config_key` | VARCHAR(100) | NO | UNIQUE | Configuration identifier | Key-value system |
| `config_value` | JSON | NO |  | Configuration data | Flexible data storage |
| `description` | TEXT | YES |  | Configuration purpose | Documentation |
| `category` | VARCHAR(50) | YES | INDEX | Config grouping | Organization |
| `created_at` | TIMESTAMP | NO |  | Creation time | Audit trail |
| `updated_at` | TIMESTAMP | NO |  | Last update | Change tracking |

**Current Configurations:**
1. **alert_thresholds** (category: 'alerting')
   ```json
   {
     "stale_item_days": {
       "default": 30,
       "resale": 7, 
       "pack": 14
     },
     "high_usage_threshold": 0.8,
     "low_usage_threshold": 0.2,
     "quality_decline_threshold": 2
   }
   ```

2. **business_rules** (category: 'business')
   ```json
   {
     "resale_categories": ["Resale"],
     "pack_bin_locations": ["pack"],
     "rental_statuses": ["On Rent", "Delivered"],
     "available_statuses": ["Ready to Rent"],
     "service_statuses": ["Repair", "Needs to be Inspected"]
   }
   ```

3. **dashboard_settings** (category: 'ui')
   ```json
   {
     "default_date_range": 30,
     "critical_alert_limit": 50,
     "refresh_interval_minutes": 15,
     "show_resolved_alerts": false
   }
   ```

**Tab 6 Integration:** Powers Configuration management interface

---

### 10. `inventory_metrics_daily` - Performance Optimization
**Purpose:** Pre-calculated daily metrics for dashboard performance  
**Primary Key:** `id` (auto-increment)

| Field | Type | Nullable | Key | Description | Performance Benefit |
|-------|------|----------|-----|-------------|-------------------|
| `id` | BIGINT | NO | PRIMARY | Unique metric ID | System identifier |
| `metric_date` | DATE | NO | INDEX | Date of metrics | Temporal partitioning |
| `rental_class_id` | VARCHAR(255) | YES | INDEX | Item classification | Category analysis |
| `category` | VARCHAR(100) | YES | INDEX | Business category | Grouping |
| `subcategory` | VARCHAR(100) | YES | INDEX | Business subcategory | Drill-down |
| `total_items` | INT | NO |  | Total item count | Inventory size |
| `items_on_rent` | INT | NO |  | Currently rented | Active utilization |
| `items_available` | INT | NO |  | Available for rent | Capacity analysis |
| `items_in_service` | INT | NO |  | Under maintenance | Service load |
| `items_missing` | INT | NO |  | Missing/lost items | Loss tracking |
| `utilization_rate` | DECIMAL(5,2) | YES |  | Percentage utilization | Efficiency metric |
| `avg_rental_duration` | DECIMAL(8,2) | YES |  | Average days on rent | Business intelligence |
| `revenue_potential` | DECIMAL(10,2) | YES |  | Estimated daily revenue | Financial planning |
| `created_at` | TIMESTAMP | NO |  | Calculation time | Data freshness |

**Unique Key:** `(metric_date, rental_class_id)` - prevents duplicates

**Future Use:** High-performance dashboard queries and trend analysis

---

## 🗂️ Mapping Tables

### 11. `user_rental_class_mappings` - User-Defined Categories
**Purpose:** Business categorization system managed by users  
**Primary Key:** `rental_class_id`

| Field | Type | Nullable | Key | Description | Business Value |
|-------|------|----------|-----|-------------|---------------|
| `rental_class_id` | VARCHAR(50) | NO | PRIMARY | Links to seed_rental_classes | Category system |
| `category` | VARCHAR(100) | NO |  | Main business category | High-level grouping |
| `subcategory` | VARCHAR(100) | NO |  | Detailed subcategory | Granular classification |
| `short_common_name` | VARCHAR(50) | YES |  | Abbreviated display name | UI optimization |
| `created_at` | DATETIME | NO |  | Mapping creation | Audit trail |
| `updated_at` | DATETIME | NO |  | Last modification | Change tracking |

**Business Categories:** Tents, Linens, Tables, Chairs, Dance Floors, Staging, etc.
**Tab 6 Integration:** Powers category filtering throughout analytics

---

### 12. `rental_class_mappings` - System Default Categories
**Purpose:** Default categorization fallback system  
**Primary Key:** `rental_class_id`

| Field | Type | Nullable | Description | Relationship |
|-------|------|----------|-------------|--------------|
| `rental_class_id` | VARCHAR(50) | NO | Links to seed_rental_classes | System integration |
| `category` | VARCHAR(100) | NO | Default category | Fallback classification |
| `subcategory` | VARCHAR(100) | NO | Default subcategory | System defaults |
| `short_common_name` | VARCHAR(50) | YES | System display name | UI fallback |

**Priority:** User mappings override system mappings when present

---

### 13. `hand_counted_catalog` - Manual Item Templates
**Purpose:** Template system for commonly hand-counted items  
**Primary Key:** `id` (auto-increment)

| Field | Type | Nullable | Key | Description | Business Purpose |
|-------|------|----------|-----|-------------|-----------------|
| `id` | INT | NO | PRIMARY | Unique catalog ID | System identifier |
| `rental_class_id` | VARCHAR(50) | YES |  | Associated rental class | Category correlation |
| `item_name` | VARCHAR(255) | NO | UNIQUE | Standard item name | Template identifier |
| `hand_counted_name` | VARCHAR(255) | YES | INDEX | Custom display name | User-friendly naming |

**Usage:** Powers Tab 4 hand-counted item selection and UI customization

---

## ⚙️ Utility Tables

### 14. `refresh_state` - Data Synchronization State
**Purpose:** Tracks API data refresh status and timing  
**Primary Key:** `id` (auto-increment)

| Field | Type | Nullable | Description | System Function |
|-------|------|----------|-------------|-----------------|
| `id` | INT | NO | Unique state ID | System identifier |
| `last_refresh` | DATETIME | YES | When last refresh completed | Sync timing |
| `state_type` | VARCHAR(50) | YES | Type of refresh state | Process classification |

**State Types:** 'full_refresh', 'incremental_refresh', 'api_sync'

---

### 15. `laundry_contract_status` - Contract Status Tracking
**Purpose:** Specialized status tracking for laundry contracts  
**Primary Key:** Not specified (utility table)

| Field | Description | Business Function |
|-------|-------------|-------------------|
| Contract-specific status fields | Laundry workflow states | Tab 4 process management |

---

## 🔗 Relationship Matrix

### Primary Relationships
```
id_item_master (tag_id) ──┬── id_transactions (tag_id) [1:N]
                          ├── id_rfidtag (tag_id) [1:1]
                          ├── inventory_health_alerts (tag_id) [1:N]
                          └── item_usage_history (tag_id) [1:N]

seed_rental_classes (rental_class_id) ──┬── id_item_master (rental_class_num) [1:N]
                                         ├── user_rental_class_mappings [1:1]
                                         └── rental_class_mappings [1:1]

id_transactions (contract_number) ──┬── id_hand_counted_items [1:N]
                                     └── contract_snapshots [1:N]
```

### Analytics Relationships
```
Tab 6 Analytics Data Flow:
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│ id_item_master  │───►│ Stale Items      │───►│ Health Alerts       │
│ • date_last_scan│    │ Analysis         │    │ Generation          │
│ • bin_location  │    │                  │    │                     │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
         │                       │                        │
         ▼                       ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│ id_transactions │───►│ Usage Patterns   │───►│ Configuration       │
│ • scan_type     │    │ Analysis         │    │ Management          │
│ • scan_date     │    │                  │    │                     │
└─────────────────┘    └──────────────────┘    └─────────────────────┘
```

## 🎯 Business Logic Integration

### Status Values and Their Meanings
- **"On Rent"**: Item currently with customer
- **"Ready to Rent"**: Available inventory  
- **"Repair"**: Needs maintenance
- **"Needs to be Inspected"**: Requires quality check

### Location-Based Business Rules
- **`bin_location = "resale"`**: Different stale item thresholds (7 days vs 30 days)
- **`bin_location = "pack"`**: Pack-specific business logic (14-day threshold)
- **Location tracking**: GPS coordinates for mobile operations

### Quality Degradation Tracking
- **Quality Scale**: 1-5 rating system
- **Condition Flags**: Boolean flags for specific issues
- **Service Routing**: Automatic workflow based on condition

---

## 📈 Analytics and Performance

### Indexing Strategy
- **Primary Performance:** `tag_id`, `scan_date`, `contract_number`
- **Analytics Queries:** `date_last_scanned`, `status`, `category`
- **Filtering Support:** `alert_type`, `severity`, `rental_class_id`

### Data Volume Projections
- **Current Scale:** ~50,000 items, ~1M transactions
- **Growth Rate:** ~10,000 transactions/month
- **Performance Target:** <500ms query response times

### Future Scalability
- **Partitioning Strategy:** Date-based partitioning for large tables
- **Archive Strategy:** Move old transactions to archive tables
- **Performance Monitoring:** Query optimization based on usage patterns

---

This schema supports the full RFID Dashboard application from basic inventory management through advanced analytics, with a foundation for future AI/ML integration and business intelligence expansion.

**Last Updated:** August 26, 2025 - Phase 2 Complete