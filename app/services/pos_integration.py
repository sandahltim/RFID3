"""
POS Integration Service
Handles CSV imports, data validation, and correlation with RFID system
"""

import os
import csv
import json
import hashlib
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
from sqlalchemy import text, create_engine
from sqlalchemy.exc import SQLAlchemyError
import logging
from pathlib import Path

class POSIntegrationService:
    """Service for integrating POS CSV data with RFID inventory system"""
    
    def __init__(self, db_connection, logger=None):
        """
        Initialize POS Integration Service
        
        Args:
            db_connection: SQLAlchemy database connection
            logger: Optional logger instance
        """
        self.db = db_connection
        self.logger = logger or logging.getLogger(__name__)
        self.pos_directory = Path("/home/tim/RFID3/shared/POR")
        
        # Column mappings for different CSV types
        self.column_mappings = {
            'equipment': {
                'ItemNum': 'item_num',
                'Key': 'item_key',
                'Name': 'name',
                'Loc': 'location',
                'Category': 'category',
                'Department': 'department',
                'Type Desc': 'type_desc',
                'Qty': 'quantity',
                'Home Store': 'home_store',
                'Current Store': 'current_store',
                'Group': 'item_group',
                'MANF': 'manufacturer',
                'ModelNo': 'model_no',
                'SerialNo': 'serial_no',
                'PartNo': 'part_no',
                'License No': 'license_no',
                'Model Year': 'model_year',
                'T/O MTD': 'turnover_mtd',
                'T/O YTD': 'turnover_ytd',
                'T/O LTD': 'turnover_ltd'
            },
            'itemlist': {
                'id_item_master': 'item_id',
                'tag_id': 'tag_id',
                'serial_number': 'serial_number',
                'rental_class_num': 'rental_class_num',
                'common_name': 'common_name',
                'quality': 'quality',
                'bin_location': 'bin_location',
                'status': 'status'
            }
        }
        
    def process_csv_file(self, file_path: str, file_type: str = 'equipment') -> Dict[str, Any]:
        """
        Process a POS CSV file and import to staging table
        
        Args:
            file_path: Path to CSV file
            file_type: Type of CSV (equipment, itemlist, etc.)
            
        Returns:
            Dictionary with import statistics
        """
        try:
            # Generate batch ID
            batch_id = self._generate_batch_id(file_path)
            file_name = os.path.basename(file_path)
            
            self.logger.info(f"Processing CSV file: {file_name}, Batch ID: {batch_id}")
            
            # Read CSV with pandas for better handling
            df = pd.read_csv(file_path, low_memory=False)
            
            # Get column mapping for this file type
            column_map = self.column_mappings.get(file_type, {})
            
            # Rename columns based on mapping
            df.rename(columns=column_map, inplace=True)
            
            # Add metadata columns
            df['import_batch_id'] = batch_id
            df['file_name'] = file_name
            df['import_date'] = datetime.now()
            df['processing_status'] = 'PENDING'
            
            # Clean numeric columns
            numeric_columns = ['quantity', 'turnover_mtd', 'turnover_ytd', 'turnover_ltd', 
                             'repair_cost_ltd', 'sell_price', 'retail_price']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Insert to staging table
            rows_imported = self._insert_to_staging(df, batch_id)
            
            # Process correlations
            correlation_results = self._process_correlations(batch_id)
            
            # Detect quality issues
            quality_issues = self._detect_quality_issues(batch_id)
            
            return {
                'success': True,
                'batch_id': batch_id,
                'file_name': file_name,
                'rows_imported': rows_imported,
                'correlations': correlation_results,
                'quality_issues': quality_issues
            }
            
        except Exception as e:
            self.logger.error(f"Error processing CSV file: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_batch_id(self, file_path: str) -> str:
        """Generate unique batch ID for import"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        file_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        return f"POS_{timestamp}_{file_hash}"
    
    def _insert_to_staging(self, df: pd.DataFrame, batch_id: str) -> int:
        """Insert DataFrame to pos_data_staging table"""
        try:
            # Prepare data for insertion
            records = df.to_dict('records')
            
            # Use bulk insert for performance
            with self.db.begin() as conn:
                # Clear old staging data for this batch (if reprocessing)
                conn.execute(text("""
                    DELETE FROM pos_data_staging 
                    WHERE import_batch_id = :batch_id
                """), {'batch_id': batch_id})
                
                # Insert new data
                for idx, record in enumerate(records):
                    record['row_number'] = idx + 1
                    
                    conn.execute(text("""
                        INSERT INTO pos_data_staging (
                            item_num, item_key, name, location, category, department,
                            type_desc, quantity, home_store, current_store, item_group,
                            manufacturer, model_no, serial_no, part_no, license_no,
                            model_year, turnover_mtd, turnover_ytd, turnover_ltd,
                            import_batch_id, file_name, row_number, import_date,
                            processing_status
                        ) VALUES (
                            :item_num, :item_key, :name, :location, :category, :department,
                            :type_desc, :quantity, :home_store, :current_store, :item_group,
                            :manufacturer, :model_no, :serial_no, :part_no, :license_no,
                            :model_year, :turnover_mtd, :turnover_ytd, :turnover_ltd,
                            :import_batch_id, :file_name, :row_number, :import_date,
                            :processing_status
                        )
                    """), record)
            
            return len(records)
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error during staging insert: {str(e)}")
            raise
    
    def _process_correlations(self, batch_id: str) -> Dict[str, int]:
        """Process correlations between POS and RFID data"""
        try:
            with self.db.begin() as conn:
                # Call stored procedure
                result = conn.execute(text("""
                    CALL sp_process_pos_import(:batch_id, :file_name)
                """), {
                    'batch_id': batch_id,
                    'file_name': f"batch_{batch_id}"
                })
                
                # Get results
                row = result.fetchone()
                if row:
                    return {
                        'matched': row[0],
                        'partial': row[1],
                        'orphaned': row[2],
                        'error': row[3]
                    }
            
            return {'matched': 0, 'partial': 0, 'orphaned': 0, 'error': 0}
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error processing correlations: {str(e)}")
            return {'error': str(e)}
    
    def _detect_quality_issues(self, batch_id: str) -> List[Dict]:
        """Detect data quality issues in imported data"""
        issues = []
        
        try:
            with self.db.begin() as conn:
                # Check for duplicates
                duplicates = conn.execute(text("""
                    SELECT item_num, COUNT(*) as cnt
                    FROM pos_data_staging
                    WHERE import_batch_id = :batch_id
                    GROUP BY item_num
                    HAVING COUNT(*) > 1
                """), {'batch_id': batch_id}).fetchall()
                
                for dup in duplicates:
                    issues.append({
                        'type': 'DUPLICATE',
                        'severity': 'MEDIUM',
                        'field': 'item_num',
                        'value': dup[0],
                        'count': dup[1]
                    })
                
                # Check for missing critical fields
                missing = conn.execute(text("""
                    SELECT COUNT(*) as cnt
                    FROM pos_data_staging
                    WHERE import_batch_id = :batch_id
                        AND (item_num IS NULL OR name IS NULL)
                """), {'batch_id': batch_id}).fetchone()
                
                if missing and missing[0] > 0:
                    issues.append({
                        'type': 'MISSING_DATA',
                        'severity': 'HIGH',
                        'field': 'item_num/name',
                        'count': missing[0]
                    })
                
                # Check for orphaned records (no match in RFID)
                orphaned = conn.execute(text("""
                    SELECT COUNT(*) as cnt
                    FROM pos_data_staging
                    WHERE import_batch_id = :batch_id
                        AND processing_status = 'ORPHANED'
                """), {'batch_id': batch_id}).fetchone()
                
                if orphaned and orphaned[0] > 0:
                    issues.append({
                        'type': 'ORPHANED',
                        'severity': 'LOW',
                        'description': 'Items in POS but not in RFID',
                        'count': orphaned[0]
                    })
                    
        except SQLAlchemyError as e:
            self.logger.error(f"Error detecting quality issues: {str(e)}")
            issues.append({'type': 'ERROR', 'message': str(e)})
        
        return issues
    
    def correlate_rfid_pos(self, rfid_tag: str, pos_item_num: str, 
                          confidence: float = 1.0) -> bool:
        """
        Create manual correlation between RFID tag and POS item
        
        Args:
            rfid_tag: RFID tag ID
            pos_item_num: POS item number
            confidence: Confidence score (0.0-1.0)
            
        Returns:
            Success status
        """
        try:
            with self.db.begin() as conn:
                # Check if correlation exists
                existing = conn.execute(text("""
                    SELECT correlation_id 
                    FROM inventory_correlation_master
                    WHERE rfid_tag_id = :rfid_tag OR pos_item_num = :pos_num
                """), {'rfid_tag': rfid_tag, 'pos_num': pos_item_num}).fetchone()
                
                if existing:
                    # Update existing correlation
                    conn.execute(text("""
                        UPDATE inventory_correlation_master
                        SET rfid_tag_id = :rfid_tag,
                            pos_item_num = :pos_num,
                            confidence_score = :confidence,
                            last_verified_date = NOW(),
                            verification_source = 'MANUAL'
                        WHERE correlation_id = :corr_id
                    """), {
                        'rfid_tag': rfid_tag,
                        'pos_num': pos_item_num,
                        'confidence': confidence,
                        'corr_id': existing[0]
                    })
                else:
                    # Create new correlation
                    master_id = f"CORR_{rfid_tag}_{pos_item_num}"
                    conn.execute(text("""
                        INSERT INTO inventory_correlation_master (
                            master_item_id, rfid_tag_id, pos_item_num,
                            tracking_type, confidence_score, 
                            verification_source, created_by
                        ) VALUES (
                            :master_id, :rfid_tag, :pos_num,
                            'RFID', :confidence, 'MANUAL', 'SYSTEM'
                        )
                    """), {
                        'master_id': master_id,
                        'rfid_tag': rfid_tag,
                        'pos_num': pos_item_num,
                        'confidence': confidence
                    })
                
                return True
                
        except SQLAlchemyError as e:
            self.logger.error(f"Error creating correlation: {str(e)}")
            return False
    
    def get_correlation_status(self) -> Dict[str, Any]:
        """Get overall correlation status and statistics"""
        try:
            with self.db.begin() as conn:
                # Overall statistics
                stats = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_correlations,
                        COUNT(DISTINCT rfid_tag_id) as rfid_items,
                        COUNT(DISTINCT pos_item_num) as pos_items,
                        AVG(confidence_score) as avg_confidence,
                        SUM(CASE WHEN tracking_type = 'RFID' THEN 1 ELSE 0 END) as rfid_tracked,
                        SUM(CASE WHEN tracking_type = 'BULK' THEN 1 ELSE 0 END) as bulk_tracked,
                        SUM(CASE WHEN tracking_type = 'HYBRID' THEN 1 ELSE 0 END) as hybrid_tracked
                    FROM inventory_correlation_master
                """)).fetchone()
                
                # Migration progress
                migration = conn.execute(text("""
                    SELECT 
                        COUNT(*) as active_migrations,
                        SUM(items_migrated) as total_migrated,
                        SUM(items_remaining) as total_remaining
                    FROM migration_tracking
                    WHERE migration_status IN ('PLANNED', 'IN_PROGRESS')
                """)).fetchone()
                
                # Quality issues
                quality = conn.execute(text("""
                    SELECT 
                        COUNT(*) as open_issues,
                        COUNT(DISTINCT correlation_id) as affected_items
                    FROM data_quality_metrics
                    WHERE resolution_status = 'OPEN'
                """)).fetchone()
                
                return {
                    'correlations': {
                        'total': stats[0] if stats else 0,
                        'rfid_items': stats[1] if stats else 0,
                        'pos_items': stats[2] if stats else 0,
                        'avg_confidence': float(stats[3]) if stats and stats[3] else 0.0,
                        'by_type': {
                            'rfid': stats[4] if stats else 0,
                            'bulk': stats[5] if stats else 0,
                            'hybrid': stats[6] if stats else 0
                        }
                    },
                    'migration': {
                        'active': migration[0] if migration else 0,
                        'items_migrated': migration[1] if migration else 0,
                        'items_remaining': migration[2] if migration else 0
                    },
                    'quality': {
                        'open_issues': quality[0] if quality else 0,
                        'affected_items': quality[1] if quality else 0
                    }
                }
                
        except SQLAlchemyError as e:
            self.logger.error(f"Error getting correlation status: {str(e)}")
            return {'error': str(e)}
    
    def scan_for_new_files(self) -> List[Dict]:
        """Scan POS directory for new CSV files to process"""
        new_files = []
        
        try:
            # Get list of already processed files
            with self.db.begin() as conn:
                processed = conn.execute(text("""
                    SELECT DISTINCT file_name 
                    FROM pos_data_staging
                    WHERE import_date > DATE_SUB(NOW(), INTERVAL 30 DAY)
                """)).fetchall()
                
                processed_files = {row[0] for row in processed}
            
            # Scan directory
            for file_path in self.pos_directory.glob("*.csv"):
                file_name = file_path.name
                
                # Skip if already processed
                if file_name in processed_files:
                    continue
                
                # Determine file type
                file_type = 'equipment'  # Default
                if 'itemlist' in file_name.lower():
                    file_type = 'itemlist'
                elif 'customer' in file_name.lower():
                    file_type = 'customer'
                elif 'trans' in file_name.lower():
                    file_type = 'transaction'
                
                file_info = {
                    'file_name': file_name,
                    'file_path': str(file_path),
                    'file_type': file_type,
                    'size_mb': file_path.stat().st_size / (1024 * 1024),
                    'modified': datetime.fromtimestamp(file_path.stat().st_mtime),
                    'status': 'pending'
                }
                
                new_files.append(file_info)
            
        except Exception as e:
            self.logger.error(f"Error scanning for new files: {str(e)}")
        
        return new_files
    
    def auto_process_new_files(self) -> List[Dict]:
        """Automatically process all new CSV files"""
        results = []
        new_files = self.scan_for_new_files()
        
        for file_info in new_files:
            self.logger.info(f"Auto-processing file: {file_info['file_name']}")
            
            result = self.process_csv_file(
                file_info['file_path'],
                file_info['file_type']
            )
            
            result['file_info'] = file_info
            results.append(result)
        
        return results