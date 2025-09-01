# RFID3 Installation & Setup Guide

**Version:** 3.0  
**Target Environment:** Production & Development  
**Last Updated:** September 1, 2025

---

## 📋 Prerequisites

### System Requirements
- **Operating System**: Ubuntu 22.04 LTS or CentOS 8+ (recommended)
- **Python**: 3.11+ (critical for performance optimizations)
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: 20GB+ available space
- **Network**: Stable internet connection for POS API integration

### Required Services
- **MariaDB**: 10.6+ or MySQL 8.0+
- **Redis**: 7.0+ (for caching and session management)
- **Nginx**: 1.18+ (for production reverse proxy, optional for development)
- **Git**: For repository management

---

## 🚀 Quick Installation (Development)

### Step 1: System Preparation
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python 3.11 and dependencies
sudo apt install python3.11 python3.11-dev python3.11-venv python3-pip -y

# Install database and cache services
sudo apt install mariadb-server redis-server -y

# Install development tools
sudo apt install git curl wget nginx -y
```

### Step 2: Database Setup
```bash
# Secure MariaDB installation
sudo mysql_secure_installation

# Create database and user
sudo mysql -u root -p
```

```sql
-- Execute these SQL commands
CREATE DATABASE rfid_inventory CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'rfid_user'@'localhost' IDENTIFIED BY 'secure_password_change_this';
GRANT ALL PRIVILEGES ON rfid_inventory.* TO 'rfid_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Step 3: Redis Configuration
```bash
# Start and enable Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test Redis connection
redis-cli ping
# Should return: PONG
```

### Step 4: Application Setup
```bash
# Clone repository (replace with actual repository URL)
git clone [your-repository-url] /home/tim/RFID3
cd /home/tim/RFID3

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
python -c "import flask; print(f'Flask version: {flask.__version__}')"
```

### Step 5: Environment Configuration
```bash
# Create environment configuration
cat > .env << 'ENV_EOF'
# Database Configuration
DB_HOST=localhost
DB_USER=rfid_user
DB_PASSWORD=secure_password_change_this
DB_DATABASE=rfid_inventory

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Application Configuration
FLASK_ENV=development
FLASK_DEBUG=True
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5000

# API Configuration (update with actual credentials)
API_USERNAME=api
API_PASSWORD=Broadway8101
ENV_EOF

# Load environment variables
export $(cat .env | xargs)
```

### Step 6: Database Optimization
```bash
# Apply performance optimizations
mysql -u rfid_user -p rfid_inventory < database_performance_optimization.sql

# If the file doesn't exist, create it:
cat > database_performance_optimization.sql << 'SQL_EOF'
-- Tab 2 Performance Optimization Indexes
CREATE INDEX IF NOT EXISTS ix_item_master_contract_status ON id_item_master(last_contract_num, status);
CREATE INDEX IF NOT EXISTS ix_transactions_contract_scan_type_date ON id_transactions(contract_number, scan_type, scan_date DESC);
CREATE INDEX IF NOT EXISTS ix_transactions_client_name ON id_transactions(client_name);
CREATE INDEX IF NOT EXISTS ix_item_master_common_name ON id_item_master(common_name);
CREATE INDEX IF NOT EXISTS ix_item_master_status_contract_common ON id_item_master(status, last_contract_num, common_name);

-- Store-specific Performance Indexes
CREATE INDEX IF NOT EXISTS ix_payroll_trends_store_week ON executive_payroll_trends(store_code, week_ending);
CREATE INDEX IF NOT EXISTS ix_scorecard_store_metric ON scorecard_trends(store_code, metric_name, week_ending);
CREATE INDEX IF NOT EXISTS ix_transactions_store_date ON id_transactions(store_location, scan_date);

-- Financial Analytics Indexes  
CREATE INDEX IF NOT EXISTS ix_pl_data_period_store ON pl_data(period, store_attribution);
CREATE INDEX IF NOT EXISTS ix_pl_data_account_period ON pl_data(account_name, period);
SQL_EOF

mysql -u rfid_user -p rfid_inventory < database_performance_optimization.sql
```

### Step 7: Start Application
```bash
# Activate virtual environment
source venv/bin/activate

# Start development server
python run.py
```

Your application should now be running at `http://localhost:5000`

---

## 🏭 Production Installation

### Step 1: Production System Setup
```bash
# Create dedicated user for RFID application
sudo adduser --system --group --home /opt/rfid3 rfid3

# Create application directory structure
sudo mkdir -p /opt/rfid3/{app,logs,backups,shared}
sudo chown -R rfid3:rfid3 /opt/rfid3
```

