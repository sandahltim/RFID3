#!/usr/bin/env python3
"""
RFID Pro to RFID Inventory Data Sync Script
Ensures all data from the legacy rfidpro database is migrated to rfid_inventory
"""

import mysql.connector
import sys
from datetime import datetime

# Database configurations
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Broadway8101',
    'charset': 'utf8mb4'
}

def get_connection(database):
    """Get database connection"""
    config = DB_CONFIG.copy()
    config['database'] = database
    return mysql.connector.connect(**config)

def get_table_names(connection):
    """Get all table names from a database"""
    cursor = connection.cursor()
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]
    cursor.close()
    return tables

def sync_table_data(source_db, target_db, table_name):
    """Sync data from source table to target table"""
    print(f"Syncing table: {table_name}")

    source_conn = get_connection(source_db)
    target_conn = get_connection(target_db)

    try:
        # Get source data count
        source_cursor = source_conn.cursor()
        source_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        source_count = source_cursor.fetchone()[0]

        # Get target data count
        target_cursor = target_conn.cursor()
        target_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        target_count = target_cursor.fetchone()[0]

        print(f"  Source: {source_count} records, Target: {target_count} records")

        if source_count > target_count:
            print(f"  Missing {source_count - target_count} records in target")

            # Get table structure
            source_cursor.execute(f"DESCRIBE {table_name}")
            columns = [col[0] for col in source_cursor.fetchall()]
            columns_str = ', '.join(columns)
            placeholders = ', '.join(['%s'] * len(columns))

            # Find records that don't exist in target
            # Using a simple approach: get all source data and insert with IGNORE
            source_cursor.execute(f"SELECT {columns_str} FROM {table_name}")
            source_data = source_cursor.fetchall()

            if source_data:
                insert_query = f"INSERT IGNORE INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                target_cursor.executemany(insert_query, source_data)
                target_conn.commit()
                print(f"  Inserted {target_cursor.rowcount} new records")
        elif source_count < target_count:
            print(f"  Target has {target_count - source_count} more records than source")
        else:
            print("  Tables are synchronized")

    except mysql.connector.Error as e:
        print(f"  ERROR syncing {table_name}: {e}")
    finally:
        source_cursor.close()
        target_cursor.close()
        source_conn.close()
        target_conn.close()

def main():
    """Main synchronization process"""
    print(f"RFID Pro to RFID Inventory Data Sync - {datetime.now()}")
    print("=" * 60)

    source_db = 'rfidpro'
    target_db = 'rfid_inventory'

    try:
        # Get table names from source database
        source_conn = get_connection(source_db)
        source_tables = get_table_names(source_conn)
        source_conn.close()

        # Get table names from target database
        target_conn = get_connection(target_db)
        target_tables = get_table_names(target_conn)
        target_conn.close()

        print(f"Source database ({source_db}): {len(source_tables)} tables")
        print(f"Target database ({target_db}): {len(target_tables)} tables")
        print()

        # Sync tables that exist in both databases
        common_tables = set(source_tables) & set(target_tables)
        print(f"Common tables to sync: {len(common_tables)}")

        for table in sorted(common_tables):
            sync_table_data(source_db, target_db, table)
            print()

        # Report tables that exist only in source
        source_only = set(source_tables) - set(target_tables)
        if source_only:
            print(f"Tables only in source ({source_db}):")
            for table in sorted(source_only):
                print(f"  - {table}")

        # Report tables that exist only in target
        target_only = set(target_tables) - set(source_tables)
        if target_only:
            print(f"Tables only in target ({target_db}):")
            for table in sorted(target_only):
                print(f"  - {table}")

        print(f"\nSync completed at {datetime.now()}")

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()