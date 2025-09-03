#!/usr/bin/env python3
"""
Database Correlation State Analysis
Comprehensive analysis of RFID3 database correlation coverage
"""

import pymysql
from tabulate import tabulate
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'rfid_user',
    'password': 'rfid_user_password',
    'database': 'rfid_inventory',
    'charset': 'utf8mb4'
}

def get_connection():
    """Create database connection"""
    return pymysql.connect(**DB_CONFIG)

def analyze_correlation_state():
    """Comprehensive analysis of correlation state"""
    conn = get_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    print("=" * 80)
    print("RFID3 DATABASE CORRELATION STATE ANALYSIS")
    print("=" * 80)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. Check table existence
    print("\n1. TABLE/VIEW EXISTENCE CHECK")
    print("-" * 40)
    
    tables_to_check = [
        'pos_equipment',
        'id_item_master', 
        'equipment_rfid_correlations',
        'combined_inventory',
        'pos_rfid_correlations',
        'rfid_pos_mapping'
    ]
    
    cursor.execute("""
        SELECT table_name, table_type
        FROM information_schema.tables
        WHERE table_schema = 'rfid_inventory'
        AND table_name IN (%s)
    """ % ','.join(['%s'] * len(tables_to_check)), tables_to_check)
    
    existing_tables = cursor.fetchall()
    table_status = []
    
    for table in tables_to_check:
        exists = any(t['table_name'] == table for t in existing_tables)
        table_type = next((t['table_type'] for t in existing_tables if t['table_name'] == table), 'N/A')
        status = '✓ EXISTS' if exists else '✗ MISSING'
        table_status.append([table, table_type, status])
    
    print(tabulate(table_status, headers=['Table/View', 'Type', 'Status'], tablefmt='grid'))
    
    # 2. Data Volume Analysis
    print("\n2. DATA VOLUME ANALYSIS")
    print("-" * 40)
    
    queries = {
        'POS Equipment (Active)': """
            SELECT COUNT(*) as count FROM pos_equipment 
            WHERE inactive = 0 
            AND category NOT IN ('UNUSED', 'NON CURRENT ITEMS', 'Parts - Internal Repair/Maint')
        """,
        'POS Equipment (Total)': "SELECT COUNT(*) as count FROM pos_equipment",
        'RFID Items (Total)': "SELECT COUNT(*) as count FROM id_item_master WHERE identifier_type = 'RFID'",
        'RFID Unique Classes': "SELECT COUNT(DISTINCT rental_class_num) as count FROM id_item_master WHERE identifier_type = 'RFID'",
        'Equipment Correlations': "SELECT COUNT(*) as count FROM equipment_rfid_correlations",
        'POS-RFID Correlations': "SELECT COUNT(*) as count FROM pos_rfid_correlations",
        'RFID-POS Mappings': "SELECT COUNT(*) as count FROM rfid_pos_mapping"
    }
    
    volumes = []
    for label, query in queries.items():
        try:
            cursor.execute(query)
            result = cursor.fetchone()
            volumes.append([label, f"{result['count']:,}"])
        except Exception as e:
            volumes.append([label, f"ERROR: {str(e)[:30]}"])
    
    print(tabulate(volumes, headers=['Metric', 'Count'], tablefmt='grid'))
    
    # 3. Correlation Coverage Analysis
    print("\n3. CORRELATION COVERAGE ANALYSIS")
    print("-" * 40)
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_correlations,
            SUM(CASE WHEN confidence_score >= 0.8 THEN 1 ELSE 0 END) as high_confidence,
            SUM(CASE WHEN confidence_score >= 0.5 AND confidence_score < 0.8 THEN 1 ELSE 0 END) as medium_confidence,
            SUM(CASE WHEN confidence_score < 0.5 THEN 1 ELSE 0 END) as low_confidence,
            AVG(confidence_score) as avg_confidence
        FROM equipment_rfid_correlations
    """)
    
    corr_stats = cursor.fetchone()
    
    # Calculate coverage percentage
    cursor.execute("""
        SELECT COUNT(*) as active_equipment 
        FROM pos_equipment 
        WHERE inactive = 0 
        AND category NOT IN ('UNUSED', 'NON CURRENT ITEMS', 'Parts - Internal Repair/Maint')
    """)
    active_equip = cursor.fetchone()['active_equipment']
    
    coverage_pct = (corr_stats['total_correlations'] / active_equip * 100) if active_equip > 0 else 0
    
    print(f"Total Correlations: {corr_stats['total_correlations']:,}")
    print(f"Active Equipment: {active_equip:,}")
    print(f"Coverage Percentage: {coverage_pct:.2f}%")
    print(f"\nConfidence Distribution:")
    print(f"  High (≥0.8): {corr_stats['high_confidence']:,}")
    print(f"  Medium (0.5-0.8): {corr_stats['medium_confidence']:,}")
    print(f"  Low (<0.5): {corr_stats['low_confidence']:,}")
    print(f"  Average Score: {corr_stats['avg_confidence']:.2f}")
    
    # 4. RFID Data Match Analysis
    print("\n4. RFID DATA MATCH ANALYSIS")
    print("-" * 40)
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_correlations,
            SUM(CASE WHEN rfid_match.rental_class_num IS NOT NULL THEN 1 ELSE 0 END) as matching_rfid_data
        FROM equipment_rfid_correlations erc
        LEFT JOIN (
            SELECT DISTINCT rental_class_num 
            FROM id_item_master 
            WHERE identifier_type = 'RFID'
        ) rfid_match ON erc.rfid_rental_class_num = rfid_match.rental_class_num
    """)
    
    match_stats = cursor.fetchone()
    match_pct = (match_stats['matching_rfid_data'] / match_stats['total_correlations'] * 100) if match_stats['total_correlations'] > 0 else 0
    
    print(f"Correlations with matching RFID data: {match_stats['matching_rfid_data']:,} / {match_stats['total_correlations']:,} ({match_pct:.1f}%)")
    
    # 5. Combined Inventory View Analysis
    print("\n5. COMBINED INVENTORY VIEW ANALYSIS")
    print("-" * 40)
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_items,
            SUM(CASE WHEN correlation_confidence IS NOT NULL THEN 1 ELSE 0 END) as correlated_items,
            SUM(CASE WHEN rfid_tag_count > 0 THEN 1 ELSE 0 END) as items_with_rfid,
            SUM(CASE WHEN data_quality_flag = 'good_quality' THEN 1 ELSE 0 END) as good_quality,
            SUM(CASE WHEN data_quality_flag = 'quantity_mismatch' THEN 1 ELSE 0 END) as qty_mismatch,
            SUM(CASE WHEN data_quality_flag = 'low_confidence_match' THEN 1 ELSE 0 END) as low_conf,
            SUM(CASE WHEN data_quality_flag = 'no_rfid_correlation' THEN 1 ELSE 0 END) as no_correlation
        FROM combined_inventory
    """)
    
    view_stats = cursor.fetchone()
    
    view_data = [
        ['Total Items in View', f"{view_stats['total_items']:,}"],
        ['Items with Correlations', f"{view_stats['correlated_items']:,}"],
        ['Items with RFID Tags', f"{view_stats['items_with_rfid']:,}"],
        ['Good Quality', f"{view_stats['good_quality']:,}"],
        ['Quantity Mismatch', f"{view_stats['qty_mismatch']:,}"],
        ['Low Confidence', f"{view_stats['low_conf']:,}"],
        ['No Correlation', f"{view_stats['no_correlation']:,}"]
    ]
    
    print(tabulate(view_data, headers=['Metric', 'Count'], tablefmt='grid'))
    
    # 6. Sample Working Correlations
    print("\n6. SAMPLE WORKING CORRELATIONS (with RFID data)")
    print("-" * 40)
    
    cursor.execute("""
        SELECT 
            erc.pos_item_num,
            LEFT(erc.pos_equipment_name, 30) as equipment_name,
            erc.rfid_rental_class_num,
            COUNT(DISTINCT iim.tag_num) as rfid_tags,
            erc.confidence_score
        FROM equipment_rfid_correlations erc
        INNER JOIN id_item_master iim ON erc.rfid_rental_class_num = iim.rental_class_num
        WHERE iim.identifier_type = 'RFID'
        GROUP BY erc.id
        ORDER BY COUNT(DISTINCT iim.tag_num) DESC
        LIMIT 10
    """)
    
    working_correlations = cursor.fetchall()
    
    if working_correlations:
        headers = ['POS Item', 'Equipment Name', 'RFID Class', 'Tag Count', 'Confidence']
        rows = [[r['pos_item_num'], r['equipment_name'], r['rfid_rental_class_num'], 
                r['rfid_tags'], f"{r['confidence_score']:.1f}"] for r in working_correlations]
        print(tabulate(rows, headers=headers, tablefmt='grid'))
    else:
        print("No working correlations found with RFID data")
    
    # 7. Discrepancy Analysis
    print("\n7. DISCREPANCY ANALYSIS")
    print("-" * 40)
    
    print("\nDocumented vs Actual State:")
    documented = {
        'Equipment Correlations': 533,
        'Coverage Percentage': 58.7,
        'Combined Inventory View': 'Operational',
        'Cross-system Analytics': 'Enabled'
    }
    
    actual = {
        'Equipment Correlations': corr_stats['total_correlations'],
        'Coverage Percentage': coverage_pct,
        'Combined Inventory View': 'EXISTS' if any(t['table_name'] == 'combined_inventory' for t in existing_tables) else 'MISSING',
        'Cross-system Analytics': 'PARTIAL' if match_stats['matching_rfid_data'] > 0 else 'DISABLED'
    }
    
    discrepancy_table = []
    for key in documented:
        doc_val = documented[key]
        act_val = actual[key]
        match = '✓' if str(doc_val) == str(act_val) or (isinstance(doc_val, (int, float)) and isinstance(act_val, (int, float)) and abs(doc_val - act_val) < 1) else '✗'
        discrepancy_table.append([key, doc_val, act_val, match])
    
    print(tabulate(discrepancy_table, headers=['Metric', 'Documented', 'Actual', 'Match'], tablefmt='grid'))
    
    cursor.close()
    conn.close()
    
    return corr_stats, match_stats, view_stats

if __name__ == "__main__":
    analyze_correlation_state()