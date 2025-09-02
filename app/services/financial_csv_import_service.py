"""
Enhanced Financial CSV Import Service for Executive Analytics
Handles Excel CSV export quirks and complex parsing challenges
Includes robust currency, percentage, and quoted field parsing
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
    """Enhanced service for importing financial CSV data files with Excel export handling"""
    
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
            "warnings": [],
            "parsing_issues": []
        }

    def robust_excel_csv_parser(self, file_path: str, parse_dates: bool = True) -> pd.DataFrame:
        """Enhanced CSV parser that handles Excel export quirks properly"""
        logger.info(f"Parsing Excel CSV file: {file_path}")
        
        try:
            # Read CSV with proper quoting handling for Excel exports
            df = pd.read_csv(
                file_path,
                encoding='utf-8',
                low_memory=False,
                quotechar='"',  # Excel uses double quotes
                skipinitialspace=True,  # Handle spaces after commas
                na_values=['', 'NULL', 'null', 'N/A', 'n/a', '#N/A'],
                keep_default_na=True,
                dtype=str  # Read everything as string first for custom parsing
            )
            
            # Log original structure
            logger.info(f"Raw CSV: {len(df)} rows, {len(df.columns)} columns")
            logger.info(f"Column headers: {list(df.columns[:10])}...")  # First 10 headers
            
            # Clean headers - remove leading/trailing spaces
            original_headers = df.columns.tolist()
            cleaned_headers = [str(col).strip() for col in df.columns]
            df.columns = cleaned_headers
            
            # Log header cleaning
            header_changes = []
            for orig, clean in zip(original_headers, cleaned_headers):
                if str(orig) != clean:
                    header_changes.append(f"'{orig}' -> '{clean}'")
            
            if header_changes:
                logger.info(f"Header cleaning: {len(header_changes)} headers cleaned")
                for change in header_changes[:5]:  # Log first 5 changes
                    logger.debug(f"Header change: {change}")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to parse Excel CSV {file_path}: {e}")
            raise

    def aggressive_currency_cleaner(self, value: str) -> Optional[float]:
        """Aggressively clean currency values from Excel CSV exports"""
        if pd.isna(value) or value is None:
            return None
            
        # Convert to string and strip spaces
        clean_val = str(value).strip()
        
        # Handle empty or dash values
        if clean_val in ['', '-', '$-', '$ -', ' ', 'nan', 'NaN', 'NULL']:
            return 0.0
        
        # Handle percentage values - these should not be processed as currency
        if '%' in clean_val:
            logger.debug(f"Percentage value found in currency field: '{value}'")
            return None
        
        # Remove quotes first - Excel exports often have quoted values like '" $118,244 "'
        clean_val = clean_val.strip('"').strip("'").strip()
        
        # Remove currency symbols and formatting
        # Handle patterns like: " $118,244 ", "$118,244", "$-", "118244"
        clean_val = clean_val.replace('$', '').replace(',', '').replace(' ', '')
        
        # Handle parentheses as negative (accounting format)
        if clean_val.startswith('(') and clean_val.endswith(')'):
            clean_val = '-' + clean_val[1:-1]
        
        # Try to convert to float
        try:
            return float(clean_val) if clean_val else 0.0
        except (ValueError, TypeError):
            logger.warning(f"Could not parse currency value: '{value}' -> '{clean_val}'")
            self.import_stats["parsing_issues"].append(f"Currency parse failed: '{value}'")
            return None

    def aggressive_percentage_cleaner(self, value: str) -> Optional[float]:
        """Clean percentage values from Excel CSV exports"""
        if pd.isna(value) or value is None:
            return None
            
        clean_val = str(value).strip()
        
        # Handle empty values
        if clean_val in ['', '-', ' ', 'nan', 'NaN', 'NULL']:
            return None
        
        # Remove % symbol and convert
        clean_val = clean_val.replace('%', '').replace(' ', '')
        
        try:
            # Convert to decimal (10% -> 0.10)
            return float(clean_val) / 100.0 if clean_val else None
        except (ValueError, TypeError):
            logger.warning(f"Could not parse percentage value: '{value}' -> '{clean_val}'")
            self.import_stats["parsing_issues"].append(f"Percentage parse failed: '{value}'")
            return None

    def aggressive_numeric_cleaner(self, value: str) -> Optional[float]:
        """Clean numeric values including counts and integers"""
        if pd.isna(value) or value is None:
            return None
            
        clean_val = str(value).strip()
        
        # Handle empty values
        if clean_val in ['', '-', ' ', 'nan', 'NaN', 'NULL']:
            return None
        
        # Remove commas from numbers
        clean_val = clean_val.replace(',', '')
        
        try:
            return float(clean_val) if clean_val else None
        except (ValueError, TypeError):
            logger.warning(f"Could not parse numeric value: '{value}' -> '{clean_val}'")
            self.import_stats["parsing_issues"].append(f"Numeric parse failed: '{value}'")
            return None

    def enhanced_column_name_cleaner(self, col_name: str) -> str:
        """Enhanced column name cleaning with correct UI column mapping"""
        if pd.isna(col_name) or str(col_name).strip() == '':
            return 'column_unnamed'
        
        # Convert to string and trim
        original = str(col_name).strip()
        clean = original.lower()
        
        # Handle specific column mappings first - these are exact matches for expected UI format
        exact_mappings = {
            # Date column
            'week ending sunday': 'week_ending',
            
            # Revenue columns - map to revenue_XXXX format
            '3607 revenue': 'revenue_3607',
            '6800 revenue': 'revenue_6800',
            '728 revenue': 'revenue_728',
            '8101 revenue': 'revenue_8101',
            
            # Reservation columns - Next 14 days
            '$ on reservation - next 14 days - 3607': 'reservation_next14_3607',
            '$ on reservation - next 14 days - 6800': 'reservation_next14_6800',
            '$ on reservation - next 14 days - 728': 'reservation_next14_728',
            '$ on reservation - next 14 days - 8101': 'reservation_next14_8101',
            
            # Total reservation columns
            'total $ on reservation 3607': 'total_reservation_3607',
            'total $ on reservation 6800': 'total_reservation_6800',
            'total $ on reservation 728': 'total_reservation_728',
            'total $ on reservation 8101': 'total_reservation_8101',
            
            # Financial health columns
            '% -total ar ($) > 45 days': 'ar_over_45_days_percent',
            'total discount $ company wide': 'total_discount',
            
            # Contract columns - UI expects new_contracts_XXXX format
            '# new open contracts 3607': 'new_contracts_3607',
            '# new open contracts 6800': 'new_contracts_6800', 
            '# new open contracts 728': 'new_contracts_728',
            '# new open contracts 8101': 'new_contracts_8101',
            
            # Deliveries - UI expects shorter name
            '# deliveries scheduled next 7 days weds-tues 8101': 'deliveries_scheduled_8101'
        }
        
        # Check for exact mapping first
        if clean in exact_mappings:
            logger.debug(f"Exact mapping: '{original}' -> '{exact_mappings[clean]}'")
            return exact_mappings[clean]
        
        # Handle general cleaning for other columns
        # Replace multiple spaces with single space
        clean = re.sub(r'\s+', ' ', clean)
        
        # Replace special characters and spaces with underscores
        clean = re.sub(r'[^a-z0-9_]', '_', clean)
        
        # Replace multiple underscores with single
        clean = re.sub(r'_+', '_', clean)
        
        # Clean up leading/trailing underscores
        clean = clean.strip('_')
        
        # Ensure it starts with a letter
        if clean and not clean[0].isalpha():
            clean = f'col_{clean}'
        
        # Additional pattern-based mappings for other store-related columns
        pattern_mappings = {
            'new_open_contracts_3607': 'contracts_3607',
            'new_open_contracts_6800': 'contracts_6800',
            'new_open_contracts_728': 'contracts_728',
            'new_open_contracts_8101': 'contracts_8101'
        }
        
        for pattern, replacement in pattern_mappings.items():
            if pattern in clean:
                clean = clean.replace(pattern, replacement)
        
        # Truncate if too long
        if len(clean) > 64:
            clean = clean[:64]
        
        return clean if clean else 'column_unnamed'

    def smart_date_parser(self, date_str: str) -> pd.Timestamp:
        """Enhanced date parser that handles various formats including Excel serial numbers"""
        if pd.isna(date_str) or date_str == '' or date_str is None:
            return pd.NaT
        
        date_str = str(date_str).strip()
        
        try:
            # Check if this is an Excel serial number (numeric string like "44577")
            if date_str.isdigit() and len(date_str) >= 4:
                excel_serial = int(date_str)
                # Excel serial numbers start from 1900-01-01 (serial 1)
                # but Excel incorrectly treats 1900 as a leap year, so we need to adjust
                if 1 <= excel_serial <= 100000:  # Reasonable range for dates
                    # Convert Excel serial to datetime
                    # Excel epoch is 1900-01-01, but we need to account for Excel's leap year bug
                    from datetime import datetime, timedelta
                    excel_epoch = datetime(1899, 12, 30)  # Adjusted for Excel's bug
                    parsed_date = excel_epoch + timedelta(days=excel_serial)
                    logger.debug(f"Converted Excel serial {excel_serial} to {parsed_date.strftime('%Y-%m-%d')}")
                    return pd.Timestamp(parsed_date)
            
            # Try MM/DD/YYYY format
            if '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3:
                    if len(parts[2]) == 4:
                        return pd.to_datetime(date_str, format='%m/%d/%Y')
                    elif len(parts[2]) == 2:
                        # Convert 2-digit year to 4-digit
                        year = int(parts[2])
                        if year <= 30:
                            year += 2000
                        else:
                            year += 1900
                        date_str = f"{parts[0]}/{parts[1]}/{year}"
                        return pd.to_datetime(date_str, format='%m/%d/%Y')
            
            # Try other common formats
            return pd.to_datetime(date_str, errors='coerce')
                
        except Exception as e:
            logger.warning(f"Date parsing failed for '{date_str}': {e}")
            return pd.NaT

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
                        'financial_csv_enhanced',
                        NOW(),
                        'in_progress'
                    )
                """))
                session.commit()
                batch_id = result.lastrowid
                logger.info(f"Created enhanced import batch {batch_id}")
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
        """Enhanced ScorecardTrends import with comprehensive Excel CSV parsing"""
        if not file_path:
            pattern = os.path.join(self.CSV_BASE_PATH, "ScorecardTrends*.csv")
            files = glob.glob(pattern)
            if not files:
                raise FileNotFoundError(f"No ScorecardTrends CSV files found")
            file_path = max(files, key=os.path.getctime)
            
        logger.info(f"Starting enhanced ScorecardTrends import from: {file_path}")
        
        try:
            # Use enhanced parser
            df = self.robust_excel_csv_parser(file_path)
            
            # Log raw sample for debugging
            if len(df) > 0:
                sample_row = df.iloc[0].to_dict()
                logger.info("Raw first row sample:")
                for col, val in list(sample_row.items())[:10]:
                    logger.info(f"  '{col}': '{val}'")
            
            # Filter meaningful columns (first 25 or named columns)
            meaningful_cols = []
            for i, col in enumerate(df.columns):
                if i < 25:
                    meaningful_cols.append(col)
                elif not str(col).startswith('Column') and not str(col).startswith('Unnamed'):
                    meaningful_cols.append(col)
            
            df = df[meaningful_cols]
            logger.info(f"Filtered to {len(df.columns)} meaningful columns")
            
            # Clean column names with enhanced cleaner
            original_cols = df.columns.tolist()
            df.columns = [self.enhanced_column_name_cleaner(col) for col in df.columns]
            
            # Log column name mapping
            col_mapping = {}
            for orig, clean in zip(original_cols, df.columns):
                if orig != clean:
                    col_mapping[orig] = clean
            
            if col_mapping:
                logger.info(f"Column mapping applied: {len(col_mapping)} columns renamed")
                for orig, clean in list(col_mapping.items())[:5]:
                    logger.info(f"  '{orig}' -> '{clean}'")
            
            # Parse dates in first column
            date_col = df.columns[0]
            if 'week' in date_col.lower() or 'date' in date_col.lower():
                logger.info(f"Parsing dates in column: {date_col}")
                df[date_col] = df[date_col].apply(self.smart_date_parser)
                non_null_dates = df[date_col].notna().sum()
                logger.info(f"Successfully parsed {non_null_dates}/{len(df)} dates")
            
            # Enhanced data type conversion with comprehensive logging
            conversion_stats = {
                'currency_columns': [],
                'percentage_columns': [],
                'numeric_columns': [],
                'conversion_issues': 0
            }
            
            for col in df.columns:
                col_lower = col.lower()
                original_non_null = df[col].notna().sum()
                
                # Percentage columns (check first to avoid currency processing)
                if '%' in col or 'percent' in col_lower or 'total_ar_45_days' in col_lower:
                    logger.info(f"Processing percentage column: {col}")
                    conversion_stats['percentage_columns'].append(col)
                    
                    cleaned_values = df[col].apply(self.aggressive_percentage_cleaner)
                    df[col] = cleaned_values
                    
                    new_non_null = df[col].notna().sum()
                    logger.info(f"  Percentage conversion: {original_non_null} -> {new_non_null} valid values")
                
                # Currency columns (excluding percentage columns)
                elif any(keyword in col_lower for keyword in ['revenue', 'dollar', 'amount', 'discount', 'reservation']) and 'total_ar_45_days' not in col_lower:
                    logger.info(f"Processing currency column: {col}")
                    conversion_stats['currency_columns'].append(col)
                    
                    # Apply aggressive currency cleaning
                    cleaned_values = df[col].apply(self.aggressive_currency_cleaner)
                    df[col] = cleaned_values
                    
                    new_non_null = df[col].notna().sum()
                    logger.info(f"  Currency conversion: {original_non_null} -> {new_non_null} valid values")
                    
                    # Log sample conversions
                    if original_non_null > 0:
                        sample_orig = df[col].iloc[:3].tolist() if len(df) > 0 else []
                        logger.debug(f"  Sample values: {sample_orig}")
                

                
                # Numeric columns (counts, numbers, etc.)
                elif any(keyword in col_lower for keyword in ['number', 'count', 'contracts', 'deliveries', 'quotes', 'week_number']):
                    logger.info(f"Processing numeric column: {col}")
                    conversion_stats['numeric_columns'].append(col)
                    
                    cleaned_values = df[col].apply(self.aggressive_numeric_cleaner)
                    df[col] = cleaned_values
                    
                    new_non_null = df[col].notna().sum()
                    logger.info(f"  Numeric conversion: {original_non_null} -> {new_non_null} valid values")
            
            # Log conversion summary
            logger.info("Data conversion summary:")
            logger.info(f"  Currency columns: {len(conversion_stats['currency_columns'])}")
            logger.info(f"  Percentage columns: {len(conversion_stats['percentage_columns'])}")  
            logger.info(f"  Numeric columns: {len(conversion_stats['numeric_columns'])}")
            logger.info(f"  Parsing issues: {len(self.import_stats['parsing_issues'])}")
            
            # Check for store-specific revenue data
            store_revenue_cols = [col for col in df.columns if 'store' in col and 'revenue' in col]
            if store_revenue_cols:
                logger.info(f"Found store-specific revenue columns: {store_revenue_cols}")
                for col in store_revenue_cols:
                    non_null_count = df[col].notna().sum()
                    non_zero_count = (df[col] != 0).sum() if df[col].notna().any() else 0
                    logger.info(f"  {col}: {non_null_count} non-null, {non_zero_count} non-zero values")
            
            # Create or update table
            self._create_enhanced_scorecard_table(df)
            
            # Import data
            imported_count = self._import_dataframe(df, 'scorecard_trends_data')
            
            self.import_stats["files_processed"] += 1
            self.import_stats["total_records_processed"] += len(df)
            self.import_stats["total_records_imported"] += imported_count
            
            logger.info(f"Enhanced ScorecardTrends import completed: {imported_count}/{len(df)} records")
            
            return {
                "success": True,
                "file_path": file_path,
                "total_records": len(df),
                "imported_records": imported_count,
                "columns_imported": len(df.columns),
                "conversion_stats": conversion_stats,
                "parsing_issues": len(self.import_stats["parsing_issues"])
            }
            
        except Exception as e:
            logger.error(f"Enhanced ScorecardTrends import failed: {str(e)}", exc_info=True)
            self.import_stats["errors"].append(f"ScorecardTrends: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }

    def import_payroll_trends(self, file_path: str = None) -> Dict:
        """Enhanced PayrollTrends import with Excel CSV parsing"""
        if not file_path:
            pattern = os.path.join(self.CSV_BASE_PATH, "PayrollTrends*.csv")
            files = glob.glob(pattern)
            if not files:
                raise FileNotFoundError(f"No PayrollTrends CSV files found")
            file_path = max(files, key=os.path.getctime)
            
        logger.info(f"Starting enhanced PayrollTrends import from: {file_path}")
        
        try:
            df = self.robust_excel_csv_parser(file_path)
            logger.info(f"Read {len(df)} records with {len(df.columns)} columns")
            
            # Clean column names
            df.columns = [self.enhanced_column_name_cleaner(col) for col in df.columns]
            
            # Parse date column
            date_cols = [col for col in df.columns if 'week' in col.lower() and 'ending' in col.lower()]
            if date_cols:
                date_col = date_cols[0]
                df['week_ending'] = df[date_col].apply(self.smart_date_parser)
                logger.info(f"Parsed dates from column: {date_col}")
            
            # Convert numeric columns with enhanced cleaning
            for col in df.columns:
                if any(keyword in col.lower() for keyword in ['revenue', 'payroll']):
                    df[col] = df[col].apply(self.aggressive_currency_cleaner)
                elif 'hours' in col.lower():
                    df[col] = df[col].apply(self.aggressive_numeric_cleaner)
            
            # Create or update table
            self._create_enhanced_payroll_table(df)
            
            # Import data
            imported_count = self._import_dataframe(df, 'pos_payroll_trends')
            
            self.import_stats["files_processed"] += 1
            self.import_stats["total_records_processed"] += len(df)
            self.import_stats["total_records_imported"] += imported_count
            
            logger.info(f"Enhanced PayrollTrends import completed: {imported_count}/{len(df)} records")
            
            return {
                "success": True,
                "file_path": file_path,
                "total_records": len(df),
                "imported_records": imported_count
            }
            
        except Exception as e:
            logger.error(f"Enhanced PayrollTrends import failed: {str(e)}", exc_info=True)
            self.import_stats["errors"].append(f"PayrollTrends: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }

    def import_profit_loss(self, file_path: str = None) -> Dict:
        """Enhanced P&L import - profit and loss statements"""
        if not file_path:
            pattern = os.path.join(self.CSV_BASE_PATH, "PL*.csv")
            files = glob.glob(pattern)
            if not files:
                raise FileNotFoundError(f"No P&L CSV files found")
            file_path = max(files, key=os.path.getctime)
            
        logger.info(f"Starting enhanced P&L import from: {file_path}")
        
        try:
            df = self.robust_excel_csv_parser(file_path)
            
            # Clean column names
            clean_cols = [self.enhanced_column_name_cleaner(col) for col in df.columns]
            df.columns = clean_cols
            
            # Create normalized structure
            normalized_data = []
            
            # Process each row as an account line
            for idx, row in df.iterrows():
                if pd.notna(row.iloc[0]):
                    account_name = str(row.iloc[0])
                    
                    # Process monthly data columns
                    for col_idx in range(1, min(14, len(df.columns))):
                        if col_idx < len(row):
                            value = row.iloc[col_idx]
                            if pd.notna(value):
                                col_name = df.columns[col_idx] if col_idx < len(df.columns) else f"month_{col_idx}"
                                
                                # Use enhanced currency cleaner
                                cleaned_amount = self.aggressive_currency_cleaner(value)
                                
                                normalized_data.append({
                                    'account_line': account_name,
                                    'period': col_name,
                                    'amount': cleaned_amount,
                                    'line_number': idx + 1,
                                    'import_batch_id': self.import_batch_id
                                })
            
            if normalized_data:
                df_normalized = pd.DataFrame(normalized_data)
                
                # Create or update table
                self._create_profit_loss_table(df_normalized)
                
                # Import data
                imported_count = self._import_dataframe(df_normalized, 'pos_profit_loss')
                
                self.import_stats["files_processed"] += 1
                self.import_stats["total_records_processed"] += len(df_normalized)
                self.import_stats["total_records_imported"] += imported_count
                
                logger.info(f"Enhanced P&L import completed: {imported_count}/{len(df_normalized)} records")
                
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
            logger.error(f"Enhanced P&L import failed: {str(e)}", exc_info=True)
            self.import_stats["errors"].append(f"P&L: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }

    def import_customers(self, file_path: str = None) -> Dict:
        """Enhanced customer import"""
        if not file_path:
            pattern = os.path.join(self.CSV_BASE_PATH, "customer*.csv")
            files = glob.glob(pattern)
            if not files:
                raise FileNotFoundError(f"No customer CSV files found")
            file_path = max(files, key=os.path.getctime)
            
        logger.info(f"Starting enhanced customer import from: {file_path}")
        
        try:
            df = self.robust_excel_csv_parser(file_path)
            logger.info(f"Read {len(df)} customer records")
            
            # Clean column names
            df.columns = [self.enhanced_column_name_cleaner(col) for col in df.columns]
            
            # Parse date columns
            date_columns = ['birthdate', 'open_date', 'last_active_date']
            for col in date_columns:
                if col in df.columns:
                    df[col] = df[col].apply(self.smart_date_parser)
            
            # Convert numeric columns with enhanced cleaning
            numeric_columns = ['credit_limit', 'ytd_payments', 'ytd_rentals', 'life_payments', 'life_rentals']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = df[col].apply(self.aggressive_currency_cleaner)
            
            # Add import batch
            df['import_batch_id'] = self.import_batch_id
            
            # Create or update table
            self._create_customers_table(df)
            
            # Import data
            imported_count = self._import_dataframe(df, 'pos_customers')
            
            self.import_stats["files_processed"] += 1
            self.import_stats["total_records_processed"] += len(df)
            self.import_stats["total_records_imported"] += imported_count
            
            logger.info(f"Enhanced customer import completed: {imported_count}/{len(df)} records")
            
            return {
                "success": True,
                "file_path": file_path,
                "total_records": len(df),
                "imported_records": imported_count
            }
            
        except Exception as e:
            logger.error(f"Enhanced customer import failed: {str(e)}", exc_info=True)
            self.import_stats["errors"].append(f"Customer: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }

    def _create_enhanced_scorecard_table(self, df: pd.DataFrame):
        """Create enhanced scorecard trends table with correct UI column mapping support"""
        with self.Session() as session:
            try:
                # Drop existing table
                session.execute(text("DROP TABLE IF EXISTS scorecard_trends_data"))
                
                # Build CREATE TABLE statement
                columns_sql = []
                columns_sql.append("id INT AUTO_INCREMENT PRIMARY KEY")
                
                for col in df.columns:
                    dtype = str(df[col].dtype)
                    col_lower = col.lower()
                    
                    # Date/datetime columns - be very specific
                    if col_lower == 'week_ending' or col_lower == 'week_ending_sunday' or 'datetime' in dtype:
                        sql_type = "DATETIME"
                    # Revenue columns - specific UI format (revenue_XXXX)
                    elif col_lower.startswith('revenue_') and any(store in col_lower for store in ['3607', '6800', '728', '8101']):
                        sql_type = "DECIMAL(15,2)"
                    # Reservation columns
                    elif any(keyword in col_lower for keyword in ['reservation_next14_', 'total_reservation_']):
                        sql_type = "DECIMAL(15,2)"
                    # Financial health columns
                    elif col_lower in ['ar_over_45_days_percent']:
                        sql_type = "DECIMAL(8,4)"  # Support 4 decimal places for percentages
                    elif col_lower in ['total_discount']:
                        sql_type = "DECIMAL(15,2)"
                    # General revenue and currency columns
                    elif 'revenue' in col_lower or 'dollar' in col_lower or 'amount' in col_lower or 'discount' in col_lower or 'reservation' in col_lower:
                        sql_type = "DECIMAL(15,2)"
                    # Percentage columns
                    elif '%' in col or 'percent' in col_lower or col_lower == 'total_ar_45_days':
                        sql_type = "DECIMAL(8,4)"  # Support 4 decimal places for percentages
                    # Integer columns  
                    elif any(k in col_lower for k in ['number', 'count', 'contracts', 'deliveries', 'quotes', 'week_number', 'new_contracts']):
                        sql_type = "INT"
                    else:
                        sql_type = "TEXT"
                    
                    columns_sql.append(f"`{col}` {sql_type}")
                
                columns_sql.append("import_batch_id INT")
                columns_sql.append("created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                
                # Add indexes
                if any('week' in col.lower() for col in df.columns):
                    week_col = next(col for col in df.columns if 'week' in col.lower())
                    columns_sql.append(f"INDEX idx_week (`{week_col}`)")
                
                columns_sql.append("INDEX idx_batch (import_batch_id)")
                
                # Add revenue-specific indexes for the UI format
                revenue_cols = [col for col in df.columns if col.lower().startswith('revenue_')]
                for revenue_col in revenue_cols[:4]:  # Index the 4 store revenue columns
                    clean_name = revenue_col.replace('_', '')
                    columns_sql.append(f"INDEX idx_{clean_name} (`{revenue_col}`)")
                
                # Add reservation indexes
                reservation_cols = [col for col in df.columns if 'reservation' in col.lower()]
                for res_col in reservation_cols[:4]:  # Limit to avoid too many indexes
                    clean_name = res_col.replace('_', '')[:20]  # Limit name length
                    columns_sql.append(f"INDEX idx_{clean_name} (`{res_col}`)")
                
                create_sql = f"""
                    CREATE TABLE scorecard_trends_data (
                        {', '.join(columns_sql)}
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
                
                session.execute(text(create_sql))
                session.commit()
                logger.info("Created enhanced scorecard_trends_data table with UI column mapping support")
                
            except Exception as e:
                logger.error(f"Failed to create enhanced scorecard table: {e}")
                session.rollback()
                raise

    def _create_enhanced_payroll_table(self, df: pd.DataFrame):
        """Create enhanced payroll trends table"""
        with self.Session() as session:
            try:
                session.execute(text("DROP TABLE IF EXISTS pos_payroll_trends"))
                
                columns_sql = []
                columns_sql.append("id INT AUTO_INCREMENT PRIMARY KEY")
                
                for col in df.columns:
                    dtype = str(df[col].dtype)
                    col_lower = col.lower()
                    
                    if 'datetime' in dtype or 'ending' in col_lower:
                        sql_type = "DATE"
                    elif 'revenue' in col_lower or 'payroll' in col_lower:
                        sql_type = "DECIMAL(12,2)"
                    elif 'hours' in col_lower:
                        sql_type = "DECIMAL(8,2)"  # Support fractional hours
                    else:
                        sql_type = "VARCHAR(255)"
                    
                    columns_sql.append(f"`{col}` {sql_type}")
                
                columns_sql.append("import_batch_id INT")
                columns_sql.append("created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                
                # Add indexes
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
                logger.info("Created enhanced pos_payroll_trends table")
                
            except Exception as e:
                logger.error(f"Failed to create enhanced payroll table: {e}")
                session.rollback()
                raise

    def _create_profit_loss_table(self, df: pd.DataFrame):
        """Create profit/loss table schema"""
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
        """Create customers table schema"""
        with self.Session() as session:
            try:
                session.execute(text("DROP TABLE IF EXISTS pos_customers"))
                
                columns_sql = []
                columns_sql.append("id INT AUTO_INCREMENT PRIMARY KEY")
                
                skip_import_batch = 'import_batch_id' in df.columns
                
                for col in df.columns:
                    if skip_import_batch and col == 'import_batch_id':
                        continue
                        
                    dtype = str(df[col].dtype)
                    col_lower = col.lower()
                    
                    if col == 'cnum':
                        sql_type = "VARCHAR(50) UNIQUE"
                    elif col in ['key', 'zip', 'zip4']:
                        sql_type = "VARCHAR(20)"
                    elif 'datetime' in dtype or 'date' in col_lower:
                        sql_type = "DATE"
                    elif any(k in col_lower for k in ['limit', 'payment', 'rental']):
                        sql_type = "DECIMAL(12,2)"
                    elif col in ['name', 'address', 'employer', 'email']:
                        sql_type = "VARCHAR(255)"
                    elif col in ['notes', 'comments']:
                        sql_type = "TEXT"
                    else:
                        sql_type = "VARCHAR(255)"
                    
                    columns_sql.append(f"`{col}` {sql_type}")
                
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
        """Import DataFrame to database table with enhanced error handling"""
        imported_count = 0
        batch_size = 1000
        
        # Add import batch ID if not present
        if 'import_batch_id' not in df.columns:
            df['import_batch_id'] = self.import_batch_id
        
        with self.Session() as session:
            try:
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i+batch_size]
                    
                    # Convert DataFrame to dict records, handling NaN/None properly
                    records = batch.replace({np.nan: None, 'nan': None, 'NaN': None}).to_dict('records')
                    
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
                        batch_errors = 0
                        for record in records:
                            try:
                                session.execute(text(insert_sql), record)
                                imported_count += 1
                            except Exception as e:
                                batch_errors += 1
                                if batch_errors <= 5:  # Log first 5 errors per batch
                                    logger.warning(f"Failed to import record: {e}")
                                    self.import_stats["warnings"].append(str(e)[:100])
                        
                        if batch_errors > 5:
                            logger.warning(f"Additional {batch_errors - 5} errors occurred in this batch")
                    
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
        """Import all financial CSV files with enhanced processing"""
        logger.info("Starting comprehensive enhanced financial data import")
        
        # Create import batch
        self.import_batch_id = self.create_import_batch()
        
        results = {}
        
        # Import each file type
        file_imports = [
            ('scorecard_trends', self.import_scorecard_trends),
            ('payroll_trends', self.import_payroll_trends),
            ('profit_loss', self.import_profit_loss),
            ('customers', self.import_customers)
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
            'warnings': self.import_stats['warnings'][:10] if self.import_stats['warnings'] else [],
            'parsing_issues': len(self.import_stats['parsing_issues'])
        }
        
        logger.info(f"Enhanced financial import completed. Success: {all_success}")
        logger.info(f"Summary: {self.import_stats['files_processed']} files, "
                   f"{self.import_stats['total_records_imported']}/{self.import_stats['total_records_processed']} records imported")
        logger.info(f"Parsing issues encountered: {len(self.import_stats['parsing_issues'])}")
        
        return summary

    def verify_import(self) -> Dict:
        """Verify imported data with enhanced analysis"""
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
                    
                    # Enhanced verification for scorecard trends
                    if table == 'pos_scorecard_trends':
                        # Check for store-specific revenue data using correct UI column names
                        store_check = session.execute(text(f"""
                            SELECT 
                                COUNT(*) as total_rows,
                                COUNT(CASE WHEN revenue_3607 IS NOT NULL AND revenue_3607 > 0 THEN 1 END) as revenue_3607_data,
                                COUNT(CASE WHEN revenue_6800 IS NOT NULL AND revenue_6800 > 0 THEN 1 END) as revenue_6800_data,
                                COUNT(CASE WHEN revenue_728 IS NOT NULL AND revenue_728 > 0 THEN 1 END) as revenue_728_data,
                                COUNT(CASE WHEN revenue_8101 IS NOT NULL AND revenue_8101 > 0 THEN 1 END) as revenue_8101_data,
                                COUNT(CASE WHEN reservation_next14_3607 IS NOT NULL AND reservation_next14_3607 > 0 THEN 1 END) as reservation_next14_3607_data,
                                COUNT(CASE WHEN total_reservation_3607 IS NOT NULL AND total_reservation_3607 > 0 THEN 1 END) as total_reservation_3607_data,
                                COUNT(CASE WHEN ar_over_45_days_percent IS NOT NULL THEN 1 END) as ar_over_45_days_data,
                                COUNT(CASE WHEN total_discount IS NOT NULL AND total_discount > 0 THEN 1 END) as total_discount_data
                            FROM {table}
                        """)).fetchone()
                        
                        verification[table] = {
                            'record_count': count,
                            'exists': True,
                            'sample_records': samples,
                            'store_data_check': dict(store_check._mapping) if store_check else None
                        }
                    else:
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

    def diagnostic_csv_analysis(self, file_path: str = None) -> Dict:
        """Diagnostic analysis of CSV structure and parsing issues"""
        if not file_path:
            pattern = os.path.join(self.CSV_BASE_PATH, "ScorecardTrends*.csv")
            files = glob.glob(pattern)
            if not files:
                raise FileNotFoundError(f"No ScorecardTrends CSV files found")
            file_path = max(files, key=os.path.getctime)
        
        logger.info(f"Running diagnostic analysis on: {file_path}")
        
        try:
            # Read raw CSV
            df = self.robust_excel_csv_parser(file_path)
            
            analysis = {
                'file_path': file_path,
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'headers': list(df.columns),
                'sample_data': {},
                'data_quality': {},
                'store_analysis': {}
            }
            
            # Analyze first few rows
            for i in range(min(3, len(df))):
                row_data = {}
                for j, col in enumerate(df.columns[:10]):  # First 10 columns
                    row_data[col] = str(df.iloc[i, j])
                analysis['sample_data'][f'row_{i}'] = row_data
            
            # Analyze store-specific columns
            store_patterns = ['3607', '6800', '728', '8101']
            for pattern in store_patterns:
                store_cols = [col for col in df.columns if pattern in str(col)]
                if store_cols:
                    analysis['store_analysis'][f'store_{pattern}'] = {
                        'columns': store_cols,
                        'column_count': len(store_cols)
                    }
                    
                    # Check data in store columns
                    for col in store_cols[:2]:  # Check first 2 store columns
                        non_empty = df[col].notna().sum()
                        non_zero = 0
                        try:
                            numeric_data = df[col].apply(self.aggressive_currency_cleaner)
                            non_zero = (numeric_data > 0).sum()
                        except:
                            pass
                        
                        analysis['store_analysis'][f'store_{pattern}'][f'{col}_stats'] = {
                            'non_empty_count': int(non_empty),
                            'non_zero_count': int(non_zero),
                            'sample_values': df[col].dropna().iloc[:3].tolist() if non_empty > 0 else []
                        }
            
            # Data quality analysis
            for col in df.columns[:15]:  # Analyze first 15 columns
                non_null = df[col].notna().sum()
                unique_vals = df[col].nunique()
                sample_vals = df[col].dropna().iloc[:3].tolist() if non_null > 0 else []
                
                analysis['data_quality'][col] = {
                    'non_null_count': int(non_null),
                    'unique_count': int(unique_vals),
                    'sample_values': [str(v) for v in sample_vals]
                }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Diagnostic analysis failed: {e}")
            return {'error': str(e), 'file_path': file_path}
