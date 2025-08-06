#!/bin/bash
set -e
cd /home/tim/RFID3
/usr/bin/git fetch origin
/usr/bin/git reset --hard origin/main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart rfid_dash_dev.service

