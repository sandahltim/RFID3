# RFID3 Technical Deployment Guide

**Version:** 1.0  
**Date:** 2025-08-29  
**Target Audience:** System Administrators, DevOps Engineers  
**Environment:** Production/Staging Deployment  

---

## Executive Summary

This guide provides complete technical instructions for deploying the RFID3 Inventory Management and Business Intelligence System. The system includes advanced analytics, predictive capabilities, and executive dashboards with comprehensive API integration.

### System Requirements

#### Minimum Hardware Requirements
- **CPU**: ARM64 (Raspberry Pi 4+) or x86-64 (2+ cores)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 32GB minimum, 64GB+ recommended
- **Network**: 100 Mbps Ethernet connection
- **Database Storage**: 10GB+ for production data

#### Software Requirements
- **Operating System**: Linux (Ubuntu 20.04+, Raspberry Pi OS)
- **Python**: 3.11 or higher
- **Database**: MariaDB 10.6+ or MySQL 8.0+
- **Cache**: Redis 6.0+
- **Web Server**: nginx 1.18+ (production)

---

## Pre-Deployment Checklist

### Environment Preparation
- [ ] Server provisioned with required specifications
- [ ] Operating system updated to latest stable version
- [ ] Network connectivity tested and firewall configured
- [ ] SSL certificates obtained (if using HTTPS)
- [ ] Backup strategy defined and tested

### Access Requirements
- [ ] SSH access to deployment server
- [ ] Database administrator credentials
- [ ] API credentials for external integrations
- [ ] File system permissions for shared directories

---

## Installation Process

### Step 1: System Dependencies

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y \
    python3.11 \
    python3.11-pip \
    python3.11-dev \
    python3.11-venv \
    git \
    nginx \
    redis-server \
    mariadb-server \
    curl \
    wget \
    unzip \
    build-essential \
    libffi-dev \
    libssl-dev

# Start and enable services
sudo systemctl enable --now redis-server
sudo systemctl enable --now mariadb
sudo systemctl enable --now nginx
```

### Step 2: Database Setup

```bash
# Secure MariaDB installation
sudo mysql_secure_installation

# Create database and user
mysql -u root -p << 'SQL'
CREATE DATABASE rfid_inventory 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

CREATE USER 'rfid_user'@'localhost' 
    IDENTIFIED BY 'CHANGE_THIS_PASSWORD';

GRANT ALL PRIVILEGES ON rfid_inventory.* 
    TO 'rfid_user'@'localhost';

FLUSH PRIVILEGES;
SQL
```

### Step 3: Application Deployment

```bash
# Create application directory
sudo mkdir -p /opt/rfid3
sudo chown $USER:$USER /opt/rfid3
cd /opt/rfid3

# Clone repository
git clone https://github.com/your-org/RFID3.git .
# OR: Upload application files if not using git

# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create required directories
mkdir -p logs
mkdir -p backups
mkdir -p shared/{POR,incent}
mkdir -p instance

# Set proper permissions
sudo chown -R www-data:www-data /opt/rfid3/logs
sudo chown -R $USER:www-data /opt/rfid3/shared
chmod 755 /opt/rfid3/shared
chmod 775 /opt/rfid3/shared/{POR,incent}
```

### Step 4: Environment Configuration

```bash
# Create environment configuration file
cat > /opt/rfid3/.env << 'EOF'
# Database Configuration
DB_HOST=localhost
DB_USER=rfid_user
DB_PASSWORD=CHANGE_THIS_PASSWORD
DB_DATABASE=rfid_inventory
DB_CHARSET=utf8mb4
DB_COLLATION=utf8mb4_unicode_ci

# Application Configuration
APP_IP=0.0.0.0
FLASK_ENV=production
FLASK_DEBUG=False

# API Configuration (Internal Use)
API_USERNAME=api
API_PASSWORD=CHANGE_THIS_PASSWORD

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Security Configuration
SECRET_KEY=GENERATE_RANDOM_SECRET_KEY_HERE

# External API Configuration
EXTERNAL_API_ENABLED=true
WEATHER_API_KEY=your_weather_api_key_here
ECONOMIC_API_KEY=your_economic_api_key_here
