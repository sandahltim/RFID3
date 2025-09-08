-- User Feedback System Database Migration
-- Creates all tables needed for comprehensive user feedback on predictive analytics correlations
-- Created: 2025-08-29
-- Version: 1.0.0

-- Feedback Types and Status Enums (implemented as CHECK constraints for compatibility)

-- Main correlation feedback table
CREATE TABLE IF NOT EXISTS correlation_feedback (
    feedback_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    correlation_id VARCHAR(100),
    prediction_id VARCHAR(100),
    feedback_type ENUM('CORRELATION_RATING', 'PREDICTION_VALIDATION', 'BUSINESS_CONTEXT', 'CORRELATION_SUGGESTION', 'DATA_SOURCE_SUGGESTION') NOT NULL,
    status ENUM('SUBMITTED', 'UNDER_REVIEW', 'IMPLEMENTED', 'REJECTED', 'ARCHIVED') DEFAULT 'SUBMITTED',
    
    -- User information
    user_id VARCHAR(100) NOT NULL,
    user_name VARCHAR(255),
    user_role VARCHAR(100),
    
    -- Rating metrics
    relevance_rating INT CHECK (relevance_rating >= 1 AND relevance_rating <= 5),
    accuracy_rating INT CHECK (accuracy_rating >= 1 AND accuracy_rating <= 5),
    usefulness_rating INT CHECK (usefulness_rating >= 1 AND usefulness_rating <= 5),
    thumbs_up_down BOOLEAN,
    confidence_level INT DEFAULT 3 CHECK (confidence_level >= 1 AND confidence_level <= 5),
    
    -- Text feedback
    title VARCHAR(255),
    comments TEXT,
    business_context TEXT,
    suggested_improvements TEXT,
    
    -- Metadata
    submitted_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Processing information
    reviewed_by VARCHAR(100),
    reviewed_date DATETIME,
    admin_notes TEXT,
    implementation_notes TEXT,
    
    -- Context data (JSON stored as TEXT for compatibility)
    context_data TEXT,
    
    INDEX idx_feedback_correlation (correlation_id),
    INDEX idx_feedback_type (feedback_type),
    INDEX idx_feedback_date (submitted_date),
    INDEX idx_feedback_user (user_id),
    INDEX idx_feedback_status (status)
);

-- Prediction validation table
CREATE TABLE IF NOT EXISTS prediction_validation (
    validation_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    prediction_id VARCHAR(100) NOT NULL,
    
    -- Prediction details
    prediction_type VARCHAR(50),
    prediction_date DATETIME NOT NULL,
    prediction_period VARCHAR(50),
    
    -- Predicted vs actual values
    predicted_value DECIMAL(15, 2),
    actual_value DECIMAL(15, 2),
    accuracy_score DECIMAL(5, 2),
    
    -- Additional metrics (stored as JSON TEXT)
    predicted_metrics TEXT,
    actual_metrics TEXT,
    
    -- Validation information
    validation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    validated_by VARCHAR(100),
    validation_method VARCHAR(100) DEFAULT 'manual',
    
    -- Business impact assessment
    business_impact_predicted VARCHAR(20),
    business_impact_actual VARCHAR(20),
    cost_of_inaccuracy DECIMAL(12, 2),
    
    -- Notes and context
    validation_notes TEXT,
    external_factors TEXT,
    lessons_learned TEXT,
    
    INDEX idx_prediction_id (prediction_id),
    INDEX idx_validation_date (validation_date),
    INDEX idx_accuracy_score (accuracy_score),
    INDEX idx_prediction_type (prediction_type)
);

-- Correlation suggestions table
CREATE TABLE IF NOT EXISTS correlation_suggestions (
    suggestion_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    -- Suggestion classification
    suggestion_type VARCHAR(50) DEFAULT 'new_correlation',
    status ENUM('SUBMITTED', 'UNDER_REVIEW', 'IMPLEMENTED', 'REJECTED', 'ARCHIVED') DEFAULT 'SUBMITTED',
    priority_score INT DEFAULT 3 CHECK (priority_score >= 1 AND priority_score <= 5),
    
    -- User information
    user_id VARCHAR(100) NOT NULL,
    user_name VARCHAR(255),
    user_role VARCHAR(100),
    
    -- Suggestion details
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    business_justification TEXT,
    expected_impact VARCHAR(20) DEFAULT 'medium',
    
    -- Proposed correlation details
    proposed_factor_1 VARCHAR(255),
    proposed_factor_2 VARCHAR(255),
    expected_relationship VARCHAR(100),
    suggested_data_source VARCHAR(255),
    
    -- Implementation details
    estimated_effort VARCHAR(20) DEFAULT 'medium',
    required_resources TEXT,
    implementation_timeline VARCHAR(50),
    
    -- Voting and community feedback
    upvotes INT DEFAULT 0,
    downvotes INT DEFAULT 0,
    
    -- Processing
    submitted_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    reviewed_date DATETIME,
    reviewed_by VARCHAR(100),
    implementation_date DATETIME,
    
    -- Admin notes
    admin_notes TEXT,
    rejection_reason TEXT,
    
    INDEX idx_suggestion_status (status),
    INDEX idx_suggestion_type (suggestion_type),
    INDEX idx_suggestion_date (submitted_date),
    INDEX idx_suggestion_priority (priority_score)
);

