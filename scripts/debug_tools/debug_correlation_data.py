#!/usr/bin/env python3
"""
Debug correlation data to understand why no matches are found
"""

import mysql.connector

def get_db_connection():
    """Get database connection."""
    return mysql.connector.connect(
        host='localhost',
        user='rfid_user',
        password='rfid_user_password',
        database='rfid_inventory'
    )

def main():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    print("=== DEBUGGING CORRELATION DATA ===")
    
    # Check sample POS equipment data
    print("\n1. Sample POS Equipment Data:")
    cursor.execute("SELECT item_num, name, qty FROM pos_equipment LIMIT 10")
    pos_sample = cursor.fetchall()
    for item in pos_sample:
        print(f"  ItemNum: {item['item_num']}, Qty: {item['qty']}, Name: {item['name'][:50]}...")
    
    # Check sample seed data
    print("\n2. Sample Seed Data:")
    cursor.execute("SELECT rental_class_id, common_name FROM seed_rental_classes LIMIT 10")
    seed_sample = cursor.fetchall()
    for item in seed_sample:
        print(f"  ClassID: {item['rental_class_id']}, Name: {item['common_name'][:50]}...")
    
    # Check for direct matches
    print("\n3. Direct ItemNum Matches:")
    cursor.execute("""
        SELECT pe.item_num, pe.name, pe.qty, sd.common_name
        FROM pos_equipment pe
        JOIN seed_rental_classes sd ON pe.item_num = sd.rental_class_id
        LIMIT 10
    """)
    matches = cursor.fetchall()
    if matches:
        print(f"Found {len(matches)} direct matches:")
        for match in matches:
            print(f"  {match['item_num']}: POS='{match['name'][:30]}...' | SEED='{match['common_name'][:30]}...' | Qty={match['qty']}")
    else:
        print("  No direct matches found!")
    
    # Check id_item_master counts
    print("\n4. RFID Item Master Sample:")
    cursor.execute("""
        SELECT rental_class_num, COUNT(*) as tag_count, 
               GROUP_CONCAT(DISTINCT common_name LIMIT 3) as sample_names
        FROM id_item_master 
        WHERE rental_class_num IS NOT NULL
        GROUP BY rental_class_num 
        LIMIT 10
    """)
    rfid_sample = cursor.fetchall()
    if rfid_sample:
        for item in rfid_sample:
            print(f"  Class: {item['rental_class_num']}, Tags: {item['tag_count']}, Names: {item['sample_names']}")
    else:
        print("  No RFID item master data found!")
    
    # Check existing correlations
    print("\n5. Existing Correlations Sample:")
    cursor.execute("SELECT pos_item_num, pos_equipment_name, rfid_rental_class_num, rfid_common_name FROM equipment_rfid_correlations LIMIT 5")
    existing = cursor.fetchall()
    for corr in existing:
        print(f"  {corr['pos_item_num']}: {corr['pos_equipment_name'][:30]}...")
    
    # Check potential matches that might not be correlated yet
    print("\n6. Uncorrelated Potential Matches:")
    cursor.execute("""
        SELECT pe.item_num, pe.name, pe.qty, sd.common_name,
               (SELECT COUNT(*) FROM id_item_master im WHERE im.rental_class_num = sd.rental_class_id) as tag_count
        FROM pos_equipment pe
        JOIN seed_rental_classes sd ON pe.item_num = sd.rental_class_id
        LEFT JOIN equipment_rfid_correlations erc ON pe.item_num = erc.pos_item_num
        WHERE erc.id IS NULL
        LIMIT 10
    """)
    uncorrelated = cursor.fetchall()
    if uncorrelated:
        print(f"Found {len(uncorrelated)} uncorrelated matches:")
        for match in uncorrelated:
            print(f"  {match['item_num']}: Qty={match['qty']}, Tags={match['tag_count']}")
            print(f"    POS: {match['name'][:50]}")
            print(f"    SEED: {match['common_name'][:50]}")
    else:
        print("  All potential matches are already correlated!")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()