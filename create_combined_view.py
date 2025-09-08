#!/usr/bin/env python3
"""
Create Combined Inventory View
Executes the database migration to create the combined inventory view
"""

import os
os.environ['FLASK_SKIP_SCHEDULER'] = '1'

from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("🚀 Creating combined inventory view...")
    
    # Read the SQL migration
    with open('migrations/create_combined_inventory_view.sql', 'r') as f:
        sql_content = f.read()
    
    # Remove comments and split statements properly
    lines = [line for line in sql_content.split('\n') if line.strip() and not line.strip().startswith('--')]
    cleaned_sql = '\n'.join(lines)
    
    # Split by semicolons but handle multi-line statements
    statements = []
    current_stmt = ""
    
    for line in cleaned_sql.split('\n'):
        current_stmt += line + '\n'
        if line.strip().endswith(';'):
            statements.append(current_stmt.strip())
            current_stmt = ""
    
    for i, stmt in enumerate(statements, 1):
        try:
            if stmt and not stmt.startswith('--'):
                db.session.execute(text(stmt))
                print(f"✅ Statement {i}: {stmt.split()[0]} {stmt.split()[1] if len(stmt.split()) > 1 else ''}...")
        except Exception as e:
            print(f"⚠️ Error in statement {i}: {e}")
            print(f"Statement preview: {stmt[:150]}...")
    
    try:
        db.session.commit()
        print("🏁 Combined inventory view creation completed successfully")
        
        # Test the view
        result = db.session.execute(text("SELECT COUNT(*) as total FROM combined_inventory")).fetchone()
        print(f"📊 Combined inventory view contains {result[0]} equipment items")
        
        # Sample data quality check
        quality_check = db.session.execute(text("""
            SELECT 
                data_quality_flag,
                COUNT(*) as count
            FROM combined_inventory 
            GROUP BY data_quality_flag
            ORDER BY count DESC
        """)).fetchall()
        
        print("📈 Data Quality Breakdown:")
        for row in quality_check:
            print(f"   {row[0]}: {row[1]} items")
            
    except Exception as e:
        print(f"❌ Error committing transaction: {e}")
        db.session.rollback()