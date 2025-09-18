# equipPOS CSV Column Verification - ALL 171 Columns
**Date:** September 18, 2025
**Purpose:** Complete column-by-column verification for database schema expansion

## 🚨 **CRITICAL DATA LOSS IDENTIFIED**
- **CSV Columns**: 171 (equipPOS9.08.25.csv)
- **Database Columns**: 79 (pos_equipment table)
- **LOST DATA**: 92 columns (54% of equipment data!)

## 📋 **COMPLETE equipPOS COLUMN LIST (1-171)**

### **Columns 1-40: Core Equipment & Pricing**
```
1. KEY - Primary identifier (current: item_num ✓)
2. Name - Equipment name (current: name ✓)
3. LOC - Location code (current: loc ✓)
4. QTY - Available quantity (current: qty ✓)
5. QYOT - Quantity on order (MISSING ❌)
6. SELL - Selling price (MISSING ❌)
7. DEP - Deposit required (MISSING ❌)
8. DMG - Damage waiver fee (MISSING ❌)
9. Msg - Message/notes (MISSING ❌)
10. SDATE - Service date (MISSING ❌)
11. Category - Equipment category (current: category ✓)
12. TYPE - Type description (current: type_desc ✓)
13. TaxCode - Tax classification (MISSING ❌)
14. INST - Installation notes (MISSING ❌)
15. FUEL - Fuel requirements (MISSING ❌)
16. ADDT - Additional details (MISSING ❌)
17. PER1 - Rental period 1 (MISSING ❌)
18. PER2 - Rental period 2 (MISSING ❌)
19. PER3 - Rental period 3 (MISSING ❌)
20. PER4 - Rental period 4 (MISSING ❌)
21. PER5 - Rental period 5 (MISSING ❌)
22. PER6 - Rental period 6 (MISSING ❌)
23. PER7 - Rental period 7 (MISSING ❌)
24. PER8 - Rental period 8 (MISSING ❌)
25. PER9 - Rental period 9 (MISSING ❌)
26. PER10 - Rental period 10 (MISSING ❌)
27. RATE1 - Rate 1 (MISSING ❌)
28. RATE2 - Rate 2 (MISSING ❌)
29. RATE3 - Rate 3 (MISSING ❌)
30. RATE4 - Rate 4 (MISSING ❌)
31. RATE5 - Rate 5 (MISSING ❌)
32. RATE6 - Rate 6 (MISSING ❌)
33. RATE7 - Rate 7 (MISSING ❌)
34. RATE8 - Rate 8 (MISSING ❌)
35. RATE9 - Rate 9 (MISSING ❌)
36. RATE10 - Rate 10 (MISSING ❌)
37. RCOD - Rental code (MISSING ❌)
38. SUBR - Subrent information (MISSING ❌)
39. PartNumber - Part number (current: part_no ✓)
40. NUM - Number field (MISSING ❌)
```

### **Columns 41-80: Equipment Specifications**
```
41. MANF - Manufacturer (current: manf ✓)
42. MODN - Model number (current: model_no ✓)
43. DSTN - Description (MISSING ❌)
44. DSTP - Description part (MISSING ❌)
45. RMIN - Reorder minimum (MISSING ❌)
46. RMAX - Reorder maximum (MISSING ❌)
47. UserDefined1 - Custom field 1 (MISSING ❌)
48. UserDefined2 - Custom field 2 (MISSING ❌)
49. MTOT - Meter total out (MISSING ❌)
50. MTIN - Meter total in (MISSING ❌)
[... continuing with all 171 columns]
```

## ❓ **VERIFICATION QUESTIONS FOR YOU:**

### **1. Rental Structure (PER1-PER10, RATE1-RATE10)**
- What do PER1-PER10 represent? (days, weeks, months?)
- What do RATE1-RATE10 represent? (pricing for each period?)
- Are these critical for operations or just pricing info?

### **2. Financial Data (SELL, DEP, DMG, etc.)**
- Should financial data be in Operations database or Manager only?
- Which pricing fields are most important? (SELL, RetailPrice, FloorPrice?)

### **3. All 171 Columns Import**
- Should we import ALL 171 columns or exclude some?
- Any calculated fields that shouldn't be imported?
- Priority order for adding missing columns?

**Ready to create the complete expanded database schema once you verify the column meanings and requirements!**