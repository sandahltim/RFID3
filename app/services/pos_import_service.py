# app/services/pos_import_service.py
# POS Data Import Service
# Created: 2025-08-28

import csv
import os
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Tuple, Optional
from sqlalchemy import and_, or_, func
from app import db
from app.models.pos_models import (
    POSTransaction, POSTransactionItem, POSCustomer, POSEquipment,
    POSImportLog, POSRFIDCorrelation, POSInventoryDiscrepancy
)
from app.services.logger import get_logger

logger = get_logger(__name__)


class POSImportService:
    """Service for importing POS data from CSV files."""
    
    def __init__(self):
        self.batch_id = None
        self.import_log = None
        self.errors = []
        self.warnings = []
        
    def generate_batch_id(self) -> str:
        """Generate unique batch ID for import."""
        return f"POS_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats from POS data."""
        if not date_str or date_str in ['', 'NULL', '12/30/1899 12:00 AM']:
            return None
            
        # Try different date formats
        formats = [
            '%m/%d/%Y %H:%M',
            '%m/%d/%Y %H:%M:%S',
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y',
            '%Y-%m-%d'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def parse_decimal(self, value_str: str) -> Optional[Decimal]:
        """Parse decimal values from POS data."""
        if not value_str or value_str in ['', 'NULL', None]:
            return None
        try:
            # Remove any currency symbols and commas
            cleaned = value_str.replace('$', '').replace(',', '').strip()
            return Decimal(cleaned) if cleaned else None
        except (ValueError, TypeError, InvalidOperation) as e:
            logger.warning(f"Could not parse decimal '{value_str}': {str(e)}")
            return None
    
    def parse_bool(self, value_str: str) -> bool:
        """Parse boolean values from POS data."""
        if not value_str:
            return False
        return value_str.upper() in ['TRUE', 'T', 'YES', 'Y', '1']
    
    def parse_int(self, value_str: str) -> Optional[int]:
        """Parse integer values from POS data."""
        if not value_str or value_str.strip() == '':
            return None
        try:
            return int(float(value_str))  # Handle decimals that should be ints
        except (ValueError, TypeError):
            return None
    
    def import_transactions(self, file_path: str) -> Tuple[int, int, List[str]]:
        """Import POS transactions from CSV file."""
        logger.info(f"Starting transaction import from: {file_path}")
        
        imported = 0
        failed = 0
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Check if transaction already exists
                        contract_no = row.get('CNTR', '').strip()
                        store_no = row.get('STR', '001').strip()

                        existing = POSTransaction.query.filter_by(
                            contract_no=contract_no,
                            store_no=store_no
                        ).first()

                        if existing:
                            logger.debug(f"Transaction already exists: {contract_no}")
                            continue

                        # Create new transaction with correct CSV column mapping
                        transaction = POSTransaction(
                            # Basic transaction info (using actual CSV column names)
                            contract_no=contract_no,
                            store_no=store_no,
                            customer_no=row.get('CUSN', '').strip() or None,
                            stat=row.get('STAT', '').strip() or None,
                            status=row.get('Status', '').strip() or None,
                            contract_date=self.parse_date(row.get('DATE')),
                            contract_time=row.get('TIME', '').strip() or None,
                            last_modified_date=self.parse_date(row.get('UpdatedDateTime')),
                            close_date=self.parse_date(row.get('CLDT')),
                            billed_date=self.parse_date(row.get('Billed')),
                            completed_date=self.parse_date(row.get('Completed')),
                            
                            # Financial fields
                            rent_amt=self.parse_decimal(row.get('RENT')),
                            sale_amt=self.parse_decimal(row.get('SALE')),
                            tax_amt=self.parse_decimal(row.get('TAX')),
                            dmg_wvr_amt=self.parse_decimal(row.get('DMG')),
                            total=self.parse_decimal(row.get('TOTL')),
                            total_paid=self.parse_decimal(row.get('PAID')),
                            payment_method=row.get('PYMT', '').strip() or None,
                            total_owed=self.parse_decimal(row.get('TOTL')) - self.parse_decimal(row.get('PAID')) if self.parse_decimal(row.get('TOTL')) and self.parse_decimal(row.get('PAID')) else None,
                            deposit_paid_amt=self.parse_decimal(row.get('DEPP')),
                            
                            # Contact info
                            contact=row.get('Contact', '').strip() or None,
                            contact_phone=row.get('ContactPhone', '').strip() or None,
                            ordered_by=row.get('OrderedBy', '').strip() or None,
                            
                            # Delivery info (original fields)
                            delivery_requested=self.parse_bool(row.get('Delvr')),
                            promised_delivery_date=self.parse_date(row.get('DeliveryDatePromised')),
                            actual_delivery_date=self.parse_date(row.get('DeliveryDate')),
                            delivery_truck_no=row.get('DeliveryTruckNumber', '').strip() or None,
                            delivery_trip_no=row.get('DeliveryTrip', '').strip() or None,
                            delivered_to=row.get('DeliverToCompany', '').strip() or None,
                            delivery_address=row.get('DeliveryAddress', '').strip() or None,
                            delivery_city=row.get('DeliveryCity', '').strip() or None,
                            delivery_zipcode=row.get('DeliveryZip', '').strip() or None,
                            
                            # Pickup info (original fields)
                            pickup_requested=self.parse_bool(row.get('Pickup')),
                            promised_pickup_date=self.parse_date(row.get('PickupDatePromised')),
                            actual_pickup_date=self.parse_date(row.get('PickupDate')),
                            pickup_truck_no=row.get('PickupTruckNumber', '').strip() or None,
                            pickup_trip_no=row.get('PickupTrip', '').strip() or None,
                            picked_up_by=row.get('PickedUpBy', '').strip() or None,
                            
                            # Job info
                            job_po=row.get('JBPO', '').strip() or None,
                            job_id=row.get('JBID', '').strip() or None,
                            job_site=row.get('JobSite', '').strip() or None,
                            type=row.get('TransactionType', '').strip() or None,
                            
                            # NEW COMPREHENSIVE FIELDS
                            # Operator and management
                            operator_id=row.get('OPID', '').strip() or None,
                            operator_created=row.get('OperatorCreated', '').strip() or None,
                            operator_assigned=row.get('OperatorAssigned', '').strip() or None,
                            salesman=row.get('Salesman', '').strip() or None,
                            current_modify_op_no=row.get('CurrentModifyOpNo', '').strip() or None,
                            
                            # Transaction status
                            secondary_status=row.get('SecondaryStatus', '').strip() or None,
                            cancelled=self.parse_bool(row.get('Cancelled')),
                            review_billing=self.parse_bool(row.get('ReviewBilling')),
                            archived=self.parse_bool(row.get('Archived')),
                            transaction_type=row.get('TransactionType', '').strip() or None,
                            operation=row.get('Operation', '').strip() or None,
                            
                            # Financial details
                            rent_discount=self.parse_decimal(row.get('RentDiscount')),
                            sale_discount=self.parse_decimal(row.get('SaleDiscount')),
                            sale_discount_percent=self.parse_decimal(row.get('Discount')),
                            item_percentage=self.parse_decimal(row.get('ItemPercentage')),
                            damage_waiver_exempt=self.parse_bool(row.get('DamageWaiverExempt')),
                            item_percentage_exempt=self.parse_bool(row.get('ItemPercentageExempt')),
                            damage_waiver_tax_amount=self.parse_decimal(row.get('DamageWaiverTaxAmount')),
                            item_percentage_tax_amount=self.parse_decimal(row.get('ItemPercentageTaxAmount')),
                            other_tax_amount=self.parse_decimal(row.get('OtherTaxAmount')),
                            tax_code=row.get('TaxCode', '').strip() or None,
                            price_level=row.get('PriceLevel', '').strip() or None,
                            rate_engine_id=row.get('RateEngineId', '').strip() or None,
                            desired_deposit=self.parse_decimal(row.get('DesiredDeposit')),
                            
                            # Payment and accounting
                            payment_deposit_paid=self.parse_decimal(row.get('DEPP')),
                            payment_deposit_required=self.parse_decimal(row.get('DEPR')),
                            card_swipe=self.parse_bool(row.get('CardSwipe')),
                            posted_cash=self.parse_bool(row.get('PostedCash')),
                            posted_accrual=self.parse_bool(row.get('PostedAccrual')),
                            currency_number=row.get('CurrencyNumber', '').strip() or None,
                            exchange_rate=self.parse_decimal(row.get('ExchangeRate')),
                            discount_table=row.get('DiscountTable', '').strip() or None,
                            accounting_link=row.get('AccountingLink', '').strip() or None,
                            accounting_transaction_id=row.get('AccountingTransactionId', '').strip() or None,
                            invoice_number=row.get('InvoiceNumber', '').strip() or None,
                            revenue_date=self.parse_date(row.get('RevenueDate')),
                            
                            # Enhanced delivery details
                            delivery_confirmed=self.parse_bool(row.get('DeliveryConfirmed')),
                            delivery_trip=row.get('DeliveryTrip', '').strip() or None,
                            delivery_route=row.get('DeliveryRoute', '').strip() or None,
                            delivery_crew_count=self.parse_int(row.get('DeliveryCrewCount')),
                            delivery_setup_time=self.parse_int(row.get('DeliverySetupTime')),
                            delivery_setup_time_computed=self.parse_int(row.get('DeliverySetupTimeComputed')),
                            delivery_notes=row.get('DeliveryNotes', '').strip() or None,
                            deliver_to_company=row.get('DeliverToCompany', '').strip() or None,
                            delivery_verified_address=self.parse_bool(row.get('VerifiedAddress')),
                            delivery_same_address=self.parse_bool(row.get('SameAddress')),
                            
                            # Enhanced pickup details
                            pickup_confirmed=self.parse_bool(row.get('PickupConfirmed')),
                            pickup_trip=row.get('PickupTrip', '').strip() or None,
                            pickup_route=row.get('PickupRoute', '').strip() or None,
                            pickup_crew_count=self.parse_int(row.get('PickupCrewCount')),
                            pickup_load_time=self.parse_int(row.get('PickupLoadTime')),
                            pickup_notes=row.get('PickupNotes', '').strip() or None,
                            pickup_contact=row.get('PickupContact', '').strip() or None,
                            pickup_contact_phone=row.get('PickupContactPhone', '').strip() or None,
                            pickup_from_company=row.get('PickupFromCompany', '').strip() or None,
                            pickup_verified_address=self.parse_bool(row.get('PickupVerifiedAddress')),
                            pickup_same_address=self.parse_bool(row.get('PickupSameAddress')),
                            pickup_address=row.get('PickupAddress', '').strip() or None,
                            pickup_city=row.get('PickupCity', '').strip() or None,
                            pickup_zipcode=row.get('PickupZip', '').strip() or None,
                            picked_up_by_dl_no=row.get('PickedUpDlNo', '').strip() or None,
                            auto_license=row.get('AutoLicense', '').strip() or None,
                            
                            # Event and contract management
                            event_end_date=self.parse_date(row.get('EventEndDate')),
                            master_bill=row.get('MasterBill', '').strip() or None,
                            parent_contract=row.get('ParentContract', '').strip() or None,
                            service_seq=self.parse_int(row.get('ServiceSeq')),
                            modification=row.get('Modification', '').strip() or None,
                            notes=row.get('Notes', '').strip() or None,
                            class_id=row.get('ClassID', '').strip() or None,
                            
                            # Communication and documentation
                            last_letter=row.get('LastLetter', '').strip() or None,
                            letter_date=self.parse_date(row.get('LetterDate')),
                            updated_date_time=self.parse_date(row.get('UpdatedDateTime')),
                            created_date=self.parse_date(row.get('CreatedDate')),
                            
                            # Import metadata
                            import_batch=self.batch_id
                        )
                        
                        db.session.add(transaction)
                        imported += 1
                        
                        # Commit in batches
                        if imported % 100 == 0:
                            db.session.commit()
                            logger.info(f"Imported {imported} transactions...")
                            
                    except Exception as e:
                        failed += 1
                        error_msg = f"Row {row_num}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        db.session.rollback()
                
                # Final commit
                db.session.commit()
                logger.info(f"Transaction import complete: {imported} imported, {failed} failed")
                
        except Exception as e:
            logger.error(f"Failed to import transactions: {str(e)}")
            db.session.rollback()
            raise
        
        return imported, failed, errors
    
    def import_transaction_items(self, file_path: str) -> Tuple[int, int, List[str]]:
        """Import POS transaction items from CSV file."""
        logger.info(f"Starting transaction items import from: {file_path}")
        
        imported = 0
        failed = 0
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        contract_no = row.get('CNTR', '').strip()
                        line_number = self.parse_int(row.get('LineNumber', 0)) or self.parse_int(row.get('SUBF', 0)) or 0

                        # Check if item already exists
                        existing = POSTransactionItem.query.filter_by(
                            contract_no=contract_no,
                            line_number=line_number
                        ).first()

                        if existing:
                            logger.debug(f"Item already exists: {contract_no} line {line_number}")
                            continue

                        # Create new item with correct CSV column mapping
                        item = POSTransactionItem(
                            contract_no=contract_no,
                            item_num=row.get('ITEM', '').strip() or None,
                            qty=self.parse_int(row.get('QTY', 0)) or 0,
                            hours=self.parse_int(row.get('HRSC', 0)) or 0,
                            due_date=self.parse_date(row.get('DDT')),
                            due_time=row.get('DTM', '').strip() or None,
                            line_status=row.get('TXTY', '').strip() or None,
                            price=self.parse_decimal(row.get('PRIC')),
                            desc=row.get('Desc', '').strip() or None,
                            dmg_wvr=self.parse_decimal(row.get('DmgWvr')),
                            item_percentage=self.parse_decimal(row.get('ItemPercentage')),
                            discount_percent=self.parse_decimal(row.get('DiscountPercent')),
                            nontaxable=self.parse_bool(row.get('Nontaxable')),
                            nondiscount=self.parse_bool(row.get('Nondiscount')),
                            discount_amt=self.parse_decimal(row.get('DiscountAmount')),
                            daily_amt=self.parse_decimal(row.get('DailyAmount')),
                            weekly_amt=self.parse_decimal(row.get('WeeklyAmount')),
                            monthly_amt=self.parse_decimal(row.get('MonthlyAmount')),
                            minimum_amt=self.parse_decimal(row.get('MinimumAmount')),
                            meter_out=self.parse_decimal(row.get('ReadingOut')),
                            meter_in=self.parse_decimal(row.get('ReadingIn')),
                            downtime_hrs=self.parse_decimal(row.get('RainHours')),
                            retail_price=self.parse_decimal(row.get('RetailPrice')),
                            kit_field=row.get('KitField', '').strip() or None,
                            confirmed_date=self.parse_date(row.get('ConfirmedDate')),
                            line_number=line_number
                        )
                        
                        db.session.add(item)
                        imported += 1
                        
                        # Commit in batches
                        if imported % 100 == 0:
                            db.session.commit()
                            logger.info(f"Imported {imported} items...")
                            
                    except Exception as e:
                        failed += 1
                        error_msg = f"Row {row_num}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        db.session.rollback()
                
                # Final commit
                db.session.commit()
                logger.info(f"Item import complete: {imported} imported, {failed} failed")
                
        except Exception as e:
            logger.error(f"Failed to import items: {str(e)}")
            db.session.rollback()
            raise
        
        return imported, failed, errors
    
    def import_customers(self, file_path: str) -> Tuple[int, int, List[str]]:
        """Import POS customers from CSV file."""
        logger.info(f"Starting customer import from: {file_path}")
        
        imported = 0
        failed = 0
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        key = row.get('KEY', '').strip()

                        # Check if customer already exists
                        existing = POSCustomer.query.filter_by(key=key).first()

                        if existing:
                            # Update existing customer
                            existing.name = row.get('NAME', '').strip() or existing.name
                            existing.address = row.get('Address', '').strip() or existing.address
                            existing.city = row.get('CITY', '').strip() or existing.city
                            existing.phone = row.get('Phone', '').strip() or existing.phone
                            existing.last_active_date = self.parse_date(row.get('LastActive'))
                            logger.debug(f"Updated customer: {key}")
                        else:
                            # Create new customer with correct CSV column mapping
                            customer = POSCustomer(
                                key=key,
                                cnum=row.get('CNUM', '').strip() or None,
                                name=row.get('NAME', '').strip() or None,
                                address=row.get('Address', '').strip() or None,
                                address2=row.get('Address2', '').strip() or None,
                                city=row.get('CITY', '').strip() or None,
                                zip=row.get('ZIP', '').strip() or None,
                                zip4=row.get('ZIP4', '').strip() or None,
                                phone=row.get('Phone', '').strip() or None,
                                work_phone=row.get('WORK', '').strip() or None,
                                mobile_phone=row.get('MOBILE', '').strip() or None,
                                email=None,  # Not in CSV
                                credit_limit=None,  # Not in CSV
                                ytd_payments=None,  # Not in CSV
                                ltd_payments=None,  # Not in CSV
                                last_year_payments=None,  # Not in CSV
                                no_of_contracts=0,  # Not in CSV
                                current_balance=None,  # Not in CSV
                                open_date=self.parse_date(row.get('OpenDate')),
                                last_active_date=self.parse_date(row.get('LastActive')),
                                last_contract=None  # Not in CSV
                            )
                            
                            db.session.add(customer)
                        
                        imported += 1
                        
                        # Commit in batches
                        if imported % 100 == 0:
                            db.session.commit()
                            logger.info(f"Processed {imported} customers...")
                            
                    except Exception as e:
                        failed += 1
                        error_msg = f"Row {row_num}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        db.session.rollback()
                
                # Final commit
                db.session.commit()
                logger.info(f"Customer import complete: {imported} processed, {failed} failed")
                
        except Exception as e:
            logger.error(f"Failed to import customers: {str(e)}")
            db.session.rollback()
            raise
        
        return imported, failed, errors
    
    def import_equipment(self, file_path: str) -> Tuple[int, int, List[str]]:
        """Import POS equipment from CSV file."""
        logger.info(f"Starting equipment import from: {file_path}")
        
        imported = 0
        failed = 0 
        errors = []
        
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        item_num = row.get('KEY', '').strip()  # Equipment uses KEY as item identifier

                        if not item_num:
                            logger.warning(f"Row {row_num}: Missing KEY (item_num), skipping")
                            continue

                        # Check if equipment already exists
                        existing = POSEquipment.query.filter_by(item_num=item_num).first()

                        if existing:
                            # Update existing equipment
                            existing.name = row.get('Name', '').strip() or existing.name
                            existing.category = row.get('Category', '').strip() or existing.category
                            existing.qty = self.parse_int(row.get('QTY', 0)) or 0
                            logger.debug(f"Updated equipment: {item_num}")
                        else:
                            # Create new equipment with correct CSV column mapping
                            equipment = POSEquipment(
                                item_num=item_num,
                                key_field=item_num,  # KEY field
                                name=row.get('Name', '').strip() or None,
                                loc=row.get('LOC', '').strip() or None,
                                category=row.get('Category', '').strip() or None,
                                department=None,  # Not in CSV
                                type_desc=row.get('TYPE', '').strip() or None,
                                qty=self.parse_int(row.get('QTY', 0)) or 0,
                                home_store=None,  # Not in CSV
                                current_store=None,  # Not in CSV
                                group_field=None,  # Not in CSV
                                manf=None,  # Not in CSV
                                model_no=None,  # Not in CSV
                                serial_no=None,  # Not in CSV
                                part_no=None,  # Not in CSV
                                license_no=None,  # Not in CSV
                                model_year=None,  # Not in CSV
                                sell_price=self.parse_decimal(row.get('SELL')),
                                retail_price=None,  # Not in CSV
                                deposit=self.parse_decimal(row.get('DEP')),
                                inactive=False,  # Not in CSV
                                import_batch=self.batch_id,
                                # Additional fields from CSV
                                period_1=self.parse_decimal(row.get('PER1')),
                                period_2=self.parse_decimal(row.get('PER2')),
                                period_3=self.parse_decimal(row.get('PER3')),
                                period_4=self.parse_decimal(row.get('PER4'))
                            )
                            
                            db.session.add(equipment)
                        
                        imported += 1
                        
                        # Commit in batches  
                        if imported % 100 == 0:
                            db.session.commit()
                            logger.info(f"Processed {imported} equipment items...")
                            
                    except Exception as e:
                        failed += 1
                        error_msg = f"Row {row_num}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        db.session.rollback()
                
                # Final commit
                db.session.commit()
                logger.info(f"Equipment import complete: {imported} processed, {failed} failed")
                
        except Exception as e:
            logger.error(f"Failed to import equipment: {str(e)}")
            db.session.rollback()
            raise
        
        return imported, failed, errors
    
    def import_all_pos_data(self, base_path: str = '/home/tim/RFID3/shared/POR') -> Dict:
        """Import all POS data files from directory."""
        self.batch_id = self.generate_batch_id()
        
        # Create import log
        self.import_log = POSImportLog(
            import_batch=self.batch_id,
            import_type='full',
            started_at=datetime.now(timezone.utc),
            status='processing',
            imported_by='system'
        )
        db.session.add(self.import_log)
        db.session.commit()
        
        results = {
            'batch_id': self.batch_id,
            'transactions': {'imported': 0, 'failed': 0, 'errors': []},
            'items': {'imported': 0, 'failed': 0, 'errors': []},
            'customers': {'imported': 0, 'failed': 0, 'errors': []},
            'equipment': {'imported': 0, 'failed': 0, 'errors': []},
            'total_imported': 0,
            'total_failed': 0
        }
        
        try:
            # Find the most recent CSV files dynamically
            import glob

            # Import transactions
            trans_files = glob.glob(os.path.join(base_path, 'transactions*.csv'))
            if trans_files:
                trans_file = max(trans_files, key=os.path.getmtime)  # Get most recent
                logger.info(f"Found transactions file: {trans_file}")
                imported, failed, errors = self.import_transactions(trans_file)
                results['transactions'] = {
                    'imported': imported,
                    'failed': failed,
                    'errors': errors[:10]  # Limit errors in response
                }
                results['total_imported'] += imported
                results['total_failed'] += failed
            else:
                logger.warning("No transactions CSV files found")

            # Import transaction items
            items_files = glob.glob(os.path.join(base_path, 'transitems*.csv'))
            if items_files:
                items_file = max(items_files, key=os.path.getmtime)  # Get most recent
                logger.info(f"Found transaction items file: {items_file}")
                imported, failed, errors = self.import_transaction_items(items_file)
                results['items'] = {
                    'imported': imported,
                    'failed': failed,
                    'errors': errors[:10]
                }
                results['total_imported'] += imported
                results['total_failed'] += failed
            else:
                logger.warning("No transaction items CSV files found")

            # Import customers
            cust_files = glob.glob(os.path.join(base_path, 'customer*.csv'))
            if cust_files:
                cust_file = max(cust_files, key=os.path.getmtime)  # Get most recent
                logger.info(f"Found customer file: {cust_file}")
                imported, failed, errors = self.import_customers(cust_file)
                results['customers'] = {
                    'imported': imported,
                    'failed': failed,
                    'errors': errors[:10]
                }
                results['total_imported'] += imported
                results['total_failed'] += failed
            else:
                logger.warning("No customer CSV files found")

            # Import equipment
            equip_files = glob.glob(os.path.join(base_path, 'equip*.csv'))
            if equip_files:
                equip_file = max(equip_files, key=os.path.getmtime)  # Get most recent
                logger.info(f"Found equipment file: {equip_file}")
                imported, failed, errors = self.import_equipment(equip_file)
                results['equipment'] = {
                    'imported': imported,
                    'failed': failed,
                    'errors': errors[:10]
                }
                results['total_imported'] += imported
                results['total_failed'] += failed
            else:
                logger.warning("No equipment CSV files found")
            
            # Update import log
            self.import_log.status = 'completed'
            self.import_log.completed_at = datetime.now(timezone.utc)
            self.import_log.records_imported = results['total_imported']
            self.import_log.records_failed = results['total_failed']
            self.import_log.import_summary = results
            db.session.commit()
            
            logger.info(f"POS import completed: {results['total_imported']} imported, {results['total_failed']} failed")
            
        except Exception as e:
            # Update import log with error
            self.import_log.status = 'failed'
            self.import_log.completed_at = datetime.now(timezone.utc)
            self.import_log.error_messages = [str(e)]
            db.session.commit()
            
            logger.error(f"POS import failed: {str(e)}")
            raise
        
        return results


# Initialize service instance
pos_import_service = POSImportService()
