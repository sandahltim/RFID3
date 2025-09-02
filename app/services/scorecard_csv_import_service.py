"""
Scorecard Trends CSV Import Service
Handles importing and processing scorecard trends data with proper store mapping
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import glob
import re
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app import db
from app.models.financial_models import ScorecardTrendsData
from app.config.stores import STORES, get_store_by_pos_code, get_all_store_codes
from decimal import Decimal

class ScorecardCSVImportService:
    """Service for importing Scorecard Trends CSV data with proper store correlation"""
    
    def __init__(self):
        self.csv_base_path = "/home/tim/RFID3/shared/POR"
        self.import_stats = {
            "records_processed": 0,
            "records_imported": 0,
            "records_failed": 0,
            "errors": [],
            "warnings": []
        }
        
    def find_latest_scorecard_csv(self) -> Optional[str]:
        """Find the most recent scorecard trends CSV file"""
        pattern = os.path.join(self.csv_base_path, "ScorecardTrends*.csv")
        files = glob.glob(pattern)
        
        if not files:
            return None
            
        # Sort by modification time, newest first
        files.sort(key=os.path.getmtime, reverse=True)
        return files[0]
    
    def parse_scorecard_csv(self, file_path: str) -> pd.DataFrame:
        """Parse scorecard CSV with proper Excel date handling"""
        try:
            # Read CSV with proper handling
            df = pd.read_csv(file_path)
            
            # Handle Excel serial date format (first column)
            # Excel serial date format: days since 1900-01-01 (adjusted for Excel bug)
            if 'Week ending Sunday' in df.columns:
                df['week_ending'] = pd.to_datetime('1899-12-30') + pd.to_timedelta(df['Week ending Sunday'], 'D')
            else:
                # Try to find a date column
                date_cols = [col for col in df.columns if 'week' in col.lower() or 'date' in col.lower()]
                if date_cols:
                    df['week_ending'] = pd.to_datetime(df[date_cols[0]], errors='coerce')
                else:
                    raise ValueError("No date column found in CSV")
            
            # Map columns to standardized names
            column_mapping = {
                'Total Weekly Revenue': 'total_weekly_revenue',
                '3607 Revenue': 'revenue_3607',
                '6800 Revenue': 'revenue_6800', 
                '728 Revenue': 'revenue_728',
                '8101 Revenue': 'revenue_8101',
                '# New Open Contracts 3607': 'new_contracts_3607',
                '# New Open Contracts 6800': 'new_contracts_6800',
                '# New Open Contracts 728': 'new_contracts_728', 
                '# New Open Contracts 8101': 'new_contracts_8101',
                '# Deliveries Scheduled next 7 days Weds-Tues 8101': 'deliveries_scheduled_8101',
                '$ on Reservation - Next 14 days - 3607': 'reservation_next14_3607',
                '$ on Reservation - Next 14 days - 6800': 'reservation_next14_6800',
                '$ on Reservation - Next 14 days - 728': 'reservation_next14_728', 
                '$ on Reservation - Next 14 days - 8101': 'reservation_next14_8101',
                'Total $ on Reservation 3607': 'total_reservation_3607',
                'Total $ on Reservation 6800': 'total_reservation_6800',
                'Total $ on Reservation 728': 'total_reservation_728',
                'Total $ on Reservation 8101': 'total_reservation_8101',
                '% -Total AR ($) > 45 days': 'ar_over_45_days_percent',
                'Total Discount $ Company Wide': 'total_discount',
                'WEEK NUMBER': 'week_number',
                '# Open Quotes 8101': 'open_quotes_8101',
                '$ Total AR (Cash Customers)': 'total_ar_cash_customers'
            }
            
            # Rename columns if they exist
            for old_name, new_name in column_mapping.items():
                if old_name in df.columns:
                    df.rename(columns={old_name: new_name}, inplace=True)
            
            # Clean and convert data types
            df = self._clean_scorecard_data(df)
            
            return df
            
        except Exception as e:
            self.import_stats["errors"].append(f"Failed to parse CSV {file_path}: {str(e)}")
            raise
    
    def _clean_scorecard_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate scorecard data"""
        
        # Convert percentage fields (handle both decimal and percentage formats)
        if 'ar_over_45_days_percent' in df.columns:
            df['ar_over_45_days_percent'] = df['ar_over_45_days_percent'].apply(self._parse_percentage)
        
        # Convert monetary fields
        monetary_columns = [
            'total_weekly_revenue', 'revenue_3607', 'revenue_6800', 'revenue_728', 'revenue_8101',
            'reservation_next14_3607', 'reservation_next14_6800', 'reservation_next14_728', 'reservation_next14_8101',
            'total_reservation_3607', 'total_reservation_6800', 'total_reservation_728', 'total_reservation_8101',
            'total_discount', 'total_ar_cash_customers'
        ]
        
        for col in monetary_columns:
            if col in df.columns:
                df[col] = df[col].apply(self._parse_currency)
        
        # Convert integer fields
        integer_columns = [
            'new_contracts_3607', 'new_contracts_6800', 'new_contracts_728', 'new_contracts_8101',
            'deliveries_scheduled_8101', 'week_number', 'open_quotes_8101'
        ]
        
        for col in integer_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
        # Remove rows with no meaningful data
        df = df.dropna(subset=['week_ending'])
        df = df[df['week_ending'].notna()]
        
        # Sort by date
        df = df.sort_values('week_ending')
        
        return df
    
    def _parse_currency(self, value) -> Optional[Decimal]:
        """Parse currency values handling various formats"""
        if pd.isna(value) or value == '':
            return None
            
        if isinstance(value, (int, float)):
            return Decimal(str(value))
        
        # Remove currency symbols, commas, and whitespace
        clean_value = str(value).strip()
        clean_value = re.sub(r'[\$,\s]', '', clean_value)
        
        # Handle empty or non-numeric values
        if not clean_value or clean_value in ['-', 'N/A', 'n/a']:
            return None
            
        try:
            return Decimal(clean_value)
        except:
            return None
    
    def _parse_percentage(self, value) -> Optional[Decimal]:
        """Parse percentage values handling both decimal and percentage formats"""
        if pd.isna(value) or value == '':
            return None
            
        if isinstance(value, (int, float)):
            # If value is already a decimal (0.15 for 15%), keep as is
            # If value is a percentage (15 for 15%), convert to decimal
            if value > 1:
                return Decimal(str(value / 100))
            else:
                return Decimal(str(value))
        
        clean_value = str(value).strip()
        clean_value = re.sub(r'[%\s]', '', clean_value)
        
        if not clean_value or clean_value in ['-', 'N/A', 'n/a']:
            return None
            
        try:
            numeric_val = float(clean_value)
            # Convert percentage to decimal if needed
            if numeric_val > 1:
                return Decimal(str(numeric_val / 100))
            else:
                return Decimal(str(numeric_val))
        except:
            return None
    
    def import_scorecard_data(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Import scorecard trends data from CSV file"""
        
        if not file_path:
            file_path = self.find_latest_scorecard_csv()
            if not file_path:
                return {
                    "success": False,
                    "error": "No scorecard CSV files found",
                    "stats": self.import_stats
                }
        
        try:
            # Parse the CSV
            df = self.parse_scorecard_csv(file_path)
            
            if df.empty:
                return {
                    "success": False, 
                    "error": "CSV file is empty or contains no valid data",
                    "stats": self.import_stats
                }
            
            # Clear existing data (or implement incremental updates)
            self._clear_existing_data(df['week_ending'].min(), df['week_ending'].max())
            
            # Import the data
            imported_count = 0
            
            for index, row in df.iterrows():
                try:
                    scorecard_record = ScorecardTrendsData(
                        week_ending=row['week_ending'].date(),
                        total_weekly_revenue=row.get('total_weekly_revenue'),
                        revenue_3607=row.get('revenue_3607'),
                        revenue_6800=row.get('revenue_6800'), 
                        revenue_728=row.get('revenue_728'),
                        revenue_8101=row.get('revenue_8101'),
                        new_contracts_3607=row.get('new_contracts_3607'),
                        new_contracts_6800=row.get('new_contracts_6800'),
                        new_contracts_728=row.get('new_contracts_728'),
                        new_contracts_8101=row.get('new_contracts_8101'),
                        deliveries_scheduled_8101=row.get('deliveries_scheduled_8101'),
                        reservation_next14_3607=row.get('reservation_next14_3607'),
                        reservation_next14_6800=row.get('reservation_next14_6800'),
                        reservation_next14_728=row.get('reservation_next14_728'),
                        reservation_next14_8101=row.get('reservation_next14_8101'),
                        total_reservation_3607=row.get('total_reservation_3607'),
                        total_reservation_6800=row.get('total_reservation_6800'),
                        total_reservation_728=row.get('total_reservation_728'),
                        total_reservation_8101=row.get('total_reservation_8101'),
                        ar_over_45_days_percent=row.get('ar_over_45_days_percent'),
                        total_discount=row.get('total_discount'),
                        week_number=row.get('week_number'),
                        open_quotes_8101=row.get('open_quotes_8101'),
                        total_ar_cash_customers=row.get('total_ar_cash_customers'),
                        created_at=datetime.utcnow()
                    )
                    
                    db.session.add(scorecard_record)
                    imported_count += 1
                    self.import_stats["records_processed"] += 1
                    
                except Exception as e:
                    self.import_stats["errors"].append(f"Failed to import row {index}: {str(e)}")
                    self.import_stats["records_failed"] += 1
                    continue
            
            # Commit the transaction
            db.session.commit()
            self.import_stats["records_imported"] = imported_count
            
            return {
                "success": True,
                "message": f"Successfully imported {imported_count} scorecard records",
                "file_path": file_path,
                "date_range": {
                    "start": df['week_ending'].min().strftime('%Y-%m-%d'),
                    "end": df['week_ending'].max().strftime('%Y-%m-%d')
                },
                "stats": self.import_stats
            }
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Failed to import scorecard data: {str(e)}"
            self.import_stats["errors"].append(error_msg)
            
            return {
                "success": False,
                "error": error_msg,
                "stats": self.import_stats
            }
    
    def _clear_existing_data(self, start_date: datetime, end_date: datetime):
        """Clear existing scorecard data for the date range being imported"""
        try:
            deleted_count = ScorecardTrendsData.query.filter(
                ScorecardTrendsData.week_ending >= start_date.date(),
                ScorecardTrendsData.week_ending <= end_date.date()
            ).delete(synchronize_session='fetch')
            
            if deleted_count > 0:
                self.import_stats["warnings"].append(f"Cleared {deleted_count} existing records for date range {start_date.date()} to {end_date.date()}")
                
        except Exception as e:
            self.import_stats["warnings"].append(f"Failed to clear existing data: {str(e)}")
    
    def get_store_correlation_mapping(self) -> Dict[str, str]:
        """Get the correct store correlation mapping based on centralized config"""
        return {
            '3607': STORES['3607'].name,  # Wayzata
            '6800': STORES['6800'].name,  # Brooklyn Park  
            '728': STORES['728'].name,    # Elk River
            '8101': STORES['8101'].name,  # Fridley
            '000': STORES['000'].name     # Legacy/Unassigned
        }
    
    def validate_store_codes(self) -> Dict[str, Any]:
        """Validate that scorecard store codes match centralized configuration"""
        scorecard_codes = ['3607', '6800', '728', '8101', '000']
        centralized_codes = get_all_store_codes()
        
        validation_result = {
            "valid": True,
            "issues": [],
            "mapping": {}
        }
        
        for code in scorecard_codes:
            if code in centralized_codes:
                validation_result["mapping"][code] = STORES[code].name
            else:
                validation_result["valid"] = False
                validation_result["issues"].append(f"Store code {code} not found in centralized configuration")
        
        return validation_result

# Singleton instance
_scorecard_import_service = None

def get_scorecard_import_service():
    """Get or create scorecard import service instance"""
    global _scorecard_import_service
    if _scorecard_import_service is None:
        _scorecard_import_service = ScorecardCSVImportService()
    return _scorecard_import_service
