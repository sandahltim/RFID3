# RFID3 Technical Deployment Guide

**Version:** 1.0  
**Date:** 2025-08-29  
**System:** RFID Inventory Management & Predictive Analytics

---

## Quick Start Deployment

### Prerequisites
```bash
# System requirements
- Ubuntu 20.04+ or Raspberry Pi OS
- Python 3.11+
- MariaDB 10.6+
- Redis 6.0+
- 4GB+ RAM, 32GB+ storage

# Install dependencies
sudo apt update && sudo apt install -y python3.11 python3.11-pip python3.11-venv mariadb-server redis-server nginx git
```

### Database Setup
```bash
# Create database
mysql -u root -p << 'SQL'
CREATE DATABASE rfid_inventory CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'rfid_user'@'localhost' IDENTIFIED BY 'rfid_user_password';
GRANT ALL PRIVILEGES ON rfid_inventory.* TO 'rfid_user'@'localhost';
FLUSH PRIVILEGES;
SQL
```

### Application Deployment
```bash
# Clone and setup
git clone <repository-url> /opt/rfid3
cd /opt/rfid3
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Initialize database
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

### Service Configuration
```bash
# Create systemd service
sudo tee /etc/systemd/system/rfid3.service << 'EOF'
[Unit]
Description=RFID3 Application
After=network.target mariadb.service

[Service]
Type=exec
User=www-data
WorkingDirectory=/opt/rfid3
Environment=PATH=/opt/rfid3/venv/bin
ExecStart=/opt/rfid3/venv/bin/gunicorn -b 0.0.0.0:8101 -w 4 run:app
Restart=always

[Install]
WantedBy=multi-user.target
