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
        """Clean and normalize equipment data with contamination filtering"""
        
        logger.info(f"Starting equipment data cleaning: {len(df)} raw records")
        
        # CRITICAL CONTAMINATION FILTERS - Remove obsolete data
        contamination_filters = [
            df['Category'].str.upper() == 'UNUSED',
            df['Category'].str.upper() == 'NON CURRENT ITEMS', 
            df['Inactive'].fillna(False).astype(bool) == True
        ]
        
        # Count contaminated records before removal
        contaminated_mask = contamination_filters[0] | contamination_filters[1] | contamination_filters[2]
        contaminated_count = contaminated_mask.sum()
        logger.warning(f"Filtering out {contaminated_count} contaminated records ({contaminated_count/len(df)*100:.1f}%)")
        
        # Apply contamination filter
        df = df[~contaminated_mask].copy()
        logger.info(f"After contamination filtering: {len(df)} clean records ({len(df)/(len(df)+contaminated_count)*100:.1f}% retained)")
        
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
                        'key_field': str(row.get('Key', ''))[:100],  # CRITICAL: Key field for identifier type classification
                        'name': str(row.get('Name', ''))[:300],  # Truncate to field limit
                        'category': str(row.get('Category', ''))[:100],
                        'qty': int(row.get('Qty', 0)),  # CRITICAL: Quantity for bulk/serialized classification
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
        import_batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
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
            "batch_id": import_batch_id,
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
        """Import scorecard trends data from ScorecardTrends*.csv"""
        logger.info(f"Starting scorecard trends import from: {file_path}")
        
        try:
            # Read CSV and handle wide format with many columns
            df = pd.read_csv(file_path, encoding='utf-8', low_memory=False)
            
            # Remove empty/unnamed columns that are common in Excel exports
            meaningful_cols = []
            for col in df.columns:
                if not str(col).startswith('Unnamed:') and pd.notna(col):
                    if df[col].dropna().nunique() > 0:  # Has actual data
                        meaningful_cols.append(col)
            
            df = df[meaningful_cols[:50]]  # Limit to first 50 meaningful columns
            logger.info(f"Scorecard CSV processed: {len(df)} records, {len(df.columns)} columns")
            
            # Clean the data
            df = self._clean_scorecard_data(df)
            
            # Import in batches
            imported_count = self._import_scorecard_batch(df)
            
            return {
                "success": True,
                "file_path": file_path,
                "total_records": len(df),
                "imported_records": imported_count
            }
            
        except Exception as e:
            logger.error(f"Scorecard import failed: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def import_payroll_trends(self, file_path: str) -> Dict:
        """Import payroll trends data from PayrollTrends*.csv"""
        logger.info(f"Starting payroll trends import from: {file_path}")
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8', low_memory=False)
            logger.info(f"Payroll CSV shape: {df.shape}")
            
            # Clean the data
            df = self._clean_payroll_data(df)
            
            # Import in batches
            imported_count = self._import_payroll_batch(df)
            
            return {
                "success": True,
                "file_path": file_path,
                "total_records": len(df),
                "imported_records": imported_count
            }
            
        except Exception as e:
            logger.error(f"Payroll import failed: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def import_profit_loss(self, file_path: str) -> Dict:
        """Import profit & loss data from PL*.csv"""
        logger.info(f"Starting P&L import from: {file_path}")
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8', low_memory=False)
            logger.info(f"P&L CSV shape: {df.shape}")
            
            # Clean the data
            df = self._clean_profit_loss_data(df)
            
            # Import in batches
            imported_count = self._import_profit_loss_batch(df)
            
            return {
                "success": True,
                "file_path": file_path,
                "total_records": len(df),
                "imported_records": imported_count
            }
            
        except Exception as e:
            logger.error(f"P&L import failed: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _clean_scorecard_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean scorecard trends data"""
        # Handle date columns
        for col in df.columns:
            if 'date' in col.lower() or 'week' in col.lower():
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Convert numeric columns
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to numeric if it looks numeric
                try:
                    numeric_series = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.replace('$', ''), errors='coerce')
                    if not numeric_series.isna().all():
                        df[col] = numeric_series.fillna(0)
                except:
                    pass
        
        return df

    def _import_scorecard_batch(self, df: pd.DataFrame) -> int:
        """Import scorecard trends batch"""
        imported_count = 0
        session = self.Session()
        
        try:
            # Create table if it doesn't exist
            self._ensure_scorecard_table_exists(session)
            
            # Convert DataFrame to records and insert
            for _, row in df.iterrows():
                try:
                    # Create a generic record structure
                    record_data = {}
                    for col in df.columns:
                        clean_col = self._clean_column_name(col)
                        value = row[col]
                        if pd.isna(value):
                            record_data[clean_col] = None
                        else:
                            record_data[clean_col] = value
                    
                    # Add metadata
                    record_data['import_date'] = datetime.now()
                    record_data['import_batch'] = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    # Insert using dynamic SQL
                    columns = list(record_data.keys())
                    placeholders = ', '.join([f":{col}" for col in columns])
                    
                    insert_sql = text(f"""
                        INSERT INTO pos_scorecard_trends ({', '.join(columns)})
                        VALUES ({placeholders})
                        ON DUPLICATE KEY UPDATE import_date = VALUES(import_date)
                    """)
                    
                    session.execute(insert_sql, record_data)
                    imported_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error importing scorecard record: {e}")
                    continue
            
            session.commit()
            
        except Exception as e:
            session.rollback()
            logger.error(f"Scorecard batch import failed: {e}")
        finally:
            session.close()
        
        return imported_count

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
                    record_data['import_batch'] = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
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
        """Clean profit & loss data"""
        # Financial data cleaning
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

    def _import_profit_loss_batch(self, df: pd.DataFrame) -> int:
        """Import profit & loss batch"""
        imported_count = 0
        session = self.Session()
        
        try:
            self._ensure_profit_loss_table_exists(session)
            
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
                    record_data['import_batch'] = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    columns = list(record_data.keys())
                    placeholders = ', '.join([f":{col}" for col in columns])
                    
                    insert_sql = text(f"""
                        INSERT INTO pos_profit_loss ({', '.join(columns)})
                        VALUES ({placeholders})
                        ON DUPLICATE KEY UPDATE import_date = VALUES(import_date)
                    """)
                    
                    session.execute(insert_sql, record_data)
                    imported_count += 1
                    
                except Exception as e:
                    logger.warning(f"Error importing P&L record: {e}")
                    continue
            
            session.commit()
            
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
                    store_id VARCHAR(10),
                    revenue DECIMAL(15,2),
                    profit DECIMAL(15,2),
                    margin DECIMAL(5,2),
                    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    import_batch VARCHAR(50),
                    INDEX idx_week_ending (week_ending),
                    INDEX idx_store_id (store_id)
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
                    store_id VARCHAR(10),
                    total_hours DECIMAL(10,2),
                    total_wages DECIMAL(15,2),
                    avg_hourly_rate DECIMAL(8,2),
                    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    import_batch VARCHAR(50),
                    INDEX idx_week_ending (week_ending),
                    INDEX idx_store_id (store_id)
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
                    import_batch VARCHAR(50),
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
