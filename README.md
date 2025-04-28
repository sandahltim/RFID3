test_rfidpi/ RFID2restore
├── app/
│   ├── __init__.py
│   ├── routes/
│   │   ├── home.py
│   │   ├── tabs.py
│   │   ├── tab1.py
│   │   ├── tab2.py
│   │   ├── tab4.py
│   │   ├── tab4.py
│   │   ├── tab5.py
│   │   ├── categories.py
│   │   └── health.py
│   ├── services/
│   │   ├── api_client.py
│   │   ├── refresh.py
│   │   └── scheduler.py
│   ├── models/
│   │   └── db_models.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── categories.html
│   │   ├── _category_rows.html
│   │   ├── home.html
│   │   ├── tab1.html
│   │   ├── tab2.html
│   │   ├── tab3.html
│   │   ├── tab4.html
│   │   ├── tab5.html
│   │   ├── _hand_counted_item.html.html
│   │   └── tab.html
├── static/
│   └── css/
│   │   ├── tab1_5.css
│   │   └── style.css
│   └── js/
│   │   ├── tab.js
│   │   ├── tab1_5.js
│   │   ├── common.js
│   │   └── expand.js
│   └── lib/
│        ├── htmx/
│        │   └── htmx.min.js
│        └── bootstrap/
│            ├── bootstrap.min.css
│            └── bootstrap.bundle.min.js
├── scripts/
│   ├── migrate_db.sql
│   ├── update_rental_class_mappings.py
│   ├── migrate_hand_counted_items.sql
│   └── setup_mariadb.sh
├── run.py
├── config.py
└── logs/


git pull origin RFID2restore
> /home/tim/test_rfidpi/logs/gunicorn_error.log
> /home/tim/test_rfidpi/logs/gunicorn_access.log
> /home/tim/test_rfidpi/logs/app.log
> /home/tim/test_rfidpi/logs/sync.log
sudo systemctl stop rfid_dash_dev.service
sudo systemctl start rfid_dash_dev.service
sudo systemctl status rfid_dash_dev.service
cat /home/tim/test_rfidpi/logs/gunicorn_error.log
cat /home/tim/test_rfidpi/logs/app.log
cat /home/tim/test_rfidpi/logs/sync.log

source venv/bin/activate

## CODE AS OF4/26/25
###run.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3607, debug=True)

###start.sh
#!/bin/bash
source /home/tim/test_rfidpi/venv/bin/activate
exec gunicorn --workers 1 --bind 0.0.0.0:3607 --chdir /home/tim/test_rfidpi run:app


rfid_dash_dev.service
[Unit]
Description=RFID Dashboard Flask App
After=network.target

[Service]
User=tim
Group=www-data
WorkingDirectory=/home/tim/test_rfidpi
Environment="PATH=/home/tim/test_rfidpi/venv/bin"
ExecStart=/home/tim/test_rfidpi/venv/bin/gunicorn --workers 1 --bind 0.0.0.0:8000 --error-logfile /home/tim/test_rfidpi/logs/gunicorn_error.log --access-logfile /home/tim/test_rfidpi/logs/gunicorn_access.log run:app
ExecStop=/bin/kill -s KILL $MAINPID
Restart=always
KillMode=mixed
TimeoutStopSec=20

[Install]
WantedBy=multi-user.target


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
sudo mkdir -p /home/tim/test_rfidpi/logs
sudo chown tim:tim /home/tim/test_rfidpi/logs
sudo chmod 750 /home/tim/test_rfidpi/logs

### migrate_db.sql
-- Drop existing tables if they exist
DROP TABLE IF EXISTS id_transactions;
DROP TABLE IF EXISTS id_item_master;
DROP TABLE IF EXISTS id_rfidtag;
DROP TABLE IF EXISTS seed_rental_classes;
DROP TABLE IF EXISTS refresh_state;
DROP TABLE IF EXISTS rental_class_mappings;

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
    notes TEXT
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
    date_updated DATETIME
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
    last_refresh VARCHAR(255) NOT NULL
);

-- Create rental_class_mappings table
CREATE TABLE rental_class_mappings (
    rental_class_id VARCHAR(50) PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100) NOT NULL
);





### config.py
import os

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# MariaDB configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'rfid_user',
    'password': 'rfid_user_password',  # Change this to a secure password
    'database': 'rfid_inventory',
    'charset': 'utf8mb4'
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
FULL_REFRESH_INTERVAL = 1800  # 30 minutes
INCREMENTAL_REFRESH_INTERVAL = 30  # 30 seconds

