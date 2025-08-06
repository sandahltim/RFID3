#!/bin/bash
source /home/tim/RFID3/venv/bin/activate
exec gunicorn --workers 3 --timeout 300 --bind 127.0.0.1:8102 --chdir /home/tim/RFID3 run:app

