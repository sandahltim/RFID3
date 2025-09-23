# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## CORE LESSONS TO APPLY

1. Always document and use code notes/version markers and clean them up at the same time
2. Assumptions cause havoc - The problem is not the things you don't know, it's the things you think you know, but just aren't so
3. Do not be afraid to ask questions - The only bad question is the one not asked
4. Do it well, then do it fast
5. Note sidequest tasks for later prioritization
6. Trust but verify
7. Complete current task.
8. Use your agents to help but verify their work.
9. Check for existing endpoints, url, dynamic variables, apis, kpis, docs and code files before creating new ones.
10. We do not fix symptoms, we solve the root problems.

## System Architecture

### RFID-KVC Dual-Service Architecture
This system implements a revolutionary dual-service architecture that separates manager/executive functions from real-time operations:

```
Manager/Executive App (Port 6801 → 8101)
├── Heavy analytics, financial data, dashboards
├── POS CSV imports and financial processing
└── Executive reporting and business intelligence

Operations API (Port 8444 → 8443 HTTPS)
├── Real-time RFID/QR scanning operations
├── Field operations and status updates
└── Mobile-optimized web interface
```

### Critical Architecture Decision
The system was redesigned to eliminate timing issues from standalone RFID scanners by implementing web-based real-time operations, solving fundamental data synchronization problems.

## Database Structure

### Core Tables
- **id_item_master**: 75K+ RFID items with real-time status
- **id_transactions**: RFID scan events and activity logs
- **pos_equipment**: Equipment catalog (import from equipPOS*.csv)
- **pos_customers**: Customer database (import from customer*.csv)
- **pos_transactions**: Contract transactions (import from transactions*.csv)
- **pos_transaction_items**: Contract line items (import from transitems*.csv)

### Critical Correlations (from /shared/POR/media/table info.xlsx)
- **transitems.ITEM ↔ equipment.NUM** (NOT equipment.KEY)
- **transactions.CNTR ↔ transitems.CNTR** (contract correlation)
- **transactions.CUSN ↔ customers.CNUM** (customer correlation)

### Store Mapping System
The system handles multiple store reference patterns:
- **001/1/3607/Wayzata** - Lake area events/DIY
- **002/2/6800/Brooklyn Park** - Industrial/construction
- **003/3/8101/Fridley** - Events (Broadway Tent & Event)
- **004/4/728/Elk River** - Rural/agricultural

## Development Commands

### Main Application
```bash
# Start development server
python run.py

# Start production server
gunicorn --workers 1 --threads 4 --timeout 600 --bind 0.0.0.0:6801 run:app

# Check system health
curl http://localhost:6801/health
```

### Operations API
```bash
# Start Operations API
cd rfid_operations_api
source venv/bin/activate
python run_api.py

# Check Operations API health
curl https://100.103.67.41:8443/health
```

### Database Operations
```bash
# Connect to database
mysql -u rfid_user -p'rfid_user_password' rfid_inventory

# Check table status
mysql -u rfid_user -p'rfid_user_password' rfid_inventory -e "SHOW TABLE STATUS;"

# Backup database
mysqldump -u rfid_user -p'rfid_user_password' rfid_inventory > backup.sql
```

### CSV Import System
```bash
# Manual CSV import via API
curl -X POST http://localhost:6801/api/import/trigger \
  -H "Content-Type: application/json" \
  -d '{"files":[{"filename":"equipPOS9.08.25.csv","type":"equipment"}],"limit":1000}'

# Check CSV import status
curl http://localhost:6801/api/import/status

# Manual RFIDpro sync
curl -X POST http://localhost:6801/refresh/rfidpro-manual
```

## CSV Import Architecture

### File Naming Patterns
- **equipPOS*.csv**: Equipment catalog (171 columns)
- **customer*.csv**: Customer database (108 columns)
- **transactions*.csv**: Contract transactions (119 columns)
- **transitems*.csv**: Transaction line items (45 columns)
- **scorecard*.csv**: Performance metrics (22 columns)
- **PayrollTrends*.csv**: Labor costs (17 columns)
- **PL*.csv**: Profit & Loss (42 columns)

