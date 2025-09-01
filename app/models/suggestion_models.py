"""
User Suggestion System Models for Minnesota Equipment Rental Business
Advanced correlation, indicator, and analytics improvement suggestion system
"""

from app import db
from datetime import datetime
from sqlalchemy.dialects.mysql import JSON
from enum import Enum

class SuggestionCategory(Enum):
    WEATHER_CORRELATION = "WEATHER_CORRELATION"
    SEASONAL_PATTERN = "SEASONAL_PATTERN"
    ECONOMIC_INDICATOR = "ECONOMIC_INDICATOR"
    OPERATIONAL_INSIGHT = "OPERATIONAL_INSIGHT"
    CUSTOMER_BEHAVIOR = "CUSTOMER_BEHAVIOR"
    GEOGRAPHIC_PATTERN = "GEOGRAPHIC_PATTERN"
    LEADING_INDICATOR = "LEADING_INDICATOR"
    TRAILING_INDICATOR = "TRAILING_INDICATOR"
    ANALYTICS_IMPROVEMENT = "ANALYTICS_IMPROVEMENT"

class SuggestionStatus(Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    VALIDATION_PENDING = "VALIDATION_PENDING"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    IMPLEMENTED = "IMPLEMENTED"
    ARCHIVED = "ARCHIVED"

class ImplementationStatus(Enum):
    FEASIBLE = "FEASIBLE"
    COMPLEX = "COMPLEX"
    REQUIRES_DATA = "REQUIRES_DATA"
    NOT_FEASIBLE = "NOT_FEASIBLE"

class UserSuggestions(db.Model):
    """Enhanced user suggestions for Minnesota equipment rental business insights"""
    __tablename__ = "user_suggestions"
    __table_args__ = (
        db.Index("idx_suggestions_category", "category"),
        db.Index("idx_suggestions_status", "status"),
        db.Index("idx_suggestions_priority", "priority_score"),
        db.Index("idx_suggestions_date", "submitted_date"),
        db.Index("idx_suggestions_user", "user_id"),
        db.Index("idx_suggestions_store", "store_location"),
        db.Index("idx_suggestions_impact", "expected_business_impact"),
    )
    
    suggestion_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    
    # Classification
    category = db.Column(db.Enum(SuggestionCategory), nullable=False)
    status = db.Column(db.Enum(SuggestionStatus), default=SuggestionStatus.SUBMITTED)
    priority_score = db.Column(db.Integer, default=3)  # 1-5 scale
    
    # User information
    user_id = db.Column(db.String(100), nullable=False)
    user_name = db.Column(db.String(255), nullable=False)
    user_role = db.Column(db.String(100))  # Store Manager, Regional Director, Executive
    store_location = db.Column(db.String(100))  # Specific store or "All Stores"
    years_experience = db.Column(db.Integer)
    
    # Core suggestion content
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    business_justification = db.Column(db.Text, nullable=False)
    
    # Correlation-specific fields
    correlation_factor_1 = db.Column(db.String(255))  # Primary factor
    correlation_factor_2 = db.Column(db.String(255))  # Secondary factor
    expected_relationship = db.Column(db.String(100))  # positive, negative, seasonal, cyclic
    correlation_strength_estimate = db.Column(db.String(50))  # weak, moderate, strong
    
    # Leading/Trailing Indicator fields
    indicator_type = db.Column(db.String(50))  # leading, trailing, coincident
    time_lag_estimate = db.Column(db.String(100))  # "2 weeks", "1 month", "seasonal"
    predictive_window = db.Column(db.String(100))  # How far in advance/behind
    
    # Minnesota-specific context
    seasonal_relevance = db.Column(db.String(100))  # spring, summer, fall, winter, year-round
    weather_dependency = db.Column(db.String(100))  # temperature, precipitation, wind, none
    geographic_scope = db.Column(db.String(100))  # single store, regional, statewide
    market_segment = db.Column(db.String(100))  # DIY, construction, events, all
    
    # Business impact assessment
    expected_business_impact = db.Column(db.String(20))  # low, medium, high, critical
    revenue_impact_estimate = db.Column(db.DECIMAL(12, 2))
    cost_savings_estimate = db.Column(db.DECIMAL(12, 2))
    efficiency_gain_estimate = db.Column(db.String(100))  # percentage or description
    
    # Supporting evidence
    historical_examples = db.Column(db.Text)  # User's observed patterns
    data_sources_suggested = db.Column(db.Text)  # Where to get validation data
    confidence_level = db.Column(db.Integer)  # 1-5 user confidence
    supporting_documents = db.Column(JSON)  # File attachments metadata
    
    # Implementation details
    implementation_complexity = db.Column(db.String(20))  # low, medium, high
    required_resources = db.Column(db.Text)
    estimated_timeline = db.Column(db.String(50))
    technical_requirements = db.Column(db.Text)
    
    # Community engagement
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    
    # Processing workflow
    submitted_date = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_date = db.Column(db.DateTime)
    reviewed_by = db.Column(db.String(100))
    validation_date = db.Column(db.DateTime)
    validation_results = db.Column(JSON)  # Statistical validation results
    implementation_date = db.Column(db.DateTime)
    
    # Admin feedback
    admin_notes = db.Column(db.Text)
    rejection_reason = db.Column(db.Text)
    implementation_notes = db.Column(db.Text)
    follow_up_required = db.Column(db.Boolean, default=False)
    
    # Analytics tracking
    suggestion_analytics = db.relationship("SuggestionAnalytics", back_populates="suggestion", lazy="dynamic")
    comments = db.relationship("SuggestionComments", back_populates="suggestion", lazy="dynamic")
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'suggestion_id': self.suggestion_id,
            'category': self.category.value if self.category else None,
            'status': self.status.value if self.status else None,
            'priority_score': self.priority_score,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'user_role': self.user_role,
            'store_location': self.store_location,
            'years_experience': self.years_experience,
            'title': self.title,
            'description': self.description,
            'business_justification': self.business_justification,
            'correlation_factor_1': self.correlation_factor_1,
            'correlation_factor_2': self.correlation_factor_2,
            'expected_relationship': self.expected_relationship,
            'correlation_strength_estimate': self.correlation_strength_estimate,
            'indicator_type': self.indicator_type,
            'time_lag_estimate': self.time_lag_estimate,
            'predictive_window': self.predictive_window,
            'seasonal_relevance': self.seasonal_relevance,
            'weather_dependency': self.weather_dependency,
            'geographic_scope': self.geographic_scope,
            'market_segment': self.market_segment,
            'expected_business_impact': self.expected_business_impact,
            'revenue_impact_estimate': float(self.revenue_impact_estimate) if self.revenue_impact_estimate else None,
            'cost_savings_estimate': float(self.cost_savings_estimate) if self.cost_savings_estimate else None,
            'efficiency_gain_estimate': self.efficiency_gain_estimate,
            'historical_examples': self.historical_examples,
            'data_sources_suggested': self.data_sources_suggested,
            'confidence_level': self.confidence_level,
            'implementation_complexity': self.implementation_complexity,
            'required_resources': self.required_resources,
            'estimated_timeline': self.estimated_timeline,
            'upvotes': self.upvotes,
            'downvotes': self.downvotes,
            'view_count': self.view_count,
            'comment_count': self.comment_count,
            'vote_score': self.upvotes - self.downvotes,
            'submitted_date': self.submitted_date.isoformat() if self.submitted_date else None,
            'reviewed_date': self.reviewed_date.isoformat() if self.reviewed_date else None,
            'implementation_date': self.implementation_date.isoformat() if self.implementation_date else None,
            'validation_results': self.validation_results
        }

