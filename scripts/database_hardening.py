#!/usr/bin/env python3
"""
Database Hardening Script - Applies optimizations and fixes based on validation results
RFID3 System - Production Hardening Suite
"""

import sys
import os
import time
from datetime import datetime
from sqlalchemy import text
import pandas as pd
import numpy as np

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

class DatabaseHardening:
    """Apply database optimizations and fixes"""
    
    def __init__(self):
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'optimizations_applied': [],
            'errors': [],
            'warnings': []
        }
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.app_context.pop()
        
    def apply_all_optimizations(self, fix_data=False):
        """Apply all database optimizations"""
        print("\n" + "="*80)
        print("RFID3 DATABASE HARDENING")
        print("="*80)
        
        # 1. Create missing indexes
        print("\n[1/5] Creating Performance Indexes...")
        self.create_indexes()
        
        # 2. Add integrity constraints
        print("\n[2/5] Adding Integrity Constraints...")
        self.add_constraints()
        
        # 3. Clean orphaned data (if requested)
        if fix_data:
            print("\n[3/5] Cleaning Orphaned Data...")
            self.clean_orphaned_data()
        else:
            print("\n[3/5] Skipping Data Cleanup (fix_data=False)...")
            
        # 4. Optimize queries with views
        print("\n[4/5] Creating Optimized Views...")
        self.create_optimized_views()
        
        # 5. Update statistics
        print("\n[5/5] Updating Database Statistics...")
        self.update_statistics()
        
        return self.results
        
    def create_indexes(self):
        """Create performance-critical indexes"""
        indexes = [
            # Core table indexes
            {
                'name': 'idx_item_master_tag',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_item_master_tag ON id_item_master(tag_id)'
            },
            {
                'name': 'idx_item_master_store',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_item_master_store ON id_item_master(current_store)'
            },
            {
                'name': 'idx_item_master_turnover',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_item_master_turnover ON id_item_master(turnover_ytd)'
            },
            {
                'name': 'idx_item_master_composite',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_item_master_composite ON id_item_master(current_store, turnover_ytd)'
            },
            
            # Transaction indexes
            {
                'name': 'idx_transactions_tag',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_transactions_tag ON id_transactions(tag_id)'
            },
            {
                'name': 'idx_transactions_date',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_transactions_date ON id_transactions(scan_date)'
            },
            {
                'name': 'idx_transactions_composite',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_transactions_composite ON id_transactions(tag_id, scan_date)'
            },
            
            # P&L indexes
            {
                'name': 'idx_pnl_store',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_pnl_store ON pos_pnl(store_id)'
            },
            {
                'name': 'idx_pnl_date',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_pnl_date ON pos_pnl(year, month)'
            },
            {
                'name': 'idx_pnl_composite',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_pnl_composite ON pos_pnl(store_id, year, month)'
            },
            
            # Correlation indexes
            {
                'name': 'idx_correlations_value',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_correlations_value ON pos_rfid_correlations(correlation_value)'
            },
            {
                'name': 'idx_correlations_pvalue',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_correlations_pvalue ON pos_rfid_correlations(p_value)'
            },
            {
                'name': 'idx_correlations_composite',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_correlations_composite ON pos_rfid_correlations(correlation_value, p_value, factor_name)'
            },
            
            # External factors indexes
            {
                'name': 'idx_external_factors_date',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_external_factors_date ON external_factors(date)'
            },
            
            # POS indexes
            {
                'name': 'idx_pos_equipment_customer',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_pos_equipment_customer ON pos_equipment(customer_id)'
            },
            {
                'name': 'idx_pos_transactions_customer',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_pos_transactions_customer ON pos_transactions(customer_id)'
            },
            {
                'name': 'idx_pos_transaction_items',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_pos_transaction_items ON pos_transaction_items(transaction_id)'
            }
        ]
        
        for index in indexes:
            try:
                db.session.execute(text(index['sql']))
                db.session.commit()
                self.results['optimizations_applied'].append({
                    'type': 'index',
                    'name': index['name'],
                    'status': 'SUCCESS'
                })
                print(f"  ✓ Created index: {index['name']}")
            except Exception as e:
                self.results['errors'].append({
                    'type': 'index',
                    'name': index['name'],
                    'error': str(e)
                })
                print(f"  ✗ Failed to create index {index['name']}: {str(e)}")
                
    def add_constraints(self):
        """Add data integrity constraints"""
        # Note: SQLite has limited support for adding constraints to existing tables
        # We'll create triggers to enforce constraints
        
        constraints = [
            # Prevent duplicate tag_ids
            {
                'name': 'unique_tag_trigger',
                'sql': """
                CREATE TRIGGER IF NOT EXISTS enforce_unique_tag
                BEFORE INSERT ON id_item_master
                BEGIN
                    SELECT CASE
                        WHEN (SELECT COUNT(*) FROM id_item_master WHERE tag_id = NEW.tag_id) > 0
                        THEN RAISE(ABORT, 'Duplicate tag_id')
                    END;
                END;
                """
            },
            
            # Ensure foreign key integrity for transactions
            {
                'name': 'fk_transaction_tag',
                'sql': """
                CREATE TRIGGER IF NOT EXISTS enforce_transaction_tag_fk
                BEFORE INSERT ON id_transactions
                BEGIN
                    SELECT CASE
                        WHEN NEW.tag_id IS NOT NULL 
                        AND (SELECT COUNT(*) FROM id_item_master WHERE tag_id = NEW.tag_id) = 0
                        THEN RAISE(ABORT, 'Foreign key violation: tag_id not found in id_item_master')
                    END;
                END;
                """
            },
            
            # Validate P&L calculations
            {
                'name': 'pnl_calculation_check',
                'sql': """
                CREATE TRIGGER IF NOT EXISTS validate_pnl_calculations
                BEFORE INSERT ON pos_pnl
                BEGIN
                    SELECT CASE
                        WHEN NEW.revenue IS NOT NULL 
                        AND NEW.cogs IS NOT NULL 
                        AND NEW.gross_profit IS NOT NULL
                        AND ABS(NEW.gross_profit - (NEW.revenue - NEW.cogs)) > 0.01
                        THEN RAISE(ABORT, 'P&L calculation error: gross_profit != revenue - cogs')
                    END;
                END;
                """
            }
        ]
        
        for constraint in constraints:
            try:
                db.session.execute(text(constraint['sql']))
                db.session.commit()
                self.results['optimizations_applied'].append({
                    'type': 'constraint',
                    'name': constraint['name'],
                    'status': 'SUCCESS'
                })
                print(f"  ✓ Added constraint: {constraint['name']}")
            except Exception as e:
                self.results['errors'].append({
                    'type': 'constraint',
                    'name': constraint['name'],
                    'error': str(e)
                })
                print(f"  ✗ Failed to add constraint {constraint['name']}: {str(e)}")
                
    def clean_orphaned_data(self):
        """Clean orphaned records from the database"""
        
        # Count orphaned transactions first
        count_query = """
        SELECT COUNT(*) 
        FROM id_transactions t
        LEFT JOIN id_item_master im ON t.tag_id = im.tag_id
        WHERE im.tag_id IS NULL
        """
        
        try:
            orphan_count = db.session.execute(text(count_query)).scalar()
            
            if orphan_count > 0:
                # Create backup table first
                backup_query = """
                CREATE TABLE IF NOT EXISTS orphaned_transactions_backup AS
                SELECT t.*
                FROM id_transactions t
                LEFT JOIN id_item_master im ON t.tag_id = im.tag_id
                WHERE im.tag_id IS NULL
                """
                
                db.session.execute(text(backup_query))
                
                # Delete orphaned records
                delete_query = """
                DELETE FROM id_transactions
                WHERE tag_id NOT IN (SELECT tag_id FROM id_item_master)
                """
                
                db.session.execute(text(delete_query))
                db.session.commit()
                
                self.results['optimizations_applied'].append({
                    'type': 'cleanup',
                    'name': 'orphaned_transactions',
                    'records_cleaned': orphan_count,
                    'status': 'SUCCESS'
                })
                print(f"  ✓ Cleaned {orphan_count} orphaned transactions (backed up)")
            else:
                print(f"  ✓ No orphaned transactions found")
                
        except Exception as e:
            self.results['errors'].append({
                'type': 'cleanup',
                'name': 'orphaned_transactions',
                'error': str(e)
            })
            print(f"  ✗ Failed to clean orphaned transactions: {str(e)}")
            
        # Clean duplicate tags (keeping the first occurrence)
        try:
            duplicate_query = """
            WITH duplicates AS (
                SELECT tag_id, MIN(rowid) as keep_rowid
                FROM id_item_master
                GROUP BY tag_id
                HAVING COUNT(*) > 1
            )
            SELECT COUNT(*) 
            FROM id_item_master
            WHERE tag_id IN (SELECT tag_id FROM duplicates)
                AND rowid NOT IN (SELECT keep_rowid FROM duplicates)
            """
            
            duplicate_count = db.session.execute(text(duplicate_query)).scalar()
            
            if duplicate_count > 0:
                # Create backup
                backup_duplicates = """
                CREATE TABLE IF NOT EXISTS duplicate_tags_backup AS
                WITH duplicates AS (
                    SELECT tag_id, MIN(rowid) as keep_rowid
                    FROM id_item_master
                    GROUP BY tag_id
                    HAVING COUNT(*) > 1
                )
                SELECT *
                FROM id_item_master
                WHERE tag_id IN (SELECT tag_id FROM duplicates)
                    AND rowid NOT IN (SELECT keep_rowid FROM duplicates)
                """
                
                db.session.execute(text(backup_duplicates))
                
                # Delete duplicates
                delete_duplicates = """
                WITH duplicates AS (
                    SELECT tag_id, MIN(rowid) as keep_rowid
                    FROM id_item_master
                    GROUP BY tag_id
                    HAVING COUNT(*) > 1
                )
                DELETE FROM id_item_master
                WHERE tag_id IN (SELECT tag_id FROM duplicates)
                    AND rowid NOT IN (SELECT keep_rowid FROM duplicates)
                """
                
                db.session.execute(text(delete_duplicates))
                db.session.commit()
                
                self.results['optimizations_applied'].append({
                    'type': 'cleanup',
                    'name': 'duplicate_tags',
                    'records_cleaned': duplicate_count,
                    'status': 'SUCCESS'
                })
                print(f"  ✓ Cleaned {duplicate_count} duplicate tags (backed up)")
            else:
                print(f"  ✓ No duplicate tags found")
                
        except Exception as e:
            self.results['errors'].append({
                'type': 'cleanup',
                'name': 'duplicate_tags',
                'error': str(e)
            })
            print(f"  ✗ Failed to clean duplicate tags: {str(e)}")
            
    def create_optimized_views(self):
        """Create optimized views for common queries"""
        views = [
            {
                'name': 'v_store_performance',
                'sql': """
                CREATE VIEW IF NOT EXISTS v_store_performance AS
                SELECT 
                    current_store,
                    COUNT(*) as total_items,
                    AVG(turnover_ytd) as avg_turnover,
                    SUM(turnover_ytd) as total_turnover,
                    MIN(turnover_ytd) as min_turnover,
                    MAX(turnover_ytd) as max_turnover
                FROM id_item_master
                GROUP BY current_store
                """
            },
            {
                'name': 'v_pnl_summary',
                'sql': """
                CREATE VIEW IF NOT EXISTS v_pnl_summary AS
                SELECT 
                    store_id,
                    year,
                    AVG(revenue) as avg_monthly_revenue,
                    SUM(revenue) as total_revenue,
                    AVG(gross_profit) as avg_monthly_profit,
                    SUM(gross_profit) as total_profit,
                    AVG(gross_margin) as avg_margin
                FROM pos_pnl
                GROUP BY store_id, year
                """
            },
            {
                'name': 'v_significant_correlations',
                'sql': """
                CREATE VIEW IF NOT EXISTS v_significant_correlations AS
                SELECT 
                    factor_name,
                    correlation_value,
                    p_value,
                    lag_days,
                    CASE 
                        WHEN ABS(correlation_value) > 0.7 THEN 'STRONG'
                        WHEN ABS(correlation_value) > 0.5 THEN 'MODERATE'
                        ELSE 'WEAK'
                    END as strength
                FROM pos_rfid_correlations
                WHERE ABS(correlation_value) > 0.5 
                    AND p_value < 0.05
                ORDER BY ABS(correlation_value) DESC
                """
            },
            {
                'name': 'v_inventory_health',
                'sql': """
                CREATE VIEW IF NOT EXISTS v_inventory_health AS
                SELECT 
                    im.current_store,
                    COUNT(DISTINCT im.tag_id) as unique_items,
                    COUNT(t.transaction_id) as total_transactions,
                    AVG(CASE 
                        WHEN t.scan_date IS NOT NULL 
                        THEN JULIANDAY('now') - JULIANDAY(t.scan_date)
                        ELSE NULL 
                    END) as avg_days_since_scan,
                    SUM(im.turnover_ytd) as total_turnover
                FROM id_item_master im
                LEFT JOIN id_transactions t ON im.tag_id = t.tag_id
                GROUP BY im.current_store
                """
            }
        ]
        
        for view in views:
            try:
                # Drop existing view if it exists
                db.session.execute(text(f"DROP VIEW IF EXISTS {view['name']}"))
                # Create new view
                db.session.execute(text(view['sql']))
                db.session.commit()
                
                self.results['optimizations_applied'].append({
                    'type': 'view',
                    'name': view['name'],
                    'status': 'SUCCESS'
                })
                print(f"  ✓ Created view: {view['name']}")
            except Exception as e:
                self.results['errors'].append({
                    'type': 'view',
                    'name': view['name'],
                    'error': str(e)
                })
                print(f"  ✗ Failed to create view {view['name']}: {str(e)}")
                
    def update_statistics(self):
        """Update database statistics for query optimization"""
        try:
            # Run ANALYZE to update SQLite statistics
            db.session.execute(text("ANALYZE"))
            
            # Vacuum to reclaim space and optimize database file
            db.session.execute(text("VACUUM"))
            
            db.session.commit()
            
            self.results['optimizations_applied'].append({
                'type': 'statistics',
                'name': 'database_statistics',
                'status': 'SUCCESS'
            })
            print(f"  ✓ Updated database statistics and optimized storage")
            
        except Exception as e:
            self.results['errors'].append({
                'type': 'statistics',
                'name': 'database_statistics',
                'error': str(e)
            })
            print(f"  ✗ Failed to update statistics: {str(e)}")
            
    def verify_optimizations(self):
        """Verify that optimizations were applied successfully"""
        verification_results = {}
        
        # Check indexes
        index_query = """
        SELECT name FROM sqlite_master 
        WHERE type = 'index' AND sql IS NOT NULL
        """
        
        try:
            indexes = db.session.execute(text(index_query)).fetchall()
            verification_results['indexes'] = {
                'count': len(indexes),
                'names': [idx[0] for idx in indexes]
            }
        except Exception as e:
            verification_results['indexes'] = {'error': str(e)}
            
        # Check views
        view_query = """
        SELECT name FROM sqlite_master 
        WHERE type = 'view'
        """
        
        try:
            views = db.session.execute(text(view_query)).fetchall()
            verification_results['views'] = {
                'count': len(views),
                'names': [view[0] for view in views]
            }
        except Exception as e:
            verification_results['views'] = {'error': str(e)}
            
        # Check triggers
        trigger_query = """
        SELECT name FROM sqlite_master 
        WHERE type = 'trigger'
        """
        
        try:
            triggers = db.session.execute(text(trigger_query)).fetchall()
            verification_results['triggers'] = {
                'count': len(triggers),
                'names': [trigger[0] for trigger in triggers]
            }
        except Exception as e:
            verification_results['triggers'] = {'error': str(e)}
            
        return verification_results


