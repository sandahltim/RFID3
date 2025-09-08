#!/usr/bin/env python3
"""
Correlation Expansion Script
Finds exact matches between POS equipment ItemNum and RFIDpro rental_class_id
Flags outliers for manual review
"""

import mysql.connector
import re
from datetime import datetime


def get_db_connection():
    """Get database connection."""
    return mysql.connector.connect(
        host='localhost',
        user='rfid_user',
        password='rfid_user_password',
        database='rfid_inventory'
    )


def normalize_text(text):
    """Normalize text for comparison - remove special characters and extra spaces."""
    if not text:
        return ''
    # Remove special characters but keep alphanumeric and basic punctuation
    normalized = re.sub(r'[^\w\s\-\.\,\(\)]', '', str(text))
    # Normalize spaces
    normalized = ' '.join(normalized.split())
    return normalized.upper()


def find_exact_matches():
    """Find exact ItemNum matches and analyze quantity correlations between POS equipment and RFIDpro."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    print("Finding exact ItemNum matches and analyzing quantities...")
    
    # Query for potential matches with quantity comparison (handle type conversion)
    query = """
    SELECT 
        pe.item_num as pos_item_num,
        pe.name as pos_equipment_name,
        pe.qty as pos_qty,
        sd.rental_class_id as rfid_rental_class_id,
        sd.common_name as rfid_common_name,
        (SELECT COUNT(*) FROM id_item_master im WHERE im.rental_class_num = sd.rental_class_id) as rfid_tag_count,
        erc.id as existing_correlation
    FROM pos_equipment pe
    JOIN seed_rental_classes sd ON CAST(pe.item_num AS UNSIGNED) = CAST(sd.rental_class_id AS UNSIGNED)
    LEFT JOIN equipment_rfid_correlations erc ON CAST(pe.item_num AS UNSIGNED) = CAST(erc.pos_item_num AS UNSIGNED)
    ORDER BY pe.item_num
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    exact_matches = []
    quantity_outliers = []
    name_outliers = []
    
    for row in results:
        pos_item_num = row['pos_item_num']
        pos_name = row['pos_equipment_name'] or ''
        pos_qty = row['pos_qty'] or 0
        rfid_class_id = row['rfid_rental_class_id']
        rfid_name = row['rfid_common_name'] or ''
        rfid_tag_count = row['rfid_tag_count'] or 0
        existing = row['existing_correlation']
        
        # Normalize names for comparison
        pos_normalized = normalize_text(pos_name)
        rfid_normalized = normalize_text(rfid_name)
        
        # Calculate quantity difference
        qty_diff = abs(pos_qty - rfid_tag_count)
        qty_percentage = (qty_diff / max(pos_qty, 1)) * 100 if pos_qty > 0 else (100 if rfid_tag_count > 0 else 0)
        
        # All results from query are exact matches due to JOIN condition
        
        # Create correlation record
        correlation_data = {
            'pos_item_num': pos_item_num,
            'pos_name': pos_name,
            'pos_qty': pos_qty,
            'rfid_class_id': rfid_class_id,
            'rfid_name': rfid_name,
            'rfid_tag_count': rfid_tag_count,
            'qty_diff': qty_diff,
            'qty_percentage': qty_percentage,
            'existing': existing
        }
        
        # Skip if already correlated
        if existing:
            # Still flag quantity discrepancies for existing correlations
            if qty_diff > 2:  # Flag if difference > 2 items
                quantity_outliers.append({
                    **correlation_data,
                    'issue': 'quantity_discrepancy_existing'
                })
            continue
        
        # Check name similarity
        if pos_normalized == rfid_normalized:
            # Check quantity similarity
            if qty_diff <= 2:  # Accept small differences (2 or fewer)
                exact_matches.append({
                    **correlation_data,
                    'match_type': 'exact_match'
                })
            else:
                # Good name match but quantity discrepancy
                quantity_outliers.append({
                    **correlation_data,
                    'issue': 'quantity_discrepancy'
                })
        else:
            # ItemNum matches but names differ
            name_outliers.append({
                **correlation_data,
                'pos_normalized': pos_normalized,
                'rfid_normalized': rfid_normalized,
                'issue': 'name_mismatch'
            })
    
    cursor.close()
    conn.close()
    
    return exact_matches, quantity_outliers, name_outliers


