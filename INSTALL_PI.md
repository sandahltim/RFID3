# Installing RFID Dashboard on a New Raspberry Pi

These steps install the project under `/home/tim/RFID3`, run Gunicorn on port **8102**, and expose Nginx on port **8101** for the user interface. The installation includes automatic daily updates from the main GitHub branch, proper database setup with all required tables, and systemd service configuration for auto-restart on boot.

## 1. Prepare the Pi
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3 python3-venv python3-pip mariadb-server mariadb-client redis-server
```

If package installation fails with a message about `/boot/firmware`, mount the boot partition and retry:
```bash
sudo mount /boot/firmware
sudo dpkg --configure -a
```

## 2. Clone the repository
```bash
mkdir -p /home/tim/RFID3
cd /home/tim/RFID3
git clone https://github.com/sandahltim/_rfidpi.git .   # note the final dot
git checkout main  # Use main branch for standard installations
```

## 3. Python environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Configure MariaDB and seed data
The application uses MariaDB for its database. The enhanced setup script will install MariaDB, create the database, and load all required schemas automatically:
```bash
chmod +x scripts/setup_mariadb.sh
sudo scripts/setup_mariadb.sh

# Initialize rental class mappings
source venv/bin/activate
python scripts/update_rental_class_mappings.py
```

## 5. Set up shared folder for CSV tag file
The Service tab expects to read and write tag CSV files in a shared directory. Run the Samba setup script to
create `/home/tim/RFID3/shared` and expose it on the network as `RFIDShare` so you can drop CSV files from another machine.
```bash
chmod +x scripts/setup_samba.sh
sudo scripts/setup_samba.sh
```

## 6. Enable the systemd service

```bash
sudo cp rfid_dash_dev.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable rfid_dash_dev.service
sudo systemctl start rfid_dash_dev.service
```

The dashboard is now available at `http://<pi-ip>:8102` directly through Gunicorn, or at `http://<pi-ip>:8101` if using Nginx proxy.

## 7. Set up automatic daily updates

Install the auto-update system that checks for GitHub updates daily:
```bash
# Make auto-update script executable
chmod +x scripts/auto_update.sh

# Install systemd timer and service for daily updates
sudo cp scripts/rfid-auto-update.service /etc/systemd/system/
sudo cp scripts/rfid-auto-update.timer /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start the timer (runs daily)
sudo systemctl enable rfid-auto-update.timer
sudo systemctl start rfid-auto-update.timer

# Check timer status
sudo systemctl status rfid-auto-update.timer
```


## 8. Optional: Nginx proxy
If you want to use Nginx, copy `rfid_dash_dev.conf` to `/etc/nginx/sites-available/` and enable it so Nginx listens on port 8101 and forwards traffic to Gunicorn on port 8102.

## 9. Manual update

To update manually at any time:
```bash
sudo /home/tim/RFID3/scripts/auto_update.sh
```

## 10. Monitoring auto-updates

Check auto-update logs:
```bash
# View recent auto-update activity
tail -f /home/tim/RFID3/logs/auto_update.log

# Check when the timer last ran and when it's scheduled to run next
sudo systemctl list-timers rfid-auto-update.timer

# View the timer journal logs
journalctl -u rfid-auto-update.timer -f
```

## 11. Logs


Application logs are in `/home/tim/RFID3/logs/`.

---
These instructions assume the `tim` user. Adjust paths if you use a different user.

