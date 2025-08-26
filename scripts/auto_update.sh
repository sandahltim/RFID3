#!/bin/bash
# auto_update.sh - Daily auto-update script for RFID3 application
# This script checks for updates from GitHub repo and applies them if found
# Created: 2025-08-25

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="$PROJECT_DIR"
LOG_DIR="$INSTALL_DIR/logs"
LOG_FILE="$LOG_DIR/auto_update.log"
SERVICE_NAME="rfid_dash_dev.service"
REPO_URL="https://github.com/sandahltim/_rfidpi.git"
BRANCH="main"
USER="tim"

# Ensure log directory exists
mkdir -p "$LOG_DIR"
chown $USER:$USER "$LOG_DIR"

# Logging function
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Function to check if we're running as the correct user
check_user() {
    if [[ $USER != "tim" && $EUID -ne 0 ]]; then
        log_message "ERROR: Script must be run as user 'tim' or root"
        exit 1
    fi
}

# Function to backup current state
backup_current() {
    local backup_dir="$INSTALL_DIR/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup key files
    cp -r "$INSTALL_DIR/app" "$backup_dir/" 2>/dev/null || true
    cp -r "$INSTALL_DIR/scripts" "$backup_dir/" 2>/dev/null || true
    cp -r "$INSTALL_DIR/static" "$backup_dir/" 2>/dev/null || true
    cp "$INSTALL_DIR"/*.py "$backup_dir/" 2>/dev/null || true
    cp "$INSTALL_DIR"/*.service "$backup_dir/" 2>/dev/null || true
    cp "$INSTALL_DIR/requirements.txt" "$backup_dir/" 2>/dev/null || true
    
    log_message "Backup created at $backup_dir"
    
    # Keep only last 5 backups
    find "$INSTALL_DIR/backups" -maxdepth 1 -type d -name "20*" | sort | head -n -5 | xargs rm -rf
}

# Function to check for updates
check_for_updates() {
    cd "$INSTALL_DIR"
    
    # Fetch latest changes
    git fetch origin "$BRANCH" 2>&1 | tee -a "$LOG_FILE"
    
    # Check if there are any differences
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse "origin/$BRANCH")
    
    if [[ "$LOCAL" != "$REMOTE" ]]; then
        log_message "Updates available. Local: $LOCAL, Remote: $REMOTE"
        return 0
    else
        log_message "No updates available. Already up to date."
        return 1
    fi
}

# Function to apply updates
apply_updates() {
    cd "$INSTALL_DIR"
    
    log_message "Starting update process..."
    
    # Create backup before updating
    backup_current
    
    # Stop the service
    log_message "Stopping $SERVICE_NAME..."
    systemctl stop "$SERVICE_NAME" 2>&1 | tee -a "$LOG_FILE"
    
    # Pull latest changes
    log_message "Pulling latest changes from $BRANCH branch..."
    git pull origin "$BRANCH" 2>&1 | tee -a "$LOG_FILE"
    
    if [[ $? -ne 0 ]]; then
        log_message "ERROR: Git pull failed"
        systemctl start "$SERVICE_NAME"
        return 1
    fi
    
    # Update Python dependencies
    log_message "Updating Python dependencies..."
    source venv/bin/activate
    pip install --upgrade pip 2>&1 | tee -a "$LOG_FILE"
    pip install -r requirements.txt 2>&1 | tee -a "$LOG_FILE"
    
    # Run database migrations if needed
    log_message "Running database migrations..."
    mysql -u rfid_user -prfid_user_password rfid_inventory < scripts/migrate_hand_counted_items.sql 2>&1 | tee -a "$LOG_FILE" || true
    
    # Update systemd service file if changed
    if [[ -f "$INSTALL_DIR/rfid_dash_dev.service" ]]; then
        if ! cmp -s "$INSTALL_DIR/rfid_dash_dev.service" "/etc/systemd/system/rfid_dash_dev.service"; then
            log_message "Updating systemd service file..."
            cp "$INSTALL_DIR/rfid_dash_dev.service" "/etc/systemd/system/"
            systemctl daemon-reload
        fi
    fi
    
    # Clear old logs to prevent disk space issues
    find "$LOG_DIR" -name "*.log" -type f -mtime +30 -delete 2>/dev/null || true
    
    # Start the service
    log_message "Starting $SERVICE_NAME..."
    systemctl start "$SERVICE_NAME" 2>&1 | tee -a "$LOG_FILE"
    
    # Check if service started successfully
    sleep 5
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_message "Update completed successfully. Service is running."
        return 0
    else
        log_message "ERROR: Service failed to start after update"
        return 1
    fi
}

# Function to send notification (optional - can be extended)
send_notification() {
    local message="$1"
    log_message "NOTIFICATION: $message"
    # Could add email, webhook, or other notification methods here
}

# Main execution
main() {
    log_message "Starting daily auto-update check..."
    
    check_user
    
    # Change to install directory
    if [[ ! -d "$INSTALL_DIR" ]]; then
        log_message "ERROR: Install directory $INSTALL_DIR not found"
        exit 1
    fi
    
    cd "$INSTALL_DIR"
    
    # Check if it's a git repository
    if [[ ! -d ".git" ]]; then
        log_message "ERROR: $INSTALL_DIR is not a git repository"
        exit 1
    fi
    
    # Check for updates
    if check_for_updates; then
        log_message "Updates found, applying..."
        if apply_updates; then
            send_notification "RFID3 application updated successfully"
        else
            send_notification "RFID3 application update failed"
            exit 1
        fi
    else
        log_message "No updates needed"
    fi
    
    log_message "Auto-update check completed"
}

# Run main function
main "$@"