class SuggestionComments(db.Model):
    """Community comments on user suggestions"""
    __tablename__ = "user_suggestion_comments"
    __table_args__ = (
        db.Index("idx_comment_suggestion", "suggestion_id"),
        db.Index("idx_comment_date", "comment_date"),
        db.Index("idx_comment_user", "user_id"),
    )
    
    comment_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    suggestion_id = db.Column(db.BigInteger, db.ForeignKey('user_suggestions.suggestion_id'), nullable=False)
    
    user_id = db.Column(db.String(100), nullable=False)
    user_name = db.Column(db.String(255), nullable=False)
    user_role = db.Column(db.String(100))
    
    comment_text = db.Column(db.Text, nullable=False)
    comment_type = db.Column(db.String(50))  # support, question, enhancement, concern
    
    # Minnesota-specific additions
    related_experience = db.Column(db.Text)  # User's related experience
    additional_data_sources = db.Column(db.Text)  # Additional data user suggests
    
    comment_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_expert_input = db.Column(db.Boolean, default=False)  # Flagged expert feedback
    
    # Voting on comments
    helpful_votes = db.Column(db.Integer, default=0)
    
    # Relationships
    suggestion = db.relationship("UserSuggestions", back_populates="comments")

class SuggestionAnalytics(db.Model):
    """Track analytics and validation results for suggestions"""
    __tablename__ = "suggestion_analytics"
    __table_args__ = (
        db.Index("idx_analytics_suggestion", "suggestion_id"),
        db.Index("idx_analytics_date", "analysis_date"),
        db.Index("idx_analytics_type", "analysis_type"),
    )
    
    analytics_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    suggestion_id = db.Column(db.BigInteger, db.ForeignKey('user_suggestions.suggestion_id'), nullable=False)
    
    # Analysis metadata
    analysis_date = db.Column(db.DateTime, default=datetime.utcnow)
    analysis_type = db.Column(db.String(50))  # statistical_validation, ml_analysis, business_impact
    
    # Statistical validation results
    correlation_coefficient = db.Column(db.DECIMAL(5, 4))
    p_value = db.Column(db.DECIMAL(10, 8))
    confidence_interval = db.Column(JSON)  # Store confidence interval data
    sample_size = db.Column(db.Integer)
    
    # Machine learning analysis
    ml_model_used = db.Column(db.String(100))
    feature_importance = db.Column(db.DECIMAL(5, 4))
    prediction_accuracy = db.Column(db.DECIMAL(5, 4))
    cross_validation_score = db.Column(db.DECIMAL(5, 4))
    
    # Business impact analysis
    revenue_impact_calculated = db.Column(db.DECIMAL(12, 2))
    cost_savings_calculated = db.Column(db.DECIMAL(12, 2))
    roi_estimate = db.Column(db.DECIMAL(8, 2))
    payback_period_months = db.Column(db.Integer)
    
    # Implementation feasibility
    technical_feasibility_score = db.Column(db.Integer)  # 1-10 scale
    data_availability_score = db.Column(db.Integer)  # 1-10 scale
    resource_requirement_score = db.Column(db.Integer)  # 1-10 scale
    overall_feasibility_score = db.Column(db.DECIMAL(3, 1))  # Weighted average
    
    # Detailed results
    analysis_results = db.Column(JSON)  # Detailed analysis data
    recommendations = db.Column(db.Text)  # AI-generated recommendations
    validation_notes = db.Column(db.Text)
    
    analyzed_by = db.Column(db.String(100))  # System or user who ran analysis
    
    # Relationships
    suggestion = db.relationship("UserSuggestions", back_populates="suggestion_analytics")

