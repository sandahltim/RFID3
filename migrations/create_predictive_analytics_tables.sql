-- Predictive Analytics Tables for RFID3 Equipment Rental System
-- Creates tables to support machine learning models and predictive analytics

-- Table to store forecast results
CREATE TABLE IF NOT EXISTS forecast_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    forecast_type VARCHAR(50) NOT NULL, -- 'demand', 'revenue', 'utilization'
    horizon_type VARCHAR(50) NOT NULL,  -- 'short_term', 'medium_term', 'long_term'
    store_id INTEGER,
    item_num VARCHAR(50),
    category VARCHAR(100),
    forecast_date DATE NOT NULL,
    forecast_value DECIMAL(12,2),
    confidence_lower DECIMAL(12,2),
    confidence_upper DECIMAL(12,2),
    confidence_level DECIMAL(3,2), -- 0.80, 0.90, 0.95
    model_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES store_mappings(id),
    INDEX idx_forecast_type_date (forecast_type, forecast_date),
    INDEX idx_store_category (store_id, category),
    INDEX idx_forecast_date (forecast_date)
);

-- Table to store model performance metrics
CREATE TABLE IF NOT EXISTS model_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_type VARCHAR(50) NOT NULL, -- 'demand_forecast', 'revenue_prediction', etc.
    model_version VARCHAR(20),
    store_id INTEGER,
    evaluation_date DATE NOT NULL,
    accuracy_score DECIMAL(5,4),
    mae DECIMAL(12,2), -- Mean Absolute Error
    mape DECIMAL(5,4), -- Mean Absolute Percentage Error
    rmse DECIMAL(12,2), -- Root Mean Square Error
    r2_score DECIMAL(5,4),
    training_samples INTEGER,
    test_samples INTEGER,
    feature_count INTEGER,
    data_quality_score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES store_mappings(id),
    INDEX idx_model_type_date (model_type, evaluation_date),
    INDEX idx_model_version (model_version)
);

-- Table to store feature importance scores
CREATE TABLE IF NOT EXISTS feature_importance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_type VARCHAR(50) NOT NULL,
    model_version VARCHAR(20),
    feature_name VARCHAR(100) NOT NULL,
    importance_score DECIMAL(8,6),
    rank_position INTEGER,
    store_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES store_mappings(id),
    INDEX idx_model_feature (model_type, feature_name),
    INDEX idx_importance_rank (importance_score DESC, rank_position)
);

-- Table to store prediction alerts and recommendations
CREATE TABLE IF NOT EXISTS prediction_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type VARCHAR(50) NOT NULL, -- 'risk', 'opportunity', 'warning'
    category VARCHAR(100), -- 'demand_risk', 'revenue_opportunity', etc.
    store_id INTEGER,
    item_num VARCHAR(50),
    title VARCHAR(200) NOT NULL,
    message TEXT,
    priority VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    impact_score DECIMAL(5,2), -- 0-100 impact score
    confidence DECIMAL(3,2), -- 0-1 confidence in alert
    trigger_date DATE,
    expiration_date DATE,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'acknowledged', 'resolved', 'expired'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES store_mappings(id),
    INDEX idx_alert_type_status (alert_type, status),
    INDEX idx_priority_date (priority, trigger_date),
    INDEX idx_store_category (store_id, category)
);

-- Table to store seasonal patterns and adjustments
CREATE TABLE IF NOT EXISTS seasonal_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_type VARCHAR(50) NOT NULL, -- 'demand', 'revenue', 'utilization'
    store_id INTEGER,
    category VARCHAR(100),
    season VARCHAR(20), -- 'winter', 'spring', 'summer', 'fall'
    month_num INTEGER, -- 1-12
    week_num INTEGER, -- 1-53
    seasonal_factor DECIMAL(8,4), -- Multiplicative factor (1.0 = average)
    trend_component DECIMAL(8,4),
    confidence_interval DECIMAL(8,4),
    sample_size INTEGER,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES store_mappings(id),
    INDEX idx_pattern_season (pattern_type, season),
    INDEX idx_store_category_month (store_id, category, month_num),
    INDEX idx_seasonal_factor (seasonal_factor)
);

