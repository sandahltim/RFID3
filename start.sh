#!/bin/bash
source /home/tim/test_rfidpi/venv/bin/activate
# Log and kill all Gunicorn processes
echo "Killing Gunicorn processes..." >> /var/log/gunicorn/start.log
sudo /usr/bin/pkill -9 -f gunicorn 2>/dev/null
sleep 2
# Check port 7409 and log what's using it
for i in {1..5}; do
    if sudo netstat -tulnp 2>/dev/null | grep -q ":7409 "; then
        echo "Port 7409 in use, attempt $i to kill..." >> /var/log/gunicorn/start.log
        PIDS=$(sudo lsof -t -i:7409 2>/dev/null)
        if [ -n "$PIDS" ]; then
            echo "Found PIDs on 7409: $PIDS" >> /var/log/gunicorn/start.log
            sudo kill -9 $PIDS 2>/dev/null
        else
            echo "No PIDs found, but port still in use" >> /var/log/gunicorn/start.log
        fi
        sleep 1
    else
        echo "Port 7409 is free after attempt $i" >> /var/log/gunicorn/start.log
        break
    fi
done
# Final check
if sudo netstat -tulnp 2>/dev/null | grep -q ":7409 "; then
    echo "Failed to free port 7409, exiting..." >> /var/log/gunicorn/start.log
    exit 1
fi
echo "Starting Gunicorn..." >> /var/log/gunicorn/start.log
exec gunicorn --workers 1 --bind 0.0.0.0:7409 --timeout 120 run:app --access-logfile /var/log/gunicorn/access.log --error-logfile /var/log/gunicorn/error.log --log-level debug