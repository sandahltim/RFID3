#!/bin/bash
source /home/tim/test_rfidpi/venv/bin/activate
# Kill all Gunicorn processes aggressively
sudo /usr/bin/pkill -9 -f gunicorn 2>/dev/null
sleep 2
# Double-check with lsof and netstat
for i in {1..3}; do
    if sudo netstat -tulnp 2>/dev/null | grep -q ":7409 "; then
        echo "Port 7409 still in use, attempt $i to kill..."
        PIDS=$(sudo lsof -t -i:7409 2>/dev/null)
        if [ -n "$PIDS" ]; then
            sudo kill -9 $PIDS 2>/dev/null
        fi
        sleep 1
    else
        echo "Port 7409 is free"
        break
    fi
done
# Ensure port is free
if sudo netstat -tulnp 2>/dev/null | grep -q ":7409 "; then
    echo "Failed to free port 7409, exiting..."
    exit 1
fi
exec gunicorn --workers 1 --bind 0.0.0.0:7409 --timeout 120 run:app --access-logfile /var/log/gunicorn/access.log --error-logfile /var/log/gunicorn/error.log --log-level debug