# Installing RFID Dashboard on Raspberry Pi

**Last Updated:** August 26, 2025  
**Version:** Phase 2 Complete - Advanced Inventory Analytics

These installation steps set up the complete RFID Dashboard application under `/home/tim/RFID3`, including the new **Tab 6: Inventory & Analytics** features. The application runs Gunicorn on port **8102** and exposes Nginx on port **8101** for the web interface.

## Features Included in This Installation

### Core Application (Tabs 1-5)
- Rental Inventory, Open Contracts, Items in Service
- Laundry Contracts with hand-counted items
- Resale/Rental Pack management
- Category management system

### 🆕 Advanced Analytics (Tab 6)
- **Health Alerts Dashboard** - Real-time inventory health monitoring
- **Stale Items Analysis** - Category-specific scan thresholds and filtering
- **Configuration Management** - Visual interface for alert threshold management
- **Usage Pattern Analysis** - Data discrepancy identification and utilization tracking
- **Advanced Filtering & Pagination** - Responsive interface with category drill-down

## Prerequisites

- Raspberry Pi with Raspberry Pi OS (Bookworm) or compatible Linux system
- Internet connection for package installation and GitHub access
- At least 8GB SD card with 2GB+ free space
- Basic command line knowledge

## Installation Methods

### Method 1: Quick Installation (Recommended)

The easy installation script automatically handles all setup steps:

```bash
# 1. Download and run the automated installer
curl -sSL https://raw.githubusercontent.com/sandahltim/_rfidpi/RFID3dev/scripts/easy_install.sh | sudo bash

# 2. Follow the prompts and wait for completion
# The script will:
# - Install all dependencies (Python, MariaDB, Redis, Nginx)
# - Clone the repository and set up the Python environment
# - Create and configure the database with analytics tables
# - Set up systemd services for auto-start
# - Configure Nginx reverse proxy
# - Install auto-update system
```

### Method 2: Manual Installation

If you prefer manual control or the easy installer fails, follow these detailed steps:

## Step 1: Prepare the System

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y git python3 python3-venv python3-pip \
    mariadb-server mariadb-client redis-server nginx curl
```

**Note:** If package installation fails with `/boot/firmware` errors:
```bash
sudo mount /boot/firmware
sudo dpkg --configure -a
# Then retry the apt install command above
```

## Step 2: Clone Repository and Setup Environment

```bash
# Create application directory and clone repository
sudo mkdir -p /home/tim/RFID3
sudo chown tim:tim /home/tim/RFID3
cd /home/tim/RFID3

# Clone repository (use RFID3dev for latest features)
git clone https://github.com/sandahltim/_rfidpi.git .
git checkout RFID3dev

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 3: Database Setup

### Configure MariaDB
```bash
# Run MariaDB setup script
chmod +x scripts/setup_mariadb.sh
sudo scripts/setup_mariadb.sh
```

This script:
- Installs and secures MariaDB
- Creates `rfid_inventory` database
- Sets up `rfid_user` with password `rfid_user_password`
- Configures proper permissions

### Create Database Tables

**Core Tables:**
```bash
# Create main application tables
mysql -u rfid_user -prfid_user_password rfid_inventory < scripts/migrate_db.sql
mysql -u rfid_user -prfid_user_password rfid_inventory < scripts/migrate_hand_counted_items.sql
```

**🆕 Analytics Tables (Required for Tab 6):**
```bash
# Create analytics tables for inventory health monitoring
mysql -u rfid_user -prfid_user_password rfid_inventory < scripts/create_inventory_analytics_tables.sql
```

This creates the new analytics infrastructure:
- `inventory_health_alerts` - Health monitoring system
- `item_usage_history` - Comprehensive lifecycle tracking  
- `inventory_config` - Configuration management
- `inventory_metrics_daily` - Performance optimization

### Initialize Data
```bash
# Set up rental class mappings
source venv/bin/activate
python scripts/update_rental_class_mappings.py
```

## Step 4: Configure Services

### Set up Application Service
```bash
# Install systemd service
sudo cp rfid_dash_dev.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable rfid_dash_dev.service
sudo systemctl start rfid_dash_dev.service

# Verify service status
sudo systemctl status rfid_dash_dev.service
```

### Configure Nginx (Optional but Recommended)
```bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/rfid-dashboard > /dev/null << 'EOF'
server {
    listen 8101;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8102;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }
}
EOF

# Enable the site
sudo ln -sf /etc/nginx/sites-available/rfid-dashboard /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default  # Remove default site
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## Step 5: Set up Shared Directory (Optional)

For CSV file sharing between devices:

```bash
# Set up Samba share
chmod +x scripts/setup_samba.sh
sudo scripts/setup_samba.sh
```

This creates:
- `/home/tim/RFID3/shared` directory
- Samba share accessible as `\\your-pi-ip\RFIDShare`
- User: `tim`, Password: `rfid_samba_pass`

## Step 6: Configure Auto-Updates (Recommended)

```bash
# Install auto-update system for daily GitHub sync
sudo scripts/setup_auto_update.sh
```

This sets up:
- Daily automatic updates from GitHub at midnight
- Backup system with rollback capability
- Service restart after updates
- Comprehensive logging

## Step 7: Verification and Testing

### Test Database Connection
```bash
# Verify database setup
mysql -u rfid_user -prfid_user_password rfid_inventory -e "
SELECT TABLE_NAME, TABLE_COMMENT 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = 'rfid_inventory' 
ORDER BY TABLE_NAME;"
```

Expected tables should include:
- Core tables: `id_item_master`, `id_transactions`, `seed_rental_classes`
- Analytics tables: `inventory_health_alerts`, `inventory_config`, `item_usage_history`

### Test Application Access
```bash
# Check service status
sudo systemctl status rfid_dash_dev.service

