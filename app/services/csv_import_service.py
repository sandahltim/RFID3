"""
CSV Import Service for Business Data
Handles weekly CSV imports from POS system into analytics database
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import glob
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from app import db
from app.services.logger import get_logger
from config import DB_CONFIG

logger = get_logger(__name__)

class CSVImportService:
    """Service for importing CSV business data files"""
    
    CSV_BASE_PATH = "/home/tim/RFID3/shared/POR"
    
    def __init__(self):
        self.logger = logger
        self.database_url = (
            f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}/{DB_CONFIG['database']}"
        )
        self.engine = create_engine(self.database_url, pool_pre_ping=True)
        self.Session = sessionmaker(bind=self.engine)
        self.import_stats = {
            "files_processed": 0,
            "total_records_processed": 0,
            "total_records_imported": 0,
            "errors": []
        }

    def import_equipment_data(self, file_path: str = None) -> Dict:
        """Import equipment/inventory data from equip8.26.25.csv"""
        if not file_path:
            # Find latest equipment file
            pattern = os.path.join(self.CSV_BASE_PATH, "equip*.csv")
            files = glob.glob(pattern)
            if not files:
                raise FileNotFoundError(f"No equipment CSV files found in {self.CSV_BASE_PATH}")
            file_path = max(files, key=os.path.getctime)  # Get newest file
            
        logger.info(f"Starting equipment import from: {file_path}")
        
        try:
            # Read CSV with error handling
            df = pd.read_csv(file_path, encoding='utf-8', low_memory=False)
            logger.info(f"Read {len(df)} records from equipment CSV")
            
            # Clean and transform data
            df = self._clean_equipment_data(df)
            
            # Import in batches for performance
            batch_size = 1000
            imported_count = 0
            
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                imported_count += self._import_equipment_batch(batch)
                
                if i % 5000 == 0:  # Progress logging every 5k records
                    logger.info(f"Imported {imported_count} equipment records so far...")
            
            # CRITICAL CORRELATION: Update RFID rental_class_num from POS ItemNum
            correlation_count = self._correlate_rfid_with_pos_data()
            
            # Update import stats
            self.import_stats["files_processed"] += 1
            self.import_stats["total_records_processed"] += len(df)
            self.import_stats["total_records_imported"] += imported_count
            
            logger.info(f"Equipment import completed: {imported_count}/{len(df)} records imported")
            logger.info(f"POS-RFID correlation completed: {correlation_count} RFID items updated with rental_class_num")
            
            return {
                "success": True,
                "file_path": file_path,
                "total_records": len(df),
                "imported_records": imported_count,
                "skipped_records": len(df) - imported_count,
                "correlation_count": correlation_count
            }
            
        except Exception as e:
            logger.error(f"Equipment import failed: {str(e)}", exc_info=True)
            self.import_stats["errors"].append(f"Equipment import: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }

    def _clean_equipment_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize equipment data"""
        
        # Handle missing values and data types
        df['ItemNum'] = df['ItemNum'].astype(str).str.strip()
        df['Name'] = df['Name'].fillna('').astype(str).str.strip()
        df['Category'] = df['Category'].fillna('').astype(str).str.strip()
        df['Current Store'] = df['Current Store'].fillna('').astype(str).str.strip()
        df['SerialNo'] = df['SerialNo'].fillna('').astype(str).str.strip()  # CRITICAL: Import serial numbers
        
        # Convert financial columns
        financial_cols = ['T/O YTD', 'T/O LTD', 'RepairCost MTD', 'RepairCost LTD', 'Sell Price']
        for col in financial_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.replace('$', ''), 
                                      errors='coerce').fillna(0)
        
        # Handle boolean columns
        df['Inactive'] = df['Inactive'].fillna(False).astype(bool)
        
        # Filter out empty or invalid item numbers
        df = df[df['ItemNum'].str.len() > 0]
        df = df[df['ItemNum'] != 'nan']
        
        logger.info(f"Cleaned equipment data: {len(df)} valid records")
        return df

    def _import_equipment_batch(self, batch_df: pd.DataFrame) -> int:
        """Import a batch of equipment records"""
        imported_count = 0
        
        try:
            # Build bulk insert query
            records = []
            for _, row in batch_df.iterrows():
                try:
                    record = {
                        'item_num': str(row.get('ItemNum', '')),
                        'name': str(row.get('Name', ''))[:300],  # Truncate to field limit
                        'category': str(row.get('Category', ''))[:100],
                        'serial_no': str(row.get('SerialNo', ''))[:100],  # CRITICAL: Include serial number for correlation
                        'turnover_ytd': float(row.get('T/O YTD', 0)),
                        'turnover_ltd': float(row.get('T/O LTD', 0)),
                        'repair_cost_ytd': float(row.get('RepairCost MTD', 0)),
                        'sell_price': float(row.get('Sell Price', 0)),
                        'current_store': str(row.get('Current Store', ''))[:10],
                        'inactive': bool(row.get('Inactive', False))
                    }
                    records.append(record)
                except Exception as e:
                    logger.warning(f"Skipping invalid equipment record: {e}")
                    continue
            
            if not records:
                return 0
            
            # Use pandas to_sql for efficient bulk insert
            records_df = pd.DataFrame(records)
            records_df.to_sql(
                'pos_equipment', 
                con=db.engine, 
                if_exists='append', 
                index=False,
                method='multi'
            )
            
            imported_count = len(records)
            
        except Exception as e:
            logger.error(f"Batch import failed: {e}")
            # Try individual inserts as fallback
            for record in records:
                try:
                    query = text("""
                        INSERT IGNORE INTO pos_equipment 
                        (item_num, name, category, serial_no, turnover_ytd, turnover_ltd, repair_cost_ytd, sell_price, current_store, inactive)
                        VALUES (:item_num, :name, :category, :serial_no, :turnover_ytd, :turnover_ltd, :repair_cost_ytd, :sell_price, :current_store, :inactive)
                    """)
                    db.session.execute(query, record)
                    imported_count += 1
                except Exception as ie:
                    logger.warning(f"Failed to import individual record {record.get('item_num')}: {ie}")
                    continue
            
            db.session.commit()
        
        return imported_count
    
    def _correlate_rfid_with_pos_data(self) -> int:
        """
        CORRELATION: Update POS equipment with RFID rental_class_num for analytics
        RFIDpro rental_class_num (from API/seed) is source of truth
        POS ItemNum should correlate with RFID rental_class_num for cross-system analytics
        """
        correlation_count = 0
        
        try:
            logger.info("Starting POS-RFID correlation for analytics...")
            
            # Update POS equipment with correlation field pointing to RFID rental_class_num
            # This preserves RFIDpro as source of truth while enabling POS-RFID analytics
            correlation_query = text("""
                UPDATE pos_equipment pos
                INNER JOIN id_item_master rfid ON TRIM(COALESCE(pos.serial_no, '')) = TRIM(COALESCE(rfid.serial_number, ''))
                SET pos.rfid_rental_class_num = rfid.rental_class_num
                WHERE TRIM(COALESCE(pos.serial_no, '')) != ''
                AND TRIM(COALESCE(rfid.serial_number, '')) != ''
                AND TRIM(COALESCE(rfid.rental_class_num, '')) != ''
            """)
            
            # First add the correlation column if it doesn't exist
            try:
                db.session.execute(text("ALTER TABLE pos_equipment ADD COLUMN rfid_rental_class_num VARCHAR(255)"))
                db.session.commit()
                logger.info("Added rfid_rental_class_num column to pos_equipment")
            except:
                pass  # Column already exists
            
            result = db.session.execute(correlation_query)
            correlation_count = result.rowcount
            db.session.commit()
            
            if correlation_count > 0:
                logger.info(f"CORRELATION SUCCESS: Updated {correlation_count} POS items with RFID rental_class_num correlation")
            else:
                logger.info("CORRELATION INFO: No matches found - RFIDpro remains source of truth for rental_class_num")
            
        except Exception as e:
            logger.error(f"CORRELATION ERROR: {e}")
            db.session.rollback()
            
        return correlation_count

    def import_transactions_data(self, file_path: str = None) -> Dict:
        """Import transaction data from transactions8.26.25.csv"""
        if not file_path:
            pattern = os.path.join(self.CSV_BASE_PATH, "transactions*.csv")
            files = glob.glob(pattern)
            if not files:
                raise FileNotFoundError(f"No transaction CSV files found in {self.CSV_BASE_PATH}")
            file_path = max(files, key=os.path.getctime)
            
        logger.info(f"Starting transactions import from: {file_path}")
        
        try:
            # Read CSV with chunk processing for large file
            chunk_size = 5000
            imported_count = 0
            total_records = 0
            
            for chunk in pd.read_csv(file_path, encoding='utf-8', chunksize=chunk_size, low_memory=False):
                chunk = self._clean_transactions_data(chunk)
                imported_count += self._import_transactions_batch(chunk)
                total_records += len(chunk)
                
                if total_records % 10000 == 0:
                    logger.info(f"Processed {total_records} transaction records...")
            
            logger.info(f"Transaction import completed: {imported_count}/{total_records} records imported")
            
            return {
                "success": True,
                "file_path": file_path,
                "total_records": total_records,
                "imported_records": imported_count
            }
            
        except Exception as e:
            logger.error(f"Transaction import failed: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def import_transaction_items_data(self, file_path: str = None) -> Dict:
        """Import transaction items data from transitems8.26.25.csv"""
        if not file_path:
            pattern = os.path.join(self.CSV_BASE_PATH, "transitems*.csv")
            files = glob.glob(pattern)
            if not files:
                raise FileNotFoundError(f"No transaction items CSV files found in {self.CSV_BASE_PATH}")
            file_path = max(files, key=os.path.getctime)
            
        logger.info(f"Starting transaction items import from: {file_path}")
        
        try:
            # Read CSV with chunk processing for large file (53MB, ~597K records)
            chunk_size = 3000
            imported_count = 0
            total_records = 0
            
            for chunk in pd.read_csv(file_path, encoding='utf-8', chunksize=chunk_size, low_memory=False):
                chunk = self._clean_transaction_items_data(chunk)
                imported_count += self._import_transaction_items_batch(chunk)
                total_records += len(chunk)
                
                if total_records % 15000 == 0:
                    logger.info(f"Processed {total_records} transaction item records...")
            
            logger.info(f"Transaction items import completed: {imported_count}/{total_records} records imported")
            
            return {
                "success": True,
                "file_path": file_path,
                "total_records": total_records,
                "imported_records": imported_count
            }
            
        except Exception as e:
            logger.error(f"Transaction items import failed: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def import_customer_data(self, csv_file_path: str, limit: int = None) -> Dict[str, Any]:
        """Import customer data from CSV file"""
        logger.info(f"Starting customer import from {csv_file_path}")
        
        try:
            # Read CSV
            df = pd.read_csv(csv_file_path)
            logger.info(f"Customer CSV shape: {df.shape}")
            
            if limit:
                df = df.head(limit)
                logger.info(f"Limited customer import to {limit} records")
            
            # Clean the data
            df = self._clean_customer_data(df)
            
            total_records = len(df)
            imported_count = 0
            
            # Import in chunks
            chunk_size = 1000
            session = self.Session()
            
            try:
                for chunk_start in range(0, total_records, chunk_size):
                    chunk = df.iloc[chunk_start:chunk_start + chunk_size]
                    logger.debug(f"Processing customer chunk {chunk_start//chunk_size + 1}")
                    
                    # Convert to list of dictionaries
                    records = chunk.to_dict('records')
                    
                    for record in records:
                        try:
                            # Clean record - convert pandas NaT to None for MySQL compatibility  
                            clean_record = {}
                            for key, value in record.items():
                                if pd.isna(value):
                                    clean_record[key] = None
                                else:
                                    clean_record[key] = value
                            
                            # Insert using raw SQL to handle duplicates - using actual schema columns
                            insert_sql = text("""
                                INSERT INTO pos_customers 
                                (`key`, cnum, name, address, city, zip, phone, email, 
                                 ytd_payments, ltd_payments, no_of_contracts, current_balance, 
                                 credit_limit, open_date, last_active_date, import_date)
                                VALUES 
                                (:key, :cnum, :name, :address, :city, :zip, :phone, :email,
                                 :ytd_payments, :ltd_payments, :no_of_contracts, :current_balance,
                                 :credit_limit, :open_date, :last_active_date, NOW())
                                ON DUPLICATE KEY UPDATE
                                name = VALUES(name),
                                address = VALUES(address),
                                ytd_payments = VALUES(ytd_payments),
                                last_active_date = VALUES(last_active_date),
                                import_date = NOW()
                            """)
                            
                            session.execute(insert_sql, clean_record)
                            imported_count += 1
                            
                        except Exception as e:
                            logger.warning(f"Error importing customer record: {e}")
                            continue
                    
                    # Commit each chunk
                    session.commit()
                    
                logger.info(f"Customer import completed: {imported_count}/{total_records} records")
                
                return {
                    "success": True,
                    "file_path": csv_file_path,
                    "total_records": total_records,
                    "records_imported": imported_count
                }
                
            except Exception as e:
                session.rollback()
                logger.error(f"Database error during customer import: {e}")
                raise
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"Customer import failed: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _clean_customer_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize customer data"""
        
        # Handle column name variations (CNUM vs Cnum, etc.)
        if 'CNUM' in df.columns:
            df['Cnum'] = df['CNUM']
        if 'No of Contracts' in df.columns:
            df['No. of Contracts'] = df['No of Contracts']
        
        # Required columns mapping to match actual database schema
        column_mapping = {
            'Key': 'key',
            'Cnum': 'cnum', 
            'Name': 'name',
            'Address': 'address',
            'City': 'city',
            'Zip': 'zip',
            'Phone': 'phone',
            'Email': 'email',
            'Open Date': 'open_date',
            'Last Active Date': 'last_active_date',
            'YTD Payments': 'ytd_payments',
            'LTD Payments': 'ltd_payments',
            'No. of Contracts': 'no_of_contracts',
            'CurrentBalance': 'current_balance',
            'Credit Limit': 'credit_limit'
        }
        
        # Rename columns
        for old_col, new_col in column_mapping.items():
            if old_col in df.columns:
                df[new_col] = df[old_col]
        
        # Clean text fields
        text_fields = ['name', 'address', 'city', 'phone', 'email', 'cnum']
        for field in text_fields:
            if field in df.columns:
                df[field] = df[field].astype(str).str.strip().replace('nan', None)
        
        # Convert numeric fields
        numeric_fields = ['ytd_payments', 'ltd_payments', 'current_balance', 'credit_limit', 'no_of_contracts']
        for field in numeric_fields:
            if field in df.columns:
                df[field] = pd.to_numeric(df[field], errors='coerce').fillna(0)
        
        # Convert date fields
        date_fields = ['open_date', 'last_active_date', 'last_payment_date']
        for field in date_fields:
            if field in df.columns:
                df[field] = pd.to_datetime(df[field], errors='coerce')
        
        # Select only the columns we need
        required_cols = list(column_mapping.values())
        available_cols = [col for col in required_cols if col in df.columns]
        df = df[available_cols]
        
        # Fill missing required fields and handle data corruption
        if 'key' in df.columns:
            df['key'] = pd.to_numeric(df['key'], errors='coerce').fillna(0).astype(int)
            # Remove rows with corrupted key (0 means invalid conversion)
            df = df[df['key'] > 0]
        else:
            df['key'] = range(1, len(df) + 1)  # Generate keys if missing
        
        # Ensure all required columns have defaults
        defaults = {
            'cnum': '',
            'name': 'Unknown',
            'address': '',
            'city': '',
            'zip': '',
            'phone': '',
            'email': '',
            'ytd_payments': 0.0,
            'ltd_payments': 0.0,
            'current_balance': 0.0,
            'credit_limit': 0.0,
            'no_of_contracts': 0
        }
        
        for col, default_val in defaults.items():
            if col not in df.columns:
                df[col] = default_val
            else:
                df[col] = df[col].fillna(default_val)
        
        # Handle datetime columns separately - convert NaT to None for MySQL
        date_columns = ['open_date', 'last_active_date']
        for col in date_columns:
            if col in df.columns:
                # Replace NaT with None (NULL in database)
                df[col] = df[col].where(pd.notna(df[col]), None)
        
        return df

    def _clean_transactions_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize transaction data"""
        
        # Clean contract numbers
        df['Contract No'] = df['Contract No'].astype(str).str.strip()
        df['Customer No'] = df['Customer No'].fillna('').astype(str).str.strip()
        df['Store No'] = df['Store No'].fillna('').astype(str).str.strip()
        
        # Convert date columns
        date_cols = ['Contract Date', 'Close Date', 'Billed Date', 'Completed Date']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Convert financial columns
        financial_cols = ['Rent Amt', 'Sale Amt', 'Tax Amt', 'Total', 'Total Paid', 'Total Owed']
        for col in financial_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.replace('$', ''), 
                                      errors='coerce').fillna(0)
        
        # Filter valid contracts
        df = df[df['Contract No'].str.len() > 0]
        df = df[df['Contract No'] != 'nan']
        
        return df

    def _import_transactions_batch(self, batch_df: pd.DataFrame) -> int:
        """Import a batch of transaction records"""
        imported_count = 0
        session = self.Session()
        
        try:
            for _, row in batch_df.iterrows():
                try:
                    # Insert using raw SQL to handle all database schema columns
                    insert_sql = text("""
                        INSERT INTO pos_transactions 
                        (contract_no, store_no, customer_no, status, contract_date, close_date, 
                         rent_amt, sale_amt, tax_amt, total, total_paid, total_owed)
                        VALUES 
                        (:contract_no, :store_no, :customer_no, :status, :contract_date, :close_date,
                         :rent_amt, :sale_amt, :tax_amt, :total, :total_paid, :total_owed)
                        ON DUPLICATE KEY UPDATE
                        status = VALUES(status),
                        total_paid = VALUES(total_paid),
                        import_date = NOW()
                    """)
                    
                    record = {
                        'contract_no': str(row.get('Contract No', ''))[:50],
                        'store_no': str(row.get('Store No', ''))[:10],
                        'customer_no': str(row.get('Customer No', ''))[:50],
                        'status': str(row.get('Status', ''))[:50],
                        'contract_date': row.get('Contract Date'),
                        'close_date': row.get('Close Date'),
                        'rent_amt': float(row.get('Rent Amt', 0) or 0),
                        'sale_amt': float(row.get('Sale Amt', 0) or 0),
                        'tax_amt': float(row.get('Tax Amt', 0) or 0),
                        'total': float(row.get('Total', 0) or 0),
                        'total_paid': float(row.get('Total Paid', 0) or 0),
                        'total_owed': float(row.get('Total Owed', 0) or 0)
                    }
                    
                    # Clean record - convert pandas NaT to None for MySQL compatibility  
                    clean_record = {}
                    for key, value in record.items():
                        if pd.isna(value):
                            clean_record[key] = None
                        else:
                            clean_record[key] = value
                    
                    session.execute(insert_sql, clean_record)
                    imported_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error importing transaction record: {e}")
                    continue
            
            # Commit the batch
            session.commit()
        
        except Exception as e:
            session.rollback()
            logger.error(f"Transaction batch import failed: {e}")
        finally:
            session.close()
        
        return imported_count

    def _clean_transaction_items_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize transaction items data"""
        
        # Clean contract and item numbers
        df['Contract No'] = df['Contract No'].astype(str).str.strip()
        df['ItemNum'] = df['ItemNum'].fillna('').astype(str).str.strip()
        
        # Convert date/time columns
        date_cols = ['Due Date', 'ConfirmedDate']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Convert numeric columns
        numeric_cols = ['Qty', 'Hours', 'Price', 'ItemPercentage', 'DiscountPercent', 
                       'Discount Amt', 'Daily Amt', 'Weekly Amt', 'Monthly Amt', 
                       'Minimum Amt', 'Meter Out', 'Meter In', 'Downtime Hrs', 'RetailPrice']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.replace('$', ''), 
                                      errors='coerce').fillna(0)
        
        # Filter valid records
        df = df[df['Contract No'].str.len() > 0]
        df = df[df['Contract No'] != 'nan']
        df = df[df['ItemNum'].str.len() > 0]
        df = df[df['ItemNum'] != 'nan']
        
        return df

    def _import_transaction_items_batch(self, batch_df: pd.DataFrame) -> int:
        """Import a batch of transaction item records"""
        imported_count = 0
        session = self.Session()
        
        try:
            for _, row in batch_df.iterrows():
                try:
                    # Insert using raw SQL to handle database schema
                    insert_sql = text("""
                        INSERT INTO pos_transaction_items 
                        (contract_no, item_num, qty, hours, due_date, due_time, line_status, 
                         price, `desc`, dmg_wvr, item_percentage, discount_percent, 
                         nontaxable, nondiscount, discount_amt, daily_amt, weekly_amt, 
                         monthly_amt, minimum_amt, meter_out, meter_in, downtime_hrs, 
                         retail_price, kit_field, confirmed_date, line_number)
                        VALUES 
                        (:contract_no, :item_num, :qty, :hours, :due_date, :due_time, :line_status,
                         :price, :description, :dmg_wvr, :item_percentage, :discount_percent,
                         :nontaxable, :nondiscount, :discount_amt, :daily_amt, :weekly_amt,
                         :monthly_amt, :minimum_amt, :meter_out, :meter_in, :downtime_hrs,
                         :retail_price, :kit_field, :confirmed_date, :line_number)
                        ON DUPLICATE KEY UPDATE
                        qty = VALUES(qty),
                        price = VALUES(price),
                        import_date = NOW()
                    """)
                    
                    record = {
                        'contract_no': str(row.get('Contract No', ''))[:50],
                        'item_num': str(row.get('ItemNum', ''))[:50],
                        'qty': float(row.get('Qty', 0) or 0),
                        'hours': float(row.get('Hours', 0) or 0),
                        'due_date': row.get('Due Date'),
                        'due_time': str(row.get('Due Time', ''))[:20],
                        'line_status': str(row.get('Line Status', ''))[:50],
                        'price': float(row.get('Price', 0) or 0),
                        'description': str(row.get('Desc', ''))[:500],
                        'dmg_wvr': float(row.get('DmgWvr', 0) or 0),
                        'item_percentage': float(row.get('ItemPercentage', 0) or 0),
                        'discount_percent': float(row.get('DiscountPercent', 0) or 0),
                        'nontaxable': 1 if str(row.get('Nontaxable', 'False')).lower() == 'true' else 0,
                        'nondiscount': 1 if str(row.get('Nondiscount', 'False')).lower() == 'true' else 0,
                        'discount_amt': float(row.get('Discount Amt', 0) or 0),
                        'daily_amt': float(row.get('Daily Amt', 0) or 0),
                        'weekly_amt': float(row.get('Weekly Amt', 0) or 0),
                        'monthly_amt': float(row.get('Monthly Amt', 0) or 0),
                        'minimum_amt': float(row.get('Minimum Amt', 0) or 0),
                        'meter_out': float(row.get('Meter Out', 0) or 0),
                        'meter_in': float(row.get('Meter In', 0) or 0),
                        'downtime_hrs': float(row.get('Downtime Hrs', 0) or 0),
                        'retail_price': float(row.get('RetailPrice', 0) or 0),
                        'kit_field': str(row.get('KitField', ''))[:50],
                        'confirmed_date': row.get('ConfirmedDate'),
                        'line_number': str(row.get('LineNumber', ''))[:20]
                    }
                    
                    # Clean record - convert pandas NaT to None for MySQL compatibility  
                    clean_record = {}
                    for key, value in record.items():
                        if pd.isna(value):
                            clean_record[key] = None
                        else:
                            clean_record[key] = value
                    
                    session.execute(insert_sql, clean_record)
                    imported_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error importing transaction item record: {e}")
                    continue
            
            # Commit the batch
            session.commit()
        
        except Exception as e:
            session.rollback()
            logger.error(f"Transaction items batch import failed: {e}")
        finally:
            session.close()
        
        return imported_count

    def get_import_status(self) -> Dict:
        """Get current import statistics"""
        return {
            **self.import_stats,
            "last_update": datetime.now().isoformat()
        }

    def clear_table(self, table_name: str) -> bool:
        """Clear a table before reimport (use with caution)"""
        try:
            db.session.execute(text(f"DELETE FROM {table_name}"))
            db.session.commit()
            logger.info(f"Cleared table: {table_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to clear table {table_name}: {e}")
            db.session.rollback()
            return False