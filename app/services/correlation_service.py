# Correlation Service - Based on YOUR specifications
# Version: 2025-09-18-v1

from typing import Dict, Optional
from sqlalchemy import text
from app import db
from app.services.logger import get_logger

logger = get_logger(__name__)

class CorrelationService:
    """
    Correlation service based on YOUR specifications:
    transitems.ITEM ↔ equipment.NUM ↔ rental_class_num ↔ id_transactions.rental_class_id
    """

    def __init__(self):
        # Store mapping patterns per YOUR specifications
        self.store_patterns = {
            '001': {'id': '3607', 'name': 'Wayzata'},
            '002': {'id': '6800', 'name': 'Brooklyn Park'},
            '003': {'id': '8101', 'name': 'Fridley'},
            '004': {'id': '728', 'name': 'Elk River'},
            '1': {'id': '3607', 'name': 'Wayzata'},
            '2': {'id': '6800', 'name': 'Brooklyn Park'},
            '3': {'id': '8101', 'name': 'Fridley'},
            '4': {'id': '728', 'name': 'Elk River'},
            '3607': {'id': '3607', 'name': 'Wayzata'},
            '6800': {'id': '6800', 'name': 'Brooklyn Park'},
            '8101': {'id': '8101', 'name': 'Fridley'},
            '728': {'id': '728', 'name': 'Elk River'}
        }

    def correlate_transitems_to_equipment(self, transitems_item: str) -> Optional[Dict]:
        """
        Correlate transitems.ITEM to equipment.NUM per YOUR specifications
        """
        try:
            session = db.session()

            # YOUR Excel: transitems.ITEM correlates to equipment.NUM
            correlation_query = text("""
                SELECT
                    e.num as equipment_num,
                    e.name as equipment_name,
                    e.category,
                    e.manufacturer as manf,
                    e.home_store,
                    e.current_store
                FROM pos_equipment e
                WHERE e.num = :transitems_item
                LIMIT 1
            """)

            result = session.execute(correlation_query, {'transitems_item': transitems_item}).fetchone()

            if result:
                return {
                    'equipment_num': result.equipment_num,
                    'equipment_name': result.equipment_name,
                    'category': result.category,
                    'manufacturer': result.manf,
                    'home_store': result.home_store,
                    'current_store': result.current_store,
                    'correlation_source': 'transitems_item_to_equipment_num'
                }
            else:
                return None

        except Exception as e:
            logger.error(f"Transitems-Equipment correlation error: {e}")
            return None

    def map_store_reference(self, store_value: str) -> Dict:
        """
        Handle store correlation patterns per YOUR specifications
        Looks for patterns: 001/1/3607/Wayzata in any format
        """
        if not store_value:
            return {'id': None, 'name': None, 'pattern': 'empty'}

        store_clean = str(store_value).strip()

        # Direct pattern match
        if store_clean in self.store_patterns:
            result = self.store_patterns[store_clean].copy()
            result['pattern'] = 'direct_match'
            return result

        # Check if store appears in column headers or data
        for pattern, info in self.store_patterns.items():
            if pattern in store_clean or info['name'].lower() in store_clean.lower():
                result = info.copy()
                result['pattern'] = 'partial_match'
                return result

        return {'id': store_clean, 'name': 'unknown', 'pattern': 'no_match'}

    def determine_transaction_status_from_dates(self, transaction_data: Dict) -> str:
        """
        Determine transaction status using dates and logic per YOUR specifications
        Ignore POS STAT field (YOUR Excel: "unknown")
        """
        try:
            from datetime import datetime

            date_fields = {
                'transaction_date': transaction_data.get('DATE'),
                'completed_date': transaction_data.get('Completed'),
                'billed_date': transaction_data.get('Billed'),
                'delivery_date': transaction_data.get('DeliveryDate'),
                'pickup_date': transaction_data.get('PickupDate')
            }

            # Parse dates
            parsed_dates = {}
            for field, value in date_fields.items():
                if value:
                    try:
                        parsed_dates[field] = datetime.strptime(str(value), '%Y-%m-%d')
                    except:
                        parsed_dates[field] = None

            # Business logic for status determination
            if parsed_dates.get('completed_date'):
                return 'completed'
            elif parsed_dates.get('pickup_date'):
                return 'picked_up'
            elif parsed_dates.get('delivery_date'):
                return 'delivered'
            elif parsed_dates.get('billed_date'):
                return 'billed'
            elif parsed_dates.get('transaction_date'):
                return 'active'
            else:
                return 'unknown'

        except Exception as e:
            logger.error(f"Status determination error: {e}")
            return 'error'