# Bedrock Transformation Service - Corrected Column Names
# Version: 2025-09-23-v2
# Purpose: Transform bedrock raw data with EXACT column names from database

from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import Dict, List, Optional, Any
import re
import json
from sqlalchemy import text
from app import db
from app.services.logger import get_logger

logger = get_logger(__name__)

class BedrockTransformationService:
    """
    Transform bedrock raw data into business objects with EXACT column correlations
    Uses ACTUAL column names from bedrock tables after import correction
    """

    def __init__(self):
        self.store_mapping = self._load_store_mapping()

    def transform_equipment_from_bedrock(self, bedrock_row: Dict) -> Dict:
        """Transform equipment with EXACT bedrock column names"""
        try:
            equipment_key = self._clean_text(bedrock_row.get('pos_equipment_equipment_key', ''))

            return {
                # Core identification
                'item_num': equipment_key,
                'name': self._clean_text(bedrock_row.get('pos_equipment_name', '')),
                'category': self._clean_text(bedrock_row.get('pos_equipment_category', '')),
                'type': self._clean_text(bedrock_row.get('pos_equipment_type', '')),
                'location': self._clean_text(bedrock_row.get('pos_equipment_loc', '')),

                # Inventory data
                'quantity': self._parse_int(bedrock_row.get('pos_equipment_qty')),
                'quantity_on_order': self._parse_int(bedrock_row.get('pos_equipment_qyot')),

                # Financial data
                'selling_price': self._parse_decimal(bedrock_row.get('pos_equipment_sell')),
                'deposit_amount': self._parse_decimal(bedrock_row.get('pos_equipment_dep')),
                'damage_waiver': self._parse_decimal(bedrock_row.get('pos_equipment_dmg')),

                # Service date
                'service_date': self._parse_date(bedrock_row.get('pos_equipment_sdate')),

                # RFID correlation (CORRECT: equipment.NUM → id_item_master.rental_class_num)
                'rfid_correlation': self._find_rfid_correlation(
                    self._clean_text(bedrock_row.get('pos_equipment_num', ''))
                ),

                # Metadata
                'transformation_version': '2.0_corrected',
                'transformed_at': datetime.now()
            }

        except Exception as e:
            logger.error(f"Equipment transformation error: {e}")
            return None

    def transform_customer_from_bedrock(self, bedrock_row: Dict) -> Dict:
        """Transform customer with EXACT bedrock column names"""
        try:
            return {
                # Core identification
                'customer_key': self._clean_text(bedrock_row.get('pos_customers_key', '')),
                'customer_name': self._clean_text(bedrock_row.get('pos_customers_name', '')),

                # Contact information
                'address': self._clean_text(bedrock_row.get('pos_customers_address', '')),
                'address2': self._clean_text(bedrock_row.get('pos_customers_address2', '')),
                'city': self._clean_text(bedrock_row.get('pos_customers_city', '')),
                'zip_code': self._clean_text(bedrock_row.get('pos_customers_zip', '')),
                'phone': self._clean_text(bedrock_row.get('pos_customers_phone', '')),
                'work_phone': self._clean_text(bedrock_row.get('pos_customers_work', '')),
                'mobile': self._clean_text(bedrock_row.get('pos_customers_mobile', '')),
                'email': self._clean_text(bedrock_row.get('pos_customers_email', '')),

                # Personal info
                'drivers_license': self._clean_text(bedrock_row.get('pos_customers_driverslicense', '')),
                'birth_date': self._parse_date(bedrock_row.get('pos_customers_birthdate')),
                'employer': self._clean_text(bedrock_row.get('pos_customers_employer', '')),

                # Metadata
                'transformation_version': '2.0_corrected',
                'transformed_at': datetime.now()
            }

        except Exception as e:
            logger.error(f"Customer transformation error: {e}")
            return None

    def transform_transaction_from_bedrock(self, bedrock_row: Dict) -> Dict:
        """Transform transaction with EXACT bedrock column names"""
        try:
            contract_num = self._clean_text(bedrock_row.get('pos_transactions_cntr', ''))
            customer_num = self._clean_text(bedrock_row.get('pos_transactions_cusn', ''))

            return {
                # Core identification
                'contract_number': contract_num,
                'customer_number': customer_num,
                'date': self._parse_date(bedrock_row.get('pos_transactions_date')),
                'time': self._clean_text(bedrock_row.get('pos_transactions_time', '')),
                'operator_id': self._clean_text(bedrock_row.get('pos_transactions_opid', '')),

                # Financial data
                'payment': self._parse_decimal(bedrock_row.get('pos_transactions_pymt')),
                'deposit': self._parse_decimal(bedrock_row.get('pos_transactions_dpmt')),
                'rent_amount': self._parse_decimal(bedrock_row.get('pos_transactions_rent')),
                'sale_amount': self._parse_decimal(bedrock_row.get('pos_transactions_sale')),
                'tax_amount': self._parse_decimal(bedrock_row.get('pos_transactions_tax')),
                'total_amount': self._parse_decimal(bedrock_row.get('pos_transactions_totl')),

                # Status
                'status': self._clean_text(bedrock_row.get('pos_transactions_stat', '')),

                # Customer correlation (critical)
                'customer_correlation': self._find_customer_correlation(customer_num),

                # MISSING CORRELATIONS from Excel documentation:
                'id_item_master_correlation': self._find_id_item_master_from_contract(contract_num),  # CNTR → id_item_master.last_contract_num
                'id_transactions_correlation': self._find_id_transactions_from_contract(contract_num),  # CNTR → id_transactions.contract_number

                # Metadata
                'transformation_version': '2.0_corrected',
                'transformed_at': datetime.now()
            }

        except Exception as e:
            logger.error(f"Transaction transformation error: {e}")
            return None

    def transform_transitem_from_bedrock(self, bedrock_row: Dict) -> Dict:
        """Transform transaction item with EXACT bedrock column names"""
        try:
            contract_num = self._clean_text(bedrock_row.get('pos_transitems_cntr', ''))
            item_num = self._clean_text(bedrock_row.get('pos_transitems_item', ''))

            return {
                # Core identification
                'contract_number': contract_num,
                'item_number': item_num,
                'quantity': self._parse_int(bedrock_row.get('pos_transitems_qty')),
                'price': self._parse_decimal(bedrock_row.get('pos_transitems_pric')),
                'description': self._clean_text(bedrock_row.get('pos_transitems_desc', '')),

                # CRITICAL CORRELATIONS (from Excel documentation):
                'equipment_correlation': self._find_equipment_correlation(item_num),  # transitems.ITEM → equipment.NUM
                'transaction_correlation': self._find_transaction_correlation(contract_num),  # transactions.CNTR ↔ transitems.CNTR
                'rfid_transactions_correlation': self._find_rfid_transactions_correlation(item_num),  # transitems.ITEM → id_transactions.rental_class_id

                # ADDITIONAL CORRELATIONS from Excel:
                'customer_from_contract_correlation': self._find_customer_from_contract(contract_num),  # transitems.CNTR → customers.LastContract
                'id_item_master_correlation': self._find_id_item_master_from_contract(contract_num),  # transitems.CNTR → id_item_master.last_contract_num

                # Metadata
                'transformation_version': '2.0_corrected',
                'transformed_at': datetime.now()
            }

        except Exception as e:
            logger.error(f"Transitem transformation error: {e}")
            return None

    # Correlation methods with EXACT column names

    def _find_rfid_correlation(self, equipment_num: str) -> Optional[Dict]:
        """CORRECT: equipment.NUM → id_item_master.rental_class_num (from Excel documentation)"""
        if not equipment_num:
            return None

        try:
            session = db.session()
            result = session.execute(text("""
                SELECT tag_id, serial_number, status, bin_location, rental_class_num
                FROM id_item_master
                WHERE rental_class_num = :equipment_num
                LIMIT 1
            """), {'equipment_num': equipment_num})

            rfid_item = result.fetchone()
            if rfid_item:
                return {
                    'tag_id': rfid_item[0],
                    'serial_number': rfid_item[1],
                    'status': rfid_item[2],
                    'bin_location': rfid_item[3],
                    'rental_class_num': rfid_item[4],
                    'correlation_type': 'equipment_NUM_to_rfid_rental_class_num'
                }
            return None

        except Exception as e:
            logger.error(f"RFID correlation lookup failed: {e}")
            return None

    def _find_rfid_transactions_correlation(self, item_num: str) -> Optional[Dict]:
        """CORRECT: transitems.ITEM → id_transactions.rental_class_id (from Excel documentation)"""
        if not item_num:
            return None

        try:
            session = db.session()
            result = session.execute(text("""
                SELECT id, transaction_type, timestamp, rental_class_id
                FROM id_transactions
                WHERE rental_class_id = :item_num
                ORDER BY timestamp DESC
                LIMIT 5
            """), {'item_num': item_num})

            transactions = []
            for row in result.fetchall():
                transactions.append({
                    'transaction_id': row[0],
                    'transaction_type': row[1],
                    'timestamp': row[2],
                    'rental_class_id': row[3]
                })

            if transactions:
                return {
                    'recent_transactions': transactions,
                    'correlation_type': 'transitems_ITEM_to_rfid_transactions_rental_class_id',
                    'transaction_count': len(transactions)
                }
            return None

        except Exception as e:
            logger.error(f"RFID transactions correlation lookup failed: {e}")
            return None

    def _find_equipment_correlation(self, item_num: str) -> Optional[Dict]:
        """CORRECT: transitems.ITEM → equipment.NUM (from Excel documentation)"""
        if not item_num:
            return None

        try:
            session = db.session()
            result = session.execute(text("""
                SELECT pos_equipment_equipment_key, pos_equipment_name, pos_equipment_category,
                       pos_equipment_sell, pos_equipment_num
                FROM raw_pos_equipment
                WHERE pos_equipment_num = :item_num
                LIMIT 1
            """), {'item_num': item_num})

            equipment = result.fetchone()
            if equipment:
                return {
                    'equipment_key': equipment[0],
                    'equipment_name': equipment[1],
                    'equipment_category': equipment[2],
                    'selling_price': equipment[3],
                    'equipment_num': equipment[4],
                    'correlation_type': 'transitems_ITEM_to_equipment_NUM'
                }
            return None

        except Exception as e:
            logger.error(f"Equipment correlation lookup failed: {e}")
            return None

    def _find_customer_correlation(self, customer_num: str) -> Optional[Dict]:
        """CORRECT: transactions.CUSN → customers.CNUM (from Excel documentation)"""
        if not customer_num:
            return None

        try:
            session = db.session()
            result = session.execute(text("""
                SELECT pos_customers_key, pos_customers_name, pos_customers_phone, pos_customers_cnum
                FROM raw_pos_customers
                WHERE pos_customers_cnum = :customer_num OR pos_customers_key = :customer_num
                LIMIT 1
            """), {'customer_num': customer_num})

            customer = result.fetchone()
            if customer:
                return {
                    'customer_key': customer[0],
                    'customer_name': customer[1],
                    'phone': customer[2],
                    'customer_cnum': customer[3],
                    'correlation_type': 'transactions_CUSN_to_customers_CNUM'
                }
            return None

        except Exception as e:
            logger.error(f"Customer correlation lookup failed: {e}")
            return None

    def _find_transaction_correlation(self, contract_num: str) -> Optional[Dict]:
        """Find transaction correlation using EXACT column names"""
        if not contract_num:
            return None

        try:
            session = db.session()
            result = session.execute(text("""
                SELECT pos_transactions_cusn, pos_transactions_totl, pos_transactions_date
                FROM raw_pos_transactions
                WHERE pos_transactions_cntr = :contract_num
                LIMIT 1
            """), {'contract_num': contract_num})

            transaction = result.fetchone()
            if transaction:
                return {
                    'customer_number': transaction[0],
                    'total_amount': transaction[1],
                    'transaction_date': transaction[2],
                    'correlation_type': 'transitems_to_transaction'
                }
            return None

        except Exception as e:
            logger.error(f"Transaction correlation lookup failed: {e}")
            return None

    def _load_store_mapping(self) -> Dict:
        """Load store code mapping"""
        return {
            '001': '3607',  # Wayzata
            '002': '6800',  # Brooklyn Park
            '003': '8101',  # Fridley
            '004': '728',   # Elk River
            '1': '3607', '2': '6800', '3': '8101', '4': '728',
            '3607': '3607', '6800': '6800', '8101': '8101', '728': '728'
        }

    def _clean_text(self, value: Any) -> str:
        """Clean text values"""
        if value is None or value == '':
            return ''
        return str(value).strip()

    def _parse_int(self, value: Any) -> Optional[int]:
        """Parse integer values safely"""
        if value is None or value == '':
            return None
        try:
            return int(float(str(value)))
        except (ValueError, TypeError):
            return None

    def _parse_decimal(self, value: Any) -> Optional[Decimal]:
        """Parse decimal values safely"""
        if value is None or value == '':
            return None
        try:
            clean_value = str(value).replace('$', '').replace(',', '').strip()
            return Decimal(clean_value)
        except (InvalidOperation, TypeError, ValueError):
            return None

    def _parse_date(self, value: Any) -> Optional[datetime]:
        """Parse date values safely"""
        if value is None or value == '':
            return None
        try:
            if isinstance(value, datetime):
                return value
            return datetime.strptime(str(value), '%Y-%m-%d')
        except (ValueError, TypeError):
            return None

    def _find_customer_from_contract(self, contract_num: str) -> Optional[Dict]:
        """MISSING: transitems.CNTR → customers.LastContract (from Excel documentation)"""
        if not contract_num:
            return None

        try:
            session = db.session()
            result = session.execute(text("""
                SELECT pos_customers_key, pos_customers_name, pos_customers_phone, pos_customers_lastcontract
                FROM raw_pos_customers
                WHERE pos_customers_lastcontract = :contract_num
                LIMIT 1
            """), {'contract_num': contract_num})

            customer = result.fetchone()
            if customer:
                return {
                    'customer_key': customer[0],
                    'customer_name': customer[1],
                    'phone': customer[2],
                    'last_contract': customer[3],
                    'correlation_type': 'transitems_CNTR_to_customers_LastContract'
                }
            return None

        except Exception as e:
            logger.error(f"Customer from contract correlation lookup failed: {e}")
            return None

    def _find_id_item_master_from_contract(self, contract_num: str) -> Optional[Dict]:
        """MISSING: CNTR → id_item_master.last_contract_num (from Excel documentation)"""
        if not contract_num:
            return None

        try:
            session = db.session()
            result = session.execute(text("""
                SELECT tag_id, serial_number, item_num, rental_class_num, last_contract_num
                FROM id_item_master
                WHERE last_contract_num = :contract_num
                LIMIT 5
            """), {'contract_num': contract_num})

            items = []
            for row in result.fetchall():
                items.append({
                    'tag_id': row[0],
                    'serial_number': row[1],
                    'item_num': row[2],
                    'rental_class_num': row[3],
                    'last_contract_num': row[4]
                })

            if items:
                return {
                    'related_items': items,
                    'correlation_type': 'contract_to_id_item_master_last_contract_num',
                    'item_count': len(items)
                }
            return None

        except Exception as e:
            logger.error(f"ID item master from contract correlation lookup failed: {e}")
            return None

    def _find_id_transactions_from_contract(self, contract_num: str) -> Optional[Dict]:
        """MISSING: CNTR → id_transactions.contract_number (from Excel documentation)"""
        if not contract_num:
            return None

        try:
            session = db.session()
            result = session.execute(text("""
                SELECT id, timestamp, notes, contract_number
                FROM id_transactions
                WHERE contract_number = :contract_num
                ORDER BY timestamp DESC
                LIMIT 10
            """), {'contract_num': contract_num})

            transactions = []
            for row in result.fetchall():
                transactions.append({
                    'transaction_id': row[0],
                    'timestamp': row[1],
                    'notes': row[2],
                    'contract_number': row[3]
                })

            if transactions:
                return {
                    'related_transactions': transactions,
                    'correlation_type': 'contract_to_id_transactions_contract_number',
                    'transaction_count': len(transactions)
                }
            return None

        except Exception as e:
            logger.error(f"ID transactions from contract correlation lookup failed: {e}")
            return None

# Service instance
bedrock_transformation_service = BedrockTransformationService()