-- Table to store external factor correlations
CREATE TABLE IF NOT EXISTS external_correlations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    factor_type VARCHAR(50) NOT NULL, -- 'weather', 'economic', 'competitor', 'event'
    factor_name VARCHAR(100) NOT NULL,
    store_id INTEGER,
    category VARCHAR(100),
    correlation_coefficient DECIMAL(8,6), -- -1 to 1
    p_value DECIMAL(8,6),
    sample_size INTEGER,
    time_lag_days INTEGER DEFAULT 0, -- Lag effect in days
    significance_level DECIMAL(3,2) DEFAULT 0.05,
    analysis_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES store_mappings(id),
    INDEX idx_factor_correlation (factor_type, correlation_coefficient DESC),
    INDEX idx_store_factor (store_id, factor_type),
    INDEX idx_significance (p_value, significance_level)
);

-- Table to store equipment utilization predictions
CREATE TABLE IF NOT EXISTS utilization_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_num VARCHAR(50) NOT NULL,
    store_id INTEGER,
    category VARCHAR(100),
    prediction_date DATE NOT NULL,
    predicted_utilization DECIMAL(5,4), -- 0-1 utilization rate
    optimal_utilization DECIMAL(5,4), -- Target utilization rate
    utilization_gap DECIMAL(6,4), -- Difference from optimal
    revenue_impact DECIMAL(12,2), -- Potential revenue impact
    recommendation_type VARCHAR(50), -- 'rebalance', 'promote', 'retire'
    priority_score INTEGER, -- 1-100 priority for action
    model_version VARCHAR(20),
    confidence DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES store_mappings(id),
    INDEX idx_item_date (item_num, prediction_date),
    INDEX idx_utilization_gap (utilization_gap DESC),
    INDEX idx_priority_score (priority_score DESC)
);

-- Table to store data quality metrics over time
CREATE TABLE IF NOT EXISTS data_quality_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    measurement_date DATE NOT NULL,
    store_id INTEGER,
    data_source VARCHAR(50), -- 'pos', 'rfid', 'financial'
    completeness_score DECIMAL(5,2), -- 0-100
    freshness_score DECIMAL(5,2), -- 0-100
    consistency_score DECIMAL(5,2), -- 0-100
    accuracy_score DECIMAL(5,2), -- 0-100
    correlation_coverage DECIMAL(5,2), -- 0-100 percentage
    overall_quality_score DECIMAL(5,2), -- 0-100 weighted average
    total_records INTEGER,
    missing_records INTEGER,
    duplicate_records INTEGER,
    outlier_records INTEGER,
    validation_errors INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES store_mappings(id),
    INDEX idx_quality_date (measurement_date),
    INDEX idx_overall_score (overall_quality_score DESC),
    INDEX idx_source_quality (data_source, overall_quality_score)
);

-- Table to store ML model configurations and metadata
CREATE TABLE IF NOT EXISTS ml_model_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_type VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(20),
    algorithm VARCHAR(50), -- 'linear_regression', 'random_forest', 'lstm', etc.
    hyperparameters TEXT, -- JSON string of hyperparameters
    feature_list TEXT, -- JSON array of feature names
    training_start_date DATE,
    training_end_date DATE,
    validation_score DECIMAL(8,6),
    test_score DECIMAL(8,6),
    model_file_path VARCHAR(500),
    preprocessing_pipeline TEXT, -- JSON description of preprocessing steps
    is_active BOOLEAN DEFAULT FALSE,
    deployment_date TIMESTAMP,
    retirement_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_model_type_version (model_type, model_version),
    INDEX idx_active_models (is_active, model_type),
    INDEX idx_deployment_date (deployment_date)
);

-- Table to store A/B test results for predictive models
CREATE TABLE IF NOT EXISTS model_ab_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_name VARCHAR(100) NOT NULL,
    model_a_type VARCHAR(50),
    model_a_version VARCHAR(20),
    model_b_type VARCHAR(50),
    model_b_version VARCHAR(20),
    store_id INTEGER,
    start_date DATE,
    end_date DATE,
    metric_name VARCHAR(50), -- 'accuracy', 'revenue_impact', etc.
    model_a_result DECIMAL(8,4),
    model_b_result DECIMAL(8,4),
    statistical_significance DECIMAL(3,2),
    confidence_level DECIMAL(3,2),
    sample_size_a INTEGER,
    sample_size_b INTEGER,
    winner VARCHAR(10), -- 'model_a', 'model_b', 'no_winner'
    test_status VARCHAR(20) DEFAULT 'running', -- 'running', 'completed', 'stopped'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES store_mappings(id),
    INDEX idx_test_status (test_status, end_date),
    INDEX idx_winner_significance (winner, statistical_significance)
);