### Step 2: Application Deployment
```bash
# Switch to application user
sudo su - rfid3

# Clone application to production directory
git clone [your-repository-url] /opt/rfid3/app
cd /opt/rfid3/app

# Create production virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Production Database Configuration
```bash
# Create production database
sudo mysql -u root -p
```

```sql
CREATE DATABASE rfid_inventory_prod CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'rfid_prod'@'localhost' IDENTIFIED BY 'very_secure_production_password';
GRANT ALL PRIVILEGES ON rfid_inventory_prod.* TO 'rfid_prod'@'localhost';

-- Additional production security
GRANT SELECT, INSERT, UPDATE, DELETE ON rfid_inventory_prod.* TO 'rfid_prod'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Step 4: Production Environment Configuration
```bash
# Create production environment file
sudo -u rfid3 tee /opt/rfid3/app/.env.production << 'PROD_ENV_EOF'
# Production Database Configuration
DB_HOST=localhost
DB_USER=rfid_prod
DB_PASSWORD=very_secure_production_password
DB_DATABASE=rfid_inventory_prod

# Production Redis Configuration
REDIS_URL=redis://localhost:6379/1

# Production Application Configuration
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=generate_a_very_secure_secret_key_here

# Production API Configuration
API_USERNAME=api
API_PASSWORD=secure_production_api_password

# Performance Configuration
SQLALCHEMY_POOL_SIZE=15
SQLALCHEMY_MAX_OVERFLOW=25
SQLALCHEMY_POOL_TIMEOUT=30
SQLALCHEMY_POOL_RECYCLE=3600
PROD_ENV_EOF
```

### Step 5: Gunicorn Configuration
```bash
# Create Gunicorn configuration
sudo -u rfid3 tee /opt/rfid3/app/gunicorn.conf.py << 'GUNICORN_EOF'
# Gunicorn production configuration
import multiprocessing

# Server socket
bind = "0.0.0.0:6800"
backlog = 2048

# Worker processes
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2

# Restart workers
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Logging
accesslog = "/opt/rfid3/logs/gunicorn-access.log"
errorlog = "/opt/rfid3/logs/gunicorn-error.log"
loglevel = "info"

# Process naming
proc_name = "rfid3-inventory"

# Server mechanics
daemon = False
pidfile = "/opt/rfid3/logs/gunicorn.pid"
user = "rfid3"
group = "rfid3"
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/path/to/ssl/key.pem"
# certfile = "/path/to/ssl/cert.pem"
GUNICORN_EOF
```

### Step 6: Systemd Service Configuration
```bash
# Create systemd service file
sudo tee /etc/systemd/system/rfid3.service << 'SERVICE_EOF'
[Unit]
Description=RFID3 Inventory Management System
Requires=mysql.service redis.service
After=network.target mysql.service redis.service

[Service]
Type=notify
User=rfid3
Group=rfid3
RuntimeDirectory=rfid3
WorkingDirectory=/opt/rfid3/app
Environment=PATH=/opt/rfid3/app/venv/bin
Environment=PYTHONPATH=/opt/rfid3/app
EnvironmentFile=/opt/rfid3/app/.env.production
ExecStart=/opt/rfid3/app/venv/bin/gunicorn -c gunicorn.conf.py 'app:create_app()'
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Reload systemd and start service
sudo systemctl daemon-reload
sudo systemctl enable rfid3.service
sudo systemctl start rfid3.service
```

### Step 7: Nginx Reverse Proxy (Production)
```bash
# Create Nginx configuration
sudo tee /etc/nginx/sites-available/rfid3 << 'NGINX_EOF'
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Static files
    location /static {
        alias /opt/rfid3/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:6800;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:6800/health;
        access_log off;
    }
}
NGINX_EOF

# Enable site and restart Nginx
sudo ln -sf /etc/nginx/sites-available/rfid3 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔧 Configuration Options

### Database Performance Tuning
```sql
-- MariaDB/MySQL optimization for RFID3
-- Add to /etc/mysql/mariadb.conf.d/50-server.cnf or /etc/mysql/mysql.conf.d/mysqld.cnf

[mysqld]
# InnoDB settings for performance
innodb_buffer_pool_size = 2G                 # 70-80% of available RAM
innodb_log_file_size = 256M
innodb_log_buffer_size = 16M
innodb_flush_log_at_trx_commit = 2
innodb_thread_concurrency = 0
innodb_flush_method = O_DIRECT
innodb_file_per_table = 1

# Query cache (if available)
query_cache_type = 1
query_cache_size = 128M
query_cache_limit = 2M

# Connection settings
max_connections = 200
connect_timeout = 5
wait_timeout = 600
max_allowed_packet = 16M
thread_cache_size = 128
sort_buffer_size = 4M
bulk_insert_buffer_size = 16M
tmp_table_size = 32M
max_heap_table_size = 32M

# Restart MariaDB after configuration changes
# sudo systemctl restart mariadb
```

### Redis Performance Configuration
```bash
# Redis configuration for production
# Edit /etc/redis/redis.conf

