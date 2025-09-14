# RFID3 Database Schema Analysis for Contract Management UI

## Executive Summary
This document provides a comprehensive analysis of the RFID3 database structure, focusing on tables and relationships necessary for building a contract management UI with RFID/EPC assignment capabilities.

## 1. Core Tables for Contract/Rental Management

### 1.1 Contract Tables

#### **pos_transactions** (Primary Contract Table)
- **Purpose**: Stores all POS transaction/contract data from external accounting system
- **Key Fields**:
  - `contract_no` (String, PK) - Unique contract identifier
  - `store_no` (String) - Store location
  - `customer_no` (String) - Links to customer data
  - `status` (String) - Contract status (Active, Closed, etc.)
  - `contract_date` (DateTime) - Contract creation date
  - `close_date` (DateTime) - Contract closure date
  - `completed_date` (DateTime) - Contract completion date
  - `parent_contract` (String) - For linked/sub-contracts
  - Financial fields: `total`, `deposit`, `tax`, `discount`, etc.
- **Indexes**: contract_no, customer_no, contract_date, status, store_no
- **Unique Constraint**: (contract_no, store_no)

#### **contract_snapshots**
- **Purpose**: Historical tracking of items assigned to contracts
- **Key Fields**:
  - `contract_number` (String) - Links to pos_transactions.contract_no
  - `tag_id` (String) - RFID tag identifier
  - `snapshot_date` (DateTime) - When snapshot was taken
  - `status`, `quality`, `bin_location` - Item state at snapshot time
  - `client_name`, `common_name` - Customer and item details
- **Use Case**: Track historical contract assignments and item states

#### **laundry_contract_status**
- **Purpose**: Track specialized laundry/rental contract workflow states
- **Key Fields**:
  - `contract_number` (String, Unique) - Links to contract
  - `status` (String) - Contract lifecycle status
  - `finalized_date`, `returned_date`, `pickup_date` - Workflow dates
  - `finalized_by`, `returned_by`, `pickup_by` - User tracking
- **Use Case**: Manage contract lifecycle states and transitions

### 1.2 Contract Line Items

#### **pos_transaction_items**
- **Purpose**: Individual line items within contracts
- **Key Fields**:
  - `contract_no` (String, FK) - Links to pos_transactions
  - `item_num` (String) - Item SKU/number
  - `qty` (Integer) - Quantity
  - `line_status` (String) - RX (Reserved), RR (Returned), S (Sold), etc.
  - `due_date` (DateTime) - Expected return date
  - `price`, `dmg_wvr` - Pricing and damage waiver
- **Unique Constraint**: (contract_no, line_number)

## 2. RFID/EPC Item Tables

### 2.1 Primary Item Tables

#### **id_item_master** (Master Item Registry)
- **Purpose**: Central repository for all RFID-tracked items
- **Key Fields**:
  - `tag_id` (String, PK) - RFID EPC code (HEX format)
  - `item_num` (Integer, Unique) - Internal item number
  - `serial_number` (String) - Manufacturer serial
  - `rental_class_num` (String) - Item type/category
  - `status` (String) - Current item status
  - `last_contract_num` (String) - Most recent contract assignment
  - `identifier_type` (String) - NULL for RFID items, 'None' for manual
  - Location: `bin_location`, `home_store`, `current_store`
  - Financial: `turnover_ytd`, `repair_cost_ltd`, `sell_price`
- **RFID Detection**: Items with NULL identifier_type and HEX EPC pattern

#### **id_rfidtag** (RFID Tag Registry)
- **Purpose**: Simplified RFID tag tracking
- **Key Fields**:
  - `tag_id` (String, PK) - RFID EPC code
  - `rental_class_num` (String) - Item category
  - `status` (String) - Tag status
  - `last_contract_num` (String) - Last assignment
  - `category`, `common_name` - Item classification

### 2.2 Item Tracking Tables

#### **id_transactions** (Item Movement History)
- **Purpose**: Track all item scans and movements
- **Key Fields**:
  - `tag_id` (String) - RFID identifier
  - `contract_number` (String) - Associated contract
  - `scan_type` (String) - Type of scan/transaction
  - `scan_date` (DateTime) - When scanned
  - `status` (String) - Item status at scan
  - Damage indicators: `dirty_or_mud`, `leaves`, `oil`, `mold`, `stain`, etc.
  - Service flags: `sewing_repair_needed`, `service_required`
  - `location_of_repair` (String) - Repair location tracking

#### **item_usage_history**
- **Purpose**: Comprehensive item lifecycle tracking
- **Key Fields**:
  - `tag_id` (String) - RFID identifier
  - `event_type` (Enum) - rental, return, service, status_change, location_change, quality_change
