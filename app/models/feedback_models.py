"""
User Feedback System Models
SQLAlchemy models for comprehensive user feedback on predictive analytics correlations
"""

from app import db
from datetime import datetime
from sqlalchemy.dialects.mysql import JSON
from enum import Enum

class FeedbackType(Enum):
    CORRELATION_RATING = "CORRELATION_RATING"
    PREDICTION_VALIDATION = "PREDICTION_VALIDATION"
    BUSINESS_CONTEXT = "BUSINESS_CONTEXT"
    CORRELATION_SUGGESTION = "CORRELATION_SUGGESTION"
    DATA_SOURCE_SUGGESTION = "DATA_SOURCE_SUGGESTION"

class FeedbackStatus(Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    IMPLEMENTED = "IMPLEMENTED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"

class CorrelationFeedback(db.Model):
    """Core feedback table for correlation insights and predictions"""
    __tablename__ = "correlation_feedback"
    __table_args__ = (
        db.Index("idx_feedback_correlation", "correlation_id"),
        db.Index("idx_feedback_type", "feedback_type"),
        db.Index("idx_feedback_date", "submitted_date"),
        db.Index("idx_feedback_user", "user_id"),
        db.Index("idx_feedback_status", "status"),
    )
    
    feedback_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    
    # Link to correlation or prediction
    correlation_id = db.Column(db.String(100))  # Can reference correlation analysis results
    prediction_id = db.Column(db.String(100))   # Can reference specific predictions
    
    # Feedback classification
    feedback_type = db.Column(db.Enum(FeedbackType), nullable=False)
    status = db.Column(db.Enum(FeedbackStatus), default=FeedbackStatus.SUBMITTED)
    
    # User information
    user_id = db.Column(db.String(100), nullable=False)
    user_name = db.Column(db.String(255))
    user_role = db.Column(db.String(100))  # e.g., "Store Manager", "Regional Director"
    
    # Rating metrics
    relevance_rating = db.Column(db.Integer)  # 1-5 stars
    accuracy_rating = db.Column(db.Integer)   # 1-5 stars
    usefulness_rating = db.Column(db.Integer) # 1-5 stars
    thumbs_up_down = db.Column(db.Boolean)    # True=up, False=down, None=not rated
    confidence_level = db.Column(db.Integer)  # 1-5 confidence in their feedback
    
    # Text feedback
    title = db.Column(db.String(255))
    comments = db.Column(db.Text)
    business_context = db.Column(db.Text)
    suggested_improvements = db.Column(db.Text)
    
    # Metadata
    submitted_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Processing information
    reviewed_by = db.Column(db.String(100))
    reviewed_date = db.Column(db.DateTime)
    admin_notes = db.Column(db.Text)
    implementation_notes = db.Column(db.Text)
    
    # Context data (store additional context as JSON)
    context_data = db.Column(JSON)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'feedback_id': self.feedback_id,
            'correlation_id': self.correlation_id,
            'prediction_id': self.prediction_id,
            'feedback_type': self.feedback_type.value if self.feedback_type else None,
            'status': self.status.value if self.status else None,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'user_role': self.user_role,
            'relevance_rating': self.relevance_rating,
            'accuracy_rating': self.accuracy_rating,
            'usefulness_rating': self.usefulness_rating,
            'thumbs_up_down': self.thumbs_up_down,
            'confidence_level': self.confidence_level,
            'title': self.title,
            'comments': self.comments,
            'business_context': self.business_context,
            'suggested_improvements': self.suggested_improvements,
            'submitted_date': self.submitted_date.isoformat() if self.submitted_date else None,
            'updated_date': self.updated_date.isoformat() if self.updated_date else None,
            'context_data': self.context_data
        }

