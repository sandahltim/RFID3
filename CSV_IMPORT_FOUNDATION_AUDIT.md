# CSV Import Foundation Audit - Systematic Fix Plan
**Date:** September 18, 2025
**Issue:** Rat's nest of CSV import issues found in foundation

## 🚨 **CRITICAL ISSUES IDENTIFIED**

### **1. Manual Import Route Problems**
- **Equipment Import**: Method signature error (too many arguments)
- **Transaction Items**: "Unsupported file type: transaction_items"
- **Incomplete Service Integration**: Not all import services connected

### **2. CSV Coverage Analysis**

| CSV File | Columns | Import Service | Manual Route | Status |
|----------|---------|----------------|--------------|---------|
| equipPOS | 171 | ✅ equipment_import_service.py | ❌ Signature error | BROKEN |
| customer | 84 | ✅ csv_import_service.py | ✅ Working | OK |
| transactions | 109 | ✅ csv_import_service.py | ✅ Working | OK |
| transitems | 45 | ✅ transitems_import_service.py | ❌ Not connected | MISSING |
| scorecard | 22 | ✅ scorecard_csv_import_service.py | ✅ Just added | FIXED |
| PayrollTrends | 17 | ✅ payroll_import_service.py | ✅ Just added | FIXED |
| PL | 40+ | ✅ pnl_import_service.py | ✅ Working | OK |

### **3. Database Schema Verification Needed**
- **pos_equipment**: Does it have ALL 171 equipPOS columns?
- **Correlation tables**: Are they properly structured?
- **Financial tables**: Do they match CSV structures?

## 🔧 **SYSTEMATIC FIX PLAN**

### **Phase 1: Fix Immediate Import Issues**
1. Fix equipment import method signature
2. Add transitems (transaction_items) support
3. Verify all method parameters match
4. Test each CSV type individually

### **Phase 2: Database Schema Verification**
1. Compare pos_equipment table with equipPOS CSV (171 columns)
2. Verify customer table matches customer CSV (84 columns)
3. Check transaction tables match CSV structures
4. Ensure all import services write to correct tables

### **Phase 3: Comprehensive Testing**
1. Test import of each CSV type with small batch
2. Verify data actually reaches database tables
3. Check for column mapping errors
4. Document any missing columns

## 📊 **CSV STRUCTURE ANALYSIS**

### **POS Equipment (171 columns)**
```
KEY,Name,LOC,QTY,QYOT,SELL,DEP,DMG,Msg,SDATE,Category,TYPE,TaxCode,INST,FUEL,ADDT,
PER1-PER10 (10 columns),RATE1-RATE10 (10 columns),
RCOD,SUBR,PartNumber,NUM,MANF,MODN,DSTN,DSTP,RMIN,RMAX,UserDefined1,UserDefined2,
[... 120+ more columns including financial, vendor, specifications, etc.]
```

### **Unique Format CSVs**
- **Scorecard**: Week-based performance metrics (dynamic week columns)
- **PayrollTrends**: Store-specific payroll by 2-week periods
- **PL**: Profit & Loss with store breakdown and complex accounting structure

### **Transaction Data (2 types)**
- **transactions.csv**: Contract/transaction headers (109 columns)
- **transitems.csv**: Line items within transactions (45 columns)

## 🎯 **ROOT CAUSE**
The manual import system was built incrementally without systematic verification that all CSV types and columns are properly supported. Multiple import services exist but aren't properly integrated into the manual import route.

## ✅ **FIX PRIORITY**
1. **CRITICAL**: Fix equipment import (26MB file, 171 columns)
2. **HIGH**: Add transitems support (95MB file, transaction details)
3. **MEDIUM**: Verify database schemas match CSV structures
4. **LOW**: Optimize import performance for large files

This systematic audit reveals the foundation needs comprehensive verification and fixes.