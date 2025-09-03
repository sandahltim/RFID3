#!/usr/bin/env python3
"""
Verify POS Database Tables Structure
Ensures tables are ready for CSV import
"""

import pymysql
import pandas as pd
import os
from datetime import datetime
from pathlib import Path

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'rfid_user',
    'password': 'rfid_user_password',
    'database': 'rfid_inventory',
    'charset': 'utf8mb4',
}

# CSV file locations (adjust paths as needed)
CSV_FILES = {
    'pos_customers': '/home/tim/RFID3/shared/POR/customer8.26.25.csv',
    'pos_transactions': '/home/tim/RFID3/shared/POR/transactions8.26.25.csv',
    'pos_transaction_items': '/home/tim/RFID3/shared/POR/transitems8.26.25.csv',
    'pos_scorecard_trends': '/home/tim/RFID3/shared/POR/ScorecardTrends8.26.25.csv',
    'pos_payroll_trends': '/home/tim/RFID3/shared/POR/PayrollTrends8.26.25.csv',
    'pos_profit_loss': '/home/tim/RFID3/shared/POR/PL8.28.25.csv',
}

def get_table_info(cursor, table_name):
    """Get detailed information about a table"""
    # Get column information
    cursor.execute(f"""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            CHARACTER_MAXIMUM_LENGTH,
            IS_NULLABLE,
            COLUMN_KEY,
            COLUMN_DEFAULT,
            EXTRA
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = '{DB_CONFIG['database']}'
        AND TABLE_NAME = '{table_name}'
        ORDER BY ORDINAL_POSITION
    """)
    columns = cursor.fetchall()
    
    # Get index information
    cursor.execute(f"""
        SELECT 
            INDEX_NAME,
            GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) as COLUMNS
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = '{DB_CONFIG['database']}'
        AND TABLE_NAME = '{table_name}'
        GROUP BY INDEX_NAME
    """)
    indexes = cursor.fetchall()
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]
    
    return {
        'columns': columns,
        'indexes': indexes,
        'row_count': row_count
    }

def check_csv_compatibility(table_name, csv_path):
    """Check if CSV file structure is compatible with table"""
    if not os.path.exists(csv_path):
        return {'exists': False, 'path': csv_path}
    
    try:
        # Read first few rows to get structure
        df = pd.read_csv(csv_path, nrows=5)
        
        return {
            'exists': True,
            'path': csv_path,
            'columns': list(df.columns),
            'column_count': len(df.columns),
            'sample_row': df.iloc[0].to_dict() if len(df) > 0 else None,
            'file_size_mb': os.path.getsize(csv_path) / (1024 * 1024)
        }
    except Exception as e:
        return {
            'exists': True,
            'path': csv_path,
            'error': str(e)
        }

def generate_column_mapping(table_columns, csv_columns):
    """Generate mapping between CSV columns and table columns"""
    # Clean column names for comparison
    def clean_name(name):
        return str(name).lower().strip().replace(' ', '_').replace('-', '_')
    
    mapping = {}
    unmapped_csv = []
    unmapped_table = []
    
    csv_clean = {clean_name(c): c for c in csv_columns}
    table_clean = {clean_name(c[0]): c[0] for c in table_columns}
    
    # Try to match columns
    for csv_clean_name, csv_original in csv_clean.items():
        if csv_clean_name in table_clean:
            mapping[csv_original] = table_clean[csv_clean_name]
        else:
            unmapped_csv.append(csv_original)
    
    # Find unmapped table columns
    mapped_table_cols = set(mapping.values())
    for col_info in table_columns:
        col_name = col_info[0]
        if col_name not in mapped_table_cols and col_name not in ['id', 'import_date', 'import_batch', 'file_source']:
            unmapped_table.append(col_name)
    
    return {
        'mapping': mapping,
        'unmapped_csv': unmapped_csv,
        'unmapped_table': unmapped_table
    }

