# app/services/pnl_import_service.py
"""
P&L (Profit and Loss) CSV Import Service
Handles import of financial data with monthly actuals and projections
"""

import pandas as pd
import numpy as np
import os
import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import Dict, List, Tuple, Optional, Any
import logging
from config import DB_CONFIG
from .logger import get_logger

logger = get_logger(__name__)

class PnLImportService:
    def __init__(self):
        self.database_url = (
            f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}/{DB_CONFIG['database']}"
        )
        self.engine = create_engine(self.database_url, pool_pre_ping=True)
        self.Session = sessionmaker(bind=self.engine)
        
        # Store mappings for data normalization
        self.store_mappings = {
            '3607': 'Wayzata',
            '6800': 'Brooklyn Park', 
            '728': 'Elk River',
            '8101': 'Fridley'
        }
        
        # P&L metric types supported
        self.metric_types = [
            'Rental Revenue',
            'Sales Revenue', 
            'COGS',
            'Gross Profit',
            'Operating Expenses',
            'Net Income'
        ]

    def clean_currency_value(self, value: Any) -> Optional[Decimal]:
        """Clean and convert currency values to Decimal"""
        if pd.isna(value) or value == '' or value is None:
            return None
            
        # Convert to string and clean
        str_val = str(value).strip()
        if not str_val or str_val.lower() in ['nan', 'null', 'none']:
            return None
            
        # Remove currency symbols, commas, parentheses
        cleaned = re.sub(r'[\$,\(\)]', '', str_val)
        
        # Handle negative values in parentheses
        if '(' in str_val and ')' in str_val:
            cleaned = '-' + cleaned
            
        try:
            return Decimal(cleaned)
        except (ValueError, InvalidOperation):
            logger.warning(f"Could not parse currency value: {value}")
            return None

    def parse_date_from_columns(self, month_col: str, year: int) -> Optional[date]:
        """Parse date from month column name and year"""
        month_mapping = {
            'January': 1, 'February': 2, 'March': 3, 'April': 4,
            'May': 5, 'June': 6, 'July': 7, 'August': 8,
            'September': 9, 'October': 10, 'November': 11, 'December': 12,
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
            'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        try:
            if month_col in month_mapping:
                return date(year, month_mapping[month_col], 1)
            # Try direct month name lookup
            for month_name, month_num in month_mapping.items():
                if month_name.lower() in month_col.lower():
                    return date(year, month_num, 1)
        except ValueError as e:
            logger.warning(f"Could not parse date from {month_col}, {year}: {e}")
            
        return None

    def extract_financial_data_from_csv(self, csv_path: str) -> List[Dict]:
        """Extract and normalize financial data from P&L CSV"""
        logger.info(f"Starting P&L CSV import from: {csv_path}")
        
        try:
            # Read the CSV with specific encoding and handle complex format
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            logger.info(f"Read CSV with shape: {df.shape}")
            
            # The CSV has a complex structure - analyze first few rows
            financial_records = []
            current_metric_type = None
            
            for idx, row in df.iterrows():
                # Skip first few header rows
                if idx < 4:
                    continue
                    
                # Check if this row defines a metric type
                first_col = str(row.iloc[0]).strip()
                if first_col in self.metric_types:
                    current_metric_type = first_col
                    logger.debug(f"Found metric type: {current_metric_type}")
                    continue
                    
                # Check if this row contains store data
                if current_metric_type and first_col in self.store_mappings:
                    store_code = first_col
                    store_name = self.store_mappings[store_code]
                    
                    # Extract data from columns - need to parse the complex date structure
                    # Looking at the CSV, columns represent months/years in different sections
                    col_names = df.columns.tolist()
                    
                    # Process actual data columns (skip first column which is store code)
                    for col_idx in range(1, len(row)):
                        if col_idx >= len(col_names):
                            break
                            
                        value = row.iloc[col_idx]
                        cleaned_value = self.clean_currency_value(value)
                        
                        if cleaned_value is not None and cleaned_value != 0:
                            # Try to determine date from column structure
                            # This is complex due to the CSV format - using position-based logic
                            
                            # Based on CSV analysis: columns 1-7 are 2021, 8-21 are 2022, etc.
                            year = 2021
                            month = col_idx
                            
                            if col_idx >= 8:
                                year = 2022
                                month = col_idx - 7
                            if col_idx >= 21:
                                year = 2023
                                month = col_idx - 20
                            if col_idx >= 34:
                                year = 2024
                                month = col_idx - 33
                            if col_idx >= 47:
                                year = 2025
                                month = col_idx - 46
                                
                            # Adjust month to be within 1-12
                            if month > 12:
                                continue
                                
                            try:
                                month_date = date(year, month, 1)
                                
                                record = {
                                    'store_code': store_code,
                                    'store_name': store_name,
                                    'month_year': month_date,
                                    'metric_type': current_metric_type,
                                    'actual_amount': cleaned_value,
                                    'projected_amount': None,  # Will be determined later
                                    'data_source': 'CSV_IMPORT'
                                }
                                financial_records.append(record)
                                
                            except ValueError:
                                continue
            
            logger.info(f"Extracted {len(financial_records)} financial records")
            return financial_records
            
        except Exception as e:
            logger.error(f"Error parsing P&L CSV: {e}")
            raise

    def import_pnl_csv_data(self, csv_path: str, limit: int = 25000) -> Dict[str, Any]:
        """Import P&L data from CSV file"""
        logger.info(f"Starting P&L import from {csv_path}, limit: {limit}")
        
        try:
            # Extract data from CSV
            financial_data = self.extract_financial_data_from_csv(csv_path)
            
            if not financial_data:
                return {
                    "success": False,
                    "error": "No financial data found in CSV",
                    "records_imported": 0
                }
            
            # Limit records if specified
            if limit and len(financial_data) > limit:
                financial_data = financial_data[:limit]
                logger.info(f"Limited import to {limit} records")
            
            # Import data in chunks
            chunk_size = 1000
            imported_count = 0
            duplicate_count = 0
            error_count = 0
            
            session = self.Session()
            
            try:
                for i in range(0, len(financial_data), chunk_size):
                    chunk = financial_data[i:i + chunk_size]
                    logger.debug(f"Processing chunk {i//chunk_size + 1}, size: {len(chunk)}")
                    
                    for record in chunk:
                        try:
                            # Insert or update record
                            insert_sql = text("""
                                INSERT INTO pos_pnl 
                                (store_code, month_year, metric_type, actual_amount, 
                                 projected_amount, data_source, import_date)
                                VALUES 
                                (:store_code, :month_year, :metric_type, :actual_amount,
                                 :projected_amount, :data_source, NOW())
                                ON DUPLICATE KEY UPDATE
                                actual_amount = VALUES(actual_amount),
                                projected_amount = VALUES(projected_amount),
                                updated_at = NOW()
                            """)
                            
                            session.execute(insert_sql, {
                                'store_code': record['store_code'],
                                'month_year': record['month_year'],
                                'metric_type': record['metric_type'],
                                'actual_amount': record['actual_amount'],
                                'projected_amount': record.get('projected_amount'),
                                'data_source': record['data_source']
                            })
                            
                            imported_count += 1
                            
                        except IntegrityError:
                            duplicate_count += 1
                            continue
                        except Exception as e:
                            logger.warning(f"Error importing record: {e}")
                            error_count += 1
                            continue
                    
                    # Commit each chunk
                    session.commit()
                    logger.debug(f"Committed chunk {i//chunk_size + 1}")
                
                # Generate summary statistics
                summary_stats = self.get_import_summary(session)
                
                logger.info(f"P&L import completed: {imported_count} imported, "
                           f"{duplicate_count} duplicates, {error_count} errors")
                
                return {
                    "success": True,
                    "records_imported": imported_count,
                    "duplicates_skipped": duplicate_count,
                    "errors": error_count,
                    "summary_stats": summary_stats,
                    "stores_processed": list(self.store_mappings.keys()),
                    "metric_types": self.metric_types
                }
                
            except Exception as e:
                session.rollback()
                logger.error(f"Database error during P&L import: {e}")
                raise
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"P&L import failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "records_imported": 0
            }

    def get_import_summary(self, session) -> Dict[str, Any]:
        """Generate summary statistics after import"""
        try:
            # Get counts by store and metric type
            summary_sql = text("""
                SELECT 
                    store_code,
                    metric_type,
                    COUNT(*) as record_count,
                    MIN(month_year) as earliest_date,
                    MAX(month_year) as latest_date,
                    SUM(actual_amount) as total_actual,
                    AVG(actual_amount) as avg_actual
                FROM pos_pnl 
                WHERE import_date >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                GROUP BY store_code, metric_type
                ORDER BY store_code, metric_type
            """)
            
            results = session.execute(summary_sql).fetchall()
            
            summary = {
                "total_records": sum(r.record_count for r in results),
                "date_range": {
                    "earliest": min(r.earliest_date for r in results) if results else None,
                    "latest": max(r.latest_date for r in results) if results else None
                },
                "by_store": {},
                "by_metric": {}
            }
            
            # Organize by store and metric
            for row in results:
                store_code = row.store_code
                metric_type = row.metric_type
                
                if store_code not in summary["by_store"]:
                    summary["by_store"][store_code] = {}
                
                summary["by_store"][store_code][metric_type] = {
                    "records": row.record_count,
                    "total_actual": float(row.total_actual) if row.total_actual else 0,
                    "avg_actual": float(row.avg_actual) if row.avg_actual else 0
                }
                
                if metric_type not in summary["by_metric"]:
                    summary["by_metric"][metric_type] = 0
                summary["by_metric"][metric_type] += row.record_count
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating import summary: {e}")
            return {"error": str(e)}

    def get_pnl_analytics(self, store_code: Optional[str] = None, 
                         metric_type: Optional[str] = None) -> Dict[str, Any]:
        """Get P&L analytics with variance analysis"""
        session = self.Session()
        
        try:
            base_query = """
                SELECT 
                    psm.store_name,
                    pp.store_code,
                    pp.metric_type,
                    YEAR(pp.month_year) as year,
                    MONTH(pp.month_year) as month,
                    pp.month_year,
                    pp.actual_amount,
                    pp.projected_amount,
                    (pp.actual_amount - COALESCE(pp.projected_amount, 0)) as variance,
                    CASE 
                        WHEN pp.projected_amount > 0 THEN 
                            ((pp.actual_amount - pp.projected_amount) / pp.projected_amount * 100)
                        ELSE NULL 
                    END as variance_percentage,
                    pp.percentage_total_revenue
                FROM pos_pnl pp
                LEFT JOIN pos_store_mapping psm ON pp.store_code = psm.store_code
                WHERE psm.active = TRUE
            """
            
            params = {}
            if store_code:
                base_query += " AND pp.store_code = :store_code"
                params['store_code'] = store_code
                
            if metric_type:
                base_query += " AND pp.metric_type = :metric_type"
                params['metric_type'] = metric_type
                
            base_query += " ORDER BY pp.store_code, pp.metric_type, pp.month_year"
            
            results = session.execute(text(base_query), params).fetchall()
            
            # Process results
            analytics_data = []
            for row in results:
                analytics_data.append({
                    'store_name': row.store_name,
                    'store_code': row.store_code,
                    'metric_type': row.metric_type,
                    'year': row.year,
                    'month': row.month,
                    'month_year': row.month_year.strftime('%Y-%m-%d'),
                    'actual_amount': float(row.actual_amount) if row.actual_amount else 0,
                    'projected_amount': float(row.projected_amount) if row.projected_amount else 0,
                    'variance': float(row.variance) if row.variance else 0,
                    'variance_percentage': float(row.variance_percentage) if row.variance_percentage else 0,
                    'percentage_total_revenue': float(row.percentage_total_revenue) if row.percentage_total_revenue else 0
                })
            
            return {
                "success": True,
                "data": analytics_data,
                "record_count": len(analytics_data)
            }
            
        except Exception as e:
            logger.error(f"Error getting P&L analytics: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": []
            }
        finally:
            session.close()