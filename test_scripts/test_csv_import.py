#!/usr/bin/env python3
"""
Test script for CSV import service
"""

import sys
import os
sys.path.insert(0, '/home/tim/RFID3')

from app import create_app, db
from app.services.csv_import_service import CSVImportService

def test_equipment_import():
    """Test importing equipment data"""
    
    app = create_app()
    with app.app_context():
        
        print("Starting CSV import test...")
        
        # Create import service
        importer = CSVImportService()
        
        # Test equipment import
        print("Testing equipment data import...")
        result = importer.import_equipment_data()
        
        print(f"Import result: {result}")
        
        if result["success"]:
            # Check what was imported
            from sqlalchemy import text
            
            query = text("SELECT COUNT(*) as count FROM pos_equipment")
            count_result = db.session.execute(query).fetchone()
            print(f"Total equipment records in database: {count_result.count}")
            
            # Show sample data
            sample_query = text("SELECT item_num, name, category, turnover_ytd, sell_price FROM pos_equipment LIMIT 5")
            sample_results = db.session.execute(sample_query).fetchall()
            
            print("\nSample equipment records:")
            for row in sample_results:
                print(f"Item: {row.item_num} | Name: {row.name[:30]} | Category: {row.category} | Turnover YTD: ${row.turnover_ytd}")
        else:
            print(f"Import failed: {result.get('error')}")

if __name__ == "__main__":
    test_equipment_import()