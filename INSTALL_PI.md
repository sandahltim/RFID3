# Installing RFID Dashboard on a New Raspberry Pi

These steps install the project under `/home/tim/RFID3`, run Gunicorn on port **8102**, and expose Nginx on port **8101** for the user interface while configuring automatic updates via Tailscale and GitHub Actions.

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
git clone https://github.com/SMOK33Y3/BTErfid.git .   # note the final dot



```

## 3. Python environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 4. Configure MariaDB and seed data
The application uses MariaDB for its database. Run the helper script to install and secure MariaDB, create the database, and load the schema:
```bash
chmod +x scripts/setup_mariadb.sh
sudo scripts/setup_mariadb.sh
mysql -u rfid_user -prfid_user_password rfid_inventory < scripts/migrate_db.sql
mysql -u rfid_user -prfid_user_password rfid_inventory < scripts/migrate_hand_counted_items.sql

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

The dashboard is now available at `http://<pi-ip>:8101` through Nginx, which proxies to Gunicorn on port 8102.


## 7. Optional: Nginx proxy
If you use Nginx, copy `rfid_dash_dev.conf` to `/etc/nginx/sites-available/` and enable it so Nginx listens on port 8101 and forwards traffic to Gunicorn on port 8102.

## 8. Automatic updates via Tailscale

1. Install Tailscale on the Pi and bring it up:
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo systemctl enable --now tailscaled
sudo tailscale up --ssh
```
2. Ensure repository secrets `TAILSCALE_AUTHKEY` and `PI_TAILSCALE_IP` are set in GitHub.
3. The workflow `.github/workflows/deploy.yml` connects through Tailscale and runs `update_from_github.sh` on merges to `main`.


## 9. Manual update

To update manually:
```bash
/home/tim/RFID3/update_from_github.sh
```


## 10. Logs


Application logs are in `/home/tim/RFID3/logs/`.

---
These instructions assume the `tim` user. Adjust paths if you use a different user.

