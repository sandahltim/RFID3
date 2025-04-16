#!/bin/bash
source /home/tim/test_rfidpi/venv/bin/activate
/usr/bin/pkill -f gunicorn
sleep 2
# Ensure port is free
if sudo netstat -tulnp 2>/dev/null | grep -q ":7409 "; then
    echo "Port 7409 still in use, killing..."
    sudo kill -9 $(sudo lsof -t -i:7409) 2>/dev/null
    sleep 1
fi
exec gunicorn --workers 1 --bind 0.0.0.0:7409 --timeout 120 run:app --access-logfile /var/log/gunicorn/access.log --error-logfile /var/log/gunicorn/error.log --log-level debug