-- Suggestion comments table
CREATE TABLE IF NOT EXISTS suggestion_comments (
    comment_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    suggestion_id BIGINT NOT NULL,
    
    user_id VARCHAR(100) NOT NULL,
    user_name VARCHAR(255),
    comment_text TEXT NOT NULL,
    comment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_comment_suggestion (suggestion_id),
    INDEX idx_comment_date (comment_date),
    FOREIGN KEY (suggestion_id) REFERENCES correlation_suggestions(suggestion_id) ON DELETE CASCADE
);

-- Business context knowledge table
CREATE TABLE IF NOT EXISTS business_context_knowledge (
    knowledge_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    -- Context classification
    context_type VARCHAR(50) DEFAULT 'seasonal',
    category VARCHAR(100),
    
    -- Geographic scope
    store_id VARCHAR(10),
    region VARCHAR(100),
    applies_globally BOOLEAN DEFAULT FALSE,
    
    -- Temporal scope
    seasonal_pattern VARCHAR(100),
    time_period_start DATE,
    time_period_end DATE,
    recurrence_pattern VARCHAR(100),
    
    -- Content
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    impact_description TEXT,
    quantitative_impact DECIMAL(10, 2),
    
    -- Supporting evidence
    data_sources TEXT,
    historical_examples TEXT,
    confidence_level INT DEFAULT 3 CHECK (confidence_level >= 1 AND confidence_level <= 5),
    
    -- User information
    user_id VARCHAR(100) NOT NULL,
    user_name VARCHAR(255),
    user_role VARCHAR(100),
    local_expertise_years INT,
    
    -- Validation and usage
    submitted_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    validated_by VARCHAR(100),
    validation_date DATETIME,
    times_referenced INT DEFAULT 0,
    usefulness_score DECIMAL(3, 2),
    
    INDEX idx_context_type (context_type),
    INDEX idx_context_date (submitted_date),
    INDEX idx_context_store (store_id),
    INDEX idx_context_category (category)
);

-- Feedback analytics aggregation table
CREATE TABLE IF NOT EXISTS feedback_analytics (
    analytics_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    analytics_date DATE NOT NULL,
    metric_type VARCHAR(50) NOT NULL,
    
    -- Engagement metrics
    total_feedback_submissions INT DEFAULT 0,
    unique_users_providing_feedback INT DEFAULT 0,
    avg_rating_relevance DECIMAL(3, 2),
    avg_rating_accuracy DECIMAL(3, 2),
    avg_rating_usefulness DECIMAL(3, 2),
    
    -- Prediction accuracy trends
    avg_prediction_accuracy DECIMAL(5, 2),
    total_predictions_validated INT DEFAULT 0,
    accuracy_improvement_trend DECIMAL(5, 2),
    
    -- Suggestion metrics
    suggestions_submitted INT DEFAULT 0,
    suggestions_implemented INT DEFAULT 0,
    suggestion_implementation_rate DECIMAL(5, 2),
    
    -- Business impact metrics
    estimated_value_from_feedback DECIMAL(12, 2),
    cost_savings_identified DECIMAL(12, 2),
    revenue_improvements DECIMAL(12, 2),
    
    -- Additional metrics (stored as JSON TEXT)
    additional_metrics TEXT,
    
    calculated_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_analytics_date (analytics_date),
    INDEX idx_analytics_type (metric_type)
);

-- User feedback profile table
CREATE TABLE IF NOT EXISTS user_feedback_profile (
    profile_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(100) UNIQUE NOT NULL,
    user_name VARCHAR(255),
    user_role VARCHAR(100),
    
    -- Engagement metrics
    total_feedback_submitted INT DEFAULT 0,
    total_suggestions_submitted INT DEFAULT 0,
    total_validations_provided INT DEFAULT 0,
    
    -- Quality metrics
    avg_feedback_usefulness DECIMAL(3, 2),
    suggestions_implemented_count INT DEFAULT 0,
    expertise_score DECIMAL(5, 2) DEFAULT 50.0,
    
    -- Preferences (stored as JSON TEXT)
    preferred_notification_frequency VARCHAR(20) DEFAULT 'weekly',
    interested_categories TEXT,
    expertise_areas TEXT,
    
    -- Activity tracking
    first_feedback_date DATETIME,
    last_activity_date DATETIME,
    consecutive_active_days INT DEFAULT 0,
    
    -- Recognition (stored as JSON TEXT)
    feedback_badges TEXT,
    community_reputation INT DEFAULT 0,
    
    created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_date DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_profile_user (user_id),
    INDEX idx_profile_expertise (expertise_score)
);

