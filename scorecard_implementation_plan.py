#!/usr/bin/env python3
"""
Scorecard Data Implementation Plan
Executable implementation scripts for database optimization and dashboard integration
"""

from app import create_app, db
from app.models.financial_models import ScorecardTrendsData
from sqlalchemy import text, Index, UniqueConstraint, CheckConstraint
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_data_quality_issues():
    """Fix immediate data quality issues in scorecard data"""
    logger.info("Fixing data quality issues...")
    
    try:
        # 1. Fix revenue mismatches
        query = text("""
            UPDATE scorecard_trends_data
            SET total_weekly_revenue = COALESCE(revenue_3607, 0) + 
                                      COALESCE(revenue_6800, 0) + 
                                      COALESCE(revenue_728, 0) + 
                                      COALESCE(revenue_8101, 0)
            WHERE ABS(total_weekly_revenue - (COALESCE(revenue_3607, 0) + 
                                             COALESCE(revenue_6800, 0) + 
                                             COALESCE(revenue_728, 0) + 
                                             COALESCE(revenue_8101, 0))) > 1
        """)
        result = db.session.execute(query)
        db.session.commit()
        logger.info(f"Fixed {result.rowcount} revenue mismatches")
        
        # 2. Fill missing AR percentages with 0
        query = text("""
            UPDATE scorecard_trends_data
            SET ar_over_45_days_percent = 0
            WHERE ar_over_45_days_percent IS NULL
        """)
        result = db.session.execute(query)
        db.session.commit()
        logger.info(f"Fixed {result.rowcount} null AR percentages")
        
        # 3. Fill missing discount values with 0
        query = text("""
            UPDATE scorecard_trends_data
            SET total_discount = 0
            WHERE total_discount IS NULL
        """)
        result = db.session.execute(query)
        db.session.commit()
        logger.info(f"Fixed {result.rowcount} null discount values")
        
        return True
    except Exception as e:
        logger.error(f"Error fixing data quality: {str(e)}")
        db.session.rollback()
        return False

def create_store_master_table():
    """Create store location master table"""
    logger.info("Creating store master table...")
    
    try:
        # Create table
        create_table_sql = text("""
            CREATE TABLE IF NOT EXISTS store_location_master (
                store_code VARCHAR(10) PRIMARY KEY,
                store_name VARCHAR(100) NOT NULL,
                region VARCHAR(50),
                market_type VARCHAR(20),
                square_footage DECIMAL(10,2),
                employee_count INTEGER,
                opened_date DATE,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_region (region),
                INDEX idx_active (is_active)
            )
        """)
        db.session.execute(create_table_sql)
        
        # Insert store data
        insert_sql = text("""
            INSERT IGNORE INTO store_location_master 
            (store_code, store_name, region, market_type, is_active) VALUES
            ('3607', 'Wayzata', 'West Metro', 'Suburban', TRUE),
            ('6800', 'Brooklyn Park', 'North Metro', 'Suburban', TRUE),
            ('728', 'Elk River', 'North', 'Rural', TRUE),
            ('8101', 'Fridley', 'North Metro', 'Urban', TRUE)
        """)
        db.session.execute(insert_sql)
        db.session.commit()
        
        logger.info("Store master table created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating store master table: {str(e)}")
        db.session.rollback()
        return False

def add_database_constraints():
    """Add validation constraints to scorecard table"""
    logger.info("Adding database constraints...")
    
    try:
        # Add unique constraint on week_ending
        unique_sql = text("""
            ALTER TABLE scorecard_trends_data 
            ADD CONSTRAINT uc_week_ending UNIQUE (week_ending)
        """)
        db.session.execute(unique_sql)
        
        # Add check constraint for AR percentage
        check_ar_sql = text("""
            ALTER TABLE scorecard_trends_data 
            ADD CONSTRAINT chk_ar_percentage 
            CHECK (ar_over_45_days_percent >= 0 AND ar_over_45_days_percent <= 100)
        """)
        db.session.execute(check_ar_sql)
        
        # Add check constraint for non-negative revenues
        check_revenue_sql = text("""
            ALTER TABLE scorecard_trends_data 
            ADD CONSTRAINT chk_positive_revenue 
            CHECK (total_weekly_revenue >= 0 AND 
                   COALESCE(revenue_3607, 0) >= 0 AND 
                   COALESCE(revenue_6800, 0) >= 0 AND 
                   COALESCE(revenue_728, 0) >= 0 AND 
                   COALESCE(revenue_8101, 0) >= 0)
        """)
        db.session.execute(check_revenue_sql)
        
        db.session.commit()
        logger.info("Constraints added successfully")
        return True
    except Exception as e:
        logger.error(f"Error adding constraints: {str(e)}")
        db.session.rollback()
        return False

