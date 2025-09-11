# 🎛️ PHASE 3 CONFIGURABLE VARIABLES 
*Variables identified during hardcode elimination that should be user-configurable*

**Generated**: 2025-09-05  
**Source**: Executive Dashboard Hardcode Elimination  
**Status**: Ready for Config UI Development  
**Related Docs**: See `HARDCODE_FIXES_PROGRESS_LOG.md`, `STORE_CONFIG.md`, `docs/Configuration_Management_Guide.md`  

## 📊 PERFORMANCE THRESHOLDS

### **Utilization Metrics**
```javascript
// executive_dashboard.html:2203, 2227, 2343
UTILIZATION_EXCELLENT = 75%    // >= 75% = green/positive
UTILIZATION_GOOD = 50%         // >= 50% = yellow/neutral  
UTILIZATION_POOR = <50%        // < 50% = red/negative
```

### **Health Score Thresholds**
```javascript  
// executive_dashboard.html:2212, 2236, 2351
HEALTH_EXCELLENT = 85          // >= 85 = green/positive
HEALTH_GOOD = 70              // >= 70 = yellow/neutral
HEALTH_POOR = <70             // < 70 = red/negative  
```

### **Growth Rate Indicators**  
```javascript
// executive_dashboard.html:2219, 2243, 2358
GROWTH_STRONG = 5%            // > 5% = strong growth ↗️
GROWTH_DECLINE = -5%          // < -5% = declining ↘️  
GROWTH_STABLE = -5% to 5%     // = stable →
```

## 🎨 STORE VISUAL IDENTITY

### **Store Color Themes**
```css
/* executive_dashboard.html:659-674 */
STORE_3607_WAYZATA = #3498db (Blue)
STORE_6800_BROOKLYN = #2ecc71 (Green)  
STORE_728_ELKRIVER = #f1c40f (Yellow)
STORE_8101_FRIDLEY = #e67e22 (Orange)
```

### **Store Manager Names** 
⚠️ **Note**: Store mappings already exist in `STORE_CONFIG.md` - integrate with existing system
```javascript
// executive_dashboard.html:2153-2156 - CONSOLIDATE WITH STORE_CONFIG.md
STORE_3607_MANAGER = "Tyler" (Since 2008)
STORE_6800_MANAGER = "Zack" (Since 2022)  
STORE_728_MANAGER = "Bruce" (Since 2024)
STORE_8101_MANAGER = "Tim" (Since 2022)
```

## 📈 CALCULATION PARAMETERS

### **Revenue Variance Simulation** 
```javascript
// executive_dashboard.html:2189-2191
WEEKLY_VARIANCE_MIN = 95%      // 0.95 minimum weekly variation
WEEKLY_VARIANCE_MAX = 105%     // 1.05 maximum weekly variation  
RANDOM_VARIANCE_RANGE = 10%    // 0.1 total range (95%-105%)
```

### **YoY Calculation Fallback**
```javascript  
// executive_dashboard.html:2187
YOY_FALLBACK_RATE = 95%        // 0.95 when no real YoY data available
```

## 🔧 CHART CONFIGURATION

### **Chart Default Values**
```javascript
// executive_dashboard.html:1812, 1996, 2039  
DEFAULT_REVENUE_BASE = $50,000     // Base revenue for calculations
CURRENCY_FORMAT_K_THRESHOLD = 1,000    // Switch to "K" format  
CURRENCY_FORMAT_M_THRESHOLD = 1,000,000 // Switch to "M" format
```

### **Animation & Display Settings**
```javascript
// executive_dashboard.html:27-29, 1445
KPI_ANIMATION_DURATION = 2000ms    // Counter animation duration
KPI_UPDATE_DELAY = 500ms           // Initial update delay  
ANIMATION_FPS = 60                 // Animation frame rate
```

## 🏢 BUSINESS RULES

### **Store Operational Dates**  
⚠️ **Note**: Store operational data already exists in `STORE_CONFIG.md` - consolidate
```html
<!-- executive_dashboard.html:857-866 - INTEGRATE WITH EXISTING STORE SYSTEM -->
STORE_3607_SINCE = "2008"     // Wayzata founding year (existing in STORE_CONFIG.md)
STORE_6800_SINCE = "2022"     // Brooklyn Park founding year
STORE_8101_SINCE = "2022"     // Fridley founding year
STORE_728_SINCE = "2024"      // Elk River founding year
```

### **Data Source Architecture**
⚠️ **Note**: Already documented in `HARDCODE_FIXES_PROGRESS_LOG.md` - reference existing
```javascript
// Based on user requirements - SEE HARDCODE_FIXES_PROGRESS_LOG.md for details
EXECUTIVE_DASHBOARD_DATA_SOURCE = "P&L"           // Financial perspective
MANAGER_DASHBOARD_DATA_SOURCE = "ScoreCard"       // Operational perspective  
LABOR_METRICS_DATA_SOURCE = "Payroll"            // Both dashboards use for labor
```

