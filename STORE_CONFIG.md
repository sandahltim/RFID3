# Store Configuration Reference 🏪

## Overview
This document serves as the authoritative reference for all store locations, IDs, and mappings used throughout the RFID Inventory Management System.

## Store Mappings (OFFICIAL)

| Store ID | Store Name | Location | POS Code | Item Count | Status |
|----------|------------|----------|-----------|------------|--------|
| **6800** | Brooklyn Park | Brooklyn Park, MN | 002 | ~22,000 | 🟢 Primary |
| **3607** | Wayzata | Wayzata, MN | 001 | ~5,000 | 🟢 Active |
| **8101** | Fridley | Fridley, MN | 003 | ~3,000 | 🟢 Active |
| **728** | Elk River | Elk River, MN | 004 | ~3,000 | 🟢 Active |
| **000** | Legacy/Unassigned | Multiple | 000 | ~20,000 | 🟡 Cleanup Needed |

## Historical Context

### ❌ Previous Incorrect Mappings (FIXED)
- ~~8101 = "Anoka"~~ → **CORRECTED** to "Fridley"
- ~~728 = "St. Paul"~~ → **CORRECTED** to "Elk River"

### ✅ Correct Mappings (Current)
- **6800** = Brooklyn Park ✓
- **3607** = Wayzata ✓  
- **8101** = Fridley ✓ (was incorrectly "Anoka")
- **728** = Elk River ✓ (was incorrectly "St. Paul")

## Code Implementation

### Centralized Configuration
All store mappings are now centralized in:
```python
# app/config/stores.py
STORES = {
    '6800': StoreInfo(name='Brooklyn Park', location='Brooklyn Park, MN', ...),
    '3607': StoreInfo(name='Wayzata', location='Wayzata, MN', ...),
    '8101': StoreInfo(name='Fridley', location='Fridley, MN', ...),
    '728': StoreInfo(name='Elk River', location='Elk River, MN', ...)
}
```

### Usage in Components
- **Executive Dashboard** (`tab7.py`): Uses centralized `STORE_MAPPING`
- **Global Filters** (`global_filters.html`): Updated with correct names
- **Inventory Analytics** (`inventory_analytics.html`): Consistent store names
- **All Templates**: Reference centralized configuration

### Database Schema
```sql
-- Store mappings table (if using database storage)
CREATE TABLE store_mappings (
    pos_store_code VARCHAR(3) PRIMARY KEY,  -- 001, 002, 003, 004
    store_id VARCHAR(10) NOT NULL,          -- 3607, 6800, 8101, 728
    store_name VARCHAR(50) NOT NULL,        -- Wayzata, Brooklyn Park, etc.
    location VARCHAR(100),                  -- Full address
    status ENUM('active', 'inactive') DEFAULT 'active'
);

INSERT INTO store_mappings VALUES
('001', '3607', 'Wayzata', 'Wayzata, MN', 'active'),
('002', '6800', 'Brooklyn Park', 'Brooklyn Park, MN', 'active'),
('003', '8101', 'Fridley', 'Fridley, MN', 'active'),
('004', '728', 'Elk River', 'Elk River, MN', 'active');
```

## Data Validation

### Current Item Distribution
Based on database analysis (as of 2025-08-27):
```sql
SELECT home_store, COUNT(*) as items 
FROM id_item_master 
WHERE home_store IS NOT NULL 
GROUP BY home_store 
ORDER BY items DESC;

-- Results:
-- 6800: 22,358 items (Brooklyn Park)
-- 000:  19,572 items (Legacy/Unassigned) 
-- 3607:  5,468 items (Wayzata)
-- 8101:  3,053 items (Fridley)
-- 728:   3,014 items (Elk River)
```

### Executive Dashboard Validation
Recent financial data showing corrected store names:
- **Fridley (8101)**: $177,276 revenue (highest performing)
- **Brooklyn Park (6800)**: $105,828 revenue  
- **Wayzata (3607)**: $63,423 revenue
- **Elk River (728)**: $52,832 revenue

## Maintenance Guidelines

### When Adding New Stores
1. Update `app/config/stores.py` with new `StoreInfo`
2. Add database record to `store_mappings` table
3. Update all HTML templates with new options
4. Test Executive Dashboard store filtering
5. Verify inventory analytics display
6. Update documentation (this file)

### When Modifying Existing Stores
1. **NEVER** change store IDs (6800, 3607, etc.) - these are primary keys
2. Store names can be updated in `stores.py`
3. Always test Executive Dashboard after changes
4. Update approximate item counts periodically
5. Verify all APIs return correct data

### Code Quality Standards
- **Single Source of Truth**: All store data comes from `app/config/stores.py`
- **Type Safety**: Use `StoreInfo` named tuple for structure
- **Validation**: Always validate store IDs with `validate_store_id()`
- **Fallbacks**: Provide sensible defaults for unknown store IDs
- **Documentation**: Update this file with any changes

## Integration Points

### Components Using Store Data
1. **Executive Dashboard (Tab 7)**: Financial analytics by store
2. **Inventory Analytics (Tab 6)**: Activity tracking by location
3. **Global Filters**: Cross-tab store filtering  
4. **All Tabs**: Store-aware data display
5. **API Endpoints**: Store parameter filtering
6. **Reports**: Store-based report generation

### External Systems
- **POS Integration**: Maps POS codes (001-004) to store IDs
- **CSV Imports**: Uses store IDs in data files
- **API Clients**: Reference store IDs for filtering
- **Mobile App**: Will use store IDs for location-based features

## Troubleshooting

### Common Issues
1. **"Unknown Store" in UI**: Check if store ID exists in `stores.py`
2. **Financial data missing**: Verify CSV import used correct store IDs
3. **Filter not working**: Ensure API endpoints handle store parameter
4. **Inconsistent names**: All components should use `get_store_name()`

### Debugging Commands
```bash
# Check store distribution in database
mysql -u rfid_user -p rfid_inventory -e "
  SELECT home_store, COUNT(*) FROM id_item_master 
  WHERE home_store IS NOT NULL GROUP BY home_store;"

# Test Executive Dashboard API  
curl "http://localhost:8101/api/executive/store_comparison?weeks=4"

# Verify store filtering works
curl "http://localhost:8101/api/executive/dashboard_summary?store=6800"
```

## Future Enhancements

### Planned Features
- **Dynamic Store Management**: Admin interface to add/modify stores
- **Store Performance Metrics**: Automated KPI calculation by location
- **Geographic Mapping**: Integration with mapping services
- **Mobile Store Selection**: Location-based store detection

### Database Enhancements
- **Store hierarchy**: Support for regions/districts
- **Store metadata**: Hours, contact info, specializations
- **Historical tracking**: Store name changes over time
- **Performance optimization**: Dedicated store dimension table

---

**Last Updated**: 2025-08-27  
**Version**: 2025-08-27-v1  
**Maintained By**: RFID Development Team

⚠️ **IMPORTANT**: This document is the authoritative source for store information. All code changes affecting store mappings must be reflected here.