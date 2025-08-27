#!/usr/bin/env python3
"""
POS Equipment Data Import Script
================================

Imports equip.csv from POS system into id_item_master table.
Safely merges with RFID API data using field ownership strategy.

Date: August 27, 2025
System: RFID Dashboard POS Integration
File: /home/tim/RFID3/scripts/import_equip.py
"""

import csv
import sys
import os
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

# Add root directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.logger import get_logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pymysql
from config import DB_CONFIG

# Configure logging
logger = get_logger('pos_import', level=logging.INFO)

# Store mapping from POS codes to database codes  
STORE_MAPPING = {
    '001': '3607',  # Wayzata
    '002': '6800',  # Brooklyn Park  
    '003': '8101',  # Fridley
    '004': '728',   # Elk River
    '': None        # Handle empty store codes
}

# Equipment type mapping for identifier_type
def determine_identifier_type(serial_no, qty, name, category):
    """Determine identifier type based on equipment characteristics."""
    serial_no = str(serial_no).strip() if serial_no else ""
    qty_num = 0
    
    try:
        qty_num = int(qty) if qty else 0
    except (ValueError, TypeError):
        qty_num = 0
    
    name = str(name).upper() if name else ""
    category = str(category).upper() if category else ""
    
    # Logic for identifier type determination
    if serial_no and serial_no not in ['', '0', 'None']:
        if any(keyword in name for keyword in ['TENT', 'TABLE', 'CHAIR', 'STAGE']):
            return 'RFID'  # Likely candidates for RFID tagging
        else:
            return 'Sticker'  # Has serial, use sticker tracking
    elif qty_num > 1:
        return 'Bulk'  # Multiple quantity items
    elif any(keyword in category for keyword in ['PARTS', 'ACCESSORY', 'SMALL']):
        return 'Bulk'  # Small parts typically bulk
    else:
        return 'QR'  # Default for single items without serial

def clean_decimal_value(value, field_name, item_num):
    """Clean and convert decimal values, handling various formats."""
    if not value or value in ['', '0', '0.00']:
        return None
    
    try:
        # Remove any currency symbols or commas
        clean_value = str(value).replace('$', '').replace(',', '').strip()
        if not clean_value or clean_value == '0':
            return None
        return Decimal(clean_value)
    except (InvalidOperation, ValueError, TypeError) as e:
        logger.warning(f"Invalid {field_name} for ItemNum {item_num}: '{value}' - {e}")
        return None

def parse_rental_rates(row, item_num):
    """Parse rental rates and periods into JSON structure."""
    rates = {}
    
    try:
        # Extract periods and rates (columns Period 1-10, Rate 1-10)
        for i in range(1, 11):
            period_col = f"Period {i}"
            rate_col = f"Rate {i}"
            
            period = row.get(period_col, '').strip()
            rate = row.get(rate_col, '').strip()
            
            if period and rate and rate != '0':
                try:
                    rate_decimal = Decimal(rate.replace('$', '').replace(',', ''))
                    if rate_decimal > 0:
                        rates[period] = str(rate_decimal)
                except (InvalidOperation, ValueError):
                    continue
        
        return json.dumps(rates) if rates else None
    except Exception as e:
        logger.warning(f"Error parsing rental rates for ItemNum {item_num}: {e}")
        return None

def parse_vendor_ids(row, item_num):
    """Parse vendor information into JSON structure."""
    vendors = {}
    
    try:
        # Extract vendor numbers 1-3
        for i in range(1, 4):
            vendor_col = f"Vendor No {i}"
            vendor = row.get(vendor_col, '').strip()
            
            if vendor and vendor != '0':
                vendors[f"vendor_{i}"] = vendor
        
        return json.dumps(vendors) if vendors else None
    except Exception as e:
        logger.warning(f"Error parsing vendor IDs for ItemNum {item_num}: {e}")
        return None

def generate_tag_id(item_num, identifier_type, serial_no=None):
    """Generate appropriate tag_id based on identifier type."""
    item_num = str(item_num).strip()
    
    if identifier_type == 'RFID':
        # For RFID items, we'll use a placeholder until actual RFID tags are assigned
        return f"RFID-{item_num}"
    elif identifier_type == 'Sticker' and serial_no:
        return f"STK-{serial_no}"
    elif identifier_type == 'QR':
        return f"QR-{item_num}"
    elif identifier_type == 'Bulk':
        return f"BULK-{item_num}"
    else:
        return f"ITEM-{item_num}"

