#!/usr/bin/env python3
"""
Focused test for scorecard trends import
"""

import sys
sys.path.append('/home/tim/RFID3')

from app.services.financial_csv_import_service import FinancialCSVImportService

def test_scorecard_import():
    print("Testing Scorecard Trends Import...")
    
    service = FinancialCSVImportService()
    
    # Create import batch
    service.import_batch_id = service.create_import_batch()
    print(f"Created batch ID: {service.import_batch_id}")
    
    # Import scorecard trends
    result = service.import_scorecard_trends()
    
    print(f"Import Success: {result['success']}")
    print(f"Total Records: {result.get('total_records', 0)}")
    print(f"Imported Records: {result.get('imported_records', 0)}")
    print(f"Columns: {result.get('columns_imported', 0)}")
    
    if not result['success']:
        print(f"Error: {result.get('error')}")
    
    # Verify the import
    verification = service.verify_import()
    scorecard_data = verification.get('pos_scorecard_trends', {})
    
    print(f"Records in DB: {scorecard_data.get('record_count', 0)}")
    
    if scorecard_data.get('exists'):
        samples = scorecard_data.get('sample_records', [])
        print(f"Sample records: {len(samples)}")
        for i, sample in enumerate(samples[:2]):
            print(f"  Sample {i+1}:")
            for key, value in list(sample.items())[:8]:
                print(f"    {key}: {value}")

if __name__ == "__main__":
    test_scorecard_import()
