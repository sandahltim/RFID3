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

# Force full database reload on every restart
db_path = os.path.join(os.path.dirname(__file__), "inventory.db")
print("Forcing full database reload on restart...")
if os.path.exists(db_path):
    os.remove(db_path)  # Delete existing inventory.db
    print(f"Removed existing database: {db_path}")
initialize_db()  # Create fresh schema
os.chmod(db_path, 0o664)  # Set read/write for owner and group
os.chown(db_path, os.getuid(), os.getgid())  # Set owner to current user (tim)
# Verify write access
try:
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER)")
        conn.execute("INSERT INTO test (id) VALUES (1)")
    print("Database write access confirmed")
except sqlite3.OperationalError as e:
    print(f"ERROR: Database not writable: {e}")
    raise

# Perform full refresh
refresh_data(full_refresh=True)  # Full API refresh

# Start background refresh thread only in primary process
if not is_running_from_reloader():
    refresher_thread = threading.Thread(target=background_refresh, daemon=True)
    refresher_thread.start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("Starting Flask application...")
    try:
        app.run(host="0.0.0.0", port=7409, debug=True)
    except Exception as e:
        logging.error(f"Flask failed to start: {e}")