### Import Service Architecture
The system uses a two-layer import approach:
1. **Raw Import**: Direct CSV → Raw tables (zero data loss)
2. **Transformation**: Raw data → Business objects with correlations

### Critical Import Rules
- Filter inactive equipment: `df[df['Inactive'] != True]`
- Use YOUR Excel correlation specifications in `/shared/POR/media/table info.xlsx`
- Preserve ALL CSV columns even if not immediately used
- Apply Flask app context for database operations: `with current_app.app_context():`

## Service Management

### Main Services
```bash
# Manager application
sudo systemctl status rfid_dash_dev
sudo systemctl restart rfid_dash_dev

# Operations API
sudo systemctl status rfid_operations_api
sudo systemctl restart rfid_operations_api

# Nginx proxy
sudo systemctl status nginx
sudo nginx -s reload
```

### Log Monitoring
```bash
# Application logs
tail -f /home/tim/RFID3/logs/gunicorn_error.log

# CSV import logs
tail -f /home/tim/RFID3/logs/gunicorn_access.log

# System journal
sudo journalctl -u rfid_dash_dev -f
```

## API Integration

### Manager ↔ Operations API Integration
The manager app uses `UnifiedAPIClient` to route calls between RFIDpro (legacy) and Operations API (new):
- **USE_OPERATIONS_API=false**: Routes to RFIDpro (current default)
- **USE_OPERATIONS_API=true**: Routes to Operations API

### Operations API Endpoints
```
GET/POST /api/v1/equipment - Equipment management
GET/POST /api/v1/items - RFID item operations
GET/POST /api/v1/transactions - Scan events
GET/POST /api/v1/sync - Bidirectional synchronization
```

## Configuration System

### Web-Based Configuration
Access via: `http://localhost:6801/config/`
- **8 configuration tabs** for all business settings
- **Real-time updates** applied immediately
- **Store-specific settings** supported

### Critical Configuration Files
- **config.py**: Database, API, and service configuration
- **app/config/stores.py**: Store mapping definitions
- **app/config/dashboard_config.py**: Dashboard settings

## Troubleshooting

### Common Issues
1. **502 Bad Gateway**: Check `sudo systemctl status rfid_dash_dev`
2. **Flask app context errors**: Ensure database operations use `with current_app.app_context():`
3. **CSV imports fail**: Check correlation specifications in Excel doc
4. **UnifiedAPIClient URL errors**: Verify base_url formatting in unified_api_client.py

### Data Verification
```bash
# Check equipment import success
mysql -u rfid_user -p'rfid_user_password' rfid_inventory -e "SELECT COUNT(*) FROM pos_equipment;"

# Verify correlations work
mysql -u rfid_user -p'rfid_user_password' rfid_inventory -e "
SELECT COUNT(*) FROM pos_transaction_items pti
JOIN pos_equipment pe ON pti.item_number = pe.num;"
```

## Important File Locations

### Key Documentation
- **YOUR Excel Specifications**: `/shared/POR/media/table info.xlsx` (correlation authority)
- **CSV Files**: `/shared/POR/*.csv` (import source data)
- **Architecture Summary**: `RFID_KVC_ARCHITECTURE_SUMMARY.md`

### Critical Code Files
- **Main App Factory**: `app/__init__.py`
- **CSV Import Services**: `app/services/csv_import_service.py`
- **API Integration**: `app/services/unified_api_client.py`
- **Operations API**: `rfid_operations_api/app/main.py`

### Network Configuration
- **Manager App**: http://100.103.67.41:6801 (internal) → https://100.103.67.41:8101 (external)
- **Operations API**: http://localhost:8444 (internal) → https://100.103.67.41:8443 (external)
- **Tailscale IP**: 100.103.67.41 (for remote access)

## Development Notes

### Current Status (Sept 2025)
The system is undergoing RFID-KVC architectural transformation. The manager app is stable, Operations API is deployed, but CSV imports need attention due to recent architectural changes.

### Recent Changes
- Implemented dual-service architecture
- Separated financial data from operations data
- Enhanced CSV correlation system based on Excel specifications
- Created web-based operations interface foundation

When working with this system, always verify YOUR Excel correlation specifications in `/shared/POR/media/table info.xlsx` before making database or import changes.