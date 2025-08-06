import sqlite3
import sys
from pathlib import Path


def table_exists(cur, name: str) -> bool:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None


def create_indexes(db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    if table_exists(cur, "id_item_master"):
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_item_master_rental_class_num ON id_item_master (rental_class_num)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_item_master_status ON id_item_master (status)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_item_master_bin_location ON id_item_master (bin_location)"
        )
    else:
        print("Skipping ItemMaster indexes; table id_item_master not found")

    if table_exists(cur, "id_rfidtag"):
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_rfidtag_rental_class_num ON id_rfidtag (rental_class_num)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_rfidtag_status ON id_rfidtag (status)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_rfidtag_bin_location ON id_rfidtag (bin_location)"
        )
    else:
        print("Skipping RFIDTag indexes; table id_rfidtag not found")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else "rfid_inventory.db"
    if not Path(db_file).exists():
        print(f"Database '{db_file}' does not exist; creating empty file")
    create_indexes(db_file)
