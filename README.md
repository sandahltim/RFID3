RFID3-README NEEDS FULL COMPREHENSIVE UPDATE 8/19/25 test
The project now uses the MDB UI Kit (Material Design for Bootstrap) via CDN for responsive layouts. Previous Bootstrap bundles have been removed.
├── app/
│   ├── __init__.py
│   ├── routes/
│   │   ├── home.py
│   │   ├── common.py
│   │   ├── tabs.py
│   │   ├── tab1.py
│   │   ├── tab2.py
│   │   ├── tab3.py
│   │   ├── tab4.py
│   │   ├── tab5.py
│   │   ├── categories.py
│   │   └── health.py
│   ├── services/
│   │   ├── api_client.py
│   │   ├── refresh.py
│   │   ├── scheduler.py
│   ├── models/
│   │   └── db_models.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── categories.html
│   │   ├── common.html
│   │   ├── home.html
│   │   ├── tab2.html
│   │   ├── tab3.html
│   │   ├── tab4.html
│   │   ├── tab5.html
│   │   ├── _category_rows.html
│   │   └── _hand_counted_item.html
├── static/
│   ├── css/
│   │   ├── tab1.css
│   │   ├── tab5.css
│   │   ├── tab2_4.css
│   │   └── common.css
│   ├── js/
│   │   ├── common.js
│   │   ├── tab.js
│   │   ├── home.js
│   │   ├── tab1.js
│   │   ├── tab2.js
│   │   ├── tab3.js
│   │   ├── tab4.js
│   │   ├── tab5.js
│   │   └── categories.js
├── scripts/
│   ├── migrate_db.sql
│   ├── update_rental_class_mappings.py
│   ├── migrate_hand_counted_items.sql
│   ├── setup_mariadb.sh
├── run.py
├── config.py
├── logs/
│   ├── gunicorn_error.log
│   ├── gunicorn_access.log
│   ├── rfid_dashboard.log
│   ├── app.log
│   ├── sync.log
├── README.md
└── rfid_dash_dev.service


## Database Migration: Create Tables and Indexes

This project now uses **MariaDB** for persistence. Initialize the database and create the required tables with:

```bash
chmod +x scripts/setup_mariadb.sh
sudo scripts/setup_mariadb.sh
mysql -u rfid_user -prfid_user_password rfid_inventory < scripts/migrate_db.sql
mysql -u rfid_user -prfid_user_password rfid_inventory < scripts/migrate_hand_counted_items.sql
python scripts/update_rental_class_mappings.py
```

The `migrate_hand_counted_items.sql` script adds the `hand_counted_catalog` table, which powers the Hand Counted toggle in the Manage Categories screen. Run this script after pulling updates to enable the new feature.


git pull origin
> /home/tim/RFID3/logs/gunicorn_error.log
> /home/tim/RFID3/logs/gunicorn_access.log
> /home/tim/RFID3/logs/app.log
> /home/tim/RFID3/logs/sync.log
sudo systemctl stop rfid_dash_dev.service
sudo systemctl start rfid_dash_dev.service
sudo systemctl status rfid_dash_dev.service
cat /home/tim/RFID3/logs/gunicorn_error.log
cat /home/tim/RFID3/logs/app.log
cat /home/tim/RFID3/logs/sync.log

source venv/bin/activate
# rfid_samba_pass  samba shared server on pi
## CODE AS OF 6/26/25
###run.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8102, debug=True)

#!/bin/bash
source /home/tim/RFID3/venv/bin/activate
exec gunicorn --workers 3 --timeout 300 --bind 127.0.0.1:8102 --chdir /home/tim/RFID3 run:app


### setupmariadb.sh
#!/bin/bash
# Setup MariaDB and Redis on Raspberry Pi with Bookworm

# Update and install MariaDB and Redis
sudo apt update
sudo apt install -y mariadb-server mariadb-client redis-server

# Start and enable services
sudo systemctl start mariadb
sudo systemctl enable mariadb
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Secure MariaDB installation
sudo mysql_secure_installation <<EOF

n
rfid_root_password
rfid_root_password
n
y
y
y
y
EOF

# Check if rfid_inventory database exists, create if not
sudo mysql -u root -prfid_root_password -e "CREATE DATABASE IF NOT EXISTS rfid_inventory;"

# Create or update user and privileges
sudo mysql -u root -prfid_root_password <<EOF
CREATE USER IF NOT EXISTS 'rfid_user'@'localhost' IDENTIFIED BY 'rfid_user_password';
GRANT ALL PRIVILEGES ON rfid_inventory.* TO 'rfid_user'@'localhost';
FLUSH PRIVILEGES;
EOF

# Set permissions for MariaDB
sudo chown -R mysql:mysql /var/lib/mysql
sudo chmod -R 750 /var/lib/mysql

# Create and set permissions for MariaDB log file
sudo mkdir -p /var/log/mysql
sudo touch /var/log/mysql/error.log
sudo chown mysql:mysql /var/log/mysql/error.log
sudo chmod 640 /var/log/mysql/error.log

# Add user tim to mysql group
sudo usermod -aG mysql tim

# Create logs directory for app
sudo mkdir -p /home/tim/RFID3/logs
sudo chown tim:tim /home/tim/RFID3/logs
sudo chmod 750 /home/tim/RFID3/logs


### migrate_db.sql
-- scripts/migrate_db.sql
-- migrate_db.sql version: 2025-06-26-v5

-- Drop existing tables if they exist
DROP TABLE IF EXISTS id_transactions;
DROP TABLE IF EXISTS id_item_master;
DROP TABLE IF EXISTS id_rfidtag;
DROP TABLE IF EXISTS seed_rental_classes;
DROP TABLE IF EXISTS refresh_state;
DROP TABLE IF EXISTS rental_class_mappings;
DROP TABLE IF EXISTS id_hand_counted_items;
DROP TABLE IF EXISTS user_rental_class_mappings;

-- Create id_transactions table
CREATE TABLE id_transactions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contract_number VARCHAR(255),
    tag_id VARCHAR(255) NOT NULL,
    scan_type VARCHAR(50) NOT NULL,
    scan_date DATETIME NOT NULL,
    client_name VARCHAR(255),
    common_name VARCHAR(255) NOT NULL,
    bin_location VARCHAR(255),
    status VARCHAR(50),
    scan_by VARCHAR(255),
    location_of_repair VARCHAR(255),
    quality VARCHAR(50),
    dirty_or_mud BOOLEAN,
    leaves BOOLEAN,
    oil BOOLEAN,
    mold BOOLEAN,
    stain BOOLEAN,
    oxidation BOOLEAN,
    other TEXT,
    rip_or_tear BOOLEAN,
    sewing_repair_needed BOOLEAN,
    grommet BOOLEAN,
    rope BOOLEAN,
    buckle BOOLEAN,
    date_created DATETIME,
    date_updated DATETIME,
    uuid_accounts_fk VARCHAR(255),
    serial_number VARCHAR(255),
    rental_class_num VARCHAR(255),
    longitude DECIMAL(9,6),
    latitude DECIMAL(9,6),
    wet BOOLEAN,
    service_required BOOLEAN,
    notes TEXT,
    INDEX idx_tag_id_scan_date (tag_id, scan_date)
);

-- Create id_item_master table
CREATE TABLE id_item_master (
    tag_id VARCHAR(255) PRIMARY KEY,
    uuid_accounts_fk VARCHAR(255),
    serial_number VARCHAR(255),
    client_name VARCHAR(255),
    rental_class_num VARCHAR(255),
    common_name VARCHAR(255),
    quality VARCHAR(50),
    bin_location VARCHAR(255),
    status VARCHAR(50),
    last_contract_num VARCHAR(255),
    last_scanned_by VARCHAR(255),
    notes TEXT,
    status_notes TEXT,
    longitude DECIMAL(9,6),
    latitude DECIMAL(9,6),
    date_last_scanned DATETIME,
    date_created DATETIME,
    date_updated DATETIME,
    INDEX idx_tag_id (tag_id),
    INDEX idx_status (status),
    INDEX idx_date_last_scanned (date_last_scanned)
);

-- Create id_rfidtag table
CREATE TABLE id_rfidtag (
    tag_id VARCHAR(255) PRIMARY KEY,
    uuid_accounts_fk VARCHAR(255),
    category VARCHAR(255),
    serial_number VARCHAR(255),
    client_name VARCHAR(255),
    rental_class_num VARCHAR(255),
    common_name VARCHAR(255),
    quality VARCHAR(50),
    bin_location VARCHAR(255),
    status VARCHAR(50),
    last_contract_num VARCHAR(255),
    last_scanned_by VARCHAR(255),
    notes TEXT,
    status_notes TEXT,
    longitude DECIMAL(9,6),
    latitude DECIMAL(9,6),
    date_last_scanned DATETIME,
    date_created DATETIME,
    date_updated DATETIME
);

