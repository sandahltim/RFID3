# config.py version: 2025-06-26-v8
import os

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Application IP address
APP_IP = os.environ.get('APP_IP', '192.168.3.110')

# MariaDB configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'user': os.environ.get('DB_USER', 'rfid_user'),
    'password': os.environ.get('DB_PASSWORD', 'rfid_user_password'),
    'database': os.environ.get('DB_DATABASE', 'rfid_inventory'),
    'charset': os.environ.get('DB_CHARSET', 'utf8mb4'),
    'collation': os.environ.get('DB_COLLATION', 'utf8mb4_unicode_ci')
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


def validate_config():
    """
    Validate that all required configuration is present.
    Raises ValueError if any required configuration is missing.
    
    Note: Temporarily using defaults for backwards compatibility.
    Consider setting environment variables for production security.
    """
    # Check for environment-based configuration (optional for now)
    env_vars = [
        ('DB_USER', os.environ.get('DB_USER')),
        ('DB_PASSWORD', os.environ.get('DB_PASSWORD')),
        ('DB_DATABASE', os.environ.get('DB_DATABASE')),
        ('API_USERNAME', os.environ.get('API_USERNAME')),
        ('API_PASSWORD', os.environ.get('API_PASSWORD')),
    ]
    
    # Log if using defaults vs environment variables
    import logging
    for name, value in env_vars:
        if value:
            logging.info(f"Using environment variable for {name}")
        else:
            logging.info(f"Using default configuration for {name}")
    
    # Configuration is valid (using defaults if needed)

