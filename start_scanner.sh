#!/bin/bash
# start_scanner.sh
# Startup script for RFID Mobile Scanner App
# Version: 2025-09-13-v1

# Set working directory
cd /home/tim/RFID3

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export FLASK_APP=scanner_app.py
export FLASK_ENV=production
export DB_PASSWORD=${DB_PASSWORD:-"your_secure_password"}

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the scanner application
echo "Starting RFID Mobile Scanner App on port 8444..."
echo "Employee Interface: https://127.0.0.1:8444"
echo "Supervisor Dashboard: https://127.0.0.1:8443"
echo ""
echo "Press Ctrl+C to stop the scanner app"

python scanner_app.py