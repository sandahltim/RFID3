import os
import logging
import time
from db_utils import initialize_db
from refresh_logic import refresh_data
from app import create_app
from werkzeug.serving import is_running_from_reloader
from config import DB_FILE

# Initialize Flask app globally for Gunicorn
app = create_app()

# Initialize database if it doesn't exist
db_path = os.path.join(os.path.dirname(__file__), "inventory.db")
if not os.path.exists(db_path):
    print("Creating new database...")
    initialize_db()  # Create fresh schema
    os.chmod(db_path, 0o664)  # Set read/write for owner and group
    os.chown(db_path, os.getuid(), os.getgid())  # Set owner to tim
    print(f"Initialized database: {db_path}")
else:
    print(f"Using existing database: {db_path}")

# Perform single refresh on startup, no threads
if not is_running_from_reloader():
    print("Performing initial full API refresh...")
    try:
        time.sleep(5)  # Wait for Gunicorn to stabilize
        refresh_data(full_refresh=True)
        print("Initial full refresh complete")
    except Exception as e:
        logging.error(f"Initial refresh failed: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("Starting Flask application...")
    try:
        app.run(host="0.0.0.0", port=7409, debug=True)
    except Exception as e:
        logging.error(f"Flask failed to start: {e}")