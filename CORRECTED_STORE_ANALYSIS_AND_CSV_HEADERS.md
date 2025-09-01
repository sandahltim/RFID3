# 🏢 Corrected Store Analysis & Critical CSV Header Analysis

**Updated**: August 31, 2025  
**Business Context**: KVC Companies - Minnesota Equipment Rental Operations

---

## 🎯 **CORRECTED Store Code Mappings**

### **Actual Store Profiles** *(Corrected from previous analysis)*

- **001-3607** = **Wayzata** (3607 Shoreline Drive, Wayzata, MN 55391)
  - **Business Mix**: 90% DIY/Construction + 10% Party Equipment  
  - **Delivery**: YES (DIY/Construction equipment delivery available)
  - **Specialization**: Lake Minnetonka area, DIY homeowners, contractors
  - **Service Area**: Wayzata, Lake Minnetonka communities

- **002-6800** = **Brooklyn Park** 
  - **Business Mix**: 100% DIY/Construction Equipment ONLY
  - **No Party/Tent Equipment** - Pure construction focus
  - **Delivery**: YES (Construction equipment delivery)
  - **Specialization**: Commercial contractors, industrial projects
  - **Service Area**: Brooklyn Park, northwest metro

- **003-8101** = **Fridley** 
  - **Business Mix**: 100% Tent/Party Equipment ONLY  
  - **No DIY/Construction Equipment** - Pure event focus (Broadway Tent & Event)
  - **Delivery**: YES (Party equipment delivery for events)
  - **Specialization**: Events, weddings, corporate functions
  - **Service Area**: Fridley, northeast metro, events across Twin Cities

- **004-728** = **Elk River**
  - **Business Mix**: 90% DIY/Construction + 10% Party Equipment
  - **Same profile as Wayzata** - Mixed service model  
  - **Delivery**: YES (Both equipment types)
  - **Specialization**: Rural/suburban, agricultural support, outdoor events
  - **Service Area**: Elk River, northwest suburbs

---

## 📊 **Critical Analysis of Three CSV Files**

### **1. ScorecardTrends8.26.25.csv - Executive KPIs**

**CRITICAL HEADER ANALYSIS:**

**Revenue Columns (Weeks ending Sunday):**
- `Total Weekly Revenue` - **Company-wide total**
- `3607 Revenue` - **Wayzata (90% DIY/10% Party)**
- `6800 Revenue` - **Brooklyn Park (100% DIY Construction ONLY)**
- `728 Revenue` - **Elk River (90% DIY/10% Party)**  
- `8101 Revenue` - **Fridley (100% Party/Events ONLY)**

**CRITICAL INSIGHT**: Revenue mix should reflect store specialization:
- **6800 (Brooklyn Park)** should show highest average transaction values (commercial construction)
- **8101 (Fridley)** should show seasonal spikes (wedding/event seasons)
- **3607 (Wayzata) & 728 (Elk River)** should show mixed patterns

**Activity Indicators:**
- `# New Open Contracts 3607/6800/728/8101` - **Contract volume by store**
- `# Deliveries Scheduled next 7 days 8101` - **Only tracking Fridley deliveries** (party events)
- `# Open Quotes 8101` - **Only tracking Fridley quotes** (event pipeline)

**CRITICAL ISSUE**: Why only track deliveries and quotes for 8101 (Fridley)? 
- Brooklyn Park (6800) does construction deliveries
- Wayzata (3607) and Elk River (728) offer deliveries for both equipment types

**Future Revenue Predictors:**
- `$ on Reservation - Next 14 days - [store]` - **Forward booking by store**
- `Total $ on Reservation [store]` - **Total pipeline by store**

**ANALYSIS**: 8101 (Fridley) reservations should show event seasonality patterns

**Financial Health Metrics:**
- `% -Total AR ($) > 45 days` - **Company-wide collection efficiency**
- `Total Discount $ Company Wide` - **Margin pressure indicator**
- `$ Total AR (Cash Customers)` - **Cash flow management**

---

### **2. PayrollTrends8.26.25.csv - Labor Efficiency**

**CRITICAL HEADER ANALYSIS:**

**Store Order in CSV**: 6800, 3607, 8101, 728
- This order suggests **6800 (Brooklyn Park)** may be the primary/largest operation

**Revenue Metrics per Store:**
- `Rental Revenue [store]` - **Pure equipment rental income**
- `All Revenue [store]` - **Total including sales, fees, damage waivers**

**CRITICAL INSIGHT**: 
- **6800 (Brooklyn Park)** should have highest rental/all revenue ratio (pure equipment focus)
- **8101 (Fridley)** may have lower ratio due to party service fees, setup charges

**Labor Metrics per Store:**
- `Payroll [store]` - **Weekly labor cost**
- `Wage Hours [store]` - **Total labor hours**