class SuggestionCategorizationRules(db.Model):
    """Rules for automatically categorizing and prioritizing suggestions"""
    __tablename__ = "suggestion_categorization_rules"
    __table_args__ = (
        db.Index("idx_rules_category", "suggestion_category"),
        db.Index("idx_rules_active", "is_active"),
    )
    
    rule_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    
    rule_name = db.Column(db.String(255), nullable=False)
    suggestion_category = db.Column(db.Enum(SuggestionCategory))
    
    # Rule conditions (JSON format for flexibility)
    keyword_patterns = db.Column(JSON)  # Keywords that trigger this rule
    user_role_conditions = db.Column(JSON)  # User roles this applies to
    store_location_conditions = db.Column(JSON)  # Store-specific conditions
    
    # Rule actions
    auto_priority_score = db.Column(db.Integer)  # Auto-assign priority
    auto_assign_reviewer = db.Column(db.String(100))
    require_additional_data = db.Column(db.Boolean, default=False)
    
    # Rule metadata
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    usage_count = db.Column(db.Integer, default=0)
    
    rule_description = db.Column(db.Text)

class SuggestionNotifications(db.Model):
    """Notification system for suggestion updates"""
    __tablename__ = "suggestion_notifications"
    __table_args__ = (
        db.Index("idx_notifications_user", "user_id"),
        db.Index("idx_notifications_date", "created_date"),
        db.Index("idx_notifications_read", "is_read"),
        db.Index("idx_notifications_suggestion", "suggestion_id"),
    )
    
    notification_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    
    user_id = db.Column(db.String(100), nullable=False)
    suggestion_id = db.Column(db.BigInteger, db.ForeignKey('user_suggestions.suggestion_id'))
    
    notification_type = db.Column(db.String(50))  # status_update, new_comment, implementation
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Notification metadata
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    read_date = db.Column(db.DateTime)
    
    # Action links
    action_url = db.Column(db.String(500))
    action_text = db.Column(db.String(100))

