#!/usr/bin/env python3
"""
Database Schema Generator for RFID3 POS Data
Generates complete CREATE TABLE and ALTER TABLE statements based on Excel file column specifications
"""

import pandas as pd
import re
from typing import Dict, List, Tuple, Set

def infer_data_type(column_name: str, description: str = "") -> str:
    """Infer SQL data type based on column name and description"""
    column_lower = str(column_name).lower()

    # Financial/monetary fields
    if any(keyword in column_lower for keyword in [
        'price', 'rate', 'amount', 'cost', 'value', 'deposit', 'dmg', 'sell',
        'retail', 'income', 'expense', 'revenue', 'depr', 'slvg', 'purp',
        'sale', 'rent', 'totl', 'paid', 'depp', 'tax', 'rdis', 'sdis',
        'othr', 'balance', 'limit', 'roi', 'floor', 'markup', 'commission',
        'finance', 'waiver', 'percentage', 'percent'
    ]):
        return "DECIMAL(12,2)"

    # Integer quantities and counts
    if any(keyword in column_lower for keyword in [
        'qty', 'qyot', 'number', 'count', 'num', 'cntr', 'period', 'per',
        'min', 'max', 'level', 'year', 'hour', 'day', 'crew', 'case',
        'seq', 'line', 'trip', 'fuel_tank_size', 'gvwr', 'critical',
        'cleaning_delay', 'setup_time', 'cubic'
    ]):
        return "INT"

    # Boolean fields
    if any(keyword in column_lower for keyword in [
        'non', 'inactive', 'header', 'taxable', 'discount', 'exempt',
        'confirmed', 'completed', 'billed', 'pickup', 'delivery', 'same',
        'verified', 'cancelled', 'review', 'archived', 'hide', 'require',
        'bulk', 'bought', 'suppress', 'force', 'delete', 'only_allow',
        'no_update', 'no_email', 'no_print', 'no_transfer', 'month_to_month'
    ]):
        return "BOOLEAN"

    # Date fields
    if any(keyword in column_lower for keyword in [
        'date', 'expire', 'warranty', 'created', 'updated', 'modified',
        'last_active', 'last_contract', 'last_pay', 'birthday', 'birth',
        'age_date'
    ]):
        if 'time' in column_lower or 'datetime' in column_lower:
            return "DATETIME"
        return "DATE"

    # Time fields
    if any(keyword in column_lower for keyword in ['time', 'dtm']):
        return "TIME"

    # Text/long description fields
    if any(keyword in column_lower for keyword in [
        'notes', 'message', 'description', 'comment', 'address', 'link',
        'addt', 'dstn', 'dstp'
    ]):
        if 'long' in column_lower or len(column_name) > 50:
            return "TEXT"
        return "VARCHAR(500)"

    # GPS coordinates
    if any(keyword in column_lower for keyword in ['longitude', 'latitude', 'weight']):
        return "DECIMAL(10,6)"

    # Default to VARCHAR for text fields
    return "VARCHAR(255)"

def normalize_column_name(name: str) -> str:
    """Convert column name to valid SQL identifier"""
    # Convert to string first
    name = str(name)
    # Remove special characters and spaces
    name = re.sub(r'[^\w\s]', '', name)
    # Replace spaces with underscores
    name = re.sub(r'\s+', '_', name)
    # Convert to lowercase
    name = name.lower()
    # Remove leading/trailing underscores
    name = name.strip('_')
    # Handle empty names
    if not name or name == 'no_title':
        return f"column_{hash(str(name)) % 1000}"
    return name

def get_existing_columns() -> Dict[str, Set[str]]:
    """Get existing column names from current models"""
    existing = {
        'equipment_items': {
            'id', 'item_num', 'key', 'name', 'location', 'category', 'department', 'type_desc',
            'qty', 'home_store', 'current_store', 'equipment_group', 'manufacturer', 'model_no',
            'serial_no', 'part_no', 'license_no', 'model_year', 'turnover_mtd', 'turnover_ytd',
            'turnover_ltd', 'repair_cost_mtd', 'repair_cost_ltd', 'sell_price', 'retail_price',
            'deposit', 'damage_waiver_percent', 'period_1', 'period_2', 'period_3', 'period_4',
            'period_5', 'period_6', 'period_7', 'period_8', 'period_9', 'period_10',
            'rate_1', 'rate_2', 'rate_3', 'rate_4', 'rate_5', 'rate_6', 'rate_7', 'rate_8',
            'rate_9', 'rate_10', 'reorder_min', 'reorder_max', 'user_defined_1', 'user_defined_2',
            'meter_out', 'meter_in', 'depr_method', 'depr', 'non_taxable', 'inactive', 'header_no',
            'last_purchase_date', 'last_purchase_price', 'vendor_no_1', 'vendor_no_2', 'vendor_no_3',
            'order_no_1', 'order_no_2', 'order_no_3', 'qty_on_order', 'sort', 'expiration_date',
            'warranty_date', 'weight', 'setup_time', 'income', 'created_at', 'updated_at', 'import_batch_id'
        },
        'pos_transactions': set(),  # Will be populated based on analysis
        'pos_transitems': set(),    # Will be populated based on analysis
        'pos_customer': set(),      # Will be populated based on analysis
    }
    return existing

