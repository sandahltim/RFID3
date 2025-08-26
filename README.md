# RFID Dashboard Application

**Last Updated:** August 26, 2025  
**Current Version:** Phase 2 Complete - Advanced Inventory Analytics with Configuration Management

This Flask-based RFID dashboard application manages inventory, tracks contracts, and provides comprehensive analytics for Broadway Tent and Event. It integrates with an external API for data synchronization and uses MariaDB and Redis for persistence and caching.

## 🆕 Latest Features - Phase 2 Complete

### Tab 6: Inventory & Analytics
- **Health Alerts Dashboard** - Real-time inventory health monitoring with severity-based alerting
- **Stale Items Analysis** - Category-specific thresholds for identifying items not scanned recently
- **Configuration Management** - Full UI for managing alert thresholds and business rules
- **Usage Patterns Analysis** - Utilization tracking and data discrepancy identification
- **Advanced Filtering & Pagination** - Category/subcategory filters with responsive pagination
- **Transaction Integration** - Cross-references item master with transaction history for comprehensive insights

## Project Structure

```
RFID3/
├── app/
│   ├── __init__.py
│   ├── routes/
│   │   ├── home.py
│   │   ├── common.py
│   │   ├── tabs.py
│   │   ├── tab1.py              # Rental Inventory
│   │   ├── tab2.py              # Open Contracts
│   │   ├── tab3.py              # Items in Service
│   │   ├── tab4.py              # Laundry Contracts
│   │   ├── tab5.py              # Resale/Rental Packs
│   │   ├── categories.py        # Manage Categories
│   │   ├── health.py            # System Health
│   │   └── inventory_analytics.py  # 🆕 Tab 6: Inventory Analytics
│   ├── services/
│   │   ├── api_client.py
│   │   ├── refresh.py
│   │   ├── scheduler.py
│   ├── models/
│   │   └── db_models.py         # Includes new analytics models
│   ├── templates/
│   │   ├── base.html
│   │   ├── home.html
│   │   ├── tab1.html - tab5.html
│   │   ├── categories.html
│   │   ├── inventory_analytics.html  # 🆕 Tab 6 Interface
│   │   ├── _category_rows.html
│   │   └── _hand_counted_item.html
├── static/
│   ├── css/
│   │   ├── common.css
│   │   ├── tab1.css - tab5.css
│   │   └── tab2_4.css
│   ├── js/
│   │   ├── common.js
│   │   ├── home.js
│   │   ├── tab1.js - tab5.js
│   │   └── categories.js
├── scripts/
│   ├── migrate_db.sql
│   ├── create_inventory_analytics_tables.sql  # 🆕 Analytics schema
│   ├── setup_mariadb.sh
│   ├── easy_install.sh
│   ├── update_rental_class_mappings.py
│   └── migrate_hand_counted_items.sql
├── logs/
│   ├── gunicorn_error.log
│   ├── gunicorn_access.log
│   ├── rfid_dashboard.log
│   └── app.log
├── run.py
├── config.py
├── README.md
├── INSTALL_PI.md
├── ROADMAP.md                    # 🆕 Phase upgrade plan
└── rfid_dash_dev.service
```

## Features

### Application Tabs
- **Tab 1:** Rental Inventory - View and manage rental inventory items
- **Tab 2:** Open Contracts - Track active rental contracts
- **Tab 3:** Items in Service - Monitor items requiring maintenance
- **Tab 4:** Laundry Contracts - Handle laundry processing with hand-counted items
- **Tab 5:** Resale/Rental Packs - Bulk manage resale and pack items
- **Tab 6:** 🆕 **Inventory & Analytics** - Advanced inventory health monitoring and analytics
- **Categories:** Manage rental class mappings and category assignments

### Tab 6: Inventory & Analytics Features
- **Health Alerts Dashboard**
  - Real-time inventory health scoring (0-100 scale)
  - Severity-based alerts (Critical, High, Medium, Low)
  - Category and alert type filtering
  - Automated alert generation from stale items
  
- **Stale Items Analysis**
  - Category-specific scan thresholds (Resale: 7 days, Pack: 14 days, Default: 30 days)
  - Transaction count integration
  - Advanced filtering by category, subcategory, and days threshold
  - Responsive pagination (10/25/50/100 items per page)

- **Configuration Management**
  - Visual threshold configuration interface
  - Real-time saving and validation
  - Reset to defaults capability
  - Business rule management

- **Usage Analysis**
  - Utilization pattern tracking
  - Data discrepancy analysis between ItemMaster and Transactions
  - Database health metrics
  - Orphaned record identification

### Core Functionality
- **Expandable Sections:** Detailed views for common names, items, and contracts
- **Hand-Counted Items:** Track manually counted items for laundry contracts
- **Bulk Operations:** CSV exports and bulk updates for resale/rental packs
- **Print Functionality:** Generate printouts for contracts, categories, and items
- **Real-Time Sync:** Scheduled full and incremental data refreshes from external API
- **Advanced Search:** Category-based filtering with subcategory drill-down
- **Responsive Design:** Mobile-friendly interface using MDB UI Kit

## Database Schema

