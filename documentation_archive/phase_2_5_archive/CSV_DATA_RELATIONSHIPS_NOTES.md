# CSV Data Relationships - Complete Mapping Notes

## 1. RFIDpro itemlistRFIDpro8.26.25.csv ↔ POS equip8.26.25.csv

### RFIDpro System-Only Fields (No POS Correlation):
- `id_item_master` → RFIDpro internal DB ID
- `uuid_accounts_fk` → RFIDpro company account identifier  
- `tag_id` → RFID HEX EPC code (not in POS, expanding with QR/RFID)
- `quality` → RFIDpro grading system only
- `bin_location` → RFIDpro warehouse location only
- `last_scanned_by` → RFIDpro user tracking only
- `notes` → RFIDpro notes only (for now)
- `status_notes`, `long`, `lat`, `date_last_scanned`, `date_created`, `date_updated` → All RFIDpro only

### Direct Field Correlations:
- `serial_number` (RFIDpro) ↔ `SerialNo` (POS equip)
- `rental_class_num` (RFIDpro - SOURCE OF TRUTH from seed CSV) ↔ `ItemNum` (POS equip) **[KEY CORRELATION]**
- `common_name` (RFIDpro) ↔ `Name` (POS equip)

**CRITICAL DATA FLOW**: RFIDpro `rental_class_num` comes from seed CSV via API refresh, NOT from POS data

### Complex/Algorithmic Correlations:
- `client_name` + `last_contract_num` (RFIDpro) → Requires multi-CSV lookup:
  - POS transactions: `Contract No` → `Customer No` 
  - POS customer: `Customer No` for customer data
  - POS transitems: `Contract No` + `ItemNum` cross-reference

- `status` (RFIDpro) → Algorithm from POS transactions `Status` for open contracts

### POS equip CSV Key Fields:
- `Key` → Unique ID for serialized items (bulk for future expansion)
- `Loc` → POS location (not currently used)
- `Category` → **FILTER OUT: "UNUSED"/"NON CURRENT ITEMS" (old data)**
- `Department` → POS only, not utilized currently  
- `Type Desc` → Sales vs rental vs other item types (POS only)
- `Qty` → Quantity (serialized=1, bulk=multiple, not strict rule)
- `Home Store`/`Current Store` → POS only (**RFIDpro only at store 003-8101**)
- `Group` → POS only, not utilized
- `MANF` → Manufacturer 
- `Period` fields → Hours-based data
- All financial/rental rate fields → **Important for analytics**

## 2. POS transactions8.26.25.csv ↔ RFIDpro transactionsRFIDpro8.29.25.csv

### Primary Link:
- `Contract No` (POS transactions) ↔ `contract_number` (RFIDpro transactions) ↔ `last_contract_num` (RFIDpro itemlist) **[KEY CORRELATION]**

### Status Fields:
- `Stat` (POS) → Work orders/repair (not currently used)
- `Status` (POS) → **Rental cycle: Quote, Open, Closed, Completed, Unknown** ↔ `status` (RFIDpro)

### Customer Correlation:
- `Customer No` (POS transactions) → Links to customer CSV 
- `client_name` (RFIDpro) → User-typed name (error-prone)
- **Contract number more reliable than customer name**

### Financial Data:
- `Rent Amt`, `Sale Amt`, `Tax Amt`, `Total`, `Total Paid`, etc. (POS) → **NOT in RFIDpro but super useful for analytics**

### Store Issue:
- `Store No` (POS) vs **RFIDpro only at store 003-8101** → Needs strategic solution

### RFIDpro Transaction Details:
**scan_type Field (RFIDpro-only operational):**
- `Touch` → Inventory scan or status change (wet → ready to rent)
- `Rental` → Item going out on contract
- `Delivered` → Item delivered to customer
- `Returned` → Contract closing in RFIDpro system

**Quality Inspection Fields (Future Analytics Value):**
- `dirty_or_mud`, `leaves`, `oil`, `mold`, `stain`, `oxidation`, `rip_or_tear`, `sewing_repair_needed`, `grommet`, `rope`, `buckle`, `wet`, `service_required`

**Date Fields (Independent Meanings):**
- POS: `Contract Date`, `Close Date`, `Delivery Date`, `Pickup Date` → Contract lifecycle
- RFIDpro: `scan_date` → Physical scan timestamp

## 3. POS customer8.26.25.csv - Customer Data Chain

### Customer Linkage Chain:
- `CNUM` (customer CSV) = `Customer No` (transactions CSV) = lookup for RFIDpro `client_name` **[KEY CORRELATION]**

### Customer Financial Data:
- `YTD Payments`, `LTD Payments`, `CurrentBalance`, etc. → **Not currently used but will be integrated**

## 4. POS transitems8.26.25.csv - The Bridge Table

### Critical Bridge Function:
- `Contract No` + `ItemNum` (transitems) = **Bridge between contracts and specific equipment** **[KEY CORRELATION]**

### Links:
- `Contract No` → matches POS transactions (contract details)
- `ItemNum` → matches POS equip (equipment details)
- **Shows exactly which items were on which contracts**

### Line Status:
- **Need clarification on abbreviations and correlations** (unknown currently)

## 5. Key Data Flow Summary

**Complete Data Chain:**
1. **Equipment**: POS equip ↔ RFIDpro itemlist (via `ItemNum`/`rental_class_num`)
2. **Contracts**: POS transactions ↔ RFIDpro transactions (via `Contract No`)
3. **Items-on-Contracts**: POS transitems bridges contracts to equipment (`Contract No` + `ItemNum`)
4. **Customers**: POS customer provides full data via `CNUM` → `Customer No`

**Critical Integration Points:**
- **ItemNum** (POS equip) = **rental_class_num** (RFIDpro itemlist)
- **Contract No** across all transaction systems
- **Customer No/CNUM** for customer data chain
- Store 003-8101 RFIDpro limitation vs multi-store POS data

**Empty Database Tables to Populate:**
- RentalClassMapping (0 records) → Use rental_class_num correlations
- RFIDTag (0 records) → Use tag_id/HEX EPC data  
- HandCountedItems (0 records) → Use scan/touch data

**Data Quality Issues:**
- 81% ItemMaster records have NULL status
- 81% missing rental_class_num assignments  
- 83% missing quality grades
