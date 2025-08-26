#!/bin/bash
# Setup MariaDB and Redis on Raspberry Pi with Bookworm
# Enhanced version that includes database schema creation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Starting MariaDB and Redis setup..."
echo "Script directory: $SCRIPT_DIR"
echo "Project directory: $PROJECT_DIR"

# Update and install MariaDB and Redis
echo "Installing MariaDB and Redis..."
sudo apt update
sudo apt install -y mariadb-server mariadb-client redis-server

# Start and enable services
echo "Starting and enabling services..."
sudo systemctl start mariadb
sudo systemctl enable mariadb
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Secure MariaDB installation
echo "Securing MariaDB installation..."
sudo mysql_secure_installation <<'EOS'

n
rfid_root_password
rfid_root_password
n
y
y
y
y
EOS

# Check if rfid_inventory database exists, create if not with proper charset/collation
echo "Creating database and user..."
sudo mysql -u root -prfid_root_password -e "CREATE DATABASE IF NOT EXISTS rfid_inventory CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Create or update user and privileges
sudo mysql -u root -prfid_root_password <<'EOS'
CREATE USER IF NOT EXISTS 'rfid_user'@'localhost' IDENTIFIED BY 'rfid_user_password';
GRANT ALL PRIVILEGES ON rfid_inventory.* TO 'rfid_user'@'localhost';
FLUSH PRIVILEGES;
EOS

# Apply database migrations
echo "Applying database schema..."
if [ -f "$SCRIPT_DIR/migrate_db.sql" ]; then
    echo "Running main database migration..."
    mysql -u rfid_user -prfid_user_password rfid_inventory < "$SCRIPT_DIR/migrate_db.sql"
else
    echo "Warning: migrate_db.sql not found at $SCRIPT_DIR/migrate_db.sql"
fi

if [ -f "$SCRIPT_DIR/migrate_hand_counted_items.sql" ]; then
    echo "Running hand counted items migration..."
    mysql -u rfid_user -prfid_user_password rfid_inventory < "$SCRIPT_DIR/migrate_hand_counted_items.sql"
else
    echo "Warning: migrate_hand_counted_items.sql not found at $SCRIPT_DIR/migrate_hand_counted_items.sql"
fi

# Set permissions for MariaDB
sudo chown -R mysql:mysql /var/lib/mysql
sudo chmod -R 750 /var/lib/mysql

# Create and set permissions for MariaDB log file
sudo mkdir -p /var/log/mysql
sudo touch /var/log/mysql/error.log
sudo chown mysql:mysql /var/log/mysql/error.log
sudo chmod 640 /var/log/mysql/error.log

# Add user tim to mysql group
sudo usermod -aG mysql tim

# Create logs and backup directories for app
echo "Creating application directories..."
sudo mkdir -p "$PROJECT_DIR/logs"
sudo mkdir -p "$PROJECT_DIR/backups"
sudo chown -R tim:tim "$PROJECT_DIR/logs"
sudo chown -R tim:tim "$PROJECT_DIR/backups"
sudo chmod 750 "$PROJECT_DIR/logs"
sudo chmod 750 "$PROJECT_DIR/backups"

# Test database connection
echo "Testing database connection..."
if mysql -u rfid_user -prfid_user_password -e "USE rfid_inventory; SHOW TABLES;" > /dev/null 2>&1; then
    echo "Database setup completed successfully!"
    mysql -u rfid_user -prfid_user_password -e "USE rfid_inventory; SHOW TABLES;"
else
    echo "Error: Database connection test failed!"
    exit 1
fi

echo "MariaDB and Redis setup complete!"

