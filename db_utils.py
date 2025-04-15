import sqlite3
import os
import sys
from config import DB_FILE

def initialize_db():
    print(f"Trying to create database at {DB_FILE}")
    print(f"User: {os.getuid()}:{os.getgid()}")
    print(f"Directory permissions: {os.stat(os.path.dirname(DB_FILE)).st_mode & 0o777}")
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        print("Connected to SQLite")

        # id_item_master
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS id_item_master (
                tag_id TEXT PRIMARY KEY,
                uuid_accounts_fk TEXT,
                serial_number TEXT,
                client_name TEXT,
                rental_class_num TEXT,
                common_name TEXT,
                quality TEXT,
                bin_location TEXT,
                status TEXT,
                last_contract_num TEXT,
                last_scanned_by TEXT,
                notes TEXT,
                status_notes TEXT,
                long TEXT,
                lat TEXT,
                date_last_scanned TEXT,
                date_created TEXT,
                date_updated TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_contract ON id_item_master (last_contract_num)")
        print("Created id_item_master table")

        # id_transactions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS id_transactions (
                contract_number TEXT,
                client_name TEXT,
                tag_id TEXT,
                common_name TEXT,
                bin_location TEXT,
                scan_type TEXT,
                status TEXT,
                scan_date TEXT,
                scan_by TEXT,
                location_of_repair TEXT,
                quality TEXT,
                dirty_or_mud TEXT,
                leaves TEXT,
                oil TEXT,
                mold TEXT,
                stain TEXT,
                oxidation TEXT,
                other TEXT,
                rip_or_tear TEXT,
                sewing_repair_needed TEXT,
                grommet TEXT,
                rope TEXT,
                buckle TEXT,
                date_created TEXT,
                date_updated TEXT,
                uuid_accounts_fk TEXT,
                serial_number TEXT,
                rental_class_num TEXT,
                long TEXT,
                lat TEXT,
                wet TEXT,
                service_required TEXT,
                notes TEXT,
                PRIMARY KEY (contract_number, tag_id, scan_type, scan_date)
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_date ON id_transactions (client_name, scan_date)")
        print("Created id_transactions table")

        # seed_rental_classes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seed_rental_classes (
                rental_class_id TEXT PRIMARY KEY,
                common_name TEXT,
                bin_location TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_common_name ON seed_rental_classes (common_name)")
        print("Created seed_rental_classes table")

        # id_rfidtag
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS id_rfidtag (
                tag_id TEXT PRIMARY KEY,
                common_name TEXT,
                category TEXT,
                status TEXT,
                item_type TEXT,
                last_contract_num TEXT,
                date_assigned TEXT,
                date_sold TEXT,
                date_discarded TEXT,
                reuse_count INTEGER,
                last_updated TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rfidtag_status ON id_rfidtag (status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rfidtag_category ON id_rfidtag (category)")
        print("Created id_rfidtag table")

        conn.commit()
        print("Changes committed")
        conn.close()
        print(f"Database initialized at {DB_FILE}")
    except sqlite3.OperationalError as e:
        print(f"SQLite error: {e}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        raise

if __name__ == "__main__":
    initialize_db()