# Test application response
curl -I http://localhost:8102/  # Direct application
curl -I http://localhost:8101/  # Through Nginx proxy
```

### Access Web Interface
1. Open browser and navigate to: `http://your-pi-ip:8101`
2. Verify all tabs load correctly (Tabs 1-6)
3. Test Tab 6 "Inventory & Analytics" features:
   - Health Alerts Dashboard
   - Stale Items Analysis with filtering
   - Configuration Management interface
   - Usage Analysis sections

## Configuration

### API Configuration
Update `/home/tim/RFID3/config.py` with your API credentials:
```python
API_USERNAME = 'your_api_username'
API_PASSWORD = 'your_api_password'
APP_IP = 'your_pi_ip_address'  # Update this to your Pi's IP
```

### Analytics Configuration
Access Tab 6 → Configuration to adjust:
- **Stale Item Thresholds:** Default (30 days), Resale (7 days), Pack (14 days)
- **Usage Thresholds:** High usage (0.8), Low usage (0.2)
- **Quality Decline Threshold:** Grade drops (2 levels)

## Initial Data Setup

1. **Full Data Refresh:** Click "Full Refresh" on the home page
2. **Category Assignment:** Use "Manage Categories" to assign items to categories
3. **Generate Analytics:** Use Tab 6 → "Generate Alerts" to populate health alerts
4. **Configure Thresholds:** Adjust alert thresholds via Tab 6 → Configuration

## Monitoring and Maintenance

### Log Files
```bash
# Application logs
tail -f /home/tim/RFID3/logs/rfid_dashboard.log
tail -f /home/tim/RFID3/logs/gunicorn_error.log
tail -f /home/tim/RFID3/logs/app.log

# System logs
sudo journalctl -u rfid_dash_dev.service -f
```

### Service Management
```bash
# Restart application
sudo systemctl restart rfid_dash_dev.service

# Check status
sudo systemctl status rfid_dash_dev.service

# View recent logs
sudo journalctl -u rfid_dash_dev.service --since "10 minutes ago"
```

### Database Maintenance
```bash
# Check database size and health
mysql -u rfid_user -prfid_user_password rfid_inventory -e "
SELECT 
    table_name,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'DB Size in MB'
FROM information_schema.tables
WHERE table_schema='rfid_inventory'
ORDER BY (data_length + index_length) DESC;"
```

## Troubleshooting

### Common Issues

**Service Won't Start:**
```bash
# Check detailed logs
sudo journalctl -u rfid_dash_dev.service --lines=50
# Often caused by missing Python dependencies or database connection issues
```

**Database Connection Errors:**
```bash
# Verify MariaDB is running
sudo systemctl status mariadb

# Test connection manually
mysql -u rfid_user -prfid_user_password -h localhost rfid_inventory
```

**Tab 6 Analytics Not Loading:**
```bash
# Ensure analytics tables exist
mysql -u rfid_user -prfid_user_password rfid_inventory -e "SHOW TABLES LIKE '%inventory_%';"

# Re-create analytics tables if missing
mysql -u rfid_user -prfid_user_password rfid_inventory < scripts/create_inventory_analytics_tables.sql
```

**Performance Issues:**
- Check available disk space: `df -h`
- Monitor memory usage: `free -h`
- Review MariaDB performance: Check `/var/log/mysql/error.log`

**Network Access Issues:**
```bash
# Check if ports are open
sudo netstat -tlnp | grep -E ':(8101|8102)'

# Test firewall (if enabled)
sudo ufw status
```

### Getting Help

1. **Check Logs First:** Most issues are logged in detail
2. **Review Documentation:** See [README.md](README.md) for feature documentation
3. **GitHub Issues:** Report bugs at https://github.com/sandahltim/_rfidpi/issues
4. **Service Status:** Always check `systemctl status` for service-related issues

## Upgrade Instructions

### From Previous Versions
If upgrading from a version without Tab 6 analytics:

```bash
# 1. Backup your data
mysqldump -u rfid_user -prfid_user_password rfid_inventory > backup_$(date +%Y%m%d).sql

# 2. Pull latest code
cd /home/tim/RFID3
git pull origin RFID3dev

# 3. Update Python dependencies
source venv/bin/activate
pip install -r requirements.txt

# 4. Create new analytics tables
mysql -u rfid_user -prfid_user_password rfid_inventory < scripts/create_inventory_analytics_tables.sql

# 5. Restart service
sudo systemctl restart rfid_dash_dev.service
```

### Development Updates
The system can automatically update from GitHub:
```bash
# Manual update
cd /home/tim/RFID3
git pull origin RFID3dev
sudo systemctl restart rfid_dash_dev.service

# Auto-updates run daily if configured during installation
```

---

**Installation Complete!** 

Your RFID Dashboard with advanced analytics is now ready. Access the web interface at `http://your-pi-ip:8101` and explore the new Tab 6: Inventory & Analytics features.

**Next Steps:**
1. Configure API credentials in `config.py`
2. Run initial data refresh from the home page  
3. Assign categories via "Manage Categories"
4. Explore analytics features in Tab 6
5. Set up alert thresholds via Tab 6 → Configuration

**Last Updated:** August 26, 2025