def create_performance_indexes():
    """Create performance indexes for faster queries"""
    logger.info("Creating performance indexes...")
    
    try:
        # Composite index for time-series queries
        index1_sql = text("""
            CREATE INDEX IF NOT EXISTS idx_week_revenue 
            ON scorecard_trends_data (week_ending, total_weekly_revenue)
        """)
        db.session.execute(index1_sql)
        
        # Index for high AR risk queries
        index2_sql = text("""
            CREATE INDEX IF NOT EXISTS idx_ar_risk 
            ON scorecard_trends_data (ar_over_45_days_percent)
            WHERE ar_over_45_days_percent > 10
        """)
        db.session.execute(index2_sql)
        
        # Index for store-specific queries
        index3_sql = text("""
            CREATE INDEX IF NOT EXISTS idx_store_revenues 
            ON scorecard_trends_data 
            (revenue_3607, revenue_6800, revenue_728, revenue_8101)
        """)
        db.session.execute(index3_sql)
        
        db.session.commit()
        logger.info("Indexes created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating indexes: {str(e)}")
        db.session.rollback()
        return False

def create_analytics_views():
    """Create database views for analytics"""
    logger.info("Creating analytics views...")
    
    try:
        # Weekly performance view
        view1_sql = text("""
            CREATE OR REPLACE VIEW v_weekly_performance AS
            SELECT 
                s.week_ending,
                s.week_number,
                s.total_weekly_revenue,
                -- Store metrics
                COALESCE(s.revenue_3607, 0) as wayzata_revenue,
                COALESCE(s.revenue_6800, 0) as brooklyn_park_revenue,
                COALESCE(s.revenue_728, 0) as elk_river_revenue,
                COALESCE(s.revenue_8101, 0) as fridley_revenue,
                -- Contract metrics
                COALESCE(s.new_contracts_3607, 0) + 
                COALESCE(s.new_contracts_6800, 0) + 
                COALESCE(s.new_contracts_728, 0) + 
                COALESCE(s.new_contracts_8101, 0) as total_contracts,
                -- Pipeline metrics
                COALESCE(s.reservation_next14_3607, 0) + 
                COALESCE(s.reservation_next14_6800, 0) + 
                COALESCE(s.reservation_next14_728, 0) + 
                COALESCE(s.reservation_next14_8101, 0) as total_pipeline,
                -- Risk indicators
                s.ar_over_45_days_percent,
                CASE 
                    WHEN s.ar_over_45_days_percent > 20 THEN 'HIGH'
                    WHEN s.ar_over_45_days_percent > 10 THEN 'MEDIUM'
                    ELSE 'LOW'
                END as ar_risk_level,
                -- Revenue concentration
                GREATEST(
                    COALESCE(s.revenue_3607, 0),
                    COALESCE(s.revenue_6800, 0),
                    COALESCE(s.revenue_728, 0),
                    COALESCE(s.revenue_8101, 0)
                ) / NULLIF(s.total_weekly_revenue, 0) * 100 as max_store_concentration
            FROM scorecard_trends_data s
            ORDER BY s.week_ending DESC
        """)
        db.session.execute(view1_sql)
        
        # Store comparison view
        view2_sql = text("""
            CREATE OR REPLACE VIEW v_store_comparison AS
            SELECT 
                'Wayzata' as store_name,
                '3607' as store_code,
                SUM(revenue_3607) as total_revenue,
                SUM(new_contracts_3607) as total_contracts,
                AVG(revenue_3607 / NULLIF(new_contracts_3607, 0)) as avg_contract_value,
                COUNT(*) as weeks_of_data
            FROM scorecard_trends_data
            WHERE revenue_3607 > 0
            
            UNION ALL
            
            SELECT 
                'Brooklyn Park',
                '6800',
                SUM(revenue_6800),
                SUM(new_contracts_6800),
                AVG(revenue_6800 / NULLIF(new_contracts_6800, 0)),
                COUNT(*)
            FROM scorecard_trends_data
            WHERE revenue_6800 > 0
            
            UNION ALL
            
            SELECT 
                'Elk River',
                '728',
                SUM(revenue_728),
                SUM(new_contracts_728),
                AVG(revenue_728 / NULLIF(new_contracts_728, 0)),
                COUNT(*)
            FROM scorecard_trends_data
            WHERE revenue_728 > 0
            
            UNION ALL
            
            SELECT 
                'Fridley',
                '8101',
                SUM(revenue_8101),
                SUM(new_contracts_8101),
                AVG(revenue_8101 / NULLIF(new_contracts_8101, 0)),
                COUNT(*)
            FROM scorecard_trends_data
            WHERE revenue_8101 > 0
        """)
        db.session.execute(view2_sql)
        
        db.session.commit()
        logger.info("Analytics views created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating views: {str(e)}")
        db.session.rollback()
        return False

