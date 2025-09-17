# API Database Verification Checklist

**Created:** 2025-09-17
**Purpose:** Verify API database schema before proceeding with implementation

## 📋 **Schema Verification Steps**

### **1. Database Structure Verification**
```bash
# Test database creation
mysql -u root -p < /home/tim/RFID3/api_database_schema.sql

# Verify tables created
mysql -u root -p -e "USE rfid_api_v1; SHOW TABLES;"

# Check table structures
mysql -u root -p -e "USE rfid_api_v1; DESCRIBE api_items;"
mysql -u root -p -e "USE rfid_api_v1; DESCRIBE api_transactions;"
mysql -u root -p -e "USE rfid_api_v1; DESCRIBE api_equipment;"
mysql -u root -p -e "USE rfid_api_v1; DESCRIBE api_correlations;"
```

### **2. Data Compatibility Check**
- [ ] **api_items** matches id_item_master structure
- [ ] **api_transactions** matches id_transactions structure
- [ ] **api_equipment** contains POS equipment fields
- [ ] **api_correlations** replaces equipment_rfid_correlations
- [ ] All indexes are properly created
- [ ] Foreign key constraints work

### **3. Column Mapping Verification**

#### **api_items ↔ id_item_master**
| API Column | Original Column | Status |
|------------|-----------------|---------|
| tag_id | tag_id | ✓ Exact match |
| rental_class_num | rental_class_num | ✓ Exact match |
| common_name | common_name | ✓ Exact match |
| status | status | ✓ Exact match |
| current_store | current_store | ✓ Exact match |
| identifier_type | identifier_type | ✓ Exact match |

#### **api_equipment ↔ pos_equipment**
| API Column | POS Column | Status |
|------------|------------|---------|
| item_num | item_num (normalized) | ⚠️ Remove .0 suffix |
| pos_item_num | item_num (original) | ✓ Preserve original |
| name | name | ✓ Exact match |
| category | category | ✓ Exact match |
| to_ytd | to_ytd | ✓ Exact match |
| current_store | current_store | ✓ Exact match |

### **4. Data Migration Test**
```sql
-- Test data migration queries
-- 1. Items migration
INSERT INTO rfid_api_v1.api_items
SELECT * FROM rfid_inventory.id_item_master LIMIT 100;

-- 2. Transactions migration
INSERT INTO rfid_api_v1.api_transactions
SELECT * FROM rfid_inventory.id_transactions LIMIT 100;

-- 3. Equipment migration (with normalization)
INSERT INTO rfid_api_v1.api_equipment (item_num, pos_item_num, name, category)
SELECT
    REPLACE(item_num, '.0', '') as item_num,
    item_num as pos_item_num,
    name,
    category
FROM rfid_inventory.pos_equipment LIMIT 100;

-- 4. Correlation migration
INSERT INTO rfid_api_v1.api_correlations
SELECT * FROM rfid_inventory.equipment_rfid_correlations LIMIT 100;
```

## 🔍 **Critical Verification Points**

### **Schema Accuracy**
- [ ] All current columns from id_item_master are included
- [ ] All current columns from id_transactions are included
- [ ] POS equipment fields properly mapped
- [ ] Correlation table maintains existing relationships

### **Data Types & Constraints**
- [ ] VARCHAR lengths match current usage
- [ ] DECIMAL precision correct for financial fields
- [ ] DATETIME fields properly configured
- [ ] Boolean fields default correctly
- [ ] Indexes created for performance

### **Relationships & Keys**
- [ ] Primary keys defined correctly
- [ ] Foreign keys maintain referential integrity
- [ ] Unique constraints prevent duplicates
- [ ] Indexes optimize common queries

## ⚠️ **Known Considerations**

### **RFIDpro Integration**
- Manual sync trigger only
- Preserve current external API calls until phased out
- Sync log tracks all external data imports

### **Store Code Mapping**
- Current stores: 3607, 6800, 728, 8101
- POS stores: 001→3607, 002→6800, 003→8101, 004→728
- Handle store code translation in API layer

### **Identifier Types**
- RFID items: identifier_type = 'None' (string, not NULL)
- QR items: identifier_type = 'QR'
- Handle string comparison properly

## 📊 **Performance Verification**

### **Index Testing**
```sql
-- Test index performance
EXPLAIN SELECT * FROM api_items WHERE rental_class_num = 'TEST123';
EXPLAIN SELECT * FROM api_transactions WHERE tag_id = 'TEST_TAG';
EXPLAIN SELECT * FROM api_equipment WHERE current_store = '3607';
EXPLAIN SELECT * FROM api_correlations WHERE pos_item_num = '12345.0';
```

### **Expected Results**
- [ ] All queries use indexes (no full table scans)
- [ ] Foreign key lookups are fast
- [ ] Complex joins perform reasonably

## ✅ **Approval Required**

**Before proceeding with API implementation, verify:**

1. [ ] Database schema created successfully
2. [ ] All tables have correct structure
3. [ ] Sample data migration works
4. [ ] Indexes improve query performance
5. [ ] No conflicts with existing database
6. [ ] All field mappings are accurate

**Sign-off:** _________________________
**Date:** ___________________________

---

**Next Steps After Approval:**
1. Create FastAPI application structure
2. Implement REST endpoints
3. Build operations UI
4. Configure nginx routing
5. Create deployment package