-- Create seed_rental_classes table
CREATE TABLE seed_rental_classes (
    rental_class_id VARCHAR(255) PRIMARY KEY,
    common_name VARCHAR(255),
    bin_location VARCHAR(255)
);

-- Create refresh_state table
CREATE TABLE refresh_state (
    id INT PRIMARY KEY AUTO_INCREMENT,
    last_refresh DATETIME,
    state_type VARCHAR(50)
);

-- Create rental_class_mappings table
CREATE TABLE rental_class_mappings (
    rental_class_id VARCHAR(50) PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100) NOT NULL,
    short_common_name VARCHAR(50)
);

-- Create id_hand_counted_items table
CREATE TABLE id_hand_counted_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    contract_number VARCHAR(50) NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    action VARCHAR(50) NOT NULL,
    timestamp DATETIME NOT NULL,
    user VARCHAR(50) NOT NULL
);

-- Create user_rental_class_mappings table
CREATE TABLE user_rental_class_mappings (
    rental_class_id VARCHAR(50) PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100) NOT NULL,
    short_common_name VARCHAR(50),
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

### rfid_dash_dev.service
[Unit]
Description=RFID Dashboard Flask App
After=network.target mariadb.service

[Service]
User=tim
Group=www-data
WorkingDirectory=/home/tim/RFID3
Environment="PATH=/home/tim/RFID3/venv/bin:/usr/bin"
ExecStart=/home/tim/RFID3/venv/bin/gunicorn --workers 1 --threads 4 --timeout 600 --bind 0.0.0.0:8102 --error-logfile /home/tim/RFID3/logs/gunicorn_error.log --access-logfile /home/tim/RFID3/logs/gunicorn_access.log run:app
ExecStop=/bin/kill -s KILL $MAINPID
Restart=always
KillMode=mixed
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target




### config.py
# config.py version: 2025-06-26-v8
import os

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Application IP address
APP_IP = os.environ.get('APP_IP', '192.168.3.112')

# MariaDB configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'rfid_user',
    'password': 'rfid_user_password',
    'database': 'rfid_inventory',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

# Redis configuration
REDIS_URL = 'redis://localhost:6379/0'

# API configuration
API_USERNAME = os.environ.get('API_USERNAME', 'api')
API_PASSWORD = os.environ.get('API_PASSWORD', 'Broadway8101')
LOGIN_URL = 'https://login.cloud.ptshome.com/api/v1/login'
ITEM_MASTER_URL = 'https://cs.iot.ptshome.com/api/v1/data/14223767938169344381'
TRANSACTION_URL = 'https://cs.iot.ptshome.com/api/v1/data/14223767938169346196'
SEED_URL = 'https://cs.iot.ptshome.com/api/v1/data/14223767938169215907'

# Refresh intervals (seconds)
FULL_REFRESH_INTERVAL = 3600  # 1 hour
INCREMENTAL_REFRESH_INTERVAL = 60  # 60 seconds
INCREMENTAL_LOOKBACK_SECONDS = 600  # Look back 10 minutes
INCREMENTAL_FALLBACK_SECONDS = 172800  # Fall back to 2 days if API filter fails

# Bulk update configuration
BULK_UPDATE_BATCH_SIZE = 50  # Batch size for bulk updates in tab5.py

# Logging
LOG_FILE = os.path.join(BASE_DIR, 'logs', 'rfid_dashboard.log')

# SQLAlchemy configuration
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_timeout': 30,
    'pool_recycle': 1800,  # Recycle connections every 30 minutes
    'connect_args': {'charset': 'utf8mb4', 'collation': 'utf8mb4_unicode_ci'}
}

#mariadbhash   *8226E019AE8D0D41243D07D91ABCD8E2F20358BC  root password    MySecureRootPass123


### db_models.py
# app/models/db_models.py
# db_models.py version: 2025-06-20-v3
from app import db
from datetime import datetime

class ItemMaster(db.Model):
    __tablename__ = 'id_item_master'

    tag_id = db.Column(db.String(255), primary_key=True)
    uuid_accounts_fk = db.Column(db.String(255))
    serial_number = db.Column(db.String(255))
    client_name = db.Column(db.String(255))
    rental_class_num = db.Column(db.String(255))
    common_name = db.Column(db.String(255))
    quality = db.Column(db.String(50))
    bin_location = db.Column(db.String(255))
    status = db.Column(db.String(50))
    last_contract_num = db.Column(db.String(255))
    last_scanned_by = db.Column(db.String(255))
    notes = db.Column(db.Text)
    status_notes = db.Column(db.Text)
    longitude = db.Column(db.DECIMAL(9, 6))
    latitude = db.Column(db.DECIMAL(9, 6))
    date_last_scanned = db.Column(db.DateTime)
    date_created = db.Column(db.DateTime)
    date_updated = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'tag_id': self.tag_id,
            'uuid_accounts_fk': self.uuid_accounts_fk,
            'serial_number': self.serial_number,
            'client_name': self.client_name,
            'rental_class_num': self.rental_class_num,
            'common_name': self.common_name,
            'quality': self.quality,
            'bin_location': self.bin_location,
            'status': self.status,
            'last_contract_num': self.last_contract_num,
            'last_scanned_by': self.last_scanned_by,
            'notes': self.notes,
            'status_notes': self.status_notes,
            'longitude': float(self.longitude) if self.longitude else None,
            'latitude': float(self.latitude) if self.latitude else None,
            'date_last_scanned': self.date_last_scanned.isoformat() if self.date_last_scanned else None,
            'date_created': self.date_created.isoformat() if self.date_created else None,
            'date_updated': self.date_updated.isoformat() if self.date_updated else None
        }

class Transaction(db.Model):
    __tablename__ = 'id_transactions'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    contract_number = db.Column(db.String(255))
    tag_id = db.Column(db.String(255), nullable=False)
    scan_type = db.Column(db.String(50), nullable=False)
    scan_date = db.Column(db.DateTime, nullable=False)
    client_name = db.Column(db.String(255))
    common_name = db.Column(db.String(255), nullable=False)
    bin_location = db.Column(db.String(255))
    status = db.Column(db.String(50))
    scan_by = db.Column(db.String(255))
    location_of_repair = db.Column(db.String(255))
    quality = db.Column(db.String(50))
    dirty_or_mud = db.Column(db.Boolean)
    leaves = db.Column(db.Boolean)
    oil = db.Column(db.Boolean)
    mold = db.Column(db.Boolean)
    stain = db.Column(db.Boolean)
    oxidation = db.Column(db.Boolean)
    other = db.Column(db.Text)
    rip_or_tear = db.Column(db.Boolean)
    sewing_repair_needed = db.Column(db.Boolean)
    grommet = db.Column(db.Boolean)
    rope = db.Column(db.Boolean)
    buckle = db.Column(db.Boolean)
    date_created = db.Column(db.DateTime)
    date_updated = db.Column(db.DateTime)
    uuid_accounts_fk = db.Column(db.String(255))
    serial_number = db.Column(db.String(255))
    rental_class_num = db.Column(db.String(255))
    longitude = db.Column(db.DECIMAL(9, 6))
    latitude = db.Column(db.DECIMAL(9, 6))
    wet = db.Column(db.Boolean)
    service_required = db.Column(db.Boolean)
    notes = db.Column(db.Text)

