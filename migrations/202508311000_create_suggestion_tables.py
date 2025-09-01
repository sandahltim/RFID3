"""
Create User Suggestions System Tables
Migration to create comprehensive suggestion system for Minnesota equipment rental analytics
"""

import mysql.connector
from datetime import datetime
import logging

# Database configuration (import from your config)
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_user',
    'password': 'your_password', 
    'database': 'your_database',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

def create_suggestion_tables():
    """Create all tables for the suggestion system"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Create user_suggestions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_suggestions (
                suggestion_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                
                -- Classification
                category ENUM(
                    'WEATHER_CORRELATION', 'SEASONAL_PATTERN', 'ECONOMIC_INDICATOR',
                    'OPERATIONAL_INSIGHT', 'CUSTOMER_BEHAVIOR', 'GEOGRAPHIC_PATTERN',
                    'LEADING_INDICATOR', 'TRAILING_INDICATOR', 'ANALYTICS_IMPROVEMENT'
                ) NOT NULL,
                status ENUM(
                    'SUBMITTED', 'UNDER_REVIEW', 'VALIDATION_PENDING', 
                    'VALIDATED', 'REJECTED', 'IMPLEMENTED', 'ARCHIVED'
                ) DEFAULT 'SUBMITTED',
                priority_score INT DEFAULT 3,
                
                -- User information
                user_id VARCHAR(100) NOT NULL,
                user_name VARCHAR(255) NOT NULL,
                user_role VARCHAR(100),
                store_location VARCHAR(100),
                years_experience INT,
                
                -- Core content
                title VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                business_justification TEXT NOT NULL,
                
                -- Correlation-specific fields
                correlation_factor_1 VARCHAR(255),
                correlation_factor_2 VARCHAR(255),
                expected_relationship VARCHAR(100),
                correlation_strength_estimate VARCHAR(50),
                
                -- Leading/Trailing Indicator fields
                indicator_type VARCHAR(50),
                time_lag_estimate VARCHAR(100),
                predictive_window VARCHAR(100),
                
                -- Minnesota-specific context
                seasonal_relevance VARCHAR(100),
                weather_dependency VARCHAR(100),
                geographic_scope VARCHAR(100),
                market_segment VARCHAR(100),
                
                -- Business impact assessment
                expected_business_impact VARCHAR(20),
                revenue_impact_estimate DECIMAL(12,2),
                cost_savings_estimate DECIMAL(12,2),
                efficiency_gain_estimate VARCHAR(100),
                
                -- Supporting evidence
                historical_examples TEXT,
                data_sources_suggested TEXT,
                confidence_level INT,
                supporting_documents JSON,
                
                -- Implementation details
                implementation_complexity VARCHAR(20),
                required_resources TEXT,
                estimated_timeline VARCHAR(50),
                technical_requirements TEXT,
                
                -- Community engagement
                upvotes INT DEFAULT 0,
                downvotes INT DEFAULT 0,
                view_count INT DEFAULT 0,
                comment_count INT DEFAULT 0,
                
                -- Processing workflow
                submitted_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                reviewed_date DATETIME,
                reviewed_by VARCHAR(100),
                validation_date DATETIME,
                validation_results JSON,
                implementation_date DATETIME,
                
                -- Admin feedback
                admin_notes TEXT,
                rejection_reason TEXT,
                implementation_notes TEXT,
                follow_up_required BOOLEAN DEFAULT FALSE,
                
                -- Indexes
                INDEX idx_suggestions_category (category),
                INDEX idx_suggestions_status (status),
                INDEX idx_suggestions_priority (priority_score),
                INDEX idx_suggestions_date (submitted_date),
                INDEX idx_suggestions_user (user_id),
                INDEX idx_suggestions_store (store_location),
                INDEX idx_suggestions_impact (expected_business_impact)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ Created user_suggestions table")
        
        # Create suggestion_comments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suggestion_comments (
                comment_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                suggestion_id BIGINT NOT NULL,
                
                user_id VARCHAR(100) NOT NULL,
                user_name VARCHAR(255) NOT NULL,
                user_role VARCHAR(100),
                
                comment_text TEXT NOT NULL,
                comment_type VARCHAR(50),
                
                -- Minnesota-specific additions
                related_experience TEXT,
                additional_data_sources TEXT,
                
                comment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_expert_input BOOLEAN DEFAULT FALSE,
                helpful_votes INT DEFAULT 0,
                
                -- Indexes
                INDEX idx_comment_suggestion (suggestion_id),
                INDEX idx_comment_date (comment_date),
                INDEX idx_comment_user (user_id),
                
                FOREIGN KEY (suggestion_id) REFERENCES user_suggestions(suggestion_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ Created suggestion_comments table")
        
        # Create suggestion_analytics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suggestion_analytics (
                analytics_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                suggestion_id BIGINT NOT NULL,
                
                -- Analysis metadata
                analysis_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                analysis_type VARCHAR(50),
                
                -- Statistical validation results
                correlation_coefficient DECIMAL(5,4),
                p_value DECIMAL(10,8),
                confidence_interval JSON,
                sample_size INT,
                
                -- Machine learning analysis
                ml_model_used VARCHAR(100),
                feature_importance DECIMAL(5,4),
                prediction_accuracy DECIMAL(5,4),
                cross_validation_score DECIMAL(5,4),
                
                -- Business impact analysis
                revenue_impact_calculated DECIMAL(12,2),
                cost_savings_calculated DECIMAL(12,2),
                roi_estimate DECIMAL(8,2),
                payback_period_months INT,
                
                -- Implementation feasibility
                technical_feasibility_score INT,
                data_availability_score INT,
                resource_requirement_score INT,
                overall_feasibility_score DECIMAL(3,1),
                
                -- Detailed results
                analysis_results JSON,
                recommendations TEXT,
                validation_notes TEXT,
                
                analyzed_by VARCHAR(100),
                
                -- Indexes
                INDEX idx_analytics_suggestion (suggestion_id),
                INDEX idx_analytics_date (analysis_date),
                INDEX idx_analytics_type (analysis_type),
                
                FOREIGN KEY (suggestion_id) REFERENCES user_suggestions(suggestion_id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ Created suggestion_analytics table")
        
        # Create suggestion_notifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suggestion_notifications (
                notification_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                
                user_id VARCHAR(100) NOT NULL,
                suggestion_id BIGINT,
                
                notification_type VARCHAR(50),
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                
                -- Notification metadata
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_read BOOLEAN DEFAULT FALSE,
                read_date DATETIME,
                
                -- Action links
                action_url VARCHAR(500),
                action_text VARCHAR(100),
                
                -- Indexes
                INDEX idx_notifications_user (user_id),
                INDEX idx_notifications_date (created_date),
                INDEX idx_notifications_read (is_read),
                INDEX idx_notifications_suggestion (suggestion_id),
                
                FOREIGN KEY (suggestion_id) REFERENCES user_suggestions(suggestion_id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ Created suggestion_notifications table")
        
        # Create suggestion_rewards table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suggestion_rewards (
                reward_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                
                user_id VARCHAR(100) NOT NULL,
                suggestion_id BIGINT,
                
                reward_type VARCHAR(50),
                reward_name VARCHAR(255) NOT NULL,
                reward_description TEXT,
                
                -- Reward criteria
                criteria_met JSON,
                business_value_generated DECIMAL(12,2),
                
                awarded_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                awarded_by VARCHAR(100),
                
                -- Display information
                badge_icon VARCHAR(255),
                is_public BOOLEAN DEFAULT TRUE,
                display_on_profile BOOLEAN DEFAULT TRUE,
                
                -- Indexes
                INDEX idx_rewards_user (user_id),
                INDEX idx_rewards_suggestion (suggestion_id),
                INDEX idx_rewards_date (awarded_date),
                
                FOREIGN KEY (suggestion_id) REFERENCES user_suggestions(suggestion_id) ON DELETE SET NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ Created suggestion_rewards table")
        
        # Create minnesota_industry_context table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS minnesota_industry_context (
                context_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                
                -- Geographic context
                region VARCHAR(100),
                county VARCHAR(100),
                
                -- Temporal context
                season VARCHAR(20),
                months_applicable JSON,
                
                -- Industry context
                industry_segment VARCHAR(100),
                market_characteristics TEXT,
                
                -- Economic patterns
                economic_indicators JSON,
                seasonal_multipliers JSON,
                
                -- Context description
                context_description TEXT NOT NULL,
                business_implications TEXT,
                
                -- Supporting data
                data_sources TEXT,
                confidence_level INT,
                
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(100),
                validated_by VARCHAR(100),
                validation_date DATETIME,
                
                -- Usage tracking
                reference_count INT DEFAULT 0,
                last_referenced DATETIME,
                
                -- Indexes
                INDEX idx_context_season (season),
                INDEX idx_context_region (region),
                INDEX idx_context_industry (industry_segment)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        print("✓ Created minnesota_industry_context table")
        
        # Insert some sample Minnesota industry context data
        cursor.execute("""
            INSERT IGNORE INTO minnesota_industry_context (
                context_id, region, season, months_applicable, industry_segment,
                context_description, business_implications, confidence_level, created_by
            ) VALUES 
            (1, 'Twin Cities', 'spring', '[3,4,5]', 'construction',
             'Spring construction season begins with ground thaw, typically mid-March',
             'High demand for excavation and earth-moving equipment rentals',
             5, 'system'),
            (2, 'Lake Minnetonka Area', 'summer', '[6,7,8]', 'events',
             'Peak wedding and event season around lakes and recreational areas',
             'Increased demand for tents, tables, chairs, and event equipment',
             5, 'system'),
            (3, 'Statewide', 'winter', '[12,1,2]', 'all',
             'Harsh Minnesota winters with sub-zero temperatures and heavy snow',
             'High demand for heaters, snow removal equipment, and indoor event supplies',
             5, 'system'),
            (4, 'Duluth Area', 'summer', '[6,7,8,9]', 'tourism',
             'Tourism season brings outdoor events and cabin rentals',
             'Seasonal spike in recreational equipment and outdoor event rentals',
             4, 'system')
        """)
        print("✓ Inserted sample Minnesota industry context data")
        
        connection.commit()
        print("✅ All suggestion system tables created successfully!")
        
    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
        if connection:
            connection.rollback()
        raise err
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if connection:
            connection.rollback()
        raise e
    finally:
        if connection:
            cursor.close()
            connection.close()

def drop_suggestion_tables():
    """Drop all suggestion system tables (for rollback)"""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Drop tables in reverse order due to foreign key constraints
        tables_to_drop = [
            'suggestion_rewards',
            'suggestion_notifications', 
            'suggestion_analytics',
            'suggestion_comments',
            'minnesota_industry_context',
            'user_suggestions'
        ]
        
        for table in tables_to_drop:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
            print(f"✓ Dropped {table} table")
        
        connection.commit()
        print("✅ All suggestion system tables dropped successfully!")
        
    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
        raise err
    finally:
        if connection:
            cursor.close()
            connection.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--drop':
        print("🗑️  Dropping suggestion system tables...")
        drop_suggestion_tables()
    else:
        print("🚀 Creating suggestion system tables...")
        create_suggestion_tables()
        print("\n🎉 Migration completed! The suggestion system is ready to use.")
        print("\nNext steps:")
        print("1. Update your application configuration if needed")
        print("2. Start the application and visit /suggestions")
        print("3. Submit your first analytics suggestion!")