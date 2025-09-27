"""
Comprehensive Payroll Data Import Service
Fixes horizontal data structure and correlation issues
Integrates with centralized store configuration
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
from app.config.stores import STORES, get_store_manager, get_store_business_type, get_store_name
from app.models.financial_models import PayrollTrendsData
from config import DB_CONFIG

logger = get_logger(__name__)

class PayrollImportService:
    """Dedicated service for importing payroll data with proper correlation handling"""
    
    CSV_BASE_PATH = "/home/tim/RFID3-RFID-KVC/shared/POR"
    
    def __init__(self):
        self.logger = logger
        self.database_url = (
            f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}/{DB_CONFIG['database']}"
        )
        self.engine = create_engine(self.database_url, pool_pre_ping=True)
        self.Session = sessionmaker(bind=self.engine)
        self.import_batch_id = None
        self.import_stats = {
            "files_processed": 0,
            "total_records_processed": 0,
            "total_records_imported": 0,
            "normalized_records": 0,
            "errors": [],
            "warnings": [],
            "store_correlations": {}
        }

    def robust_csv_parser(self, file_path: str) -> pd.DataFrame:
        """Parse CSV with proper Excel export handling"""
        logger.info(f"Parsing payroll CSV file: {file_path}")
        
        try:
            df = pd.read_csv(
                file_path,
                encoding='utf-8',
                low_memory=False,
                quotechar='"',
                skipinitialspace=True,
                na_values=['', 'NULL', 'null', 'N/A', 'n/a', '#N/A'],
                keep_default_na=True,
                dtype=str
            )
            
            logger.info(f"Raw CSV: {len(df)} rows, {len(df.columns)} columns")
            logger.info(f"Column headers: {list(df.columns)}")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to parse CSV {file_path}: {e}")
            raise

    def aggressive_currency_cleaner(self, value: str) -> Optional[float]:
        """Clean currency values from Excel CSV exports"""
        if pd.isna(value) or value is None:
            return None
            
        clean_val = str(value).strip()
        
        if clean_val in ['', '-', '$-', '$ -', ' ', 'nan', 'NaN', 'NULL']:
            return 0.0
        
        # Remove quotes and currency symbols
        clean_val = clean_val.strip('"').strip("'").strip()
        clean_val = clean_val.replace('$', '').replace(',', '').replace(' ', '')
        
        # Handle parentheses as negative (accounting format)
        if clean_val.startswith('(') and clean_val.endswith(')'):
            clean_val = '-' + clean_val[1:-1]
        
        try:
            return float(clean_val) if clean_val else 0.0
        except (ValueError, TypeError):
            logger.warning(f"Could not parse currency value: '{value}' -> '{clean_val}'")
            return None

    def aggressive_numeric_cleaner(self, value: str) -> Optional[float]:
        """Clean numeric values including hours"""
        if pd.isna(value) or value is None:
            return None
            
        clean_val = str(value).strip()
        
        if clean_val in ['', '-', ' ', 'nan', 'NaN', 'NULL']:
            return None
        
        # Remove commas from numbers
        clean_val = clean_val.replace(',', '')
        
        try:
            return float(clean_val) if clean_val else None
        except (ValueError, TypeError):
            logger.warning(f"Could not parse numeric value: '{value}' -> '{clean_val}'")
            return None

    def smart_date_parser(self, date_str: str) -> pd.Timestamp:
        """Parse dates with various formats including Excel serial numbers"""
        if pd.isna(date_str) or date_str == '' or date_str is None:
            return pd.NaT
        
        date_str = str(date_str).strip()
        
        try:
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

    def normalize_horizontal_payroll_data(self, df: pd.DataFrame) -> List[Dict]:
        """
        Convert horizontal payroll data to normalized records
        
        The CSV structure is:
        WEEK ENDING SUN, Rental Revenue 6800, All Revenue 6800, Payroll 6800, Wage Hours 6800,
                         Rental Revenue 3607, All Revenue 3607, Payroll 3607, Wage Hours 3607, ...
        
        We need to convert this to individual records per store per week.
        """
        logger.info("Normalizing horizontal payroll data structure")
        
        normalized_data = []
        
        # Parse the date column (first column)
        date_col = df.columns[0]
        logger.info(f"Using date column: {date_col}")
        
        # Identify store codes from column headers
        store_codes = []
        for col in df.columns[1:]:  # Skip date column
            col_str = str(col)
            for store_code in ['6800', '3607', '8101', '728']:
                if store_code in col_str:
                    if store_code not in store_codes:
                        store_codes.append(store_code)
                        logger.info(f"Found store code {store_code} in headers")
                    break
        
        logger.info(f"Identified store codes: {store_codes}")
        
        # Process each row
        for idx, row in df.iterrows():
            week_ending_raw = row.iloc[0]
            week_ending = self.smart_date_parser(week_ending_raw)
            
            if pd.isna(week_ending):
                logger.warning(f"Skipping row {idx}: invalid date '{week_ending_raw}'")
                continue
            
            # For each store, extract its data
            for store_code in store_codes:
                # Find columns for this store
                store_columns = {}
                for col_idx, col in enumerate(df.columns[1:], 1):  # Skip date column
                    col_str = str(col).lower()
                    if store_code in col_str:
                        if 'rental revenue' in col_str:
                            store_columns['rental_revenue'] = col_idx
                        elif 'all revenue' in col_str and 'rental' not in col_str:
                            store_columns['all_revenue'] = col_idx
                        elif 'payroll' in col_str:
                            store_columns['payroll_amount'] = col_idx
                        elif 'hours' in col_str:
                            store_columns['wage_hours'] = col_idx
                
                # Extract values for this store
                rental_revenue = None
                all_revenue = None
                payroll_amount = None
                wage_hours = None
                
                if 'rental_revenue' in store_columns:
                    rental_revenue = self.aggressive_currency_cleaner(row.iloc[store_columns['rental_revenue']])
                if 'all_revenue' in store_columns:
                    all_revenue = self.aggressive_currency_cleaner(row.iloc[store_columns['all_revenue']])
                if 'payroll_amount' in store_columns:
                    payroll_amount = self.aggressive_currency_cleaner(row.iloc[store_columns['payroll_amount']])
                if 'wage_hours' in store_columns:
                    wage_hours = self.aggressive_numeric_cleaner(row.iloc[store_columns['wage_hours']])
                
                # Get manager and business type from centralized config
                manager = get_store_manager(store_code)
                business_type = get_store_business_type(store_code)
                store_name = get_store_name(store_code)
                
                # Create normalized record
                normalized_record = {
                    'week_ending': week_ending.date() if not pd.isna(week_ending) else None,
                    'location_code': store_code,
                    'store_name': store_name,
                    'manager': manager,
                    'business_type': business_type,
                    'rental_revenue': rental_revenue,
                    'all_revenue': all_revenue,
                    'payroll_amount': payroll_amount,
                    'wage_hours': wage_hours,
                    'import_batch_id': self.import_batch_id
                }
                
                # Only add if we have some meaningful data
                if any([rental_revenue, all_revenue, payroll_amount, wage_hours]):
                    normalized_data.append(normalized_record)
                    
                    # Track store correlations
                    if store_code not in self.import_stats["store_correlations"]:
                        self.import_stats["store_correlations"][store_code] = {
                            "name": store_name,
                            "manager": manager,
                            "business_type": business_type,
                            "records_count": 0
                        }
                    self.import_stats["store_correlations"][store_code]["records_count"] += 1
        
        logger.info(f"Normalized {len(normalized_data)} records from horizontal structure")
        logger.info(f"Store correlations: {self.import_stats['store_correlations']}")
        
        return normalized_data

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
                        'payroll_trends_corrected',
                        NOW(),
                        'in_progress'
                    )
                """))
                session.commit()
                batch_id = result.lastrowid
                logger.info(f"Created payroll import batch {batch_id}")
                return batch_id
            except Exception as e:
                logger.error(f"Failed to create import batch: {e}")
                session.rollback()
                raise

    def clear_existing_payroll_data(self):
        """Clear existing payroll data to avoid duplicates"""
        with self.Session() as session:
            try:
                # Delete from payroll_trends_data table
                session.execute(text("DELETE FROM payroll_trends_data"))
                session.commit()
                logger.info("Cleared existing payroll data")
            except Exception as e:
                logger.error(f"Failed to clear existing payroll data: {e}")
                session.rollback()
                raise

    def import_normalized_payroll_data(self, normalized_data: List[Dict]) -> int:
        """Import normalized payroll data using the PayrollTrendsData model"""
        imported_count = 0
        # OLD - HARDCODED (WRONG): batch_size = 100
        # NEW - CONFIGURABLE (CORRECT): Use LaborCostConfiguration batch_processing_size (capped at 200)
        from app.models.config_models import LaborCostConfiguration, get_default_labor_cost_config
        try:
            config = LaborCostConfiguration.query.filter_by(
                user_id='default_user', 
                config_name='default'
            ).first()
            
            if config:
                batch_size = min(config.batch_processing_size, 200)  # Cap at 200 as per user requirement
            else:
                defaults = get_default_labor_cost_config()
                batch_size = min(defaults['batch_processing']['default_batch_size'], 200)
        except Exception:
            batch_size = 100  # Safe fallback
        
        with self.Session() as session:
            try:
                for i in range(0, len(normalized_data), batch_size):
                    batch = normalized_data[i:i+batch_size]
                    
                    for record in batch:
                        try:
                            # Create PayrollTrendsData record
                            payroll_record = PayrollTrendsData(
                                week_ending=record['week_ending'],
                                location_code=record['location_code'],
                                rental_revenue=record['rental_revenue'],
                                all_revenue=record['all_revenue'],
                                payroll_amount=record['payroll_amount'],
                                wage_hours=record['wage_hours'],
                                created_at=datetime.utcnow()
                            )
                            
                            session.add(payroll_record)
                            imported_count += 1
                            
                        except Exception as e:
                            logger.warning(f"Failed to import record: {e}")
                            self.import_stats["warnings"].append(str(e)[:100])
                    
                    # Commit batch
                    session.commit()
                    
                    if (i + batch_size) % 500 == 0:
                        logger.info(f"Imported {imported_count} payroll records...")
                
                logger.info(f"Total imported payroll records: {imported_count}")
                
            except Exception as e:
                logger.error(f"Import failed for payroll data: {e}")
                session.rollback()
                raise
        
        return imported_count

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

    def import_payroll_trends_corrected(self, file_path: str = None) -> Dict:
        """
        Corrected PayrollTrends import that properly handles horizontal data structure
        and fixes all correlation issues with centralized store configuration
        """
        if not file_path:
            pattern = os.path.join(self.CSV_BASE_PATH, "PayrollTrends*.csv")
            files = glob.glob(pattern)
            if not files:
                raise FileNotFoundError(f"No PayrollTrends CSV files found")
            file_path = max(files, key=os.path.getctime)
            
        logger.info(f"Starting CORRECTED PayrollTrends import from: {file_path}")
        
        # Create import batch
        self.import_batch_id = self.create_import_batch()
        
        try:
            # Parse CSV
            df = self.robust_csv_parser(file_path)
            logger.info(f"Read {len(df)} records with {len(df.columns)} columns")
            
            # Clear existing data to avoid duplicates
            self.clear_existing_payroll_data()
            
            # Normalize horizontal data structure
            normalized_data = self.normalize_horizontal_payroll_data(df)
            
            if not normalized_data:
                raise ValueError("No payroll data could be normalized")
            
            # Import normalized data
            imported_count = self.import_normalized_payroll_data(normalized_data)
            
            self.import_stats["files_processed"] = 1
            self.import_stats["total_records_processed"] = len(df)
            self.import_stats["normalized_records"] = len(normalized_data)
            self.import_stats["total_records_imported"] = imported_count
            
            # Update batch status
            self.update_import_batch(
                self.import_batch_id,
                'completed',
                self.import_stats
            )
            
            logger.info(f"CORRECTED PayrollTrends import completed successfully")
            logger.info(f"Original rows: {len(df)}, Normalized records: {len(normalized_data)}, Imported: {imported_count}")
            
            return {
                "success": True,
                "file_path": file_path,
                "original_records": len(df),
                "normalized_records": len(normalized_data),
                "imported_records": imported_count,
                "store_correlations": self.import_stats["store_correlations"],
                "batch_id": self.import_batch_id
            }
            
        except Exception as e:
            logger.error(f"CORRECTED PayrollTrends import failed: {str(e)}", exc_info=True)
            self.import_stats["errors"].append(f"PayrollTrends: {str(e)}")
            
            # Update batch status to failed
            self.update_import_batch(
                self.import_batch_id,
                'failed',
                self.import_stats
            )
            
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path,
                "batch_id": self.import_batch_id
            }

    def verify_payroll_import(self) -> Dict:
        """Verify imported payroll data with manager correlations"""
        verification = {}
        
        with self.Session() as session:
            try:
                # Get total count
                result = session.execute(text("SELECT COUNT(*) as count FROM payroll_trends_data"))
                total_count = result.fetchone()[0]
                
                # Get store-specific counts with manager correlations
                store_analysis = {}
                for store_code in ['6800', '3607', '8101', '728']:
                    store_result = session.execute(text("""
                        SELECT 
                            location_code,
                            COUNT(*) as record_count,
                            MIN(week_ending) as earliest_week,
                            MAX(week_ending) as latest_week,
                            SUM(CASE WHEN payroll_amount IS NOT NULL AND payroll_amount > 0 THEN 1 ELSE 0 END) as payroll_records,
                            SUM(CASE WHEN all_revenue IS NOT NULL AND all_revenue > 0 THEN 1 ELSE 0 END) as revenue_records,
                            AVG(CASE WHEN payroll_amount IS NOT NULL AND payroll_amount > 0 THEN payroll_amount END) as avg_payroll,
                            AVG(CASE WHEN all_revenue IS NOT NULL AND all_revenue > 0 THEN all_revenue END) as avg_revenue
                        FROM payroll_trends_data 
                        WHERE location_code = :store_code
                        GROUP BY location_code
                    """), {'store_code': store_code}).fetchone()
                    
                    if store_result:
                        manager = get_store_manager(store_code)
                        business_type = get_store_business_type(store_code)
                        store_name = get_store_name(store_code)
                        
                        store_analysis[store_code] = {
                            'store_name': store_name,
                            'manager': manager,
                            'business_type': business_type,
                            'record_count': store_result.record_count,
                            'earliest_week': str(store_result.earliest_week) if store_result.earliest_week else None,
                            'latest_week': str(store_result.latest_week) if store_result.latest_week else None,
                            'payroll_records': store_result.payroll_records,
                            'revenue_records': store_result.revenue_records,
                            'avg_payroll': float(store_result.avg_payroll) if store_result.avg_payroll else 0,
                            'avg_revenue': float(store_result.avg_revenue) if store_result.avg_revenue else 0
                        }
                
                # Get sample records
                sample_result = session.execute(text("""
                    SELECT 
                        week_ending, location_code, rental_revenue, all_revenue, 
                        payroll_amount, wage_hours
                    FROM payroll_trends_data 
                    ORDER BY week_ending DESC, location_code 
                    LIMIT 5
                """))
                samples = [dict(row._mapping) for row in sample_result]
                
                verification = {
                    'total_records': total_count,
                    'store_analysis': store_analysis,
                    'sample_records': samples,
                    'import_success': total_count > 0,
                    'manager_correlations_verified': all(
                        store['manager'] in ['TYLER', 'ZACK', 'TIM', 'BRUCE'] 
                        for store in store_analysis.values()
                    )
                }
                
            except Exception as e:
                verification = {
                    'error': str(e),
                    'import_success': False
                }
        
        return verification
