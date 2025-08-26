# config.py version: 2025-06-26-v8
import os
from pathlib import Path

# Base directory - using Path for better path handling
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
STATIC_DIR = BASE_DIR / "static"
SHARED_DIR = BASE_DIR / "shared"

# Application IP address
APP_IP = os.environ.get('APP_IP', '192.168.3.110')

# MariaDB configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'rfid_user'),
    'password': os.environ.get('DB_PASSWORD'),
    'database': os.environ.get('DB_DATABASE', 'rfid_inventory'),
    'charset': os.environ.get('DB_CHARSET', 'utf8mb4'),
    'collation': os.environ.get('DB_COLLATION', 'utf8mb4_unicode_ci')
}

# Redis configuration
REDIS_URL = 'redis://localhost:6379/0'

# API configuration
API_USERNAME = os.environ.get("API_USERNAME")  # no default
API_PASSWORD = os.environ.get("API_PASSWORD")
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
LOG_FILE = LOG_DIR / 'rfid_dashboard.log'

# SQLAlchemy configuration
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'max_overflow': 20,
    'pool_timeout': 30,
    'pool_recycle': 1800,  # Recycle connections every 30 minutes
    'connect_args': {'charset': 'utf8mb4', 'collation': 'utf8mb4_unicode_ci'}
}


def validate_config():
    """
    Validate that all required configuration is present.
    Raises RuntimeError if any required environment variables are missing.
    """
    required_vars = ['API_USERNAME', 'API_PASSWORD', 'DB_PASSWORD']
    
    for var in required_vars:
        if not globals()[var]:
            raise RuntimeError(f"{var} environment variable required")

