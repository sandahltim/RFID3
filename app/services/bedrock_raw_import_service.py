# Bedrock Raw Import Service - ALL columns from ALL 4 POS CSVs
# Version: 2025-09-23
# Purpose: Import ALL CSV columns to bedrock raw tables with professional naming

import pandas as pd
import os
from datetime import datetime
from sqlalchemy import text
from app import db
from app.services.logger import get_logger

logger = get_logger(__name__)

class BedrockRawImportService:
    """
    Bedrock raw import service for automated Tuesday 8am imports
    Imports ALL columns from all 4 POS CSVs to bedrock raw tables
    Professional naming: raw_pos_[type] with pos_[type]_[field] columns
    """

    def __init__(self):
        self.csv_base_path = "/home/tim/RFID3/shared/POR"

    def import_all_pos_data(self) -> dict:
        """
        Import ALL 4 POS CSVs to bedrock raw tables
        For automated Tuesday 8am scheduler
        """
        batch_id = f"bedrock_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"🏗️ Starting bedrock raw import - batch {batch_id}")

        results = {
            'batch_id': batch_id,
            'equipment': self.import_equipment_to_bedrock(batch_id),
            'customers': self.import_customers_to_bedrock(batch_id),
            'transactions': self.import_transactions_to_bedrock(batch_id),
            'transitems': self.import_transitems_to_bedrock(batch_id),
            'total_imported': 0
        }

        # Calculate total
        total = sum(r.get('imported', 0) for r in results.values() if isinstance(r, dict))
        results['total_imported'] = total

        logger.info(f"🏁 Bedrock import complete: {total} total records")
        return results

    def import_equipment_to_bedrock(self, batch_id: str) -> dict:
        """Import ALL 171 equipment columns to raw_pos_equipment with exact column mapping"""
        try:
            # Find latest equipPOS file
            files = [f for f in os.listdir(self.csv_base_path)
                    if f.startswith('equipPOS') and f.endswith('.csv')]
            if not files:
                return {'imported': 0, 'error': 'No equipPOS files found'}

            latest = max(files, key=lambda f: os.path.getmtime(os.path.join(self.csv_base_path, f)))
            file_path = os.path.join(self.csv_base_path, latest)

            # Read CSV with ALL columns
            df = pd.read_csv(file_path, dtype=str)
            logger.info(f"Equipment: {len(df)} records, {len(df.columns)} columns from {latest}")

            # Get actual table columns from database
            session = db.session()
            result = session.execute(text("SHOW COLUMNS FROM raw_pos_equipment"))
            actual_columns = [row[0] for row in result.fetchall()
                            if row[0] not in ['id', 'import_batch_id', 'import_timestamp']]

            # Clear table
            session.execute(text("TRUNCATE TABLE raw_pos_equipment"))

            # Verify column count matches
            csv_columns = list(df.columns)
            if len(csv_columns) != len(actual_columns):
                return {'imported': 0, 'error': f"Column count mismatch: CSV has {len(csv_columns)}, table has {len(actual_columns)}"}

            # Import records with exact column mapping
            imported = 0
            for _, row in df.iterrows():
                try:
                    values = {'import_batch_id': batch_id}
                    for csv_col, table_col in zip(csv_columns, actual_columns):
                        values[table_col] = str(row[csv_col])[:500] if pd.notna(row[csv_col]) else ''

                    # Build SQL with exact column names
                    insert_cols = ', '.join(actual_columns)
                    insert_vals = ', '.join([f':{col}' for col in actual_columns])
                    sql = f"INSERT INTO raw_pos_equipment (import_batch_id, {insert_cols}) VALUES (:import_batch_id, {insert_vals})"

                    session.execute(text(sql), values)
                    imported += 1

                    if imported % 5000 == 0:
                        session.commit()
                        logger.info(f"Equipment: {imported}/{len(df)}")

                except Exception as e:
                    if imported < 5:
                        logger.warning(f"Equipment error: {e}")

            session.commit()
            logger.info(f"✅ Equipment bedrock: {imported} records imported")
            return {'imported': imported}

        except Exception as e:
            logger.error(f"Equipment bedrock failed: {e}")
            return {'imported': 0, 'error': str(e)}

    def import_customers_to_bedrock(self, batch_id: str) -> dict:
        """Import ALL 108 customer columns to raw_pos_customers"""
        try:
            files = [f for f in os.listdir(self.csv_base_path)
                    if f.startswith('customer') and f.endswith('.csv')]
            if not files:
                return {'imported': 0, 'error': 'No customer files found'}

            latest = max(files, key=lambda f: os.path.getmtime(os.path.join(self.csv_base_path, f)))
            file_path = os.path.join(self.csv_base_path, latest)

            df = pd.read_csv(file_path, dtype=str)
            logger.info(f"Customers: {len(df)} records, {len(df.columns)} columns from {latest}")

            session = db.session()
            imported = 0

            for _, row in df.iterrows():
                try:
                    values = {'import_batch_id': batch_id}
                    columns = ['import_batch_id']

                    for csv_col in df.columns:
                        db_col = f'pos_customers_{csv_col.lower()}'
                        columns.append(db_col)
                        values[db_col] = str(row[csv_col])[:500] if pd.notna(row[csv_col]) else ''

                    columns_str = ', '.join(columns)
                    placeholders = ', '.join([f':{col}' for col in columns])

                    session.execute(text(f'''
                        INSERT INTO raw_pos_customers ({columns_str})
                        VALUES ({placeholders})
                    '''), values)

                    imported += 1

                    if imported % 10000 == 0:
                        session.commit()
                        logger.info(f"Customers: {imported}/{len(df)}")

                except Exception as e:
                    if imported < 5:
                        logger.warning(f"Customer error: {e}")

            session.commit()
            logger.info(f"✅ Customers bedrock: {imported} records imported")
            return {'imported': imported}

        except Exception as e:
            logger.error(f"Customer bedrock failed: {e}")
            return {'imported': 0, 'error': str(e)}

    def import_transactions_to_bedrock(self, batch_id: str) -> dict:
        """Import ALL 119 transaction columns to raw_pos_transactions"""
        try:
            files = [f for f in os.listdir(self.csv_base_path)
                    if f.startswith('transactions') and f.endswith('.csv')]
            if not files:
                return {'imported': 0, 'error': 'No transaction files found'}

            latest = max(files, key=lambda f: os.path.getmtime(os.path.join(self.csv_base_path, f)))
            file_path = os.path.join(self.csv_base_path, latest)

            df = pd.read_csv(file_path, dtype=str)
            logger.info(f"Transactions: {len(df)} records, {len(df.columns)} columns from {latest}")

            session = db.session()
            imported = 0

            for _, row in df.iterrows():
                try:
                    values = {'import_batch_id': batch_id}
                    columns = ['import_batch_id']

                    for csv_col in df.columns:
                        db_col = f'pos_transactions_{csv_col.lower()}'
                        columns.append(db_col)
                        values[db_col] = str(row[csv_col])[:500] if pd.notna(row[csv_col]) else ''

                    columns_str = ', '.join(columns)
                    placeholders = ', '.join([f':{col}' for col in columns])

                    session.execute(text(f'''
                        INSERT INTO raw_pos_transactions ({columns_str})
                        VALUES ({placeholders})
                    '''), values)

                    imported += 1

                    if imported % 15000 == 0:
                        session.commit()
                        logger.info(f"Transactions: {imported}/{len(df)}")

                except Exception as e:
                    if imported < 5:
                        logger.warning(f"Transaction error: {e}")

            session.commit()
            logger.info(f"✅ Transactions bedrock: {imported} records imported")
            return {'imported': imported}

        except Exception as e:
            logger.error(f"Transaction bedrock failed: {e}")
            return {'imported': 0, 'error': str(e)}

    def import_transitems_to_bedrock(self, batch_id: str) -> dict:
        """Import ALL 45 transitems columns to raw_pos_transitems with YOUR Excel correlations"""
        try:
            files = [f for f in os.listdir(self.csv_base_path)
                    if f.startswith('transitems') and f.endswith('.csv')]
            if not files:
                return {'imported': 0, 'error': 'No transitems files found'}

            latest = max(files, key=lambda f: os.path.getmtime(os.path.join(self.csv_base_path, f)))
            file_path = os.path.join(self.csv_base_path, latest)

            df = pd.read_csv(file_path, dtype=str)
            logger.info(f"Transitems: {len(df)} records, {len(df.columns)} columns from {latest}")

            session = db.session()
            imported = 0

            for _, row in df.iterrows():
                try:
                    values = {'import_batch_id': batch_id}
                    columns = ['import_batch_id']

                    for csv_col in df.columns:
                        db_col = f'pos_transitems_{csv_col.lower()}'
                        columns.append(db_col)
                        values[db_col] = str(row[csv_col])[:500] if pd.notna(row[csv_col]) else ''

                    columns_str = ', '.join(columns)
                    placeholders = ', '.join([f':{col}' for col in columns])

                    session.execute(text(f'''
                        INSERT INTO raw_pos_transitems ({columns_str})
                        VALUES ({placeholders})
                    '''), values)

                    imported += 1

                    if imported % 20000 == 0:
                        session.commit()
                        logger.info(f"Transitems: {imported}/{len(df)}")

                except Exception as e:
                    if imported < 5:
                        logger.warning(f"Transitems error: {e}")

            session.commit()
            logger.info(f"✅ Transitems bedrock: {imported} records imported")
            return {'imported': imported}

        except Exception as e:
            logger.error(f"Transitems bedrock failed: {e}")
            return {'imported': 0, 'error': str(e)}

# Service instance for scheduler and manual imports
bedrock_raw_import_service = BedrockRawImportService()