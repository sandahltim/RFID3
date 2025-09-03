#!/usr/bin/env python3
"""Check dependencies before cleanup"""

from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    # Check for any relationships or dependencies
    print('CHECKING DEPENDENCIES AND RELATIONSHIPS:')
    print('=' * 50)
    
    # Check if there are any POS transactions that reference these items
    print('\n1. POS TRANSACTIONS TABLE:')
    try:
        trans_count = db.session.execute(text('SELECT COUNT(*) FROM pos_transactions')).scalar()
        print(f'   Total POS transactions: {trans_count:,}')
        
        # Check how transactions link (by contract_no not item_num)
        sample_trans = db.session.execute(text('''
            SELECT contract_no, item_num, store_code, date_out, date_in
            FROM pos_transactions
            LIMIT 5
        ''')).fetchall()
        
        print('   Sample transactions (showing linking via contract_no):')
        for t in sample_trans:
            print(f'     Contract: {t[0]}, Item: {t[1]}, Store: {t[2]}, Out: {t[3]}, In: {t[4]}')
            
    except Exception as e:
        print(f'   No pos_transactions table or error: {e}')
    
    # Check stores table
    print('\n2. STORES TABLE:')
    try:
        stores = db.session.execute(text('SELECT store_code, store_name FROM stores')).fetchall()
        print(f'   Active stores: {len(stores)}')
        for s in stores[:3]:
            print(f'     {s[0]}: {s[1]}')
    except Exception as e:
        print(f'   Error checking stores: {e}')
    
    # Check if contaminated items have any turnover
    print('\n3. CONTAMINATED ITEMS WITH REVENUE:')
    revenue_check = db.session.execute(text('''
        SELECT COUNT(*), SUM(turnover_ytd), SUM(turnover_ltd)
        FROM pos_equipment
        WHERE (category IN ("UNUSED", "NON CURRENT ITEMS") OR inactive = 1)
        AND (turnover_ytd > 0 OR turnover_ltd > 0)
    ''')).fetchone()
    
    print(f'   Contaminated items with revenue: {revenue_check[0]:,}')
    print(f'   Total YTD revenue from contaminated: ${revenue_check[1] or 0:,.2f}')
    print(f'   Total LTD revenue from contaminated: ${revenue_check[2] or 0:,.2f}')
    
    # Check clean items revenue
    print('\n4. CLEAN ITEMS REVENUE:')
    clean_revenue = db.session.execute(text('''
        SELECT COUNT(*), SUM(turnover_ytd), SUM(turnover_ltd)
        FROM pos_equipment
        WHERE category NOT IN ("UNUSED", "NON CURRENT ITEMS") 
        AND (inactive = 0 OR inactive IS NULL)
    ''')).fetchall()[0]
    
    print(f'   Clean items count: {clean_revenue[0]:,}')
    print(f'   Total YTD revenue from clean: ${clean_revenue[1] or 0:,.2f}')
    print(f'   Total LTD revenue from clean: ${clean_revenue[2] or 0:,.2f}')