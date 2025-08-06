#!/bin/bash
# Setup MariaDB and Redis on Raspberry Pi with Bookworm

# Update and install MariaDB and Redis
sudo apt update
sudo apt install -y mariadb-server mariadb-client redis-server

# Start and enable services
sudo systemctl start mariadb
sudo systemctl enable mariadb
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Secure MariaDB installation
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
sudo mysql -u root -prfid_root_password -e "CREATE DATABASE IF NOT EXISTS rfid_inventory CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Create or update user and privileges
sudo mysql -u root -prfid_root_password <<'EOS'
CREATE USER IF NOT EXISTS 'rfid_user'@'localhost' IDENTIFIED BY 'rfid_user_password';
GRANT ALL PRIVILEGES ON rfid_inventory.* TO 'rfid_user'@'localhost';
FLUSH PRIVILEGES;
EOS

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

# Create logs directory for app
sudo mkdir -p /home/tim/RFID3/logs
sudo chown tim:tim /home/tim/RFID3/logs
sudo chmod 750 /home/tim/RFID3/logs

