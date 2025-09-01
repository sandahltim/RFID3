"""
Financial CSV Import Service for Executive Analytics
Handles import of financial data files: ScorecardTrends, PayrollTrends, P&L, and Customer data
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import glob
import re
from sqlalchemy import text, create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, Date, Boolean, DECIMAL, TEXT, Index
from sqlalchemy.orm import sessionmaker
from app import db
from app.services.logger import get_logger
from config import DB_CONFIG

logger = get_logger(__name__)

class FinancialCSVImportService:
    """Service for importing financial CSV data files"""
    
    CSV_BASE_PATH = "/home/tim/RFID3/shared/POR"
    
    def __init__(self):
        self.logger = logger
        self.database_url = (
            f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}/{DB_CONFIG['database']}"
        )
        self.engine = create_engine(self.database_url, pool_pre_ping=True)
        self.Session = sessionmaker(bind=self.engine)
        self.metadata = MetaData()
        self.import_batch_id = None
        self.import_stats = {
            "files_processed": 0,
            "total_records_processed": 0,
            "total_records_imported": 0,
            "errors": [],
            "warnings": []
        }

    def smart_date_parser(self, date_str: str) -> pd.Timestamp:
        """Smart date parser that handles various date formats correctly"""
        if pd.isna(date_str) or date_str == '':
            return pd.NaT
        
        date_str = str(date_str).strip()
        
        try:
            # Try MM/DD/YYYY format first
            if '/' in date_str and len(date_str.split('/')[2]) == 4:
                return pd.to_datetime(date_str, format='%m/%d/%Y')
            
            # Try MM/DD/YY format - handle 2-digit years properly
            elif '/' in date_str and len(date_str.split('/')[2]) == 2:
                # Convert 2-digit year to 4-digit
                parts = date_str.split('/')
                year = int(parts[2])
                # Assume years 00-30 are 2000-2030, 31-99 are 1931-1999
                if year <= 30:
                    year += 2000
                else:
                    year += 1900
                date_str = f"{parts[0]}/{parts[1]}/{year}"
                return pd.to_datetime(date_str, format='%m/%d/%Y')
            
            # Try other common formats
            else:
                return pd.to_datetime(date_str, errors='coerce')
                
        except Exception as e:
            logger.warning(f"Date parsing failed for '{date_str}': {e}")
            return pd.NaT

    def clean_column_name(self, col_name: str) -> str:
        """Clean column name for database compatibility"""
        # Handle special cases first
        if pd.isna(col_name) or str(col_name).strip() == '':
            return 'column_unnamed'
        
        # Convert to string and clean
        clean = str(col_name).lower()
        
        # Replace special characters with underscores
        clean = re.sub(r'[^a-z0-9_]', '_', clean)
        
        # Replace multiple underscores with single
        clean = re.sub(r'_+', '_', clean)
        
        # Remove leading/trailing underscores
        clean = clean.strip('_')
        
        # Ensure it starts with a letter
        if clean and not clean[0].isalpha():
            clean = f'col_{clean}'
        
        # Truncate if too long (MySQL column name limit)
        if len(clean) > 64:
            clean = clean[:64]
        
        return clean if clean else 'column_unnamed'

    def create_import_batch(self) -> int:
        """Create new import batch record"""
        with self.Session() as session:
            try:
                result = session.execute(text("""
                    INSERT INTO import_batches (
                        import_type,
                        started_at,
                        status
                    ) VALUES (
                        'financial_csv',
                        NOW(),
                        'in_progress'
                    )
                """))
                session.commit()
                batch_id = result.lastrowid
                logger.info(f"Created import batch {batch_id}")
                return batch_id
            except Exception as e:
                logger.error(f"Failed to create import batch: {e}")
                session.rollback()
                raise

    def update_import_batch(self, batch_id: int, status: str, stats: Dict = None):
        """Update import batch status"""
        with self.Session() as session:
            try:
                if stats:
                    session.execute(text("""
                        UPDATE import_batches 
                        SET status = :status,
                            completed_at = NOW(),
                            records_processed = :records_processed,
                            records_imported = :records_imported,
                            errors = :errors
                        WHERE id = :batch_id
                    """), {
                        'status': status,
                        'batch_id': batch_id,
                        'records_processed': stats.get('total_records_processed', 0),
                        'records_imported': stats.get('total_records_imported', 0),
                        'errors': str(stats.get('errors', []))[:1000] if stats.get('errors') else None
                    })
                else:
                    session.execute(text("""
                        UPDATE import_batches 
                        SET status = :status,
                            completed_at = NOW()
                        WHERE id = :batch_id
                    """), {
                        'status': status,
                        'batch_id': batch_id
                    })
                session.commit()
            except Exception as e:
                logger.error(f"Failed to update import batch: {e}")
                session.rollback()

    def import_scorecard_trends(self, file_path: str = None) -> Dict:
        """Import ScorecardTrends data - key business metrics"""
        if not file_path:
            pattern = os.path.join(self.CSV_BASE_PATH, "ScorecardTrends*.csv")
            files = glob.glob(pattern)
            if not files:
                raise FileNotFoundError(f"No ScorecardTrends CSV files found")
            file_path = max(files, key=os.path.getctime)
            
        logger.info(f"Starting ScorecardTrends import from: {file_path}")
        
        try:
            # Read CSV - this file has MANY columns
            df = pd.read_csv(file_path, encoding='utf-8', low_memory=False)
            logger.info(f"Read {len(df)} records with {len(df.columns)} columns")
            
            # Keep only meaningful columns (first 25 plus any with real names)
            meaningful_cols = []
            for i, col in enumerate(df.columns):
                if i < 25:  # Keep first 25 columns
                    meaningful_cols.append(col)
                elif not str(col).startswith('Column') and not str(col).startswith('Unnamed'):
                    # Keep columns with real names
                    meaningful_cols.append(col)
            
            df = df[meaningful_cols]
            logger.info(f"Filtered to {len(df.columns)} meaningful columns")
            
            # Clean column names
            df.columns = [self.clean_column_name(col) for col in df.columns]
            
            # Parse dates in first column
            if 'week_ending_sunday' in df.columns:
                df['week_ending_sunday'] = df['week_ending_sunday'].apply(self.smart_date_parser)
            
            # Convert financial columns to numeric
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ['revenue', 'dollar', 'amount', 'discount', 'ar', 'reservation']):
                    # Remove $ and , from values
                    if df[col].dtype == 'object':
                        df[col] = df[col].astype(str).str.replace('$', '').str.replace(',', '')
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                elif any(keyword in col.lower() for keyword in ['number', 'count', 'contracts', 'deliveries', 'quotes']):
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                elif '%' in col:
                    # Handle percentage columns
                    if df[col].dtype == 'object':
                        df[col] = df[col].astype(str).str.replace('%', '')
                        df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Create or update table
            self._create_scorecard_table(df)
            
            # Import data
            imported_count = self._import_dataframe(df, 'pos_scorecard_trends')
            
            self.import_stats["files_processed"] += 1
            self.import_stats["total_records_processed"] += len(df)
            self.import_stats["total_records_imported"] += imported_count
            
            logger.info(f"ScorecardTrends import completed: {imported_count}/{len(df)} records")
            
            return {
                "success": True,
                "file_path": file_path,
                "total_records": len(df),
                "imported_records": imported_count,
                "columns_imported": len(df.columns)
            }
            
        except Exception as e:
            logger.error(f"ScorecardTrends import failed: {str(e)}", exc_info=True)
            self.import_stats["errors"].append(f"ScorecardTrends: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }

    def import_payroll_trends(self, file_path: str = None) -> Dict:
        """Import PayrollTrends data - payroll analytics by store"""
        if not file_path:
            pattern = os.path.join(self.CSV_BASE_PATH, "PayrollTrends*.csv")
            files = glob.glob(pattern)
            if not files:
                raise FileNotFoundError(f"No PayrollTrends CSV files found")
            file_path = max(files, key=os.path.getctime)
            
        logger.info(f"Starting PayrollTrends import from: {file_path}")
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8', low_memory=False)
            logger.info(f"Read {len(df)} records with {len(df.columns)} columns")
            
            # Clean column names
            df.columns = [self.clean_column_name(col) for col in df.columns]
            
            # Parse date column - rename for consistency
            if 'col_2_week_ending_sun' in df.columns:
                df['week_ending'] = df['col_2_week_ending_sun'].apply(self.smart_date_parser)
            elif '2_week_ending_sun' in df.columns:
                df['week_ending'] = df['2_week_ending_sun'].apply(self.smart_date_parser)
            
            # Convert numeric columns
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ['revenue', 'payroll', 'hours']):
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
            
            # Create or update table
            self._create_payroll_table(df)
            
            # Import data
            imported_count = self._import_dataframe(df, 'pos_payroll_trends')
            
            self.import_stats["files_processed"] += 1
            self.import_stats["total_records_processed"] += len(df)
            self.import_stats["total_records_imported"] += imported_count
            
            logger.info(f"PayrollTrends import completed: {imported_count}/{len(df)} records")
            
            return {
                "success": True,
                "file_path": file_path,
                "total_records": len(df),
                "imported_records": imported_count
            }
            
        except Exception as e:
            logger.error(f"PayrollTrends import failed: {str(e)}", exc_info=True)
            self.import_stats["errors"].append(f"PayrollTrends: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }

    def import_profit_loss(self, file_path: str = None) -> Dict:
        """Import P&L data - profit and loss statements"""
        if not file_path:
            pattern = os.path.join(self.CSV_BASE_PATH, "PL*.csv")
            files = glob.glob(pattern)
            if not files:
                raise FileNotFoundError(f"No P&L CSV files found")
            file_path = max(files, key=os.path.getctime)
            
        logger.info(f"Starting P&L import from: {file_path}")
        
        try:
            # P&L file has a different structure - it's more like a report
            df = pd.read_csv(file_path, encoding='utf-8', low_memory=False)
            
            # The P&L file appears to have a matrix structure
            # We need to transform it into a normalized format
            
            # Clean column names
            clean_cols = []
            for col in df.columns:
                clean_cols.append(self.clean_column_name(col))
            df.columns = clean_cols
            
            # Create normalized structure
            normalized_data = []
            
            # Process each row as an account line
            for idx, row in df.iterrows():
                # Get account name from first column
                if pd.notna(row.iloc[0]):
                    account_name = str(row.iloc[0])
                    
                    # Process monthly data columns (usually columns 2-13 for 12 months)
                    for col_idx in range(1, min(14, len(df.columns))):
                        if col_idx < len(row):
                            value = row.iloc[col_idx]
                            if pd.notna(value):
                                # Try to extract month from column name
                                col_name = df.columns[col_idx] if col_idx < len(df.columns) else f"month_{col_idx}"
                                
                                normalized_data.append({
                                    'account_line': account_name,
                                    'period': col_name,
                                    'amount': pd.to_numeric(str(value).replace('$', '').replace(',', ''), errors='coerce'),
                                    'line_number': idx + 1,
                                    'import_batch_id': self.import_batch_id
                                })
            
            # Create DataFrame from normalized data
            if normalized_data:
                df_normalized = pd.DataFrame(normalized_data)
                
                # Create or update table
                self._create_profit_loss_table(df_normalized)
                
                # Import data
                imported_count = self._import_dataframe(df_normalized, 'pos_profit_loss')
                
                self.import_stats["files_processed"] += 1
                self.import_stats["total_records_processed"] += len(df_normalized)
                self.import_stats["total_records_imported"] += imported_count
                
                logger.info(f"P&L import completed: {imported_count}/{len(df_normalized)} records")
                
                return {
                    "success": True,
                    "file_path": file_path,
                    "total_records": len(df_normalized),
                    "imported_records": imported_count,
                    "original_rows": len(df)
                }
            else:
                raise ValueError("No data could be normalized from P&L file")
            
        except Exception as e:
            logger.error(f"P&L import failed: {str(e)}", exc_info=True)
            self.import_stats["errors"].append(f"P&L: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }

    def import_customers(self, file_path: str = None) -> Dict:
        """Import customer data"""
        if not file_path:
            pattern = os.path.join(self.CSV_BASE_PATH, "customer*.csv")
            files = glob.glob(pattern)
            if not files:
                raise FileNotFoundError(f"No customer CSV files found")
            file_path = max(files, key=os.path.getctime)
            
        logger.info(f"Starting customer import from: {file_path}")
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8', low_memory=False)
            logger.info(f"Read {len(df)} customer records")
            
            # Clean column names
            df.columns = [self.clean_column_name(col) for col in df.columns]
            
            # Parse date columns
            date_columns = ['birthdate', 'open_date', 'last_active_date']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Convert numeric columns
            numeric_columns = ['credit_limit', 'ytd_payments', 'ytd_rentals', 'life_payments', 'life_rentals']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Add import batch
            df['import_batch_id'] = self.import_batch_id
            
            # Create or update table
            self._create_customers_table(df)
            
            # Import data
            imported_count = self._import_dataframe(df, 'pos_customers')
            
            self.import_stats["files_processed"] += 1
            self.import_stats["total_records_processed"] += len(df)
            self.import_stats["total_records_imported"] += imported_count
            
            logger.info(f"Customer import completed: {imported_count}/{len(df)} records")
            
            return {
                "success": True,
                "file_path": file_path,
                "total_records": len(df),
                "imported_records": imported_count
            }
            
        except Exception as e:
            logger.error(f"Customer import failed: {str(e)}", exc_info=True)
            self.import_stats["errors"].append(f"Customer: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }

    def _create_scorecard_table(self, df: pd.DataFrame):
        """Create or update scorecard trends table schema"""
        with self.Session() as session:
            try:
                # Drop existing table if needed
                session.execute(text("DROP TABLE IF EXISTS pos_scorecard_trends"))
                
                # Build CREATE TABLE statement dynamically based on DataFrame
                columns_sql = []
                columns_sql.append("id INT AUTO_INCREMENT PRIMARY KEY")
                
                for col in df.columns:
                    dtype = str(df[col].dtype)
                    
                    if 'datetime' in dtype:
                        sql_type = "DATETIME"
                    elif 'float' in dtype or any(k in col for k in ['revenue', 'amount', 'dollar', 'discount']):
                        sql_type = "DECIMAL(15,2)"
                    elif 'int' in dtype or any(k in col for k in ['number', 'count', 'week_number']):
                        sql_type = "INT"
                    elif '%' in col:
                        sql_type = "DECIMAL(5,2)"
                    else:
                        # Default to TEXT for flexibility
                        sql_type = "TEXT"
                    
                    columns_sql.append(f"`{col}` {sql_type}")
                
                columns_sql.append("import_batch_id INT")
                columns_sql.append("created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                columns_sql.append("INDEX idx_week_ending (week_ending_sunday)")
                columns_sql.append("INDEX idx_batch (import_batch_id)")
                
                create_sql = f"""
                    CREATE TABLE pos_scorecard_trends (
                        {', '.join(columns_sql)}
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
                
                session.execute(text(create_sql))
                session.commit()
                logger.info("Created pos_scorecard_trends table")
                
            except Exception as e:
                logger.error(f"Failed to create scorecard table: {e}")
                session.rollback()
                raise

    def _create_payroll_table(self, df: pd.DataFrame):
        """Create or update payroll trends table schema"""
        with self.Session() as session:
            try:
                session.execute(text("DROP TABLE IF EXISTS pos_payroll_trends"))
                
                columns_sql = []
                columns_sql.append("id INT AUTO_INCREMENT PRIMARY KEY")
                
                for col in df.columns:
                    dtype = str(df[col].dtype)
                    
                    if 'datetime' in dtype or 'ending' in col:
                        sql_type = "DATE"
                    elif 'float' in dtype or any(k in col for k in ['revenue', 'payroll']):
                        sql_type = "DECIMAL(12,2)"
                    elif 'int' in dtype or 'hours' in col:
                        sql_type = "INT"
                    else:
                        sql_type = "VARCHAR(255)"
                    
                    columns_sql.append(f"`{col}` {sql_type}")
                
                columns_sql.append("import_batch_id INT")
                columns_sql.append("created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                
                # Only add week_ending index if the column exists
                if 'week_ending' in df.columns:
                    columns_sql.append("INDEX idx_week (week_ending)")
                columns_sql.append("INDEX idx_batch (import_batch_id)")
                
                create_sql = f"""
                    CREATE TABLE pos_payroll_trends (
                        {', '.join(columns_sql)}
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
                
                session.execute(text(create_sql))
                session.commit()
                logger.info("Created pos_payroll_trends table")
                
            except Exception as e:
                logger.error(f"Failed to create payroll table: {e}")
                session.rollback()
                raise

    def _create_profit_loss_table(self, df: pd.DataFrame):
        """Create or update profit/loss table schema"""
        with self.Session() as session:
            try:
                session.execute(text("DROP TABLE IF EXISTS pos_profit_loss"))
                
                create_sql = """
                    CREATE TABLE pos_profit_loss (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        account_line VARCHAR(255),
                        period VARCHAR(100),
                        amount DECIMAL(15,2),
                        line_number INT,
                        import_batch_id INT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_account (account_line),
                        INDEX idx_period (period),
                        INDEX idx_batch (import_batch_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
                
                session.execute(text(create_sql))
                session.commit()
                logger.info("Created pos_profit_loss table")
                
            except Exception as e:
                logger.error(f"Failed to create P&L table: {e}")
                session.rollback()
                raise

    def _create_customers_table(self, df: pd.DataFrame):
        """Create or update customers table schema"""
        with self.Session() as session:
            try:
                session.execute(text("DROP TABLE IF EXISTS pos_customers"))
                
                columns_sql = []
                columns_sql.append("id INT AUTO_INCREMENT PRIMARY KEY")
                
                # Skip if import_batch_id is already in the DataFrame columns
                skip_import_batch = 'import_batch_id' in df.columns
                
                for col in df.columns:
                    # Skip duplicate import_batch_id
                    if skip_import_batch and col == 'import_batch_id':
                        continue
                        
                    dtype = str(df[col].dtype)
                    
                    if col == 'cnum':
                        sql_type = "VARCHAR(50) UNIQUE"
                    elif col in ['key', 'zip', 'zip4']:
                        sql_type = "VARCHAR(20)"
                    elif 'datetime' in dtype or 'date' in col:
                        sql_type = "DATE"
                    elif 'float' in dtype or any(k in col for k in ['limit', 'payment', 'rental']):
                        sql_type = "DECIMAL(12,2)"
                    elif col in ['name', 'address', 'employer', 'email']:
                        sql_type = "VARCHAR(255)"
                    elif col in ['notes', 'comments']:
                        sql_type = "TEXT"
                    else:
                        sql_type = "VARCHAR(255)"
                    
                    columns_sql.append(f"`{col}` {sql_type}")
                
                # Always add import_batch_id column
                columns_sql.append("import_batch_id INT")
                    
                columns_sql.append("created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                columns_sql.append("INDEX idx_cnum (cnum)")
                columns_sql.append("INDEX idx_name (name)")
                columns_sql.append("INDEX idx_batch (import_batch_id)")
                
                create_sql = f"""
                    CREATE TABLE pos_customers (
                        {', '.join(columns_sql)}
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
                
                session.execute(text(create_sql))
                session.commit()
                logger.info("Created pos_customers table")
                
            except Exception as e:
                logger.error(f"Failed to create customers table: {e}")
                session.rollback()
                raise

    def _import_dataframe(self, df: pd.DataFrame, table_name: str) -> int:
        """Import DataFrame to database table"""
        imported_count = 0
        batch_size = 1000
        
        # Add import batch ID if not present
        if 'import_batch_id' not in df.columns:
            df['import_batch_id'] = self.import_batch_id
        
        with self.Session() as session:
            try:
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i+batch_size]
                    
                    # Convert DataFrame to dict records
                    records = batch.replace({np.nan: None}).to_dict('records')
                    
                    if records:
                        # Build INSERT statement
                        columns = list(records[0].keys())
                        placeholders = ', '.join([f":{col}" for col in columns])
                        columns_str = ', '.join([f"`{col}`" for col in columns])
                        
                        insert_sql = f"""
                            INSERT INTO {table_name} ({columns_str})
                            VALUES ({placeholders})
                        """
                        
                        # Execute batch insert
                        for record in records:
                            try:
                                session.execute(text(insert_sql), record)
                                imported_count += 1
                            except Exception as e:
                                logger.warning(f"Failed to import record: {e}")
                                self.import_stats["warnings"].append(str(e)[:100])
                    
                    # Commit batch
                    session.commit()
                    
                    if (i + batch_size) % 5000 == 0:
                        logger.info(f"Imported {imported_count} records to {table_name}...")
                
                logger.info(f"Total imported to {table_name}: {imported_count} records")
                
            except Exception as e:
                logger.error(f"Import failed for {table_name}: {e}")
                session.rollback()
                raise
        
        return imported_count

    def import_all_financial_files(self) -> Dict:
        """Import all financial CSV files in sequence"""
        logger.info("Starting comprehensive financial data import")
        
        # Create import batch
        self.import_batch_id = self.create_import_batch()
        
        results = {}
        
        # Import each file type
        file_imports = [
            ('customers', self.import_customers),
            ('scorecard_trends', self.import_scorecard_trends),
            ('payroll_trends', self.import_payroll_trends),
            ('profit_loss', self.import_profit_loss)
        ]
        
        for name, import_func in file_imports:
            logger.info(f"Importing {name}...")
            try:
                result = import_func()
                results[name] = result
                
                if not result.get('success'):
                    logger.error(f"Failed to import {name}: {result.get('error')}")
            except Exception as e:
                logger.error(f"Exception importing {name}: {e}")
                results[name] = {
                    'success': False,
                    'error': str(e)
                }
        
        # Update batch status
        all_success = all(r.get('success', False) for r in results.values())
        self.update_import_batch(
            self.import_batch_id,
            'completed' if all_success else 'failed',
            self.import_stats
        )
        
        # Generate summary
        summary = {
            'batch_id': self.import_batch_id,
            'overall_success': all_success,
            'files_processed': self.import_stats['files_processed'],
            'total_records_processed': self.import_stats['total_records_processed'],
            'total_records_imported': self.import_stats['total_records_imported'],
            'results': results,
            'errors': self.import_stats['errors'],
            'warnings': self.import_stats['warnings'][:10] if self.import_stats['warnings'] else []
        }
        
        logger.info(f"Financial import completed. Success: {all_success}")
        logger.info(f"Summary: {self.import_stats['files_processed']} files, "
                   f"{self.import_stats['total_records_imported']}/{self.import_stats['total_records_processed']} records imported")
        
        return summary

    def verify_import(self) -> Dict:
        """Verify imported data by checking record counts"""
        verification = {}
        
        with self.Session() as session:
            tables = [
                'pos_customers',
                'pos_scorecard_trends', 
                'pos_payroll_trends',
                'pos_profit_loss'
            ]
            
            for table in tables:
                try:
                    result = session.execute(text(f"SELECT COUNT(*) as count FROM {table}"))
                    count = result.fetchone()[0]
                    
                    # Get sample records
                    sample_result = session.execute(text(f"SELECT * FROM {table} LIMIT 3"))
                    samples = [dict(row._mapping) for row in sample_result]
                    
                    verification[table] = {
                        'record_count': count,
                        'exists': True,
                        'sample_records': samples
                    }
                except Exception as e:
                    verification[table] = {
                        'exists': False,
                        'error': str(e)
                    }
        
        return verification