#!/usr/bin/env python3
"""
Create POS correlation tables in the database.
Run this script to set up the POS integration tables.
"""

import sys
import os

# Set environment to skip API authentication for table creation
os.environ['SKIP_API_AUTH'] = '1'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import DB_CONFIG

def create_pos_tables_direct():
    """Create POS tables directly without full app initialization."""
    
    # Create minimal Flask app
    app = Flask(__name__)
    
    # Configure database
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}/{DB_CONFIG['database']}?charset={DB_CONFIG['charset']}&collation={DB_CONFIG['collation']}"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize SQLAlchemy
    db = SQLAlchemy(app)
    
    with app.app_context():
        try:
            # Import models after app context is set
            from app.models.pos_models import (
                POSTransaction, POSTransactionItem, POSCustomer,
                POSRFIDCorrelation, POSInventoryDiscrepancy, POSAnalytics,
                POSImportLog
            )
            
            print("Creating POS tables...")
            
            # Create tables
            tables_to_create = [
                POSTransaction.__table__,
                POSTransactionItem.__table__,
                POSCustomer.__table__,
                POSRFIDCorrelation.__table__,
                POSInventoryDiscrepancy.__table__,
                POSAnalytics.__table__,
                POSImportLog.__table__
            ]
            
            for table in tables_to_create:
                try:
                    table.create(db.engine, checkfirst=True)
                    print(f"  ✓ Created/verified table: {table.name}")
                except Exception as e:
                    print(f"  ✗ Error with table {table.name}: {str(e)}")
            
            print("\n✅ POS tables creation completed!")
            print("\n📋 Next steps:")
            print("1. Start the application: python3 run.py")
            print("2. Visit POS Dashboard: http://localhost:6800/api/pos/dashboard")
            print("3. Click 'Import POS Data' to import CSV files from /shared/POR/")
            print("4. Click 'Run Correlation' to correlate POS items with RFID inventory")
            print("\n📊 Available POS data files:")
            print("  - transactions8.26.25.csv")
            print("  - transitems8.26.25.csv")
            print("  - customer8.26.25.csv")
            
        except Exception as e:
            print(f"❌ Error creating tables: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    create_pos_tables_direct()
