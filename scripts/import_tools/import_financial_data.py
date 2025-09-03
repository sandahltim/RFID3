#!/usr/bin/env python3
"""
Financial Data Import Execution Script
Imports all financial CSV files into the database for executive analytics
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.financial_csv_import_service import FinancialCSVImportService
from app.services.logger import get_logger

logger = get_logger(__name__)

def ensure_import_batches_table():
    """Ensure the import_batches table exists"""
    from sqlalchemy import text
    from config import DB_CONFIG
    from sqlalchemy import create_engine
    
    database_url = (
        f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}/{DB_CONFIG['database']}"
    )
    engine = create_engine(database_url, pool_pre_ping=True)
    
    with engine.connect() as conn:
        try:
            # Create import_batches table if it doesn't exist
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS import_batches (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    import_type VARCHAR(50),
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP NULL,
                    status VARCHAR(20),
                    records_processed INT DEFAULT 0,
                    records_imported INT DEFAULT 0,
                    errors TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_import_type (import_type),
                    INDEX idx_status (status),
                    INDEX idx_started (started_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """))
            conn.commit()
            logger.info("Import batches table ready")
        except Exception as e:
            logger.error(f"Failed to create import_batches table: {e}")
            raise

def check_csv_files():
    """Check if all required CSV files exist"""
    csv_dir = Path("/home/tim/RFID3/shared/POR")
    
    required_patterns = [
        "customer*.csv",
        "ScorecardTrends*.csv",
        "PayrollTrends*.csv",
        "PL*.csv"
    ]
    
    found_files = {}
    missing_files = []
    
    print("\n📁 Checking for CSV files...")
    print("=" * 60)
    
    for pattern in required_patterns:
        files = list(csv_dir.glob(pattern))
        if files:
            # Get the newest file
            newest = max(files, key=lambda f: f.stat().st_mtime)
            found_files[pattern] = newest
            file_size = newest.stat().st_size / (1024 * 1024)  # Convert to MB
            print(f"✅ Found: {newest.name} ({file_size:.2f} MB)")
        else:
            missing_files.append(pattern)
            print(f"❌ Missing: {pattern}")
    
    if missing_files:
        print(f"\n⚠️  Warning: {len(missing_files)} file types missing")
        response = input("Continue with available files? (y/n): ")
        if response.lower() != 'y':
            print("Import cancelled.")
            return False, found_files
    
    return True, found_files

def main():
    """Main execution function"""
    print("\n" + "=" * 60)
    print("    FINANCIAL DATA IMPORT SYSTEM")
    print("=" * 60)
    print(f"Import started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check for CSV files
    proceed, found_files = check_csv_files()
    if not proceed:
        return
    
    # Initialize Flask app context
    print("\n🔧 Initializing application...")
    app = create_app()
    
    with app.app_context():
        try:
            # Ensure database tables exist
            print("📊 Preparing database...")
            ensure_import_batches_table()
            
            # Initialize import service
            print("🚀 Starting import service...")
            import_service = FinancialCSVImportService()
            
            # Perform imports
            print("\n" + "=" * 60)
            print("    IMPORTING DATA")
            print("=" * 60)
            
            results = import_service.import_all_financial_files()
            
            # Display results
            print("\n" + "=" * 60)
            print("    IMPORT RESULTS")
            print("=" * 60)
            
            print(f"\n📋 Batch ID: {results.get('batch_id')}")
            print(f"✅ Overall Success: {results.get('overall_success')}")
            print(f"📁 Files Processed: {results.get('files_processed')}")
            print(f"📊 Records Processed: {results.get('total_records_processed'):,}")
            print(f"✅ Records Imported: {results.get('total_records_imported'):,}")
            
            # Display individual file results
            print("\n📈 Individual File Results:")
            print("-" * 40)
            for file_type, result in results.get('results', {}).items():
                status = "✅" if result.get('success') else "❌"
                print(f"\n{status} {file_type.upper()}:")
                if result.get('success'):
                    print(f"   - Records: {result.get('imported_records'):,}/{result.get('total_records'):,}")
                    if 'columns_imported' in result:
                        print(f"   - Columns: {result.get('columns_imported')}")
                    if 'file_path' in result:
                        print(f"   - File: {Path(result['file_path']).name}")
                else:
                    print(f"   - Error: {result.get('error')}")
            
            # Display errors if any
            if results.get('errors'):
                print("\n⚠️  Errors encountered:")
                for error in results['errors'][:5]:  # Show first 5 errors
                    print(f"   - {error}")
            
            # Display warnings summary
            if results.get('warnings'):
                print(f"\n⚠️  Warnings: {len(results.get('warnings', []))} (showing first 5)")
                for warning in results.get('warnings', [])[:5]:
                    print(f"   - {warning}")
            
            # Verify import
            print("\n" + "=" * 60)
            print("    VERIFICATION")
            print("=" * 60)
            
            print("\n🔍 Verifying imported data...")
            verification = import_service.verify_import()
            
            print("\n📊 Table Record Counts:")
            print("-" * 40)
            for table, info in verification.items():
                if info.get('exists'):
                    print(f"✅ {table}: {info['record_count']:,} records")
                else:
                    print(f"❌ {table}: Not found or error")
            
            # Final summary
            print("\n" + "=" * 60)
            if results.get('overall_success'):
                print("🎉 IMPORT COMPLETED SUCCESSFULLY!")
            else:
                print("⚠️  IMPORT COMPLETED WITH ERRORS")
            print("=" * 60)
            print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Provide next steps
            print("\n📝 Next Steps:")
            print("1. Review the imported data in the database")
            print("2. Check the import_batches table for batch details")
            print("3. Use the financial analytics endpoints to access the data")
            print("4. Set up automated weekly imports if needed")
            
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR: {e}")
            logger.error(f"Import failed with critical error: {e}", exc_info=True)
            return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)