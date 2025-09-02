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
from app.models.financial_models import ScorecardTrendsData, ScorecardMetricsDefinition
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
        
    def find_all_scorecard_csvs(self) -> List[str]:
        """Find all scorecard CSV files (by year) - supports both old and new naming conventions"""
        # Look for old year-specific files: scorecard2022.csv
        old_year_pattern = os.path.join(self.csv_base_path, "scorecard[0-9][0-9][0-9][0-9].csv")
        old_year_files = glob.glob(old_year_pattern)
        
        # Look for new date-specific files: scorecard01.01.25.csv  
        new_date_pattern = os.path.join(self.csv_base_path, "scorecard[0-9][0-9].[0-9][0-9].[0-9][0-9].csv")
        new_date_files = glob.glob(new_date_pattern)
        
        # Also check general scorecard files (exclude already found files)
        general_pattern = os.path.join(self.csv_base_path, "scorecard*.csv")
        general_files = [f for f in glob.glob(general_pattern) 
                        if f not in old_year_files and f not in new_date_files]
        
        # Also check legacy format
        legacy_pattern = os.path.join(self.csv_base_path, "ScorecardTrends*.csv")
        legacy_files = glob.glob(legacy_pattern)
        
        all_files = old_year_files + new_date_files + general_files + legacy_files
        
        if not all_files:
            return []
            
        # Sort by filename (year files will be in chronological order)
        all_files.sort()
        return all_files
        
    def find_latest_scorecard_csv(self) -> Optional[str]:
        """Find the most recent scorecard trends CSV file"""
        all_files = self.find_all_scorecard_csvs()
        if not all_files:
            return None
        # Return most recent by modification time
        all_files.sort(key=os.path.getmtime, reverse=True)
        return all_files[0]
    
    def extract_year_from_filename(self, file_path: str) -> Optional[int]:
        """Extract year from filename - handles both old (scorecard2022.csv) and new (scorecard01.01.25.csv) formats"""
        try:
            filename = os.path.basename(file_path)
            
            # Try old format first: scorecard2022.csv -> 2022
            old_match = re.search(r'scorecard(\d{4})', filename)
            if old_match:
                return int(old_match.group(1))
            
            # Try new format: scorecardMM.DD.YY.csv -> 20YY
            new_match = re.search(r'scorecard\d{2}\.\d{2}\.(\d{2})', filename)
            if new_match:
                year_suffix = int(new_match.group(1))
                # Convert 2-digit year to 4-digit (25 -> 2025, 24 -> 2024, etc.)
                if year_suffix >= 20:  # 20-99 maps to 2020-2099
                    return 2000 + year_suffix
                else:  # 00-19 maps to 2000-2019
                    return 2000 + year_suffix
            
            return None
        except:
            return None
    
    def parse_scorecard_csv(self, file_path: str) -> pd.DataFrame:
        """Parse transposed scorecard CSV with row-based metrics and weekly columns"""
        try:
            # Read CSV with proper handling
            df = pd.read_csv(file_path, dtype=str)
            
            self.import_stats["warnings"].append(f"Raw CSV shape: {df.shape}")
            
            # Remove the first empty column if exists
            if df.columns[0] == '' or df.columns[0].startswith('Unnamed'):
                df = df.drop(df.columns[0], axis=1)
            
            # Extract weekly date columns (skip metadata columns)
            metadata_cols = ['Group Name', 'Status', 'Title', 'Description', 'Owner', 'Goal', 'Average', 'Total']
            date_columns = [col for col in df.columns if col not in metadata_cols and '-' in col]
            
            self.import_stats["warnings"].append(f"Found {len(date_columns)} date columns")
            
            # Define metric row mappings
            metric_rows = {
                1: {'field': 'total_weekly_revenue', 'type': 'currency'},
                2: {'field': 'revenue_3607', 'type': 'currency'},
                3: {'field': 'revenue_6800', 'type': 'currency'}, 
                4: {'field': 'revenue_728', 'type': 'currency'},
                5: {'field': 'revenue_8101', 'type': 'currency'},
                6: {'field': 'new_contracts_3607', 'type': 'integer'},
                7: {'field': 'new_contracts_6800', 'type': 'integer'},
                8: {'field': 'new_contracts_728', 'type': 'integer'}, 
                9: {'field': 'new_contracts_8101', 'type': 'integer'},
                10: {'field': 'deliveries_scheduled_8101', 'type': 'integer'},
                11: {'field': 'reservation_next14_3607', 'type': 'currency'},
                12: {'field': 'reservation_next14_6800', 'type': 'currency'},
                13: {'field': 'reservation_next14_728', 'type': 'currency'}, 
                14: {'field': 'reservation_next14_8101', 'type': 'currency'},
                15: {'field': 'total_reservation_3607', 'type': 'currency'},
                16: {'field': 'total_reservation_6800', 'type': 'currency'},
                17: {'field': 'total_reservation_728', 'type': 'currency'},
                18: {'field': 'total_reservation_8101', 'type': 'currency'},
                19: {'field': 'ar_over_45_days_percent', 'type': 'percentage'},
                20: {'field': 'total_discount', 'type': 'currency'},
                # Can add more mappings as needed
            }
            
            # Convert transposed data to normalized records
            records = []
            
            for date_col in date_columns:
                # Parse the date from column header (e.g., "Sep 01 - Sep 07")
                try:
                    # Extract the end date from the range
                    date_parts = date_col.split(' - ')
                    if len(date_parts) == 2:
                        end_date_str = date_parts[1]
                        # Extract year from filename for accurate date parsing
                        file_year = self.extract_year_from_filename(file_path)
                        end_date = self._parse_date_header(date_col, file_year)
                    else:
                        continue
                except:
                    self.import_stats["warnings"].append(f"Could not parse date from column: {date_col}")
                    continue
                
                if end_date is None:
                    continue
                    
                # Create record for this week
                record = {'week_ending': end_date}
                
                # Extract metrics from each mapped row
                for row_idx, metric_info in metric_rows.items():
                    if row_idx <= len(df):
                        try:
                            raw_value = df.iloc[row_idx - 1][date_col] if date_col in df.columns else None
                            
                            if metric_info['type'] == 'currency':
                                cleaned_value = self._parse_currency(raw_value)
                            elif metric_info['type'] == 'percentage':
                                cleaned_value = self._parse_percentage(raw_value)
                            elif metric_info['type'] == 'integer':
                                cleaned_value = self._parse_integer(raw_value)
                            else:
                                cleaned_value = None
                                
                            record[metric_info['field']] = cleaned_value
                            
                        except Exception as e:
                            self.import_stats["warnings"].append(f"Error parsing {metric_info['field']} for {date_col}: {str(e)}")
                            record[metric_info['field']] = None
                
                records.append(record)
            
            # Convert to DataFrame
            result_df = pd.DataFrame(records)
            
            # Clean NaN values by replacing with None
            result_df = result_df.replace({np.nan: None})
            
            # Sort by date
            if 'week_ending' in result_df.columns:
                result_df = result_df.sort_values('week_ending')
            
            self.import_stats["warnings"].append(f"Converted to {len(result_df)} weekly records")
            
            return result_df
            
        except Exception as e:
            self.import_stats["errors"].append(f"Failed to parse transposed CSV {file_path}: {str(e)}")
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
    
    def _parse_date_header(self, date_header: str, file_year: int = None) -> Optional[datetime]:
        """Parse date from header like 'Dec 26 - Jan 01' with explicit year from filename"""
        try:
            # Extract the end date (Sunday)
            parts = date_header.split(' - ')
            if len(parts) != 2:
                return None
                
            end_date_str = parts[1].strip()
            
            # If we have a year from filename, use it
            if file_year:
                target_year = file_year
            else:
                # Fallback to current year logic
                current_date = datetime.now()
                target_year = current_date.year
                
            # Try parsing with different formats
            formats = ['%b %d', '%B %d', '%m/%d', '%m-%d']
            
            for fmt in formats:
                try:
                    parsed = datetime.strptime(f"{end_date_str} {target_year}", f"{fmt} %Y")
                    return parsed.date()
                except ValueError:
                    continue
                    
            # If target year fails, try adjacent years (for year-end transitions)
            for year_offset in [-1, 1]:
                try_year = target_year + year_offset
                for fmt in formats:
                    try:
                        parsed = datetime.strptime(f"{end_date_str} {try_year}", f"{fmt} %Y")
                        return parsed.date()
                    except ValueError:
                        continue
                    
            return None
            
        except Exception:
            return None
    
    def _parse_integer(self, value) -> Optional[int]:
        """Parse integer values handling various formats"""
        if pd.isna(value) or value == '' or value is None:
            return None
            
        # Handle numpy nan
        if hasattr(value, '__name__') and 'nan' in str(value).lower():
            return None
            
        # Handle string values
        if isinstance(value, str):
            clean_value = value.strip()
            # Remove commas and other formatting
            clean_value = re.sub(r'[,\s]', '', clean_value)
            
            if clean_value in ['-', 'N/A', 'n/a', '', 'nan']:
                return None
                
            try:
                return int(float(clean_value))
            except:
                return None
                
        # Handle numeric values (including numpy types)
        try:
            # Convert to float first to handle any numeric type
            float_val = float(value)
            # Check if it's actually a number
            if np.isnan(float_val):
                return None
            return int(float_val)
        except:
            return None
    
    def extract_and_store_metadata(self, file_path: str):
        """Extract metadata from CSV and store in database"""
        try:
            # Read just the metadata columns
            df = pd.read_csv(file_path, dtype=str)
            
            # Remove the first empty column if exists
            if df.columns[0] == '' or df.columns[0].startswith('Unnamed'):
                df = df.drop(df.columns[0], axis=1)
            
            metadata_cols = ['Group Name', 'Status', 'Title', 'Description', 'Owner', 'Goal', 'Average', 'Total']
            
            # Define metric mappings
            metric_rows = {
                1: 'total_weekly_revenue',
                2: 'revenue_3607', 
                3: 'revenue_6800',
                4: 'revenue_728',
                5: 'revenue_8101',
                6: 'new_contracts_3607',
                7: 'new_contracts_6800',
                8: 'new_contracts_728',
                9: 'new_contracts_8101',
                10: 'deliveries_scheduled_8101',
                11: 'reservation_next14_3607',
                12: 'reservation_next14_6800',
                13: 'reservation_next14_728',
                14: 'reservation_next14_8101',
                15: 'total_reservation_3607',
                16: 'total_reservation_6800',
                17: 'total_reservation_728',
                18: 'total_reservation_8101',
                19: 'ar_over_45_days_percent',
                20: 'total_discount'
            }
            
            # Extract metadata for each metric
            for row_idx, metric_code in metric_rows.items():
                if row_idx <= len(df):
                    try:
                        row_data = df.iloc[row_idx - 1]
                        
                        # Check if this metric definition already exists
                        existing = ScorecardMetricsDefinition.query.filter_by(metric_code=metric_code).first()
                        
                        if existing:
                            # Update existing
                            existing.row_number = row_idx
                            existing.title = str(row_data.get('Title', '')).strip()
                            existing.description = str(row_data.get('Description', '')).strip()  
                            existing.owner = str(row_data.get('Owner', '')).strip()
                            existing.goal = str(row_data.get('Goal', '')).strip()
                            existing.status = str(row_data.get('Status', '')).strip()
                            existing.updated_at = datetime.utcnow()
                        else:
                            # Create new
                            metric_def = ScorecardMetricsDefinition(
                                row_number=row_idx,
                                metric_code=metric_code,
                                title=str(row_data.get('Title', '')).strip(),
                                description=str(row_data.get('Description', '')).strip(),
                                owner=str(row_data.get('Owner', '')).strip(),
                                goal=str(row_data.get('Goal', '')).strip(),
                                status=str(row_data.get('Status', '')).strip()
                            )
                            db.session.add(metric_def)
                            
                    except Exception as e:
                        self.import_stats["warnings"].append(f"Could not extract metadata for row {row_idx}: {str(e)}")
            
            db.session.commit()
            self.import_stats["warnings"].append("Metadata extracted and stored successfully")
            
        except Exception as e:
            self.import_stats["warnings"].append(f"Failed to extract metadata: {str(e)}")
    
    def import_all_scorecard_files(self) -> Dict[str, Any]:
        """Import all scorecard CSV files with metadata"""
        all_files = self.find_all_scorecard_csvs()
        
        if not all_files:
            return {
                "success": False,
                "error": "No scorecard CSV files found",
                "stats": self.import_stats
            }
        
        total_imported = 0
        files_processed = []
        
        # Extract metadata from the most recent file
        if all_files:
            self.extract_and_store_metadata(all_files[-1])
        
        # Import data from all files
        for file_path in all_files:
            try:
                result = self.import_scorecard_data(file_path)
                if result["success"]:
                    total_imported += result["stats"]["records_imported"]
                    files_processed.append({
                        "file": os.path.basename(file_path),
                        "records": result["stats"]["records_imported"],
                        "date_range": result.get("date_range", {})
                    })
                else:
                    self.import_stats["errors"].append(f"Failed to import {file_path}: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                self.import_stats["errors"].append(f"Error processing {file_path}: {str(e)}")
        
        return {
            "success": len(files_processed) > 0,
            "message": f"Imported {total_imported} total records from {len(files_processed)} files",
            "files_processed": files_processed,
            "stats": self.import_stats
        }
    
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
                        week_ending=row['week_ending'] if hasattr(row['week_ending'], 'date') else row['week_ending'],
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
    
    def _clear_existing_data(self, start_date, end_date):
        """Clear existing scorecard data for the date range being imported"""
        try:
            # Handle different date types
            start_date_obj = start_date if hasattr(start_date, 'date') else start_date
            end_date_obj = end_date if hasattr(end_date, 'date') else end_date
            
            deleted_count = ScorecardTrendsData.query.filter(
                ScorecardTrendsData.week_ending >= start_date_obj,
                ScorecardTrendsData.week_ending <= end_date_obj
            ).delete(synchronize_session='fetch')
            
            if deleted_count > 0:
                self.import_stats["warnings"].append(f"Cleared {deleted_count} existing records for date range {start_date_obj} to {end_date_obj}")
                
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
