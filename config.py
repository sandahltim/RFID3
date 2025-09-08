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
    'password': os.environ.get('DB_PASSWORD') or 'rfid_user_password',  # default for development
    'database': os.environ.get('DB_DATABASE', 'rfid_inventory'),
    'charset': os.environ.get('DB_CHARSET', 'utf8mb4'),
    'collation': os.environ.get('DB_COLLATION', 'utf8mb4_unicode_ci')
}

# Redis configuration
REDIS_URL = 'redis://localhost:6379/0'

# API configuration - Internal use only with hardcoded credentials  
API_USERNAME = os.environ.get("API_USERNAME") or "api"  # hardcoded for internal use
API_PASSWORD = os.environ.get("API_PASSWORD") or "Broadway8101"  # hardcoded for internal use
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
    
    Note: Currently using defaults for development. In production, set environment
    variables for API_USERNAME, API_PASSWORD, and DB_PASSWORD for security.
    """
    # Check if running with environment variables (recommended for production)
    env_vars = ['API_USERNAME', 'API_PASSWORD', 'DB_PASSWORD']
    using_defaults = []
    
    for var in env_vars:
        if not os.environ.get(var):
            using_defaults.append(var)
    
    if using_defaults:
        import logging
        logging.warning(f"Using default values for: {', '.join(using_defaults)}. "
                       f"Set environment variables for production security.")

