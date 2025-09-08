#!/usr/bin/env python3
"""
Database Optimization for Tab 6 (Inventory Analytics)
Addresses performance issues and missing indexes
"""

from app import create_app, db
from sqlalchemy import text, Index
from app.models.db_models import ItemMaster, Transaction, UserRentalClassMapping
import time

def create_missing_indexes():
    """Create indexes to optimize Tab 6 queries"""
    
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("DATABASE OPTIMIZATION FOR TAB 6")
        print("=" * 60)
        
        indexes_to_create = [
            # For resale tracking queries
            ("CREATE INDEX IF NOT EXISTS idx_urcm_category ON user_rental_class_mappings(category)", 
             "Category index for resale filtering"),
            
            # For usage analysis joins
            ("CREATE INDEX IF NOT EXISTS idx_im_rental_class ON id_item_master(rental_class_num)", 
             "Rental class index for joins"),
            
            # For transaction date filtering
            ("CREATE INDEX IF NOT EXISTS idx_trans_scan_date ON id_transactions(scan_date)",
             "Transaction date index for time-based queries"),
            
            # Composite index for resale queries
            ("CREATE INDEX IF NOT EXISTS idx_urcm_cat_subcat ON user_rental_class_mappings(category, subcategory)",
             "Composite index for category/subcategory filtering"),
            
            # For usage history queries
            ("CREATE INDEX IF NOT EXISTS idx_usage_event_date ON item_usage_history(event_date)",
             "Usage history date index"),
            
            ("CREATE INDEX IF NOT EXISTS idx_usage_tag_event ON item_usage_history(tag_id, event_type)",
             "Composite index for usage history lookups"),
        ]
        
        print("\nCreating indexes...")
        for sql, description in indexes_to_create:
            try:
                print(f"  Creating: {description}...")
                start = time.time()
                db.session.execute(text(sql))
                db.session.commit()
                elapsed = time.time() - start
                print(f"    ✓ Created in {elapsed:.2f} seconds")
            except Exception as e:
                print(f"    ✗ Error: {str(e)}")
                db.session.rollback()
        
        print("\n" + "=" * 60)
        print("INDEX VERIFICATION")
        print("=" * 60)
        
        # Verify indexes
        tables = ['id_item_master', 'id_transactions', 'user_rental_class_mappings', 'item_usage_history']
        
        for table in tables:
            try:
                result = db.session.execute(text(f"SHOW INDEX FROM {table}"))
                indexes = result.fetchall()
                print(f"\n{table}:")
                unique_indexes = set()
                for idx in indexes:
                    index_name = idx[2]  # Key_name is at position 2
                    column_name = idx[4]  # Column_name is at position 4
                    if index_name not in unique_indexes:
                        print(f"  - {index_name} on {column_name}")
                        unique_indexes.add(index_name)
            except Exception as e:
                print(f"  Error checking indexes: {str(e)}")

def analyze_query_performance():
    """Analyze performance of key Tab 6 queries"""
    
    app = create_app()
    with app.app_context():
        print("\n" + "=" * 60)
        print("QUERY PERFORMANCE ANALYSIS")
        print("=" * 60)
        
        queries = [
            ("Resale Items Count", """
                SELECT COUNT(DISTINCT im.tag_id) 
                FROM id_item_master im
                JOIN user_rental_class_mappings urcm ON im.rental_class_num = urcm.rental_class_id
                WHERE urcm.category = 'Resale'
            """),
            
            ("Usage Patterns", """
                SELECT urcm.category, COUNT(DISTINCT t.tag_id) as item_count
                FROM user_rental_class_mappings urcm
                JOIN id_item_master im ON urcm.rental_class_id = im.rental_class_num
                JOIN id_transactions t ON im.tag_id = t.tag_id
                WHERE t.scan_date >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                GROUP BY urcm.category
                LIMIT 10
            """),
            
            ("Stale Items", """
                SELECT COUNT(*) FROM id_item_master 
                WHERE status = 'Ready to Rent' 
                AND date_last_scanned < DATE_SUB(NOW(), INTERVAL 30 DAY)
            """),
        ]
        
        for name, query in queries:
            try:
                print(f"\nTesting: {name}")
                start = time.time()
                result = db.session.execute(text(query))
                rows = result.fetchall()
                elapsed = time.time() - start
                print(f"  Results: {len(rows)} rows")
                print(f"  Time: {elapsed:.3f} seconds")
                
                if elapsed > 1.0:
                    print(f"  ⚠ SLOW QUERY - Consider optimization")
                else:
                    print(f"  ✓ Performance acceptable")
                    
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")

def fix_data_relationships():
    """Fix missing rental class mappings"""
    
    app = create_app()
    with app.app_context():
        print("\n" + "=" * 60)
        print("DATA RELATIONSHIP FIXES")
        print("=" * 60)
        
        # Count items with null rental_class_num
        null_count = db.session.query(func.count(ItemMaster.tag_id)).filter(
            ItemMaster.rental_class_num.is_(None)
        ).scalar()
        
        print(f"Items with NULL rental_class_num: {null_count}")
        
        if null_count > 0:
            print("\nAttempting to fix NULL rental_class_num values...")
            
            # Try to infer rental class from common_name patterns
            updates = 0
            
            # Get sample of items with null rental class
            null_items = db.session.query(ItemMaster).filter(
                ItemMaster.rental_class_num.is_(None)
            ).limit(100).all()
            
            for item in null_items:
                # Try to match based on common_name
                if item.common_name:
                    # Look for similar items with rental class
                    similar = db.session.query(ItemMaster).filter(
                        ItemMaster.common_name == item.common_name,
                        ItemMaster.rental_class_num.isnot(None)
                    ).first()
                    
                    if similar:
                        item.rental_class_num = similar.rental_class_num
                        updates += 1
            
            if updates > 0:
                db.session.commit()
                print(f"  ✓ Updated {updates} items with inferred rental_class_num")
            else:
                print("  ℹ Could not infer rental class values - manual mapping required")
        
        # Check for unmapped rental classes
        unmapped_query = text("""
            SELECT DISTINCT im.rental_class_num, COUNT(*) as item_count
            FROM id_item_master im
            LEFT JOIN user_rental_class_mappings urcm ON im.rental_class_num = urcm.rental_class_id
            WHERE im.rental_class_num IS NOT NULL
            AND urcm.rental_class_id IS NULL
            GROUP BY im.rental_class_num
            LIMIT 10
        """)
        
        result = db.session.execute(unmapped_query)
        unmapped = result.fetchall()
        
        if unmapped:
            print(f"\nFound {len(unmapped)} unmapped rental classes:")
            for rental_class, count in unmapped:
                print(f"  - Rental Class {rental_class}: {count} items")
            print("\n  ⚠ These rental classes need category/subcategory mappings")

def main():
    print("\nTAB 6 DATABASE OPTIMIZATION SUITE")
    print("=" * 60)
    
    # Run all optimizations
    create_missing_indexes()
    analyze_query_performance()
    fix_data_relationships()
    
    print("\n" + "=" * 60)
    print("OPTIMIZATION COMPLETE")
    print("=" * 60)
    print("\nRecommendations:")
    print("1. Run populate_usage_history.py to generate usage data")
    print("2. Review unmapped rental classes and add mappings")
    print("3. Consider archiving old transactions for better performance")
    print("4. Monitor slow queries and add indexes as needed")

if __name__ == "__main__":
    from sqlalchemy import func
    main()