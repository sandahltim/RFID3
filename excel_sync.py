import pandas as pd
import sqlite3
import requests
import io
from datetime import datetime
from config import DB_FILE
import time
import logging
import os

# Configure logging to write to sync.log
LOG_FILE = "/home/tim/test_rfidpi/sync.log"
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(name)s:%(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# Updated OneDrive URL (replace with direct download link)
EXCEL_URL = "https://1drv.ms/x/c/35ee6b0cbe6f4ec9/EQI9rtWjqMVCsUJBHhh1iO0BbmpPaIOn0P5k6UVNprnrzA?e=WTVXiS&download=1"

def sync_excel_to_db():
    logging.debug(f"Syncing cloud Excel to {DB_FILE} at {datetime.now()}")
    max_retries = 3
    retry_delay = 5

    # Test URL accessibility with redirect handling
    session = requests.Session()
    try:
        logging.debug("Testing OneDrive URL accessibility")
        response = session.head(EXCEL_URL, allow_redirects=True, timeout=10)
        logging.debug(f"URL response status: {response.status_code}")
        if response.status_code != 200:
            logging.error(f"OneDrive URL inaccessible after redirects: {response.status_code}")
            return
    except Exception as e:
        logging.error(f"Error accessing OneDrive URL: {e}")
        return

    for attempt in range(max_retries):
        try:
            # Download Excel from OneDrive
            logging.debug("Downloading Excel from OneDrive")
            response = session.get(EXCEL_URL, stream=True, allow_redirects=True, timeout=30)
            response.raise_for_status()
            content_length = response.headers.get('Content-Length', 'Unknown')
            logging.debug(f"Downloaded content length: {content_length} bytes")
            
            # Read Excel from stream
            logging.debug("Reading Excel file into pandas")
            xl = pd.ExcelFile(io.BytesIO(response.content))
            logging.debug(f"Excel sheets found: {xl.sheet_names}")
            
            with DatabaseConnection() as conn:
                cursor = conn.cursor()
                rows_inserted = 0

                for sheet_name in xl.sheet_names:
                    if sheet_name.lower() == 'map':
                        logging.debug(f"Skipping sheet: {sheet_name}")
                        continue
                    logging.debug(f"Processing sheet: {sheet_name}")
                    df = pd.read_excel(xl, sheet_name=sheet_name)
                    logging.debug(f"Sheet {sheet_name} has {len(df)} rows")
                    for index, row in df.iterrows():
                        # Skip if Common_Name (Column B) is empty or NaN
                        if pd.isna(row.get('Common_Name')) or not str(row.get('Common_Name')).strip():
                            logging.debug(f"Row {index}: Skipping tag {row.get('EPC', 'unknown')}: Common_Name is empty")
                            continue
                        try:
                            epc = str(row.get('EPC', '')).strip()
                            common_name = str(row.get('Common_Name', '')).strip()
                            category = str(row.get('Category', 'Other')).strip()
                            item_type = 'resale' if 'resale' in category.lower() else 'rental'
                            logging.debug(f"Row {index}: Processing tag - EPC: {epc}, Common Name: {common_name}, Category: {category}, Item Type: {item_type}")
                            cursor.execute("""
                                INSERT OR REPLACE INTO id_rfidtag (
                                    tag_id, common_name, category, status, item_type,
                                    last_contract_num, date_assigned, date_sold, date_discarded,
                                    reuse_count, last_updated
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                epc, common_name, category, 'active', item_type,
                                None, None, None, None, 0,
                                datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                            ))
                            rows_inserted += 1
                            logging.debug(f"Row {index}: Inserted/Updated tag: {epc}")
                        except Exception as e:
                            logging.error(f"Row {index}: Error inserting tag {row.get('EPC', 'unknown')}: {e}")

                logging.debug(f"Cloud Excel sync completed. Inserted/Updated {rows_inserted} rows.")
            break
        except Exception as e:
            logging.error(f"Error syncing cloud Excel (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logging.error("All retries failed")

if __name__ == "__main__":
    sync_excel_to_db()