class PredictionValidation(db.Model):
    """Track actual outcomes vs predictions for accuracy measurement"""
    __tablename__ = "prediction_validation"
    __table_args__ = (
        db.Index("idx_prediction_id", "prediction_id"),
        db.Index("idx_validation_date", "validation_date"),
        db.Index("idx_accuracy_score", "accuracy_score"),
        db.Index("idx_prediction_type", "prediction_type"),
    )
    
    validation_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    prediction_id = db.Column(db.String(100), nullable=False)
    
    # Prediction details
    prediction_type = db.Column(db.String(50))  # demand_forecast, inventory_optimization, etc.
    prediction_date = db.Column(db.DateTime, nullable=False)
    prediction_period = db.Column(db.String(50))  # "2024-Q3", "2024-05", etc.
    
    # Predicted vs actual values
    predicted_value = db.Column(db.DECIMAL(15, 2))
    actual_value = db.Column(db.DECIMAL(15, 2))
    accuracy_score = db.Column(db.DECIMAL(5, 2))  # Calculated accuracy percentage
    
    # Additional metrics
    predicted_metrics = db.Column(JSON)  # Store complex prediction data
    actual_metrics = db.Column(JSON)     # Store actual outcome data
    
    # Validation information
    validation_date = db.Column(db.DateTime, default=datetime.utcnow)
    validated_by = db.Column(db.String(100))
    validation_method = db.Column(db.String(100))  # manual, automated, etc.
    
    # Business impact assessment
    business_impact_predicted = db.Column(db.String(20))  # high, medium, low
    business_impact_actual = db.Column(db.String(20))
    cost_of_inaccuracy = db.Column(db.DECIMAL(12, 2))
    
    # Notes and context
    validation_notes = db.Column(db.Text)
    external_factors = db.Column(db.Text)
    lessons_learned = db.Column(db.Text)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'validation_id': self.validation_id,
            'prediction_id': self.prediction_id,
            'prediction_type': self.prediction_type,
            'prediction_date': self.prediction_date.isoformat() if self.prediction_date else None,
            'prediction_period': self.prediction_period,
            'predicted_value': float(self.predicted_value) if self.predicted_value else None,
            'actual_value': float(self.actual_value) if self.actual_value else None,
            'accuracy_score': float(self.accuracy_score) if self.accuracy_score else None,
            'validation_date': self.validation_date.isoformat() if self.validation_date else None,
            'validated_by': self.validated_by,
            'business_impact_predicted': self.business_impact_predicted,
            'business_impact_actual': self.business_impact_actual,
            'cost_of_inaccuracy': float(self.cost_of_inaccuracy) if self.cost_of_inaccuracy else None,
            'validation_notes': self.validation_notes,
            'lessons_learned': self.lessons_learned
        }

class CorrelationSuggestions(db.Model):
    """User suggestions for new correlations and data sources"""
    __tablename__ = "correlation_suggestions"
    __table_args__ = (
        db.Index("idx_suggestion_status", "status"),
        db.Index("idx_suggestion_type", "suggestion_type"),
        db.Index("idx_suggestion_date", "submitted_date"),
        db.Index("idx_suggestion_priority", "priority_score"),
    )
    
    suggestion_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    
    # Suggestion classification
    suggestion_type = db.Column(db.String(50))  # new_correlation, data_source, metric_enhancement
    status = db.Column(db.Enum(FeedbackStatus), default=FeedbackStatus.SUBMITTED)
    priority_score = db.Column(db.Integer, default=3)  # 1-5 priority
    
    # User information
    user_id = db.Column(db.String(100), nullable=False)
    user_name = db.Column(db.String(255))
    user_role = db.Column(db.String(100))
    
    # Suggestion details
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    business_justification = db.Column(db.Text)
    expected_impact = db.Column(db.String(20))  # high, medium, low
    
    # Proposed correlation details
    proposed_factor_1 = db.Column(db.String(255))
    proposed_factor_2 = db.Column(db.String(255))
    expected_relationship = db.Column(db.String(100))  # positive, negative, seasonal, etc.
    suggested_data_source = db.Column(db.String(255))
    
    # Implementation details
    estimated_effort = db.Column(db.String(20))  # low, medium, high
    required_resources = db.Column(db.Text)
    implementation_timeline = db.Column(db.String(50))
    
    # Voting and community feedback
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    community_comments = db.relationship("CorrelationSuggestionComments", back_populates="suggestion", lazy="dynamic")
    
    # Processing
    submitted_date = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_date = db.Column(db.DateTime)
    reviewed_by = db.Column(db.String(100))
    implementation_date = db.Column(db.DateTime)
    
    # Admin notes
    admin_notes = db.Column(db.Text)
    rejection_reason = db.Column(db.Text)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'suggestion_id': self.suggestion_id,
            'suggestion_type': self.suggestion_type,
            'status': self.status.value if self.status else None,
            'priority_score': self.priority_score,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'user_role': self.user_role,
            'title': self.title,
            'description': self.description,
            'business_justification': self.business_justification,
            'expected_impact': self.expected_impact,
            'proposed_factor_1': self.proposed_factor_1,
            'proposed_factor_2': self.proposed_factor_2,
            'expected_relationship': self.expected_relationship,
            'suggested_data_source': self.suggested_data_source,
            'upvotes': self.upvotes,
            'downvotes': self.downvotes,
            'vote_score': self.upvotes - self.downvotes,
            'submitted_date': self.submitted_date.isoformat() if self.submitted_date else None,
            'implementation_date': self.implementation_date.isoformat() if self.implementation_date else None
        }

