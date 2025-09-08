"""
User Suggestions API - Minnesota Equipment Rental Business
RESTful API for correlation suggestions, indicators, and analytics improvements
"""

from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models.suggestion_models import (
    UserSuggestions, SuggestionComments, SuggestionAnalytics,
    SuggestionNotifications, SuggestionRewards, MinnesotaIndustryContext,
    SuggestionCategory, SuggestionStatus, ImplementationStatus
)
from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_, or_
import json
import logging

# Create blueprint
suggestions_api_bp = Blueprint('suggestions_api', __name__, url_prefix='/api/suggestions')

@suggestions_api_bp.route('/submit', methods=['POST'])
def submit_suggestion():
    """Submit a new correlation/analytics suggestion"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['category', 'title', 'description', 'business_justification', 'user_id', 'user_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate category
        try:
            category = SuggestionCategory(data['category'])
        except ValueError:
            return jsonify({'error': 'Invalid suggestion category'}), 400
        
        # Create suggestion
        suggestion = UserSuggestions(
            category=category,
            user_id=data['user_id'],
            user_name=data['user_name'],
            user_role=data.get('user_role'),
            store_location=data.get('store_location'),
            years_experience=data.get('years_experience'),
            
            # Core content
            title=data['title'][:255],  # Ensure within limit
            description=data['description'],
            business_justification=data['business_justification'],
            
            # Correlation-specific
            correlation_factor_1=data.get('correlation_factor_1'),
            correlation_factor_2=data.get('correlation_factor_2'),
            expected_relationship=data.get('expected_relationship'),
            correlation_strength_estimate=data.get('correlation_strength_estimate'),
            
            # Indicator-specific
            indicator_type=data.get('indicator_type'),
            time_lag_estimate=data.get('time_lag_estimate'),
            predictive_window=data.get('predictive_window'),
            
            # Minnesota context
            seasonal_relevance=data.get('seasonal_relevance'),
            weather_dependency=data.get('weather_dependency'),
            geographic_scope=data.get('geographic_scope', 'single store'),
            market_segment=data.get('market_segment', 'all'),
            
            # Business impact
            expected_business_impact=data.get('expected_business_impact', 'medium'),
            revenue_impact_estimate=data.get('revenue_impact_estimate'),
            cost_savings_estimate=data.get('cost_savings_estimate'),
            efficiency_gain_estimate=data.get('efficiency_gain_estimate'),
            
            # Evidence
            historical_examples=data.get('historical_examples'),
            data_sources_suggested=data.get('data_sources_suggested'),
            confidence_level=data.get('confidence_level', 3),
            
            # Implementation
            implementation_complexity=data.get('implementation_complexity', 'medium'),
            required_resources=data.get('required_resources'),
            estimated_timeline=data.get('estimated_timeline'),
            technical_requirements=data.get('technical_requirements')
        )
        
        # Auto-prioritize based on business impact and user role
        priority_score = calculate_priority_score(data)
        suggestion.priority_score = priority_score
        
        db.session.add(suggestion)
        db.session.commit()
        
        # Create notification for admins
        create_admin_notification(suggestion)
        
        current_app.logger.info(f"New suggestion submitted: {suggestion.suggestion_id} by {data['user_name']}")
        
        return jsonify({
            'success': True,
            'suggestion_id': suggestion.suggestion_id,
            'message': 'Suggestion submitted successfully',
            'priority_score': priority_score
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error submitting suggestion: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to submit suggestion'}), 500

@suggestions_api_bp.route('/list', methods=['GET'])
def list_suggestions():
    """Get list of suggestions with filtering and sorting"""
    try:
        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        category = request.args.get('category')
        status = request.args.get('status')
        user_id = request.args.get('user_id')
        store_location = request.args.get('store_location')
        sort_by = request.args.get('sort_by', 'submitted_date')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Build query
        query = UserSuggestions.query
        
        if category:
            try:
                category_enum = SuggestionCategory(category)
                query = query.filter(UserSuggestions.category == category_enum)
            except ValueError:
                return jsonify({'error': 'Invalid category'}), 400
        
        if status:
            try:
                status_enum = SuggestionStatus(status)
                query = query.filter(UserSuggestions.status == status_enum)
            except ValueError:
                return jsonify({'error': 'Invalid status'}), 400
        
        if user_id:
            query = query.filter(UserSuggestions.user_id == user_id)
            
        if store_location:
            query = query.filter(UserSuggestions.store_location.like(f'%{store_location}%'))
        
        # Sorting
        if sort_by == 'priority':
            sort_column = UserSuggestions.priority_score
        elif sort_by == 'votes':
            sort_column = (UserSuggestions.upvotes - UserSuggestions.downvotes)
        elif sort_by == 'views':
            sort_column = UserSuggestions.view_count
        else:
            sort_column = getattr(UserSuggestions, sort_by, UserSuggestions.submitted_date)
        
        if sort_order == 'desc':
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)
        
        # Paginate
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        suggestions = [suggestion.to_dict() for suggestion in paginated.items]
        
        return jsonify({
            'suggestions': suggestions,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_pages': paginated.pages,
                'total_items': paginated.total,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error listing suggestions: {str(e)}")
        return jsonify({'error': 'Failed to retrieve suggestions'}), 500

@suggestions_api_bp.route('/<int:suggestion_id>', methods=['GET'])
def get_suggestion(suggestion_id):
    """Get detailed suggestion information"""
    try:
        suggestion = UserSuggestions.query.get_or_404(suggestion_id)
        
        # Increment view count
        suggestion.view_count += 1
        db.session.commit()
        
        # Get comments
        comments = SuggestionComments.query.filter_by(suggestion_id=suggestion_id).order_by(SuggestionComments.comment_date).all()
        
        # Get analytics if available
        analytics = SuggestionAnalytics.query.filter_by(suggestion_id=suggestion_id).order_by(desc(SuggestionAnalytics.analysis_date)).first()
        
        result = suggestion.to_dict()
        result['comments'] = [comment.to_dict() for comment in comments]
        if analytics:
            result['analytics'] = analytics.to_dict()
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error getting suggestion {suggestion_id}: {str(e)}")
        return jsonify({'error': 'Failed to retrieve suggestion'}), 500

@suggestions_api_bp.route('/<int:suggestion_id>/vote', methods=['POST'])
def vote_suggestion(suggestion_id):
    """Vote on a suggestion (upvote/downvote)"""
    try:
        data = request.get_json()
        vote_type = data.get('vote_type')  # 'up' or 'down'
        user_id = data.get('user_id')
        
        if vote_type not in ['up', 'down']:
            return jsonify({'error': 'Invalid vote type'}), 400
        
        if not user_id:
            return jsonify({'error': 'User ID required'}), 400
        
        suggestion = UserSuggestions.query.get_or_404(suggestion_id)
        
        # Update vote count
        if vote_type == 'up':
            suggestion.upvotes += 1
        else:
            suggestion.downvotes += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'upvotes': suggestion.upvotes,
            'downvotes': suggestion.downvotes,
            'vote_score': suggestion.upvotes - suggestion.downvotes
        })
        
    except Exception as e:
        current_app.logger.error(f"Error voting on suggestion {suggestion_id}: {str(e)}")
        return jsonify({'error': 'Failed to vote'}), 500

@suggestions_api_bp.route('/<int:suggestion_id>/comment', methods=['POST'])
def add_comment(suggestion_id):
    """Add a comment to a suggestion"""
    try:
        data = request.get_json()
        
        required_fields = ['user_id', 'user_name', 'comment_text']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Verify suggestion exists
        suggestion = UserSuggestions.query.get_or_404(suggestion_id)
        
        comment = SuggestionComments(
            suggestion_id=suggestion_id,
            user_id=data['user_id'],
            user_name=data['user_name'],
            user_role=data.get('user_role'),
            comment_text=data['comment_text'],
            comment_type=data.get('comment_type', 'support'),
            related_experience=data.get('related_experience'),
            additional_data_sources=data.get('additional_data_sources'),
            is_expert_input=data.get('is_expert_input', False)
        )
        
        db.session.add(comment)
        
        # Update comment count
        suggestion.comment_count += 1
        
        db.session.commit()
        
        # Notify suggestion author
        create_comment_notification(suggestion, comment)
        
        return jsonify({
            'success': True,
            'comment_id': comment.comment_id,
            'message': 'Comment added successfully'
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error adding comment to suggestion {suggestion_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to add comment'}), 500

@suggestions_api_bp.route('/<int:suggestion_id>/update_status', methods=['PUT'])
def update_suggestion_status(suggestion_id):
    """Update suggestion status (admin only)"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        admin_notes = data.get('admin_notes')
        reviewed_by = data.get('reviewed_by')
        
        if not new_status:
            return jsonify({'error': 'Status required'}), 400
        
        try:
            status_enum = SuggestionStatus(new_status)
        except ValueError:
            return jsonify({'error': 'Invalid status'}), 400
        
        suggestion = UserSuggestions.query.get_or_404(suggestion_id)
        
        old_status = suggestion.status
        suggestion.status = status_enum
        suggestion.reviewed_by = reviewed_by
        suggestion.reviewed_date = datetime.utcnow()
        
        if admin_notes:
            suggestion.admin_notes = admin_notes
        
        if new_status == 'REJECTED':
            suggestion.rejection_reason = data.get('rejection_reason')
        elif new_status == 'IMPLEMENTED':
            suggestion.implementation_date = datetime.utcnow()
            suggestion.implementation_notes = data.get('implementation_notes')
        
        db.session.commit()
        
        # Create status update notification
        create_status_notification(suggestion, old_status, status_enum)
        
        current_app.logger.info(f"Suggestion {suggestion_id} status updated from {old_status.value if old_status else None} to {new_status}")
        
        return jsonify({
            'success': True,
            'message': 'Status updated successfully',
            'new_status': new_status
        })
        
    except Exception as e:
        current_app.logger.error(f"Error updating suggestion {suggestion_id} status: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update status'}), 500

@suggestions_api_bp.route('/analytics', methods=['GET'])
def get_suggestions_analytics():
    """Get analytics on suggestion system performance"""
    try:
        # Time period
        days = request.args.get('days', 30, type=int)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Basic metrics
        total_suggestions = UserSuggestions.query.filter(
            UserSuggestions.submitted_date >= start_date
        ).count()
        
        # By category
        category_stats = db.session.query(
            UserSuggestions.category,
            func.count(UserSuggestions.suggestion_id).label('count')
        ).filter(
            UserSuggestions.submitted_date >= start_date
        ).group_by(UserSuggestions.category).all()
        
        # By status
        status_stats = db.session.query(
            UserSuggestions.status,
            func.count(UserSuggestions.suggestion_id).label('count')
        ).filter(
            UserSuggestions.submitted_date >= start_date
        ).group_by(UserSuggestions.status).all()
        
        # Top contributors
        top_contributors = db.session.query(
            UserSuggestions.user_name,
            UserSuggestions.user_role,
            func.count(UserSuggestions.suggestion_id).label('suggestion_count'),
            func.sum(UserSuggestions.upvotes - UserSuggestions.downvotes).label('total_votes')
        ).filter(
            UserSuggestions.submitted_date >= start_date
        ).group_by(
            UserSuggestions.user_name, UserSuggestions.user_role
        ).order_by(desc('suggestion_count')).limit(10).all()
        
        # Implementation rate
        implemented_count = UserSuggestions.query.filter(
            and_(
                UserSuggestions.submitted_date >= start_date,
                UserSuggestions.status == SuggestionStatus.IMPLEMENTED
            )
        ).count()
        
        implementation_rate = (implemented_count / total_suggestions * 100) if total_suggestions > 0 else 0
        
        return jsonify({
            'period_days': days,
            'total_suggestions': total_suggestions,
            'implementation_rate': round(implementation_rate, 2),
            'implemented_count': implemented_count,
            'category_breakdown': [
                {'category': cat[0].value, 'count': cat[1]} 
                for cat in category_stats
            ],
            'status_breakdown': [
                {'status': status[0].value, 'count': status[1]} 
                for status in status_stats
            ],
            'top_contributors': [
                {
                    'user_name': contrib[0],
                    'user_role': contrib[1],
                    'suggestion_count': contrib[2],
                    'total_votes': contrib[3] or 0
                }
                for contrib in top_contributors
            ]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting suggestions analytics: {str(e)}")
        return jsonify({'error': 'Failed to retrieve analytics'}), 500

@suggestions_api_bp.route('/minnesota-context', methods=['GET'])
def get_minnesota_context():
    """Get Minnesota-specific industry context for suggestions"""
    try:
        season = request.args.get('season')
        region = request.args.get('region')
        industry_segment = request.args.get('industry_segment')
        
        query = MinnesotaIndustryContext.query
        
        if season:
            query = query.filter(MinnesotaIndustryContext.season == season)
        if region:
            query = query.filter(MinnesotaIndustryContext.region.like(f'%{region}%'))
        if industry_segment:
            query = query.filter(MinnesotaIndustryContext.industry_segment == industry_segment)
        
        contexts = query.order_by(desc(MinnesotaIndustryContext.confidence_level)).all()
        
        return jsonify({
            'contexts': [
                {
                    'context_id': ctx.context_id,
                    'region': ctx.region,
                    'season': ctx.season,
                    'industry_segment': ctx.industry_segment,
                    'context_description': ctx.context_description,
                    'business_implications': ctx.business_implications,
                    'confidence_level': ctx.confidence_level,
                    'seasonal_multipliers': ctx.seasonal_multipliers
                }
                for ctx in contexts
            ]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting Minnesota context: {str(e)}")
        return jsonify({'error': 'Failed to retrieve context'}), 500

# Helper functions
def calculate_priority_score(data):
    """Calculate auto-priority based on various factors"""
    score = 3  # Default medium priority
    
    # Business impact
    impact = data.get('expected_business_impact', 'medium')
    if impact == 'critical':
        score += 2
    elif impact == 'high':
        score += 1
    elif impact == 'low':
        score -= 1
    
    # User role
    role = data.get('user_role', '').lower()
    if 'director' in role or 'executive' in role:
        score += 1
    elif 'manager' in role:
        score += 0.5
    
    # Confidence level
    confidence = data.get('confidence_level', 3)
    if confidence >= 4:
        score += 0.5
    elif confidence <= 2:
        score -= 0.5
    
    # Revenue impact
    revenue_impact = data.get('revenue_impact_estimate', 0)
    if revenue_impact:
        if revenue_impact > 50000:
            score += 1
        elif revenue_impact > 10000:
            score += 0.5
    
    return max(1, min(5, int(score)))

def create_admin_notification(suggestion):
    """Create notification for admins about new suggestion"""
    try:
        # This would typically query for admin users
        admin_users = ['admin', 'analytics_admin']  # Placeholder
        
        for admin_id in admin_users:
            notification = SuggestionNotifications(
                user_id=admin_id,
                suggestion_id=suggestion.suggestion_id,
                notification_type='new_suggestion',
                title=f'New {suggestion.category.value} Suggestion',
                message=f'{suggestion.user_name} submitted: {suggestion.title}',
                action_url=f'/suggestions/{suggestion.suggestion_id}',
                action_text='Review Suggestion'
            )
            db.session.add(notification)
        
        db.session.commit()
        
    except Exception as e:
        current_app.logger.error(f"Error creating admin notification: {str(e)}")

def create_comment_notification(suggestion, comment):
    """Create notification for suggestion author about new comment"""
    try:
        if comment.user_id != suggestion.user_id:  # Don't notify self
            notification = SuggestionNotifications(
                user_id=suggestion.user_id,
                suggestion_id=suggestion.suggestion_id,
                notification_type='new_comment',
                title='New Comment on Your Suggestion',
                message=f'{comment.user_name} commented on "{suggestion.title}"',
                action_url=f'/suggestions/{suggestion.suggestion_id}#comments',
                action_text='View Comment'
            )
            db.session.add(notification)
            db.session.commit()
            
    except Exception as e:
        current_app.logger.error(f"Error creating comment notification: {str(e)}")

def create_status_notification(suggestion, old_status, new_status):
    """Create notification for status changes"""
    try:
        status_messages = {
            SuggestionStatus.UNDER_REVIEW: "Your suggestion is now under review",
            SuggestionStatus.VALIDATED: "Your suggestion has been validated",
            SuggestionStatus.IMPLEMENTED: "Your suggestion has been implemented! 🎉",
            SuggestionStatus.REJECTED: "Your suggestion has been reviewed"
        }
        
        message = status_messages.get(new_status, f"Status updated to {new_status.value}")
        
        notification = SuggestionNotifications(
            user_id=suggestion.user_id,
            suggestion_id=suggestion.suggestion_id,
            notification_type='status_update',
            title='Suggestion Status Update',
            message=f'{message}: "{suggestion.title}"',
            action_url=f'/suggestions/{suggestion.suggestion_id}',
            action_text='View Details'
        )
        db.session.add(notification)
        db.session.commit()
        
    except Exception as e:
        current_app.logger.error(f"Error creating status notification: {str(e)}")

# Add to_dict method to SuggestionComments if not exists
def comment_to_dict(self):
    return {
        'comment_id': self.comment_id,
        'user_name': self.user_name,
        'user_role': self.user_role,
        'comment_text': self.comment_text,
        'comment_type': self.comment_type,
        'related_experience': self.related_experience,
        'additional_data_sources': self.additional_data_sources,
        'comment_date': self.comment_date.isoformat() if self.comment_date else None,
        'is_expert_input': self.is_expert_input,
        'helpful_votes': self.helpful_votes
    }

# Monkey patch if method doesn't exist
if not hasattr(SuggestionComments, 'to_dict'):
    SuggestionComments.to_dict = comment_to_dict

# Add to_dict method to SuggestionAnalytics if not exists  
def analytics_to_dict(self):
    return {
        'analytics_id': self.analytics_id,
        'analysis_date': self.analysis_date.isoformat() if self.analysis_date else None,
        'analysis_type': self.analysis_type,
        'correlation_coefficient': float(self.correlation_coefficient) if self.correlation_coefficient else None,
        'p_value': float(self.p_value) if self.p_value else None,
        'confidence_interval': self.confidence_interval,
        'sample_size': self.sample_size,
        'ml_model_used': self.ml_model_used,
        'feature_importance': float(self.feature_importance) if self.feature_importance else None,
        'prediction_accuracy': float(self.prediction_accuracy) if self.prediction_accuracy else None,
        'revenue_impact_calculated': float(self.revenue_impact_calculated) if self.revenue_impact_calculated else None,
        'cost_savings_calculated': float(self.cost_savings_calculated) if self.cost_savings_calculated else None,
        'roi_estimate': float(self.roi_estimate) if self.roi_estimate else None,
        'technical_feasibility_score': self.technical_feasibility_score,
        'overall_feasibility_score': float(self.overall_feasibility_score) if self.overall_feasibility_score else None,
        'recommendations': self.recommendations,
        'validation_notes': self.validation_notes
    }

if not hasattr(SuggestionAnalytics, 'to_dict'):
    SuggestionAnalytics.to_dict = analytics_to_dict