class RFIDTag(db.Model):
    __tablename__ = 'id_rfidtag'

    tag_id = db.Column(db.String(255), primary_key=True)
    uuid_accounts_fk = db.Column(db.String(255))
    category = db.Column(db.String(255))
    serial_number = db.Column(db.String(255))
    client_name = db.Column(db.String(255))
    rental_class_num = db.Column(db.String(255))
    common_name = db.Column(db.String(255))
    quality = db.Column(db.String(50))
    bin_location = db.Column(db.String(255))
    status = db.Column(db.String(50))
    last_contract_num = db.Column(db.String(255))
    last_scanned_by = db.Column(db.String(255))
    notes = db.Column(db.Text)
    status_notes = db.Column(db.Text)
    longitude = db.Column(db.DECIMAL(9, 6))
    latitude = db.Column(db.DECIMAL(9, 6))
    date_last_scanned = db.Column(db.DateTime)
    date_created = db.Column(db.DateTime)
    date_updated = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'tag_id': self.tag_id,
            'uuid_accounts_fk': self.uuid_accounts_fk,
            'category': self.category,
            'serial_number': self.serial_number,
            'client_name': self.client_name,
            'rental_class_num': self.rental_class_num,
            'common_name': self.common_name,
            'quality': self.quality,
            'bin_location': self.bin_location,
            'status': self.status,
            'last_contract_num': self.last_contract_num,
            'last_scanned_by': self.last_scanned_by,
            'notes': self.notes,
            'status_notes': self.status_notes,
            'longitude': float(self.longitude) if self.longitude else None,
            'latitude': float(self.latitude) if self.latitude else None,
            'date_last_scanned': self.date_last_scanned.isoformat() if self.date_last_scanned else None,
            'date_created': self.date_created.isoformat() if self.date_created else None,
            'date_updated': self.date_updated.isoformat() if self.date_updated else None
        }

class SeedRentalClass(db.Model):
    __tablename__ = 'seed_rental_classes'

    rental_class_id = db.Column(db.String(255), primary_key=True)
    common_name = db.Column(db.String(255))
    bin_location = db.Column(db.String(255))

class RefreshState(db.Model):
    __tablename__ = 'refresh_state'

    id = db.Column(db.Integer, primary_key=True)
    last_refresh = db.Column(db.DateTime)  # Changed to DateTime
    state_type = db.Column(db.String(50))  # Added state_type

class RentalClassMapping(db.Model):
    __tablename__ = 'rental_class_mappings'

    rental_class_id = db.Column(db.String(50), primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    subcategory = db.Column(db.String(100), nullable=False)
    short_common_name = db.Column(db.String(50))

class HandCountedItems(db.Model):
    __tablename__ = 'id_hand_counted_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    contract_number = db.Column(db.String(50), nullable=False)
    item_name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    user = db.Column(db.String(50), nullable=False)

class UserRentalClassMapping(db.Model):
    __tablename__ = 'user_rental_class_mappings'

    rental_class_id = db.Column(db.String(50), primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    subcategory = db.Column(db.String(100), nullable=False)
    short_common_name = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

### __init__.py
# app/__init__.py
# Version: 2025-06-26-v4
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_redis import FlaskRedis
from config import DB_CONFIG, REDIS_URL, LOG_FILE, APP_IP
from datetime import datetime

# Initialize extensions
db = SQLAlchemy()
cache = FlaskRedis()

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder='/home/tim/RFID3/static')

    # Configure logging
    log_dir = os.path.dirname(LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    handler = RotatingFileHandler(LOG_FILE, maxBytes=1000000, backupCount=5)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logging.getLogger('').handlers = []
    app.logger.handlers = []
    logging.getLogger('').addHandler(handler)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG)
    app.logger.propagate = False
    app.logger.info("Application starting up - logging initialized")
    app.logger.debug(f"Static folder path: {app.static_folder}")

    # Database configuration
    try:
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}&collation={DB_CONFIG['collation']}"
        )
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_timeout': 30,
            'pool_recycle': 1800,
        }
        app.config['REDIS_URL'] = REDIS_URL
        app.config['APP_IP'] = APP_IP
        app.logger.info("Database and Redis configuration set successfully")
    except Exception as e:
        app.logger.error(f"Failed to set database/Redis configuration: {str(e)}", exc_info=True)
        raise

    # Initialize extensions
    try:
        db.init_app(app)
        cache.init_app(app)
        app.logger.info("Extensions initialized successfully")
    except Exception as e:
        app.logger.error(f"Failed to initialize extensions: {str(e)}", exc_info=True)
        raise

    # Add custom Jinja2 filters
    def timestamp_filter(value):
        return int(datetime.now().timestamp())
    app.jinja_env.filters['timestamp'] = timestamp_filter

    def datetimeformat(value):
        if value is None:
            return 'N/A'
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except ValueError:
                return value
        return value.strftime('%Y-%m-%d %H:%M:%S')
    app.jinja_env.filters['datetimeformat'] = datetimeformat

    # Create database tables
    try:
        with app.app_context():
            app.logger.info("Creating database tables")
            db.create_all()
            app.logger.info("Database tables created")
    except Exception as e:
        app.logger.error(f"Failed to create database tables: {str(e)}", exc_info=True)
        raise

    # Import and register blueprints
    try:
        from app.routes.home import home_bp
        from app.routes.tab1 import tab1_bp
        from app.routes.tab2 import tab2_bp
        from app.routes.tab3 import tab3_bp
        from app.routes.tab4 import tab4_bp
        from app.routes.tab5 import tab5_bp
        from app.routes.categories import categories_bp
        from app.routes.health import health_bp
        from app.routes.tabs import tabs_bp
        from app.services.refresh import refresh_bp

        app.register_blueprint(home_bp)
        app.register_blueprint(tab1_bp)
        app.register_blueprint(tab2_bp)
        app.register_blueprint(tab3_bp)
        app.register_blueprint(tab4_bp)
        app.register_blueprint(tab5_bp)
        app.register_blueprint(categories_bp)
        app.register_blueprint(health_bp)
        app.register_blueprint(tabs_bp)
        app.register_blueprint(refresh_bp)
        app.logger.info("Blueprints registered successfully")
    except Exception as e:
        app.logger.error(f"Failed to register blueprints: {str(e)}", exc_info=True)
        raise

    # Initialize scheduler
    try:
        from app.services.scheduler import init_scheduler
        init_scheduler(app)
        app.logger.info("Scheduler initialized successfully")
    except Exception as e:
        app.logger.error(f"Failed to initialize scheduler: {str(e)}", exc_info=True)
        raise

    app.logger.info("Application startup completed successfully")
    return app
    

### bulk_update_mappings.py
# scripts/bulk_update_mappings.py
# bulk_update_mappings.py version: 2025-06-20-v2
import sys
import os
import csv
from datetime import datetime

# Add the project directory to the Python path
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from app.models.db_models import UserRentalClassMapping
from config import DB_CONFIG, SQLALCHEMY_ENGINE_OPTIONS
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File handler for script-specific log
log_dir = os.path.join(project_dir, 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
file_handler = logging.FileHandler(os.path.join(log_dir, 'bulk_update_mappings.log'))
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Database connection
try:
    db_url = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}&collation={DB_CONFIG['collation']}"
    engine = create_engine(db_url, **SQLALCHEMY_ENGINE_OPTIONS)
    Session = sessionmaker(bind=engine)
    session = Session()
    logger.info("Successfully connected to the database")
except Exception as e:
    logger.error(f"Failed to connect to the database: {str(e)}")
    sys.exit(1)

# Path to the CSV file
csv_file_path = os.path.join(project_dir, 'seeddata_20250425155406.csv')