class CorrelationSuggestionComments(db.Model):
    """Comments on correlation suggestions"""
    __tablename__ = "correlation_suggestion_comments"
    __table_args__ = (
        db.Index("idx_comment_suggestion", "suggestion_id"),
        db.Index("idx_comment_date", "comment_date"),
    )
    
    comment_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    suggestion_id = db.Column(db.BigInteger, db.ForeignKey('correlation_suggestions.suggestion_id'), nullable=False)
    
    user_id = db.Column(db.String(100), nullable=False)
    user_name = db.Column(db.String(255))
    comment_text = db.Column(db.Text, nullable=False)
    comment_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    suggestion = db.relationship("CorrelationSuggestions", back_populates="community_comments")

class BusinessContextKnowledge(db.Model):
    """Store business knowledge and context provided by users"""
    __tablename__ = "business_context_knowledge"
    __table_args__ = (
        db.Index("idx_context_type", "context_type"),
        db.Index("idx_context_date", "submitted_date"),
        db.Index("idx_context_store", "store_code"),
        db.Index("idx_context_category", "category"),
    )
    
    knowledge_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    
    # Context classification
    context_type = db.Column(db.String(50))  # seasonal, market, operational, external
    category = db.Column(db.String(100))     # wedding_season, local_competition, etc.
    
    # Geographic scope
    store_code = db.Column(db.String(10))
    region = db.Column(db.String(100))
    applies_globally = db.Column(db.Boolean, default=False)
    
    # Temporal scope
    seasonal_pattern = db.Column(db.String(100))  # annual, monthly, weekly
    time_period_start = db.Column(db.Date)
    time_period_end = db.Column(db.Date)
    recurrence_pattern = db.Column(db.String(100))
    
    # Content
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    impact_description = db.Column(db.Text)
    quantitative_impact = db.Column(db.DECIMAL(10, 2))  # percentage or absolute impact
    
    # Supporting evidence
    data_sources = db.Column(db.Text)
    historical_examples = db.Column(db.Text)
    confidence_level = db.Column(db.Integer)  # 1-5
    
    # User information
    user_id = db.Column(db.String(100), nullable=False)
    user_name = db.Column(db.String(255))
    user_role = db.Column(db.String(100))
    local_expertise_years = db.Column(db.Integer)
    
    # Validation and usage
    submitted_date = db.Column(db.DateTime, default=datetime.utcnow)
    validated_by = db.Column(db.String(100))
    validation_date = db.Column(db.DateTime)
    times_referenced = db.Column(db.Integer, default=0)
    usefulness_score = db.Column(db.DECIMAL(3, 2))
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'knowledge_id': self.knowledge_id,
            'context_type': self.context_type,
            'category': self.category,
            'store_code': self.store_code,
            'region': self.region,
            'applies_globally': self.applies_globally,
            'seasonal_pattern': self.seasonal_pattern,
            'time_period_start': self.time_period_start.isoformat() if self.time_period_start else None,
            'time_period_end': self.time_period_end.isoformat() if self.time_period_end else None,
            'title': self.title,
            'description': self.description,
            'impact_description': self.impact_description,
            'quantitative_impact': float(self.quantitative_impact) if self.quantitative_impact else None,
            'confidence_level': self.confidence_level,
            'user_name': self.user_name,
            'user_role': self.user_role,
            'local_expertise_years': self.local_expertise_years,
            'submitted_date': self.submitted_date.isoformat() if self.submitted_date else None,
            'times_referenced': self.times_referenced,
            'usefulness_score': float(self.usefulness_score) if self.usefulness_score else None
        }

