# CSV Transformation Service - Professional Architecture
# Version: 2025-09-18-v1
# Purpose: Transform raw CSV data into business objects

from decimal import Decimal
from datetime import datetime
from typing import Dict, Optional
from sqlalchemy import text
from app import db
from app.services.logger import get_logger

logger = get_logger(__name__)

class CSVTransformationService:
    """
    Professional CSV transformation service
    Converts raw CSV data into clean business objects
    """

    def __init__(self):
        self.store_mapping = {
            '001': '3607',  # Wayzata
            '002': '6800',  # Brooklyn Park
            '003': '8101',  # Fridley
            '004': '728'    # Elk River
        }

    def transform_equipment_batch(self, batch_id: str) -> Dict:
        """Transform raw equipment data to business format"""
        try:
            session = db.session()

            # Transform raw equipment data
            transform_sql = text("""
                INSERT INTO pos_equipment (
                    item_num, name, category, manufacturer,
                    home_store, current_store,
                    created_at, updated_at
                )
                SELECT
                    equipment_key as item_num,
                    name,
                    category,
                    manufacturer,
                    CASE
                        WHEN location_code = '001' THEN '3607'
                        WHEN location_code = '002' THEN '6800'
                        WHEN location_code = '003' THEN '8101'
                        WHEN location_code = '004' THEN '728'
                        ELSE location_code
                    END as home_store,
                    CASE
                        WHEN location_code = '001' THEN '3607'
                        WHEN location_code = '002' THEN '6800'
                        WHEN location_code = '003' THEN '8101'
                        WHEN location_code = '004' THEN '728'
                        ELSE location_code
                    END as current_store,
                    NOW() as created_at,
                    NOW() as updated_at
                FROM equipment_csv_raw
                WHERE import_batch_id = :batch_id
                AND import_status = 'pending'
                AND equipment_key IS NOT NULL
                AND equipment_key != ''
            """)

            result = session.execute(transform_sql, {'batch_id': batch_id})

            # Mark raw records as processed
            update_sql = text("""
                UPDATE equipment_csv_raw
                SET import_status = 'processed', processed_at = NOW()
                WHERE import_batch_id = :batch_id
                AND import_status = 'pending'
            """)

            session.execute(update_sql, {'batch_id': batch_id})
            session.commit()

            logger.info(f"Equipment transformation complete: {result.rowcount} records")

            return {
                'success': True,
                'transformed_records': result.rowcount,
                'batch_id': batch_id
            }

        except Exception as e:
            session.rollback()
            logger.error(f"Equipment transformation failed: {e}")
            return {'success': False, 'error': str(e)}
        finally:
            session.close()

    def parse_decimal(self, value: str) -> Optional[Decimal]:
        """Parse decimal values safely"""
        if not value or value.strip() == '':
            return None
        try:
            clean_value = str(value).replace('$', '').replace(',', '').strip()
            return Decimal(clean_value)
        except:
            return None

    def parse_boolean(self, value: str) -> Optional[bool]:
        """Parse boolean values from CSV"""
        if not value:
            return None
        val = str(value).lower().strip()
        return val in ['true', '1', 'yes', 'y']