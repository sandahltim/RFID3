import pandas as pd
import sqlite3
import requests
import io
from datetime import datetime
from config import DB_FILE
import time
import logging

logging.basicConfig(level=logging.DEBUG)

EXCEL_URL = "https://1drv.ms/x/c/35ee6b0cbe6f4ec9/EVSGqI3IgmhHsXQxEzgVTpsBemnqpRhD1_2_yZLyznVJ_w?e=sKg2qD"

def sync_excel_to_db():
    logging.debug(f"Syncing cloud Excel to {DB_FILE} at {datetime.now()}")
    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            # Download Excel from OneDrive
            response = requests.get(EXCEL_URL, stream=True, timeout=30)
            response.raise_for_status()
            
            # Read Excel from stream
            xl = pd.ExcelFile(io.BytesIO(response.content))
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()

            for sheet_name in xl.sheet_names:
                if sheet_name.lower() == 'map':
                    logging.debug(f"Skipping sheet: {sheet_name}")
                    continue
                logging.debug(f"Processing sheet: {sheet_name}")
                df = pd.read_excel(xl, sheet_name=sheet_name)
                for index, row in df.iterrows():
                    try:
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
                        logging.debug(f"Inserted/Updated tag: {row['EPC']}")
                    except Exception as e:
                        logging.error(f"Error inserting tag {row.get('EPC', 'unknown')}: {e}")

            conn.commit()
            logging.debug("Cloud Excel sync completed.")
            break
        except Exception as e:
            logging.error(f"Error syncing cloud Excel (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                if 'conn' in locals():
                    conn.rollback()
        finally:
            if 'conn' in locals():
                conn.close()

if __name__ == "__main__":
    sync_excel_to_db()