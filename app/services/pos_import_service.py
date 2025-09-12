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
                        existing = POSTransaction.query.filter_by(
                            contract_no=row.get('Contract No', '').strip(),
                            store_no=row.get('Store No', '001').strip()
                        ).first()
                        
                        if existing:
                            logger.debug(f"Transaction already exists: {row.get('Contract No')}")
                            continue
                        
                        # Create new transaction with comprehensive field mapping
                        transaction = POSTransaction(
                            # Basic transaction info (using CSV column names)
                            contract_no=row.get('CNTR', '').strip(),
                            store_no=row.get('STR', '001').strip(),
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
                        contract_no = row.get('Contract No', '').strip()
                        line_number = int(row.get('LineNumber', 0))
                        
                        # Check if item already exists
                        existing = POSTransactionItem.query.filter_by(
                            contract_no=contract_no,
                            line_number=line_number
                        ).first()
                        
                        if existing:
                            logger.debug(f"Item already exists: {contract_no} line {line_number}")
                            continue
                        
                        # Create new item
                        item = POSTransactionItem(
                            contract_no=contract_no,
                            item_num=row.get('ItemNum', '').strip() or None,
                            qty=int(row.get('Qty', 0) or 0),
                            hours=int(row.get('Hours', 0) or 0),
                            due_date=self.parse_date(row.get('Due Date')),
                            due_time=row.get('Due Time', '').strip() or None,
                            line_status=row.get('Line Status', '').strip() or None,
                            price=self.parse_decimal(row.get('Price')),
                            desc=row.get('Desc', '').strip() or None,
                            dmg_wvr=self.parse_decimal(row.get('DmgWvr')),
                            item_percentage=self.parse_decimal(row.get('ItemPercentage')),
                            discount_percent=self.parse_decimal(row.get('DiscountPercent')),
                            nontaxable=self.parse_bool(row.get('Nontaxable')),
                            nondiscount=self.parse_bool(row.get('Nondiscount')),
                            discount_amt=self.parse_decimal(row.get('Discount Amt')),
                            daily_amt=self.parse_decimal(row.get('Daily Amt')),
                            weekly_amt=self.parse_decimal(row.get('Weekly Amt')),
                            monthly_amt=self.parse_decimal(row.get('Monthly Amt')),
                            minimum_amt=self.parse_decimal(row.get('Minimum Amt')),
                            meter_out=self.parse_decimal(row.get('Meter Out')),
                            meter_in=self.parse_decimal(row.get('Meter In')),
                            downtime_hrs=self.parse_decimal(row.get('Downtime Hrs')),
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
                        key = row.get('Key', '').strip()
                        
                        # Check if customer already exists
                        existing = POSCustomer.query.filter_by(key=key).first()
                        
                        if existing:
                            # Update existing customer
                            existing.name = row.get('Name', '').strip() or existing.name
                            existing.address = row.get('Address', '').strip() or existing.address
                            existing.city = row.get('City', '').strip() or existing.city
                            existing.email = row.get('Email', '').strip() or existing.email
                            existing.phone = row.get('Phone', '').strip() or existing.phone
                            existing.current_balance = self.parse_decimal(row.get('CurrentBalance'))
                            existing.last_active_date = self.parse_date(row.get('Last Active Date'))
                            logger.debug(f"Updated customer: {key}")
                        else:
                            # Create new customer
                            customer = POSCustomer(
                                key=key,
                                cnum=row.get('CNUM', '').strip() or None,
                                name=row.get('Name', '').strip() or None,
                                address=row.get('Address', '').strip() or None,
                                address2=row.get('Address2', '').strip() or None,
                                city=row.get('City', '').strip() or None,
                                zip=row.get('Zip', '').strip() or None,
                                zip4=row.get('Zip4', '').strip() or None,
                                phone=row.get('Phone', '').strip() or None,
                                work_phone=row.get('Work Phone', '').strip() or None,
                                mobile_phone=row.get('Mobile Phone', '').strip() or None,
                                email=row.get('Email', '').strip() or None,
                                credit_limit=self.parse_decimal(row.get('Credit Limit')),
                                ytd_payments=self.parse_decimal(row.get('YTD Payments')),
                                ltd_payments=self.parse_decimal(row.get('LTD Payments')),
                                last_year_payments=self.parse_decimal(row.get('Last Year Payments')),
                                no_of_contracts=int(row.get('No of Contracts', 0) or 0),
                                current_balance=self.parse_decimal(row.get('CurrentBalance')),
                                open_date=self.parse_date(row.get('Open Date')),
                                last_active_date=self.parse_date(row.get('Last Active Date')),
                                last_contract=row.get('Last Contract', '').strip() or None
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
                        item_num = row.get('ItemNum', '').strip()
                        
                        if not item_num:
                            logger.warning(f"Row {row_num}: Missing ItemNum, skipping")
                            continue
                        
                        # Check if equipment already exists
                        existing = POSEquipment.query.filter_by(item_num=item_num).first()
                        
                        if existing:
                            # Update existing equipment
                            existing.name = row.get('Name', '').strip() or existing.name
                            existing.category = row.get('Category', '').strip() or existing.category
                            existing.current_store = row.get('Current Store', '').strip() or existing.current_store
                            existing.qty = int(row.get('Qty', 0) or 0)
                            existing.inactive = self.parse_bool(row.get('Inactive'))
                            logger.debug(f"Updated equipment: {item_num}")
                        else:
                            # Create new equipment
                            equipment = POSEquipment(
                                item_num=item_num,
                                key_field=row.get('Key', '').strip() or None,
                                name=row.get('Name', '').strip() or None,
                                loc=row.get('Loc', '').strip() or None,
                                category=row.get('Category', '').strip() or None,
                                department=row.get('Department', '').strip() or None,
                                type_desc=row.get('Type Desc', '').strip() or None,
                                qty=int(row.get('Qty', 0) or 0),
                                home_store=row.get('Home Store', '').strip() or None,
                                current_store=row.get('Current Store', '').strip() or None,
                                group_field=row.get('Group', '').strip() or None,
                                manf=row.get('MANF', '').strip() or None,
                                model_no=row.get('ModelNo', '').strip() or None,
                                serial_no=row.get('SerialNo', '').strip() or None,
                                part_no=row.get('PartNo', '').strip() or None,
                                license_no=row.get('License No', '').strip() or None,
                                model_year=row.get('Model Year', '').strip() or None,
                                sell_price=self.parse_decimal(row.get('Sell Price')),
                                retail_price=self.parse_decimal(row.get('RetailPrice')),
                                deposit=self.parse_decimal(row.get('Deposit')),
                                inactive=self.parse_bool(row.get('Inactive')),
                                import_batch=self.batch_id
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
            # Import transactions  
            trans_file = os.path.join(base_path, 'transactionsPOS8.26.25.csv')
            if os.path.exists(trans_file):
                imported, failed, errors = self.import_transactions(trans_file)
                results['transactions'] = {
                    'imported': imported,
                    'failed': failed,
                    'errors': errors[:10]  # Limit errors in response
                }
                results['total_imported'] += imported
                results['total_failed'] += failed
            
            # Import transaction items
            items_file = os.path.join(base_path, 'transitemsPOS8.26.25.csv')
            if os.path.exists(items_file):
                imported, failed, errors = self.import_transaction_items(items_file)
                results['items'] = {
                    'imported': imported,
                    'failed': failed,
                    'errors': errors[:10]
                }
                results['total_imported'] += imported
                results['total_failed'] += failed
            
            # Import customers
            cust_file = os.path.join(base_path, 'customerPOS8.26.25.csv')
            if os.path.exists(cust_file):
                imported, failed, errors = self.import_customers(cust_file)
                results['customers'] = {
                    'imported': imported,
                    'failed': failed,
                    'errors': errors[:10]
                }
                results['total_imported'] += imported
                results['total_failed'] += failed
            
            # Import equipment
            equip_file = os.path.join(base_path, 'equipPOS8.26.25.csv')
            if os.path.exists(equip_file):
                imported, failed, errors = self.import_equipment(equip_file)
                results['equipment'] = {
                    'imported': imported,
                    'failed': failed,
                    'errors': errors[:10]
                }
                results['total_imported'] += imported
                results['total_failed'] += failed
            
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
