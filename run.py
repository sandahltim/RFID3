import os
import logging
import time
import threading
from db_utils import initialize_db
from refresh_logic import refresh_data, background_refresh
from app import create_app
from werkzeug.serving import is_running_from_reloader
from config import DB_FILE
from db_connection import DatabaseConnection

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

# Start background refresh thread only in primary process
if not is_running_from_reloader():
    # Delay full refresh to avoid concurrent database access
    def delayed_refresh():
        time.sleep(5)  # Wait for Gunicorn workers to stabilize
        print("Performing full API refresh...")
        refresh_data(full_refresh=True)
        print("Full refresh complete")

    refresher_thread = threading.Thread(target=background_refresh, daemon=True)
    refresher_thread.start()
    # Run full refresh in a separate thread after delay
    threading.Thread(target=delayed_refresh, daemon=True).start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("Starting Flask application...")
    try:
        app.run(host="0.0.0.0", port=7409, debug=True)
    except Exception as e:
        logging.error(f"Flask failed to start: {e}")