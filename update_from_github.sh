#!/bin/bash
# update_from_github.sh
# Version: 2025-08-06-v2
# Description: Updates RFID Dashboard from GitHub main branch, installs dependencies, and restarts service
# Created: 2025-08-06
# Author: Grok 3 (assisted by xAI)
# Usage: ./update_from_github.sh

set -e  # Exit on any error

# Define project directory and log file
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$PROJECT_DIR/logs/update.log"

# Ensure log directory exists
mkdir -p "$PROJECT_DIR/logs"
touch "$LOG_FILE"
chmod 640 "$LOG_FILE"
chown tim:tim "$LOG_FILE"

# Log start time
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting update" >> "$LOG_FILE"

# Navigate to project directory
cd "$PROJECT_DIR" || { echo "Failed to cd to $PROJECT_DIR" >> "$LOG_FILE"; exit 1; }

# Stash local changes, excluding database and config files
echo "Stashing local changes" >> "$LOG_FILE"
/usr/bin/git stash push --include-untracked -- . ':!*.sql' ':!*.db' ':!config.py' ':!logs/*' >> "$LOG_FILE" 2>&1

# Fetch and reset to latest dev branch
echo "Fetching and resetting to origin/RFID3dev" >> "$LOG_FILE"
/usr/bin/git fetch origin >> "$LOG_FILE" 2>&1
/usr/bin/git reset --hard origin/RFID3dev >> "$LOG_FILE" 2>&1

# Activate virtual environment
echo "Activating virtual environment" >> "$LOG_FILE"
source venv/bin/activate || { echo "Failed to activate virtual environment" >> "$LOG_FILE"; exit 1; }

# Install dependencies
echo "Installing dependencies" >> "$LOG_FILE"
pip install -r requirements.txt >> "$LOG_FILE" 2>&1

# Restart service
echo "Restarting rfid_dash_dev.service" >> "$LOG_FILE"
sudo systemctl restart rfid_dash_dev.service >> "$LOG_FILE" 2>&1

# Log completion
echo "$(date '+%Y-%m-%d %H:%M:%S') - Update completed successfully" >> "$LOG_FILE"
