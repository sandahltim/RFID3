#!/usr/bin/env python3
"""
Comprehensive CSV Import System for All POS Files
Imports ALL columns from ALL non-RFIDpro CSV files for Tuesday 8am automation

Files to import:
- customer8.26.25.csv (Customer data)
- equip8.26.25.csv (Equipment data) 
- transactions8.26.25.csv (Transaction data)
- transitems8.26.25.csv (Transaction items data)
- ScorecardTrends8.26.25.csv (Business metrics/KPIs)
- PayrollTrends8.26.25.csv (Payroll analytics)
- PL8.28.25.csv (P&L/Financial data)
"""

from app import create_app, db
from sqlalchemy import text
import pandas as pd
import sys
from datetime import datetime
import os
import re
from pathlib import Path

class ComprehensiveCSVImporter:
    def __init__(self):
        self.app = create_app()
        self.csv_configs = {
            'customers': {
                'file_pattern': r'customer\d+\.\d+\.\d+\.csv',
                'table_name': 'pos_customers',
                'primary_key': 'cnum'
            },
            'equipment': {
                'file_pattern': r'equip\d+\.\d+\.\d+\.csv', 
                'table_name': 'pos_equipment',
                'primary_key': 'item_num'
            },
            'transactions': {
                'file_pattern': r'transactions\d+\.\d+\.\d+\.csv',
                'table_name': 'pos_transactions', 
                'primary_key': 'contract_no'
            },
            'transitems': {
                'file_pattern': r'transitems\d+\.\d+\.\d+\.csv',
                'table_name': 'pos_transaction_items',
                'primary_key': ['contract_no', 'line_number']
            },
            'scorecard': {
                'file_pattern': r'ScorecardTrends\d+\.\d+\.\d+\.csv',
                'table_name': 'pos_scorecard_trends',
                'primary_key': 'week_ending'
            },
            'payroll': {
                'file_pattern': r'PayrollTrends\d+\.\d+\.\d+\.csv',
                'table_name': 'pos_payroll_trends', 
                'primary_key': 'week_ending'
            },
            'pl': {
                'file_pattern': r'PL\d+\.\d+\.\d+\.csv',
                'table_name': 'pos_profit_loss',
                'primary_key': 'account_line'
            }
        }
        
    def analyze_csv_structures(self, csv_directory: str = 'shared/POR'):
        """Analyze all CSV files and their column structures"""
        
        with self.app.app_context():
            print("🔍 Comprehensive CSV Structure Analysis")
            print("=" * 60)
            
            csv_dir = Path(csv_directory)
            analyses = {}
            
            for category, config in self.csv_configs.items():
                print(f"\n📋 {category.upper()} FILES:")
                
                # Find matching files
                matching_files = []
                for csv_file in csv_dir.glob('*.csv'):
                    if re.match(config['file_pattern'], csv_file.name) and 'RFIDpro' not in csv_file.name:
                        matching_files.append(csv_file)
                
                if not matching_files:
                    print(f"   ⚠️  No files found matching pattern: {config['file_pattern']}")
                    continue
                
                for csv_file in matching_files:
                    print(f"   📄 {csv_file.name}")
                    
                    try:
                        # Read first few rows to analyze structure
                        df = pd.read_csv(csv_file, nrows=5, dtype=str)
                        
                        # Remove empty columns for ScorecardTrends and similar files
                        if 'scorecard' in category.lower() or len(df.columns) > 1000:
                            # Keep only columns that have meaningful names or data
                            meaningful_cols = []
                            for col in df.columns:
                                # Keep if has a real name or has actual data
                                if not str(col).startswith('Unnamed:') and not str(col).startswith('Column') and pd.notna(col):
                                    if df[col].dropna().nunique() > 0:  # Has actual data
                                        meaningful_cols.append(col)
                                elif len(meaningful_cols) < 50:  # Keep first 50 even if named poorly
                                    meaningful_cols.append(col)
                            df = df[meaningful_cols]
                        
                        analysis = {
                            'file': csv_file.name,
                            'table_name': config['table_name'],
                            'primary_key': config['primary_key'],
                            'columns': list(df.columns),
                            'row_count_sample': len(df),
                            'data_types': self._infer_column_types(df)
                        }
                        
                        analyses[category] = analysis
                        
                        print(f"      Columns ({len(df.columns)}): {', '.join(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}")
                        print(f"      Target table: {config['table_name']}")
                        print(f"      Primary key: {config['primary_key']}")
                        
                    except Exception as e:
                        print(f"      ❌ Error analyzing {csv_file.name}: {e}")
            
            return analyses
    
    def _infer_column_types(self, df: pd.DataFrame) -> dict:
        """Infer appropriate database column types from pandas DataFrame"""
        type_mapping = {}
        
        for col in df.columns:
            # Clean column name for database compatibility
            clean_col = self._clean_column_name(col)
            
            # Sample the data to infer type
            sample_values = df[col].dropna().head(10)
            
            if len(sample_values) == 0:
                type_mapping[clean_col] = 'TEXT'
                continue
            
            # Check for boolean patterns
            if all(str(v).upper() in ['TRUE', 'FALSE', '1', '0', 'YES', 'NO'] for v in sample_values):
                type_mapping[clean_col] = 'BOOLEAN'
                continue
            
            # Check for date patterns
            date_patterns = [r'\d{1,2}/\d{1,2}/\d{4}', r'\d{4}-\d{2}-\d{2}']
            if any(re.match(pattern, str(sample_values.iloc[0])) for pattern in date_patterns):
                type_mapping[clean_col] = 'DATETIME'
                continue
                
            # Check for numeric patterns
            try:
                pd.to_numeric(sample_values, errors='raise')
                # Check if all values are integers
                if all(float(v).is_integer() for v in sample_values if pd.notna(v)):
                    type_mapping[clean_col] = 'BIGINT'
                else:
                    type_mapping[clean_col] = 'DECIMAL(15,2)'
                continue
            except:
                pass
            
            # Check for long text vs short text
            max_length = max(len(str(v)) for v in sample_values)
            if max_length > 255:
                type_mapping[clean_col] = 'TEXT'
            else:
                type_mapping[clean_col] = f'VARCHAR({min(max_length * 2, 500)})'
        
        return type_mapping
    
    def _clean_column_name(self, col_name: str) -> str:
        """Clean column name for database compatibility"""
        # Remove special characters, replace spaces with underscores
        clean = re.sub(r'[^\w\s]', '', str(col_name))
        clean = re.sub(r'\s+', '_', clean)
        clean = clean.lower().strip('_')
        
        # Handle reserved words
        reserved_words = ['key', 'order', 'date', 'time', 'status', 'type', 'desc']
        if clean in reserved_words:
            clean = f'{clean}_field'
            
        return clean
    
    def generate_table_schemas(self, analyses: dict) -> dict:
        """Generate CREATE TABLE statements for all CSV imports"""
        
        schemas = {}
        
        for category, analysis in analyses.items():
            table_name = analysis['table_name']
            columns_sql = []
            
            # Add primary key
            pk = analysis['primary_key']
            if isinstance(pk, list):
                # Composite primary key
                for pk_col in pk:
                    clean_pk = self._clean_column_name(pk_col)
                    columns_sql.append(f"    {clean_pk} VARCHAR(50) NOT NULL")
            else:
                clean_pk = self._clean_column_name(pk)
                columns_sql.append(f"    {clean_pk} VARCHAR(50) PRIMARY KEY")
            
            # Add all other columns
            for original_col, data_type in analysis['data_types'].items():
                if original_col not in [self._clean_column_name(pk) for pk in (analysis['primary_key'] if isinstance(analysis['primary_key'], list) else [analysis['primary_key']])]:
                    columns_sql.append(f"    {original_col} {data_type}")
            
            # Add metadata columns
            columns_sql.extend([
                "    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "    import_batch VARCHAR(50)",
                "    file_source VARCHAR(100)"
            ])
            
            # Handle composite primary key
            if isinstance(pk, list):
                pk_constraint = f",\n    PRIMARY KEY ({', '.join([self._clean_column_name(col) for col in pk])})"
                columns_sql[-1] += pk_constraint
            
            columns_joined = ',\n'.join(columns_sql)
            create_sql = f"""
CREATE TABLE IF NOT EXISTS {table_name} (
{columns_joined}
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""
            
            schemas[category] = {
                'table_name': table_name,
                'create_sql': create_sql,
                'columns': analysis['data_types']
            }
        
        return schemas
    
    def create_tuesday_automation_schedule(self):
        """Create Tuesday 8am CSV import automation"""
        
        scheduler_addition = '''
# Add to app/services/scheduler.py

def run_tuesday_csv_imports():
    """Run comprehensive CSV imports for all POS data - Tuesdays at 8am"""
    with app.app_context():
        if retry_database_connection():
            try:
                with acquire_lock(redis_client, "csv_import_lock", 1800):  # 30 min timeout
                    logger.info("Starting Tuesday 8am CSV imports (all POS files)")
                    
                    from .comprehensive_csv_import_service import ComprehensiveCSVImporter
                    importer = ComprehensiveCSVImporter()
                    
                    import_results = importer.import_all_csv_files()
                    logger.info(f"Tuesday CSV imports completed: {import_results}")
                    
            except LockError:
                logger.debug("CSV import lock exists, skipping import")
            except Exception as e:
                logger.error(f"Tuesday CSV import failed: {str(e)}", exc_info=True)
        else:
            logger.error("Skipping CSV import due to database connection failure")

# Add cron-style scheduling for Tuesday 8am
scheduler.add_job(
    func=run_tuesday_csv_imports,
    trigger="cron", 
    day_of_week="tue",
    hour=8,
    minute=0,
    id="tuesday_csv_import",
    replace_existing=True,
    coalesce=True,
    max_instances=1
)
'''
        return scheduler_addition

def main():
    importer = ComprehensiveCSVImporter()
    
    print("🚀 Comprehensive CSV Import System")
    print("=" * 50)
    
    # Analyze all CSV structures
    analyses = importer.analyze_csv_structures()
    
    if '--generate-schemas' in sys.argv:
        print("\n🏗️  Generating Database Schemas...")
        schemas = importer.generate_table_schemas(analyses)
        
        for category, schema in schemas.items():
            print(f"\n-- {category.upper()} TABLE:")
            print(schema['create_sql'])
    
    if '--show-automation' in sys.argv:
        print("\n⏰ Tuesday 8am Automation Code:")
        print(importer.create_tuesday_automation_schedule())
    
    print(f"\n✅ Analysis complete! Found {len(analyses)} CSV categories to import.")
    print("\nNext steps:")
    print("1. Run with --generate-schemas to see database table creation SQL")
    print("2. Run with --show-automation to see Tuesday scheduling code") 
    print("3. Create tables and implement import logic")
    print("4. Add Tuesday 8am scheduling to scheduler.py")

if __name__ == "__main__":
    main()