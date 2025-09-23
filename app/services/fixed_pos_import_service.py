# Fixed POS Import Service - CSV Direct Import Only
# Version: 2025-09-23
# Purpose: Automated Tuesday 8am CSV imports from POR folder

import pandas as pd
import os
from datetime import datetime
from sqlalchemy import text
from app import db
from app.services.logger import get_logger

logger = get_logger(__name__)

class FixedPOSImportService:
    """
    Fixed POS import service for automated Tuesday 8am imports
    Imports directly from CSV files, no RFIDpro API dependency
    """

    def __init__(self):
        self.csv_base_path = "/home/tim/RFID3/shared/POR"

    def import_all_pos_data(self) -> dict:
        """
        Import all POS CSV files automatically
        Designed for Tuesday 8am scheduler execution
        """
        results = {
            'equipment': {'imported': 0, 'errors': []},
            'customers': {'imported': 0, 'errors': []},
            'transactions': {'imported': 0, 'errors': []},
            'transitems': {'imported': 0, 'errors': []},
            'total_imported': 0,
            'batch_id': f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }

        try:
            # Import equipment (equipPOS*.csv)
            equipment_result = self._import_equipment_csv()
            results['equipment'] = equipment_result
            results['total_imported'] += equipment_result['imported']

            # Import customers (customer*.csv)
            customer_result = self._import_customers_csv()
            results['customers'] = customer_result
            results['total_imported'] += customer_result['imported']

            # Import transactions (transactions*.csv)
            transaction_result = self._import_transactions_csv()
            results['transactions'] = transaction_result
            results['total_imported'] += transaction_result['imported']

            # Import transitems (transitems*.csv)
            transitems_result = self._import_transitems_csv()
            results['transitems'] = transitems_result
            results['total_imported'] += transitems_result['imported']

            logger.info(f"POS import completed: {results['total_imported']} total records imported")
            return results

        except Exception as e:
            logger.error(f"POS import failed: {e}")
            return {'error': str(e), 'total_imported': 0}

    def _import_equipment_csv(self) -> dict:
        """Import latest equipPOS CSV file"""
        try:
            # Find latest equipPOS file
            equipment_files = [f for f in os.listdir(self.csv_base_path)
                             if f.startswith('equipPOS') and f.endswith('.csv')]

            if not equipment_files:
                return {'imported': 0, 'errors': ['No equipPOS files found']}

            latest_file = max(equipment_files, key=lambda f: os.path.getmtime(os.path.join(self.csv_base_path, f)))
            file_path = os.path.join(self.csv_base_path, latest_file)

            # Read and import
            df = pd.read_csv(file_path)
            df_active = df[df['Inactive'] != True]  # Filter active items

            logger.info(f"Importing {len(df_active)} active equipment from {latest_file}")

            session = db.session()
            imported = 0

            for _, row in df_active.iterrows():
                try:
                    session.execute(text('''
                        INSERT INTO pos_equipment (key_field, name, category, manufacturer)
                        VALUES (:k, :n, :c, :m)
                        ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        category = VALUES(category),
                        manufacturer = VALUES(manufacturer)
                    '''), {
                        'k': str(row['KEY']),
                        'n': str(row['Name'])[:500],
                        'c': str(row['Category']),
                        'm': str(row.get('MANF', ''))
                    })
                    imported += 1
                except Exception as e:
                    if imported < 5:  # Log first few errors only
                        logger.warning(f"Equipment import error: {e}")

            session.commit()
            return {'imported': imported, 'errors': []}

        except Exception as e:
            logger.error(f"Equipment CSV import failed: {e}")
            return {'imported': 0, 'errors': [str(e)]}

    def _import_customers_csv(self) -> dict:
        """Import latest customer CSV file"""
        try:
            customer_files = [f for f in os.listdir(self.csv_base_path)
                            if f.startswith('customer') and f.endswith('.csv')]

            if not customer_files:
                return {'imported': 0, 'errors': ['No customer files found']}

            latest_file = max(customer_files, key=lambda f: os.path.getmtime(os.path.join(self.csv_base_path, f)))
            file_path = os.path.join(self.csv_base_path, latest_file)

            df = pd.read_csv(file_path)
            logger.info(f"Importing {len(df)} customers from {latest_file}")

            session = db.session()
            imported = 0

            for _, row in df.iterrows():
                try:
                    session.execute(text('''
                        INSERT INTO pos_customers (key_field, name, city)
                        VALUES (:k, :n, :c)
                        ON DUPLICATE KEY UPDATE
                        name = VALUES(name),
                        city = VALUES(city)
                    '''), {
                        'k': str(row['KEY']),
                        'n': str(row['NAME'])[:500],
                        'c': str(row['CITY'])
                    })
                    imported += 1
                except Exception as e:
                    if imported < 5:
                        logger.warning(f"Customer import error: {e}")

            session.commit()
            return {'imported': imported, 'errors': []}

        except Exception as e:
            logger.error(f"Customer CSV import failed: {e}")
            return {'imported': 0, 'errors': [str(e)]}

    def _import_transactions_csv(self) -> dict:
        """Import latest transactions CSV file"""
        try:
            transaction_files = [f for f in os.listdir(self.csv_base_path)
                               if f.startswith('transactions') and f.endswith('.csv')]

            if not transaction_files:
                return {'imported': 0, 'errors': ['No transaction files found']}

            latest_file = max(transaction_files, key=lambda f: os.path.getmtime(os.path.join(self.csv_base_path, f)))
            file_path = os.path.join(self.csv_base_path, latest_file)

            df = pd.read_csv(file_path)
            logger.info(f"Importing {len(df)} transactions from {latest_file}")

            session = db.session()
            imported = 0

            for _, row in df.iterrows():
                try:
                    session.execute(text('''
                        INSERT INTO pos_transactions (contract_no, customer_no)
                        VALUES (:c, :cust)
                        ON DUPLICATE KEY UPDATE
                        customer_no = VALUES(customer_no)
                    '''), {
                        'c': str(row['CNTR']),  # YOUR Excel: CNTR = contract number
                        'cust': str(row['CUSN'])  # YOUR Excel: CUSN = customer number
                    })
                    imported += 1
                except Exception as e:
                    if imported < 5:
                        logger.warning(f"Transaction import error: {e}")

            session.commit()
            return {'imported': imported, 'errors': []}

        except Exception as e:
            logger.error(f"Transaction CSV import failed: {e}")
            return {'imported': 0, 'errors': [str(e)]}

    def _import_transitems_csv(self) -> dict:
        """Import latest transitems CSV file with YOUR Excel correlations"""
        try:
            transitems_files = [f for f in os.listdir(self.csv_base_path)
                              if f.startswith('transitems') and f.endswith('.csv')]

            if not transitems_files:
                return {'imported': 0, 'errors': ['No transitems files found']}

            latest_file = max(transitems_files, key=lambda f: os.path.getmtime(os.path.join(self.csv_base_path, f)))
            file_path = os.path.join(self.csv_base_path, latest_file)

            df = pd.read_csv(file_path)
            logger.info(f"Importing {len(df)} transitems from {latest_file}")

            session = db.session()
            imported = 0

            for _, row in df.iterrows():
                try:
                    session.execute(text('''
                        INSERT INTO pos_transaction_items (contract_no, item_no)
                        VALUES (:c, :item)
                        ON DUPLICATE KEY UPDATE
                        item_no = VALUES(item_no)
                    '''), {
                        'c': str(row['CNTR']),  # YOUR Excel: CNTR = contract number
                        'item': str(row['ITEM'])  # YOUR Excel: ITEM correlates to equipment.NUM
                    })
                    imported += 1
                except Exception as e:
                    if imported < 5:
                        logger.warning(f"Transitems import error: {e}")

            session.commit()
            return {'imported': imported, 'errors': []}

        except Exception as e:
            logger.error(f"Transitems CSV import failed: {e}")
            return {'imported': 0, 'errors': [str(e)]}

# Create service instance for scheduler
fixed_pos_import_service = FixedPOSImportService()