def bulk_update_mappings():
    try:
        # Verify the CSV file exists
        if not os.path.exists(csv_file_path):
            logger.error(f"CSV file not found at: {csv_file_path}")
            raise FileNotFoundError(f"CSV file not found at: {csv_file_path}")

        # Read the CSV file and deduplicate mappings
        mappings_dict = {}
        row_count = 0
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            logger.info("Starting to read CSV file")
            
            # Verify expected columns
            expected_columns = {'rental_class_id', 'Cat', 'SubCat'}
            if not expected_columns.issubset(reader.fieldnames):
                logger.error(f"CSV file missing required columns. Expected: {expected_columns}, Found: {reader.fieldnames}")
                raise ValueError(f"CSV file missing required columns: {expected_columns}")

            for row in reader:
                row_count += 1
                try:
                    rental_class_id = row.get('rental_class_id', '').strip()
                    category = row.get('Cat', '').strip()
                    subcategory = row.get('SubCat', '').strip()

                    # Skip rows with missing rental_class_id, category, or subcategory
                    if not rental_class_id or not category or not subcategory:
                        logger.debug(f"Skipping row {row_count} with missing data: rental_class_id={rental_class_id}, category={category}, subcategory={subcategory}")
                        continue

                    # Deduplicate: Keep the first occurrence of rental_class_id
                    if rental_class_id in mappings_dict:
                        logger.warning(f"Duplicate rental_class_id found at row {row_count}: {rental_class_id}. Keeping the first occurrence.")
                        continue

                    mappings_dict[rental_class_id] = {
                        'rental_class_id': rental_class_id,
                        'category': category,
                        'subcategory': subcategory
                    }
                    logger.debug(f"Processed valid row {row_count}: {mappings_dict[rental_class_id]}")
                except Exception as row_error:
                    logger.error(f"Error processing row {row_count}: {str(row_error)}", exc_info=True)
                    continue

        mappings = list(mappings_dict.values())
        logger.info(f"Processed {row_count} total rows from CSV, {len(mappings)} unique mappings found")

        # Clear existing user mappings
        deleted_count = session.query(UserRentalClassMapping).delete()
        logger.info(f"Deleted {deleted_count} existing user mappings")

        # Insert new user mappings one at a time to handle errors gracefully
        inserted_count = 0
        for mapping in mappings:
            try:
                user_mapping = UserRentalClassMapping(
                    rental_class_id=mapping['rental_class_id'],
                    category=mapping['category'],
                    subcategory=mapping['subcategory'],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(user_mapping)
                session.commit()  # Commit each insert individually
                inserted_count += 1
                logger.debug(f"Inserted mapping: {mapping}")
            except IntegrityError as integrity_error:
                logger.error(f"Integrity error for mapping {mapping}: {str(integrity_error)}")
                session.rollback()
                continue
            except Exception as insert_error:
                logger.error(f"Error inserting mapping {mapping}: {str(insert_error)}", exc_info=True)
                session.rollback()
                continue

        logger.info(f"Successfully inserted {inserted_count} mappings into user_rental_class_mappings")

    except Exception as e:
        logger.error(f"Error during bulk update: {str(e)}", exc_info=True)
        session.rollback()
        raise
    finally:
        session.close()
        logger.info("Database session closed")

if __name__ == "__main__":
    logger.info("Starting bulk update of rental class mappings")
    try:
        bulk_update_mappings()
        logger.info("Bulk update completed successfully")
    except Exception as main_error:
        logger.error(f"Script failed: {str(main_error)}", exc_info=True)
        sys.exit(1)

### migrate_db.sql
-- scripts/migrate_db.sql
-- migrate_db.sql version: 2025-06-26-v5

-- Drop existing tables if they exist
DROP TABLE IF EXISTS id_transactions;
DROP TABLE IF EXISTS id_item_master;
DROP TABLE IF EXISTS id_rfidtag;
DROP TABLE IF EXISTS seed_rental_classes;
DROP TABLE IF EXISTS refresh_state;
DROP TABLE IF EXISTS rental_class_mappings;
DROP TABLE IF EXISTS id_hand_counted_items;
DROP TABLE IF EXISTS user_rental_class_mappings;

-- Create id_transactions table
CREATE TABLE id_transactions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    contract_number VARCHAR(255),
    tag_id VARCHAR(255) NOT NULL,
    scan_type VARCHAR(50) NOT NULL,
    scan_date DATETIME NOT NULL,
    client_name VARCHAR(255),
    common_name VARCHAR(255) NOT NULL,
    bin_location VARCHAR(255),
    status VARCHAR(50),
    scan_by VARCHAR(255),
    location_of_repair VARCHAR(255),
    quality VARCHAR(50),
    dirty_or_mud BOOLEAN,
    leaves BOOLEAN,
    oil BOOLEAN,
    mold BOOLEAN,
    stain BOOLEAN,
    oxidation BOOLEAN,
    other TEXT,
    rip_or_tear BOOLEAN,
    sewing_repair_needed BOOLEAN,
    grommet BOOLEAN,
    rope BOOLEAN,
    buckle BOOLEAN,
    date_created DATETIME,
    date_updated DATETIME,
    uuid_accounts_fk VARCHAR(255),
    serial_number VARCHAR(255),
    rental_class_num VARCHAR(255),
    longitude DECIMAL(9,6),
    latitude DECIMAL(9,6),
    wet BOOLEAN,
    service_required BOOLEAN,
    notes TEXT,
    INDEX idx_tag_id_scan_date (tag_id, scan_date)
);

-- Create id_item_master table
CREATE TABLE id_item_master (
    tag_id VARCHAR(255) PRIMARY KEY,
    uuid_accounts_fk VARCHAR(255),
    serial_number VARCHAR(255),
    client_name VARCHAR(255),
    rental_class_num VARCHAR(255),
    common_name VARCHAR(255),
    quality VARCHAR(50),
    bin_location VARCHAR(255),
    status VARCHAR(50),
    last_contract_num VARCHAR(255),
    last_scanned_by VARCHAR(255),
    notes TEXT,
    status_notes TEXT,
    longitude DECIMAL(9,6),
    latitude DECIMAL(9,6),
    date_last_scanned DATETIME,
    date_created DATETIME,
    date_updated DATETIME,
    INDEX idx_tag_id (tag_id),
    INDEX idx_status (status),
    INDEX idx_date_last_scanned (date_last_scanned)
);

-- Create id_rfidtag table
CREATE TABLE id_rfidtag (
    tag_id VARCHAR(255) PRIMARY KEY,
    uuid_accounts_fk VARCHAR(255),
    category VARCHAR(255),
    serial_number VARCHAR(255),
    client_name VARCHAR(255),
    rental_class_num VARCHAR(255),
    common_name VARCHAR(255),
    quality VARCHAR(50),
    bin_location VARCHAR(255),
    status VARCHAR(50),
    last_contract_num VARCHAR(255),
    last_scanned_by VARCHAR(255),
    notes TEXT,
    status_notes TEXT,
    longitude DECIMAL(9,6),
    latitude DECIMAL(9,6),
    date_last_scanned DATETIME,
    date_created DATETIME,
    date_updated DATETIME
);

-- Create seed_rental_classes table
CREATE TABLE seed_rental_classes (
    rental_class_id VARCHAR(255) PRIMARY KEY,
    common_name VARCHAR(255),
    bin_location VARCHAR(255)
);

-- Create refresh_state table
CREATE TABLE refresh_state (
    id INT PRIMARY KEY AUTO_INCREMENT,
    last_refresh DATETIME,
    state_type VARCHAR(50)
);

-- Create rental_class_mappings table
CREATE TABLE rental_class_mappings (
    rental_class_id VARCHAR(50) PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100) NOT NULL,
    short_common_name VARCHAR(50)
);

-- Create id_hand_counted_items table
CREATE TABLE id_hand_counted_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    contract_number VARCHAR(50) NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    action VARCHAR(50) NOT NULL,
    timestamp DATETIME NOT NULL,
    user VARCHAR(50) NOT NULL
);

-- Create user_rental_class_mappings table
CREATE TABLE user_rental_class_mappings (
    rental_class_id VARCHAR(50) PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100) NOT NULL,
    short_common_name VARCHAR(50),
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

### migrate_hand_counted_items.sql



### migrate_short_common_name.sql
-- migrate_short_common_name.sql version: 2025-06-19-v1
-- Add short_common_name column to rental_class_mappings table
ALTER TABLE rental_class_mappings
ADD COLUMN short_common_name VARCHAR(50);

-- Add short_common_name column to user_rental_class_mappings table
ALTER TABLE user_rental_class_mappings
ADD COLUMN short_common_name VARCHAR(50);

-- Populate short_common_name in rental_class_mappings by truncating common_name to 20 characters
UPDATE rental_class_mappings rcm
JOIN seed_rental_classes src ON rcm.rental_class_id = src.rental_class_id
SET rcm.short_common_name = LEFT(src.common_name, 20);

-- Populate short_common_name in user_rental_class_mappings by truncating common_name to 20 characters
UPDATE user_rental_class_mappings urcm
JOIN seed_rental_classes src ON urcm.rental_class_id = src.rental_class_id
SET urcm.short_common_name = LEFT(src.common_name, 20);

### migrate_user_mappings.sql
-- Migration script to add the user_rental_class_mappings table
-- Added on 2025-04-23 to store user-defined mappings separately

