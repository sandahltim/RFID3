#!/bin/bash
source venv/bin/activate
pkill -f gunicorn
sleep 1
gunicorn --workers 1 --bind 0.0.0.0:7409 --timeout 120 run:app --access-logfile /var/log/gunicorn/access.log --error-logfile /var/log/gunicorn/error.log --log-level debug