class FeedbackAnalytics(db.Model):
    """Aggregated analytics on feedback system usage and trends"""
    __tablename__ = "feedback_analytics"
    __table_args__ = (
        db.Index("idx_analytics_date", "analytics_date"),
        db.Index("idx_analytics_type", "metric_type"),
    )
    
    analytics_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    analytics_date = db.Column(db.Date, nullable=False)
    metric_type = db.Column(db.String(50), nullable=False)
    
    # Engagement metrics
    total_feedback_submissions = db.Column(db.Integer, default=0)
    unique_users_providing_feedback = db.Column(db.Integer, default=0)
    avg_rating_relevance = db.Column(db.DECIMAL(3, 2))
    avg_rating_accuracy = db.Column(db.DECIMAL(3, 2))
    avg_rating_usefulness = db.Column(db.DECIMAL(3, 2))
    
    # Prediction accuracy trends
    avg_prediction_accuracy = db.Column(db.DECIMAL(5, 2))
    total_predictions_validated = db.Column(db.Integer, default=0)
    accuracy_improvement_trend = db.Column(db.DECIMAL(5, 2))
    
    # Suggestion metrics
    suggestions_submitted = db.Column(db.Integer, default=0)
    suggestions_implemented = db.Column(db.Integer, default=0)
    suggestion_implementation_rate = db.Column(db.DECIMAL(5, 2))
    
    # Business impact metrics
    estimated_value_from_feedback = db.Column(db.DECIMAL(12, 2))
    cost_savings_identified = db.Column(db.DECIMAL(12, 2))
    revenue_improvements = db.Column(db.DECIMAL(12, 2))
    
    # Additional metrics as JSON for flexibility
    additional_metrics = db.Column(JSON)
    
    calculated_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'analytics_id': self.analytics_id,
            'analytics_date': self.analytics_date.isoformat() if self.analytics_date else None,
            'metric_type': self.metric_type,
            'total_feedback_submissions': self.total_feedback_submissions,
            'unique_users_providing_feedback': self.unique_users_providing_feedback,
            'avg_rating_relevance': float(self.avg_rating_relevance) if self.avg_rating_relevance else 0,
            'avg_rating_accuracy': float(self.avg_rating_accuracy) if self.avg_rating_accuracy else 0,
            'avg_rating_usefulness': float(self.avg_rating_usefulness) if self.avg_rating_usefulness else 0,
            'avg_prediction_accuracy': float(self.avg_prediction_accuracy) if self.avg_prediction_accuracy else 0,
            'total_predictions_validated': self.total_predictions_validated,
            'suggestions_submitted': self.suggestions_submitted,
            'suggestions_implemented': self.suggestions_implemented,
            'suggestion_implementation_rate': float(self.suggestion_implementation_rate) if self.suggestion_implementation_rate else 0,
            'estimated_value_from_feedback': float(self.estimated_value_from_feedback) if self.estimated_value_from_feedback else 0,
            'additional_metrics': self.additional_metrics
        }

class UserFeedbackProfile(db.Model):
    """Track user engagement and expertise in providing feedback"""
    __tablename__ = "user_feedback_profile"
    __table_args__ = (
        db.Index("idx_profile_user", "user_id"),
        db.Index("idx_profile_expertise", "expertise_score"),
    )
    
    profile_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.String(100), unique=True, nullable=False)
    user_name = db.Column(db.String(255))
    user_role = db.Column(db.String(100))
    
    # Engagement metrics
    total_feedback_submitted = db.Column(db.Integer, default=0)
    total_suggestions_submitted = db.Column(db.Integer, default=0)
    total_validations_provided = db.Column(db.Integer, default=0)
    
    # Quality metrics
    avg_feedback_usefulness = db.Column(db.DECIMAL(3, 2))
    suggestions_implemented_count = db.Column(db.Integer, default=0)
    expertise_score = db.Column(db.DECIMAL(5, 2), default=50.0)  # 0-100
    
    # Preferences
    preferred_notification_frequency = db.Column(db.String(20), default='weekly')
    interested_categories = db.Column(JSON)
    expertise_areas = db.Column(JSON)
    
    # Activity tracking
    first_feedback_date = db.Column(db.DateTime)
    last_activity_date = db.Column(db.DateTime)
    consecutive_active_days = db.Column(db.Integer, default=0)
    
    # Recognition
    feedback_badges = db.Column(JSON)  # Store earned badges/achievements
    community_reputation = db.Column(db.Integer, default=0)
    
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'profile_id': self.profile_id,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'user_role': self.user_role,
            'total_feedback_submitted': self.total_feedback_submitted,
            'total_suggestions_submitted': self.total_suggestions_submitted,
            'total_validations_provided': self.total_validations_provided,
            'avg_feedback_usefulness': float(self.avg_feedback_usefulness) if self.avg_feedback_usefulness else 0,
            'suggestions_implemented_count': self.suggestions_implemented_count,
            'expertise_score': float(self.expertise_score) if self.expertise_score else 50,
            'interested_categories': self.interested_categories,
            'expertise_areas': self.expertise_areas,
            'feedback_badges': self.feedback_badges,
            'community_reputation': self.community_reputation,
            'last_activity_date': self.last_activity_date.isoformat() if self.last_activity_date else None
        }