CREATE TABLE IF NOT EXISTS user_rental_class_mappings (
    rental_class_id VARCHAR(50) PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Add indexes for faster lookups
CREATE INDEX idx_user_rental_class_mappings_rental_class_id ON user_rental_class_mappings (rental_class_id);

### migrate_user_rental_class_mappings.sql
-- migrate_user_rental_class_mappings.sql version: 2025-06-19-v1
-- Migration script to add the user_rental_class_mappings table
-- Added on 2025-04-23 to store user-defined mappings separately

CREATE TABLE IF NOT EXISTS user_rental_class_mappings (
    rental_class_id VARCHAR(50) PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Add indexes for faster lookups
CREATE INDEX idx_user_rental_class_mappings_rental_class_id ON user_rental_class_mappings (rental_class_id);


### setup_samba.sh
#!/bin/bash
# setup_samba.sh
# Configures Samba server for RFIDShare on Raspberry Pi and ensures shared directory exists
# Created: 2025-05-20
# Updated: 2025-05-20
# Usage: Run as root or with sudo
# chmod +x setup_samba.sh && sudo ./setup_samba.sh

# Exit on error
set -e

# Log file
LOG_FILE="/home/tim/RFID3/logs/samba_setup.log"
mkdir -p /home/tim/RFID3/logs
touch $LOG_FILE
chown tim:tim $LOG_FILE
chmod 640 $LOG_FILE
exec 1>>$LOG_FILE 2>&1
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting Samba setup"

# Ensure Samba is installed
if ! command -v smbd >/dev/null; then
    echo "Installing Samba..."
    apt update
    apt install -y samba samba-common-bin
else
    echo "Samba already installed"
fi

# Create shared directory
SHARED_DIR="/home/tim/RFID3/shared"
echo "Creating shared directory: $SHARED_DIR"
mkdir -p $SHARED_DIR
chown tim:tim $SHARED_DIR
chmod 770 $SHARED_DIR

# Verify Samba configuration includes RFIDShare
if ! grep -q "\[RFIDShare\]" /etc/samba/smb.conf; then
    echo "Adding RFIDShare configuration to smb.conf"
    # Backup existing Samba configuration
    if [ -f /etc/samba/smb.conf ]; then
        echo "Backing up existing smb.conf"
        cp /etc/samba/smb.conf /etc/samba/smb.conf.bak
    fi
    # Append RFIDShare configuration
    cat << EOF >> /etc/samba/smb.conf
[RFIDShare]
path = /home/tim/RFID3/shared
writable = yes
browsable = yes
guest ok = no
valid users = tim
create mask = 0660
directory mask = 0770
EOF
else
    echo "RFIDShare configuration already exists in smb.conf"
fi

# Ensure Samba user 'tim' exists
if ! pdbedit -L | grep -q "^tim:"; then
    echo "Setting up Samba user 'tim'"
    (echo "rfid_samba_pass"; echo "rfid_samba_pass") | smbpasswd -a tim
else
    echo "Samba user 'tim' already exists"
fi

# Enable and restart Samba services
echo "Restarting Samba services"
systemctl enable smbd
systemctl enable nmbd
systemctl restart smbd
systemctl restart nmbd

# Open firewall ports for Samba (if ufw is enabled)
if command -v ufw >/dev/null; then
    echo "Configuring firewall for Samba"
    ufw allow Samba
fi

# Test Samba configuration
echo "Testing Samba configuration"
testparm -s

# Set ownership and permissions for log directory
echo "Setting log directory permissions"
chown -R tim:tim /home/tim/RFID3/logs
chmod -R 750 /home/tim/RFID3/logs

echo "$(date '+%Y-%m-%d %H:%M:%S') - Samba setup completed successfully"

### update_rental_class_mappings.py
# update_rental_class_mappings.py version: 2025-06-19-v1
import sys
import os

# Add the project directory to the Python path
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_dir)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.db_models import RentalClassMapping
from config import DB_CONFIG
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection
try:
    db_url = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}"
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
except Exception as e:
    logger.error(f"Failed to connect to the database: {str(e)}")
    sys.exit(1)

# Data to upsert (using rental_class_id values from seed data)
data = [
    {"rental_class_id": "61885", "category": "Round Linen", "subcategory": "108 in"},
    {"rental_class_id": "61914", "category": "Round Linen", "subcategory": "108 in"},
    {"rental_class_id": "61890", "category": "Round Linen", "subcategory": "108 in"},
    {"rental_class_id": "61886", "category": "Round Linen", "subcategory": "108 in"},
    {"rental_class_id": "61908", "category": "Round Linen", "subcategory": "108 in"},
]

try:
    for entry in data:
        rental_class_id = entry['rental_class_id']
        category = entry['category']
        subcategory = entry['subcategory']

        # Check if the record exists
        existing_mapping = session.query(RentalClassMapping).filter_by(rental_class_id=rental_class_id).first()

        if existing_mapping:
            # Update existing record
            existing_mapping.category = category
            existing_mapping.subcategory = subcategory
            logger.info(f"Updated rental_class_id {rental_class_id} with category '{category}' and subcategory '{subcategory}'")
        else:
            # Insert new record
            new_mapping = RentalClassMapping(
                rental_class_id=rental_class_id,
                category=category,
                subcategory=subcategory
            )
            session.add(new_mapping)
            logger.info(f"Inserted rental_class_id {rental_class_id} with category '{category}' and subcategory '{subcategory}'")

    # Commit the transaction
    session.commit()
    logger.info("Successfully updated rental class mappings")

except Exception as e:
    logger.error(f"Error updating rental class mappings: {str(e)}")
    session.rollback()
    raise
finally:
    session.close()
    logger.info("Database session closed")




### Not all items will have Category or Subcategory assigned until assigned by user.

### Database Schemas

#### Item Master (`id_item_master`)
- **Purpose**: Master dataset of all items, uniquely identified by `tag_id` (RFID EPC code).
- **Fields**:
  - `tag_id` (String(255), PK): RFID EPC code.
  - `uuid_accounts_fk` (String(255)): Account foreign key.
  - `serial_number` (String(255)): Serial number.
  - `client_name` (String(255)): Client name.
  - `rental_class_num` (String(255)): Rental class ID (links to `seed_rental_classes.rental_class_id`).
  - `common_name` (String(255)): Item name.
  - `quality` (String(50)): Quality.
  - `bin_location` (String(255)): Location (e.g., "resale", "sold").
  - `status` (String(50)): Status (e.g., "On Rent", "Ready to Rent").
  - `last_contract_num` (String(255)): Latest contract number.
  - `last_scanned_by` (String(255)): Who last scanned.
  - `notes` (Text): Notes.
  - `status_notes` (Text): Status notes.
  - `longitude` (Decimal(9,6)): Scan longitude.
  - `latitude` (Decimal(9,6)): Scan latitude.
  - `date_last_scanned` (DateTime): Last scan date.
  - `date_created` (DateTime): Record creation date.
  - `date_updated` (DateTime): Last update date.
- **API Endpoint**: `cs.iot.ptshome.com/api/v1/data/14223767938169344381` (GET/POST/PUT/PATCH)

#### Transactions (`id_transactions`)
- **Purpose**: Transaction history for items.
- **Fields**:
  - `id` (BigInteger, PK, Auto-increment): Unique transaction ID.
  - `contract_number` (String(255)): Contract number.
  - `tag_id` (String(255)): RFID EPC code (links to `id_item_master.tag_id`).
  - `scan_type` (String(50)): "Touch", "Rental", or "Return".
  - `scan_date` (DateTime): Transaction date.
  - `client_name` (String(255)): Client name.
  - `common_name` (String(255)): Item name.
  - `bin_location` (String(255)): Location.
  - `status` (String(50)): Status.
  - `scan_by` (String(255)): Who scanned.
  - `location_of_repair` (String(255)): Repair location.
  - `quality` (String(50)): Quality.
  - `dirty_or_mud`, `leaves`, `oil`, `mold`, `stain`, `oxidation`, `rip_or_tear`, `sewing_repair_needed`, `grommet`, `rope`, `buckle`, `wet` (Boolean): Condition flags.
  - `other` (Text): Condition notes.
  - `rental_class_num` (String(255)): Rental class ID (links to `seed_rental_classes.rental_class_id`).
  - `serial_number` (String(255)): Serial number.
  - `longitude` (Decimal(9,6)): Scan longitude.
  - `latitude` (Decimal(9,6)): Scan latitude.
  - `service_required` (Boolean): Service needed.
  - `date_created` (DateTime): Creation date.
  - `date_updated` (DateTime): Last update.
  - `uuid_accounts_fk` (String(255)): Account foreign key.
  - `notes` (Text): Notes.
- **API Endpoint**: `cs.iot.ptshome.com/api/v1/data/14223767938169346196` (GET)

#### Seed Rental Classes (`seed_rental_classes`)
- **Purpose**: Maps rental class IDs to common names and bin locations.
- **Fields**:
  - `rental_class_id` (String(255), PK): Rental class ID (links to `id_item_master.rental_class_num` and `id_transactions.rental_class_num`).
  - `common_name` (String(255)): Common name.
  - `bin_location` (String(255)): Default bin location.
