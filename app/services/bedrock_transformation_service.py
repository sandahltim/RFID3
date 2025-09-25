# Bedrock Transformation Service - Corrected Column Names
# Version: 2025-09-25-v3-common-names-added
# Purpose: Transform bedrock raw data with EXACT column names from database
#
# CHANGELOG v3:
# - Added get_common_names_for_category() method for POS vs RFID comparison
# - Fixed parameter naming: store_filter instead of store for consistency
# - Proper store code mapping using self.store_mapping
# - Eliminated problematic column references (im.current_status, im.contract_status)

from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import Dict, List, Optional, Any
import re
import json
from sqlalchemy import text
from app import db
from app.services.logger import get_logger
from app.config.stores import STORES
from app.config.pos_category_mappings import get_category_description

logger = get_logger(__name__)

class BedrockTransformationService:
    """
    Transform bedrock raw data into business objects with EXACT column correlations
    Uses ACTUAL column names from bedrock tables after import correction
    """

    def __init__(self):
        self.store_mapping = self._load_store_mapping()

    def transform_equipment_from_bedrock(self, bedrock_row: Dict) -> Dict:
        """Transform equipment with EXACT bedrock column names + two-tier category system"""
        try:
            equipment_key = self._clean_text(bedrock_row.get('pos_equipment_equipment_key', ''))
            equipment_num = self._clean_text(bedrock_row.get('pos_equipment_num', ''))

            # Two-tier category system: User mappings override PDF defaults
            # Use joined user mapping data if available, otherwise fall back to PDF defaults
            user_category_from_join = bedrock_row.get('user_category')
            user_subcategory_from_join = bedrock_row.get('user_subcategory')

            if user_category_from_join and user_subcategory_from_join:
                # Use data from the join (more efficient)
                final_category = user_category_from_join
                final_subcategory = user_subcategory_from_join
            else:
                # Check if equipment should be filtered out
                from app.config.pos_category_mappings import is_filtered_category
                csv_category = bedrock_row.get('pos_equipment_category')

                if is_filtered_category(csv_category):
                    # Skip this equipment - it should be filtered out
                    return None

                # Fall back to PDF defaults for unmapped equipment
                default_category_info = self._get_default_category_from_csv_number(csv_category)
                final_category = default_category_info['category']
                final_subcategory = default_category_info['subcategory']

            # Get store name from current store
            store_name = self._get_store_name_from_location(bedrock_row.get('pos_equipment_currentstore', ''))

            return {
                # Core identification
                'item_num': equipment_key,
                'equipment_num': equipment_num,
                'name': self._clean_text(bedrock_row.get('pos_equipment_name', '')),
                'category': final_category,
                'subcategory': final_subcategory,
                'csv_category_number': self._clean_text(bedrock_row.get('pos_equipment_category', '')),
                'type': self._clean_text(bedrock_row.get('pos_equipment_type', '')),
                'location': self._clean_text(bedrock_row.get('pos_equipment_loc', '')),
                'current_store': self._clean_text(bedrock_row.get('pos_equipment_currentstore', '')),
                'store_name': store_name,

                # User category mappings (for reference)
                'user_category': user_category_from_join,
                'user_subcategory': user_subcategory_from_join,
                'user_short_name': None,  # TODO: Add short_common_name to user_rental_class_mappings join if needed

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

    # API Support Methods

    def get_equipment_catalog(self, limit: int = 100, offset: int = 0,
                             category: str = None, store: str = None, search: str = None,
                             user_category: str = None, type_filter: str = None,
                             status: str = None, bin_filter: str = None) -> Dict[str, Any]:
        """Get equipment catalog with pagination and filters including user categories"""
        try:
            session = db.session()

            # Show ALL POS inventory - don't pre-filter by categories
            # User mappings will provide categorization where available, but don't exclude items without mappings
            category_filter = "1=1"  # Show all equipment

            # Always join with user category mappings to get proper category/subcategory info
            query = f"""
                SELECT re.*, ucm.category as user_category, ucm.subcategory as user_subcategory
                FROM raw_pos_equipment re
                LEFT JOIN user_rental_class_mappings ucm ON re.pos_equipment_num = ucm.rental_class_id
                WHERE {category_filter}
            """

            params = {}

            # Add filters
            if category:
                query += " AND re.pos_equipment_category LIKE :category"
                params['category'] = f'%{category}%'

            if user_category:
                query += " AND ucm.category LIKE :user_category"
                params['user_category'] = f'%{user_category}%'

            if store:
                # Support both store code and store name filtering
                store_ids = self._get_store_ids_from_filter(store)
                if store_ids:
                    placeholders = ','.join([f':store_{i}' for i in range(len(store_ids))])
                    query += f" AND (re.pos_equipment_currentstore IN ({placeholders})"
                    for i, store_id in enumerate(store_ids):
                        params[f'store_{i}'] = store_id
                    query += " OR re.pos_equipment_currentstore LIKE :store_like)"
                    params['store_like'] = f'%{store}%'
                else:
                    query += " AND re.pos_equipment_currentstore LIKE :store_like"
                    params['store_like'] = f'%{store}%'

            if search:
                query += " AND (re.pos_equipment_name LIKE :search OR re.pos_equipment_category LIKE :search OR re.pos_equipment_equipment_key LIKE :search)"
                params['search'] = f'%{search}%'

            # Type filter (RFID vs all items)
            if type_filter and type_filter.upper() == 'RFID':
                # Need to join with id_item_master if not already joined
                if 'LEFT JOIN id_item_master im' not in query:
                    # Add id_item_master join - we already have user_rental_class_mappings join
                    query = query.replace(
                        "LEFT JOIN user_rental_class_mappings ucm",
                        "LEFT JOIN id_item_master im ON re.pos_equipment_num = im.rental_class_num\n                LEFT JOIN user_rental_class_mappings ucm"
                    )

                # Filter to only items that have RFID tags
                query += " AND (im.tag_id IS NOT NULL AND im.tag_id != '' AND im.tag_id != '0')"

            # Status filter (only applies to RFID-tagged items)
            if status and status != 'all':
                # Ensure we have the RFID join if status filter is applied
                if 'LEFT JOIN id_item_master im' not in query:
                    # Add id_item_master join - we already have user_rental_class_mappings join
                    query = query.replace(
                        "LEFT JOIN user_rental_class_mappings ucm",
                        "LEFT JOIN id_item_master im ON re.pos_equipment_num = im.rental_class_num\n                LEFT JOIN user_rental_class_mappings ucm"
                    )

                # Filter by RFID item status (only for items with RFID tags)
                query += " AND (im.tag_id IS NOT NULL AND im.tag_id != '' AND im.tag_id != '0' AND im.current_status LIKE :status)"
                params['status'] = f'%{status}%'

            # Bin filter (internal store location)
            if bin_filter and bin_filter != 'all':
                field_prefix = "re." if ("FROM raw_pos_equipment re" in query or type_filter) else ""
                query += f" AND {field_prefix}pos_equipment_currentlocation LIKE :bin"
                params['bin'] = f'%{bin_filter}%'

            # Add pagination
            query += " ORDER BY pos_equipment_name LIMIT :limit OFFSET :offset"
            params['limit'] = limit
            params['offset'] = offset

            # Execute query
            result = session.execute(text(query), params)
            rows = result.fetchall()

            # Transform results
            items = []
            for row in rows:
                row_dict = dict(row._asdict())
                equipment = self.transform_equipment_from_bedrock(row_dict)
                if equipment:  # Skip filtered equipment
                    items.append(equipment)

            # Get total count for pagination
            count_query = query.replace(f" ORDER BY pos_equipment_name LIMIT :limit OFFSET :offset", "")
            count_params = {k: v for k, v in params.items() if k not in ['limit', 'offset']}
            count_result = session.execute(text(f"SELECT COUNT(*) FROM ({count_query}) AS subq"), count_params)
            total = count_result.scalar()

            return {
                'items': items,
                'total': total,
                'has_more': (offset + len(items)) < total,
                'filters_applied': {
                    'category': category,
                    'user_category': user_category,
                    'store': store,
                    'search': search,
                    'type_filter': type_filter,
                    'status': status,
                    'bin_filter': bin_filter
                }
            }

        except Exception as e:
            logger.error(f"Failed to get equipment catalog: {e}")
            return {'items': [], 'total': 0, 'has_more': False}

    def _get_store_ids_from_filter(self, store_filter: str) -> List[str]:
        """Convert display store code to POS codes for filtering using proper store mapping"""
        try:
            if not store_filter or store_filter == 'all':
                return []

            # Use the stores.py configuration for proper mapping
            from app.config.stores import STORES

            # Check if the filter matches a display store code
            if store_filter in STORES:
                pos_code = STORES[store_filter].pos_code
                # Return both formatted (002) and unformatted (2) versions
                pos_code_unformatted = str(int(pos_code))
                return [pos_code, pos_code_unformatted]

            # Also check reverse mapping (pos_code to display code)
            for display_code, store_info in STORES.items():
                if store_info.pos_code == store_filter or str(int(store_info.pos_code)) == store_filter:
                    return [store_info.pos_code, str(int(store_info.pos_code))]

            # Return as-is if no mapping found
            return [store_filter]

        except Exception as e:
            logger.error(f"Failed to get store IDs from filter: {e}")
            return [store_filter]

    def get_contract_details(self, contract_no: str) -> Optional[Dict]:
        """Get contract details with items and correlations"""
        try:
            session = db.session()

            # Get transaction details
            trans_result = session.execute(text("""
                SELECT * FROM raw_pos_transactions
                WHERE pos_transactions_cntr = :contract_no
                LIMIT 1
            """), {'contract_no': contract_no})

            trans_row = trans_result.fetchone()
            if not trans_row:
                return None

            trans_dict = dict(trans_row._asdict())
            transaction = self.transform_transaction_from_bedrock(trans_dict)

            # Get transaction items
            items_result = session.execute(text("""
                SELECT * FROM raw_pos_transitems
                WHERE pos_transitems_cntr = :contract_no
            """), {'contract_no': contract_no})

            items = []
            for item_row in items_result.fetchall():
                item_dict = dict(item_row._asdict())
                transitem = self.transform_transitem_from_bedrock(item_dict)

                # Add correlation info
                correlation = self._find_equipment_correlation(transitem.get('item_num', ''))
                if correlation:
                    transitem['correlation'] = correlation

                items.append(transitem)

            transaction['items'] = items
            transaction['item_count'] = len(items)

            return transaction

        except Exception as e:
            logger.error(f"Failed to get contract details: {e}")
            return None

    def get_customer_profile(self, customer_no: str) -> Optional[Dict]:
        """Get customer profile with contract history"""
        try:
            session = db.session()

            # Get customer details
            cust_result = session.execute(text("""
                SELECT * FROM raw_pos_customers
                WHERE pos_customers_cnum = :customer_no
                LIMIT 1
            """), {'customer_no': customer_no})

            cust_row = cust_result.fetchone()
            if not cust_row:
                return None

            cust_dict = dict(cust_row._asdict())
            customer = self.transform_customer_from_bedrock(cust_dict)

            # Get recent contracts
            contracts_result = session.execute(text("""
                SELECT * FROM raw_pos_transactions
                WHERE pos_transactions_cusn = :customer_no
                ORDER BY pos_transactions_out DESC
                LIMIT 10
            """), {'customer_no': customer_no})

            contracts = []
            for contract_row in contracts_result.fetchall():
                contract_dict = dict(contract_row._asdict())
                contract = self.transform_transaction_from_bedrock(contract_dict)
                contracts.append(contract)

            customer['recent_contracts'] = contracts
            customer['contract_count'] = len(contracts)

            return customer

        except Exception as e:
            logger.error(f"Failed to get customer profile: {e}")
            return None

    def get_rfid_correlations(self, limit: int = 100, offset: int = 0,
                             correlation_type: str = None) -> Dict[str, Any]:
        """Get RFID-POS correlations"""
        try:
            session = db.session()

            # Get RFID items with POS correlations
            query = """
                SELECT im.*, re.pos_equipment_name, re.pos_equipment_category
                FROM id_item_master im
                LEFT JOIN raw_pos_equipment re ON im.rental_class_num = re.pos_equipment_num
                WHERE im.rental_class_num IS NOT NULL
                ORDER BY im.common_name
                LIMIT :limit OFFSET :offset
            """

            result = session.execute(text(query), {'limit': limit, 'offset': offset})
            correlations = []

            for row in result.fetchall():
                row_dict = dict(row._asdict())
                correlation = {
                    'rfid_tag_id': row_dict.get('tag_id'),
                    'rfid_common_name': row_dict.get('common_name'),
                    'rfid_rental_class': row_dict.get('rental_class_num'),
                    'pos_equipment_name': row_dict.get('pos_equipment_name'),
                    'pos_equipment_category': row_dict.get('pos_equipment_category'),
                    'correlation_type': 'automatic' if row_dict.get('pos_equipment_name') else 'missing',
                    'confidence_score': 1.0 if row_dict.get('pos_equipment_name') else 0.0
                }
                correlations.append(correlation)

            # Get total count
            count_result = session.execute(text("""
                SELECT COUNT(*) FROM id_item_master
                WHERE rental_class_num IS NOT NULL
            """))
            total = count_result.scalar()

            return {
                'correlations': correlations,
                'total': total,
                'has_more': (offset + len(correlations)) < total
            }

        except Exception as e:
            logger.error(f"Failed to get RFID correlations: {e}")
            return {'correlations': [], 'total': 0, 'has_more': False}

    def search_equipment(self, search_query: str, limit: int = 50) -> Dict[str, Any]:
        """Search equipment across all fields"""
        try:
            session = db.session()

            # Build search query
            query = """
                SELECT * FROM raw_pos_equipment
                WHERE pos_equipment_name LIKE :search
                   OR pos_equipment_category LIKE :search
                   OR pos_equipment_equipment_key LIKE :search
                   OR pos_equipment_type LIKE :search
                ORDER BY pos_equipment_name
                LIMIT :limit
            """

            search_param = f'%{search_query}%'
            result = session.execute(text(query), {'search': search_param, 'limit': limit})

            items = []
            for row in result.fetchall():
                row_dict = dict(row._asdict())
                equipment = self.transform_equipment_from_bedrock(row_dict)
                if equipment:  # Skip filtered equipment
                    items.append(equipment)

            return {
                'items': items,
                'total': len(items),
                'query': search_query
            }

        except Exception as e:
            logger.error(f"Failed to search equipment: {e}")
            return {'items': [], 'total': 0, 'query': search_query}

    def get_recent_transactions(self, limit: int = 100, store_filter: str = None,
                               days_back: int = 30) -> Dict[str, Any]:
        """Get recent transactions with summary"""
        try:
            session = db.session()

            # Build query with date filter
            query = """
                SELECT * FROM raw_pos_transactions
                WHERE pos_transactions_out >= DATE_SUB(NOW(), INTERVAL :days DAY)
            """
            params = {'days': days_back, 'limit': limit}

            if store_filter:
                query += " AND pos_transactions_loc LIKE :store"
                params['store'] = f'%{store_filter}%'

            query += " ORDER BY pos_transactions_out DESC LIMIT :limit"

            result = session.execute(text(query), params)

            transactions = []
            total_value = Decimal('0.0')

            for row in result.fetchall():
                row_dict = dict(row._asdict())
                transaction = self.transform_transaction_from_bedrock(row_dict)
                transactions.append(transaction)

                # Add to total value
                if transaction.get('subtotal'):
                    total_value += Decimal(str(transaction['subtotal']))

            return {
                'transactions': transactions,
                'summary': {
                    'count': len(transactions),
                    'total_value': float(total_value),
                    'period_days': days_back
                }
            }

        except Exception as e:
            logger.error(f"Failed to get recent transactions: {e}")
            return {'transactions': [], 'summary': {}}

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get dashboard summary data"""
        try:
            session = db.session()

            # Get basic counts
            equipment_count = session.execute(text("SELECT COUNT(*) FROM raw_pos_equipment")).scalar()
            customer_count = session.execute(text("SELECT COUNT(*) FROM raw_pos_customers")).scalar()
            transaction_count = session.execute(text("SELECT COUNT(*) FROM raw_pos_transactions")).scalar()

            # Get RFID correlation stats
            rfid_total = session.execute(text("SELECT COUNT(*) FROM id_item_master")).scalar()
            rfid_correlated = session.execute(text("""
                SELECT COUNT(*) FROM id_item_master im
                JOIN raw_pos_equipment re ON im.rental_class_num = re.pos_equipment_num
            """)).scalar()

            return {
                'equipment_catalog': {
                    'total_items': equipment_count,
                    'categories': self._get_category_summary()
                },
                'customers': {
                    'total_customers': customer_count
                },
                'transactions': {
                    'total_contracts': transaction_count,
                    'recent_summary': self._get_recent_summary()
                },
                'correlations': {
                    'rfid_items': rfid_total,
                    'correlated_items': rfid_correlated,
                    'correlation_rate': round((rfid_correlated / rfid_total * 100), 2) if rfid_total > 0 else 0
                }
            }

        except Exception as e:
            logger.error(f"Failed to get dashboard summary: {e}")
            return {}

    def get_equipment_details(self, equipment_key: str) -> Optional[Dict]:
        """Get detailed equipment information"""
        try:
            session = db.session()

            result = session.execute(text("""
                SELECT * FROM raw_pos_equipment
                WHERE pos_equipment_equipment_key = :key
                LIMIT 1
            """), {'key': equipment_key})

            row = result.fetchone()
            if not row:
                return None

            row_dict = dict(row._asdict())
            equipment = self.transform_equipment_from_bedrock(row_dict)

            # Add correlation info
            correlation = self._find_equipment_correlation(equipment_key)
            if correlation:
                equipment['rfid_correlation'] = correlation

            return equipment

        except Exception as e:
            logger.error(f"Failed to get equipment details: {e}")
            return None

    def _get_category_summary(self) -> List[Dict]:
        """Get equipment category summary"""
        try:
            session = db.session()
            result = session.execute(text("""
                SELECT pos_equipment_category as category, COUNT(*) as count
                FROM raw_pos_equipment
                WHERE pos_equipment_category IS NOT NULL
                  AND pos_equipment_category != ''
                GROUP BY pos_equipment_category
                ORDER BY count DESC
                LIMIT 10
            """))

            return [{'category': row.category, 'count': row.count} for row in result.fetchall()]

        except Exception as e:
            logger.error(f"Failed to get category summary: {e}")
            return []

    def _get_recent_summary(self) -> Dict:
        """Get recent transaction summary"""
        try:
            session = db.session()
            result = session.execute(text("""
                SELECT COUNT(*) as count
                FROM raw_pos_transactions
                WHERE pos_transactions_out >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            """))

            recent_count = result.scalar()
            return {'last_30_days': recent_count}

        except Exception as e:
            logger.error(f"Failed to get recent summary: {e}")
            return {}

    def _get_user_category_mapping(self, equipment_num: str) -> Dict:
        """Get user category mapping for equipment"""
        try:
            if not equipment_num:
                return {}

            session = db.session()

            # First try to find by matching rental_class_id from RFID correlation
            rfid_result = session.execute(text("""
                SELECT im.rental_class_num
                FROM id_item_master im
                WHERE im.rental_class_num = :equipment_num
                LIMIT 1
            """), {'equipment_num': equipment_num})

            rental_class_id = rfid_result.scalar()

            if rental_class_id:
                # Get user mapping by rental_class_id
                mapping_result = session.execute(text("""
                    SELECT category, subcategory, short_common_name
                    FROM user_rental_class_mappings
                    WHERE rental_class_id = :rental_class_id
                    LIMIT 1
                """), {'rental_class_id': str(rental_class_id)})

                mapping_row = mapping_result.fetchone()
                if mapping_row:
                    return {
                        'category': mapping_row.category,
                        'subcategory': mapping_row.subcategory,
                        'short_common_name': mapping_row.short_common_name
                    }

            return {}

        except Exception as e:
            logger.error(f"Failed to get user category mapping: {e}")
            return {}

    def _get_default_category_from_csv_number(self, csv_category_number) -> Dict:
        """Get default category/subcategory from CSV category number using cats.pdf mappings"""
        try:
            category_description = get_category_description(csv_category_number)

            # Both category and subcategory use the same description as default
            return {
                'category': category_description,
                'subcategory': category_description  # Same text for both as requested
            }

        except Exception as e:
            logger.error(f"Failed to get default category mapping: {e}")
            return {
                'category': 'Unmapped Equipment',
                'subcategory': 'Unmapped Equipment'
            }

    def _get_store_name_from_location(self, location: str) -> Optional[str]:
        """Get store name from location using store mappings"""
        try:
            if not location:
                return None

            session = db.session()

            # Try to match location against store mappings
            result = session.execute(text("""
                SELECT store_name
                FROM store_mappings
                WHERE store_id = :location
                   OR pos_store_code = :location
                   OR store_name LIKE :location_like
                LIMIT 1
            """), {
                'location': location,
                'location_like': f'%{location}%'
            })

            row = result.fetchone()
            return row.store_name if row else None

        except Exception as e:
            logger.error(f"Failed to get store name from location: {e}")
            return None

    def _load_store_mapping(self) -> Dict[str, str]:
        """Load store mapping from STORES config"""
        try:
            # Create mapping from display codes to POS codes
            mapping = {}
            for store_code, store_info in STORES.items():
                # Display code (6800) → POS code (002)
                mapping[store_code] = store_info.pos_code
                # Also support POS code → POS code (002 → 002)
                mapping[store_info.pos_code] = store_info.pos_code
                # Support with leading zeros stripped (2 → 002)
                mapping[str(int(store_info.pos_code))] = store_info.pos_code
            return mapping
        except Exception as e:
            logger.error(f"Failed to load store mapping: {e}")
            return {}

    def get_common_names_for_category(self, category: str, subcategory: str, store_filter: str = None,
                                     page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Get common names (equipment names) for a category/subcategory with POS vs RFID comparison"""
        try:
            logger.info(f"Getting common names for {category}/{subcategory} using bedrock transformation")

            # Use correct table relationships without problematic columns
            query = """
            SELECT DISTINCT
                rpe.pos_equipment_name as common_name,
                rpe.pos_equipment_num as equipment_num,
                rpe.pos_equipment_qty as pos_quantity,
                COUNT(im.tag_id) as rfid_count,
                urcm.category,
                urcm.subcategory
            FROM raw_pos_equipment rpe
            INNER JOIN user_rental_class_mappings urcm
                ON rpe.pos_equipment_num = urcm.rental_class_id
            LEFT JOIN id_item_master im
                ON rpe.pos_equipment_num = im.rental_class_num
                AND im.tag_id IS NOT NULL
                AND im.tag_id != ''
            WHERE urcm.category = :category
                AND urcm.subcategory = :subcategory
                AND rpe.pos_equipment_name IS NOT NULL
                AND rpe.pos_equipment_name != ''
            """

            params = {'category': category, 'subcategory': subcategory}

            # Add store filter if specified
            if store_filter and store_filter != 'all':
                # Convert display store to POS store if needed
                pos_store_code = self.store_mapping.get(store_filter, store_filter)
                query += " AND rpe.pos_equipment_currentstore = :store_filter"
                params['store_filter'] = pos_store_code

            query += """
            GROUP BY rpe.pos_equipment_name, rpe.pos_equipment_num, rpe.pos_equipment_qty,
                     urcm.category, urcm.subcategory
            ORDER BY rpe.pos_equipment_name ASC
            """

            # Apply pagination
            offset = (page - 1) * per_page
            paginated_query = query + f" LIMIT {per_page} OFFSET {offset}"

            with db.engine.connect() as connection:
                # Get paginated results
                result = connection.execute(text(paginated_query), params)

                # Get total count
                count_query = f"SELECT COUNT(*) FROM ({query}) as counted"
                count_result = connection.execute(text(count_query), params)
                total_count = count_result.scalar()

                common_names = []
                for row in result:
                    common_name = row[0] if row[0] else 'Unknown Equipment'
                    equipment_num = row[1]
                    pos_quantity = int(row[2]) if row[2] else 0
                    rfid_count = int(row[3]) if row[3] else 0

                    # Calculate mismatch indicator
                    quantity_match = rfid_count == pos_quantity
                    mismatch_type = ""
                    if not quantity_match:
                        if rfid_count > pos_quantity:
                            mismatch_type = "more_tags_than_pos"
                        else:
                            mismatch_type = "fewer_tags_than_pos"

                    # Estimate status (simplified since we can't rely on non-existent columns)
                    items_available = max(pos_quantity, rfid_count)  # Use higher count
                    items_on_contracts = 0  # Will enhance when contract correlation is fixed
                    items_in_service = 0   # Will enhance when status tracking is fixed

                    common_names.append({
                        "name": common_name,
                        "pos_quantity": pos_quantity,      # POS system quantity
                        "rfid_count": rfid_count,          # Actual RFID tagged count
                        "quantity_match": quantity_match,   # True if counts match
                        "mismatch_type": mismatch_type,    # Type of mismatch if any
                        "total_items": max(pos_quantity, rfid_count),
                        "items_on_contracts": items_on_contracts,
                        "items_in_service": items_in_service,
                        "items_available": items_available,
                        "equipment_num": equipment_num,
                        "source": "bedrock_transformation"
                    })

                return {
                    'items': common_names,
                    'total': total_count,
                    'page': page,
                    'per_page': per_page,
                    'has_more': (offset + len(common_names)) < total_count
                }

        except Exception as e:
            logger.error(f"Bedrock transformation error in get_common_names_for_category: {e}", exc_info=True)
            logger.error(f"Failed parameters - category: {category}, subcategory: {subcategory}, store_filter: {store_filter}")
            return {
                'items': [],
                'total': 0,
                'page': page,
                'per_page': per_page,
                'has_more': False,
                'error_context': f"Transformation failed for {category}/{subcategory}"
            }

    def get_individual_rfid_items(self, category: str, subcategory: str, equipment_name: str,
                                store_filter: str = None, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """Get individual RFID tagged items for a specific equipment name"""
        try:
            logger.info(f"Getting individual RFID items for {category}/{subcategory}/{equipment_name}")

            # Build base query to get individual RFID items
            base_query = """
            SELECT DISTINCT
                im.tag_id,
                im.rental_class_num,
                rpe.pos_equipment_name as equipment_name,
                im.status as rfid_status,
                rpe.pos_equipment_currentstore as store_code,
                COALESCE(stores_map.name, rpe.pos_equipment_currentstore) as store_name
            FROM id_item_master im
            INNER JOIN raw_pos_equipment rpe ON im.rental_class_num = rpe.pos_equipment_num
            INNER JOIN user_rental_class_mappings urcm ON rpe.pos_equipment_num = urcm.rental_class_id
            LEFT JOIN (
                SELECT code, name FROM (
                    SELECT '001' as code, 'Wayzata' as name
                    UNION SELECT '002' as code, 'Brooklyn Park' as name
                    UNION SELECT '003' as code, 'Fridley' as name
                    UNION SELECT '004' as code, 'Elk River' as name
                ) stores
            ) stores_map ON rpe.pos_equipment_currentstore = stores_map.code
            WHERE urcm.category = :category
                AND urcm.subcategory = :subcategory
                AND rpe.pos_equipment_name = :equipment_name
            """

            # Add store filtering if specified
            if store_filter and store_filter != 'all':
                store_codes = self._get_store_codes_for_filter(store_filter)
                if store_codes:
                    placeholders = ','.join([f':store_{i}' for i in range(len(store_codes))])
                    base_query += f" AND rpe.pos_equipment_currentstore IN ({placeholders})"

            # Add pagination
            offset = (page - 1) * per_page
            base_query += f" ORDER BY im.tag_id LIMIT {per_page} OFFSET {offset}"

            # Execute query
            session = db.session()
            query_params = {
                'category': category,
                'subcategory': subcategory,
                'equipment_name': equipment_name
            }

            # Add store filter parameters if needed
            if store_filter and store_filter != 'all':
                store_codes = self._get_store_codes_for_filter(store_filter)
                if store_codes:
                    for i, code in enumerate(store_codes):
                        query_params[f'store_{i}'] = code

            result = session.execute(text(base_query), query_params)
            rows = result.fetchall()

            # Transform results
            items = []
            for row in rows:
                items.append({
                    'tag_id': row.tag_id,
                    'rental_class_num': row.rental_class_num,
                    'equipment_name': row.equipment_name,
                    'rfid_status': row.rfid_status,
                    'store_code': row.store_code,
                    'store_name': row.store_name
                })

            # Get total count for pagination
            count_query = """
            SELECT COUNT(DISTINCT im.tag_id)
            FROM id_item_master im
            INNER JOIN raw_pos_equipment rpe ON im.rental_class_num = rpe.pos_equipment_num
            INNER JOIN user_rental_class_mappings urcm ON rpe.pos_equipment_num = urcm.rental_class_id
            WHERE urcm.category = :category
                AND urcm.subcategory = :subcategory
                AND rpe.pos_equipment_name = :equipment_name
            """

            if store_filter and store_filter != 'all':
                store_codes = self._get_store_codes_for_filter(store_filter)
                if store_codes:
                    placeholders = ','.join([f':store_{i}' for i in range(len(store_codes))])
                    count_query += f" AND rpe.pos_equipment_currentstore IN ({placeholders})"

            count_result = session.execute(text(count_query), query_params)
            total = count_result.scalar() or 0

            logger.info(f"Found {len(items)} individual RFID items for {equipment_name} (total: {total})")

            return {
                'items': items,
                'total': total,
                'page': page,
                'per_page': per_page,
                'has_more': total > (page * per_page)
            }

        except Exception as e:
            logger.error(f"Failed to get individual RFID items: {e}", exc_info=True)
            return {
                'items': [],
                'total': 0,
                'page': page,
                'per_page': per_page,
                'has_more': False,
                'error': str(e)
            }


# Service instance
bedrock_transformation_service = BedrockTransformationService()