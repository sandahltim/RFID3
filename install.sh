#!/bin/bash

# Comprehensive install script for RFID Dashboard on Raspberry Pi
# Run as root or with sudo on a fresh Raspberry Pi OS

set -e  # Exit on any error

echo "Starting RFID Dashboard installation..."

# Variables
REPO_URL="https://github.com/sandahltim/_rfidpi.git"
BRANCH="newdev"
INSTALL_DIR="/home/tim/test_rfidpi"
USER="tim"
GROUP="tim"
DB_FILE="${INSTALL_DIR}/inventory.db"
HAND_COUNTED_DB="${INSTALL_DIR}/tab5_hand_counted.db"
LOG_DIR="/var/log/gunicorn"
SERVICE_NAME="rfid_dash"
API_LOGIN_URL="https://login.cloud.ptshome.com/api/v1/login"
ONEDRIVE_URL="https://1drv.ms/x/c/35ee6b0cbe6f4ec9/EQI9rtWjqMVCsUJBHhh1iO0BbmpPaIOn0P5k6UVNprnrzA?e=WTVXiS&download=1"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check command success
check_status() {
    if [ $? -ne 0 ]; then
        log "ERROR: $1 failed"
        exit 1
    fi
}

# 1. Update system and install prerequisites
log "Updating system and installing prerequisites..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3 python3-venv python3-dev libatlas-base-dev curl sqlite3
check_status "System update and prerequisite installation"

# 2. Create tim user if it doesn't exist
if ! id "${USER}" &>/dev/null; then
    log "Creating user ${USER}..."
    sudo adduser --gecos "" --disabled-password "${USER}"
    sudo usermod -aG sudo "${USER}"
    check_status "User creation"
fi

# 3. Set up install directory
log "Setting up install directory ${INSTALL_DIR}..."
if [ -d "${INSTALL_DIR}" ]; then
    log "Removing existing install directory..."
    sudo rm -rf "${INSTALL_DIR}"
fi
mkdir -p "${INSTALL_DIR}"
sudo chown "${USER}:${GROUP}" "${INSTALL_DIR}"
sudo chmod 775 "${INSTALL_DIR}"
cd "${INSTALL_DIR}"

# 4. Clone repository
log "Cloning ${REPO_URL} (branch: ${BRANCH})..."
git clone -b "${BRANCH}" "${REPO_URL}" .
check_status "Git clone"
sudo chown -R "${USER}:${GROUP}" "${INSTALL_DIR}"
sudo chmod -R 775 "${INSTALL_DIR}"

# 5. Create and activate virtual environment
log "Setting up Python virtual environment..."
python3 -m venv venv
check_status "Virtual environment creation"
source venv/bin/activate

# 6. Install Python dependencies
log "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
# Ensure consistent Flask and Gunicorn versions
pip install flask==2.2.5 gunicorn==23.0.0
check_status "Python dependency installation"

# 7. Initialize databases
log "Initializing databases..."
python3 db_utils.py
check_status "Main database initialization"
touch "${HAND_COUNTED_DB}"
sudo chmod 666 "${HAND_COUNTED_DB}"
sudo chown "${USER}:${GROUP}" "${HAND_COUNTED_DB}"
check_status "Hand-counted database setup"

# 8. Set up log directory
log "Setting up log directory ${LOG_DIR}..."
sudo mkdir -p "${LOG_DIR}"
sudo chown "${USER}:${GROUP}" "${LOG_DIR}"
sudo chmod 775 "${LOG_DIR}"
sudo touch /var/log/rfid_dash.log
sudo chown "${USER}:${GROUP}" /var/log/rfid_dash.log
sudo chmod 664 /var/log/rfid_dash.log

# 9. Configure systemd service
log "Configuring systemd service..."
cat > rfid_dash.service << EOL
[Unit]
Description=RFID Dashboard Flask App
After=network.target

[Service]
User=${USER}
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/start.sh
Restart=always
RestartSec=5
StandardOutput=append:/var/log/rfid_dash.log
StandardError=append:/var/log/rfid_dash.log

[Install]
WantedBy=multi-user.target
EOL
sudo mv rfid_dash.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/rfid_dash.service
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"
check_status "Systemd service setup"

# 10. Create start.sh
log "Creating start.sh..."
cat > start.sh << EOL
#!/bin/bash
source ${INSTALL_DIR}/venv/bin/activate
gunicorn --workers 2 --bind 0.0.0.0:7409 run:app --access-logfile ${LOG_DIR}/access.log --error-logfile ${LOG_DIR}/error.log --log-level debug
EOL
chmod +x start.sh
check_status "start.sh creation"

# 11. Verify API and OneDrive connectivity
log "Verifying API connectivity..."
curl -s -o /dev/null -w "%{http_code}" "${API_LOGIN_URL}" > /tmp/api_status
if [ "$(cat /tmp/api_status)" -ne 200 ] && [ "$(cat /tmp/api_status)" -ne 401 ]; then
    log "WARNING: API endpoint ${API_LOGIN_URL} may be unreachable (status: $(cat /tmp/api_status))"
else
    log "API endpoint reachable"
fi

log "Verifying OneDrive URL..."
curl -s -o /dev/null -w "%{http_code}" "${ONEDRIVE_URL}" > /tmp/onedrive_status
if [ "$(cat /tmp/onedrive_status)" -eq 200 ] || [ "$(cat /tmp/onedrive_status)" -eq 302 ]; then
    log "OneDrive URL accessible"
else
    log "WARNING: OneDrive URL may be inaccessible (status: $(cat /tmp/onedrive_status))"
fi

# 12. Start the service
log "Starting ${SERVICE_NAME} service..."
sudo systemctl start "${SERVICE_NAME}"
sleep 5  # Wait for service to start
if sudo systemctl is-active --quiet "${SERVICE_NAME}"; then
    log "${SERVICE_NAME} service started successfully"
else
    log "ERROR: Failed to start ${SERVICE_NAME}. Checking logs..."
    cat /var/log/rfid_dash.log
    cat "${LOG_DIR}/error.log"
    exit 1
fi

# 13. Test the app
log "Testing Flask app..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:7409 > /tmp/app_status
if [ "$(cat /tmp/app_status)" -eq 200 ]; then
    log "Flask app is running at http://localhost:7409"
else
    log "ERROR: Flask app not responding (status: $(cat /tmp/app_status)). Check logs:"
    cat /var/log/rfid_dash.log
    cat "${LOG_DIR}/error.log"
    exit 1
fi

log "Installation complete! Access the dashboard at http://$(hostname -I | awk '{print $1}'):7409"
log "Logs are at /var/log/rfid_dash.log and ${LOG_DIR}/"