# RFID3 Scripts Directory

This directory contains organized utility and analysis scripts for the RFID3 inventory management system.

## Directory Structure

### `/correlation_analysis/`
Scripts for expanding and analyzing correlations between POS and RFID systems:
- `expand_correlations.py` - Main correlation expansion with type conversion and quantity analysis
- `fix_name_mismatches.py` - Name normalization to fix punctuation differences  
- `fix_correlations.py` - Legacy correlation fixing script

### `/debug_tools/`
Development and debugging utilities:
- `debug_correlation_data.py` - Data inspection for correlation debugging
- `test_type_conversion.py` - Test type conversion between POS decimals and RFID strings

### `/analysis/`
Data analysis and reporting scripts:
- `analyze_*.py` - Various data analysis scripts for different aspects of the system
- `final_report.py` - System analysis reporting

### `/import_tools/`
Data import and transformation utilities:
- `import_*.py` - Various CSV import scripts for different data sources
- `create_*.py` - Database table creation scripts
- `transform_*.py` - Data transformation utilities

### `/verification/`
System verification and validation scripts:
- `verify_*.py` - Various verification scripts for data integrity
- `check_*.py` - System health check utilities

### `/roadmap/`
Implementation roadmap and migration scripts:
- `roadmap_*.py` - Implementation plan execution scripts

## Usage

All scripts should be run from the RFID3 project root directory:

```bash
cd /home/tim/RFID3
python3 scripts/correlation_analysis/expand_correlations.py
```

## Key Scripts

- **expand_correlations.py**: Primary script for expanding POS-RFID correlations (expanded system from 95 to 533 correlations)
- **fix_name_mismatches.py**: Normalize name differences to add more correlations (added 83 additional matches)

---
*Created: September 3, 2025*
*RFID3 Inventory Management System*