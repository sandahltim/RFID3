#!/bin/bash
# Setup MariaDB on Raspberry Pi 4 with Bookworm

# Update and install MariaDB
sudo apt update
sudo apt install -y mariadb-server mariadb-client redis-server

# Start and enable services
sudo systemctl start mariadb
sudo systemctl enable mariadb
sudo systemctl start redis
sudo systemctl enable redis

# Secure MariaDB installation
sudo mysql_secure_installation <<EOF

y
rfid_root_password
rfid_root_password
y
y
y
y
EOF

# Create database and user
sudo mysql -u root -prfid_root_password <<EOF
CREATE DATABASE rfid_inventory;
CREATE USER 'rfid_user'@'localhost' IDENTIFIED BY 'rfid_user_password';
GRANT ALL PRIVILEGES ON rfid_inventory.* TO 'rfid_user'@'localhost';
FLUSH PRIVILEGES;
EOF

# Set permissions
sudo chown -R mysql:mysql /var/lib/mysql
sudo chmod -R 750 /var/lib/mysql
sudo chown mysql:mysql /var/log/mysql/error.log
sudo chmod 640 /var/log/mysql/error.log
sudo usermod -aG mysql tim

# Create logs directory
sudo mkdir -p /home/tim/test_rfidpi/logs
sudo chown tim:tim /home/tim/test_rfidpi/logs
sudo chmod 750 /home/tim/test_rfidpi/logs