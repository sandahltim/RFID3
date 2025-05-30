#!/bin/bash
source /home/tim/test_rfidpi/venv/bin/activate
exec gunicorn --workers 3 --timeout 300 --bind 0.0.0.0:3607 --chdir /home/tim/test_rfidpi run:app