class SuggestionRewards(db.Model):
    """Recognition and reward system for valuable suggestions"""
    __tablename__ = "suggestion_rewards"
    __table_args__ = (
        db.Index("idx_rewards_user", "user_id"),
        db.Index("idx_rewards_suggestion", "suggestion_id"),
        db.Index("idx_rewards_date", "awarded_date"),
    )
    
    reward_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    
    user_id = db.Column(db.String(100), nullable=False)
    suggestion_id = db.Column(db.BigInteger, db.ForeignKey('user_suggestions.suggestion_id'))
    
    reward_type = db.Column(db.String(50))  # badge, recognition, monetary
    reward_name = db.Column(db.String(255), nullable=False)
    reward_description = db.Column(db.Text)
    
    # Reward criteria
    criteria_met = db.Column(JSON)  # What criteria earned this reward
    business_value_generated = db.Column(db.DECIMAL(12, 2))
    
    awarded_date = db.Column(db.DateTime, default=datetime.utcnow)
    awarded_by = db.Column(db.String(100))
    
    # Display information
    badge_icon = db.Column(db.String(255))  # Path to badge icon
    is_public = db.Column(db.Boolean, default=True)
    display_on_profile = db.Column(db.Boolean, default=True)

class MinnesotaIndustryContext(db.Model):
    """Minnesota-specific industry context and seasonal patterns"""
    __tablename__ = "minnesota_industry_context"
    __table_args__ = (
        db.Index("idx_context_season", "season"),
        db.Index("idx_context_region", "region"),
        db.Index("idx_context_industry", "industry_segment"),
    )
    
    context_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    
    # Geographic context
    region = db.Column(db.String(100))  # Twin Cities, Duluth, Rochester, etc.
    county = db.Column(db.String(100))
    
    # Temporal context
    season = db.Column(db.String(20))  # spring, summer, fall, winter
    months_applicable = db.Column(JSON)  # [3,4,5] for spring
    
    # Industry context
    industry_segment = db.Column(db.String(100))  # construction, events, DIY
    market_characteristics = db.Column(db.Text)
    
    # Economic patterns
    economic_indicators = db.Column(JSON)  # Relevant economic data
    seasonal_multipliers = db.Column(JSON)  # Demand multipliers by season
    
    # Context description
    context_description = db.Column(db.Text, nullable=False)
    business_implications = db.Column(db.Text)
    
    # Supporting data
    data_sources = db.Column(db.Text)
    confidence_level = db.Column(db.Integer)  # 1-5
    
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(100))
    validated_by = db.Column(db.String(100))
    validation_date = db.Column(db.DateTime)
    
    # Usage tracking
    reference_count = db.Column(db.Integer, default=0)
    last_referenced = db.Column(db.DateTime)