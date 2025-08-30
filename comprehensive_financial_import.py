#!/usr/bin/env python3
"""
Comprehensive Financial Import System
Complete solution for importing all POS and financial data files
Includes both transactional and financial analytics data
"""

import sys
import os
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.financial_csv_import_service import FinancialCSVImportService
from app.services.csv_import_service import CSVImportService
from app.services.logger import get_logger
from sqlalchemy import text, create_engine
from config import DB_CONFIG

logger = get_logger(__name__)

class ComprehensiveFinancialImporter:
    """Complete import system for all CSV data files"""
    
    def __init__(self):
        self.app = create_app()
        self.financial_service = FinancialCSVImportService()
        self.csv_service = CSVImportService()
        self.database_url = (
            f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
            f"{DB_CONFIG['host']}/{DB_CONFIG['database']}"
        )
        self.engine = create_engine(self.database_url, pool_pre_ping=True)
        
        self.import_summary = {
            'start_time': datetime.now(),
            'financial_files': {},
            'transactional_files': {},
            'errors': [],
            'warnings': []
        }
    
    def analyze_all_csv_files(self):
        """Analyze all CSV files in the POR directory"""
        csv_dir = Path("/home/tim/RFID3/shared/POR")
        
        print("\n📊 CSV FILE ANALYSIS")
        print("=" * 70)
        
        csv_files = list(csv_dir.glob("*.csv"))
        print(f"Found {len(csv_files)} CSV files in {csv_dir}")
        
        file_info = {}
        for csv_file in csv_files:
            if 'RFIDpro' in csv_file.name:
                continue  # Skip RFID files
                
            file_size = csv_file.stat().st_size / (1024 * 1024)  # MB
            
            # Quick analysis of structure
            try:
                df_sample = pd.read_csv(csv_file, nrows=5)
                row_count_estimate = sum(1 for _ in open(csv_file)) - 1  # Subtract header
                
                file_info[csv_file.name] = {
                    'size_mb': round(file_size, 2),
                    'columns': len(df_sample.columns),
                    'rows_estimate': row_count_estimate,
                    'sample_columns': list(df_sample.columns)[:10]
                }
                
                # Categorize file
                if 'customer' in csv_file.name.lower():
                    category = 'Customer Data'
                elif 'equip' in csv_file.name.lower():
                    category = 'Equipment/Inventory'
                elif 'transaction' in csv_file.name.lower():
                    category = 'Transactions'
                elif 'transitem' in csv_file.name.lower():
                    category = 'Transaction Items'
                elif 'scorecard' in csv_file.name.lower():
                    category = 'Business Metrics'
                elif 'payroll' in csv_file.name.lower():
                    category = 'Payroll Analytics'
                elif 'pl' in csv_file.name.lower():
                    category = 'Profit & Loss'
                else:
                    category = 'Other'
                
                file_info[csv_file.name]['category'] = category
                
            except Exception as e:
                file_info[csv_file.name] = {
                    'size_mb': round(file_size, 2),
                    'error': str(e),
                    'category': 'Unknown'
                }
        
        # Display analysis
        categories = {}
        for fname, info in file_info.items():
            cat = info.get('category', 'Unknown')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((fname, info))
        
        for category, files in sorted(categories.items()):
            print(f"\n📁 {category}:")
            for fname, info in files:
                if 'error' not in info:
                    print(f"   - {fname}")
                    print(f"     Size: {info['size_mb']} MB | "
                          f"Rows: ~{info.get('rows_estimate', 0):,} | "
                          f"Columns: {info.get('columns', 0)}")
                else:
                    print(f"   - {fname} (Error reading file)")
        
        return file_info
    
    def import_financial_files(self):
        """Import all financial data files"""
        print("\n💰 IMPORTING FINANCIAL DATA")
        print("=" * 70)
        
        with self.app.app_context():
            results = self.financial_service.import_all_financial_files()
            self.import_summary['financial_files'] = results
            
            # Display results
            if results.get('overall_success'):
                print("✅ Financial data import completed successfully")
            else:
                print("⚠️  Financial data import completed with errors")
            
            print(f"   - Files: {results.get('files_processed')}")
            print(f"   - Records: {results.get('total_records_imported'):,}/{results.get('total_records_processed'):,}")
            
            return results
    
    def import_transactional_files(self):
        """Import equipment and transaction files"""
        print("\n📦 IMPORTING TRANSACTIONAL DATA")
        print("=" * 70)
        
        with self.app.app_context():
            results = {}
            
            # Import equipment data
            print("\n🔧 Importing equipment data...")
            try:
                equip_result = self.csv_service.import_equipment_data()
                results['equipment'] = equip_result
                if equip_result.get('success'):
                    print(f"✅ Equipment: {equip_result.get('imported_records'):,} records")
                else:
                    print(f"❌ Equipment: {equip_result.get('error')}")
            except Exception as e:
                print(f"❌ Equipment import failed: {e}")
                results['equipment'] = {'success': False, 'error': str(e)}
            
            # Import transactions if method exists
            print("\n💳 Importing transactions...")
            try:
                # Check if transactions import method exists
                if hasattr(self.csv_service, 'import_transactions'):
                    trans_result = self.csv_service.import_transactions()
                    results['transactions'] = trans_result
                    if trans_result.get('success'):
                        print(f"✅ Transactions: {trans_result.get('imported_records'):,} records")
                else:
                    print("⚠️  Transactions import not implemented")
                    results['transactions'] = {'success': False, 'error': 'Not implemented'}
            except Exception as e:
                print(f"❌ Transactions import failed: {e}")
                results['transactions'] = {'success': False, 'error': str(e)}
            
            self.import_summary['transactional_files'] = results
            return results
    
    def create_data_correlations(self):
        """Create correlations between different data sources"""
        print("\n🔗 CREATING DATA CORRELATIONS")
        print("=" * 70)
        
        with self.engine.connect() as conn:
            correlations = {}
            
            # 1. Customer-Transaction Correlation
            try:
                result = conn.execute(text("""
                    SELECT COUNT(DISTINCT c.cnum) as customers_with_transactions
                    FROM pos_customers c
                    WHERE EXISTS (
                        SELECT 1 FROM pos_transactions t 
                        WHERE t.customer_id = c.cnum
                    )
                """))
                correlations['customer_transactions'] = result.fetchone()[0]
                print(f"✅ Customers with transactions: {correlations['customer_transactions']:,}")
            except:
                print("⚠️  Customer-Transaction correlation not available")
            
            # 2. Equipment-Revenue Correlation
            try:
                result = conn.execute(text("""
                    SELECT COUNT(DISTINCT item_num) as equipment_items
                    FROM pos_equipment
                    WHERE rental_rate > 0
                """))
                correlations['revenue_generating_equipment'] = result.fetchone()[0]
                print(f"✅ Revenue-generating equipment: {correlations['revenue_generating_equipment']:,}")
            except:
                print("⚠️  Equipment-Revenue correlation not available")
            
            # 3. Store Performance Correlation
            try:
                result = conn.execute(text("""
                    SELECT 
                        COUNT(DISTINCT CASE WHEN revenue_3607 > 0 THEN 1 END) as store_3607,
                        COUNT(DISTINCT CASE WHEN revenue_6800 > 0 THEN 1 END) as store_6800,
                        COUNT(DISTINCT CASE WHEN revenue_728 > 0 THEN 1 END) as store_728,
                        COUNT(DISTINCT CASE WHEN revenue_8101 > 0 THEN 1 END) as store_8101
                    FROM pos_scorecard_trends
                    WHERE week_ending_sunday IS NOT NULL
                """))
                row = result.fetchone()
                if row:
                    print(f"✅ Store data availability:")
                    print(f"   - Store 3607: {row[0]} weeks")
                    print(f"   - Store 6800: {row[1]} weeks")
                    print(f"   - Store 728: {row[2]} weeks")
                    print(f"   - Store 8101: {row[3]} weeks")
            except:
                print("⚠️  Store performance correlation not available")
            
            return correlations
    
    def generate_executive_summary(self):
        """Generate executive summary of imported data"""
        print("\n📊 EXECUTIVE SUMMARY")
        print("=" * 70)
        
        with self.engine.connect() as conn:
            summary = {}
            
            # Get key metrics
            metrics = [
                ("Total Customers", "SELECT COUNT(*) FROM pos_customers"),
                ("Active Equipment Items", "SELECT COUNT(*) FROM pos_equipment WHERE status = 'Active'"),
                ("Weeks of Scorecard Data", "SELECT COUNT(DISTINCT week_ending_sunday) FROM pos_scorecard_trends"),
                ("Payroll Periods", "SELECT COUNT(DISTINCT week_ending) FROM pos_payroll_trends"),
                ("P&L Accounts", "SELECT COUNT(DISTINCT account_line) FROM pos_profit_loss")
            ]
            
            for metric_name, query in metrics:
                try:
                    result = conn.execute(text(query))
                    value = result.fetchone()[0]
                    summary[metric_name] = value
                    print(f"📈 {metric_name}: {value:,}")
                except:
                    print(f"⚠️  {metric_name}: Not available")
            
            # Calculate revenue trends if available
            try:
                result = conn.execute(text("""
                    SELECT 
                        MIN(week_ending_sunday) as earliest_date,
                        MAX(week_ending_sunday) as latest_date,
                        AVG(total_weekly_revenue) as avg_weekly_revenue,
                        MAX(total_weekly_revenue) as max_weekly_revenue
                    FROM pos_scorecard_trends
                    WHERE total_weekly_revenue IS NOT NULL
                """))
                row = result.fetchone()
                if row and row[0]:
                    print(f"\n💰 Revenue Analysis:")
                    print(f"   - Period: {row[0]} to {row[1]}")
                    print(f"   - Average Weekly: ${row[2]:,.2f}" if row[2] else "   - Average Weekly: N/A")
                    print(f"   - Peak Weekly: ${row[3]:,.2f}" if row[3] else "   - Peak Weekly: N/A")
            except:
                pass
            
            return summary
    
    def run_complete_import(self):
        """Run the complete import process"""
        print("\n" + "=" * 70)
        print("    COMPREHENSIVE FINANCIAL DATA IMPORT SYSTEM")
        print("=" * 70)
        print(f"Started: {self.import_summary['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Analyze files
        print("\n[Step 1/5] Analyzing CSV files...")
        file_analysis = self.analyze_all_csv_files()
        
        # Step 2: Import financial files
        print("\n[Step 2/5] Importing financial data...")
        financial_results = self.import_financial_files()
        
        # Step 3: Import transactional files
        print("\n[Step 3/5] Importing transactional data...")
        transactional_results = self.import_transactional_files()
        
        # Step 4: Create correlations
        print("\n[Step 4/5] Creating data correlations...")
        correlations = self.create_data_correlations()
        
        # Step 5: Generate summary
        print("\n[Step 5/5] Generating executive summary...")
        executive_summary = self.generate_executive_summary()
        
        # Final report
        print("\n" + "=" * 70)
        print("    IMPORT COMPLETE")
        print("=" * 70)
        
        end_time = datetime.now()
        duration = (end_time - self.import_summary['start_time']).total_seconds()
        
        print(f"\n⏱️  Duration: {duration:.1f} seconds")
        print(f"📁 Files Processed: {len(file_analysis)}")
        
        # Overall success
        financial_success = financial_results.get('overall_success', False)
        trans_success = any(r.get('success', False) for r in transactional_results.values())
        
        if financial_success and trans_success:
            print("\n🎉 ALL IMPORTS COMPLETED SUCCESSFULLY!")
        elif financial_success or trans_success:
            print("\n⚠️  PARTIAL SUCCESS - Some imports completed")
        else:
            print("\n❌ IMPORT FAILED - Please check errors")
        
        print("\n📝 Next Steps:")
        print("1. Review imported data using the analytics dashboard")
        print("2. Set up automated weekly imports via cron")
        print("3. Configure data retention policies")
        print("4. Enable real-time analytics endpoints")
        
        return {
            'success': financial_success or trans_success,
            'duration': duration,
            'files_analyzed': len(file_analysis),
            'financial_results': financial_results,
            'transactional_results': transactional_results,
            'correlations': correlations,
            'executive_summary': executive_summary
        }

def main():
    """Main execution function"""
    importer = ComprehensiveFinancialImporter()
    
    try:
        results = importer.run_complete_import()
        return 0 if results['success'] else 1
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        logger.error(f"Import failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())