def insert_correlations(matches):
    """Insert new correlations into database."""
    if not matches:
        print("No new correlations to insert")
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    insert_query = """
    INSERT INTO equipment_rfid_correlations 
    (pos_item_num, normalized_item_num, rfid_rental_class_num, 
     pos_equipment_name, rfid_common_name, confidence_score, 
     correlation_type, seed_class_id, created_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    inserted = 0
    for match in matches:
        try:
            values = (
                match['pos_item_num'],
                match['pos_item_num'],  # normalized same as original for exact matches
                match['rfid_class_id'],
                match['pos_name'],
                match['rfid_name'],
                100.0,  # 100% confidence for exact matches
                'exact_match',
                match['rfid_class_id'],
                datetime.now()
            )
            
            cursor.execute(insert_query, values)
            inserted += 1
            
        except Exception as e:
            print(f"Error inserting correlation for {match['pos_item_num']}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Inserted {inserted} new correlations")
    return inserted


def print_quantity_outliers(outliers):
    """Print quantity discrepancy outliers for manual review."""
    if not outliers:
        print("No quantity discrepancies found!")
        return
    
    print(f"\n=== QUANTITY DISCREPANCIES ({len(outliers)}) ===")
    print("POS Qty vs RFID Tag Count differences:")
    print()
    
    for outlier in outliers:
        print(f"ItemNum: {outlier['pos_item_num']}")
        print(f"  Name: {outlier['pos_name']}")
        print(f"  POS Qty: {outlier['pos_qty']}")
        print(f"  RFID Tags: {outlier['rfid_tag_count']}")
        print(f"  Difference: {outlier['qty_diff']} ({outlier['qty_percentage']:.1f}%)")
        print(f"  Status: {'Already Correlated' if outlier['issue'] == 'quantity_discrepancy_existing' else 'New'}")
        print()

def print_name_outliers(outliers):
    """Print name mismatch outliers for manual review.""" 
    if not outliers:
        print("No name mismatches found!")
        return
    
    print(f"\n=== NAME MISMATCHES ({len(outliers)}) ===")
    print("ItemNum matches but names differ:")
    print()
    
    for outlier in outliers:
        print(f"ItemNum: {outlier['pos_item_num']}")
        print(f"  POS Name:  '{outlier['pos_name']}'")
        print(f"  RFID Name: '{outlier['rfid_name']}'")
        print(f"  POS Qty: {outlier['pos_qty']} | RFID Tags: {outlier['rfid_tag_count']}")
        print(f"  POS Norm:  '{outlier['pos_normalized']}'")
        print(f"  RFID Norm: '{outlier['rfid_normalized']}'")
        print()


def main():
    """Main execution."""
    print("=== POS-RFIDpro Correlation Expansion ===")
    print(f"Started at: {datetime.now()}")
    print()
    
    # Get current correlation count
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM equipment_rfid_correlations")
    current_count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    
    print(f"Current correlations: {current_count}")
    
    # Find matches
    exact_matches, quantity_outliers, name_outliers = find_exact_matches()
    
    print(f"Found {len(exact_matches)} new exact matches")
    print(f"Found {len(quantity_outliers)} quantity discrepancies")
    print(f"Found {len(name_outliers)} name mismatches")
    
    # Insert exact matches
    if exact_matches:
        inserted = insert_correlations(exact_matches)
        print(f"Successfully inserted {inserted} correlations")
        
        # Show new total
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM equipment_rfid_correlations")
        new_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        print(f"New correlation total: {new_count}")
        print(f"Expansion: {current_count} → {new_count} (+{new_count - current_count})")
    
    # Print outliers for review
    print_quantity_outliers(quantity_outliers)
    print_name_outliers(name_outliers)
    
    print(f"\nCompleted at: {datetime.now()}")


if __name__ == "__main__":
    main()