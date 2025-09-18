# Complete CSV Import Specification & File Naming Structure
**Date:** September 18, 2025
**Purpose:** Systematic documentation of ALL CSV imports for foundation repair

## 📊 **CSV FILE NAMING PATTERNS & REQUIREMENTS**

### **Current Files in /shared/POR/ (Verified 2025-09-18)**

| CSV File | Naming Pattern | Columns | Size | Purpose | Import Service |
|----------|----------------|---------|------|---------|----------------|
| **equipPOS9.08.25.csv** | `equipPOS*.csv` | 171 | 26.17 MB | Equipment catalog | equipment_import_service.py |
| **customer9.08.25.csv** | `customer*.csv` | 84 | 50.8 MB | Customer database | csv_import_service.py |
| **transactions9.08.25.csv** | `transactions*.csv` | 109 | 101.69 MB | Contract transactions | csv_import_service.py |
| **transitems9.08.25.csv** | `transitems*.csv` | 45 | 95.32 MB | Transaction line items | transitems_import_service.py |
| **scorecard9.18.25.csv** | `scorecard*.csv` | 22 | 0.01 MB | Performance metrics | scorecard_csv_import_service.py |
| **PayrollTrends8.26.25.csv** | `PayrollTrends*.csv` | 17 | 0.01 MB | Labor costs by store | payroll_import_service.py |
| **PL8.28.25.csv** | `PL*.csv` | 40+ | 0.01 MB | Profit & Loss statements | pnl_import_service.py |

## 🗄️ **DATABASE TABLE COLUMN AUDIT**

### **CRITICAL ISSUE: Missing Columns in Database Tables**

| Table | Current Columns | CSV Columns | Missing | Data Loss |
|-------|-----------------|-------------|---------|-----------|
| **pos_equipment** | 79 | 171 | **92** | **54% DATA LOSS** |
| **pos_customers** | ? | 84 | ? | **UNKNOWN** |
| **pos_transactions** | ? | 109 | ? | **UNKNOWN** |
| **pos_transaction_items** | ? | 45 | ? | **UNKNOWN** |

---

## 📋 **equipPOS CSV COMPLETE COLUMN SPECIFICATION (171 Columns)**

### **Columns 1-20: Basic Item Information**
```
1. KEY - Primary identifier (item number)
2. Name - Equipment name/description
3. LOC - Location code
4. QTY - Available quantity
5. QYOT - Quantity on order
6. SELL - Selling price
7. DEP - Deposit required
8. DMG - Damage waiver fee
9. Msg - Message/notes
10. SDATE - Service date
11. Category - Equipment category
12. TYPE - Type description
13. TaxCode - Tax classification
14. INST - Installation notes
15. FUEL - Fuel requirements
16. ADDT - Additional details
17-20. [Need verification of meaning]
```

### **Columns 21-30: Rental Periods (PER1-PER10)**
```
17. PER1 - Rental period 1
18. PER2 - Rental period 2
19. PER3 - Rental period 3
20. PER4 - Rental period 4
21. PER5 - Rental period 5
22. PER6 - Rental period 6
23. PER7 - Rental period 7
24. PER8 - Rental period 8
25. PER9 - Rental period 9
26. PER10 - Rental period 10
```

### **Columns 31-40: Rental Rates (RATE1-RATE10)**
```
27. RATE1 - Rate for period 1
28. RATE2 - Rate for period 2
29. RATE3 - Rate for period 3
30. RATE4 - Rate for period 4
31. RATE5 - Rate for period 5
32. RATE6 - Rate for period 6
33. RATE7 - Rate for period 7
34. RATE8 - Rate for period 8
35. RATE9 - Rate for period 9
36. RATE10 - Rate for period 10
```

### **Columns 41-60: Equipment Details**
```
37. RCOD - Rental code
38. SUBR - Subrent information
39. PartNumber - Manufacturer part number
40. NUM - Number field
41. MANF - Manufacturer
42. MODN - Model number
43. DSTN - Description
44. DSTP - Description part
45. RMIN - Reorder minimum
46. RMAX - Reorder maximum
47. UserDefined1 - Custom field 1
48. UserDefined2 - Custom field 2
[... continuing with remaining columns]
```

## ❓ **VERIFICATION NEEDED FROM YOU**

**For equipPOS columns, I need clarification on:**

1. **What do PER1-PER10 represent?** (rental periods - days? weeks? months?)
2. **What do RATE1-RATE10 represent?** (pricing for each period?)
3. **Financial columns meaning?** (SELL vs RetailPrice vs FloorPrice?)
4. **Should ALL 171 columns be imported?** (some might be calculated fields?)

**Once you verify the meanings, I'll:**
1. Create complete database schema with ALL 171 columns
2. Update import service to handle every column
3. Test the import to ensure no data loss
4. Move to next CSV systematically