-- Create views for common analytics queries

-- View for latest forecasts by category
CREATE VIEW IF NOT EXISTS latest_forecasts AS
SELECT 
    fr.forecast_type,
    fr.horizon_type,
    fr.store_id,
    fr.category,
    fr.forecast_date,
    fr.forecast_value,
    fr.confidence_lower,
    fr.confidence_upper,
    fr.confidence_level,
    sm.store_name,
    sm.business_type
FROM forecast_results fr
LEFT JOIN store_mappings sm ON fr.store_id = sm.id
WHERE fr.created_at = (
    SELECT MAX(created_at) 
    FROM forecast_results fr2 
    WHERE fr2.forecast_type = fr.forecast_type 
    AND fr2.horizon_type = fr.horizon_type 
    AND fr2.store_id = fr.store_id 
    AND fr2.category = fr.category
);

-- View for active high-priority alerts
CREATE VIEW IF NOT EXISTS active_priority_alerts AS
SELECT 
    pa.*,
    sm.store_name,
    sm.business_type
FROM prediction_alerts pa
LEFT JOIN store_mappings sm ON pa.store_id = sm.id
WHERE pa.status = 'active'
AND pa.priority IN ('high', 'critical')
AND (pa.expiration_date IS NULL OR pa.expiration_date >= DATE('now'))
ORDER BY 
    CASE pa.priority 
        WHEN 'critical' THEN 1
        WHEN 'high' THEN 2
        ELSE 3
    END,
    pa.impact_score DESC;

-- View for model performance summary
CREATE VIEW IF NOT EXISTS model_performance_summary AS
SELECT 
    mp.model_type,
    mp.model_version,
    COUNT(*) as evaluation_count,
    AVG(mp.accuracy_score) as avg_accuracy,
    AVG(mp.data_quality_score) as avg_data_quality,
    MAX(mp.evaluation_date) as latest_evaluation,
    AVG(mp.training_samples) as avg_training_samples
FROM model_performance mp
WHERE mp.evaluation_date >= DATE('now', '-30 days')
GROUP BY mp.model_type, mp.model_version
ORDER BY avg_accuracy DESC;

-- View for utilization optimization opportunities
CREATE VIEW IF NOT EXISTS utilization_opportunities AS
SELECT 
    up.*,
    e.category,
    e.sub_category,
    sm.store_name,
    sm.business_type,
    CASE 
        WHEN up.utilization_gap < -0.2 THEN 'Underutilized'
        WHEN up.utilization_gap > 0.2 THEN 'Overutilized'
        ELSE 'Optimal'
    END as utilization_status
FROM utilization_predictions up
LEFT JOIN pos_equipment e ON up.item_num = e.item_num
LEFT JOIN store_mappings sm ON up.store_id = sm.id
WHERE up.prediction_date = (
    SELECT MAX(prediction_date) 
    FROM utilization_predictions up2 
    WHERE up2.item_num = up.item_num
)
AND ABS(up.utilization_gap) > 0.1
ORDER BY up.priority_score DESC;

-- Create indexes for optimal query performance
CREATE INDEX IF NOT EXISTS idx_forecast_results_composite ON forecast_results(forecast_type, store_id, category, forecast_date);
CREATE INDEX IF NOT EXISTS idx_model_performance_composite ON model_performance(model_type, evaluation_date, accuracy_score);
CREATE INDEX IF NOT EXISTS idx_prediction_alerts_composite ON prediction_alerts(status, priority, trigger_date);
CREATE INDEX IF NOT EXISTS idx_utilization_predictions_composite ON utilization_predictions(store_id, priority_score, prediction_date);
CREATE INDEX IF NOT EXISTS idx_data_quality_history_composite ON data_quality_history(measurement_date, overall_quality_score, store_id);