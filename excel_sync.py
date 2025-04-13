import pandas as pd
import sqlite3
import requests
import io
from datetime import datetime
from config import DB_FILE

EXCEL_URL = "https://1drv.ms/x/c/35ee6b0cbe6f4ec9/EVSGqI3IgmhHsXQxEzgVTpsBemnqpRhD1_2_yZLyznVJ_w?e=Lwzkvh"

def sync_excel_to_db():
    print(f"Syncing cloud Excel to {DB_FILE} at {datetime.now()}")
    try:
        # Download Excel from OneDrive
        response = requests.get(EXCEL_URL, stream=True)
        if response.status_code != 200:
            raise Exception(f"Failed to download Excel: {response.status_code}")
        
        # Read Excel from stream
        xl = pd.ExcelFile(io.BytesIO(response.content))
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        for sheet_name in xl.sheet_names:
            if sheet_name.lower() == 'map':
                continue
            df = pd.read_excel(xl, sheet_name=sheet_name)
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
        print("Cloud Excel sync completed.")
    except Exception as e:
        print(f"Error syncing cloud Excel: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    sync_excel_to_db()