- **Use Case**: Track complete item history for analytics

## 3. Customer & Reservation Tables

### 3.1 Customer Data

#### **pos_customers**
- **Purpose**: Customer master data from POS
- **Key Fields**:
  - `cnum` (String) - Customer number
  - `name` (String) - Customer name
  - `key` (String, Unique) - Unique customer identifier
  - Contact info: `phone`, `work_phone`, `mobile_phone`
  - Address fields: `address`, `city`, `zip`
- **Links To**: pos_transactions.customer_no

### 3.2 Reservation Tracking

**Note**: No dedicated reservation table exists. Reservations are tracked through:
- **pos_transactions** with specific status values
- **pos_transaction_items** with `line_status = 'RX'` (Reserved)
- **Financial models** track reservation metrics:
  - `reservation_value_next_14_days`
  - `total_reservation_value`
  - Store-specific: `total_on_reservation_[store_no]`

## 4. Status & Service Tracking

### 4.1 Status Values (Common Across Tables)

#### Item Status Options (id_item_master.status):
- Available/In-Stock
- On Contract/Rented
- In Repair/Service
- Cleaning/Processing
- Lost/Missing
- Damaged/Write-off
- Reserved

#### Line Status Options (pos_transaction_items.line_status):
- **RX** - Reserved (on reservation)
- **RR** - Returned from rental
- **S** - Sold
- **D** - Delivered
- **P** - Picked up

### 4.2 Service & Repair Tracking

Service records are tracked through:
1. **id_transactions** table:
   - Damage flags (dirty_or_mud, oil, mold, etc.)
   - Service flags (sewing_repair_needed, service_required)
   - location_of_repair field

2. **item_usage_history** table:
   - event_type = 'service' for service records
   - Comprehensive event tracking

3. **Status fields** in id_item_master:
   - status = 'In Repair' or 'Cleaning'
   - status_notes for detailed information

## 5. Integration & Correlation Tables

### 5.1 POS-RFID Integration

#### **pos_rfid_correlations**
- **Purpose**: Map POS items to RFID-tracked items
- **Key Fields**:
  - `pos_item_num` (String) - POS SKU
  - `rfid_tag_id` (String) - Specific RFID tag
  - `rfid_rental_class_num` (String) - RFID item category
  - `correlation_type` (String) - Mapping strategy
  - `confidence_score` - Correlation confidence
- **Use Case**: Bridge POS and RFID systems for unified tracking

#### **pos_inventory_discrepancy**
- **Purpose**: Track inventory mismatches
- **Key Fields**:
  - `contract_no` - Related contract
  - `discrepancy_type` - Type of issue (missing, double_booked, etc.)
- **Use Case**: Identify and resolve inventory conflicts

## 6. Key Relationships & Foreign Keys

### Primary Relationships:
1. **Contract → Items**:
   - pos_transactions.contract_no → pos_transaction_items.contract_no
   - pos_transactions.contract_no → contract_snapshots.contract_number
   - pos_transactions.contract_no → id_item_master.last_contract_num

2. **Customer → Contracts**:
   - pos_customers.cnum → pos_transactions.customer_no

3. **RFID → Items**:
   - id_item_master.tag_id = id_rfidtag.tag_id
   - id_item_master.tag_id → id_transactions.tag_id
   - id_item_master.tag_id → item_usage_history.tag_id

4. **POS → RFID Mapping**:
   - pos_transaction_items.item_num → pos_rfid_correlations.pos_item_num
   - pos_rfid_correlations.rfid_tag_id → id_item_master.tag_id

## 7. Contract Management UI Requirements Mapping

### 7.1 Assign RFID EPC Codes to Items
**Tables Involved**:
- UPDATE `id_item_master` SET tag_id = [EPC_CODE]
- UPDATE `id_rfidtag` SET tag_id = [EPC_CODE]
- INSERT INTO `pos_rfid_correlations` for POS mapping

### 7.2 Add/Remove Items from Contracts
**Tables Involved**:
- INSERT/DELETE `pos_transaction_items`
- UPDATE `id_item_master` SET last_contract_num = [CONTRACT_NO]
- INSERT `contract_snapshots` for history
- INSERT `id_transactions` for movement tracking

### 7.3 Assign Items to Reservations
**Tables Involved**:
- UPDATE `pos_transaction_items` SET line_status = 'RX'
- UPDATE `id_item_master` SET status = 'Reserved'
- Track in financial models reservation fields

