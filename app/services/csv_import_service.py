"""
CSV Import Service for Business Data
Handles weekly CSV imports from POS system into analytics database
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from app.models.db_models import PLData
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
        """Import equipment/inventory data from equipPOS8.26.25.csv or equip8.26.25.csv"""
        if not file_path:
            # Find latest equipment file - try POS prefix first, then original
            pos_pattern = os.path.join(self.CSV_BASE_PATH, "equipPOS*.csv")
            old_pattern = os.path.join(self.CSV_BASE_PATH, "equip*.csv")
            
            pos_files = glob.glob(pos_pattern)
            old_files = glob.glob(old_pattern)
            
            # Prefer POS-prefixed files if available
            files = pos_files if pos_files else old_files
            
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
        """Clean and normalize equipment data with contamination filtering"""
        
        logger.info(f"Starting equipment data cleaning: {len(df)} raw records")
        
        # CRITICAL CONTAMINATION FILTERS - Remove obsolete data
        contamination_filters = [
            df['Category'].astype(str).str.upper() == 'UNUSED',
            df['Category'].astype(str).str.upper() == 'NON CURRENT ITEMS',
            df['Inactive'].fillna(False).astype(str).str.upper() == 'TRUE'
        ]
        
        # Count contaminated records before removal
        contaminated_mask = contamination_filters[0] | contamination_filters[1] | contamination_filters[2]
        contaminated_count = contaminated_mask.sum()
        logger.warning(f"Filtering out {contaminated_count} contaminated records ({contaminated_count/len(df)*100:.1f}%)")
        
        # Apply contamination filter
        df = df[~contaminated_mask].copy()
        logger.info(f"After contamination filtering: {len(df)} clean records ({len(df)/(len(df)+contaminated_count)*100:.1f}% retained)")
        
        # Handle missing values and data types
        df['ItemNum'] = df.get('ItemNum', df.get('KEY', '')).astype(str).str.strip()
        df['Name'] = df['Name'].fillna('').astype(str).str.strip()
        df['Category'] = df['Category'].fillna('').astype(str).str.strip()
        df['Current Store'] = df.get('Current Store', df.get('CurrentStore', '')).fillna('').astype(str).str.strip()
        df['SerialNo'] = df.get('SerialNo', df.get('SerialNumber', '')).fillna('').astype(str).str.strip()
        
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
                        'item_num': str(row.get('KEY', '')),  # CSV has KEY not ItemNum
                        'name': str(row.get('Name', ''))[:300],
                        'category': str(row.get('Category', ''))[:100],
                        'home_store': str(row.get('HomeStore', ''))[:10],
                        'current_store': str(row.get('CurrentStore', ''))[:10],
                        'inactive': str(row.get('Inactive', 'False')).upper() == 'TRUE'
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
                        (item_num, key_field, qty, name, category, serial_no, turnover_ytd, turnover_ltd, repair_cost_ytd, sell_price, current_store, inactive)
                        VALUES (:item_num, :key_field, :qty, :name, :category, :serial_no, :turnover_ytd, :turnover_ltd, :repair_cost_ytd, :sell_price, :current_store, :inactive)
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
            except SQLAlchemyError as e:
                db.session.rollback()
                logger.debug(f"Column already exists or other SQL error: {str(e)}")
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
        df['Contract No'] = df.get('Contract No', df.get('CNTR', '')).astype(str).str.strip()
        df['Customer No'] = df.get('Customer No', df.get('CUSN', '')).fillna('').astype(str).str.strip()
        df['Store No'] = df.get('Store No', df.get('STR', '')).fillna('').astype(str).str.strip()
        
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
                        'contract_no': str(row.get('CNTR', ''))[:50],
                        'store_no': str(row.get('STR', ''))[:10],
                        'customer_no': str(row.get('CUSN', ''))[:50],
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
    def import_all_csv_files(self) -> Dict:
        """
        Comprehensive Tuesday 8am CSV Import - All 7 POS CSV Files
        Imports: customers, equipment, transactions, transaction_items, scorecard, payroll, profit_loss
        """
        logger.info("🚀 Starting comprehensive Tuesday CSV import for all POS data")
        
        # Reset import stats for this run
        self.import_stats = {
            "files_processed": 0,
            "total_records_processed": 0,
            "total_records_imported": 0,
            "errors": []
        }
        
        import_results = {}
        import_batch_id_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # CSV configurations with all 7 files
        csv_configs = {
            'customers': {
                'file_pattern': r'customer\d+\.\d+\.\d+\.csv',
                'import_method': 'import_customer_data',
                'table_name': 'pos_customers'
            },
            'equipment': {
                'file_pattern': r'equip\d+\.\d+\.\d+\.csv',
                'import_method': 'import_equipment_data',
                'table_name': 'pos_equipment'
            },
            'transactions': {
                'file_pattern': r'transactions\d+\.\d+\.\d+\.csv',
                'import_method': 'import_transactions_data',
                'table_name': 'pos_transactions'
            },
            'transaction_items': {
                'file_pattern': r'transitems\d+\.\d+\.\d+\.csv',
                'import_method': 'import_transaction_items_data',
                'table_name': 'pos_transaction_items'
            },
            'scorecard': {
                'file_pattern': r'ScorecardTrends\d+\.\d+\.\d+\.csv',
                'import_method': 'import_scorecard_trends',
                'table_name': 'pos_scorecard_trends'
            },
            'payroll': {
                'file_pattern': r'PayrollTrends\d+\.\d+\.\d+\.csv',
                'import_method': 'import_payroll_trends',
                'table_name': 'pos_payroll_trends'
            },
            'profit_loss': {
                'file_pattern': r'PL\d+\.\d+\.\d+\.csv',
                'import_method': 'import_profit_loss',
                'table_name': 'pos_profit_loss'
            }
        }
        
        # Process each CSV file type
        for file_type, config in csv_configs.items():
            try:
                logger.info(f"🔄 Processing {file_type.upper()} CSV files...")
                
                # Find matching files (excluding RFIDpro files)
                matching_files = []
                import re
                
                for csv_file in os.listdir(self.CSV_BASE_PATH):
                    if csv_file.endswith('.csv') and 'RFIDpro' not in csv_file:
                        if re.match(config['file_pattern'], csv_file):
                            full_path = os.path.join(self.CSV_BASE_PATH, csv_file)
                            matching_files.append(full_path)
                
                if not matching_files:
                    logger.warning(f"⚠️  No {file_type} files found matching pattern: {config['file_pattern']}")
                    import_results[file_type] = {
                        "success": False,
                        "error": f"No files found matching pattern: {config['file_pattern']}",
                        "files_processed": 0
                    }
                    continue
                
                # Get the most recent file
                latest_file = max(matching_files, key=os.path.getctime)
                logger.info(f"📄 Found {file_type} file: {os.path.basename(latest_file)}")
                
                # Call the appropriate import method
                if hasattr(self, config['import_method']):
                    import_method = getattr(self, config['import_method'])
                    result = import_method(latest_file)
                    import_results[file_type] = result
                    
                    if result.get("success"):
                        logger.info(f"✅ {file_type.upper()} import completed: {result.get('imported_records', 0)} records")
                    else:
                        logger.error(f"❌ {file_type.upper()} import failed: {result.get('error')}")
                else:
                    logger.error(f"❌ Import method {config['import_method']} not found for {file_type}")
                    import_results[file_type] = {
                        "success": False,
                        "error": f"Import method {config['import_method']} not implemented"
                    }
                
            except Exception as e:
                logger.error(f"❌ Error processing {file_type}: {str(e)}", exc_info=True)
                import_results[file_type] = {
                    "success": False,
                    "error": str(e)
                }
                self.import_stats["errors"].append(f"{file_type}: {str(e)}")
        
        # Generate summary
        successful_imports = sum(1 for result in import_results.values() if result.get("success"))
        total_imports = len(import_results)
        
        summary = {
            "batch_id": import_batch_id_id,
            "timestamp": datetime.now().isoformat(),
            "total_file_types": total_imports,
            "successful_imports": successful_imports,
            "failed_imports": total_imports - successful_imports,
            "import_results": import_results,
            "overall_stats": self.import_stats
        }
        
        logger.info(f"🏁 Tuesday CSV import completed: {successful_imports}/{total_imports} file types successful")
        
        return summary

    def import_scorecard_trends(self, file_path: str) -> Dict:
        """Import scorecard trends data from ScorecardTrends*.csv with proper store marker support"""
        logger.info(f"Starting FIXED scorecard trends import from: {file_path}")
        
        try:
            # Read CSV with all columns preserved
            df = pd.read_csv(file_path, encoding='utf-8', low_memory=False)
            logger.info(f"Original CSV shape: {df.shape}")
            logger.info(f"CSV columns: {list(df.columns)}")
            
            # Clean the data first
            df = self._clean_scorecard_data_fixed(df)
            
            # Import using new normalized approach with store markers
            imported_count = self._import_scorecard_batch_fixed(df)
            
            return {
                "success": True,
                "file_path": file_path,
                "total_records": len(df),
                "imported_records": imported_count
            }
            
        except Exception as e:
            logger.error(f"Scorecard import failed: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}


    # Legacy function aliases for backward compatibility
    def _clean_scorecard_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Legacy alias for _clean_scorecard_data_fixed"""
        return self._clean_scorecard_data_fixed(df)

    def _import_scorecard_batch(self, df: pd.DataFrame) -> int:
        """Legacy alias for _import_scorecard_batch_fixed"""
        return self._import_scorecard_batch_fixed(df)
    def _clean_scorecard_data_fixed(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean scorecard data with proper column handling for actual CSV structure"""
        logger.info(f"Cleaning scorecard data: {len(df)} records")
        
        # Handle the Week ending Sunday column (date parsing)
        date_columns = [col for col in df.columns if 'week' in col.lower() and 'ending' in col.lower()]
        for col in date_columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            logger.info(f"Processed date column: {col}")
        
        # Convert financial/numeric columns (handle $, comma formatting)
        financial_patterns = ['revenue', 'reservation', 'discount', 'ar', 'cash']
        for col in df.columns:
            if any(pattern in col.lower() for pattern in financial_patterns):
                if df[col].dtype == 'object':
                    # Clean financial data: remove $, commas, handle empty strings
                    df[col] = df[col].astype(str).str.replace(r'[$,]', '', regex=True)
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    logger.debug(f"Processed financial column: {col}")
        
        # Convert integer columns (contracts, quotes, deliveries)
        integer_patterns = ['contracts', 'quotes', 'deliveries', 'week number']
        for col in df.columns:
            if any(pattern in col.lower() for pattern in integer_patterns):
                if col.lower() != 'week ending sunday':  # Don't convert date column
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                    logger.debug(f"Processed integer column: {col}")
        
        # Handle percentage columns (AR aging)
        percentage_patterns = ['%', 'percent']
        for col in df.columns:
            if any(pattern in col.lower() for pattern in percentage_patterns):
                if df[col].dtype == 'object':
                    # Remove % sign and convert to decimal
                    df[col] = df[col].astype(str).str.replace('%', '').str.strip()
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    logger.debug(f"Processed percentage column: {col}")
        
        logger.info(f"Data cleaning completed: {len(df)} clean records")
        return df

    def _import_scorecard_batch_fixed(self, df: pd.DataFrame) -> int:
        """Import scorecard data with proper store marker support and column mapping"""
        imported_count = 0
        session = self.Session()
        
        try:
            # Store mapping configuration
            STORE_MAPPING = {
                '3607': 'Wayzata',
                '6800': 'Brooklyn Park', 
                '728': 'Elk River',
                '8101': 'Fridley'
            }
            
            # Build column mapping based on actual CSV structure vs database columns
            column_mapping = self._build_scorecard_column_mapping(df.columns)
            logger.info(f"Built column mapping for {len(column_mapping)} columns")
            
            for _, row in df.iterrows():
                try:
                    # Extract base data that applies to all records
                    base_data = self._extract_base_scorecard_data(row, df.columns)
                    
                    # Skip rows with invalid dates
                    if not base_data.get('week_ending_sunday'):
                        continue
                    
                    # Skip rows with only future dates and no actual business data
                    # Future rows only have week numbers but no revenue/operational data
                    if not self._has_any_business_data(row, df.columns):
                        continue
                    
                    # COMPANY-WIDE RECORD (store_code = "000")
                    # Contains aggregated data for entire company
                    company_record = {
                        **base_data,
                        'store_code': '000',
                        'import_batch_id': int(datetime.now().strftime('%m%d%H%M')),
                        # Skip created_at - it auto-generates
                    }
                    
                    # Add company-wide metrics
                    company_record.update(self._extract_company_wide_metrics(row, df.columns))
                    
                    # Insert company-wide record
                    self._insert_scorecard_record(session, company_record)
                    imported_count += 1
                    
                    # STORE-SPECIFIC RECORDS (store_code = store codes)  
                    # Only create store records when there's actual store-specific data in CSV
                    if self._has_store_specific_data_in_csv(row, df.columns):
                        for store_code, store_name in STORE_MAPPING.items():
                            store_record = {
                                **base_data,
                                'store_code': store_code,
                                'import_batch_id': int(datetime.now().strftime('%m%d%H%M')),
                            # Skip created_at - it auto-generates
                            }
                            
                            # Add store-specific metrics
                            store_record.update(self._extract_store_specific_metrics(row, df.columns, store_code))
                            
                            # Insert store record (ON DUPLICATE KEY UPDATE will handle duplicates)
                            self._insert_scorecard_record(session, store_record)
                            imported_count += 1
                        else:
                            logger.debug(f"Skipping store {store_code} record - no meaningful data")
                    
                except Exception as e:
                    logger.warning(f"Error processing scorecard row: {e}")
                    continue
            
            session.commit()
            logger.info(f"Successfully imported {imported_count} scorecard records (company-wide + store-specific)")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Scorecard batch import failed: {e}")
            raise
        finally:
            session.close()
        
        return imported_count

    def _build_scorecard_column_mapping(self, csv_columns) -> Dict[str, str]:
        """Build mapping from CSV column names to database column names"""
        mapping = {}
        
        for col in csv_columns:
            col_clean = col.strip()
            
            # Date columns
            if 'week ending sunday' in col_clean.lower():
                mapping[col] = 'week_ending_sunday'
            
            # Revenue columns - map to new store revenue fields
            elif '3607 revenue' in col_clean.lower():
                mapping[col] = 'col_3607_revenue'
            elif '6800 revenue' in col_clean.lower():
                mapping[col] = 'col_6800_revenue' 
            elif '728 revenue' in col_clean.lower():
                mapping[col] = 'col_728_revenue'
            elif '8101 revenue' in col_clean.lower():
                mapping[col] = 'col_8101_revenue'
            elif 'total weekly revenue' in col_clean.lower():
                mapping[col] = 'total_weekly_revenue'
                
            # Contract columns
            elif '# new open contracts 3607' in col_clean.lower():
                mapping[col] = 'new_open_contracts_3607'
            elif '# new open contracts 6800' in col_clean.lower():
                mapping[col] = 'new_open_contracts_6800'
            elif '# new open contracts 728' in col_clean.lower():
                mapping[col] = 'new_open_contracts_728'
            elif '# new open contracts 8101' in col_clean.lower():
                mapping[col] = 'new_open_contracts_8101'
                
            # Reservation columns
            elif 'total $ on reservation 3607' in col_clean.lower():
                mapping[col] = 'total_on_reservation_3607'
            elif 'total $ on reservation 6800' in col_clean.lower():
                mapping[col] = 'total_on_reservation_6800'
            elif 'total $ on reservation 728' in col_clean.lower():
                mapping[col] = 'total_on_reservation_728'
            elif 'total $ on reservation 8101' in col_clean.lower():
                mapping[col] = 'total_on_reservation_8101'
                
            # Other important columns
            elif 'deliveries scheduled next 7 days' in col_clean.lower():
                mapping[col] = 'deliveries_scheduled_next_7_days_weds_tues_8101'
            elif 'week number' in col_clean.lower():
                mapping[col] = 'week_number'
        
        return mapping

    def _extract_base_scorecard_data(self, row, columns) -> Dict:
        """Extract base data that applies to all scorecard records"""
        base_data = {}
        
        # Find and extract week ending date
        for col in columns:
            if 'week ending sunday' in col.lower():
                date_val = row[col]
                if pd.notna(date_val):
                    base_data['week_ending_sunday'] = date_val
                    break
        
        # Extract total weekly revenue with proper cleaning
        for col in columns:
            if 'total weekly revenue' in col.lower():
                revenue_val = row[col]
                if pd.notna(revenue_val):
                    # Clean currency data: remove $, commas, spaces
                    cleaned_value = str(revenue_val).replace('$', '').replace(',', '').strip()
                    if cleaned_value and cleaned_value != '':
                        try:
                            base_data['total_weekly_revenue'] = float(cleaned_value)
                        except (ValueError, TypeError):
                            logger.warning(f"Could not convert total revenue '{revenue_val}' to float")
                    break
        
        return base_data

    def _extract_company_wide_metrics(self, row, columns) -> Dict:
        """Extract company-wide aggregated metrics"""
        metrics = {}
        
        # Company-wide metrics (totals, percentages, etc.)
        for col in columns:
            col_lower = col.lower()
            if 'total discount' in col_lower and 'company wide' in col_lower:
                if pd.notna(row[col]):
                    metrics['total_discount_company_wide'] = float(row[col])
            elif '% -total ar' in col_lower and '45 days' in col_lower:
                if pd.notna(row[col]):
                    metrics['ar_over_45_days_percent'] = float(row[col])
            elif 'total ar (cash customers)' in col_lower:
                if pd.notna(row[col]):
                    metrics['total_ar_cash_customers'] = float(row[col])
                    
        return metrics

    def _extract_store_specific_metrics(self, row, columns, store_code: str) -> Dict:
        """Extract store-specific metrics for given store code"""
        metrics = {}
        
        # Store revenue - map to correct database column name
        revenue_col = f'{store_code} Revenue'
        for col in columns:
            if revenue_col.lower() in col.lower():
                if pd.notna(row[col]):
                    # Clean currency data: remove $, commas, spaces
                    cleaned_value = str(row[col]).replace('$', '').replace(',', '').strip()
                    if cleaned_value and cleaned_value != '':
                        try:
                            metrics[f'col_{store_code}_revenue'] = float(cleaned_value)
                        except (ValueError, TypeError):
                            logger.warning(f"Could not convert revenue '{row[col]}' to float for store {store_code}")
                break
        
        # Store contracts
        for col in columns:
            if f'# new open contracts {store_code}' in col.lower():
                if pd.notna(row[col]):
                    # Clean numeric data
                    cleaned_value = str(row[col]).replace(',', '').strip()
                    if cleaned_value and cleaned_value != '':
                        try:
                            metrics[f'new_open_contracts_{store_code}'] = int(float(cleaned_value))
                        except (ValueError, TypeError):
                            logger.warning(f"Could not convert contracts '{row[col]}' to int for store {store_code}")
                break
        
        # Store reservations  
        for col in columns:
            if f'total $ on reservation {store_code}' in col.lower():
                if pd.notna(row[col]):
                    # Clean currency data
                    cleaned_value = str(row[col]).replace('$', '').replace(',', '').strip()
                    if cleaned_value and cleaned_value != '':
                        try:
                            metrics[f'total_on_reservation_{store_code}'] = float(cleaned_value)
                        except (ValueError, TypeError):
                            logger.warning(f"Could not convert reservation '{row[col]}' to float for store {store_code}")
                break
        
        # Store-specific deliveries (8101 only based on CSV)
        if store_code == '8101':
            for col in columns:
                if '# deliveries scheduled next 7 days' in col.lower() and '8101' in col.lower():
                    if pd.notna(row[col]):
                        metrics['deliveries_scheduled_next_7_days_weds_tues_8101'] = int(row[col])
                    break
        
        return metrics

    def _has_any_business_data(self, row, columns) -> bool:
        """Check if row has any actual business data (not just date and week number)"""
        # Key indicators of actual business data
        business_indicators = [
            'total weekly revenue',
            '3607 revenue', '6800 revenue', '728 revenue', '8101 revenue',
            '# new open contracts',
            '$ on reservation',
            'total discount',
            '# open quotes'
        ]
        
        for col in columns:
            col_lower = col.lower().strip()
            if any(indicator in col_lower for indicator in business_indicators):
                value = row[col]
                if pd.notna(value) and value != 0 and str(value).strip() not in ['', '0', '$0']:
                    return True
        
        return False

    def _has_store_specific_data_in_csv(self, row, columns) -> bool:
        """Check if CSV row has store-specific data based on column headers with store numbers"""
        # Store-specific columns have store numbers in headers (3607, 6800, 728, 8101)
        # Company-wide columns do NOT have store numbers in headers
        store_indicators = ['3607', '6800', '728', '8101']
        
        for col in columns:
            # Check if column header contains store numbers AND has data
            if any(store_num in col for store_num in store_indicators):
                value = row[col]
                if pd.notna(value) and value != 0 and str(value).strip() not in ['', '0', '$0']:
                    return True
        
        return False

    def _has_meaningful_store_data(self, store_record: Dict) -> bool:
        """Check if store record has any meaningful data beyond base fields"""
        # Check if any store-specific fields have non-zero values
        store_fields = [
            f'col_{store_record["store_code"]}_revenue',
            f'new_open_contracts_{store_record["store_code"]}', 
            f'total_on_reservation_{store_record["store_code"]}',
            'deliveries_scheduled_next_7_days_weds_tues_8101'
        ]
        
        return any(
            store_record.get(field, 0) not in [None, 0, 0.0] 
            for field in store_fields
        )

    def _insert_scorecard_record(self, session, record_data: Dict):
        """Insert scorecard record with proper error handling"""
        try:
            # Build column list and values for parameterized query
            columns = []
            values = {}
            
            for key, value in record_data.items():
                if key in ['week_ending_sunday', 'total_weekly_revenue', 'store_code', 
                          'col_3607_revenue', 'col_6800_revenue', 'col_728_revenue', 'col_8101_revenue',
                          'new_open_contracts_3607', 'new_open_contracts_6800', 
                          'new_open_contracts_728', 'new_open_contracts_8101',
                          'total_on_reservation_3607', 'total_on_reservation_6800',
                          'total_on_reservation_728', 'total_on_reservation_8101',
                          'deliveries_scheduled_next_7_days_weds_tues_8101', 'import_batch_id']:
                    columns.append(key)
                    values[key] = value
            
            if not columns:
                logger.warning("No valid columns found for scorecard record insertion")
                return
            
            # Create INSERT statement
            column_str = ', '.join(columns)
            placeholder_str = ', '.join([f":{col}" for col in columns])
            
            insert_sql = text(f"""
                INSERT INTO pos_scorecard_trends ({column_str})
                VALUES ({placeholder_str})
                ON DUPLICATE KEY UPDATE
                total_weekly_revenue = VALUES(total_weekly_revenue),
                import_batch_id = VALUES(import_batch_id)
            """)
            
            session.execute(insert_sql, values)
            
        except Exception as e:
            logger.error(f"Error inserting scorecard record: {e}")
            logger.error(f"Record data: {record_data}")
            raise

    def _clean_payroll_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean payroll trends data"""
        # Similar to scorecard cleaning
        for col in df.columns:
            if 'date' in col.lower() or 'week' in col.lower():
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    numeric_series = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.replace('$', ''), errors='coerce')
                    if not numeric_series.isna().all():
                        df[col] = numeric_series.fillna(0)
                except:
                    pass
        
        return df

    def _import_payroll_batch(self, df: pd.DataFrame) -> int:
        """Import payroll trends batch"""
        imported_count = 0
        session = self.Session()
        
        try:
            self._ensure_payroll_table_exists(session)
            
            for _, row in df.iterrows():
                try:
                    record_data = {}
                    for col in df.columns:
                        clean_col = self._clean_column_name(col)
                        value = row[col]
                        if pd.isna(value):
                            record_data[clean_col] = None
                        else:
                            record_data[clean_col] = value
                    
                    record_data['import_date'] = datetime.now()
                    record_data['import_batch_id'] = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    columns = list(record_data.keys())
                    placeholders = ', '.join([f":{col}" for col in columns])
                    
                    insert_sql = text(f"""
                        INSERT INTO pos_payroll_trends ({', '.join(columns)})
                        VALUES ({placeholders})
                        ON DUPLICATE KEY UPDATE import_date = VALUES(import_date)
                    """)
                    
                    session.execute(insert_sql, record_data)
                    imported_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error importing payroll record: {e}")
                    continue
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            logger.error(f"Payroll batch import failed: {e}")
        finally:
            session.close()
        
        return imported_count

    def _clean_profit_loss_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean profit & loss data and automatically transpose matrix format to normalized format
        Handles both original matrix format (PL8.28.25.csv) and transposed format (transposedPL.csv)
        """
        logger.info(f"Processing P&L data - Shape: {df.shape}")
        
        # Check if this is the matrix format (original PL8.28.25.csv)
        # Matrix format has store codes as columns (3607, 6800, 728, 8101) and account names
        # and the first column contains month names (June, July, August, etc.)
        is_matrix_format = False
        
        # Check if first column contains month names
        if len(df) > 0:
            first_col_values = df.iloc[:, 0].astype(str).str.strip().str.lower()
            month_names = ['june', 'july', 'august', 'september', 'october', 'november', 'december', 'january', 'february', 'march', 'april', 'may']
            if any(month in first_col_values.values for month in month_names):
                is_matrix_format = True
        
        # Also check for store code columns which indicate matrix format
        if any(col in ['3607', '6800', '728', '8101'] for col in df.columns):
            is_matrix_format = True
            
        if is_matrix_format:
            logger.info("Detected matrix format P&L data - converting to normalized format")
            df = self._transpose_pl_matrix(df)
        else:
            logger.info("Processing already normalized P&L data")
        
        # Standard financial data cleaning
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    numeric_series = pd.to_numeric(
                        df[col].astype(str).str.replace(',', '').str.replace('$', '').str.replace('(', '-').str.replace(')', ''),
                        errors='coerce'
                    )
                    if not numeric_series.isna().all():
                        df[col] = numeric_series.fillna(0)
                except:
                    pass
        
        return df
    
    def _transpose_pl_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert P&L matrix format to database-normalized format with proper account naming
        Input: Wide format with periods as rows and accounts/stores as columns
        Output: Long format for database with meaningful account names
        
        Structure understanding:
        - Columns 2-5: Store codes under "Rental Revenue" (implicit)
        - Column 6: "Sales Revenue" category header  
        - Columns 7-10: Store codes under "Sales Revenue"
        - Column 11+: Company-wide accounts (Other Revenue, COGS, etc.)
        """
        logger.info("Converting P&L matrix to normalized format with proper account naming...")
        
        try:
            data_df = df.copy()
            store_codes = ['3607', '6800', '728', '8101']
            
            # Build account mapping with proper context understanding
            account_columns = []
            current_category = "Rental Revenue"  # First section is implicitly Rental Revenue
            
            for col_idx, col_name in enumerate(df.columns):
                if col_idx < 2:  # Skip period and year columns
                    continue
                    
                col_name = str(col_name).strip()
                if not col_name or col_name in ['nan', '', 'Unnamed']:
                    continue
                
                # Handle pandas duplicate column renaming (3607.1, 6800.1, etc.)
                base_col_name = col_name.split('.')[0]  # Remove .1, .2, etc.
                
                # Check if this is a store code (including renamed ones)
                if col_name in store_codes or base_col_name in store_codes:
                    # Store-specific account under current category
                    actual_store = base_col_name if base_col_name in store_codes else col_name
                    if current_category:
                        account_name = f"{current_category} - {actual_store}"
                        store_code = actual_store
                    else:
                        # Fallback if no category context
                        account_name = actual_store
                        store_code = actual_store
                elif col_name in ['Sales Revenue', 'Rental Revenue', 'Other Revenue', 'COGS', 'Expenses']:
                    # Category header - update context and also treat as account
                    current_category = col_name
                    account_name = col_name  # Company-wide total
                    store_code = None
                else:
                    # Company-wide account (no store breakdown)
                    account_name = col_name
                    store_code = None
                    # Don't update category for individual accounts
                
                account_columns.append({
                    'index': col_idx,
                    'name': account_name,
                    'column': col_name,
                    'store_code': store_code,
                    'category': current_category
                })
                
                logger.debug(f"Column {col_idx}: '{col_name}' -> Account: '{account_name}', Store: {store_code}, Category: {current_category}")
            
            # Build normalized records
            normalized_records = []
            
            for _, row in data_df.iterrows():
                period = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                year_str = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                
                # Skip invalid periods
                if not period or period == 'nan' or period == 'TTM':
                    continue
                    
                # Convert year to integer
                try:
                    year = int(float(year_str))
                except (ValueError, TypeError):
                    continue
                
                # Process each account for this period
                for account_info in account_columns:
                    try:
                        amount_value = row.iloc[account_info['index']]
                        
                        # Convert to float
                        if pd.isna(amount_value) or str(amount_value).strip() == '':
                            amount = 0.0
                        else:
                            amount = float(str(amount_value).replace(',', '').replace('$', ''))
                        
                        # Only include non-zero amounts
                        if amount != 0.0:
                            normalized_records.append({
                                'account_name': account_info['name'],
                                'period_month': period,
                                'period_year': year,
                                'amount': amount,
                                'percentage': 0.0,  # Calculate later if needed
                                'category': account_info.get('category', 'Unknown'),
                                'account_code': f"PL{account_info['index']:03d}",
                                'store_code': account_info.get('store_code')
                            })
                    except Exception as e:
                        logger.warning(f"Error processing account {account_info['name']}: {e}")
                        continue
            
            if normalized_records:
                result_df = pd.DataFrame(normalized_records)
                logger.info(f"Converted P&L matrix to {len(normalized_records)} normalized records")
                return result_df
            else:
                logger.warning("No valid P&L data found in matrix")
                # Return empty DataFrame with correct structure
                return pd.DataFrame(columns=['account_name', 'period_month', 'period_year', 'amount', 'percentage', 'category', 'account_code'])
            
        except Exception as e:
            logger.error(f"Error converting P&L matrix: {str(e)}", exc_info=True)
            # Return empty DataFrame with correct structure on error
            return pd.DataFrame(columns=['account_name', 'period_month', 'period_year', 'amount', 'percentage', 'category', 'account_code'])

    def _categorize_pl_account(self, account_name: str) -> str:
        """Categorize P&L account based on name"""
        account_lower = account_name.lower()
        
        # Store-specific accounts (3607, 6800, 728, 8101 are store codes)
        if account_name in ['3607', '6800', '728', '8101', '3607.1', '6800.1', '728.1', '8101.1']:
            return 'Store Revenue'
        elif any(word in account_lower for word in ['revenue', 'sales', 'income', 'net income']):
            return 'Revenue'
        elif any(word in account_lower for word in ['cogs', 'cost of goods', 'merchandise', 'repair parts', 'shop supplies']):
            return 'Cost of Goods Sold'
        elif any(word in account_lower for word in ['payroll', 'wages', 'benefits', 'labor', 'contract labor']):
            return 'Payroll & Benefits'
        elif any(word in account_lower for word in ['rent', 'occupancy', 'facility']):
            return 'Occupancy'
        elif any(word in account_lower for word in ['advertising', 'marketing']):
            return 'Marketing'
        elif any(word in account_lower for word in ['office', 'supplies', 'admin', 'accounting', 'professional']):
            return 'Administrative'
        elif any(word in account_lower for word in ['loan', 'interest', 'financing', 'large equip']):
            return 'Financing'
        elif any(word in account_lower for word in ['fuel', 'gas', 'oil', 'freight', 'uniforms', 'repairs']):
            return 'Operating Expenses'
        else:
            return 'Other'

    def _import_profit_loss_batch(self, df: pd.DataFrame) -> int:
        """Import profit & loss batch into pl_data table"""
        imported_count = 0
        session = self.Session()
        
        try:
            # Import into pl_data table (normalized format)
            for _, row in df.iterrows():
                try:
                    # Check if this is normalized format (has account_name, period_month, etc.)
                    if 'account_name' in df.columns and 'period_month' in df.columns:
                        # Normalized format - import directly into pl_data
                        pl_record = PLData(
                            account_code=row.get('account_code', ''),
                            account_name=row.get('account_name', ''),
                            period_month=row.get('period_month', ''),
                            period_year=int(row.get('period_year', 2023)),
                            amount=float(row.get('amount', 0.0)) if pd.notna(row.get('amount', 0.0)) else 0.0,
                            percentage=float(row.get('percentage', 0.0)) if pd.notna(row.get('percentage', 0.0)) else 0.0,
                            category=row.get('category', 'Other'),
                            created_at=datetime.now()
                        )
                        
                        # Check for existing record
                        existing = session.query(PLData).filter_by(
                            account_name=pl_record.account_name,
                            period_month=pl_record.period_month,
                            period_year=pl_record.period_year
                        ).first()
                        
                        if existing:
                            # Update existing record
                            existing.amount = pl_record.amount
                            existing.percentage = pl_record.percentage
                            existing.category = pl_record.category
                            existing.created_at = datetime.now()
                        else:
                            # Add new record
                            session.add(pl_record)
                        
                        imported_count += 1
                    else:
                        # Old wide format - skip with warning
                        logger.warning("Skipping old wide format P&L record - should be normalized first")
                        continue
                    
                except Exception as e:
                    logger.warning(f"Error importing P&L record {row.to_dict()}: {e}")
                    continue
            
            session.commit()
            logger.info(f"Successfully imported {imported_count} P&L records into pl_data table")
            
        except Exception as e:
            session.rollback()
            logger.error(f"P&L batch import failed: {e}")
        finally:
            session.close()
        
        return imported_count

    def _clean_column_name(self, col_name: str) -> str:
        """Clean column name for database compatibility"""
        import re
        # Remove special characters, replace spaces with underscores
        clean = re.sub(r'[^\w\s]', '', str(col_name))
        clean = re.sub(r'\s+', '_', clean)
        clean = clean.lower().strip('_')
        
        # Handle reserved words
        reserved_words = ['key', 'order', 'date', 'time', 'status', 'type', 'desc']
        if clean in reserved_words:
            clean = f'{clean}_field'
            
        return clean

    def _ensure_scorecard_table_exists(self, session):
        """Ensure scorecard trends table exists with flexible schema"""
        try:
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS pos_scorecard_trends (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    week_ending DATE,
                    store_code VARCHAR(10),
                    revenue DECIMAL(15,2),
                    profit DECIMAL(15,2),
                    margin DECIMAL(5,2),
                    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    import_batch_id VARCHAR(50),
                    INDEX idx_week_ending (week_ending),
                    INDEX idx_store_code (store_code)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            session.commit()
        except Exception as e:
            logger.debug(f"Scorecard table already exists or creation failed: {e}")

    def _ensure_payroll_table_exists(self, session):
        """Ensure payroll trends table exists with flexible schema"""
        try:
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS pos_payroll_trends (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    week_ending DATE,
                    store_code VARCHAR(10),
                    total_hours DECIMAL(10,2),
                    total_wages DECIMAL(15,2),
                    avg_hourly_rate DECIMAL(8,2),
                    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    import_batch_id VARCHAR(50),
                    INDEX idx_week_ending (week_ending),
                    INDEX idx_store_code (store_code)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            session.commit()
        except Exception as e:
            logger.debug(f"Payroll table already exists or creation failed: {e}")

    def _ensure_profit_loss_table_exists(self, session):
        """Ensure profit & loss table exists with flexible schema"""
        try:
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS pos_profit_loss (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    account_line VARCHAR(100),
                    account_description VARCHAR(255),
                    current_month DECIMAL(15,2),
                    year_to_date DECIMAL(15,2),
                    prior_year DECIMAL(15,2),
                    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    import_batch_id VARCHAR(50),
                    INDEX idx_account_line (account_line)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            session.commit()
        except Exception as e:
            logger.debug(f"P&L table already exists or creation failed: {e}")

    def manual_trigger_tuesday_import(self) -> Dict:
        """Manual trigger for Tuesday CSV import - for testing and on-demand use"""
        logger.info("🔧 MANUAL TRIGGER: Starting comprehensive CSV import")
        
        try:
            result = self.import_all_csv_files()
            logger.info(f"🔧 MANUAL TRIGGER: Import completed - {result.get('successful_imports', 0)}/{result.get('total_file_types', 0)} successful")
            return result
            
        except Exception as e:
            logger.error(f"🔧 MANUAL TRIGGER: Import failed - {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