def generate_table_schema(tab_name: str, columns: List[str]) -> Tuple[str, List[str]]:
    """Generate CREATE TABLE and ALTER TABLE statements for a tab"""

    existing_columns = get_existing_columns()
    table_mapping = {
        'equipment': 'equipment_items',
        'transactions': 'pos_transactions',
        'transitems': 'pos_transitems',
        'customer': 'pos_customer',
        'scorecard': 'pos_scorecard',
        'payroll': 'pos_payroll',
        'pl': 'pos_profit_loss'
    }

    table_name = table_mapping.get(tab_name.lower(), f'pos_{tab_name.lower()}')
    existing_cols = existing_columns.get(table_name, set())

    # Generate column definitions
    column_defs = []
    alter_statements = []

    for i, col_name in enumerate(columns):
        if not col_name or pd.isna(col_name):
            continue

        normalized_name = normalize_column_name(col_name)
        if not normalized_name:
            continue

        data_type = infer_data_type(col_name)

        # Skip if column already exists
        if normalized_name in existing_cols:
            continue

        column_def = f"    {normalized_name} {data_type}"
        if 'id' in normalized_name.lower() and i == 0:
            column_def += " PRIMARY KEY AUTO_INCREMENT"

        column_def += f" COMMENT '{col_name.replace(chr(39), chr(39)+chr(39)) if isinstance(col_name, str) else 'Generated column'}'"

        column_defs.append(column_def)

        # Generate ALTER TABLE statement for existing tables
        if table_name == 'equipment_items':
            alter_statements.append(f"ALTER TABLE {table_name} ADD COLUMN {normalized_name} {data_type} COMMENT '{col_name.replace(chr(39), chr(39)+chr(39)) if isinstance(col_name, str) else 'Generated column'}';")

    # Generate CREATE TABLE statement
    create_table = f"""
-- {tab_name.upper()} Table Schema ({len(columns)} total columns)
CREATE TABLE IF NOT EXISTS {table_name} (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Primary key',
{','.join(column_defs)},
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation time',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record update time'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='{tab_name} data from POS system';
"""

    return create_table, alter_statements

def main():
    """Main function to process Excel file and generate SQL"""

    excel_file = '/home/tim/RFID3/shared/POR/media/table info.xlsx'
    output_file = '/home/tim/RFID3/complete_database_schema.sql'

    print("Reading Excel file and generating database schemas...")

    try:
        xl = pd.ExcelFile(excel_file)
        all_sql = []
        all_alters = []

        all_sql.append("""-- ================================================================
-- RFID3 Complete Database Schema Generation
-- Generated from: table info.xlsx
-- Purpose: Create complete schemas for all POS data tables
-- ================================================================

SET FOREIGN_KEY_CHECKS = 0;
""")

        # Process each tab
        for sheet_name in xl.sheet_names:
            print(f"Processing {sheet_name} tab...")

            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            columns = df.columns.tolist()

            print(f"  - Found {len(columns)} columns")

            create_sql, alter_statements = generate_table_schema(sheet_name, columns)

            all_sql.append(f"\n-- ================================================================")
            all_sql.append(f"-- {sheet_name.upper()} TABLE")
            all_sql.append(f"-- Total columns: {len(columns)}")
            all_sql.append(f"-- ================================================================")
            all_sql.append(create_sql)

            if alter_statements:
                all_alters.extend(alter_statements)

        # Add ALTER TABLE statements for existing tables
        if all_alters:
            all_sql.append(f"\n-- ================================================================")
            all_sql.append(f"-- ALTER TABLE STATEMENTS FOR EXISTING TABLES")
            all_sql.append(f"-- ================================================================")
            all_sql.extend(all_alters)

        all_sql.append("\nSET FOREIGN_KEY_CHECKS = 1;")

        # Write to file
        with open(output_file, 'w') as f:
            f.write('\n'.join(all_sql))

        print(f"\nSQL schema written to: {output_file}")
        print(f"Total ALTER statements: {len(all_alters)}")

        # Summary statistics
        for sheet_name in xl.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            print(f"{sheet_name}: {len(df.columns)} columns")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()