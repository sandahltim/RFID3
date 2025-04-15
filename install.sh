#!/bin/bash
echo "Setting up RFID Dashboard on Pi..."
sudo apt update && sudo apt install python3.11 -y || { echo "Python install failed"; exit 1; }
python3.11 -m venv venv || { echo "Venv creation failed"; exit 1; }
source venv/bin/activate
pip install flask==2.3.2 gunicorn==20.1.0 pandas==2.0.3 requests==2.31.0 || { echo "Pip install failed"; exit 1; }
sudo cp rfid_dash_dev.service /etc/systemd/system/ || { echo "Systemd copy failed"; exit 1; }
sudo systemctl daemon-reload
sudo systemctl enable rfid_dash_dev || { echo "Systemd enable failed"; exit 1; }

# Initialize DB with correct permissions
echo "Setting up databases..."
DB_DIR="/home/tim/test_rfidpi"
DB_FILE="$DB_DIR/inventory.db"
HAND_COUNTED_DB="$DB_DIR/tab5_hand_counted.db"

# Ensure directory permissions
sudo chown tim:tim "$DB_DIR"
sudo chmod 775 "$DB_DIR"

# Create inventory.db
if [ ! -f "$DB_FILE" ]; then
    touch "$DB_FILE"
    chown tim:tim "$DB_FILE"
    chmod 664 "$DB_FILE"
    python3 db_utils.py  # Initialize schema
    echo "Created and initialized inventory.db"
else
    chown tim:tim "$DB_FILE"
    chmod 664 "$DB_FILE"
    echo "Set permissions for existing inventory.db"
fi

# Create tab5_hand_counted.db
if [ ! -f "$HAND_COUNTED_DB" ]; then
    touch "$HAND_COUNTED_DB"
    chown tim:tim "$HAND_COUNTED_DB"
    chmod 664 "$HAND_COUNTED_DB"
    python3 -c "import sqlite3; conn = sqlite3.connect('$HAND_COUNTED_DB'); cursor = conn.cursor(); cursor.execute('CREATE TABLE IF NOT EXISTS hand_counted_items (id INTEGER PRIMARY KEY AUTOINCREMENT, last_contract_num TEXT, common_name TEXT, total_items INTEGER, tag_id TEXT DEFAULT NULL, date_last_scanned TEXT, last_scanned_by TEXT)'); conn.commit(); conn.close()"
    echo "Created and initialized tab5_hand_counted.db"
else
    chown tim:tim "$HAND_COUNTED_DB"
    chmod 664 "$HAND_COUNTED_DB"
    echo "Set permissions for existing tab5_hand_counted.db"
fi

echo "Install complete! Reboot to start or run ./start.sh."