# Simple CSV Import - Clean up my mess
# Just import CSV data to raw tables, no overengineering

import pandas as pd
import os
from sqlalchemy import text
from app import db
from datetime import datetime

class SimpleCSVImport:
    """Simple CSV import that actually works"""

    def __init__(self):
        self.csv_path = "/home/tim/RFID3/shared/POR"

    def import_equipment_raw(self, file_path=None, limit=None):
        """Import equipment CSV to raw table - simple and working"""
        try:
            if not file_path:
                file_path = f"{self.csv_path}/equipPOS9.08.25.csv"

            # Read CSV
            df = pd.read_csv(file_path, dtype=str)  # All text for simplicity
            if limit:
                df = df.head(limit)

            print(f"Read {len(df)} equipment records")

            # Simple insert to raw table with app context
            from flask import current_app

            with current_app.app_context():
                session = db.session()
                batch_id = f"equip_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                inserted = 0
                for _, row in df.iterrows():
                    try:
                    session.execute(text("""
                        INSERT INTO equipment_csv_raw
                        (import_batch_id, source_file, equipment_key, equipment_name, location_code, category, manufacturer)
                        VALUES (:batch_id, :file, :key, :name, :loc, :category, :manf)
                    """), {
                        'batch_id': batch_id,
                        'file': os.path.basename(file_path),
                        'key': str(row.get('KEY', '')),
                        'name': str(row.get('Name', '')),
                        'loc': str(row.get('LOC', '')),
                        'category': str(row.get('Category', '')),
                        'manf': str(row.get('MANF', ''))
                    })
                    inserted += 1
                except Exception as e:
                    print(f"Error inserting row: {e}")
                    continue

            session.commit()
            session.close()

            return {'success': True, 'inserted': inserted, 'batch_id': batch_id}

        except Exception as e:
            print(f"Equipment import error: {e}")
            return {'success': False, 'error': str(e)}

    def test_all_raw_imports(self):
        """Test if raw import layer works"""
        result = self.import_equipment_raw(limit=5)
        print(f"Equipment raw import test: {result}")
        return result