**CRITICAL ANALYSIS NEEDED**:
- **8101 (Fridley)** should have higher labor hours for event setup/teardown
- **6800 (Brooklyn Park)** should have highest revenue per labor hour (equipment-focused)
- **3607 (Wayzata) & 728 (Elk River)** should show mixed labor patterns

---

### **3. PL8.28.25.csv - Profit & Loss Analysis**

**CRITICAL HEADER STRUCTURE ANALYSIS:**

**Company Identification:**
- Row 1: `KVC Companies` - **Parent company name**
- Row 2: `Actual Monthly Cashflow` - **P&L focus**

**Time Period Structure:**
- **2021**: June-December (partial year)
- **2022**: Full year (January-December) + TTM (Trailing Twelve Months)
- **2023**: Full year + TTM
- **2024**: Partial year through current period + TTM
- **Additional columns**: % Tot Rev, PEG Target

**CRITICAL REVENUE ANALYSIS**:
Row 5: `Rental Revenue` - **Core business metric**

**CRITICAL QUESTIONS FOR P&L:**
1. **Are revenues consolidated** or broken down by store/business line?
2. **How are A1 Rent It vs Broadway Tent & Event** revenues separated?
3. **What are the PEG Targets** and how do they relate to store performance?
4. **TTM calculations** - Are they rolling 12-month windows?

---

## 🔍 **Critical Business Intelligence Gaps**

### **1. Store Delivery Tracking Inconsistency**
- **Issue**: Only 8101 (Fridley) delivery metrics tracked in scorecard
- **Impact**: Missing delivery performance for 3607, 6800, 728
- **Solution**: Implement delivery tracking for all stores offering delivery

### **2. Business Line Revenue Separation**
- **Issue**: No clear DIY vs Party revenue breakdown by store
- **Impact**: Cannot optimize equipment mix or seasonal planning
- **Solution**: Add business line revenue columns to scorecard

### **3. Labor Efficiency by Business Type**
- **Issue**: Party setup labor (8101) vs equipment rental labor (6800) mixed
- **Impact**: Cannot optimize staffing or pricing models
- **Solution**: Separate labor metrics by equipment type

### **4. Seasonal Pattern Recognition**
- **Issue**: P&L monthly data doesn't correlate with weekly operational data
- **Impact**: Cannot predict seasonal cash flow patterns
- **Solution**: Weekly financial metrics aligned with operational reporting

---

## 📈 **Corrected Business Intelligence Framework**

### **Store Specialization Analytics**

**Brooklyn Park (6800) - 100% Construction Focus:**
```sql
-- Should show highest revenue per transaction (commercial equipment)
-- Should have lowest labor ratio (equipment pickup vs setup)
-- Should have highest equipment utilization rates
```

**Fridley (8101) - 100% Party Focus:**
```sql
-- Should show seasonal revenue patterns (wedding season peaks)
-- Should have highest labor costs (setup/teardown)
-- Should track delivery/setup metrics heavily
```

**Wayzata (3607) & Elk River (728) - Mixed 90/10:**
```sql
-- Should show blended revenue patterns
-- Should optimize equipment mix seasonally
-- Should balance delivery/pickup operations
```

### **Revenue Flow Correlation**

**Corrected Chain:**
```
ScorecardTrends (by store specialization) → 
PayrollTrends (by labor type) → 
POS Transactions (by equipment category) →
RFID Equipment (by business line)
```

---

## 🚀 **Implementation Corrections Needed**

### **1. Update Equipment Categorization Service**
```python
# CORRECTED store profiles
STORE_PROFILES = {
    '3607': {'name': 'Wayzata', 'construction': 0.90, 'events': 0.10, 'delivery': True},
    '6800': {'name': 'Brooklyn Park', 'construction': 1.00, 'events': 0.00, 'delivery': True},
    '8101': {'name': 'Fridley', 'construction': 0.00, 'events': 1.00, 'delivery': True},
    '728': {'name': 'Elk River', 'construction': 0.90, 'events': 0.10, 'delivery': True}
}
```

### **2. Corrected Revenue Expectations**
- **Company-wide target**: ~75% Construction, ~25% Events (based on store mix)
- **6800 (Brooklyn Park)**: Should drive highest construction revenue
- **8101 (Fridley)**: Should drive all event revenue
- **3607 & 728**: Should provide balanced revenue streams

### **3. Seasonal Optimization**
- **Spring/Summer**: 8101 (Fridley) event peak, construction steady at 6800
- **Fall/Winter**: Construction focus at 6800, indoor events at 8101
- **Year-round**: 3607 & 728 provide stability with mixed offerings

---

## 🎯 **Next Steps for Accurate Implementation**

1. **Validate store addresses and confirm current operations**
2. **Analyze equipment inventory by actual store to validate specializations**  
3. **Review delivery logs to understand actual service patterns**
4. **Cross-reference POS data with store profiles**
5. **Update all analytics services with corrected store mappings**

This corrected analysis provides the accurate foundation for implementing Minnesota-specific business intelligence that reflects the actual operational structure of KVC Companies' equipment rental network. 🏢