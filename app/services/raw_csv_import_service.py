# Raw CSV Import Service - Simple 1:1 Import
# Version: 2025-09-18-v1
# Purpose: Import CSV files directly with zero transformation

import pandas as pd
import os
from datetime import datetime
from typing import Dict, List
from sqlalchemy import text
from app import db
from app.services.logger import get_logger

logger = get_logger(__name__)

class RawCSVImportService:
    """
    Simple CSV importer that preserves ALL data in raw format
    No transformations, no data loss, maximum flexibility
    """

    def __init__(self):
        self.csv_base_path = "/home/tim/RFID3/shared/POR"

    def import_equipment_raw(self, file_path: str, batch_size: int = 1000) -> Dict:
        """Import equipPOS CSV directly to equipment_raw table"""
        try:
            # Generate batch ID
            batch_id = f"equipment_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Read CSV
            df = pd.read_csv(file_path)
            logger.info(f"Read {len(df)} rows with {len(df.columns)} columns from {file_path}")

            # Import in batches
            total_imported = 0
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]

                # Insert batch into raw table
                batch_records = []
                for _, row in batch.iterrows():
                    record = {
                        'import_batch_id': batch_id,
                        'source_file': os.path.basename(file_path),
                        **{col: str(row[col]) if pd.notna(row[col]) else '' for col in df.columns}
                    }
                    batch_records.append(record)

                # Bulk insert
                self._bulk_insert_equipment_raw(batch_records)
                total_imported += len(batch_records)

                logger.info(f"Imported batch {i//batch_size + 1}: {len(batch_records)} records")

            return {
                'success': True,
                'batch_id': batch_id,
                'total_records': total_imported,
                'columns_preserved': len(df.columns),
                'file_path': file_path
            }

        except Exception as e:
            logger.error(f"Raw equipment import failed: {e}")
            return {'success': False, 'error': str(e)}

    def _bulk_insert_equipment_raw(self, records: List[Dict]):
        """Bulk insert equipment records into raw table"""
        if not records:
            return

        # Generate INSERT statement for raw table
        session = db.session()
        try:
            # Build column list (all CSV columns)
            columns = list(records[0].keys())
            column_str = ', '.join([f'`{col}`' for col in columns])
            value_placeholders = ', '.join([':' + col for col in columns])

            insert_sql = f"""
                INSERT INTO equipment_raw ({column_str})
                VALUES ({value_placeholders})
            """

            session.execute(text(insert_sql), records)
            session.commit()

        except Exception as e:
            session.rollback()
            logger.error(f"Bulk insert failed: {e}")
            raise
        finally:
            session.close()

    def get_import_status(self, batch_id: str) -> Dict:
        """Get import batch status"""
        try:
            session = db.session()

            # Count records by status
            status_query = text("""
                SELECT
                    import_status,
                    COUNT(*) as count
                FROM equipment_raw
                WHERE import_batch_id = :batch_id
                GROUP BY import_status
            """)

            results = session.execute(status_query, {'batch_id': batch_id}).fetchall()

            status_counts = {row.import_status: row.count for row in results}

            return {
                'batch_id': batch_id,
                'status_counts': status_counts,
                'total_records': sum(status_counts.values())
            }

        except Exception as e:
            logger.error(f"Error getting import status: {e}")
            return {'error': str(e)}

# This service preserves ALL CSV data with zero loss!