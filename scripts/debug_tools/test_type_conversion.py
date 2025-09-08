#!/usr/bin/env python3
"""
Test type conversion for correlation matching
"""

import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='rfid_user',
        password='rfid_user_password',
        database='rfid_inventory'
    )

def main():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    print("=== TESTING TYPE CONVERSION ===")
    
    # Test the conversion logic
    print("\n1. Type Conversion Test:")
    cursor.execute("""
        SELECT pe.item_num as pos_decimal, 
               CAST(pe.item_num AS UNSIGNED) as pos_int,
               sd.rental_class_id as seed_string
        FROM pos_equipment pe, seed_rental_classes sd
        WHERE CAST(pe.item_num AS UNSIGNED) = CAST(sd.rental_class_id AS UNSIGNED)
        LIMIT 10
    """)
    
    matches = cursor.fetchall()
    if matches:
        print(f"Found {len(matches)} type-converted matches:")
        for match in matches:
            print(f"  POS: {match['pos_decimal']} -> {match['pos_int']} | SEED: '{match['seed_string']}'")
    else:
        print("  Still no matches with type conversion!")
    
    # Check what numbers we have in each system
    print("\n2. Sample Number Ranges:")
    cursor.execute("SELECT MIN(CAST(item_num AS UNSIGNED)) as min_pos, MAX(CAST(item_num AS UNSIGNED)) as max_pos FROM pos_equipment WHERE item_num REGEXP '^[0-9]+(\\.0)?$'")
    pos_range = cursor.fetchone()
    print(f"  POS range: {pos_range['min_pos']} - {pos_range['max_pos']}")
    
    cursor.execute("SELECT MIN(CAST(rental_class_id AS UNSIGNED)) as min_seed, MAX(CAST(rental_class_id AS UNSIGNED)) as max_seed FROM seed_rental_classes WHERE rental_class_id REGEXP '^[0-9]+$'")
    seed_range = cursor.fetchone()
    print(f"  SEED range: {seed_range['min_seed']} - {seed_range['max_seed']}")
    
    # Check overlap
    print(f"\n3. Do ranges overlap? {pos_range['max_pos'] >= seed_range['min_seed'] and seed_range['max_seed'] >= pos_range['min_pos']}")
    
    # Look for specific matches
    print("\n4. Looking for specific matches:")
    cursor.execute("""
        SELECT COUNT(*) as match_count
        FROM pos_equipment pe
        JOIN seed_rental_classes sd ON CAST(pe.item_num AS UNSIGNED) = CAST(sd.rental_class_id AS UNSIGNED)
    """)
    
    match_count = cursor.fetchone()['match_count']
    print(f"  Total potential matches with type conversion: {match_count}")
    
    if match_count > 0:
        cursor.execute("""
            SELECT pe.item_num, pe.name, pe.qty,
                   sd.rental_class_id, sd.common_name,
                   (SELECT COUNT(*) FROM id_item_master im WHERE im.rental_class_num = sd.rental_class_id) as tag_count,
                   erc.id as existing
            FROM pos_equipment pe
            JOIN seed_rental_classes sd ON CAST(pe.item_num AS UNSIGNED) = CAST(sd.rental_class_id AS UNSIGNED)
            LEFT JOIN equipment_rfid_correlations erc ON CAST(pe.item_num AS UNSIGNED) = CAST(erc.pos_item_num AS UNSIGNED)
            LIMIT 10
        """)
        
        sample_matches = cursor.fetchall()
        print(f"\n  Sample matches:")
        for match in sample_matches:
            status = "ALREADY CORRELATED" if match['existing'] else "NEW"
            print(f"    {match['item_num']} -> {match['rental_class_id']} | Qty: {match['qty']} Tags: {match['tag_count']} | {status}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()