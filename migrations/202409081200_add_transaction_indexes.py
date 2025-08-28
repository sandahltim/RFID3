import sqlite3
import sys
from pathlib import Path


def table_exists(cur, name: str) -> bool:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None


def create_indexes(db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    if table_exists(cur, "id_transactions"):
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_transactions_tag_id ON id_transactions (tag_id)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_transactions_scan_date ON id_transactions (scan_date)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS ix_transactions_status ON id_transactions (status)"
        )
    else:
        print("Skipping Transaction indexes; table id_transactions not found")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else "rfid_inventory.db"
    if not Path(db_file).exists():
        print(f"Database '{db_file}' does not exist; creating empty file")
    create_indexes(db_file)

