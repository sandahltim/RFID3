#!/bin/bash
# RFID3 Easy Installation Script
# Version: 2025-08-24-v1
# 
# This script automates the complete installation of the RFID3 system
# on a fresh Raspberry Pi or Linux system.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="$PROJECT_DIR"
VENV_DIR="$INSTALL_DIR/venv"
SERVICE_NAME="rfid3"
BACKUP_DIR="${PROJECT_DIR}_backup_$(date +%Y%m%d_%H%M%S)"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}    RFID3 Easy Installation Script v1.0        ${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as correct user
if [ "$(whoami)" != "tim" ]; then
    print_error "This script must be run as user 'tim'"
    print_error "Please run: su - tim && ./easy_install.sh"
    exit 1
fi

# Backup existing installation if it exists
if [ -d "$INSTALL_DIR" ]; then
    print_warning "Existing RFID3 installation found"
    read -p "Do you want to backup the existing installation? (y/N): " backup_choice
    if [[ $backup_choice =~ ^[Yy]$ ]]; then
        print_status "Creating backup at $BACKUP_DIR"
        cp -r "$INSTALL_DIR" "$BACKUP_DIR"
        print_status "Backup created successfully"
    fi
fi

# Update system packages
print_status "Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

# Install system dependencies
print_status "Installing system dependencies..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    redis-server \
    mariadb-server \
    mariadb-client \
    nginx \
    supervisor \
    curl \
    wget \
    build-essential \
    python3-dev \
    default-libmysqlclient-dev \
    pkg-config

# Start and enable services
print_status "Starting system services..."
sudo systemctl start redis-server
sudo systemctl enable redis-server
sudo systemctl start mariadb
sudo systemctl enable mariadb

# Secure MariaDB installation (basic setup)
print_status "Setting up MariaDB..."
sudo mysql -e "CREATE DATABASE IF NOT EXISTS rfid3;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'rfid3'@'localhost' IDENTIFIED BY 'rfid3_secure_password';"
sudo mysql -e "GRANT ALL PRIVILEGES ON rfid3.* TO 'rfid3'@'localhost';"
sudo mysql -e "FLUSH PRIVILEGES;"

# Clone or update repository
if [ -d "$INSTALL_DIR/.git" ]; then
    print_status "Updating existing repository..."
    cd "$INSTALL_DIR"
    git fetch origin
    git checkout RFID3dev
    git pull origin RFID3dev
else
    print_status "Cloning RFID3 repository..."
    git clone https://github.com/sandahltim/RFID3.git "$INSTALL_DIR" || {
        print_error "Failed to clone repository"
        exit 1
    }
    cd "$INSTALL_DIR"
    git checkout RFID3dev
fi

# Create virtual environment
print_status "Creating Python virtual environment..."
if [ -d "$VENV_DIR" ]; then
    rm -rf "$VENV_DIR"
fi
python3 -m venv "$VENV_DIR"

# Activate virtual environment and install Python dependencies
print_status "Installing Python dependencies..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt

# Create config file from template
print_status "Creating configuration file..."
if [ ! -f "$INSTALL_DIR/config.py" ]; then
    cp "$INSTALL_DIR/config.py.template" "$INSTALL_DIR/config.py" 2>/dev/null || {
        cat > "$INSTALL_DIR/config.py" << EOF
# RFID3 Configuration
import os

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'rfid3',
    'password': 'rfid3_secure_password',
    'database': 'rfid3',
    'charset': 'utf8mb4'
}

# Redis configuration
REDIS_URL = 'redis://localhost:6379/0'

# API Configuration (update these with your actual credentials)
API_USERNAME = 'your_api_username'
API_PASSWORD = 'your_api_password'
LOGIN_URL = 'https://cs.iot.ptshome.com/api/v1/login'

# Logging
LOG_FILE = os.path.join(BASE_DIR, 'logs', 'rfid3.log')

# Application settings
APP_IP = '0.0.0.0'
PORT = 8102
DEBUG = False

