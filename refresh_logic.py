import os
import requests
import time
from datetime import datetime, timedelta
from config import LOGIN_URL, DB_FILE, SEED_URL, ITEM_MASTER_URL, TRANSACTION_URL, API_PASSWORD, API_USERNAME
import sqlite3
import logging

logging.basicConfig(level=logging.DEBUG, filename='/home/tim/test_rfidpi/sync.log')
logger = logging.getLogger(__name__)

TOKEN = None
TOKEN_EXPIRY = None
LAST_REFRESH = None
IS_RELOADING = False
REFRESH_INTERVAL = 180

DB_CONN = None

def init_db_connection():
    global DB_CONN
    if DB_CONN is None:
        DB_CONN = sqlite3.connect(DB_FILE, timeout=10)
        DB_CONN.row_factory = sqlite3.Row
        DB_CONN.execute("PRAGMA journal_mode=WAL")
        DB_CONN.execute("PRAGMA busy_timeout=5000")
        logger.debug("Initialized single DB connection with WAL mode")
    return DB_CONN

def close_db_connection():
    global DB_CONN
    if DB_CONN:
        DB_CONN.commit()
        DB_CONN.close()
        DB_CONN = None
        logger.debug("Closed single DB connection")

def init_refresh_state():
    global LAST_REFRESH
    logger.debug("Initializing refresh state")
    try:
        conn = init_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS refresh_state (
                id INTEGER PRIMARY KEY,
                last_refresh TEXT
            )
        """)
        cursor.execute("SELECT last_refresh FROM refresh_state WHERE id = 1")
        row = cursor.fetchone()
        if row and row[0]:
            LAST_REFRESH = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        else:
            LAST_REFRESH = datetime.utcnow() - timedelta(days=1)
            cursor.execute("INSERT OR REPLACE INTO refresh_state (id, last_refresh) VALUES (1, ?)", 
                           (LAST_REFRESH.strftime("%Y-%m-%d %H:%M:%S"),))
        conn.commit()
        logger.debug(f"Initialized LAST_REFRESH: {LAST_REFRESH}")
    except Exception as e:
        logger.error(f"Failed to initialize refresh state: {e}")
        raise

def get_access_token():
    global TOKEN, TOKEN_EXPIRY
    now = datetime.utcnow()
    if TOKEN and TOKEN_EXPIRY and now < TOKEN_EXPIRY:
        logger.debug("Using cached access token")
        return TOKEN
    payload = {"username": API_USERNAME, "password": API_PASSWORD}
    logger.debug(f"Requesting token from {LOGIN_URL} with username={API_USERNAME}")
    try:
        response = requests.post(LOGIN_URL, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        TOKEN = data.get("access_token")
        TOKEN_EXPIRY = now + timedelta(minutes=55)
        logger.debug(f"Access token received: {TOKEN[:10]}... (expires {TOKEN_EXPIRY})")
        return TOKEN
    except requests.RequestException as e:
        logger.error(f"Error fetching access token: {e}, response: {getattr(e.response, 'text', 'N/A')}")
        return None
    except ValueError as e:
        logger.error(f"Invalid JSON response from login: {e}")
        return None

def fetch_paginated_data(url, token, since_date=None):
    headers = {"Authorization": f"Bearer {token}"}
    params = {"limit": 200, "offset": 0}
    if since_date:
        if "item_master" in url:
            params["filter[]"] = f"date_last_scanned>{since_date}"
        elif "transactions" in url:
            params["filter[]"] = f"scan_date>{since_date}"
    all_data = []
    logger.debug(f"Fetching data from {url} with params={params}")
    while True:
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json().get("data", [])
            logger.debug(f"Fetched {len(data)} records from {url} at offset {params['offset']}")
            if not data:
                logger.debug(f"Finished fetching {len(all_data)} total records from {url}")
                break
            all_data.extend(data)
            params["offset"] += 200
        except requests.RequestException as e:
            logger.error(f"Error fetching data from {url}: {e}, response: {getattr(e.response, 'text', 'N/A')}")
            return all_data
        except ValueError as e:
            logger.error(f"Invalid JSON response from {url}: {e}")
            return all_data
    return all_data

def update_item_master(data):
    logger.debug(f"Updating item master with {len(data)} records")
    try:
        conn = init_db_connection()
        cursor = conn.cursor()
        for item in data:
            cursor.execute(
                """
                INSERT INTO id_item_master (
                    tag_id, uuid_accounts_fk, serial_number, client_name, rental_class_num,
                    common_name, quality, bin_location, status, last_contract_num,
                    last_scanned_by, notes, status_notes, long, lat, date_last_scanned,
                    date_created, date_updated
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(tag_id) DO UPDATE SET
                    uuid_accounts_fk = excluded.uuid_accounts_fk,
                    serial_number = excluded.serial_number,
                    client_name = excluded.client_name,
                    rental_class_num = excluded.rental_class_num,
                    common_name = excluded.common_name,
                    quality = excluded.quality,
                    bin_location = excluded.bin_location,
                    status = excluded.status,
                    last_contract_num = excluded.last_contract_num,
                    last_scanned_by = excluded.last_scanned_by,
                    notes = excluded.notes,
                    status_notes = excluded.status_notes,
                    long = excluded.long,
                    lat = excluded.lat,
                    date_last_scanned = excluded.date_last_scanned,
                    date_created = excluded.date_created,
                    date_updated = excluded.date_updated
                """,
                (
                    item.get("tag_id"), item.get("uuid_accounts_fk"), item.get("serial_number"),
                    item.get("client_name"), item.get("rental_class_num"), item.get("common_name"),
                    item.get("quality"), item.get("bin_location"), item.get("status"),
                    item.get("last_contract_num"), item.get("last_scanned_by"), item.get("notes"),
                    item.get("status_notes"), item.get("long"), item.get("lat"),
                    item.get("date_last_scanned"), item.get("date_created"), item.get("date_updated"),
                ),
            )
        conn.commit()
        logger.debug("Item Master data updated successfully")
    except Exception as e:
        logger.error(f"Database error updating item master: {e}")
        raise

def clear_transactions():
    try:
        conn = init_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM id_transactions")
        conn.commit()
        logger.debug("Cleared id_transactions table")
    except Exception as e:
        logger.error(f"Error clearing transactions: {e}")
        raise

def update_transactions(data):
    logger.debug(f"Updating transactions with {len(data)} records")
    try:
        conn = init_db_connection()
        cursor = conn.cursor()
        for txn in data:
            cursor.execute(
                """
                INSERT INTO id_transactions (
                    contract_number, client_name, tag_id, common_name, bin_location,
                    scan_type, status, scan_date, scan_by, location_of_repair,
                    quality, dirty_or_mud, leaves, oil, mold, stain, oxidation,
                    other, rip_or_tear, sewing_repair_needed, grommet, rope,
                    buckle, date_created, date_updated, uuid_accounts_fk,
                    serial_number, rental_class_num, long, lat, wet,
                    service_required, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(contract_number, tag_id, scan_type, scan_date) DO UPDATE SET
                    client_name = excluded.client_name,
                    common_name = excluded.common_name,
                    bin_location = excluded.bin_location,
                    status = excluded.status,
                    scan_by = excluded.scan_by,
                    location_of_repair = excluded.location_of_repair,
                    quality = excluded.quality,
                    dirty_or_mud = excluded.dirty_or_mud,
                    leaves = excluded.leaves,
                    oil = excluded.oil,
                    mold = excluded.mold,
                    stain = excluded.stain,
                    oxidation = excluded.oxidation,
                    other = excluded.other,
                    rip_or_tear = excluded.rip_or_tear,
                    sewing_repair_needed = excluded.sewing_repair_needed,
                    grommet = excluded.grommet,
                    rope = excluded.rope,
                    buckle = excluded.buckle,
                    date_created = excluded.date_created,
                    date_updated = excluded.date_updated,
                    uuid_accounts_fk = excluded.uuid_accounts_fk,
                    serial_number = excluded.serial_number,
                    rental_class_num = excluded.rental_class_num,
                    long = excluded.long,
                    lat = excluded.lat,
                    wet = excluded.wet,
                    service_required = excluded.service_required,
                    notes = excluded.notes
                """,
                (
                    txn.get("contract_number"), txn.get("client_name"), txn.get("tag_id"),
                    txn.get("common_name"), txn.get("bin_location"), txn.get("scan_type"),
                    txn.get("status"), txn.get("scan_date"), txn.get("scan_by"),
                    txn.get("location_of_repair"), txn.get("quality"), txn.get("dirty_or_mud"),
                    txn.get("leaves"), txn.get("oil"), txn.get("mold"), txn.get("stain"),
                    txn.get("oxidation"), txn.get("other"), txn.get("rip_or_tear"),
                    txn.get("sewing_repair_needed"), txn.get("grommet"), txn.get("rope"),
                    txn.get("buckle"), txn.get("date_created"), txn.get("date_updated"),
                    txn.get("uuid_accounts_fk"), txn.get("serial_number"), txn.get("rental_class_num"),
                    txn.get("long"), txn.get("lat"), txn.get("wet"), txn.get("service_required"),
                    txn.get("notes")
                ),
            )
        conn.commit()
        logger.debug("Transaction data updated successfully")
    except Exception as e:
        logger.error(f"Database error updating transactions: {e}")
        raise

def update_seed_data(data):
    logger.debug(f"Updating seed data with {len(data)} records")
    try:
        conn = init_db_connection()
        cursor = conn.cursor()
        for item in data:
            cursor.execute(
                """
                INSERT INTO seed_rental_classes (
                    rental_class_id, common_name, bin_location
                )
                VALUES (?, ?, ?)
                ON CONFLICT(rental_class_id) DO UPDATE SET
                    common_name = excluded.common_name,
                    bin_location = excluded.bin_location
                """,
                (
                    item.get("rental_class_id"), item.get("common_name"), item.get("bin_location"),
                ),
            )
        conn.commit()
        logger.debug("SEED data updated successfully")
    except Exception as e:
        logger.error(f"Database error updating SEED data: {e}")
        raise

def refresh_data(full_refresh=False):
    global LAST_REFRESH, IS_RELOADING
    IS_RELOADING = True
    logger.debug(f"Starting {'full' if full_refresh else 'incremental'} refresh")
    try:
        token = get_access_token()
        if not token:
            logger.error("No access token. Aborting refresh.")
            return
        since_date = None if full_refresh else LAST_REFRESH
        if since_date:
            since_date = since_date.strftime("%Y-%m-%d %H:%M:%S")
        item_master_data = fetch_paginated_data(ITEM_MASTER_URL, token, since_date)
        transactions_data = fetch_paginated_data(TRANSACTION_URL, token, since_date)
        if full_refresh:
            clear_transactions()
            seed_data = fetch_paginated_data(SEED_URL, token)
            update_seed_data(seed_data)
        update_transactions(transactions_data)
        update_item_master(item_master_data)
        LAST_REFRESH = datetime.utcnow()
        conn = init_db_connection()
        conn.execute("INSERT OR REPLACE INTO refresh_state (id, last_refresh) VALUES (1, ?)", 
                     (LAST_REFRESH.strftime("%Y-%m-%d %H:%M:%S"),))
        conn.commit()
        logger.debug(f"Database refreshed at {LAST_REFRESH}")
    except Exception as e:
        logger.error(f"Error during refresh: {e}")
        raise
    finally:
        IS_RELOADING = False

def trigger_refresh(full=False):
    logger.debug(f"Triggering {'full' if full else 'incremental'} refresh")
    refresh_data(full_refresh=full)