def main():
    """Main execution function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='RFID3 Database Hardening Script')
    parser.add_argument('--fix-data', action='store_true', 
                       help='Actually fix data issues (clean orphaned records, etc.)')
    parser.add_argument('--verify-only', action='store_true',
                       help='Only verify existing optimizations without applying new ones')
    
    args = parser.parse_args()
    
    print("Starting RFID3 Database Hardening...")
    
    with DatabaseHardening() as hardener:
        if args.verify_only:
            print("\n" + "="*80)
            print("VERIFICATION MODE - Checking Existing Optimizations")
            print("="*80)
            
            verification = hardener.verify_optimizations()
            
            print(f"\n✓ Indexes: {verification.get('indexes', {}).get('count', 0)}")
            print(f"✓ Views: {verification.get('views', {}).get('count', 0)}")
            print(f"✓ Triggers: {verification.get('triggers', {}).get('count', 0)}")
            
            # List specific items
            if verification.get('indexes', {}).get('names'):
                print("\nIndexes found:")
                for idx in verification['indexes']['names'][:10]:
                    print(f"  - {idx}")
                    
            if verification.get('views', {}).get('names'):
                print("\nViews found:")
                for view in verification['views']['names']:
                    print(f"  - {view}")
                    
        else:
            results = hardener.apply_all_optimizations(fix_data=args.fix_data)
            
            # Print summary
            print(f"\n{'='*80}")
            print("HARDENING SUMMARY")
            print('='*80)
            
            print(f"\n✓ Optimizations Applied: {len(results['optimizations_applied'])}")
            print(f"✗ Errors: {len(results['errors'])}")
            print(f"⚠ Warnings: {len(results['warnings'])}")
            
            if results['errors']:
                print("\nErrors encountered:")
                for error in results['errors'][:5]:
                    print(f"  - {error['type']}/{error['name']}: {error['error'][:100]}")
                    
            # Verify after applying
            print(f"\n{'='*80}")
            print("POST-HARDENING VERIFICATION")
            print('='*80)
            
            verification = hardener.verify_optimizations()
            print(f"\n✓ Total Indexes: {verification.get('indexes', {}).get('count', 0)}")
            print(f"✓ Total Views: {verification.get('views', {}).get('count', 0)}")
            print(f"✓ Total Triggers: {verification.get('triggers', {}).get('count', 0)}")
            
            print(f"\n{'='*80}")
            print("DATABASE HARDENING COMPLETE")
            print('='*80)
            
    return 0


if __name__ == "__main__":
    exit(main())