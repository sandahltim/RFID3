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
    'collation': 'utf8mb4_general_ci'
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