# RFID3 Configuration Management Guide

**Version:** 1.0  
**Date:** 2025-08-29  
**Target Audience:** System Administrators, Configuration Managers

---

## Configuration Overview

The RFID3 system uses multiple configuration sources to ensure flexibility, security, and maintainability:

1. **Environment Variables** (.env file)
2. **Database Configuration** (inventory_config table)  
3. **Application Configuration** (config.py)
4. **Store Configuration** (app/config/stores.py)
5. **Dashboard Configuration** (app/config/dashboard_config.py)

---

## Environment Configuration

### Core Environment Variables

**File Location:** `/opt/rfid3/.env`

```bash
# Database Configuration
DB_HOST=localhost
DB_USER=rfid_user
DB_PASSWORD=secure_password_here
DB_DATABASE=rfid_inventory
DB_CHARSET=utf8mb4
DB_COLLATION=utf8mb4_unicode_ci

# Application Settings
APP_IP=0.0.0.0
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=32_character_random_string_here

# External API Configuration  
API_USERNAME=api
API_PASSWORD=secure_api_password_here
LOGIN_URL=https://login.cloud.ptshome.com/api/v1/login
ITEM_MASTER_URL=https://cs.iot.ptshome.com/api/v1/data/14223767938169344381
TRANSACTION_URL=https://cs.iot.ptshome.com/api/v1/data/14223767938169346196
SEED_URL=https://cs.iot.ptshome.com/api/v1/data/14223767938169215907

# Cache Configuration
REDIS_URL=redis://localhost:6379/0

# External Data APIs
WEATHER_API_KEY=your_weather_api_key_here
ECONOMIC_API_KEY=your_economic_data_key_here
EXTERNAL_API_ENABLED=true

# Performance Settings
FULL_REFRESH_INTERVAL=3600
INCREMENTAL_REFRESH_INTERVAL=60
INCREMENTAL_LOOKBACK_SECONDS=600
BULK_UPDATE_BATCH_SIZE=50
```

### Security Best Practices

```bash
# Set secure file permissions
chmod 600 /opt/rfid3/.env
chown www-data:www-data /opt/rfid3/.env

# Generate secure secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Validate configuration
source /opt/rfid3/.env
echo "Database: $DB_DATABASE, Host: $DB_HOST"
```

---

## Database Configuration

### Configuration Tables

