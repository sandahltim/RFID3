# RFID Scanner Fallback Database System Guide

## Overview

The RFID Scanner application (`scanner_app.py`) now includes a robust fallback database system that automatically switches to the `rfidpro` database if the primary `rfid_inventory` database becomes unavailable.

## Database Configuration

### Primary Database: `rfid_inventory`
- **Host:** localhost
- **User:** scanner_user
- **Password:** scanner123
- **Database:** rfid_inventory
- **Purpose:** Main operational database with live data

### Fallback Database: `rfidpro`
- **Host:** localhost
- **User:** root
- **Password:** (empty)
- **Database:** rfidpro
- **Purpose:** Baseline import from RFID3 backup data as failsafe

## Implementation Details

### Database Connection Logic
The `get_db_connection()` context manager implements automatic failover:

1. **Primary Attempt:** Tries to connect to `rfid_inventory` first
2. **Fallback Attempt:** If primary fails, automatically connects to `rfidpro`
3. **Error Handling:** Logs all connection attempts and failures
4. **Transparency:** Application continues to work seamlessly regardless of which database is used

### Fallback Database Setup

The `rfidpro` database was created and populated with:

```bash
# Create database
sudo mysql -u root -e "CREATE DATABASE IF NOT EXISTS rfidpro;"

# Import latest RFID inventory backup
cd /home/tim/RFID3/backups
sudo mysql -u root rfidpro < rfid_inventory_backup_20250912_020002.sql
```

### Data Quality Verification

The `rfidpro` fallback database contains:
- **31,050 equipment items** from POS system
- **319 contract snapshots** for rental tracking
- **22 total tables** including all critical structures
- **Active contract data** from PTC, MISSISSIPPI, NORTHSIDE, DAVIS, etc.

## Monitoring Database Status

### Database Status Endpoint
Check current database status: `GET /api/db/status`

**Response Format:**
```json
{
  "status": "connected",
  "database": "rfid_inventory",
  "source": "rfid_inventory (primary)",
  "table_count": 22,
  "critical_tables_available": 2,
  "is_fallback": false,
  "timestamp": "2025-09-14T01:38:18.442467"
}
```

### Key Status Fields
- **database:** Current active database name
- **source:** Human-readable database description
- **is_fallback:** Boolean indicating if using fallback database
- **critical_tables_available:** Count of essential tables (contract_snapshots, equipment_items)

## Operational Benefits

### High Availability
- **Zero Downtime:** Automatic failover maintains service continuity
- **Transparent Operation:** Users experience no interruption during database switching
- **Data Consistency:** Fallback database contains recent baseline data

### Use Cases
1. **Primary Database Maintenance:** Continue operations during rfid_inventory updates
2. **Network Issues:** Local rfidpro database remains accessible
3. **Fresh Backup Restoration:** Fallback provides stable data while primary is restored
4. **Development/Testing:** Switch databases without code changes

## Rental Flow Compatibility

All rental flow endpoints work seamlessly with both databases:

- `/api/reservations/upcoming` - Preloaded upcoming reservations
- `/api/contracts/open` - Active contracts with status tracking
- `/api/laundry/contracts` - Laundry service management
- `/api/pos/sync` - POS data synchronization

## Maintenance

### Updating Fallback Database
To refresh the fallback database with newer data:

```bash
# Create new backup
cd /home/tim/RFID3/backups

# Import latest backup to rfidpro
sudo mysql -u root rfidpro < rfid_inventory_backup_YYYYMMDD_HHMMSS.sql
```

### Monitoring Recommendations
1. **Check Status Regularly:** Monitor `/api/db/status` endpoint
2. **Log Analysis:** Review scanner app logs for connection warnings
3. **Data Freshness:** Update fallback database periodically from backups

## Scanner App Integration

The fallback system is fully integrated with:
- ✅ Mobile scanner interface
- ✅ Rental flow management
- ✅ Equipment scanning and tracking
- ✅ Contract management
- ✅ POS data integration
- ✅ Laundry workflow management

## Conclusion

The fallback database system provides enterprise-grade reliability for the RFID scanner application, ensuring continuous operation even during primary database outages. The system transparently maintains full functionality using the baseline rfidpro dataset until primary connectivity is restored.

---
*Last Updated: 2025-09-14*
*Scanner App Version: 2025-09-13-v1*
*Database Fallback System: ACTIVE*