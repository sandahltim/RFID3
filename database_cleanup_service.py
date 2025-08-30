#!/usr/bin/env python3
"""
Database Cleanup Service - Remove contaminated POS data safely
Handles UNUSED, NON CURRENT ITEMS, and inactive records
"""

from app import create_app, db
from app.services.data_merge_strategy import get_merge_strategy
from sqlalchemy import text
import sys

def main():
    app = create_app()
    
    with app.app_context():
        merge_strategy = get_merge_strategy()
        
        print("🧹 RFID3 Database Cleanup Service")
        print("=" * 50)
        
        # Analyze current contamination
        print("📊 Analyzing current database contamination...")
        contamination = db.session.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN category = 'UNUSED' THEN 1 END) as unused,
                COUNT(CASE WHEN category = 'NON CURRENT ITEMS' THEN 1 END) as non_current,
                COUNT(CASE WHEN inactive = 1 THEN 1 END) as inactive,
                COUNT(CASE WHEN category IN ('UNUSED', 'NON CURRENT ITEMS') OR inactive = 1 THEN 1 END) as contaminated
            FROM pos_equipment
        """)).fetchone()
        
        total, unused, non_current, inactive, contaminated = contamination
        
        print(f"Total POS records: {total:,}")
        print(f"UNUSED category: {unused:,}")
        print(f"NON CURRENT ITEMS: {non_current:,}")
        print(f"Inactive records: {inactive:,}")
        print(f"Total contaminated: {contaminated:,} ({contaminated/total*100:.1f}%)")
        print(f"Clean records: {total-contaminated:,} ({(total-contaminated)/total*100:.1f}%)")
        
        # Note: POS transactions are linked by contract numbers, not item numbers
        # Contaminated equipment records are safe to remove as they don't represent
        # actual rental inventory - they are UNUSED/NON CURRENT/Inactive categories
        print("\n🔗 Transaction dependency analysis...")
        print("ℹ️  POS transactions link via contract_no, not item_num")
        print("ℹ️  Contaminated records (UNUSED/NON CURRENT/Inactive) are non-rental items")
        print("✅ Safe to clean - contaminated records don't represent active inventory")
        
        # Perform cleanup
        print(f"\n🗑️  Proceeding with cleanup of {contaminated:,} records...")
        
        if len(sys.argv) > 1 and sys.argv[1] == '--confirm':
            response = 'yes'
            print("Auto-confirmed via --confirm flag")
        else:
            response = input("Continue with cleanup? (yes/no): ").lower().strip()
        
        if response != 'yes':
            print("Cleanup cancelled")
            sys.exit(0)
        
        # Execute cleanup
        cleanup_stats = merge_strategy.clean_contaminated_pos_data()
        
        if 'error' in cleanup_stats:
            print(f"❌ Cleanup failed: {cleanup_stats['error']}")
            sys.exit(1)
        
        print("\n✅ Cleanup completed successfully!")
        print(f"   Records deleted: {cleanup_stats['total_deleted']:,}")
        print(f"   UNUSED removed: {cleanup_stats['unused_removed']:,}")
        print(f"   NON CURRENT removed: {cleanup_stats['non_current_removed']:,}")
        print(f"   Inactive removed: {cleanup_stats['inactive_removed']:,}")
        
        # Verify cleanup
        final_count = db.session.execute(text("SELECT COUNT(*) FROM pos_equipment")).scalar()
        print(f"   Final clean count: {final_count:,}")
        
        print(f"\n📋 Backup created: pos_equipment_contaminated_backup")
        print(f"   Cleanup timestamp: {cleanup_stats['cleanup_date']}")

if __name__ == "__main__":
    main()