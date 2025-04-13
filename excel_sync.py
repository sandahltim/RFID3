import pandas as pd
import sqlite3
from datetime import datetime
from config import DB_FILE

EXCEL_FILE = "/home/tim/test_rfidpi/data/tags.xlsx"

def sync_excel_to_db():
    print(f"Syncing {EXCEL_FILE} to {DB_FILE} at {datetime.now()}")
    try:
        xl = pd.ExcelFile(EXCEL_FILE)
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        for sheet_name in xl.sheet_names:
            if sheet_name.lower() == 'map':
                continue
            df = pd.read_excel(EXCEL_FILE, sheet_name=sheet_name)
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT OR REPLACE INTO id_rfidtag (
                        tag_id, common_name, category, status, item_type,
                        last_contract_num, date_assigned, date_sold, date_discarded,
                        reuse_count, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(row['EPC']), str(row['Common_Name']), str(row['Category']),
                    'active', 'resale' if sheet_name.lower() == 'resale' else 'rental',
                    None, None, None, None, 0,
                    datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                ))

        conn.commit()
        print("Excel sync completed.")
    except Exception as e:
        print(f"Error syncing Excel: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    sync_excel_to_db()