import os
import logging
import time
from db_utils import initialize_db
from refresh_logic import refresh_data
from app import create_app
from werkzeug.serving import is_running_from_reloader
from config import DB_FILE

# Initialize logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize Flask app globally for Gunicorn
app = create_app()

# Check and fix DB permissions
def ensure_db_permissions(db_path):
    try:
        if os.path.exists(db_path):
            os.chmod(db_path, 0o664)
            os.chown(db_path, os.getuid(), os.getgid())
            logging.info(f"Set permissions for {db_path}")
        else:
            open(db_path, 'a').close()  # Create empty file
            os.chmod(db_path, 0o664)
            os.chown(db_path, os.getuid(), os.getgid())
            logging.info(f"Created and set permissions for {db_path}")
    except Exception as e:
        logging.error(f"Failed to set permissions for {db_path}: {e}")
        raise

# Initialize databases
db_path = os.path.join(os.path.dirname(__file__), "inventory.db")
hand_counted_db = os.path.join(os.path.dirname(__file__), "tab5_hand_counted.db")

# Ensure permissions for inventory.db
if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
    logging.info("Creating new inventory database...")
    ensure_db_permissions(db_path)
    initialize_db()  # Create fresh schema
    logging.info(f"Initialized database: {db_path}")
else:
    ensure_db_permissions(db_path)
    logging.info(f"Using existing database: {db_path}")

# Ensure permissions for tab5_hand_counted.db
if not os.path.exists(hand_counted_db):
    logging.info("Creating new hand-counted database...")
    ensure_db_permissions(hand_counted_db)
    with sqlite3.connect(hand_counted_db) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hand_counted_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                last_contract_num TEXT,
                common_name TEXT,
                total_items INTEGER,
                tag_id TEXT DEFAULT NULL,
                date_last_scanned TEXT,
                last_scanned_by TEXT
            )
        """)
        conn.commit()
    logging.info(f"Initialized hand-counted database: {hand_counted_db}")
else:
    ensure_db_permissions(hand_counted_db)
    logging.info(f"Using existing hand-counted database: {hand_counted_db}")

# Perform single refresh on startup, no threads
if not is_running_from_reloader():
    logging.info("Performing initial full API refresh...")
    try:
        time.sleep(5)  # Wait for Gunicorn to stabilize
        refresh_data(full_refresh=True)
        logging.info("Initial full refresh complete")
    except Exception as e:
        logging.error(f"Initial refresh failed: {e}")

if __name__ == "__main__":
    logging.info("Starting Flask application...")
    try:
        app.run(host="0.0.0.0", port=7409, debug=True)
    except Exception as e:
        logging.error(f"Flask failed to start: {e}")