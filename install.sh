#!/bin/bash

# Comprehensive install script for RFID Dashboard on Raspberry Pi
# Run as root or with sudo

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

# 1. Check disk health and filesystem
log "Checking disk health..."
sudo dmesg | grep -i "I/O error" > /tmp/dmesg_errors || true
if [ -s /tmp/dmesg_errors ]; then
    log "WARNING: Disk I/O errors found. Check SD card with 'fsck /dev/mmcblk0p2'."
fi
if mount | grep "/ " | grep -q "ro,"; then
    log "ERROR: Filesystem is read-only. Attempting to remount..."
    sudo mount -o remount,rw /
    check_status "Filesystem remount"
fi
log "Running fsck to verify SD card..."
sudo touch /forcefsck
log "Filesystem check scheduled. Reboot after install if errors are found."

# 2. Update system and install prerequisites
log "Updating system and installing prerequisites..."
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3 python3-venv python3-dev libatlas-base-dev curl sqlite3
check_status "System update and prerequisite installation"

# 3. Create tim user if it doesn't exist
if ! id "${USER}" &>/dev/null; then
    log "Creating user ${USER}..."
    sudo adduser --gecos "" --disabled-password "${USER}"
    sudo usermod -aG sudo "${USER}"
    check_status "User creation"
fi

# 4. Set up install directory
log "Setting up install directory ${INSTALL_DIR}..."
if [ -d "${INSTALL_DIR}" ]; then
    log "Removing existing install directory..."
    sudo rm -rf "${INSTALL_DIR}"
fi
mkdir -p "${INSTALL_DIR}"
sudo chown "${USER}:${GROUP}" "${INSTALL_DIR}"
sudo chmod 775 "${INSTALL_DIR}"
cd "${INSTALL_DIR}"

# 5. Clone repository
log "Cloning ${REPO_URL} (branch: ${BRANCH})..."
git clone -b "${BRANCH}" "${REPO_URL}" .
check_status "Git clone"
sudo chown -R "${USER}:${GROUP}" "${INSTALL_DIR}"
sudo chmod -R 775 "${INSTALL_DIR}"

# 6. Create and activate virtual environment
log "Setting up Python virtual environment..."
python3 -m venv venv
check_status "Virtual environment creation"
source venv/bin/activate

# 7. Install Python dependencies
log "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install flask==2.2.5 gunicorn==23.0.0
check_status "Python dependency installation"

# 8. Initialize databases
log "Initializing databases..."
sudo mkdir -p "${INSTALL_DIR}"
sudo chown "${USER}:${GROUP}" "${INSTALL_DIR}"
sudo chmod 775 "${INSTALL_DIR}"
python3 db_utils.py
check_status "Main database initialization"
if [ -f "${DB_FILE}" ]; then
    sudo chmod 664 "${DB_FILE}"
    sudo chown "${USER}:${GROUP}" "${DB_FILE}"
    ls -l "${DB_FILE}"
    log "Set permissions on ${DB_FILE}"
else
    log "ERROR: ${DB_FILE} not created"
    exit 1
fi
touch "${HAND_COUNTED_DB}"
sudo chmod 666 "${HAND_COUNTED_DB}"
sudo chown "${USER}:${GROUP}" "${HAND_COUNTED_DB}"
ls -l "${HAND_COUNTED_DB}"
check_status "Hand-counted database setup"

# 9. Verify database write access
log "Verifying database write access..."
cat > test_db.py << EOL
import sqlite3
db = "${DB_FILE}"
conn = sqlite3.connect(db)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)")
cursor.execute("INSERT INTO test (id) VALUES (1)")
conn.commit()
conn.close()
print("Database write test passed")
EOL
sudo chown "${USER}:${GROUP}" test_db.py
sudo chmod 775 test_db.py
python3 test_db.py
check_status "Database write test"

# 10. Set up log directory
log "Setting up log directory ${LOG_DIR}..."
sudo mkdir -p "${LOG_DIR}"
sudo chown "${USER}:${GROUP}" "${LOG_DIR}"
sudo chmod 775 "${LOG_DIR}"
sudo touch /var/log/rfid_dash.log
sudo chown "${USER}:${GROUP}" /var/log/rfid_dash.log
sudo chmod 664 /var/log/rfid_dash.log

# 11. Configure systemd service
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

# 12. Create start.sh
log "Creating start.sh..."
cat > start.sh << EOL
#!/bin/bash
source ${INSTALL_DIR}/venv/bin/activate
gunicorn --workers 2 --bind 0.0.0.0:7409 run:app --access-logfile ${LOG_DIR}/access.log --error-logfile ${LOG_DIR}/error.log --log-level debug
EOL
chmod +x start.sh
check_status "start.sh creation"

# 13. Verify API and OneDrive connectivity
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

# 14. Patch run.py to avoid premature DB deletion
log "Patching run.py to ensure DB permissions..."
cat > run.py << EOL
import os
import logging
import time
import threading
from db_utils import initialize_db
from refresh_logic import refresh_data
from app import create_app
from werkzeug.serving import is_running_from_reloader
from config import DB_FILE
from db_connection import DatabaseConnection

# Initialize Flask app globally for Gunicorn
app = create_app()

# Initialize DB only if it doesn't exist
db_path = os.path.join(os.path.dirname(__file__), "inventory.db")
if not os.path.exists(db_path):
    print("Initializing new database...")
    initialize_db()  # Create fresh schema
    os.chmod(db_path, 0o664)  # Set read/write for owner and group
    os.chown(db_path, os.getuid(), os.getgid())  # Set owner to current user (tim)
else:
    print("Using existing database...")

# Verify write access
try:
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER)")
        conn.execute("INSERT INTO test (id) VALUES (1)")
    print("Database write access confirmed")
except sqlite3.OperationalError as e:
    print(f"ERROR: Database not writable: {e}")
    raise

# Perform full refresh
refresh_data(full_refresh=True)  # Full API refresh

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("Starting Flask application...")
    try:
        app.run(host="0.0.0.0", port=7409, debug=True)
    except Exception as e:
        logging.error(f"Flask failed to start: {e}")
EOL
sudo chown "${USER}:${GROUP}" run.py
sudo chmod 664 run.py
log "run.py patched"

# 15. Start the service
log "Starting ${SERVICE_NAME} service..."
sudo systemctl start "${SERVICE_NAME}"
sleep 15  # Extended wait for stability
if sudo systemctl is-active --quiet "${SERVICE_NAME}"; then
    log "${SERVICE_NAME} service started successfully"
else
    log "ERROR: Failed to start ${SERVICE_NAME}. Checking logs..."
    cat /var/log/rfid_dash.log
    cat "${LOG_DIR}/error.log"
    exit 1
fi

# 16. Test the app
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
log "Reboot recommended to run fsck if disk errors were detected."