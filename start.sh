#!/bin/bash
source /home/tim/test_rfidpi/venv/bin/activate
exec gunicorn --workers 2 --bind 0.0.0.0:7409 --timeout 60 run:app --access-logfile /var/log/gunicorn/access.log --error-logfile /var/log/gunicorn/error.log --log-level debug