-- Audit log for feedback system changes
CREATE TABLE IF NOT EXISTS correlation_audit_log (
    audit_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    
    -- What changed
    table_name VARCHAR(100),
    record_id BIGINT,
    action VARCHAR(20),
    
    -- Change details (stored as JSON TEXT)
    old_values TEXT,
    new_values TEXT,
    changed_fields TEXT,
    
    -- Who and when
    changed_by VARCHAR(100),
    changed_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    change_source VARCHAR(50),
    
    -- Context
    session_id VARCHAR(100),
    ip_address VARCHAR(45),
    user_agent VARCHAR(255),
    
    INDEX idx_audit_table (table_name),
    INDEX idx_audit_date (changed_date),
    INDEX idx_audit_user (changed_by)
);

-- Create sample data for demonstration
INSERT INTO correlation_feedback (
    correlation_id, feedback_type, user_id, user_name, user_role,
    relevance_rating, accuracy_rating, usefulness_rating, thumbs_up_down,
    title, comments, business_context
) VALUES 
(
    'weather-revenue-correlation', 'CORRELATION_RATING', 'demo_user_1', 'Store Manager - Brooklyn Park', 'Store Manager',
    5, 4, 5, TRUE,
    'Excellent weather correlation insight',
    'This correlation between temperature and rental demand is spot on. We see exactly this pattern in our Brooklyn Park location.',
    'Summer months show 40% higher tent and outdoor equipment rentals when temperature exceeds 75°F consistently for 3+ days.'
),
(
    'seasonal-wedding-demand', 'CORRELATION_RATING', 'demo_user_2', 'Regional Director', 'Regional Director', 
    4, 5, 4, TRUE,
    'Wedding season correlation validated',
    'May-September wedding season correlation is accurate. Helps us prepare inventory allocation.',
    'Wedding season accounts for 60% of our table/chair rentals. Peak months are June-August.'
);

INSERT INTO correlation_suggestions (
    suggestion_type, user_id, user_name, user_role, title, description,
    business_justification, expected_impact, proposed_factor_1, proposed_factor_2,
    expected_relationship, upvotes
) VALUES
(
    'new_correlation', 'demo_user_3', 'Operations Manager', 'Operations Manager',
    'High School Graduation Correlation',
    'Track correlation between high school graduation dates and party equipment demand. Graduation parties drive significant demand for tables, chairs, and tents.',
    'Graduation season creates predictable 2-3 week demand spikes in May-June that we could better prepare for with advance modeling.',
    'high', 'high_school_graduation_dates', 'party_equipment_demand',
    'positive', 8
),
(
    'data_source', 'demo_user_4', 'Business Analyst', 'Business Analyst',
    'Weather Forecast Integration',
    'Integrate 14-day weather forecasts to predict demand changes. Current system only uses historical weather.',
    'Extended weather forecasts would allow proactive inventory positioning and staffing decisions.',
    'medium', 'weather_forecast_14day', 'equipment_demand_prediction',
    'positive', 5
);

INSERT INTO business_context_knowledge (
    context_type, category, store_id, title, description, impact_description,
    quantitative_impact, user_id, user_name, user_role, confidence_level,
    local_expertise_years
) VALUES
(
    'seasonal', 'graduation_season', 'POR', 'High School Graduation Impact',
    'Local high schools (Portage Central, Portage Northern) have graduations in mid-May. Creates 2-week spike in party rentals.',
    'Graduation parties drive 300% increase in table/chair demand for 2-3 weeks in May',
    300.00, 'store_mgr_por', 'Sarah Johnson - POR', 'Store Manager', 5, 8
),
(
    'market', 'local_competition', 'POR', 'New Competitor Impact',
    'Party Plus opened 2 miles away in March 2024. Affecting weekend tent rentals specifically.',
    'Weekend tent demand down ~15% since March 2024 due to new local competitor',
    -15.00, 'store_mgr_por', 'Sarah Johnson - POR', 'Store Manager', 4, 8
);

-- Create user profiles for demo users
INSERT INTO user_feedback_profile (
    user_id, user_name, user_role, total_feedback_submitted, total_suggestions_submitted,
    expertise_score, first_feedback_date, last_activity_date
) VALUES
('demo_user_1', 'Store Manager - Brooklyn Park', 'Store Manager', 15, 3, 78.5, '2025-07-15', NOW()),
('demo_user_2', 'Regional Director', 'Regional Director', 22, 8, 89.2, '2025-06-20', NOW()),
('demo_user_3', 'Operations Manager', 'Operations Manager', 8, 12, 82.1, '2025-07-01', NOW()),
('demo_user_4', 'Business Analyst', 'Business Analyst', 31, 15, 91.7, '2025-06-10', NOW());

COMMIT;