## 🎯 IMPLEMENTATION PRIORITY

**HIGH PRIORITY** (Business Critical):
- Performance thresholds (utilization, health, growth)
- Store color themes and branding
- Calculation parameters

**MEDIUM PRIORITY** (User Experience):  
- Chart defaults and formatting
- Animation settings
- Display preferences

**LOW PRIORITY** (Administrative):
- Store founding dates  
- Manager name assignments
- Data source routing rules

## 📝 NOTES FOR DEVELOPER

1. **Integration Required**: Consolidate with existing config systems:
   - `STORE_CONFIG.md` for store mappings
   - `docs/Configuration_Management_Guide.md` for config architecture  
   - `HARDCODE_FIXES_PROGRESS_LOG.md` for business rules
2. **Validation Required**: All percentage thresholds should be 0-100 range
3. **Color Picker**: Store colors should use colorpicker UI component  
4. **Real-time Update**: Changes should reflect immediately in dashboard
5. **Backup/Restore**: Config should be exportable/importable
6. **User Roles**: Some settings may need admin-only access
7. **Database Integration**: Use existing `inventory_config` table structure

## 🔗 CONSOLIDATION NEEDED

**Duplicate Store Information**:
- This document identifies manager names and founding dates  
- `STORE_CONFIG.md` has authoritative store mappings
- **Action**: Extend existing store config rather than duplicate

**Configuration Architecture**:
- This document identifies UI thresholds
- `docs/Configuration_Management_Guide.md` has config system architecture
- **Action**: Follow existing patterns from database config table

**Total Configurable Items**: 25+ variables identified  
**Estimated Config UI Screens**: 4-5 organized by category  
**Integration Work**: Consolidate with 3 existing config systems

---

## ✅ PHASE 3 COMPLETION UPDATE (2025-09-10)

### **IMPLEMENTATION STATUS: COMPLETE AND REFINED** 🚀
- ✅ **Executive Dashboard Configuration UI**: Fully implemented and validated
- ✅ **Labor Cost Configuration**: Field ID mismatches FIXED - now fully functional
- ✅ **Store Goals Configuration**: Integrated from standalone page into main config UI
- ✅ **All Variable Forms Created**: 20+ new form fields added across 8 configuration tabs
- ✅ **Current Week Functionality**: `current_week_view_enabled` toggle working perfectly
  - **Implementation**: Complete end-to-end functionality with dynamic headers
  - **Database Schema**: `current_week_view_enabled TINYINT(1) DEFAULT 1`
  - **User Control**: Configuration UI checkbox toggles column visibility
  - **Dashboard Response**: JavaScript dynamically shows/hides current week column
  - **Headers**: Show actual calculation periods from config (e.g., "Curr Week (3w avg)")
  - **Status**: ✅ FULLY FUNCTIONAL - Users can control scorecard display and see periods
- ✅ **Real-time Updates**: All changes persist immediately via API
- ✅ **Integration Complete**: UI matches API structure 100%

### **CONFIGURATION SYSTEM CLEANUP (2025-09-10)**:
- ✅ **Labor Cost Tab**: Fixed JavaScript field ID mismatches, added missing form fields
- ✅ **Store Goals Tab**: Added complete UI with company-wide and store-specific goals
- ✅ **All 8 Tabs Functional**: Prediction, Correlation, BI, Integration, Preferences, Executive, Labor, Goals
- ✅ **API Endpoints Tested**: All configuration APIs working and validated
- ✅ **Documentation Updated**: Comprehensive technical mapping added

### **KEY VARIABLES NOW CONFIGURABLE**:
- ✅ Query time limits (financial_kpis_debug_weeks, location_kpis_revenue_weeks, etc.)
- ✅ Utilization scoring thresholds (excellent/good/fair/poor % + points)  
- ✅ Health scoring parameters (base/min/max scores)
- ✅ Revenue tier thresholds (tier_1/2/3 values + points)
- ✅ Current week view preferences and controls
- ✅ Labor cost analysis settings and alert thresholds
- ✅ Store-specific revenue, contract, and operational goals

### **UI SCREENS DELIVERED**: 
- ✅ **Complete Configuration Interface**: 8 fully functional tabs
- ✅ **Bootstrap Integration**: Navbar functional across all tabs with proper styling
- ✅ **Form Validation**: Min/max ranges and proper data types throughout
- ✅ **Professional Styling**: Fortune 500-level UI components with store branding
- ✅ **Store-Specific Elements**: Color-coded cards and badges for multi-location goals

**STATUS: PRODUCTION READY AND BATTLE-TESTED** 🚀  