#!/usr/bin/env python3
"""
Clean Database Schema Generator for RFID3 POS Data
Generates properly formatted CREATE TABLE and ALTER TABLE statements
"""

import pandas as pd
import re
from typing import Dict, List, Set

def infer_data_type(column_name: str) -> str:
    """Infer SQL data type based on column name"""
    column_lower = str(column_name).lower()

    # Financial/monetary fields
    if any(keyword in column_lower for keyword in [
        'price', 'rate', 'amount', 'cost', 'value', 'deposit', 'dmg', 'sell',
        'retail', 'income', 'expense', 'revenue', 'depr', 'slvg', 'purp',
        'sale', 'rent', 'totl', 'paid', 'depp', 'tax', 'rdis', 'sdis',
        'othr', 'balance', 'limit', 'roi', 'floor', 'markup', 'commission',
        'finance', 'waiver', 'percentage', 'percent', 'profit', 'gross'
    ]):
        return "DECIMAL(12,2)"

    # Integer quantities and counts
    if any(keyword in column_lower for keyword in [
        'qty', 'qyot', 'number', 'count', 'num', 'cntr', 'period', 'per',
        'min', 'max', 'level', 'year', 'hour', 'day', 'crew', 'case',
        'seq', 'line', 'trip', 'gvwr', 'critical', 'cubic', 'id'
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
        'age_date', 'sdate', 'ldate'
    ]):
        if 'time' in column_lower or 'datetime' in column_lower:
            return "DATETIME"
        return "DATE"

    # Time fields
    if column_lower in ['time', 'dtm'] or 'setup_time' in column_lower:
        return "TIME"

    # GPS coordinates and weights
    if any(keyword in column_lower for keyword in ['longitude', 'latitude', 'weight']):
        return "DECIMAL(10,6)"

    # Text/long description fields
    if any(keyword in column_lower for keyword in [
        'notes', 'message', 'description', 'comment', 'address', 'link',
        'addt', 'dstn', 'dstp', 'long'
    ]):
        return "TEXT"

    # Default to VARCHAR for text fields
    return "VARCHAR(255)"

def normalize_column_name(name: str) -> str:
    """Convert column name to valid SQL identifier"""
    name = str(name)
    # Remove special characters except underscores
    name = re.sub(r'[^\w\s]', '', name)
    # Replace spaces with underscores
    name = re.sub(r'\s+', '_', name)
    # Convert to lowercase
    name = name.lower()
    # Remove leading/trailing underscores
    name = name.strip('_')
    # Handle empty or problematic names
    if not name or name == 'no_title' or name.isdigit():
        return f"column_{hash(str(name)) % 1000}"
    return name

def get_existing_equipment_columns() -> Set[str]:
    """Get existing column names from equipment_items table"""
    return {
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
    }

def generate_clean_sql():
    """Generate clean, properly formatted SQL"""

    excel_file = '/home/tim/RFID3-RFID-KVC/shared/POR/media/table info.xlsx'
    output_file = '/home/tim/RFID3-RFID-KVC/clean_database_schema.sql'

    existing_equipment_cols = get_existing_equipment_columns()

    sql_lines = [
        "-- ================================================================",
        "-- RFID3 Complete Database Schema Generation",
        "-- Generated from: table info.xlsx",
        "-- Purpose: Create complete schemas for all POS data tables",
        "-- Date: 2025-09-18",
        "-- ================================================================",
        "",
        "SET FOREIGN_KEY_CHECKS = 0;",
        ""
    ]

    xl = pd.ExcelFile(excel_file)
    equipment_alters = []

    for sheet_name in xl.sheet_names:
        print(f"Processing {sheet_name} tab...")

        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        columns = df.columns.tolist()

        # Determine table name
        if sheet_name.lower() == 'equipment':
            table_name = 'equipment_items'
            # Generate ALTER statements for existing equipment table
            for col_name in columns:
                if not col_name or pd.isna(col_name):
                    continue

                normalized_name = normalize_column_name(col_name)
                if not normalized_name or normalized_name in existing_equipment_cols:
                    continue

                data_type = infer_data_type(col_name)
                comment = str(col_name).replace("'", "''")

                equipment_alters.append(
                    f"ALTER TABLE equipment_items ADD COLUMN {normalized_name} {data_type} COMMENT '{comment}';"
                )
        else:
            # Generate CREATE TABLE for other tables
            table_name = f"pos_{sheet_name.lower()}"

            sql_lines.extend([
                "-- ================================================================",
                f"-- {sheet_name.upper()} TABLE ({len(columns)} columns)",
                "-- ================================================================",
                "",
                f"CREATE TABLE IF NOT EXISTS {table_name} (",
                "    id INT PRIMARY KEY AUTO_INCREMENT COMMENT 'Primary key',"
            ])

            for col_name in columns:
                if not col_name or pd.isna(col_name):
                    continue

                normalized_name = normalize_column_name(col_name)
                if not normalized_name:
                    continue

                data_type = infer_data_type(col_name)
                comment = str(col_name).replace("'", "''")

                sql_lines.append(f"    {normalized_name} {data_type} COMMENT '{comment}',")

            sql_lines.extend([
                "    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Record creation time',",
                "    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Record update time'",
                f") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='{sheet_name} data from POS system';",
                ""
            ])

    # Add equipment ALTER statements
    if equipment_alters:
        sql_lines.extend([
            "-- ================================================================",
            f"-- EQUIPMENT TABLE ALTERATIONS ({len(equipment_alters)} new columns)",
            "-- ================================================================",
            ""
        ])
        sql_lines.extend(equipment_alters)
        sql_lines.append("")

    sql_lines.append("SET FOREIGN_KEY_CHECKS = 1;")

    # Write to file
    with open(output_file, 'w') as f:
        f.write('\n'.join(sql_lines))

    print(f"\nClean SQL schema written to: {output_file}")
    print(f"Equipment table additions: {len(equipment_alters)} columns")

    # Summary
    for sheet_name in xl.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        print(f"{sheet_name}: {len(df.columns)} columns")

if __name__ == "__main__":
    generate_clean_sql()