def create_correlation_metrics_table():
    """Create table for storing calculated correlations"""
    logger.info("Creating correlation metrics table...")
    
    try:
        create_sql = text("""
            CREATE TABLE IF NOT EXISTS scorecard_correlation_metrics (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                calculation_date DATE NOT NULL,
                metric_type VARCHAR(50) NOT NULL,
                store_code VARCHAR(10),
                correlation_value DECIMAL(5,3),
                sample_size INTEGER,
                confidence_level DECIMAL(3,2),
                p_value DECIMAL(6,4),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_calc_date (calculation_date),
                INDEX idx_metric_store (metric_type, store_code)
            )
        """)
        db.session.execute(create_sql)
        db.session.commit()
        
        logger.info("Correlation metrics table created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating correlation metrics table: {str(e)}")
        db.session.rollback()
        return False

def validate_implementation():
    """Validate that all changes were applied successfully"""
    logger.info("Validating implementation...")
    
    checks = []
    
    # Check if store master table exists
    try:
        result = db.session.execute(text("SELECT COUNT(*) FROM store_location_master"))
        count = result.scalar()
        checks.append(('Store master table', count == 4))
        logger.info(f"Store master table: {count} records")
    except:
        checks.append(('Store master table', False))
    
    # Check if constraints exist
    try:
        result = db.session.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.table_constraints 
            WHERE table_name = 'scorecard_trends_data' 
            AND constraint_type = 'UNIQUE'
        """))
        checks.append(('Unique constraints', result.scalar() > 0))
    except:
        checks.append(('Unique constraints', False))
    
    # Check if views exist
    try:
        result = db.session.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.views 
            WHERE table_name LIKE 'v_%'
        """))
        checks.append(('Analytics views', result.scalar() > 0))
    except:
        checks.append(('Analytics views', False))
    
    # Check data quality
    try:
        result = db.session.execute(text("""
            SELECT COUNT(*) 
            FROM scorecard_trends_data 
            WHERE ABS(total_weekly_revenue - (COALESCE(revenue_3607, 0) + 
                                             COALESCE(revenue_6800, 0) + 
                                             COALESCE(revenue_728, 0) + 
                                             COALESCE(revenue_8101, 0))) > 1
        """))
        mismatches = result.scalar()
        checks.append(('Revenue consistency', mismatches == 0))
        logger.info(f"Revenue mismatches: {mismatches}")
    except:
        checks.append(('Revenue consistency', False))
    
    # Print validation results
    logger.info("\nValidation Results:")
    all_passed = True
    for check_name, passed in checks:
        status = "PASS" if passed else "FAIL"
        logger.info(f"  {check_name}: {status}")
        if not passed:
            all_passed = False
    
    return all_passed

def main():
    """Execute implementation plan"""
    app = create_app()
    
    with app.app_context():
        logger.info("="*60)
        logger.info("SCORECARD DATA IMPLEMENTATION")
        logger.info(f"Started: {datetime.now()}")
        logger.info("="*60)
        
        steps = [
            ("Fix Data Quality Issues", fix_data_quality_issues),
            ("Create Store Master Table", create_store_master_table),
            ("Add Database Constraints", add_database_constraints),
            ("Create Performance Indexes", create_performance_indexes),
            ("Create Analytics Views", create_analytics_views),
            ("Create Correlation Metrics Table", create_correlation_metrics_table)
        ]
        
        success_count = 0
        for step_name, step_func in steps:
            logger.info(f"\nExecuting: {step_name}")
            try:
                if step_func():
                    logger.info(f"SUCCESS: {step_name} completed")
                    success_count += 1
                else:
                    logger.warning(f"FAILED: {step_name} encountered issues")
            except Exception as e:
                logger.error(f"ERROR in {step_name}: {str(e)}")
        
        # Validate implementation
        logger.info("\n" + "="*60)
        logger.info("VALIDATION")
        logger.info("="*60)
        
        if validate_implementation():
            logger.info("\n✓ All validations passed!")
        else:
            logger.warning("\n⚠ Some validations failed - review logs above")
        
        logger.info("\n" + "="*60)
        logger.info(f"IMPLEMENTATION COMPLETE")
        logger.info(f"Successful steps: {success_count}/{len(steps)}")
        logger.info(f"Completed: {datetime.now()}")
        logger.info("="*60)

if __name__ == "__main__":
    main()