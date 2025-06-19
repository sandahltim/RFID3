# config.py version: 2025-06-19-v4
import os

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# MariaDB configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'rfid_user',
    'password': 'rfid_user_password',  # Change this to a secure password
    'database': 'rfid_inventory',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'  # Changed to compatible collation for MariaDB 10.11
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
INCREMENTAL_LOOKBACK_SECONDS = 2592000  # Look back 30 days for incremental refresh
INCREMENTAL_FALLBACK_SECONDS = 172800  # Fall back to 2 days if API filter fails

# Bulk update configuration
BULK_UPDATE_BATCH_SIZE = 50  # Batch size for bulk updates in tab5.py

# Logging
LOG_FILE = os.path.join(BASE_DIR, 'logs', 'rfid_dashboard.log')