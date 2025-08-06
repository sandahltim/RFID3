#!/bin/bash
# setup_samba.sh
# Configures Samba server for RFIDShare on Raspberry Pi and ensures shared directory exists
# Created: 2025-05-20
# Updated: 2025-05-20
# Usage: Run as root or with sudo
# chmod +x setup_samba.sh && sudo ./setup_samba.sh

# Exit on error
set -e

# Log file
LOG_FILE="/home/tim/RFID3/logs/samba_setup.log"
mkdir -p /home/tim/RFID3/logs
touch $LOG_FILE
chown tim:tim $LOG_FILE
chmod 640 $LOG_FILE
exec 1>>$LOG_FILE 2>&1
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting Samba setup"

# Ensure Samba is installed
if ! command -v smbd >/dev/null; then
    echo "Installing Samba..."
    apt update
    apt install -y samba samba-common-bin
else
    echo "Samba already installed"
fi

# Create shared directory
SHARED_DIR="/home/tim/RFID3/shared"
echo "Creating shared directory: $SHARED_DIR"
mkdir -p $SHARED_DIR
chown tim:tim $SHARED_DIR
chmod 770 $SHARED_DIR

# Verify Samba configuration includes RFIDShare
if ! grep -q "\[RFIDShare\]" /etc/samba/smb.conf; then
    echo "Adding RFIDShare configuration to smb.conf"
    # Backup existing Samba configuration
    if [ -f /etc/samba/smb.conf ]; then
        echo "Backing up existing smb.conf"
        cp /etc/samba/smb.conf /etc/samba/smb.conf.bak
    fi
    # Append RFIDShare configuration
    cat << EOF >> /etc/samba/smb.conf
[RFIDShare]
path = /home/tim/RFID3/shared
writable = yes
browsable = yes
guest ok = no
valid users = tim
create mask = 0660
directory mask = 0770
EOF
else
    echo "RFIDShare configuration already exists in smb.conf"
fi

# Ensure Samba user 'tim' exists
if ! pdbedit -L | grep -q "^tim:"; then
    echo "Setting up Samba user 'tim'"
    (echo "rfid_samba_pass"; echo "rfid_samba_pass") | smbpasswd -a tim
else
    echo "Samba user 'tim' already exists"
fi

# Enable and restart Samba services
echo "Restarting Samba services"
systemctl enable smbd
systemctl enable nmbd
systemctl restart smbd
systemctl restart nmbd

# Open firewall ports for Samba (if ufw is enabled)
if command -v ufw >/dev/null; then
    echo "Configuring firewall for Samba"
    ufw allow Samba
fi

# Test Samba configuration
echo "Testing Samba configuration"
testparm -s

# Set ownership and permissions for log directory
echo "Setting log directory permissions"
chown -R tim:tim /home/tim/RFID3/logs
chmod -R 750 /home/tim/RFID3/logs

echo "$(date '+%Y-%m-%d %H:%M:%S') - Samba setup completed successfully"