**Table: `inventory_config`**
```sql
CREATE TABLE inventory_config (
    id INT PRIMARY KEY AUTO_INCREMENT,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT,
    config_type ENUM('string', 'integer', 'float', 'boolean', 'json') DEFAULT 'string',
    description TEXT,
    category VARCHAR(50) DEFAULT 'general',
    is_system BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### Alert Configuration

```sql
-- Alert thresholds
INSERT INTO inventory_config (config_key, config_value, config_type, description, category) VALUES
('stale_item_default_days', '30', 'integer', 'Default days before item considered stale', 'alerts'),
('stale_item_resale_days', '7', 'integer', 'Days for resale items before stale', 'alerts'),  
('stale_item_pack_days', '14', 'integer', 'Days for pack items before stale', 'alerts'),
('high_usage_threshold', '0.8', 'float', 'Utilization % threshold for high usage alert', 'alerts'),
('low_usage_threshold', '0.2', 'float', 'Utilization % threshold for low usage alert', 'alerts'),
('critical_alert_limit', '50', 'integer', 'Maximum critical alerts before escalation', 'alerts');
```

### Business Rules Configuration

```sql
-- Status classifications
INSERT INTO inventory_config (config_key, config_value, config_type, description, category) VALUES
('rental_statuses', '["On Rent", "Delivered", "Out to Customer"]', 'json', 'Statuses counting as rented', 'business_rules'),
('available_statuses', '["Ready to Rent"]', 'json', 'Statuses counting as available', 'business_rules'),
('service_statuses', '["Repair", "Needs to be Inspected", "Lost"]', 'json', 'Statuses requiring service', 'business_rules'),
('resale_categories', '["Resale"]', 'json', 'Categories treated as resale inventory', 'business_rules');
```

### Performance Configuration

```sql
-- Performance settings
INSERT INTO inventory_config (config_key, config_value, config_type, description, category) VALUES
('cache_dashboard_minutes', '5', 'integer', 'Dashboard cache duration in minutes', 'performance'),
('cache_analytics_minutes', '15', 'integer', 'Analytics cache duration in minutes', 'performance'),
('query_timeout_seconds', '30', 'integer', 'Database query timeout', 'performance'),
('batch_size_imports', '100', 'integer', 'Batch size for bulk imports', 'performance');
```

---

## Store Configuration

### Store Mapping Configuration

**File Location:** `/opt/rfid3/app/config/stores.py`

```python
# Store mapping configuration
STORE_MAPPINGS = {
    # POS Code -> Internal Store Data
    '001': {
        'internal_code': '6800',
        'display_name': 'Brooklyn Park',
        'region': 'North',
        'manager': 'John Smith',
        'phone': '(763) 555-0100',
        'address': '123 Main St, Brooklyn Park, MN',
        'operating_hours': {
            'monday': '8:00-17:00',
            'tuesday': '8:00-17:00', 
            'wednesday': '8:00-17:00',
            'thursday': '8:00-17:00',
            'friday': '8:00-17:00',
            'saturday': '9:00-15:00',
            'sunday': 'closed'
        },
        'timezone': 'America/Chicago',
        'active': True
    },
    '002': {
        'internal_code': '3607',
        'display_name': 'Wayzata', 
        'region': 'West',
        'manager': 'Jane Johnson',
        'phone': '(952) 555-0200',
        'address': '456 Lake St, Wayzata, MN',
        'operating_hours': {
            'monday': '8:00-17:00',
            'tuesday': '8:00-17:00',
            'wednesday': '8:00-17:00', 
            'thursday': '8:00-17:00',
            'friday': '8:00-17:00',
            'saturday': '9:00-15:00',
            'sunday': 'closed'
        },
        'timezone': 'America/Chicago',
        'active': True
    },
    '003': {
        'internal_code': '8101',
        'display_name': 'Fridley',
        'region': 'Central',
        'manager': 'Bob Wilson',
        'phone': '(763) 555-0300', 
        'address': '789 University Ave, Fridley, MN',
        'operating_hours': {
            'monday': '8:00-17:00',
            'tuesday': '8:00-17:00',
            'wednesday': '8:00-17:00',
            'thursday': '8:00-17:00', 
            'friday': '8:00-17:00',
            'saturday': '9:00-15:00',
            'sunday': 'closed'
        },
        'timezone': 'America/Chicago',
        'active': True
    },
    '004': {
        'internal_code': '728',
        'display_name': 'Elk River',
        'region': 'Northwest',
        'manager': 'Alice Brown',
        'phone': '(763) 555-0400',
        'address': '321 River Rd, Elk River, MN', 
        'operating_hours': {
            'monday': '8:00-17:00',
            'tuesday': '8:00-17:00',
            'wednesday': '8:00-17:00',
            'thursday': '8:00-17:00',
            'friday': '8:00-17:00',
            'saturday': '9:00-15:00',
            'sunday': 'closed'
        },
        'timezone': 'America/Chicago',
        'active': True
    }
}

# Helper functions
def get_store_display_name(store_code):
    """Get display name for store code"""
    for pos_code, store_data in STORE_MAPPINGS.items():
        if store_data['internal_code'] == store_code:
            return store_data['display_name']
    return store_code

def get_internal_code(pos_code):
    """Get internal store code from POS code"""
    return STORE_MAPPINGS.get(pos_code, {}).get('internal_code', pos_code)

def get_all_active_stores():
    """Get all active store mappings"""
    return {k: v for k, v in STORE_MAPPINGS.items() if v.get('active', True)}
