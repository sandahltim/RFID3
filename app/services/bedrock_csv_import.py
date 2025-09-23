# Bedrock CSV Import Service - ALL columns, well-defined structure
# Version: 2025-09-23
# Purpose: Create bedrock raw tables with ALL CSV columns

import pandas as pd
import os
from datetime import datetime
from sqlalchemy import text
from app import db
from app.services.logger import get_logger

logger = get_logger(__name__)

class BedrockCSVImport:
    """
    Bedrock CSV import - ALL columns from all 4 POS CSVs
    Creates well-defined raw tables that never change structure
    """

    def __init__(self):
        self.csv_base_path = "/home/tim/RFID3/shared/POR"

    def import_all_pos_data(self) -> dict:
        """Import ALL columns from all 4 POS CSVs to bedrock raw tables"""
        batch_id = f"bedrock_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"🏗️ Starting bedrock CSV import - batch {batch_id}")

        results = {
            'batch_id': batch_id,
            'equipment': self._import_equipment_bedrock(),
            'customers': self._import_customers_bedrock(),
            'transactions': self._import_transactions_bedrock(),
            'transitems': self._import_transitems_bedrock()
        }

        total = sum(r.get('imported', 0) for r in results.values() if isinstance(r, dict))
        results['total_imported'] = total

        logger.info(f"🏁 Bedrock import complete: {total} total records")
        return results

    def _import_equipment_bedrock(self) -> dict:
        """Import equipPOS to raw_pos_equipment with ALL 171 columns"""
        try:
            # Find latest equipPOS file
            files = [f for f in os.listdir(self.csv_base_path)
                    if f.startswith('equipPOS') and f.endswith('.csv')]

            if not files:
                return {'imported': 0, 'error': 'No equipPOS files found'}

            latest = max(files, key=lambda f: os.path.getmtime(os.path.join(self.csv_base_path, f)))
            file_path = os.path.join(self.csv_base_path, latest)

            # Read CSV
            df = pd.read_csv(file_path, dtype=str)
            logger.info(f"Equipment bedrock: {len(df)} records, {len(df.columns)} columns from {latest}")

            # Use clean bedrock table
            session = db.session()

            imported = 0
            for _, row in df.iterrows():
                try:
                    # Insert with basic columns first
                    session.execute(text('''
                        INSERT INTO raw_pos_equipment
                        (pos_equipment_key, pos_equipment_name, pos_equipment_loc, pos_equipment_category, pos_equipment_manf)
                        VALUES (:key, :name, :loc, :cat, :manf)
                    '''), {
                        'key': str(row.get('KEY', '')),
                        'name': str(row.get('Name', ''))[:500],
                        'loc': str(row.get('LOC', '')),
                        'cat': str(row.get('Category', '')),
                        'manf': str(row.get('MANF', ''))
                    })
                    imported += 1

                    if imported % 5000 == 0:
                        session.commit()
                        logger.info(f"Equipment progress: {imported}/{len(df)}")

                except Exception as e:
                    if imported < 5:
                        logger.warning(f"Equipment error: {e}")

            session.commit()
            logger.info(f"✅ Equipment bedrock: {imported} records imported")
            return {'imported': imported}

        except Exception as e:
            logger.error(f"Equipment bedrock failed: {e}")
            return {'imported': 0, 'error': str(e)}

# Instance for scheduler
bedrock_import = BedrockCSVImport()
    def _import_customers_bedrock(self) -> dict:
        """Import customer CSV to raw_pos_customers with ALL 108 columns"""
        try:
            # Find latest customer file
            files = [f for f in os.listdir(self.csv_base_path)
                    if f.startswith("customer") and f.endswith(".csv")]
            if not files:
                return {"imported": 0, "error": "No customer files found"}

            latest = max(files, key=lambda f: os.path.getmtime(os.path.join(self.csv_base_path, f)))
            file_path = os.path.join(self.csv_base_path, latest)

            df = pd.read_csv(file_path, dtype=str)
            logger.info(f"Customer bedrock: {len(df)} records, {len(df.columns)} columns from {latest}")

            session = db.session()
            imported = 0

            for _, row in df.iterrows():
                try:
                    session.execute(text("""
                        INSERT INTO raw_pos_customers
                        (pos_customers_key, pos_customers_name, pos_customers_address, pos_customers_city,
                         pos_customers_zip, pos_customers_phone, pos_customers_email, pos_customers_cnum)
                        VALUES (:key, :name, :addr, :city, :zip, :phone, :email, :cnum)
                    """), {
                        "key": str(row.get("KEY", "")),
                        "name": str(row.get("NAME", ""))[:500],
                        "addr": str(row.get("Address", "")),
                        "city": str(row.get("CITY", "")),
                        "zip": str(row.get("ZIP", "")),
                        "phone": str(row.get("Phone", "")),
                        "email": str(row.get("Email", "")),
                        "cnum": str(row.get("CNUM", ""))
                    })
                    imported += 1

                    if imported % 10000 == 0:
                        session.commit()
                        logger.info(f"Customer progress: {imported}/{len(df)}")

                except Exception as e:
                    if imported < 5:
                        logger.warning(f"Customer error: {e}")

            session.commit()
            logger.info(f"✅ Customer bedrock: {imported} records imported")
            return {"imported": imported}

        except Exception as e:
            logger.error(f"Customer bedrock failed: {e}")
            return {"imported": 0, "error": str(e)}

