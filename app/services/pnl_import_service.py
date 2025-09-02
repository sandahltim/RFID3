# app/services/pnl_import_service.py
"""
P&L (Profit and Loss) CSV Import Service - UPDATED FOR CENTRALIZED STORE CONFIG
Handles import of financial data with monthly actuals and projections
Uses centralized store configuration for consistent data correlation
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

# Import centralized store configuration
import sys
sys.path.append('/home/tim/RFID3/app/config')
from stores import STORES, get_store_name, get_all_store_codes, get_active_store_codes

logger = get_logger(__name__)

class PnLImportService:
    def __init__(self):
        self.database_url = (
            f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}/{DB_CONFIG['database']}"
        )
        self.engine = create_engine(self.database_url, pool_pre_ping=True)
        self.Session = sessionmaker(bind=self.engine)
        
        # Use centralized store configuration - NO MORE HARDCODED MAPPINGS
        self.store_mappings = {store_code: get_store_name(store_code) for store_code in get_all_store_codes()}
        logger.info(f"Loaded store mappings from centralized config: {self.store_mappings}")
        
        # P&L metric types supported - enhanced with actual CSV structure analysis
        self.metric_types = [
            'Rental Revenue',
            'Sales Revenue', 
            'COGS',
            'Gross Profit',
            'Operating Expenses',
            'Net Income',
            # Additional P&L metrics found in CSV analysis
            'Other Revenue',
            'Total Revenue',
            'Total COGS',
            'Total Expenses'
        ]

    def clean_currency_value(self, value: Any) -> Optional[Decimal]:
        """Clean and convert currency values to Decimal"""
        if pd.isna(value) or value == '' or value is None:
            return None
            
        # Convert to string and clean
        str_val = str(value).strip()
        if not str_val or str_val.lower() in ['nan', 'null', 'none', '']:
            return None
            
        # Remove currency symbols, commas, parentheses
        cleaned = re.sub(r'[\$,\(\)]', '', str_val)
        
        # Handle negative values in parentheses
        if '(' in str_val and ')' in str_val:
            cleaned = '-' + cleaned
            
        try:
            return Decimal(cleaned)
        except (ValueError, InvalidOperation):
            logger.debug(f"Could not parse currency value: {value}")
            return None

    def parse_month_year(self, month_str: str, year_str: Optional[str]) -> Optional[date]:
        """Parse month and year strings into a date object"""
        if not month_str or month_str.upper() in ['TTM', 'TOTAL', '']:
            return None
            
        # Month mapping
        month_mapping = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
            'jun': 6, 'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        try:
            # Try to extract year from year_str
            year = None
            if year_str and str(year_str).replace('.0', '').isdigit():
                year = int(float(year_str))
            
            # Try to find month
            month_clean = month_str.lower().strip()
            month_num = month_mapping.get(month_clean)
            
            if month_num and year and 2020 <= year <= 2030:
                return date(year, month_num, 1)
            else:
                logger.debug(f"Could not parse date: month='{month_str}' year='{year_str}'")
                return None
                
        except (ValueError, TypeError) as e:
            logger.debug(f"Date parsing error: {e}")
            return None

    def extract_financial_data_from_csv(self, csv_path: str) -> List[Dict]:
        """Extract and normalize financial data from P&L CSV with corrected structure parsing"""
        logger.info(f"Starting corrected P&L CSV import from: {csv_path}")
        
        try:
            # Read the full CSV
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            logger.info(f"Read full CSV with shape: {df.shape}")
            
            financial_records = []
            
            # Based on CSV analysis:
            # Row 1 (index 0): Headers showing store codes and categories
            # Row 2+ (index 1+): Monthly data with format: Month, Year, Store1_Value, Store2_Value, ...
            # TTM rows should be skipped
            
            for idx, row in df.iterrows():
                # Skip header row (index 0)
                if idx == 0:
                    continue
                
                # Extract month and year from first two columns
                month_str = str(row.iloc[0]).strip() if not pd.isna(row.iloc[0]) else ""
                year_str = str(row.iloc[1]).strip() if len(row) > 1 and not pd.isna(row.iloc[1]) else ""
                
                # Skip TTM (Trailing Twelve Months) and other summary rows
                if not month_str or month_str.upper() in ['TTM', 'TOTAL', ''] or not year_str:
                    continue
                
                # Parse date
                parsed_date = self.parse_month_year(month_str, year_str)
                if not parsed_date:
                    logger.debug(f"Skipping row {idx}: could not parse date from '{month_str}' '{year_str}'")
                    continue
                
                logger.debug(f"Processing row {idx}: {month_str} {year_str} -> {parsed_date}")
                
                # Extract store data from specific columns
                # Based on header analysis: columns 2-5 contain the main store revenue data
                store_data_positions = {
                    2: '3607',  # Wayzata
                    3: '6800',  # Brooklyn Park
                    4: '728',   # Elk River  
                    5: '8101'   # Fridley
                }
                
                for col_pos, store_code in store_data_positions.items():
                    if col_pos < len(row):
                        value = row.iloc[col_pos]
                        cleaned_value = self.clean_currency_value(value)
                        
                        if cleaned_value is not None and cleaned_value != 0:
                            record = {
                                'store_code': store_code,
                                'store_name': get_store_name(store_code),
                                'month_year': parsed_date,
                                'metric_type': 'Rental Revenue',  # Primary revenue metric
                                'actual_amount': cleaned_value,
                                'projected_amount': None,
                                'data_source': 'CSV_IMPORT_PL'
                            }
                            financial_records.append(record)
                            logger.debug(f"Added record: {store_code} {parsed_date} ${cleaned_value}")
                
                # Also extract additional revenue categories from other column groups
                # Columns 7-10 appear to be "Sales Revenue" for each store
                sales_revenue_positions = {
                    7: '3607',   # Wayzata Sales Revenue
                    8: '6800',   # Brooklyn Park Sales Revenue
                    9: '728',    # Elk River Sales Revenue
                    10: '8101'   # Fridley Sales Revenue
                }
                
                for col_pos, store_code in sales_revenue_positions.items():
                    if col_pos < len(row):
                        value = row.iloc[col_pos]
                        cleaned_value = self.clean_currency_value(value)
                        
                        if cleaned_value is not None and cleaned_value != 0:
                            record = {
                                'store_code': store_code,
                                'store_name': get_store_name(store_code),
                                'month_year': parsed_date,
                                'metric_type': 'Sales Revenue',
                                'actual_amount': cleaned_value,
                                'projected_amount': None,
                                'data_source': 'CSV_IMPORT_PL'
                            }
                            financial_records.append(record)
                            logger.debug(f"Added sales record: {store_code} {parsed_date} ${cleaned_value}")
            
            logger.info(f"Extracted {len(financial_records)} financial records from P&L CSV")
            return financial_records
            
        except Exception as e:
            logger.error(f"Error parsing P&L CSV: {e}")
            raise

    def import_pnl_csv_data(self, csv_path: str, limit: int = 25000) -> Dict[str, Any]:
        """Import P&L data from CSV file with enhanced correlation"""
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
                            # Insert or update record using proper store_code correlation
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
        """Generate summary statistics after import using centralized store config"""
        try:
            # Get counts by store and metric type
            summary_sql = text("""
                SELECT 
                    pp.store_code,
                    pp.metric_type,
                    COUNT(*) as record_count,
                    MIN(pp.month_year) as earliest_date,
                    MAX(pp.month_year) as latest_date,
                    SUM(pp.actual_amount) as total_actual,
                    AVG(pp.actual_amount) as avg_actual
                FROM pos_pnl pp 
                WHERE pp.import_date >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
                GROUP BY pp.store_code, pp.metric_type
                ORDER BY pp.store_code, pp.metric_type
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
            
            # Organize by store and metric using centralized store names
            for row in results:
                store_code = row.store_code
                store_name = get_store_name(store_code)  # Use centralized config
                metric_type = row.metric_type
                
                if store_code not in summary["by_store"]:
                    summary["by_store"][store_code] = {
                        "store_name": store_name,
                        "metrics": {}
                    }
                
                summary["by_store"][store_code]["metrics"][metric_type] = {
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
        """Get P&L analytics with variance analysis using centralized store config"""
        session = self.Session()
        
        try:
            # Updated query to work with centralized store configuration
            base_query = """
                SELECT 
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
                WHERE 1=1
            """
            
            params = {}
            if store_code and store_code != 'all':
                base_query += " AND pp.store_code = :store_code"
                params['store_code'] = store_code
                
            if metric_type:
                base_query += " AND pp.metric_type = :metric_type"
                params['metric_type'] = metric_type
                
            base_query += " ORDER BY pp.store_code, pp.metric_type, pp.month_year"
            
            results = session.execute(text(base_query), params).fetchall()
            
            # Process results with centralized store names
            analytics_data = []
            for row in results:
                analytics_data.append({
                    'store_code': row.store_code,
                    'store_name': get_store_name(row.store_code),  # Use centralized config
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
                "record_count": len(analytics_data),
                "stores": {code: get_store_name(code) for code in get_active_store_codes()}
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

    def validate_store_correlations(self) -> Dict[str, Any]:
        """Validate that P&L data correlates properly with centralized store config"""
        session = self.Session()
        
        try:
            # Check which stores have P&L data vs centralized config
            pnl_stores_sql = text("SELECT DISTINCT store_code FROM pos_pnl ORDER BY store_code")
            pnl_stores = [row[0] for row in session.execute(pnl_stores_sql).fetchall()]
            
            centralized_stores = get_all_store_codes()
            active_stores = get_active_store_codes()
            
            correlation_report = {
                "pnl_stores": pnl_stores,
                "centralized_stores": centralized_stores,
                "active_stores": active_stores,
                "missing_in_pnl": [s for s in centralized_stores if s not in pnl_stores],
                "missing_in_config": [s for s in pnl_stores if s not in centralized_stores],
                "properly_correlated": [s for s in pnl_stores if s in centralized_stores],
                "correlation_percentage": len([s for s in pnl_stores if s in centralized_stores]) / max(len(pnl_stores), 1) * 100
            }
            
            logger.info(f"Store correlation validation: {correlation_report['correlation_percentage']:.1f}% properly correlated")
            
            return {
                "success": True,
                "correlation_report": correlation_report
            }
            
        except Exception as e:
            logger.error(f"Error validating store correlations: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            session.close()