# Memory management
maxmemory 1gb
maxmemory-policy allkeys-lru

# Persistence (adjust based on needs)
save 900 1
save 300 10
save 60 10000

# Performance
tcp-keepalive 60
timeout 0
tcp-backlog 511

# Security
bind 127.0.0.1
requirepass your_redis_password

# Restart Redis after configuration changes
# sudo systemctl restart redis-server
```

### Application Performance Configuration
```python
# Add to config.py for production optimization
PERFORMANCE_CONFIG = {
    # Database connection pool
    'SQLALCHEMY_ENGINE_OPTIONS': {
        'pool_size': 15,
        'max_overflow': 25,
        'pool_timeout': 30,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    },
    
    # Cache configuration
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'rfid3:',
    
    # Session configuration  
    'SESSION_TYPE': 'redis',
    'SESSION_PERMANENT': False,
    'SESSION_USE_SIGNER': True,
    'SESSION_REDIS': redis.StrictRedis(host='localhost', port=6379, db=2)
}
```

---

## 🧪 Testing Installation

### Step 1: Health Check
```bash
# Test application health
curl http://localhost:6800/health

# Expected response:
{
  "status": "healthy",
  "components": {
    "database": {"healthy": true, "response_time": "0.02s"},
    "redis": {"healthy": true, "response_time": "0.001s"},
    "api": {"healthy": true},
    "scheduler": {"healthy": true}
  },
  "timestamp": "2025-09-01T12:00:00Z"
}
```

### Step 2: Performance Testing
```bash
# Run Tab 2 performance test
cd /opt/rfid3/app  # or /home/tim/RFID3 for development
python tab2_performance_test.py

# Expected output should show:
# - Page load times under 2 seconds
# - Single query optimization working
# - Cache hit rates above 60%
```

### Step 3: Database Validation
```bash
# Test database connectivity and performance
python -c "
from app import create_app, db
from app.models.db_models import ItemMaster

app = create_app()
with app.app_context():
    count = db.session.query(ItemMaster).count()
    print(f'Database connection successful. Item count: {count}')
"
```

### Step 4: API Endpoint Testing
```bash
# Test key API endpoints
curl http://localhost:6800/api/inventory/dashboard_summary
curl http://localhost:6800/tab/2/performance_stats
curl http://localhost:6800/bi/dashboard
```

---

## 🔍 Monitoring Setup

### Log Monitoring
```bash
# Create log rotation configuration
sudo tee /etc/logrotate.d/rfid3 << 'LOGROTATE_EOF'
/opt/rfid3/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 0644 rfid3 rfid3
    postrotate
        systemctl reload rfid3
    endscript
}
LOGROTATE_EOF
```

### Performance Monitoring Script
```bash
# Create monitoring script
sudo -u rfid3 tee /opt/rfid3/monitor.sh << 'MONITOR_EOF'
#!/bin/bash
# RFID3 System Monitor

LOG_FILE="/opt/rfid3/logs/monitor.log"
HEALTH_URL="http://localhost:6800/health"

echo "$(date): Checking system health..." >> $LOG_FILE

# Check application health
if curl -s -f $HEALTH_URL > /dev/null; then
    echo "$(date): Application healthy" >> $LOG_FILE
else
    echo "$(date): Application health check failed" >> $LOG_FILE
    # Add alerting logic here (email, Slack, etc.)
fi

# Check database connectivity
if mysql -u rfid_prod -p'very_secure_production_password' -e "SELECT 1;" rfid_inventory_prod &>/dev/null; then
    echo "$(date): Database connectivity OK" >> $LOG_FILE
else
    echo "$(date): Database connectivity failed" >> $LOG_FILE
fi

# Check Redis connectivity
if redis-cli ping | grep -q PONG; then
    echo "$(date): Redis connectivity OK" >> $LOG_FILE
else
    echo "$(date): Redis connectivity failed" >> $LOG_FILE
fi
MONITOR_EOF

chmod +x /opt/rfid3/monitor.sh

# Add to crontab for automated monitoring
echo "*/5 * * * * /opt/rfid3/monitor.sh" | sudo -u rfid3 crontab -
```

---

## 🔄 Backup & Maintenance

### Automated Backup Script
```bash
# Create backup script
sudo -u rfid3 tee /opt/rfid3/backup.sh << 'BACKUP_EOF'
#!/bin/bash
# RFID3 Automated Backup Script

BACKUP_DIR="/opt/rfid3/backups"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="rfid_inventory_prod"
DB_USER="rfid_prod"
DB_PASS="very_secure_production_password"

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
echo "Starting database backup..."
mysqldump -u $DB_USER -p$DB_PASS $DB_NAME | gzip > "$BACKUP_DIR/rfid_db_backup_$DATE.sql.gz"

