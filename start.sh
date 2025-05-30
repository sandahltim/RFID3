#!/bin/bash
source /home/tim/test_rfidpi/venv/bin/activate
exec gunicorn --workers 3 --timeout 300 --bind 127.0.0.1:3607 --chdir /home/tim/test_rfidpi run:app