def import_equip_csv(csv_file_path, batch_size=1000, dry_run=False):
    """
    Import equipment data from CSV file into id_item_master table.
    
    Args:
        csv_file_path (str): Path to equip.csv file
        batch_size (int): Number of records to process per batch
        dry_run (bool): If True, don't commit changes to database
    
    Returns:
        dict: Import statistics
    """
    logger.info(f"Starting POS equipment import from: {csv_file_path}")
    logger.info(f"Batch size: {batch_size}, Dry run: {dry_run}")
    
    if not os.path.exists(csv_file_path):
        logger.error(f"CSV file not found: {csv_file_path}")
        return {"success": False, "error": "File not found"}
    
    # Create direct database connection
    engine = create_engine(
        f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}",
        echo=False
    )
    Session = sessionmaker(bind=engine)
    
    stats = {
        "total_rows": 0,
        "processed": 0,
        "new_items": 0,
        "updated_items": 0,
        "skipped": 0,
        "errors": 0,
        "error_details": []
    }
    
    session = Session()
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                
                # Verify required columns
                required_columns = {'ItemNum', 'Name', 'Home Store', 'Current Store'}
                if not required_columns.issubset(set(reader.fieldnames)):
                    missing = required_columns - set(reader.fieldnames)
                    logger.error(f"Missing required columns: {missing}")
                    return {"success": False, "error": f"Missing columns: {missing}"}
                
                logger.info(f"CSV columns found: {len(reader.fieldnames)}")
                logger.debug(f"Columns: {reader.fieldnames}")
                
                batch_items = []
                
                for row_num, row in enumerate(reader, 1):
                    stats["total_rows"] = row_num
                    
                    try:
                        # Extract required fields
                        item_num = row.get('ItemNum', '').strip()
                        if not item_num:
                            logger.warning(f"Row {row_num}: Missing ItemNum, skipping")
                            stats["skipped"] += 1
                            continue
                        
                        name = row.get('Name', '').strip()
                        category = row.get('Category', '').strip()
                        department = row.get('Department', '').strip()
                        manufacturer = row.get('MANF', '').strip()
                        serial_no = row.get('SerialNo', '').strip()
                        qty = row.get('Qty', '0').strip()
                        home_store = row.get('Home Store', '').strip()
                        current_store = row.get('Current Store', '').strip()
                        
                        # Determine identifier type
                        identifier_type = determine_identifier_type(serial_no, qty, name, category)
                        
                        # Generate tag_id
                        tag_id = generate_tag_id(item_num, identifier_type, serial_no)
                        
                        # Parse financial data
                        turnover_ytd = clean_decimal_value(row.get('T/O YTD'), 'T/O YTD', item_num)
                        repair_cost_ltd = clean_decimal_value(row.get('RepairCost LTD'), 'RepairCost LTD', item_num)
                        sell_price = clean_decimal_value(row.get('Sell Price'), 'Sell Price', item_num)
                        retail_price = clean_decimal_value(row.get('RetailPrice'), 'RetailPrice', item_num)
                        
                        # Map store codes
                        home_store_mapped = STORE_MAPPING.get(home_store, home_store)
                        current_store_mapped = STORE_MAPPING.get(current_store, current_store)
                        
                        # Parse complex fields
                        rental_rates = parse_rental_rates(row, item_num)
                        vendor_ids = parse_vendor_ids(row, item_num)
                        
                        # Create item data dictionary
                        item_data = {
                            'tag_id': tag_id,
                            'item_num': int(item_num),
                            'identifier_type': identifier_type,
                            'common_name': name[:255] if name else 'Unknown',  # Limit length
                            'department': department[:100] if department else None,
                            'manufacturer': manufacturer[:100] if manufacturer else None,
                            'turnover_ytd': turnover_ytd,
                            'repair_cost_ltd': repair_cost_ltd,
                            'sell_price': sell_price,
                            'retail_price': retail_price,
                            'home_store': home_store_mapped,
                            'current_store': current_store_mapped,
                            'rental_rates': rental_rates,
                            'vendor_ids': vendor_ids,
                            'tag_history': json.dumps({"import_date": datetime.now(timezone.utc).isoformat(),
                                                      "source": "POS_equip_csv",
                                                      "original_serial": serial_no})
                        }
                        
                        batch_items.append(item_data)
                        
                        # Process batch when full
                        if len(batch_items) >= batch_size:
                            batch_stats = process_batch(batch_items, session, dry_run)
                            update_stats(stats, batch_stats)
                            batch_items = []
                            
                            logger.info(f"Processed {stats['processed']} items "
                                      f"({stats['new_items']} new, {stats['updated_items']} updated, "
                                      f"{stats['skipped']} skipped, {stats['errors']} errors)")
                    
                    except Exception as e:
                        logger.error(f"Error processing row {row_num}: {e}", exc_info=True)
                        stats["errors"] += 1
                        stats["error_details"].append(f"Row {row_num}: {str(e)}")
                        continue
                
                # Process remaining items
                if batch_items:
                    batch_stats = process_batch(batch_items, session, dry_run)
                    update_stats(stats, batch_stats)
                
                # Final statistics
                logger.info("=== POS Equipment Import Completed ===")
                logger.info(f"Total rows: {stats['total_rows']}")
                logger.info(f"Processed: {stats['processed']}")
                logger.info(f"New items: {stats['new_items']}")
                logger.info(f"Updated items: {stats['updated_items']}")
                logger.info(f"Skipped: {stats['skipped']}")
                logger.info(f"Errors: {stats['errors']}")
                
                if not dry_run and stats['errors'] == 0:
                    logger.info("Import completed successfully - all data committed")
                elif dry_run:
                    logger.info("DRY RUN completed - no data was committed to database")
                else:
                    logger.warning(f"Import completed with {stats['errors']} errors")
                
                stats["success"] = True
                return stats
                
    except Exception as e:
        logger.error(f"Critical error during import: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def process_batch(batch_items, session, dry_run):
    """Process a batch of items."""
    batch_stats = {"processed": 0, "new_items": 0, "updated_items": 0, "errors": 0}
    
    try:
        for item_data in batch_items:
            try:
                # Check if item exists by item_num or tag_id
                existing_item = session.execute(text("""
                    SELECT * FROM id_item_master 
                    WHERE item_num = :item_num OR tag_id = :tag_id
                """), {
                    'item_num': item_data['item_num'],
                    'tag_id': item_data['tag_id']
                }).fetchone()
                
                if existing_item:
                    # Update existing item with POS data only
                    update_sql = """
                        UPDATE id_item_master 
                        SET item_num = :item_num,
                            identifier_type = :identifier_type,
                            department = :department,
                            manufacturer = :manufacturer,
                            turnover_ytd = :turnover_ytd,
                            repair_cost_ltd = :repair_cost_ltd,
                            sell_price = :sell_price,
                            retail_price = :retail_price,
                            home_store = :home_store,
                            current_store = :current_store,
                            rental_rates = :rental_rates,
                            vendor_ids = :vendor_ids,
                            tag_history = :tag_history,
                            common_name = :common_name
                        WHERE tag_id = :tag_id
                    """
                    session.execute(text(update_sql), item_data)
                    batch_stats["updated_items"] += 1
                    logger.debug(f"Updated existing item: {item_data['item_num']} ({item_data['tag_id']})")
                else:
                    # Create new item
                    insert_sql = """
                        INSERT INTO id_item_master (
                            tag_id, item_num, identifier_type, common_name, department, manufacturer,
                            turnover_ytd, repair_cost_ltd, sell_price, retail_price,
                            home_store, current_store, rental_rates, vendor_ids, tag_history
                        ) VALUES (
                            :tag_id, :item_num, :identifier_type, :common_name, :department, :manufacturer,
                            :turnover_ytd, :repair_cost_ltd, :sell_price, :retail_price,
                            :home_store, :current_store, :rental_rates, :vendor_ids, :tag_history
                        )
                    """
                    session.execute(text(insert_sql), item_data)
                    batch_stats["new_items"] += 1
                    logger.debug(f"Created new item: {item_data['item_num']} ({item_data['tag_id']})")
                
                batch_stats["processed"] += 1
                
            except Exception as e:
                logger.error(f"Error processing item {item_data.get('item_num')}: {e}")
                batch_stats["errors"] += 1
                continue
        
        if not dry_run:
            session.commit()
            logger.debug(f"Committed batch: {batch_stats['processed']} items")
        else:
            session.rollback()
            logger.debug(f"Rolled back batch (dry run): {batch_stats['processed']} items")
            
    except Exception as e:
        logger.error(f"Error processing batch: {e}")
        session.rollback()
        batch_stats["errors"] += len(batch_items)
    
    return batch_stats

def update_stats(main_stats, batch_stats):
    """Update main statistics with batch statistics."""
    main_stats["processed"] += batch_stats["processed"]
    main_stats["new_items"] += batch_stats["new_items"]
    main_stats["updated_items"] += batch_stats["updated_items"]
    main_stats["errors"] += batch_stats["errors"]

def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Import POS equipment data into RFID database')
    parser.add_argument('--csv-file', 
                        default='/home/tim/RFID3/shared/POR/equip8.26.25.csv',
                        help='Path to equip.csv file')
    parser.add_argument('--batch-size', type=int, default=1000,
                        help='Batch size for processing (default: 1000)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Perform dry run without committing to database')
    
    args = parser.parse_args()
    
    logger.info("=== POS Equipment Import Starting ===")
    logger.info(f"CSV file: {args.csv_file}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Dry run: {args.dry_run}")
    
    # Import equipment data
    result = import_equip_csv(args.csv_file, args.batch_size, args.dry_run)
    
    if result["success"]:
        logger.info("Import completed successfully")
        sys.exit(0)
    else:
        logger.error(f"Import failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == '__main__':
    main()