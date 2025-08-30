# RFID3 Inventory Management System

Internal inventory management system for RFID-tagged rental equipment across multiple store locations.

## System Architecture

### Core Components
- **Flask Web Application** (Python 3.11+)
- **MariaDB Database** (rfid_inventory schema)
- **Redis Cache** (session storage and performance optimization)
- **Gunicorn WSGI Server** (production deployment)

### Database Schema
```
Primary Tables:
- id_item_master (65,942 records) - Core inventory items with RFID tags
- id_transactions (26,554 records) - Scan transaction history  
- user_rental_class_mappings (909 records) - Item categorization
- executive_payroll_trends (328 records) - Financial analytics data

Supporting Tables:
- inventory_health_alerts - System alerts and monitoring
- pos_* tables - POS system integration (staging)
```

### API Endpoints

**Inventory Analytics** (`/api/inventory/`)
- `dashboard_summary` - Overview metrics (utilization, alerts, activity)
- `business_intelligence` - Category performance analysis
- `stale_items` - Items without recent activity
- `usage_patterns` - Transaction pattern analysis

**Executive Dashboard** (`/bi/`)
- `dashboard` - Executive KPI visualization
- `api/inventory-kpis` - Real-time business metrics
- `api/store-performance` - Multi-store comparison data

## Installation

### Database Setup
```sql
CREATE DATABASE rfid_inventory CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'rfid_user'@'localhost' IDENTIFIED BY 'rfid_user_password';
GRANT ALL PRIVILEGES ON rfid_inventory.* TO 'rfid_user'@'localhost';
```

### Application Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
export DB_HOST=localhost
export DB_USER=rfid_user
export DB_PASSWORD=rfid_user_password
export DB_DATABASE=rfid_inventory

# Run application
gunicorn -b 0.0.0.0:6800 -w 4 app:create_app()
```

## Configuration

### Database Configuration (`config.py`)
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'rfid_user', 
    'password': 'rfid_user_password',
    'database': 'rfid_inventory'
}
```

### API Integration
- **POS API**: `https://login.cloud.ptshome.com/api/v1/`
- **Credentials**: Hardcoded for internal use (api/Broadway8101)

## Analytics Calculations

### Utilization Rate
```python
utilization_rate = (items_on_rent / total_items) * 100
# Where items_on_rent includes statuses: "On Rent", "Delivered", "Out to Customer"
```

### Revenue Growth  
```python
revenue_growth = ((current_period - previous_period) / previous_period) * 100
# Data source: executive_payroll_trends table
```

### ROI Calculation
```python
roi_percentage = (turnover_ytd / sell_price) * 100
# Based on ItemMaster.turnover_ytd and sell_price fields
```

## Database Relationships

### Item Classification
```
id_item_master.rental_class_num → user_rental_class_mappings.rental_class_id
│
├── category (e.g., "Linens", "Tables", "Equipment")  
├── subcategory (e.g., "General Linens", "Round Tables")
└── short_common_name (display name)
```

### Transaction Tracking
```
id_transactions.tag_id → id_item_master.tag_id
│
├── scan_date (timestamp)
├── scan_type (e.g., "Delivery", "Return", "Touch Scan")
└── location data (longitude, latitude)
```

## Known Issues

### Database Integrity
- **210 orphaned items** have rental_class_num values without corresponding mappings
- **Missing foreign key constraints** due to existing data integrity issues
- **Empty POS transactions** table (pos_transactions: 0 records)

### Performance Optimizations Applied
- Indexed critical query paths (status, store, scan_date)
- Connection pooling (pool_size: 10, max_overflow: 20)
- Redis caching for frequently accessed data

## Monitoring

### Health Check
```bash
curl http://localhost:6800/health
# Returns: {"database": "healthy", "redis": "healthy", "api": "healthy", "overall": "healthy"}
```

### Performance Metrics
- **Response Times**: 0.8ms - 141ms (target: <2s)
- **Database Size**: ~65MB (indexed)
- **Active Alerts**: ~500 inventory health alerts
- **Utilization**: 0.66% (436/65,942 items)

## Development

### Testing
```bash
# Run test suite (if available)
python -m pytest tests/ -v

# Check database connectivity
python -c "from app import create_app, db; app = create_app(); print('DB OK')"
```

### Debugging
- **Application logs**: `/home/tim/RFID3/logs/`
- **Database queries**: Enable SQLAlchemy echo mode
- **API responses**: Use curl or browser dev tools for endpoint testing

## File Structure
```
/home/tim/RFID3/
├── app/
│   ├── routes/           # API endpoints
│   ├── models/           # Database models  
│   ├── services/         # Business logic
│   └── templates/        # HTML templates
├── config.py            # Database and API configuration
├── requirements.txt     # Python dependencies
└── run.py              # Application entry point
```

This is an internal system - security considerations are minimal due to controlled network access.