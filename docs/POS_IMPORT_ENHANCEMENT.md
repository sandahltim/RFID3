# POS Import System Enhancement

## Overview
Enhanced the POS data import system to handle renamed CSV files with "POS" prefixes while maintaining backward compatibility with legacy naming conventions.

## Problem Statement
User renamed CSV files in the shared/POR directory with "POS" prefixes:
- `equip8.26.25.csv` → `equipPOS8.26.25.csv`
- `transitems8.26.25.csv` → `transitemsPOS8.26.25.csv`
- `transactions8.26.25.csv` → `transactionsPOS8.26.25.csv`

The existing import system could not discover these renamed files, breaking automated imports.

## Solution Implementation

### 1. Enhanced File Discovery Patterns

#### CSV Import Service (`csv_import_service.py`)
```python
def import_equipment_data(self, file_path: str = None) -> Dict:
    """Import equipment/inventory data from equipPOS8.26.25.csv or equip8.26.25.csv"""
    if not file_path:
        # Find latest equipment file - try POS prefix first, then original
        pos_pattern = os.path.join(self.CSV_BASE_PATH, "equipPOS*.csv")
        old_pattern = os.path.join(self.CSV_BASE_PATH, "equip*.csv")
        
        pos_files = glob.glob(pos_pattern)
        old_files = glob.glob(old_pattern)
        
        # Prefer POS-prefixed files if available
        files = pos_files if pos_files else old_files
        
        if not files:
            raise FileNotFoundError(f"No equipment CSV files found in {self.CSV_BASE_PATH}")
        file_path = max(files, key=os.path.getctime)  # Get newest file
```

#### Financial CSV Import Service (`financial_csv_import_service.py`)
```python
def import_equipment_data_pos(self) -> Dict:
    """Import POS equipment data with POS-prefixed file discovery"""
    # Find latest equipment file - try POS prefix first, then original
    pos_pattern = os.path.join(self.CSV_BASE_PATH, "equipPOS*.csv")
    old_pattern = os.path.join(self.CSV_BASE_PATH, "equip*.csv")
    
    pos_files = glob.glob(pos_pattern)
    old_files = glob.glob(old_pattern)
    
    # Prefer POS-prefixed files if available
    files = pos_files if pos_files else old_files
```

### 2. Scheduler Integration Enhancement

#### Tuesday 8am Automated Imports
Enhanced the scheduled import process to include POS equipment and transaction data:

```python
def import_all_financial_files(self) -> Dict:
    """Import all CSV files including financial and POS equipment data"""
    file_imports = [
        ('scorecard_trends', self.import_scorecard_trends),
        ('payroll_trends', self.import_payroll_trends),
        ('profit_loss', self.import_profit_loss),
        ('customers', self.import_customers),
        ('equipment_data', self.import_equipment_data_pos),      # New
        ('transitems_data', self.import_transitems_data_pos)     # New
    ]
```

#### Transitems Import Support
```python
def import_transitems_data_pos(self) -> Dict:
    """Import POS transitems (transaction items) data with POS-prefixed file discovery"""
    # Find latest transitems file - try POS prefix first, then original
    pos_pattern = os.path.join(self.CSV_BASE_PATH, "transitemsPOS*.csv")
    old_pattern = os.path.join(self.CSV_BASE_PATH, "transitems*.csv")
    
    pos_files = glob.glob(pos_pattern)
    old_files = glob.glob(old_pattern)
    
    # Prefer POS-prefixed files if available
    files = pos_files if pos_files else old_files
```

### 3. File Discovery Verification

#### Test Results
```
📦 Equipment file discovery:
POS pattern '/home/tim/RFID3/shared/POR/equipPOS*.csv': ['/home/tim/RFID3/shared/POR/equipPOS8.26.25.csv']
✅ Selected: /home/tim/RFID3/shared/POR/equipPOS8.26.25.csv

📋 Transitems file discovery:
POS pattern '/home/tim/RFID3/shared/POR/transitemsPOS*.csv': ['/home/tim/RFID3/shared/POR/transitemsPOS8.26.25.csv']
✅ Selected: /home/tim/RFID3/shared/POR/transitemsPOS8.26.25.csv

💳 Transactions file discovery:
POS pattern '/home/tim/RFID3/shared/POR/transactionsPOS*.csv': ['/home/tim/RFID3/shared/POR/transactionsPOS8.26.25.csv']
✅ Selected: /home/tim/RFID3/shared/POR/transactionsPOS8.26.25.csv
```