### 7.4 Update Item Status (Repair/Cleaning/Service)
**Tables Involved**:
- UPDATE `id_item_master` SET status = [NEW_STATUS]
- INSERT `id_transactions` with service flags
- INSERT `item_usage_history` with event_type = 'service'
- UPDATE `id_transactions` damage/service boolean fields

### 7.5 Process Returns from Contracts
**Tables Involved**:
- UPDATE `pos_transaction_items` SET line_status = 'RR'
- UPDATE `id_item_master` SET status = 'Available', last_contract_num = NULL
- UPDATE `laundry_contract_status` SET returned_date = NOW()
- INSERT `id_transactions` with scan_type = 'return'

### 7.6 Integrate with POS Data
**Tables Involved**:
- Query `pos_transactions` for contract data
- Join `pos_transaction_items` for line items
- Use `pos_rfid_correlations` for item mapping
- Check `pos_inventory_discrepancy` for conflicts

## 8. Data Quality Considerations

### 8.1 Active vs Historical Data
- **Active Contracts**: pos_transactions WHERE status IN ('Active', 'Open')
- **Historical**: contract_snapshots for point-in-time records
- **Archive Strategy**: Move closed contracts older than X months

### 8.2 Data Integrity Issues to Monitor
1. **Orphaned Items**: id_item_master with last_contract_num not in pos_transactions
2. **Double Bookings**: Items appearing in multiple active contracts
3. **Missing Correlations**: pos_transaction_items without pos_rfid_correlations
4. **Status Mismatches**: Item status doesn't match contract status

### 8.3 Critical Missing Relationships
1. No direct FK constraint between id_item_master.last_contract_num and pos_transactions.contract_no
2. No enforced relationship between pos_customers and pos_transactions
3. Missing cascade rules for contract deletion/updates

## 9. Recommended SQL Queries for Contract Management

### Get All Items for a Contract:
```sql
SELECT
    pti.*,
    im.tag_id,
    im.status as item_status,
    im.bin_location,
    prc.rfid_tag_id
FROM pos_transaction_items pti
LEFT JOIN pos_rfid_correlations prc ON pti.item_num = prc.pos_item_num
LEFT JOIN id_item_master im ON prc.rfid_tag_id = im.tag_id
WHERE pti.contract_no = ?
```

### Find Available Items for Assignment:
```sql
SELECT
    tag_id,
    serial_number,
    common_name,
    bin_location
FROM id_item_master
WHERE status = 'Available'
AND last_contract_num IS NULL
AND identifier_type IS NULL  -- RFID items only
```

### Track Item Service History:
```sql
SELECT
    t.scan_date,
    t.scan_type,
    t.location_of_repair,
    t.sewing_repair_needed,
    t.service_required,
    t.dirty_or_mud,
    t.oil,
    t.mold
FROM id_transactions t
WHERE t.tag_id = ?
AND (t.service_required = true OR t.location_of_repair IS NOT NULL)
ORDER BY t.scan_date DESC
```

## 10. AI/Predictive Analytics Readiness

### 10.1 Available Features for ML Models:
- **Temporal Data**: Extensive date fields for time-series analysis
- **Usage Patterns**: item_usage_history provides complete lifecycle
- **Financial Metrics**: Turnover, repair costs, rental rates
- **Quality Indicators**: Damage flags, quality fields
- **Location Data**: GPS coordinates, store locations

### 10.2 Potential Target Variables:
- Item failure prediction (repair_needed flags)
- Contract completion probability (close_date patterns)
- Customer churn (contract frequency analysis)
- Inventory optimization (turnover rates)

### 10.3 Data Volume Assessment:
- Sufficient transaction history in id_transactions
- Rich damage/quality indicators for predictive maintenance
- Financial history for revenue optimization models

## 11. Implementation Recommendations

### Priority 1: Core Contract Management
1. Build UI for pos_transactions and pos_transaction_items CRUD
2. Implement RFID assignment through id_item_master updates
3. Create contract-item linking through pos_rfid_correlations

### Priority 2: Status & Workflow
1. Implement status update workflows for id_item_master
2. Add service/repair tracking through id_transactions
3. Build return processing with laundry_contract_status

### Priority 3: Integration & Analytics
1. Implement POS-RFID correlation management
2. Build discrepancy detection and resolution
3. Add reservation tracking and forecasting

### Priority 4: Data Quality & Governance
1. Implement orphaned item detection
2. Add double-booking prevention
3. Create data archival processes for historical contracts

## Next Steps
1. Review existing API endpoints for contract operations
2. Design UI mockups based on table structures
3. Implement data validation rules based on constraints
4. Create stored procedures for complex operations
5. Build real-time status tracking system