# Application backup (excluding venv)
echo "Starting application backup..."
tar -czf "$BACKUP_DIR/rfid_app_backup_$DATE.tar.gz" \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='logs/*.log' \
    /opt/rfid3/app

# CSV files backup
echo "Starting CSV files backup..."
if [ -d "/opt/rfid3/app/shared" ]; then
    tar -czf "$BACKUP_DIR/rfid_csv_backup_$DATE.tar.gz" /opt/rfid3/app/shared
fi

# Cleanup old backups (keep 30 days)
echo "Cleaning up old backups..."
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
BACKUP_EOF

chmod +x /opt/rfid3/backup.sh

# Schedule daily backups at 2 AM
echo "0 2 * * * /opt/rfid3/backup.sh" | sudo -u rfid3 crontab -
```

### Maintenance Tasks
```bash
# Create maintenance script
sudo -u rfid3 tee /opt/rfid3/maintenance.sh << 'MAINTENANCE_EOF'
#!/bin/bash
# RFID3 Weekly Maintenance Tasks

echo "$(date): Starting weekly maintenance..."

# Clear application cache
curl -s -X POST http://localhost:6800/tab/2/cache_clear

# Analyze database tables for optimization
mysql -u rfid_prod -p'very_secure_production_password' rfid_inventory_prod << 'SQL'
ANALYZE TABLE id_item_master, id_transactions, executive_payroll_trends, pl_data, scorecard_trends;
OPTIMIZE TABLE id_item_master, id_transactions, executive_payroll_trends, pl_data, scorecard_trends;
SQL

# Clean up temporary files
find /tmp -name "*rfid*" -mtime +7 -delete 2>/dev/null

# Update application statistics
python3 -c "
import sys
sys.path.append('/opt/rfid3/app')
from app.services.maintenance import update_statistics
update_statistics()
"

echo "$(date): Weekly maintenance completed"
MAINTENANCE_EOF

chmod +x /opt/rfid3/maintenance.sh

# Schedule weekly maintenance on Sundays at 3 AM
echo "0 3 * * 0 /opt/rfid3/maintenance.sh" | sudo -u rfid3 crontab -
```

---

## 🚨 Troubleshooting Common Issues

### Application Won't Start
```bash
# Check service status
sudo systemctl status rfid3

# Check logs
sudo journalctl -u rfid3 -f

# Check application logs
tail -f /opt/rfid3/logs/gunicorn-error.log

# Common fixes:
# 1. Check database connectivity
mysql -u rfid_prod -p rfid_inventory_prod

# 2. Check Redis connectivity  
redis-cli ping

# 3. Restart dependencies
sudo systemctl restart mariadb redis-server
sudo systemctl restart rfid3
```

### Performance Issues
```bash
# Check performance statistics
curl http://localhost:6800/tab/2/performance_stats

# Clear cache if needed
curl -X POST http://localhost:6800/tab/2/cache_clear

# Check database performance
mysql -u rfid_prod -p rfid_inventory_prod -e "SHOW PROCESSLIST;"
mysql -u rfid_prod -p rfid_inventory_prod -e "SHOW ENGINE INNODB STATUS\G"
```

### Database Connection Issues
```bash
# Check connection limits
mysql -u root -p -e "SHOW STATUS LIKE 'Threads_connected';"
mysql -u root -p -e "SHOW STATUS LIKE 'Max_used_connections';"

# Check for long-running queries
mysql -u root -p -e "SELECT * FROM information_schema.processlist WHERE TIME > 30;"
```

---

## 📞 Support & Resources

### Log Locations
- **Application Logs**: `/opt/rfid3/logs/` (production) or `/home/tim/RFID3/logs/` (development)
- **System Logs**: `sudo journalctl -u rfid3`
- **Database Logs**: `/var/log/mysql/error.log`
- **Nginx Logs**: `/var/log/nginx/access.log` and `/var/log/nginx/error.log`

### Configuration Files
- **Application Config**: `/opt/rfid3/app/config.py`
- **Environment**: `/opt/rfid3/app/.env.production`
- **Database Config**: `/etc/mysql/mariadb.conf.d/50-server.cnf`
- **Redis Config**: `/etc/redis/redis.conf`

### Performance Verification
```bash
# Run comprehensive system check
python3 /opt/rfid3/app/comprehensive_test_suite.py

# Check specific components
python3 /opt/rfid3/app/tab2_performance_test.py
python3 /opt/rfid3/app/test_api_endpoints.py
```

---

**Installation Guide Status**: ✅ Complete | **Tested On**: Ubuntu 22.04, CentOS 8  
**Support**: System Administration Team | **Last Updated**: September 1, 2025

This comprehensive guide provides step-by-step installation instructions for both development and production environments, with performance optimization, monitoring, and maintenance procedures included.