### Core Tables
- **id_item_master** - Master inventory dataset (primary item records)
- **id_transactions** - Complete transaction history
- **id_rfidtag** - RFID tag metadata
- **seed_rental_classes** - Rental class definitions
- **user_rental_class_mappings** - User-defined category mappings

### 🆕 Analytics Tables (Phase 1-2)
- **inventory_health_alerts** - Health monitoring and alerting system
- **item_usage_history** - Comprehensive item lifecycle tracking
- **inventory_config** - Configuration management for thresholds and business rules
- **inventory_metrics_daily** - Aggregated daily metrics for performance optimization

### Table Relationships
- `id_item_master.tag_id` ↔ `id_transactions.tag_id` (one-to-many)
- `id_item_master.rental_class_num` ↔ `seed_rental_classes.rental_class_id` (many-to-one)
- `inventory_health_alerts.tag_id` ↔ `id_item_master.tag_id` (many-to-one)
- `item_usage_history.tag_id` ↔ `id_item_master.tag_id` (many-to-one)

## Prerequisites

- Raspberry Pi with Raspberry Pi OS (Bookworm) or compatible Linux system
- Python 3.11+
- MariaDB 10.5+
- Redis 6.0+
- Git
- Nginx (optional, for production)

## Quick Installation

### Using Easy Install Script
```bash
# Clone repository
git clone https://github.com/sandahltim/_rfidpi.git /home/tim/RFID3
cd /home/tim/RFID3
git checkout RFID3dev  # Use RFID3dev for latest features

# Run easy installation
chmod +x scripts/easy_install.sh
sudo scripts/easy_install.sh
```

### Manual Installation
See [INSTALL_PI.md](INSTALL_PI.md) for detailed manual installation instructions.

## Configuration

### Database
- **Host:** localhost
- **Database:** rfid_inventory  
- **User:** rfid_user
- **Password:** rfid_user_password

### API Endpoints
Configured in `config.py`:
- **Item Master:** `cs.iot.ptshome.com/api/v1/data/14223767938169344381`
- **Transactions:** `cs.iot.ptshome.com/api/v1/data/14223767938169346196`
- **Seed Data:** `cs.iot.ptshome.com/api/v1/data/14223767938169215907`

### Service Configuration
- **Application Port:** 8102 (Gunicorn)
- **Web Interface:** 8101 (Nginx proxy)
- **Service Name:** rfid_dash_dev.service
- **Auto-Restart:** Enabled via systemd

## Usage

1. **Access Application:** Navigate to `http://your-pi-ip:8101`
2. **Data Refresh:** Use "Full Refresh" button on home page for initial data sync
3. **Category Management:** Assign categories via "Manage Categories" tab
4. **Analytics:** Access comprehensive analytics via Tab 6
5. **Configuration:** Adjust alert thresholds via Tab 6 → Configuration

## Deployment

### Development (RFID3dev branch)
```bash
git add .
git commit -m "Your changes"
git push origin RFID3dev
# Changes auto-deployed via GitHub Actions
```

### Production (main branch)
```bash
git checkout main
git merge RFID3dev
git push origin main
# Production systems pull from main branch
```

## Monitoring & Logs

### Log Files
```bash
# Application logs
tail -f /home/tim/RFID3/logs/rfid_dashboard.log
tail -f /home/tim/RFID3/logs/gunicorn_error.log
tail -f /home/tim/RFID3/logs/app.log

# System status
sudo systemctl status rfid_dash_dev.service
```

### Health Monitoring
- Built-in system health dashboard accessible via main navigation
- Database connection monitoring
- API endpoint status tracking
- Automatic error recovery and logging

## Upgrade Roadmap

See [ROADMAP.md](ROADMAP.md) for detailed phase-by-phase upgrade plan including:
- **Phase 1-2:** ✅ Complete (Advanced Analytics Infrastructure)
- **Phase 3:** Resale & Pack Management + Predictive Analytics  
- **Phase 4:** Revenue Optimization + Workflow Automation
- **Phase 5:** Advanced Reporting & External Integration

## Troubleshooting

### Common Issues

**500 Errors:**
- Check `rfid_dashboard.log` and `gunicorn_error.log`
- Verify database connectivity: `mysql -u rfid_user -prfid_user_password rfid_inventory`

**Tab 6 Not Loading:**
- Ensure analytics tables created: `mysql -u rfid_user -prfid_user_password rfid_inventory < scripts/create_inventory_analytics_tables.sql`
- Check browser console for JavaScript errors
- Verify MDB UI Kit loading properly

**Data Sync Issues:**
- Verify API credentials in `config.py`
- Check network connectivity to external APIs
- Review sync logs in `logs/sync.log`

**Performance Issues:**
- Monitor database performance and connection pool
- Check Redis cache status
- Review memory usage with long-running processes

### Support

- **Issues:** Report bugs at https://github.com/sandahltim/_rfidpi/issues
- **Documentation:** See `INSTALL_PI.md` for installation details
- **Logs:** All logs stored in `/home/tim/RFID3/logs/` directory

---

**Note:** This application manages real-time inventory for Broadway Tent and Event. Not all items will have categories assigned until mapped via the "Manage Categories" interface. Hand-counted items are specific to laundry contracts and stored locally.

**Last Updated:** August 26, 2025 - Phase 2 Complete