- **API Endpoint**: `cs.iot.ptshome.com/api/v1/data/14223767938169215907` (GET/POST/PUT/PATCH)

#### Hand Counted Items (`id_hand_counted_items`, Local)
- **Purpose**: Tracks manually counted items for contracts.
- **Fields**:
  - `id` (Integer, PK, Auto-increment): Record ID.
  - `contract_number` (String(50)): Contract number.
  - `item_name` (String(255)): Item name.
  - `quantity` (Integer): Quantity.
  - `action` (String(50)): "Added" or "Removed".
  - `timestamp` (DateTime): Action date.
  - `user` (String(50)): Who performed the action.

#### Categories/Mappings (`rental_class_mappings` and `user_rental_class_mappings`, Local)
- **Purpose**: Maps rental class IDs to categories and subcategories.
- **Fields (both tables)**:
  - `rental_class_id` (String(50), PK): Rental class ID (links to `id_item_master.rental_class_num`, `id_transactions.rental_class_num`, and `seed_rental_classes.rental_class_id`).
  - `category` (String(100)): Category.
  - `subcategory` (String(100)): Subcategory.
- **Additional Fields (`user_rental_class_mappings`)**:
  - `created_at` (DateTime): Creation date.
  - `updated_at` (DateTime): Last update date.

### Relationships

- `id_item_master.tag_id` ↔ `id_transactions.tag_id` (one-to-many).
- `id_item_master.last_contract_num` ↔ `id_transactions.contract_number` (many-to-one).
- `id_item_master.rental_class_num` ↔ `seed_rental_classes.rental_class_id` (many-to-one).
- `id_item_master.rental_class_num` ↔ `rental_class_mappings.rental_class_id` (many-to-one).
- `id_transactions.rental_class_num` ↔ `seed_rental_classes.rental_class_id` (many-to-one).
- `id_hand_counted_items.contract_number` ↔ `id_item_master.last_contract_num` (one-to-many).

### Deployment Instructions

Clone the Repository:

git clone https://github.com/sandahltim/_rfidpi.git
cd RFID3
git checkout RFID6

Set Up Virtual Environment:

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Configure MariaDB and Redis:


Run the setup script:

chmod +x scripts/setup_mariadb.sh
./scripts/setup_mariadb.sh

Apply database migrations:

mysql -u root -prfid_root_password rfid_inventory < scripts/migrate_db.sql
mysql -u root -prfid_root_password rfid_inventory < scripts/migrate_hand_counted_items.sql

Update Rental Class Mappings:

python scripts/update_rental_class_mappings.py

Set Up Service:

Copy the service file:

sudo cp rfid_dash_dev.service /etc/systemd/system/rfid_dash_dev.service
sudo systemctl daemon-reload

Enable and start the service:

sudo systemctl enable rfid_dash_dev.service
sudo systemctl start rfid_dash_dev.service







Commit changes to Git:

git add .
git commit -m "Update files"
git push origin RFID6



Pull and restart on the Pi:

git pull origin RFID6
sudo systemctl stop rfid_dash_dev.service
sudo systemctl start rfid_dash_dev.service
sudo systemctl status rfid_dash_dev.service



Check Logs:

cat /home/tim/RFID3/logs/rfid_dashboard.log
cat /home/tim/RFID3/logs/gunicorn_error.log
cat /home/tim/RFID3/logs/gunicorn_access.log
cat /home/tim/RFID3/logs/app.log
cat /home/tim/RFID3/logs/sync.log

Configuration





Database: MariaDB (rfid_inventory database, user: rfid_user, password: rfid_user_password).



Redis: redis://localhost:6379/0.



API: Configured in config.py with endpoints for item master, transactions, and seed rental classes.



Logging: Logs are stored in /home/tim/RFID3/logs/



RFID Dashboard Application
This Flask-based RFID dashboard application manages inventory, tracks contracts, and handles resale/rental packs for Broadway Tent and Event. It integrates with an external API for data synchronization and uses MariaDB and Redis for persistence and caching.
Project Structure
RFID3/ RFID6
├── app/
│   ├── __init__.py
│   ├── routes/
│   │   ├── home.py
│   │   ├── common.py
│   │   ├── tabs.py
│   │   ├── tab1.py
│   │   ├── tab2.py
│   │   ├── tab3.py
│   │   ├── tab4.py
│   │   ├── tab5.py
│   │   ├── categories.py
│   │   └── health.py
│   ├── services/
│   │   ├── api_client.py
│   │   ├── refresh.py
│   │   ├── scheduler.py
│   ├── models/
│   │   └── db_models.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── categories.html
│   │   ├── common.html
│   │   ├── home.html
│   │   ├── tab2.html
│   │   ├── tab3.html
│   │   ├── tab4.html
│   │   ├── tab5.html
│   │   ├── _category_rows.html
│   │   └── _hand_counted_item.html
├── static/
│   ├── css/
│   │   ├── tab1.css
│   │   ├── tab5.css
│   │   ├── tab2_4.css
│   │   └── common.css
│   ├── js/
│   │   ├── common.js
│   │   ├── tab.js
│   │   ├── tab1.js
│   │   ├── tab2.js
│   │   ├── tab3.js
│   │   ├── tab4.js
│   │   ├── tab5.js
│   │   └── categories.js
├── scripts/
│   ├── migrate_db.sql
│   ├── update_rental_class_mappings.py
│   ├── migrate_hand_counted_items.sql
│   ├── setup_mariadb.sh
│   └── and others...
├── run.py
├── config.py
├── logs/
│   ├── gunicorn_error.log
│   ├── gunicorn_access.log
│   ├── rfid_dashboard.log
│   ├── app.log
│   ├── sync.log
├── README.md
└── rfid_dash_dev.service

Features

Tabs:

Tab 1: Rental Inventory
Tab 2: Open Contracts
Tab 3: Items in Service
Tab 4: Laundry Contracts
Tab 5: Resale/Rental Packs
Categories: Manage rental class mappings


Functionality:

View and manage inventory items, contracts, and service statuses.
Expandable sections for detailed views (e.g., common names, items).
Hand-counted item tracking for laundry contracts (Tab 4).
Bulk updates and CSV exports for resale/rental packs (Tab 5).
Print functionality for contracts, categories, and items.
Scheduled data refreshes (full and incremental) from an external API.



Prerequisites

Raspberry Pi with Raspberry Pi OS (Bookworm)
Python 3.11+
MariaDB
Redis
Git
Nginx (optional, for production)

Installation
Clone the Repository
git clone https://github.com/sandahltim/_rfidpi.git
cd RFID3
git checkout RFID6

Set Up Virtual Environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Configure MariaDB and Redis
Run the setup script to install and configure MariaDB and Redis:
chmod +x scripts/setup_mariadb.sh
./scripts/setup_mariadb.sh

Apply Database Migrations
Apply the database schema migrations:
mysql -u root -prfid_root_password rfid_inventory < scripts/migrate_db.sql
mysql -u root -prfid_root_password rfid_inventory < scripts/migrate_hand_counted_items.sql

Update Rental Class Mappings
Run the script to populate rental class mappings:
python scripts/update_rental_class_mappings.py

Set Up Service
Copy the service file to systemd:
sudo cp rfid_dash_dev.service /etc/systemd/system/rfid_dash_dev.service
sudo systemctl daemon-reload

Enable and start the service:
sudo systemctl enable rfid_dash_dev.service
sudo systemctl start rfid_dash_dev.service

Verify Service Status
sudo systemctl status rfid_dash_dev.service

Deployment
Commit Changes to Git
git add .
git commit -m "Update files"
git push origin RFID6

Pull and Restart on the Pi
ssh tim@192.168.3.112
cd /home/tim/RFID3
git pull origin RFID6
> /home/tim/RFID3/logs/gunicorn_error.log
> /home/tim/RFID3/logs/gunicorn_access.log
> /home/tim/RFID3/logs/app.log
> /home/tim/RFID3/logs/sync.log
> /home/tim/RFID3/logs/rfid_dashboard.log
sudo systemctl stop rfid_dash_dev.service
sudo systemctl start rfid_dash_dev.service
sudo systemctl status rfid_dash_dev.service
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl status nginx

Check Logs
cat /home/tim/RFID3/logs/rfid_dashboard.log
cat /home/tim/RFID3/logs/gunicorn_error.log
cat /home/tim/RFID3/logs/gunicorn_access.log
cat /home/tim/RFID3/logs/app.log
cat /home/tim/RFID3/logs/sync.log

Configuration

