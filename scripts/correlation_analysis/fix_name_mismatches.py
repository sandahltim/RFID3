#!/usr/bin/env python3
"""
Fix Name Mismatch Correlations
Normalize punctuation differences to create additional correlations
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


def normalize_name(name):
    """Advanced normalization for equipment names."""
    if not name:
        return ''
    
    # Convert to upper case
    normalized = str(name).upper()
    
    # Remove leading/trailing underscores and periods
    normalized = normalized.strip('_.')
    
    # Normalize spacing around punctuation
    normalized = re.sub(r'\s*,\s*', ', ', normalized)  # Fix comma spacing
    normalized = re.sub(r'\s*\(\s*', ' (', normalized)  # Fix parenthesis spacing  
    normalized = re.sub(r'\s*\)\s*', ') ', normalized)
    normalized = re.sub(r'\s*"\s*', ' ', normalized)    # Remove quotes
    normalized = re.sub(r'\s*\'\s*', '', normalized)    # Remove apostrophes
    normalized = re.sub(r'\s*-\s*', ' ', normalized)    # Normalize dashes
    
    # Remove extra characters that cause mismatches
    normalized = re.sub(r'[_\.](?=\s)', ' ', normalized)  # Convert _.space to space
    normalized = re.sub(r'==+', '', normalized)  # Remove equals signs
    normalized = re.sub(r'\*+', '', normalized)   # Remove asterisks
    
    # Normalize multiple spaces
    normalized = ' '.join(normalized.split())
    
    return normalized.strip()


def find_fixable_name_mismatches():
    """Find name mismatches that can be fixed with normalization."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    print("Finding fixable name mismatches...")
    
    # Get uncorrelated ItemNum matches with name differences
    query = """
    SELECT 
        pe.item_num as pos_item_num,
        pe.name as pos_equipment_name,
        pe.qty as pos_qty,
        sd.rental_class_id as rfid_rental_class_id,
        sd.common_name as rfid_common_name,
        (SELECT COUNT(*) FROM id_item_master im WHERE im.rental_class_num = sd.rental_class_id) as rfid_tag_count
    FROM pos_equipment pe
    JOIN seed_rental_classes sd ON CAST(pe.item_num AS UNSIGNED) = CAST(sd.rental_class_id AS UNSIGNED)
    LEFT JOIN equipment_rfid_correlations erc ON CAST(pe.item_num AS UNSIGNED) = CAST(erc.pos_item_num AS UNSIGNED)
    WHERE erc.id IS NULL
    ORDER BY pe.item_num
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    fixable_matches = []
    still_mismatched = []
    
    for row in results:
        pos_name = row['pos_equipment_name'] or ''
        rfid_name = row['rfid_common_name'] or ''
        
        # Normalize both names
        pos_normalized = normalize_name(pos_name)
        rfid_normalized = normalize_name(rfid_name)
        
        if pos_normalized == rfid_normalized:
            # Names match after normalization!
            fixable_matches.append({
                'pos_item_num': row['pos_item_num'],
                'pos_name': pos_name,
                'rfid_class_id': row['rfid_rental_class_id'],
                'rfid_name': rfid_name,
                'pos_qty': row['pos_qty'],
                'rfid_tag_count': row['rfid_tag_count'],
                'normalized_name': pos_normalized
            })
        else:
            # Still different after normalization
            still_mismatched.append({
                'pos_item_num': row['pos_item_num'],
                'pos_name': pos_name,
                'rfid_name': rfid_name,
                'pos_normalized': pos_normalized,
                'rfid_normalized': rfid_normalized
            })
    
    cursor.close()
    conn.close()
    
    return fixable_matches, still_mismatched


def insert_fixed_correlations(matches):
    """Insert correlations for normalized name matches."""
    if not matches:
        print("No fixable matches to insert")
        return 0
    
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
                match['pos_item_num'],  # normalized same as original for ItemNum matches
                match['rfid_class_id'],
                match['pos_name'],
                match['rfid_name'],
                95.0,  # 95% confidence for normalized name matches
                'normalized_name_match',
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
    
    return inserted


def main():
    """Main execution."""
    print("=== NAME MISMATCH CLEANUP ===")
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
    
    # Find fixable matches
    fixable_matches, still_mismatched = find_fixable_name_mismatches()
    
    print(f"Found {len(fixable_matches)} fixable name mismatches")
    print(f"Found {len(still_mismatched)} still mismatched after normalization")
    
    # Show sample fixable matches
    if fixable_matches:
        print(f"\nSample fixable matches:")
        for i, match in enumerate(fixable_matches[:5]):
            print(f"  {i+1}. {match['pos_item_num']}: '{match['pos_name'][:40]}...' → '{match['rfid_name'][:40]}...'")
            print(f"      Normalized: '{match['normalized_name'][:50]}...'")
        
        # Insert the fixes
        inserted = insert_fixed_correlations(fixable_matches)
        print(f"\nSuccessfully inserted {inserted} normalized correlations")
        
        # Show new total
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM equipment_rfid_correlations")
        new_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        print(f"New correlation total: {new_count}")
        print(f"Expansion: {current_count} → {new_count} (+{new_count - current_count})")
    
    # Show sample remaining mismatches
    if still_mismatched:
        print(f"\nSample remaining mismatches (need manual review):")
        for i, mismatch in enumerate(still_mismatched[:5]):
            print(f"  {i+1}. {mismatch['pos_item_num']}")
            print(f"      POS: '{mismatch['pos_name']}'")
            print(f"      RFID: '{mismatch['rfid_name']}'")
            print(f"      POS Norm: '{mismatch['pos_normalized']}'")
            print(f"      RFID Norm: '{mismatch['rfid_normalized']}'")
            print()
    
    print(f"\nCompleted at: {datetime.now()}")


if __name__ == "__main__":
    main()