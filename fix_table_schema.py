#!/usr/bin/env python3
"""
Fix table schema data type issues
The table creation logic is incorrectly mapping columns to DATETIME when they should be DECIMAL or INT
"""

import sys
sys.path.append('/home/tim/RFID3')

from app.services.financial_csv_import_service import FinancialCSVImportService

def fix_table_creation_logic():
    """Fix the enhanced scorecard table creation logic"""
    
    # Read the current service file
    with open('/home/tim/RFID3/app/services/financial_csv_import_service.py', 'r') as f:
        content = f.read()
    
    # Find the _create_enhanced_scorecard_table method
    old_method_start = '''    def _create_enhanced_scorecard_table(self, df: pd.DataFrame):
        """Create enhanced scorecard trends table with better data types"""
        with self.Session() as session:
            try:
                # Drop existing table
                session.execute(text("DROP TABLE IF EXISTS pos_scorecard_trends"))
                
                # Build CREATE TABLE statement
                columns_sql = []
                columns_sql.append("id INT AUTO_INCREMENT PRIMARY KEY")
                
                for col in df.columns:
                    dtype = str(df[col].dtype)
                    col_lower = col.lower()
                    
                    if 'datetime' in dtype or 'week' in col_lower:
                        sql_type = "DATETIME"
                    elif 'revenue' in col_lower or 'dollar' in col_lower or 'amount' in col_lower or 'discount' in col_lower or 'reservation' in col_lower or 'ar' in col_lower:
                        sql_type = "DECIMAL(15,2)"
                    elif '%' in col or 'percent' in col_lower:
                        sql_type = "DECIMAL(8,4)"  # Support 4 decimal places for percentages
                    elif any(k in col_lower for k in ['number', 'count', 'contracts', 'deliveries', 'quotes', 'week_number']):
                        sql_type = "INT"
                    else:
                        sql_type = "TEXT"
                    
                    columns_sql.append(f"`{col}` {sql_type}")'''
    
    new_method_start = '''    def _create_enhanced_scorecard_table(self, df: pd.DataFrame):
        """Create enhanced scorecard trends table with better data types"""
        with self.Session() as session:
            try:
                # Drop existing table
                session.execute(text("DROP TABLE IF EXISTS pos_scorecard_trends"))
                
                # Build CREATE TABLE statement
                columns_sql = []
                columns_sql.append("id INT AUTO_INCREMENT PRIMARY KEY")
                
                for col in df.columns:
                    dtype = str(df[col].dtype)
                    col_lower = col.lower()
                    
                    # Date/datetime columns - be very specific
                    if col_lower == 'week_ending_sunday' or 'datetime' in dtype:
                        sql_type = "DATETIME"
                    # Revenue and currency columns
                    elif 'revenue' in col_lower or 'dollar' in col_lower or 'amount' in col_lower or 'discount' in col_lower or 'reservation' in col_lower:
                        sql_type = "DECIMAL(15,2)"
                    # Percentage columns
                    elif '%' in col or 'percent' in col_lower or col_lower == 'total_ar_45_days':
                        sql_type = "DECIMAL(8,4)"  # Support 4 decimal places for percentages
                    # Integer columns
                    elif any(k in col_lower for k in ['number', 'count', 'contracts', 'deliveries', 'quotes', 'week_number']):
                        sql_type = "INT"
                    else:
                        sql_type = "TEXT"
                    
                    columns_sql.append(f"`{col}` {sql_type}")'''
    
    content = content.replace(old_method_start, new_method_start)
    
    # Write the updated content
    with open('/home/tim/RFID3/app/services/financial_csv_import_service.py', 'w') as f:
        f.write(content)
    
    print("✓ Fixed table creation logic for proper data types")

def main():
    print("Fixing table schema issues...")
    
    fix_table_creation_logic()
    
    print("Table schema fixes applied!")

if __name__ == "__main__":
    main()
