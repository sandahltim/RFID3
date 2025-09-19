# Raw Data Transformation Service - The Heart of the Architecture
# Version: 2025-09-18-v1
# Purpose: Transform raw CSV data into business objects with clean logic

from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import Dict, List, Optional, Any
import re
import json
from sqlalchemy import text
from app import db
from app.services.logger import get_logger

logger = get_logger(__name__)

class RawDataTransformationService:
    """
    Transforms raw CSV data into clean business objects
    Separates data import from business logic - architectural masterpiece
    """

    def __init__(self):
        self.transformation_rules = self._load_transformation_rules()

    def transform_equipment_row(self, raw_row: Dict) -> Dict:
        """Transform raw equipment CSV data into business object"""
        try:
            return {
                # Core identification
                'item_num': self._clean_text(raw_row.get('KEY', '')),
                'name': self._clean_text(raw_row.get('Name', '')),
                'category': self._clean_text(raw_row.get('Category', '')),
                'manufacturer': self._clean_text(raw_row.get('MANF', '')),
                'model_no': self._clean_text(raw_row.get('MODN', '')),

                # Inventory data
                'quantity': self._parse_int(raw_row.get('QTY')),
                'quantity_on_order': self._parse_int(raw_row.get('QYOT')),
                'location_code': self._clean_text(raw_row.get('LOC', '')),

                # Financial data
                'selling_price': self._parse_decimal(raw_row.get('SELL')),
                'deposit_amount': self._parse_decimal(raw_row.get('DEP')),
                'damage_waiver': self._parse_decimal(raw_row.get('DMG')),

                # Store assignments
                'home_store': self._map_store_code(raw_row.get('HomeStore')),
                'current_store': self._map_store_code(raw_row.get('CurrentStore')),

                # Rental structure (business logic)
                'rental_periods': self._build_rental_structure(raw_row, 'PER'),
                'rental_rates': self._build_rental_structure(raw_row, 'RATE'),

                # Physical specifications
                'height': self._parse_decimal(raw_row.get('Height')),
                'width': self._parse_decimal(raw_row.get('Width')),
                'length': self._parse_decimal(raw_row.get('Length')),
                'weight': self._parse_decimal(raw_row.get('Weight')),

                # Business flags
                'inactive': self._parse_boolean(raw_row.get('Inactive')),
                'require_cleaning': self._parse_boolean(raw_row.get('RequireCleaning')),
                'hide_on_website': self._parse_boolean(raw_row.get('HideOnWebsite')),

                # Vendor information
                'vendors': self._build_vendor_list(raw_row),

                # Dates
                'service_date': self._parse_date(raw_row.get('SDATE')),
                'created_datetime': self._parse_datetime(raw_row.get('CreatedDateTime')),
                'updated_datetime': self._parse_datetime(raw_row.get('UpdatedDateTime')),

                # Metadata
                'transformation_version': '1.0',
                'transformed_at': datetime.now()
            }

        except Exception as e:
            logger.error(f"Equipment transformation error: {e}")
            return None

    def _build_rental_structure(self, raw_row: Dict, prefix: str) -> Dict:
        """Build rental periods or rates structure from PER1-PER10 or RATE1-RATE10"""
        structure = {}
        for i in range(1, 11):
            key = f'{prefix}{i}'
            value = self._parse_decimal(raw_row.get(key))
            if value is not None:
                structure[f'{prefix.lower()}_{i}'] = value
        return structure

    def _build_vendor_list(self, raw_row: Dict) -> List[Dict]:
        """Build vendor information from VendorNumber1-3"""
        vendors = []
        for i in range(1, 4):
            vendor_num = raw_row.get(f'VendorNumber{i}')
            order_num = raw_row.get(f'OrderNumber{i}')
            if vendor_num:
                vendors.append({
                    'vendor_number': self._clean_text(vendor_num),
                    'order_number': self._clean_text(order_num),
                    'priority': i
                })
        return vendors

    def _map_store_code(self, store_value: str) -> str:
        """Map POS store codes to business store codes"""
        store_mapping = {
            '001': '3607',  # Wayzata
            '002': '6800',  # Brooklyn Park
            '003': '8101',  # Fridley
            '004': '728'    # Elk River
        }
        return store_mapping.get(str(store_value).strip(), store_value)

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
            # Remove currency symbols, commas
            clean_value = str(value).replace('$', '').replace(',', '').strip()
            return Decimal(clean_value)
        except (InvalidOperation, TypeError, ValueError):
            return None

    def _parse_boolean(self, value: Any) -> Optional[bool]:
        """Parse boolean values from various formats"""
        if value is None or value == '':
            return None

        str_value = str(value).lower().strip()
        if str_value in ['true', '1', 'yes', 'y']:
            return True
        elif str_value in ['false', '0', 'no', 'n']:
            return False
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

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parse datetime values safely"""
        if value is None or value == '':
            return None
        try:
            if isinstance(value, datetime):
                return value
            return datetime.strptime(str(value), '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            return None

    def _load_transformation_rules(self) -> Dict:
        """Load transformation rules for different CSV types"""
        return {
            'equipment': {
                'required_fields': ['KEY', 'Name', 'Category'],
                'financial_fields': ['SELL', 'DEP', 'DMG', 'RATE1', 'RATE2', 'RATE3'],
                'boolean_fields': ['Inactive', 'RequireCleaning', 'HideOnWebsite'],
                'date_fields': ['SDATE', 'CreatedDateTime', 'UpdatedDateTime']
            },
            'customers': {
                'required_fields': ['KEY', 'NAME', 'CNUM'],
                'financial_fields': ['CreditLimit', 'LastPayAmount', 'HighBalance'],
                'boolean_fields': ['ForceInfo', 'DeleteDmgWvr', 'NoEmail'],
                'date_fields': ['OpenDate', 'LastActive', 'DLExpire']
            }
        }