# Other settings
INCREMENTAL_LOOKBACK_SECONDS = 300
INCREMENTAL_FALLBACK_SECONDS = 86400
EOF
    print_status "Configuration file created - you'll need to update API credentials"
fi

# Create directories
print_status "Creating directories..."
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/static/uploads"

# Set permissions
print_status "Setting permissions..."
chmod +x "$INSTALL_DIR/scripts/"*.py
chmod +x "$INSTALL_DIR/scripts/"*.sh

# Initialize database
print_status "Initializing database..."
cd "$INSTALL_DIR"
source "$VENV_DIR/bin/activate"
python3 -c "
from app import create_app, db
import os
os.environ['SNAPSHOT_AUTOMATION'] = '1'  # Skip API client
app = create_app()
with app.app_context():
    db.create_all()
    print('Database tables created successfully')
" || print_warning "Database initialization may need manual setup"

# Run database migrations
if [ -f "$INSTALL_DIR/scripts/add_contract_snapshots.sql" ]; then
    print_status "Running database migrations..."
    mysql -u rfid3 -prfid3_secure_password rfid3 < "$INSTALL_DIR/scripts/add_contract_snapshots.sql" || {
        print_warning "Some migrations may have failed - check manually"
    }
fi

# Setup supervisor configuration
print_status "Setting up supervisor service..."
sudo tee /etc/supervisor/conf.d/rfid3.conf > /dev/null << EOF
[program:rfid3]
command=$VENV_DIR/bin/gunicorn --workers 1 --threads 4 --timeout 600 --bind 0.0.0.0:8102 --error-logfile $INSTALL_DIR/logs/gunicorn_error.log --access-logfile $INSTALL_DIR/logs/gunicorn_access.log run:app
directory=$INSTALL_DIR
user=tim
autostart=true
autorestart=true
stderr_logfile=$INSTALL_DIR/logs/supervisor_error.log
stdout_logfile=$INSTALL_DIR/logs/supervisor_output.log
environment=PYTHONPATH="$INSTALL_DIR"
EOF

# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start rfid3

# Setup automated snapshots
print_status "Setting up automated contract snapshots..."
"$INSTALL_DIR/scripts/setup_snapshot_cron.sh" || print_warning "Snapshot automation setup may need manual configuration"

# Setup nginx reverse proxy (optional)
read -p "Do you want to setup nginx reverse proxy on port 80? (y/N): " nginx_choice
if [[ $nginx_choice =~ ^[Yy]$ ]]; then
    print_status "Setting up nginx reverse proxy..."
    sudo tee /etc/nginx/sites-available/rfid3 > /dev/null << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8102;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    sudo ln -sf /etc/nginx/sites-available/rfid3 /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo nginx -t && sudo systemctl reload nginx
    print_status "Nginx reverse proxy configured"
fi

# Final status check
print_status "Checking service status..."
sleep 5
if sudo supervisorctl status rfid3 | grep -q "RUNNING"; then
    print_status "RFID3 service is running successfully!"
else
    print_warning "RFID3 service may not be running properly"
    print_status "Check logs: $INSTALL_DIR/logs/"
fi

# Installation complete
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}           Installation Complete!              ${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${GREEN}✅ RFID3 system installed successfully${NC}"
echo -e "${BLUE}📍 Installation directory:${NC} $INSTALL_DIR"
echo -e "${BLUE}🌐 Web interface:${NC} http://$(hostname -I | awk '{print $1}'):8102"
if [[ $nginx_choice =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}🌐 Nginx proxy:${NC} http://$(hostname -I | awk '{print $1}')"
fi
echo -e "${BLUE}📊 Service management:${NC} sudo supervisorctl status rfid3"
echo -e "${BLUE}📁 Log files:${NC} $INSTALL_DIR/logs/"
echo ""
echo -e "${YELLOW}⚠️  Next Steps:${NC}"
echo -e "1. Update API credentials in: $INSTALL_DIR/config.py"
echo -e "2. Test the web interface"
echo -e "3. Run first data refresh from the web interface"
echo -e "4. Check logs for any errors"
echo ""
echo -e "${GREEN}Installation completed successfully! 🎉${NC}"