Database: MariaDB (rfid_inventory database, user: rfid_user, password: rfid_user_password).
Redis: redis://localhost:6379/0.
API: Configured in config.py with endpoints for item master, transactions, and seed rental classes.
Logging: Logs are stored in /home/tim/RFID3/logs/.

Database Schemas
Item Master (id_item_master)

Purpose: Master dataset of all items, uniquely identified by tag_id (RFID EPC code).
Fields:
tag_id (String(255), PK): RFID EPC code.
uuid_accounts_fk (String(255)): Account foreign key.
serial_number (String(255)): Serial number.
client_name (String(255)): Client name.
rental_class_num (String(255)): Rental class ID (links to seed_rental_classes.rental_class_id).
common_name (String(255)): Item name.
quality (String(50)): Quality.
bin_location (String(255)): Location (e.g., "resale", "sold").
status (String(50)): Status (e.g., "On Rent", "Ready to Rent").
last_contract_num (String(255)): Latest contract number.
last_scanned_by (String(255)): Who last scanned.
notes (Text): Notes.
status_notes (Text): Status notes.
longitude (Decimal(9,6)): Scan longitude.
latitude (Decimal(9,6)): Scan latitude.
date_last_scanned (DateTime): Last scan date.
date_created (DateTime): Record creation date.
date_updated (DateTime): Last update date.


API Endpoint: cs.iot.ptshome.com/api/v1/data/14223767938169344381 (GET/POST/PUT/PATCH)

Transactions (id_transactions)

Purpose: Transaction history for items.
Fields:
id (BigInteger, PK, Auto-increment): Unique transaction ID.
contract_number (String(255)): Contract number.
tag_id (String(255)): RFID EPC code (links to id_item_master.tag_id).
scan_type (String(50)): "Touch", "Rental", or "Return".
scan_date (DateTime): Transaction date.
client_name (String(255)): Client name.
common_name (String(255)): Item name.
bin_location (String(255)): Location.
status (String(50)): Status.
scan_by (String(255)): Who scanned.
location_of_repair (String(255)): Repair location.
quality (String(50)): Quality.
dirty_or_mud, leaves, oil, mold, stain, oxidation, rip_or_tear, sewing_repair_needed, grommet, rope, buckle, wet (Boolean): Condition flags.
other (Text): Condition notes.
rental_class_num (String(255)): Rental class ID (links to seed_rental_classes.rental_class_id).
serial_number (String(255)): Serial number.
longitude (Decimal(9,6)): Scan longitude.
latitude (Decimal(9,6)): Scan latitude.
service_required (Boolean): Service needed.
date_created (DateTime): Creation date.
date_updated (DateTime): Last update.
uuid_accounts_fk (String(255)): Account foreign key.
notes (Text): Notes.


API Endpoint: cs.iot.ptshome.com/api/v1/data/14223767938169346196 (GET)

Seed Rental Classes (seed_rental_classes)

Purpose: Maps rental class IDs to common names and bin locations.
Fields:
rental_class_id (String(255), PK): Rental class ID (links to id_item_master.rental_class_num and id_transactions.rental_class_num).
common_name (String(255)): Common name.
bin_location (String(255)): Default bin location.


API Endpoint: cs.iot.ptshome.com/api/v1/data/14223767938169215907 (GET/POST/PUT/PATCH)

Hand Counted Items (id_hand_counted_items, Local)

Purpose: Tracks manually counted items for contracts.
Fields:
id (Integer, PK, Auto-increment): Record ID.
contract_number (String(50)): Contract number.
item_name (String(255)): Item name.
quantity (Integer): Quantity.
action (String(50)): "Added" or "Removed".
timestamp (DateTime): Action date.
user (String(50)): Who performed the action.



Categories/Mappings (rental_class_mappings and user_rental_class_mappings, Local)

Purpose: Maps rental class IDs to categories and subcategories.
Fields (both tables):
rental_class_id (String(50), PK): Rental class ID (links to id_item_master.rental_class_num, id_transactions.rental_class_num, and seed_rental_classes.rental_class_id).
category (String(100)): Category.
subcategory (String(100)): Subcategory.
short_common_name (String(50)): Shortened common name for display.


Additional Fields (user_rental_class_mappings):
created_at (DateTime): Creation date.
updated_at (DateTime): Last update date.



Relationships

id_item_master.tag_id ↔ id_transactions.tag_id (one-to-many).
id_item_master.last_contract_num ↔ id_transactions.contract_number (many-to-one).
id_item_master.rental_class_num ↔ seed_rental_classes.rental_class_id (many-to-one).
id_item_master.rental_class_num ↔ rental_class_mappings.rental_class_id (many-to-one).
id_transactions.rental_class_num ↔ seed_rental_classes.rental_class_id (many-to-one).
id_hand_counted_items.contract_number ↔ id_item_master.last_contract_num (one-to-many).

Usage

Access the application at http://tim:8101/ via Nginx (proxying to Gunicorn on port 8102).
Navigate through tabs to manage inventory, contracts, and categories.
Use the "Full Refresh" and "Clear API Data and Refresh" buttons on the home page to sync data.
Logs provide detailed debugging information for troubleshooting.

Troubleshooting

500 Errors:
Check rfid_dashboard.log and gunicorn_error.log for detailed error messages.
Common issues include endpoint mismatches in templates or database integrity errors.


Database Issues:
Verify MariaDB is running: sudo systemctl status mariadb
Check database connectivity: mysql -u rfid_user -prfid_user_password -h localhost rfid_inventory -e "SELECT 1;"


API Issues:
Ensure API credentials in config.py are correct.
Test API endpoints manually using curl or a similar tool.



Notes

Not all items will have a category or subcategory assigned until mapped by the user in the "Manage Categories" section.
Hand-counted items are specific to laundry contracts (Tab 4) and are stored locally in the database.

# app/services/api_client.py
# api_client.py version: 2025-06-27-v6
import requests
import time
from datetime import datetime, timedelta
from config import API_USERNAME, API_PASSWORD, LOGIN_URL, INCREMENTAL_FALLBACK_SECONDS
import logging
from urllib.parse import quote
from .. import cache

