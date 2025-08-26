# config.py version: 2025-06-26-v8
import os

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Application IP address
APP_IP = os.environ.get('APP_IP', '192.168.3.110')

# MariaDB configuration - requires environment variables
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER'),  # Required - no default
    'password': os.environ.get('DB_PASSWORD'),  # Required - no default
    'database': os.environ.get('DB_DATABASE'),  # Required - no default
    'charset': os.environ.get('DB_CHARSET', 'utf8mb4'),
    'collation': os.environ.get('DB_COLLATION', 'utf8mb4_unicode_ci')
}

# Redis configuration
REDIS_URL = 'redis://localhost:6379/0'

# API configuration - requires environment variables
API_USERNAME = os.environ.get('API_USERNAME')  # Required - no default
API_PASSWORD = os.environ.get('API_PASSWORD')  # Required - no default
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


def validate_config():
    """
    Validate that all required configuration is present.
    Raises ValueError if any required configuration is missing.
    """
    required_vars = [
        ('DB_USER', DB_CONFIG['user']),
        ('DB_PASSWORD', DB_CONFIG['password']),
        ('DB_DATABASE', DB_CONFIG['database']),
        ('API_USERNAME', API_USERNAME),
        ('API_PASSWORD', API_PASSWORD),
    ]
    
    missing = [name for name, value in required_vars if not value]
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

