#!/usr/bin/env python3
"""
Add Essential POS Integration Fields to id_item_master
Executes individual ALTER statements with error handling and verification
"""

import sys
import pymysql
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from config import DB_CONFIG, LOG_DIR
from app.services.logger import get_logger

logger = get_logger('pos_schema_setup', level=logging.INFO, log_file=str(LOG_DIR / 'pos_schema_setup.log'))

# Essential POS fields to add
ESSENTIAL_FIELDS = [
    {
        'name': 'manufacturer', 
        'definition': 'VARCHAR(100)',
        'comment': 'Equipment manufacturer'
    },
    {
        'name': 'type_desc',
        'definition': 'VARCHAR(50)', 
        'comment': 'POS type description'
    },
    {
        'name': 'turnover_ltd',
        'definition': 'DECIMAL(10,2)',
        'comment': 'Life-to-date turnover revenue'
    },
    {
        'name': 'repair_cost_ltd',
        'definition': 'DECIMAL(10,2)',
        'comment': 'Life-to-date repair costs'
    },
    {
        'name': 'sell_price',
        'definition': 'DECIMAL(10,2)',
        'comment': 'Selling/resale price'
    },
    {
        'name': 'retail_price', 
        'definition': 'DECIMAL(10,2)',
        'comment': 'Retail rental price'
    },
    {
        'name': 'home_store',
        'definition': 'VARCHAR(10)',
        'comment': 'Home store code'
    },
    {
        'name': 'current_store',
        'definition': 'VARCHAR(10)',
        'comment': 'Current store location'
    },
    {
        'name': 'quantity',
        'definition': 'INT DEFAULT 1',
        'comment': 'Quantity for bulk items'
    },
    {
        'name': 'reorder_min',
        'definition': 'INT',
        'comment': 'Minimum reorder level'
    },
    {
        'name': 'reorder_max',
        'definition': 'INT', 
        'comment': 'Maximum reorder level'
    },
    {
        'name': 'data_source',
        'definition': "VARCHAR(20) DEFAULT 'RFID_API'",
        'comment': 'Source of data'
    },
    {
        'name': 'pos_last_updated',
        'definition': 'DATETIME',
        'comment': 'Last update from POS data import'
    }
]

def connect_database():
    """Create database connection."""
    try:
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database'],
            charset=DB_CONFIG['charset']
        )
        logger.info("Database connection established")
        return connection
    except Exception as e:
        logger.error(f"Failed to connect to database: {str(e)}")
        return None

def field_exists(connection, field_name):
    """Check if field already exists in table."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'id_item_master' AND COLUMN_NAME = %s
            """, (DB_CONFIG['database'], field_name))
            result = cursor.fetchone()
            return result[0] > 0
    except Exception as e:
        logger.error(f"Error checking if field {field_name} exists: {str(e)}")
        return True  # Assume exists to avoid duplicate attempts

def add_field(connection, field_info):
    """Add a single field to id_item_master table."""
    field_name = field_info['name']
    field_definition = field_info['definition']
    field_comment = field_info['comment']
    
    if field_exists(connection, field_name):
        logger.info(f"Field {field_name} already exists, skipping")
        return True
        
    try:
        with connection.cursor() as cursor:
            sql = f"ALTER TABLE id_item_master ADD COLUMN {field_name} {field_definition} COMMENT '{field_comment}'"
            logger.info(f"Adding field: {field_name}")
            cursor.execute(sql)
            connection.commit()
            logger.info(f"Successfully added field: {field_name}")
            return True
    except Exception as e:
        logger.error(f"Failed to add field {field_name}: {str(e)}")
        return False

def create_indexes(connection):
    """Create essential indexes for POS integration."""
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_identifier_type ON id_item_master(identifier_type)",
        "CREATE INDEX IF NOT EXISTS idx_current_store ON id_item_master(current_store)", 
        "CREATE INDEX IF NOT EXISTS idx_manufacturer ON id_item_master(manufacturer)",
        "CREATE INDEX IF NOT EXISTS idx_turnover_ytd ON id_item_master(turnover_ytd)",
        "CREATE INDEX IF NOT EXISTS idx_data_source ON id_item_master(data_source)",
        "CREATE INDEX IF NOT EXISTS idx_store_status ON id_item_master(current_store, status)"
    ]
    
    success_count = 0
    for index_sql in indexes:
        try:
            with connection.cursor() as cursor:
                cursor.execute(index_sql)
                connection.commit()
                success_count += 1
                logger.info(f"Created index: {index_sql}")
        except Exception as e:
            logger.warning(f"Index creation failed (may already exist): {str(e)}")
    
    logger.info(f"Created {success_count} indexes successfully")
    return success_count

def update_existing_records(connection):
    """Update existing RFID records with default POS values."""
    try:
        with connection.cursor() as cursor:
            # Set data source for existing records
            cursor.execute("""
                UPDATE id_item_master 
                SET data_source = 'RFID_API', 
                    identifier_type = 'RFID'
                WHERE data_source IS NULL
            """)
            
            updated_count = cursor.rowcount
            connection.commit()
            logger.info(f"Updated {updated_count} existing records with RFID defaults")
            return updated_count
    except Exception as e:
        logger.error(f"Failed to update existing records: {str(e)}")
        return 0

def verify_schema(connection):
    """Verify the schema enhancement was successful."""
    try:
        with connection.cursor() as cursor:
            # Count total fields
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'id_item_master'
            """, (DB_CONFIG['database'],))
            total_fields = cursor.fetchone()[0]
            
            # Count POS fields added
            pos_field_names = [f['name'] for f in ESSENTIAL_FIELDS]
            placeholders = ','.join(['%s'] * len(pos_field_names))
            cursor.execute(f"""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'id_item_master' 
                AND COLUMN_NAME IN ({placeholders})
            """, (DB_CONFIG['database'],) + tuple(pos_field_names))
            pos_fields = cursor.fetchone()[0]
            
            logger.info(f"Schema verification: {total_fields} total fields, {pos_fields} POS fields added")
            return total_fields, pos_fields
    except Exception as e:
        logger.error(f"Schema verification failed: {str(e)}")
        return 0, 0

def main():
    """Main execution function."""
    logger.info("=== Starting POS Schema Enhancement ===")
    
    connection = connect_database()
    if not connection:
        sys.exit(1)
        
    try:
        # Add essential fields
        success_count = 0
        for field_info in ESSENTIAL_FIELDS:
            if add_field(connection, field_info):
                success_count += 1
        
        logger.info(f"Successfully added {success_count}/{len(ESSENTIAL_FIELDS)} fields")
        
        # Create indexes
        create_indexes(connection)
        
        # Update existing records
        update_existing_records(connection)
        
        # Verify results
        total_fields, pos_fields = verify_schema(connection)
        
        logger.info("=== POS Schema Enhancement Complete ===")
        print(f"Schema Enhancement Complete: {total_fields} total fields, {pos_fields} POS fields added")
        
        if pos_fields >= len(ESSENTIAL_FIELDS) * 0.8:  # 80% success rate
            sys.exit(0)
        else:
            logger.warning("Less than 80% of fields added successfully")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Schema enhancement failed: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        if connection:
            connection.close()
            logger.info("Database connection closed")

if __name__ == '__main__':
    main()