def main():
    """Main verification process"""
    print("\n" + "="*80)
    print("POS DATABASE TABLE STRUCTURE VERIFICATION")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        verification_results = {}
        
        for table_name, csv_path in CSV_FILES.items():
            print(f"\n{'='*60}")
            print(f"📊 TABLE: {table_name}")
            print(f"{'='*60}")
            
            # Get table information
            table_info = get_table_info(cursor, table_name)
            print(f"\n📋 Table Structure:")
            print(f"   • Columns: {len(table_info['columns'])}")
            print(f"   • Indexes: {len(table_info['indexes'])}")
            print(f"   • Current rows: {table_info['row_count']:,}")
            
            # Show key columns
            print(f"\n   Key columns:")
            for col in table_info['columns'][:10]:  # Show first 10 columns
                col_name, data_type, max_len, nullable, key, default, extra = col
                key_indicator = "🔑" if key == "PRI" else "📍" if key else "  "
                print(f"      {key_indicator} {col_name:<30} {data_type}({max_len or ''})")
            
            if len(table_info['columns']) > 10:
                print(f"      ... and {len(table_info['columns']) - 10} more columns")
            
            # Check CSV compatibility
            csv_info = check_csv_compatibility(table_name, csv_path)
            
            if csv_info['exists']:
                if 'error' in csv_info:
                    print(f"\n⚠️  CSV Error: {csv_info['error']}")
                else:
                    print(f"\n📄 CSV File Analysis:")
                    print(f"   • Path: {csv_info['path']}")
                    print(f"   • Size: {csv_info['file_size_mb']:.2f} MB")
                    print(f"   • Columns: {csv_info['column_count']}")
                    
                    # Generate mapping
                    mapping_info = generate_column_mapping(
                        table_info['columns'],
                        csv_info['columns']
                    )
                    
                    print(f"\n🔗 Column Mapping Analysis:")
                    print(f"   • Mapped columns: {len(mapping_info['mapping'])}")
                    print(f"   • Unmapped CSV columns: {len(mapping_info['unmapped_csv'])}")
                    print(f"   • Unmapped table columns: {len(mapping_info['unmapped_table'])}")
                    
                    if mapping_info['unmapped_csv']:
                        print(f"\n   ⚠️  CSV columns not in table:")
                        for col in mapping_info['unmapped_csv'][:5]:
                            print(f"      - {col}")
                        if len(mapping_info['unmapped_csv']) > 5:
                            print(f"      ... and {len(mapping_info['unmapped_csv']) - 5} more")
                    
                    if mapping_info['unmapped_table']:
                        print(f"\n   ⚠️  Table columns not in CSV (may need defaults):")
                        for col in mapping_info['unmapped_table'][:5]:
                            print(f"      - {col}")
                        if len(mapping_info['unmapped_table']) > 5:
                            print(f"      ... and {len(mapping_info['unmapped_table']) - 5} more")
                    
                    verification_results[table_name] = {
                        'status': 'ready' if len(mapping_info['unmapped_table']) == 0 else 'needs_review',
                        'table_columns': len(table_info['columns']),
                        'csv_columns': csv_info['column_count'],
                        'mapped': len(mapping_info['mapping']),
                        'csv_unmapped': len(mapping_info['unmapped_csv']),
                        'table_unmapped': len(mapping_info['unmapped_table'])
                    }
            else:
                print(f"\n❌ CSV file not found: {csv_info['path']}")
                verification_results[table_name] = {
                    'status': 'csv_missing',
                    'path': csv_info['path']
                }
        
        cursor.close()
        conn.close()
        
        # Summary
        print(f"\n{'='*80}")
        print("VERIFICATION SUMMARY")
        print(f"{'='*80}")
        
        ready_count = sum(1 for r in verification_results.values() if r['status'] == 'ready')
        review_count = sum(1 for r in verification_results.values() if r['status'] == 'needs_review')
        missing_count = sum(1 for r in verification_results.values() if r['status'] == 'csv_missing')
        
        print(f"\n📊 Results:")
        print(f"   ✅ Ready for import: {ready_count}")
        print(f"   ⚠️  Needs review: {review_count}")
        print(f"   ❌ CSV missing: {missing_count}")
        
        print("\n📋 Table Status:")
        for table_name, result in verification_results.items():
            status_icon = "✅" if result['status'] == 'ready' else "⚠️" if result['status'] == 'needs_review' else "❌"
            print(f"   {status_icon} {table_name:<30} - {result['status']}")
            if result['status'] == 'needs_review':
                print(f"      Table: {result['table_columns']} cols, CSV: {result['csv_columns']} cols")
                print(f"      Mapped: {result['mapped']}, Unmapped: {result['table_unmapped']} table cols")
        
        if ready_count == len(CSV_FILES):
            print("\n✅ All tables are ready for CSV import!")
        else:
            print("\n⚠️  Some tables need attention before import.")
            print("\nRecommendations:")
            print("1. Place CSV files in /home/tim/RFID3/shared/ directory")
            print("2. Review column mappings for tables marked 'needs_review'")
            print("3. Consider creating transformation scripts for complex mappings")
            print("4. Test with small sample data first")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())