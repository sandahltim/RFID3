# Check if it uses sudo; if so, modify to run as tim
# Example start.sh:
#!/bin/bash
source /home/tim/test_rfidpi/venv/bin/activate
gunicorn --workers 2 --bind 0.0.0.0:7409 run:app --access-logfile /var/log/gunicorn/access.log --error-logfile /var/log/gunicorn/error.log --log-level debug