# Configure logging
logger = logging.getLogger('api_client')
logger.setLevel(logging.INFO)
logger.handlers = []  # Clear existing handlers
file_handler = logging.FileHandler('/home/tim/RFID3/logs/rfid_dashboard.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

class APIClient:
    def __init__(self):
        self.base_url = "https://cs.iot.ptshome.com/api/v1/data/"
        self.auth_url = LOGIN_URL
        self.item_master_endpoint = "14223767938169344381"
        self.token = None
        self.token_expiry = None
        self.authenticate()

    def authenticate(self):
        payload = {"username": API_USERNAME, "password": API_PASSWORD}
        for attempt in range(5):
            try:
                logger.debug(f"Requesting token from {self.auth_url}")
                response = requests.post(self.auth_url, json=payload, timeout=20)
                data = response.json()
                logger.debug(f"Token attempt {attempt + 1}: Status {response.status_code}")
                if response.status_code == 200 and data.get('result'):
                    self.token = data.get('access_token')
                    self.token_expiry = datetime.now() + timedelta(minutes=30)
                    logger.debug(f"Access token received: expires {self.token_expiry}")
                    return
                else:
                    logger.error(f"Token attempt {attempt + 1} failed: {response.status_code}")
                    if attempt < 4:
                        time.sleep(3)
            except requests.RequestException as e:
                logger.error(f"Token attempt {attempt + 1} failed: {str(e)}")
                if attempt < 4:
                    time.sleep(3)
        logger.error("Failed to fetch access token after 5 attempts")
        raise Exception("Failed to fetch access token after 5 attempts")

    def _make_request(self, endpoint_id, params=None, method='GET', data=None, timeout=20, user_operation=False):
        if not params:
            params = {}
        if method == 'GET':
            params['offset'] = params.get('offset', 0)
            params['limit'] = params.get('limit', 200)
            params['returncount'] = params.get('returncount', True)

        if self.token_expiry and datetime.now() >= self.token_expiry:
            self.authenticate()

        headers = {"Authorization": f"Bearer {self.token}"}
        url = f"{self.base_url}{endpoint_id}"

        if method == 'GET':
            all_data = []
            while True:
                query_string = '&'.join([f"{k}={quote(str(v))}" for k, v in params.items()])
                full_url = f"{url}?{query_string}"
                logger.debug(f"Making GET request: {full_url}")
                try:
                    response = requests.get(url, headers=headers, params=params, timeout=timeout)
                    data = response.json()
                    if response.status_code == 500:
                        logger.error(f"Server error: {data}")
                        raise Exception(f"500 Internal Server Error: {data.get('result', {}).get('message', 'Unknown error')}")
                    if response.status_code != 200:
                        logger.error(f"Request failed: {response.status_code} {response.reason}")
                        raise Exception(f"{response.status_code} {response.reason}")
                    records = data.get('data', [])
                    total_count = data.get('totalcount', 0)
                    offset = params['offset']
                    logger.debug(f"Fetched {len(records)} records, Total: {total_count}, Offset: {offset}")
                    all_data.extend(records)
                    if len(records) < params['limit'] or offset + len(records) >= total_count:
                        break
                    params['offset'] += len(records)
                except requests.RequestException as e:
                    logger.error(f"Request failed: {str(e)}")
                    raise
            logger.debug(f"Total records fetched: {len(all_data)}")
            return all_data
        elif method in ['POST', 'PATCH']:
            lock_context = cache.lock("user_operation_lock", timeout=30) if user_operation else nullcontext()
            try:
                with lock_context:
                    logger.debug(f"Making {method} request to URL: {url}")
                    try:
                        if method == 'POST':
                            response = requests.post(url, headers=headers, json=data, timeout=timeout)
                        else:
                            response = requests.patch(url, headers=headers, json=data, timeout=timeout)
                        data = response.json()
                        if response.status_code == 500:
                            logger.error(f"Server error: {data}")
                            raise Exception(f"500 Internal Server Error: {data.get('result', {}).get('message', 'Unknown error')}")
                        if response.status_code not in [200, 201]:
                            logger.error(f"Request failed: {response.status_code} {response.reason}")
                            raise Exception(f"{response.status_code} {response.reason}")
                        return data
                    except requests.RequestException as e:
                        logger.error(f"Request failed: {str(e)}")
                        raise
            except redis.exceptions.LockError as e:
                logger.error(f"Redis lock error: {str(e)}", exc_info=True)
                raise
        else:
            raise ValueError(f"Unsupported method: {method}")

    def validate_date(self, date_str, field_name):
        if date_str is None or date_str == '0000-00-00 00:00:00':
            logger.debug(f"Null or invalid {field_name}: {date_str}, returning None")
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            except ValueError as e:
                logger.warning(f"Invalid {field_name}: {date_str}. Error: {str(e)}. Returning None.")
                return None

    def get_item_master(self, since_date=None, full_refresh=False):
        params = {}
        all_data = []
        if since_date and not full_refresh:
            since_date_str = since_date.strftime('%Y-%m-%d %H:%M:%S') if isinstance(since_date, datetime) else since_date
            logger.debug(f"Item master filter since_date: {since_date_str}")
            filter_str = f"date_last_scanned,gt,'{since_date_str}'"
            params['filter[gt]'] = filter_str
            try:
                data = self._make_request(self.item_master_endpoint, params, timeout=20)
                all_data = data
                logger.info(f"Fetched {len(all_data)} items with since_date filter")
                return all_data  # Return early if since_date filter is used
            except Exception as e:
                logger.warning(f"Filter failed: {str(e)}. Skipping fetch for incremental refresh.")
                return []  # Skip fetching all data for incremental refresh
        # Full refresh or no since_date
        params.pop('filter[gt]', None)
        all_data = self._make_request(self.item_master_endpoint, params, timeout=20)
        logger.info(f"Fetched {len(all_data)} items without since_date filter")
        if since_date and full_refresh:
            since_dt = self.validate_date(since_date_str, 'since_date')
            if since_dt:
                fallback_dt = datetime.utcnow() - timedelta(seconds=INCREMENTAL_FALLBACK_SECONDS)
                all_data = [
                    item for item in all_data
                    if item.get('date_last_scanned') is None or 
                    (
                        self.validate_date(item.get('date_last_scanned'), 'date_last_scanned') and
                        self.validate_date(item.get('date_last_scanned'), 'date_last_scanned') > max(since_dt, fallback_dt)
                    )
                ]
                logger.info(f"Filtered to {len(all_data)} items locally after fetching all")
        return all_data

    def get_transactions(self, since_date=None, full_refresh=False):
        params = {}
        all_data = []
        if since_date and not full_refresh:
            since_date_str = since_date.strftime('%Y-%m-%d %H:%M:%S') if isinstance(since_date, datetime) else since_date
            logger.debug(f"Transactions filter since_date: {since_date_str}")
            filter_str = f"scan_date,gt,'{since_date_str}'"
            params['filter[gt]'] = filter_str
            try:
                data = self._make_request("14223767938169346196", params, timeout=20)
                all_data = data
                logger.info(f"Fetched {len(all_data)} transactions with since_date filter")
                return all_data  # Return early if since_date filter is used
            except Exception as e:
                logger.warning(f"Filter failed: {str(e)}. Skipping fetch for incremental refresh.")
                return []  # Skip fetching all data for incremental refresh
        # Full refresh or no since_date
        params.pop('filter[gt]', None)
        all_data = self._make_request("14223767938169346196", params, timeout=20)
        logger.info(f"Fetched {len(all_data)} transactions without since_date filter")
        if since_date and full_refresh:
            since_dt = self.validate_date(since_date_str, 'since_date')
            if since_dt:
                fallback_dt = datetime.utcnow() - timedelta(seconds=INCREMENTAL_FALLBACK_SECONDS)
                all_data = [
                    item for item in all_data
                    if item.get('scan_date') is None or 
                    (
                        self.validate_date(item.get('scan_date'), 'scan_date') and
                        self.validate_date(item.get('scan_date'), 'scan_date') > max(since_dt, fallback_dt)
                    )
                ]
                logger.info(f"Filtered to {len(all_data)} transactions locally after fetching all")
        return all_data

    def get_seed_data(self, since_date=None):
        params = {}
        data = self._make_request("14223767938169215907", params, timeout=20)
        logger.info(f"Fetched {len(data)} seed rental classes")
        return data

    def update_bin_location(self, tag_id, bin_location, timeout=20):
        if not tag_id or not bin_location:
            raise ValueError("tag_id and bin_location are required")

        params = {'filter[eq]': f"tag_id,eq,'{tag_id}'"}
        items = self._make_request(self.item_master_endpoint, params, timeout=timeout)
        if not items:
            raise Exception(f"Item with tag_id {tag_id} not found in Item Master")

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        update_data = [{
            'tag_id': tag_id,
            'bin_location': bin_location,
            'date_last_scanned': current_time
        }]

        response = self._make_request(self.item_master_endpoint, params=params, method='PATCH', data=update_data, timeout=timeout, user_operation=True)
        logger.info(f"Updated bin_location for tag_id {tag_id} to {bin_location} via API")
        return response

    def update_status(self, tag_id, status, timeout=20):
        if not tag_id or not status:
            raise ValueError("tag_id and status are required")

        params = {'filter[eq]': f"tag_id,eq,'{tag_id}'"}
        items = self._make_request(self.item_master_endpoint, params, timeout=timeout)
        if not items:
            raise Exception(f"Item with tag_id {tag_id} not found in Item Master")

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        update_data = [{
            'tag_id': tag_id,
            'status': status,
            'date_last_scanned': current_time
        }]

        response = self._make_request(self.item_master_endpoint, params=params, method='PATCH', data=update_data, timeout=timeout, user_operation=True)
        logger.info(f"Updated status for tag_id {tag_id} to {status} via API")
        return response

    def update_notes(self, tag_id, notes):
        if not tag_id:
            raise ValueError("tag_id is required")

        params = {'filter[eq]': f"tag_id,eq,'{tag_id}'"}
        items = self._make_request(self.item_master_endpoint, params)
        if not items:
            raise Exception(f"Item with tag_id {tag_id} not found in Item Master")

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        update_data = [{
            'tag_id': tag_id,
            'notes': notes if notes else '',
            'date_updated': current_time
        }]

        response = self._make_request(self.item_master_endpoint, params=params, method='PATCH', data=update_data, user_operation=True)
        logger.info(f"Updated notes for tag_id {tag_id} to '{notes}' via API")
        return response

    def insert_item(self, item_data, timeout=20):
        if not item_data or 'tag_id' not in item_data:
            raise ValueError("item_data must contain a tag_id")

        response = self._make_request(self.item_master_endpoint, method='POST', data=[item_data], timeout=timeout, user_operation=True)
        logger.info(f"Inserted new item with tag_id {item_data['tag_id']} via API")
        return response
        
Last Updated: 6-6-2025
