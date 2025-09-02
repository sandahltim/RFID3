"""
Equipment Import Service for RFID3 Inventory Management System
Created: 2025-09-02
Handles import and parsing of POS equipment data from CSV/XLS files
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple, Any
import glob
import re
import json
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app import db
from app.models.equipment_models import EquipmentItem, EquipmentImportLog, EquipmentCategory
from app.services.logger import get_logger

logger = get_logger(__name__)

class EquipmentImportService:
    """Service for importing Equipment data from CSV files"""
    
    def __init__(self):
        self.csv_base_path = "/home/tim/RFID3/shared/POR"
        self.batch_id = None
        self.import_log = None
        self.import_stats = {
            "records_processed": 0,
            "records_imported": 0, 
            "records_updated": 0,
            "records_failed": 0,
            "errors": [],
            "warnings": []
        }
        
    def generate_batch_id(self) -> str:
        """Generate unique batch ID for import"""
        return f"EQUIP_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def find_equipment_files(self) -> List[str]:
        """Find equipment CSV files"""
        patterns = [
            "equip*.csv",
            "equipment*.csv", 
            "equipPOR*.csv"
        ]
        
        all_files = []
        for pattern in patterns:
            file_pattern = os.path.join(self.csv_base_path, pattern)
            all_files.extend(glob.glob(file_pattern))
            
        # Sort by modification time (newest first)
        if all_files:
            all_files.sort(key=os.path.getmtime, reverse=True)
            
        return all_files
    
    def analyze_csv_structure(self, file_path: str) -> Dict[str, Any]:
        """Analyze the structure and quality of equipment CSV file"""
        try:
            # Read first chunk to analyze structure
            df_sample = pd.read_csv(file_path, nrows=1000, low_memory=False)
            
            analysis = {
                "file_path": file_path,
                "total_rows": None,  # Will be calculated
                "total_columns": len(df_sample.columns),
                "column_names": list(df_sample.columns),
                "data_types": df_sample.dtypes.to_dict(),
                "missing_data": {},
                "data_quality_issues": [],
                "sample_data": df_sample.head(3).to_dict('records')
            }
            
            # Get actual row count
            total_rows = sum(1 for line in open(file_path)) - 1  # Subtract header
            analysis["total_rows"] = total_rows
            
            # Analyze missing data
            missing_counts = df_sample.isnull().sum()
            analysis["missing_data"] = {col: int(count) for col, count in missing_counts.items() if count > 0}
            
            # Check for data quality issues
            quality_issues = []
            
            # Check key columns
            if 'ItemNum' in df_sample.columns:
                duplicates = df_sample['ItemNum'].duplicated().sum()
                if duplicates > 0:
                    quality_issues.append(f"ItemNum duplicates found: {duplicates}")
                    
            # Check numeric columns for non-numeric values
            numeric_columns = ['Qty', 'Sell Price', 'RetailPrice', 'Deposit']
            for col in numeric_columns:
                if col in df_sample.columns:
                    try:
                        pd.to_numeric(df_sample[col], errors='coerce')
                    except Exception as e:
                        quality_issues.append(f"Non-numeric data in {col}: {str(e)}")
            
            # Check date columns
            date_columns = ['Last Purchase Date', 'Expiration Date', 'Warranty Date']
            for col in date_columns:
                if col in df_sample.columns:
                    try:
                        pd.to_datetime(df_sample[col], errors='coerce')
                    except Exception as e:
                        quality_issues.append(f"Invalid dates in {col}: {str(e)}")
                        
            analysis["data_quality_issues"] = quality_issues
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze CSV structure: {str(e)}")
            raise
    
    def parse_currency(self, value) -> Optional[Decimal]:
        """Parse currency values from CSV"""
        if pd.isna(value) or value == '' or value is None:
            return None
            
        if isinstance(value, (int, float)):
            return Decimal(str(value)) if not pd.isna(value) else None
        
        # Clean string values
        clean_value = str(value).strip()
        clean_value = re.sub(r'[\$,\s]', '', clean_value)
        
        if not clean_value or clean_value in ['-', 'N/A', 'n/a', 'NULL']:
            return None
            
        try:
            return Decimal(clean_value)
        except (ValueError, InvalidOperation):
            return None
    
    def parse_date(self, value) -> Optional[datetime]:
        """Parse date values from CSV"""
        if pd.isna(value) or value == '' or value is None:
            return None
            
        if isinstance(value, str) and value.strip() in ['', 'NULL', '12/30/1899 0:00', '12/30/1899 12:00 AM']:
            return None
            
        try:
            return pd.to_datetime(value, errors='coerce')
        except Exception:
            return None
    
    def parse_boolean(self, value) -> bool:
        """Parse boolean values from CSV"""
        if pd.isna(value) or value == '':
            return False
            
        if isinstance(value, bool):
            return value
            
        str_val = str(value).strip().upper()
        return str_val in ['TRUE', '1', 'Y', 'YES', 'ON']
    
    def parse_integer(self, value) -> Optional[int]:
        """Parse integer values from CSV"""
        if pd.isna(value) or value == '' or value is None:
            return None
            
        try:
            return int(float(str(value).strip()))
        except (ValueError, TypeError):
            return None
    
    def parse_float(self, value) -> Optional[float]:
        """Parse float values from CSV"""
        if pd.isna(value) or value == '' or value is None:
            return None
            
        try:
            return float(str(value).strip())
        except (ValueError, TypeError):
            return None
    
    def clean_equipment_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate equipment data"""
        logger.info(f"Cleaning equipment data with {len(df)} rows")
        
        # Create a copy to avoid modifying original
        cleaned_df = df.copy()
        
        # Handle missing ItemNum
        cleaned_df = cleaned_df.dropna(subset=['ItemNum'])
        
        # Clean string columns
        string_columns = ['Key', 'Name', 'Loc', 'Category', 'Department', 'Type Desc', 
                         'Group', 'MANF', 'ModelNo', 'SerialNo', 'PartNo']
        for col in string_columns:
            if col in cleaned_df.columns:
                cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
                cleaned_df[col] = cleaned_df[col].replace('nan', '')
        
        # Clean numeric columns
        numeric_columns = {
            'Qty': 'parse_integer',
            'T/O MTD': 'parse_currency',
            'T/O YTD': 'parse_currency', 
            'T/O LTD': 'parse_currency',
            'RepairCost MTD': 'parse_currency',
            'RepairCost LTD': 'parse_currency',
            'Sell Price': 'parse_currency',
            'RetailPrice': 'parse_currency',
            'Deposit': 'parse_currency',
            'DamageWaiver%': 'parse_float'
        }
        
        for col, parser_method in numeric_columns.items():
            if col in cleaned_df.columns:
                parser = getattr(self, parser_method)
                cleaned_df[col] = cleaned_df[col].apply(parser)
        
        # Clean period and rate columns
        for i in range(1, 11):
            period_col = f'Period {i}'
            rate_col = f'Rate {i}'
            
            if period_col in cleaned_df.columns:
                cleaned_df[period_col] = cleaned_df[period_col].apply(self.parse_integer)
            if rate_col in cleaned_df.columns:
                cleaned_df[rate_col] = cleaned_df[rate_col].apply(self.parse_currency)
        
        # Clean date columns
        date_columns = ['Last Purchase Date', 'Expiration Date', 'Warranty Date']
        for col in date_columns:
            if col in cleaned_df.columns:
                cleaned_df[col] = cleaned_df[col].apply(self.parse_date)
        
        # Clean boolean columns
        boolean_columns = ['NonTaxable', 'Inactive']
        for col in boolean_columns:
            if col in cleaned_df.columns:
                cleaned_df[col] = cleaned_df[col].apply(self.parse_boolean)
        
        logger.info(f"Cleaned data resulting in {len(cleaned_df)} rows")
        return cleaned_df
    
    def import_equipment_data(self, file_path: str) -> Dict[str, Any]:
        """Import equipment data from CSV file"""
        self.batch_id = self.generate_batch_id()
        
        # Create import log
        self.import_log = EquipmentImportLog(
            batch_id=self.batch_id,
            filename=os.path.basename(file_path),
            import_type='full',
            started_at=datetime.utcnow()
        )
        db.session.add(self.import_log)
        db.session.commit()
        
        try:
            logger.info(f"Starting equipment import from {file_path}")
            
            # Analyze file structure first
            analysis = self.analyze_csv_structure(file_path)
            logger.info(f"CSV Analysis: {analysis['total_rows']} rows, {analysis['total_columns']} columns")
            
            # Read the full CSV file
            df = pd.read_csv(file_path, low_memory=False)
            self.import_stats["records_processed"] = len(df)
            
            # Clean the data
            df_clean = self.clean_equipment_data(df)
            
            # Import records
            imported_count = 0
            updated_count = 0
            
            # Process in batches to manage memory
            batch_size = 1000
            total_batches = (len(df_clean) + batch_size - 1) // batch_size
            
            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = min((batch_num + 1) * batch_size, len(df_clean))
                batch_df = df_clean.iloc[start_idx:end_idx]
                
                logger.info(f"Processing batch {batch_num + 1}/{total_batches} ({len(batch_df)} records)")
                
                for index, row in batch_df.iterrows():
                    try:
                        item_num = str(row.get('ItemNum', '')).strip()
                        if not item_num:
                            continue
                            
                        # Check if equipment item already exists
                        existing_item = EquipmentItem.query.filter_by(item_num=item_num).first()
                        
                        if existing_item:
                            # Update existing item
                            self._update_equipment_item(existing_item, row)
                            updated_count += 1
                        else:
                            # Create new item
                            new_item = self._create_equipment_item(row, self.batch_id)
                            db.session.add(new_item)
                            imported_count += 1
                            
                    except Exception as e:
                        self.import_stats["errors"].append(f"Row {index}: {str(e)}")
                        self.import_stats["records_failed"] += 1
                        logger.error(f"Failed to import row {index}: {str(e)}")
                        continue
                
                # Commit batch
                try:
                    db.session.commit()
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Failed to commit batch {batch_num + 1}: {str(e)}")
                    raise
            
            # Update statistics
            self.import_stats["records_imported"] = imported_count
            self.import_stats["records_updated"] = updated_count
            
            # Update import log
            self.import_log.records_processed = self.import_stats["records_processed"]
            self.import_log.records_imported = imported_count
            self.import_log.records_updated = updated_count
            self.import_log.records_failed = self.import_stats["records_failed"]
            self.import_log.status = 'success'
            self.import_log.completed_at = datetime.utcnow()
            self.import_log.duration_seconds = (self.import_log.completed_at - self.import_log.started_at).total_seconds()
            self.import_log.warnings = json.dumps(self.import_stats["warnings"])
            
            if self.import_stats["errors"]:
                self.import_log.error_message = json.dumps(self.import_stats["errors"][:10])  # First 10 errors
            
            db.session.commit()
            
            logger.info(f"Equipment import completed: {imported_count} imported, {updated_count} updated")
            
            return {
                "success": True,
                "message": f"Successfully processed {self.import_stats['records_processed']} equipment records",
                "batch_id": self.batch_id,
                "stats": self.import_stats,
                "analysis": analysis
            }
            
        except Exception as e:
            error_msg = f"Equipment import failed: {str(e)}"
            logger.error(error_msg)
            
            # Update import log with failure
            if self.import_log:
                self.import_log.status = 'failed'
                self.import_log.error_message = error_msg
                self.import_log.completed_at = datetime.utcnow()
                db.session.commit()
            
            return {
                "success": False,
                "error": error_msg,
                "batch_id": self.batch_id,
                "stats": self.import_stats
            }
    
    def _create_equipment_item(self, row: pd.Series, batch_id: str) -> EquipmentItem:
        """Create new equipment item from CSV row"""
        item = EquipmentItem(
            item_num=str(row.get('ItemNum', '')).strip(),
            key=str(row.get('Key', '')).strip(),
            name=str(row.get('Name', '')).strip(),
            location=str(row.get('Loc', '')).strip(),
            category=str(row.get('Category', '')).strip(),
            department=str(row.get('Department', '')).strip(),
            type_desc=str(row.get('Type Desc', '')).strip(),
            qty=row.get('Qty', 0),
            home_store=str(row.get('Home Store', '')).strip(),
            current_store=str(row.get('Current Store', '')).strip(),
            equipment_group=str(row.get('Group', '')).strip(),
            manufacturer=str(row.get('MANF', '')).strip(),
            model_no=str(row.get('ModelNo', '')).strip(),
            serial_no=str(row.get('SerialNo', '')).strip(),
            part_no=str(row.get('PartNo', '')).strip(),
            license_no=str(row.get('License No', '')).strip(),
            model_year=str(row.get('Model Year', '')).strip(),
            turnover_mtd=row.get('T/O MTD', 0),
            turnover_ytd=row.get('T/O YTD', 0),
            turnover_ltd=row.get('T/O LTD', 0),
            repair_cost_mtd=row.get('RepairCost MTD', 0),
            repair_cost_ltd=row.get('RepairCost LTD', 0),
            sell_price=row.get('Sell Price', 0),
            retail_price=row.get('RetailPrice', 0),
            deposit=row.get('Deposit', 0),
            damage_waiver_percent=row.get('DamageWaiver%', 0),
            non_taxable=row.get('NonTaxable', False),
            inactive=row.get('Inactive', False),
            last_purchase_date=row.get('Last Purchase Date'),
            last_purchase_price=row.get('Last Purchase Price', 0),
            import_batch_id=batch_id
        )
        
        # Add period and rate data
        for i in range(1, 11):
            period_val = row.get(f'Period {i}', 0)
            rate_val = row.get(f'Rate {i}', 0)
            setattr(item, f'period_{i}', period_val)
            setattr(item, f'rate_{i}', rate_val)
        
        return item
    
    def _update_equipment_item(self, item: EquipmentItem, row: pd.Series):
        """Update existing equipment item with new data"""
        # Update key fields
        item.name = str(row.get('Name', '')).strip()
        item.category = str(row.get('Category', '')).strip()
        item.qty = row.get('Qty', 0)
        item.current_store = str(row.get('Current Store', '')).strip()
        item.sell_price = row.get('Sell Price', 0)
        item.retail_price = row.get('RetailPrice', 0)
        item.inactive = row.get('Inactive', False)
        item.updated_at = datetime.utcnow()
        
        # Update financial data
        item.turnover_mtd = row.get('T/O MTD', 0)
        item.turnover_ytd = row.get('T/O YTD', 0)
        item.turnover_ltd = row.get('T/O LTD', 0)

# Singleton instance
_equipment_import_service = None

def get_equipment_import_service():
    """Get or create equipment import service instance"""
    global _equipment_import_service
    if _equipment_import_service is None:
        _equipment_import_service = EquipmentImportService()
    return _equipment_import_service