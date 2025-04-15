#!/bin/bash
echo "Setting up RFID Dashboard on Pi..."
sudo apt update && sudo apt install python3.11 -y || { echo "Python install failed"; exit 1; }
python3.11 -m venv venv || { echo "Venv creation failed"; exit 1; }
source venv/bin/activate
pip install -r requirements.txt || { echo "Pip install failed"; exit 1; }
pip install flask==2.2.5 gunicorn==23.0.0 || { echo "Pip install failed"; exit 1; }
rm -f inventory.db
./venv/bin/python3 db_utils.py || { echo "Database creation failed"; exit 1; }
if [ -f "inventory.db" ]; then
    sudo chmod 664 inventory.db
    sudo chown tim:tim inventory.db
    echo "Database created: inventory.db"
else
    echo "ERROR: Database creation failed"
    exit 1
fi
sudo cp rfid_dash.service /etc/systemd/system/ || { echo "Systemd copy failed"; exit 1; }
sudo systemctl daemon-reload
sudo systemctl enable rfid_dash || { echo "Systemd enable failed"; exit 1; }
sudo systemctl start rfid_dash || { echo "Service start failed"; exit 1; }
echo "Install complete! Access at http://$(hostname -I | awk '{print $1}'):7409"