```

---

## Dashboard Configuration

### Executive Dashboard Settings

**File Location:** `/opt/rfid3/app/config/dashboard_config.py`

```python
# Executive Dashboard Configuration
EXECUTIVE_DASHBOARD_CONFIG = {
    'default_kpi_period_weeks': 12,
    'revenue_growth_comparison_weeks': 4,
    'store_performance_periods': 26,
    'prediction_horizon_weeks': 4,
    
    # Chart configurations
    'revenue_trend_chart': {
        'height': 400,
        'colors': {
            'revenue': '#2E8B57',
            'growth': '#FF6B35',
            'target': '#4169E1'
        },
        'animation_duration': 1000
    },
    
    'store_performance_chart': {
        'height': 350,
        'colors': ['#FF6B35', '#4ECDC4', '#45B7D1', '#96CEB4'],
        'show_efficiency_line': True
    },
    
    'prediction_chart': {
        'height': 300,
        'confidence_interval_opacity': 0.2,
        'prediction_line_dash': [5, 5]
    }
}

# Analytics Dashboard Configuration  
ANALYTICS_DASHBOARD_CONFIG = {
    'health_score_weights': {
        'stale_items': 0.3,
        'utilization': 0.25,
        'alert_severity': 0.2,
        'data_quality': 0.15,
        'system_performance': 0.1
    },
    
    'alert_color_scheme': {
        'critical': '#DC3545',
        'high': '#FD7E14', 
        'medium': '#FFC107',
        'low': '#28A745'
    },
    
    'utilization_thresholds': {
        'excellent': 0.8,
        'good': 0.6,
        'fair': 0.4,
        'poor': 0.2
    }
}

# Predictive Analytics Configuration
PREDICTIVE_CONFIG = {
    'external_data_sources': {
        'weather': {
            'enabled': True,
            'refresh_interval_hours': 6,
            'api_timeout_seconds': 30
        },
        'economic': {
            'enabled': True, 
            'refresh_interval_hours': 24,
            'api_timeout_seconds': 60
        },
        'seasonal': {
            'enabled': True,
            'refresh_interval_hours': 168  # Weekly
        }
    },
    
    'correlation_analysis': {
        'min_data_points': 10,
        'significance_threshold': 0.05,
        'correlation_threshold': 0.3,
        'max_lag_weeks': 4
    },
    
    'demand_forecasting': {
        'confidence_level': 0.95,
        'forecast_horizon_weeks': 4,
        'min_historical_weeks': 26
    }
}
```

---

## Configuration Management Procedures

### Updating Configuration

#### 1. Environment Variables
```bash
# Edit environment file
sudo nano /opt/rfid3/.env

# Validate changes
source /opt/rfid3/.env
echo "Configuration loaded: DB_DATABASE=$DB_DATABASE"

# Restart application
sudo systemctl restart rfid3.service

# Verify health
curl http://localhost:8101/health
```

#### 2. Database Configuration
```python
# Using the configuration API
import requests

# Update configuration value
response = requests.put('http://localhost:8101/api/inventory/configuration', 
    json={
        'alert_thresholds': {
            'stale_item_days': {
                'default': 45,  # Changed from 30
                'resale': 14,   # Changed from 7
                'pack': 21      # Changed from 14
            }
        }
    }
)

# Or direct SQL update
mysql -u rfid_user -p rfid_inventory << 'SQL'
UPDATE inventory_config 
SET config_value = '45' 
WHERE config_key = 'stale_item_default_days';
SQL
```

#### 3. Application Configuration Files
```bash
# Store configuration
sudo nano /opt/rfid3/app/config/stores.py

# Dashboard configuration  
sudo nano /opt/rfid3/app/config/dashboard_config.py

# Main application config
sudo nano /opt/rfid3/config.py

# Restart to apply changes
sudo systemctl restart rfid3.service
```

### Configuration Backup

```bash
# Create configuration backup script
cat > /opt/rfid3/scripts/backup_config.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/opt/rfid3/backups/config"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup environment file
cp /opt/rfid3/.env "$BACKUP_DIR/env_$DATE"

# Backup configuration files
cp /opt/rfid3/config.py "$BACKUP_DIR/config_$DATE.py"
cp /opt/rfid3/app/config/stores.py "$BACKUP_DIR/stores_$DATE.py" 
cp /opt/rfid3/app/config/dashboard_config.py "$BACKUP_DIR/dashboard_config_$DATE.py"

# Backup database configuration
mysqldump -u rfid_user -p'rfid_user_password' rfid_inventory inventory_config > "$BACKUP_DIR/db_config_$DATE.sql"

echo "Configuration backup completed: $DATE"