# Logging
LOG_FILE = os.path.join(BASE_DIR, 'logs', 'rfid_dashboard.log')
#mariadbhash   *8226E019AE8D0D41243D07D91ABCD8E2F20358BC  root password    MySecureRootPass123


### db_model.py
from app import db  # Import db from app/__init__.py
from datetime import datetime

class ItemMaster(db.Model):
    __tablename__ = 'id_item_master'

    tag_id = db.Column(db.String(50), primary_key=True)
    uuid_accounts_fk = db.Column(db.String(50))
    serial_number = db.Column(db.String(50))
    client_name = db.Column(db.String(100))
    rental_class_num = db.Column(db.String(50))
    common_name = db.Column(db.String(255))
    quality = db.Column(db.String(50))
    bin_location = db.Column(db.String(50))
    status = db.Column(db.String(50))
    last_contract_num = db.Column(db.String(50))
    last_scanned_by = db.Column(db.String(50))
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

    contract_number = db.Column(db.String(50))
    tag_id = db.Column(db.String(50), primary_key=True)
    scan_type = db.Column(db.String(50))
    scan_date = db.Column(db.DateTime, primary_key=True)
    client_name = db.Column(db.String(100))
    common_name = db.Column(db.String(255))
    bin_location = db.Column(db.String(50))
    status = db.Column(db.String(50))
    scan_by = db.Column(db.String(50))
    location_of_repair = db.Column(db.String(50))
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
    uuid_accounts_fk = db.Column(db.String(50))
    serial_number = db.Column(db.String(50))
    rental_class_num = db.Column(db.String(50))
    longitude = db.Column(db.DECIMAL(9, 6))
    latitude = db.Column(db.DECIMAL(9, 6))
    wet = db.Column(db.Boolean)
    service_required = db.Column(db.Boolean)
    notes = db.Column(db.Text)

class SeedRentalClass(db.Model):
    __tablename__ = 'seed_rental_classes'

    rental_class_id = db.Column(db.String(50), primary_key=True)
    common_name = db.Column(db.String(255))

class RefreshState(db.Model):
    __tablename__ = 'refresh_state'

    id = db.Column(db.Integer, primary_key=True)
    last_refresh = db.Column(db.String(50))

class RentalClassMapping(db.Model):
    __tablename__ = 'rental_class_mappings'

    rental_class_id = db.Column(db.String(50), primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    subcategory = db.Column(db.String(100), nullable=False)

# Added on 2025-04-21 to track hand-counted items for contracts
class HandCountedItems(db.Model):
    __tablename__ = 'id_hand_counted_items'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    contract_number = db.Column(db.String(50), nullable=False)  # Links to the contract
    item_name = db.Column(db.String(255), nullable=False)      # e.g., "Napkins"
    quantity = db.Column(db.Integer, nullable=False)           # Number of items
    action = db.Column(db.String(50), nullable=False)          # "Added" or "Removed"
    timestamp = db.Column(db.DateTime, nullable=False)         # When the action occurred
    user = db.Column(db.String(50), nullable=False)            # Who performed the action

# Added on 2025-04-23 to store user-defined rental class mappings
class UserRentalClassMapping(db.Model):
    __tablename__ = 'user_rental_class_mappings'

    rental_class_id = db.Column(db.String(50), primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    subcategory = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


###__init__.py
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_redis import FlaskRedis
from config import DB_CONFIG, REDIS_URL, LOG_FILE

# Initialize extensions
db = SQLAlchemy()
cache = FlaskRedis()

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, static_folder='static')

    # Configure logging
    log_dir = os.path.dirname(LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    handler = RotatingFileHandler(LOG_FILE, maxBytes=1000000, backupCount=5)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    # Clear existing handlers to prevent duplicates
    logging.getLogger('').handlers = []
    app.logger.handlers = []
    # Add handler to root logger and app logger
    logging.getLogger('').addHandler(handler)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.DEBUG)
    app.logger.propagate = False  # Prevent double logging
    app.logger.info("Application starting up - logging initialized")
    app.logger.debug(f"Static folder path: {app.static_folder}")

    # Database configuration
    try:
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}"
        )
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['REDIS_URL'] = REDIS_URL
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
        from app.services.refresh import refresh_bp
        from app.routes.tabs import tabs_bp

        app.register_blueprint(home_bp)
        app.register_blueprint(tab1_bp)
        app.register_blueprint(tab2_bp)
        app.register_blueprint(tab3_bp)
        app.register_blueprint(tab4_bp)
        app.register_blueprint(tab5_bp)
        app.register_blueprint(categories_bp)
        app.register_blueprint(health_bp)
        app.register_blueprint(refresh_bp)
        app.register_blueprint(tabs_bp)
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