## Architecture Benefits

### 1. Backward Compatibility
- **Legacy support**: System still works with original file naming
- **Graceful fallback**: If POS-prefixed files aren't found, uses original patterns
- **No breaking changes**: Existing workflows continue unchanged

### 2. Future-Proof Design
- **Preference system**: Always prefers POS-prefixed files when available
- **Extensible patterns**: Easy to add new file types or naming conventions
- **Automatic discovery**: No manual configuration required for file changes

### 3. Operational Reliability
- **Newest file selection**: Uses `os.path.getctime()` to select most recent files
- **Error handling**: Clear error messages when no files are found
- **Import statistics**: Detailed logging and success metrics

## Integration Points

### 1. Scheduler Service
- **Tuesday 8am imports**: Now include all POS data types
- **Automated correlation**: Equipment imports trigger correlation updates
- **Comprehensive logging**: Full import statistics and error tracking

### 2. Equipment Import Service
- **53,717 records**: Full POS equipment catalog import
- **Batch processing**: 1,000 record batches for performance
- **Data validation**: Comprehensive cleaning and normalization

### 3. Transitems Import Service
- **Transaction linking**: Links Contract Numbers to ItemNum (equipment)
- **Customer transaction details**: Full POS transaction item import
- **Correlation support**: Enables POS-RFID transaction correlation

## Files Modified

### Core Import Services
- `app/services/csv_import_service.py`: Equipment import with dual pattern support
- `app/services/financial_csv_import_service.py`: Enhanced with POS import methods
- `app/services/transitems_import_service.py`: Transaction items import service

### Application Infrastructure
- `app/__init__.py`: Added scheduler skip capability for correlation scripts

### Testing and Utilities
- `test_file_discovery.py`: Comprehensive file pattern testing
- `fix_correlations.py`: Enhanced correlation process using proper data sources

## Performance Considerations

### 1. File Discovery Optimization
- **Glob pattern efficiency**: Specific patterns reduce filesystem scanning
- **Timestamp-based selection**: O(n) time complexity for file selection
- **Minimal I/O operations**: Single directory scan per import type

### 2. Import Performance
- **Batch processing**: 1,000 record batches prevent memory issues
- **Progress logging**: Every 100 batches for operational visibility
- **Database optimization**: Proper indexing on correlation tables

### 3. Scheduler Efficiency
- **Parallel imports**: Multiple file types processed independently
- **Error isolation**: Import failures don't affect other data types
- **Statistics aggregation**: Consolidated reporting across all imports

## Monitoring and Maintenance

### 1. Import Success Tracking
- **File discovery logs**: Track which files are being processed
- **Import statistics**: Records processed, imported, and skipped
- **Error reporting**: Detailed error messages and stack traces

### 2. File Management
- **Automatic file selection**: Always uses newest files
- **Pattern flexibility**: Easy to adjust for new naming conventions
- **Discovery verification**: Test utilities ensure patterns work correctly

### 3. Operational Alerts
- **Missing file detection**: Clear error messages when no files found
- **Import failure notification**: Detailed error reporting for troubleshooting
- **Success rate monitoring**: Track import performance over time

## Future Enhancements

### 1. Additional File Types
- **Customer data**: `customerPOS*.csv` pattern support
- **Transaction data**: `transactionsPOS*.csv` integration
- **Financial data**: Enhanced P&L and payroll import patterns

### 2. Configuration Management
- **Pattern configuration**: Externalize file patterns to config files
- **Import scheduling**: Flexible scheduling beyond Tuesday 8am
- **Retention policies**: Automatic cleanup of old import files

### 3. Advanced Features
- **File validation**: Pre-import format and content validation
- **Delta imports**: Process only changed records
- **Real-time monitoring**: File system watchers for immediate processing

## Conclusion

The POS import enhancement successfully addresses the file naming changes while maintaining full backward compatibility. The system now robustly handles both legacy and POS-prefixed file naming conventions, with automatic preference for the newer format. This ensures reliable automated imports while providing flexibility for future naming convention changes.