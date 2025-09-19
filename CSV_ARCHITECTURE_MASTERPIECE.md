# CSV Import Architecture Masterpiece
**Date:** September 18, 2025
**Vision:** Raw Data + Business Logic Transformation

## 🎯 **ARCHITECTURAL VISION**

### **Clean Separation of Concerns**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RAW DATA      │    │ TRANSFORMATION  │    │ BUSINESS VIEWS  │
│   LAYER         │    │   SERVICES      │    │    LAYER        │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ equipment_raw   │───▶│ Field Mapping   │───▶│ equipment_view  │
│ customers_raw   │    │ Business Rules  │    │ customers_view  │
│ transactions_raw│    │ Data Validation │    │ transactions_view│
│ transitems_raw  │    │ Type Conversion │    │ transitems_view │
│ scorecard_raw   │    │ Correlation     │    │ scorecard_view  │
│ payroll_raw     │    │ Enrichment      │    │ payroll_view    │
│ pl_raw          │    │ Cleanup Logic   │    │ pl_view         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Benefits of This Architecture**

1. **Data Preservation**: Every CSV column stored forever
2. **Business Agility**: Change transformations without re-import
3. **Debugging**: Always trace back to raw source
4. **Performance**: Transform on demand, not on import
5. **Versioning**: Different transformation rules over time
6. **Testing**: A/B test different business logic

## 🗄️ **RAW DATA TABLES**

### **Design Principle: Exact CSV Mirror**
- **Column names**: Exact match to CSV headers
- **Data types**: Minimal (mostly VARCHAR/TEXT for flexibility)
- **No transformations**: Pure data preservation
- **Import speed**: Fast 1:1 mapping

```sql
-- Raw equipment table (exact CSV structure)
CREATE TABLE equipment_raw (
    id INT PRIMARY KEY AUTO_INCREMENT,
    import_batch_id VARCHAR(50),
    import_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Exact CSV columns (171 total)
    KEY VARCHAR(50),
    Name VARCHAR(500),
    LOC VARCHAR(50),
    QTY VARCHAR(20),
    QYOT VARCHAR(20),
    SELL VARCHAR(20),
    DEP VARCHAR(20),
    DMG VARCHAR(20),
    Msg TEXT,
    SDATE VARCHAR(50),
    Category VARCHAR(100),
    TYPE VARCHAR(100),
    [... all 171 columns exactly as CSV ...]

    -- Import metadata
    source_file VARCHAR(255),
    row_number INT,
    import_status ENUM('pending', 'processed', 'error') DEFAULT 'pending'
);
```

## ⚙️ **TRANSFORMATION SERVICES**

### **Business Logic Layer**
```python
class EquipmentTransformationService:
    """Transform raw equipment data into business objects"""

    def transform_equipment(self, raw_row):
        return {
            'item_num': raw_row.KEY.strip(),
            'name': raw_row.Name.strip(),
            'location': raw_row.LOC.strip(),
            'quantity': self.parse_int(raw_row.QTY),
            'quantity_on_order': self.parse_int(raw_row.QYOT),
            'sell_price': self.parse_decimal(raw_row.SELL),
            'deposit': self.parse_decimal(raw_row.DEP),
            'damage_waiver': self.parse_decimal(raw_row.DMG),
            'manufacturer': raw_row.MANF.strip(),
            'category': raw_row.Category.strip(),

            # Rental structure
            'rental_periods': {
                'period_1_hours': self.parse_decimal(raw_row.PER1),
                'period_2_hours': self.parse_decimal(raw_row.PER2),
                # ... all periods
            },
            'rental_rates': {
                'rate_1': self.parse_decimal(raw_row.RATE1),
                'rate_2': self.parse_decimal(raw_row.RATE2),
                # ... all rates
            }
        }
```

## 📊 **BUSINESS VIEWS**

### **Clean Presentation Layer**
```sql
-- Business view with clean, readable fields
CREATE VIEW equipment_business AS
SELECT
    er.KEY as item_key,
    er.Name as equipment_name,
    er.LOC as location_code,
    CAST(er.QTY as UNSIGNED) as available_quantity,
    CAST(er.QYOT as UNSIGNED) as quantity_on_order,
    CAST(er.SELL as DECIMAL(10,2)) as selling_price,
    CAST(er.DEP as DECIMAL(10,2)) as deposit_required,
    er.Category as category,
    er.MANF as manufacturer,

    -- Computed business fields
    CASE
        WHEN er.Inactive = 'True' THEN false
        ELSE true
    END as is_active,

    -- Rental rate structure
    JSON_OBJECT(
        'periods', JSON_ARRAY(er.PER1, er.PER2, er.PER3, er.PER4, er.PER5),
        'rates', JSON_ARRAY(er.RATE1, er.RATE2, er.RATE3, er.RATE4, er.RATE5)
    ) as rental_structure

FROM equipment_raw er
WHERE er.import_status = 'processed';
```

## 🚀 **IMPLEMENTATION PLAN**

### **Phase 1: Raw Data Foundation**
1. Create raw tables for each CSV type (exact column match)
2. Build simple 1:1 import services (no transformation)
3. Test raw import speed and accuracy

### **Phase 2: Transformation Services**
1. Build business logic transformation services
2. Create data type conversion utilities
3. Implement business rule validation

### **Phase 3: Business Views**
1. Create clean business views from raw data
2. Update existing code to use business views
3. Maintain backward compatibility

### **Phase 4: Migration**
1. Migrate existing systems to use new architecture
2. Performance optimization
3. Documentation and testing

This architecture is a true work of art - clean, maintainable, and future-proof!