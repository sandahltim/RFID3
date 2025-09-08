#!/usr/bin/env python3
"""Analyze database contamination before cleanup"""

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    # Current database stats
    result = db.session.execute(text('''
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN category = "UNUSED" THEN 1 END) as unused,
            COUNT(CASE WHEN category = "NON CURRENT ITEMS" THEN 1 END) as non_current,
            COUNT(CASE WHEN inactive = 1 THEN 1 END) as inactive,
            COUNT(CASE WHEN category IN ("UNUSED", "NON CURRENT ITEMS") OR inactive = 1 THEN 1 END) as contaminated
        FROM pos_equipment
    ''')).fetchone()
    
    print('=' * 60)
    print('DATABASE CONTAMINATION ANALYSIS - PHASE 2.5 CLEANUP')
    print('=' * 60)
    print('\nCURRENT DATABASE STATE:')
    print(f'  Total records: {result[0]:,}')
    print(f'  UNUSED category: {result[1]:,}')
    print(f'  NON CURRENT ITEMS: {result[2]:,}')
    print(f'  Inactive flag = TRUE: {result[3]:,}')
    print(f'\n  CONTAMINATED RECORDS: {result[4]:,} ({result[4]/result[0]*100:.1f}%)')
    print(f'  CLEAN RECORDS TO KEEP: {result[0]-result[4]:,} ({(result[0]-result[4])/result[0]*100:.1f}%)')
    
    # Sample of contaminated records
    print('\n--- SAMPLE OF CONTAMINATED RECORDS TO BE REMOVED ---')
    contaminated = db.session.execute(text('''
        SELECT item_num, name, category, inactive, turnover_ytd, turnover_ltd
        FROM pos_equipment
        WHERE category IN ("UNUSED", "NON CURRENT ITEMS") OR inactive = 1
        LIMIT 10
    ''')).fetchall()
    
    for row in contaminated:
        status = 'INACTIVE' if row[3] == 1 else 'ACTIVE'
        name = row[1][:35] if row[1] else "N/A"
        print(f'  [{status}] {row[0]}: {name:<35} | Cat: {row[2]:<20} | YTD: ${row[4] or 0:>8.2f} | LTD: ${row[5] or 0:>10.2f}')
    
    # Sample of clean records
    print('\n--- SAMPLE OF CLEAN RECORDS TO BE KEPT ---')
    clean = db.session.execute(text('''
        SELECT item_num, name, category, inactive, turnover_ytd, turnover_ltd
        FROM pos_equipment
        WHERE category NOT IN ("UNUSED", "NON CURRENT ITEMS") AND (inactive = 0 OR inactive IS NULL)
        ORDER BY turnover_ytd DESC
        LIMIT 10
    ''')).fetchall()
    
    for row in clean:
        status = 'INACTIVE' if row[3] == 1 else 'ACTIVE'
        name = row[1][:35] if row[1] else "N/A"
        print(f'  [{status}] {row[0]}: {name:<35} | Cat: {row[2]:<20} | YTD: ${row[4] or 0:>8.2f} | LTD: ${row[5] or 0:>10.2f}')
    
    # Check for any subcategory data
    print('\n--- CATEGORY DISTRIBUTION ---')
    categories = db.session.execute(text('''
        SELECT category, COUNT(*) as count
        FROM pos_equipment
        GROUP BY category
        ORDER BY count DESC
        LIMIT 10
    ''')).fetchall()
    
    for cat in categories:
        print(f'  {cat[0] or "NULL":<30}: {cat[1]:,} records')
    
    # Check backup status
    print('\n--- BACKUP TABLE STATUS ---')
    try:
        backup_count = db.session.execute(text('SELECT COUNT(*) FROM pos_equipment_contaminated_backup')).scalar()
        print(f'  Existing backup table has {backup_count:,} records')
    except:
        print('  No backup table exists yet (will be created during cleanup)')