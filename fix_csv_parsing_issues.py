#!/usr/bin/env python3
"""
Fix specific parsing issues found in CSV import
"""

import sys
import re

# Add the project root to Python path
sys.path.append('/home/tim/RFID3')

from app.services.financial_csv_import_service import FinancialCSVImportService

def fix_currency_cleaner():
    """Fix the currency cleaner to handle quoted values properly"""
    
    # Read the current service file
    with open('/home/tim/RFID3/app/services/financial_csv_import_service.py', 'r') as f:
        content = f.read()
    
    # Find the aggressive_currency_cleaner method
    old_method = '''    def aggressive_currency_cleaner(self, value: str) -> Optional[float]:
        """Aggressively clean currency values from Excel CSV exports"""
        if pd.isna(value) or value is None:
            return None
            
        # Convert to string and strip spaces
        clean_val = str(value).strip()
        
        # Handle empty or dash values
        if clean_val in ['', '-', '$-', '$ -', ' ', 'nan', 'NaN', 'NULL']:
            return 0.0
        
        # Remove currency symbols and formatting
        # Handle patterns like: " $118,244 ", "$118,244", "$-", "118244"
        clean_val = clean_val.replace('$', '').replace(',', '').replace(' ', '')
        
        # Handle parentheses as negative (accounting format)
        if clean_val.startswith('(') and clean_val.endswith(')'):
            clean_val = '-' + clean_val[1:-1]
        
        # Try to convert to float
        try:
            return float(clean_val) if clean_val else 0.0
        except (ValueError, TypeError):
            logger.warning(f"Could not parse currency value: '{value}' -> '{clean_val}'")
            self.import_stats["parsing_issues"].append(f"Currency parse failed: '{value}'")
            return None'''
    
    new_method = '''    def aggressive_currency_cleaner(self, value: str) -> Optional[float]:
        """Aggressively clean currency values from Excel CSV exports"""
        if pd.isna(value) or value is None:
            return None
            
        # Convert to string and strip spaces
        clean_val = str(value).strip()
        
        # Handle empty or dash values
        if clean_val in ['', '-', '$-', '$ -', ' ', 'nan', 'NaN', 'NULL']:
            return 0.0
        
        # Handle percentage values - these should not be processed as currency
        if '%' in clean_val:
            logger.debug(f"Percentage value found in currency field: '{value}'")
            return None
        
        # Remove quotes first - Excel exports often have quoted values like '" $118,244 "'
        clean_val = clean_val.strip('"').strip("'").strip()
        
        # Remove currency symbols and formatting
        # Handle patterns like: " $118,244 ", "$118,244", "$-", "118244"
        clean_val = clean_val.replace('$', '').replace(',', '').replace(' ', '')
        
        # Handle parentheses as negative (accounting format)
        if clean_val.startswith('(') and clean_val.endswith(')'):
            clean_val = '-' + clean_val[1:-1]
        
        # Try to convert to float
        try:
            return float(clean_val) if clean_val else 0.0
        except (ValueError, TypeError):
            logger.warning(f"Could not parse currency value: '{value}' -> '{clean_val}'")
            self.import_stats["parsing_issues"].append(f"Currency parse failed: '{value}'")
            return None'''
    
    # Replace the method
    content = content.replace(old_method, new_method)
    
    # Fix the column name mapping to handle percentage columns properly
    old_conversion = '''            for col in df.columns:
                col_lower = col.lower()
                original_non_null = df[col].notna().sum()
                
                # Currency columns
                if any(keyword in col_lower for keyword in ['revenue', 'dollar', 'amount', 'discount', 'ar', 'reservation']):'''
    
    new_conversion = '''            for col in df.columns:
                col_lower = col.lower()
                original_non_null = df[col].notna().sum()
                
                # Percentage columns (check first to avoid currency processing)
                if '%' in col or 'percent' in col_lower or 'total_ar_45_days' in col_lower:
                    logger.info(f"Processing percentage column: {col}")
                    conversion_stats['percentage_columns'].append(col)
                    
                    cleaned_values = df[col].apply(self.aggressive_percentage_cleaner)
                    df[col] = cleaned_values
                    
                    new_non_null = df[col].notna().sum()
                    logger.info(f"  Percentage conversion: {original_non_null} -> {new_non_null} valid values")
                
                # Currency columns (excluding percentage columns)
                elif any(keyword in col_lower for keyword in ['revenue', 'dollar', 'amount', 'discount', 'reservation']) and 'total_ar_45_days' not in col_lower:'''
    
    content = content.replace(old_conversion, new_conversion)
    
    # Update percentage column detection in the old elif block
    old_elif = '''                # Percentage columns
                elif '%' in col or 'percent' in col_lower:
                    logger.info(f"Processing percentage column: {col}")
                    conversion_stats['percentage_columns'].append(col)
                    
                    cleaned_values = df[col].apply(self.aggressive_percentage_cleaner)
                    df[col] = cleaned_values
                    
                    new_non_null = df[col].notna().sum()
                    logger.info(f"  Percentage conversion: {original_non_null} -> {new_non_null} valid values")'''
    
    # Remove the old percentage elif block since it's now handled first
    content = content.replace(old_elif, '')
    
    # Write the updated content
    with open('/home/tim/RFID3/app/services/financial_csv_import_service.py', 'w') as f:
        f.write(content)
    
    print("✓ Fixed currency cleaner to handle quoted values and percentage columns")

def fix_column_name_mapping():
    """Fix column name mapping for store revenue columns"""
    
    # Read the current service file
    with open('/home/tim/RFID3/app/services/financial_csv_import_service.py', 'r') as f:
        content = f.read()
    
    # Find the store mappings section
    old_mappings = '''        store_mappings = {
            '_3607_revenue': 'store_3607_revenue',
            '_6800_revenue': 'store_6800_revenue', 
            '_728_revenue': 'store_728_revenue',
            '_8101_revenue': 'store_8101_revenue',
            'new_open_contracts_3607': 'contracts_3607',
            'new_open_contracts_6800': 'contracts_6800',
            'new_open_contracts_728': 'contracts_728',
            'new_open_contracts_8101': 'contracts_8101'
        }'''
    
    new_mappings = '''        store_mappings = {
            '_3607_revenue': 'store_3607_revenue',
            '_6800_revenue': 'store_6800_revenue', 
            '_728_revenue': 'store_728_revenue',
            '_8101_revenue': 'store_8101_revenue',
            'colstore_3607_revenue': 'store_3607_revenue',
            'colstore_6800_revenue': 'store_6800_revenue', 
            'colstore_728_revenue': 'store_728_revenue',
            'colstore_8101_revenue': 'store_8101_revenue',
            'new_open_contracts_3607': 'contracts_3607',
            'new_open_contracts_6800': 'contracts_6800',
            'new_open_contracts_728': 'contracts_728',
            'new_open_contracts_8101': 'contracts_8101'
        }'''
    
    content = content.replace(old_mappings, new_mappings)
    
    # Write the updated content
    with open('/home/tim/RFID3/app/services/financial_csv_import_service.py', 'w') as f:
        f.write(content)
    
    print("✓ Fixed column name mapping for store revenue columns")

def main():
    print("Fixing CSV parsing issues...")
    
    fix_currency_cleaner()
    fix_column_name_mapping()
    
    print("All fixes applied successfully!")

if __name__ == "__main__":
    main()
