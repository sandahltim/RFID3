"""
User Feedback Service
Business logic layer for comprehensive feedback system on predictive analytics correlations
"""

from app import db
from app.models.feedback_models import (
    CorrelationFeedback, PredictionValidation, CorrelationSuggestions,
    SuggestionComments, BusinessContextKnowledge, FeedbackAnalytics,
    UserFeedbackProfile, FeedbackType, FeedbackStatus
)
from app.services.logger import get_logger
from datetime import datetime, timedelta, date
from decimal import Decimal
from sqlalchemy import func, desc, and_, or_
from typing import Dict, List, Optional, Any
import json

logger = get_logger(__name__)

class FeedbackService:
    """Service class for handling all feedback operations"""
    
    def submit_correlation_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit feedback on correlation insights"""
        try:
            feedback = CorrelationFeedback(
                correlation_id=feedback_data.get('correlation_id'),
                prediction_id=feedback_data.get('prediction_id'),
                feedback_type=FeedbackType(feedback_data.get('feedback_type', 'CORRELATION_RATING')),
                user_id=feedback_data['user_id'],
                user_name=feedback_data.get('user_name'),
                user_role=feedback_data.get('user_role'),
                relevance_rating=feedback_data.get('relevance_rating'),
                accuracy_rating=feedback_data.get('accuracy_rating'),
                usefulness_rating=feedback_data.get('usefulness_rating'),
                thumbs_up_down=feedback_data.get('thumbs_up_down'),
                confidence_level=feedback_data.get('confidence_level', 3),
                title=feedback_data.get('title'),
                comments=feedback_data.get('comments'),
                business_context=feedback_data.get('business_context'),
                suggested_improvements=feedback_data.get('suggested_improvements'),
                context_data=feedback_data.get('context_data', {})
            )
            
            db.session.add(feedback)
            db.session.commit()
            
            # Update user profile
            self._update_user_profile_on_feedback(feedback_data['user_id'])
            
            logger.info(f"Correlation feedback submitted by user {feedback_data['user_id']}")
            
            return {
                'success': True,
                'feedback_id': feedback.feedback_id,
                'message': 'Feedback submitted successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to submit correlation feedback: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def submit_prediction_validation(self, validation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit validation of prediction accuracy after actual results are known"""
        try:
            # Calculate accuracy score
            predicted = float(validation_data.get('predicted_value', 0))
            actual = float(validation_data.get('actual_value', 0))
            
            if predicted > 0:
                accuracy_score = max(0, 100 - abs((predicted - actual) / predicted * 100))
            else:
                accuracy_score = 0 if actual != 0 else 100
            
            validation = PredictionValidation(
                prediction_id=validation_data['prediction_id'],
                prediction_type=validation_data.get('prediction_type'),
                prediction_date=datetime.fromisoformat(validation_data['prediction_date'].replace('Z', '+00:00')),
                prediction_period=validation_data.get('prediction_period'),
                predicted_value=Decimal(str(predicted)),
                actual_value=Decimal(str(actual)),
                accuracy_score=Decimal(str(accuracy_score)),
                predicted_metrics=validation_data.get('predicted_metrics', {}),
                actual_metrics=validation_data.get('actual_metrics', {}),
                validated_by=validation_data['validated_by'],
                validation_method=validation_data.get('validation_method', 'manual'),
                business_impact_predicted=validation_data.get('business_impact_predicted'),
                business_impact_actual=validation_data.get('business_impact_actual'),
                cost_of_inaccuracy=validation_data.get('cost_of_inaccuracy'),
                validation_notes=validation_data.get('validation_notes'),
                external_factors=validation_data.get('external_factors'),
                lessons_learned=validation_data.get('lessons_learned')
            )
            
            db.session.add(validation)
            db.session.commit()
            
            # Update user profile
            self._update_user_profile_on_validation(validation_data['validated_by'])
            
            logger.info(f"Prediction validation submitted for prediction {validation_data['prediction_id']}")
            
            return {
                'success': True,
                'validation_id': validation.validation_id,
                'accuracy_score': float(accuracy_score),
                'message': 'Prediction validation submitted successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to submit prediction validation: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def submit_correlation_suggestion(self, suggestion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit suggestion for new correlations or data sources"""
        try:
            suggestion = CorrelationSuggestions(
                suggestion_type=suggestion_data.get('suggestion_type', 'new_correlation'),
                user_id=suggestion_data['user_id'],
                user_name=suggestion_data.get('user_name'),
                user_role=suggestion_data.get('user_role'),
                title=suggestion_data['title'],
                description=suggestion_data['description'],
                business_justification=suggestion_data.get('business_justification'),
                expected_impact=suggestion_data.get('expected_impact', 'medium'),
                proposed_factor_1=suggestion_data.get('proposed_factor_1'),
                proposed_factor_2=suggestion_data.get('proposed_factor_2'),
                expected_relationship=suggestion_data.get('expected_relationship'),
                suggested_data_source=suggestion_data.get('suggested_data_source'),
                estimated_effort=suggestion_data.get('estimated_effort', 'medium'),
                required_resources=suggestion_data.get('required_resources'),
                implementation_timeline=suggestion_data.get('implementation_timeline'),
                priority_score=suggestion_data.get('priority_score', 3)
            )
            
            db.session.add(suggestion)
            db.session.commit()
            
            # Update user profile
            self._update_user_profile_on_suggestion(suggestion_data['user_id'])
            
            logger.info(f"Correlation suggestion submitted by user {suggestion_data['user_id']}")
            
            return {
                'success': True,
                'suggestion_id': suggestion.suggestion_id,
                'message': 'Suggestion submitted successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to submit correlation suggestion: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def submit_business_context(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit business context and local knowledge"""
        try:
            context = BusinessContextKnowledge(
                context_type=context_data.get('context_type', 'seasonal'),
                category=context_data.get('category'),
                store_id=context_data.get('store_id'),
                region=context_data.get('region'),
                applies_globally=context_data.get('applies_globally', False),
                seasonal_pattern=context_data.get('seasonal_pattern'),
                time_period_start=context_data.get('time_period_start'),
                time_period_end=context_data.get('time_period_end'),
                recurrence_pattern=context_data.get('recurrence_pattern'),
                title=context_data['title'],
                description=context_data['description'],
                impact_description=context_data.get('impact_description'),
                quantitative_impact=context_data.get('quantitative_impact'),
                data_sources=context_data.get('data_sources'),
                historical_examples=context_data.get('historical_examples'),
                confidence_level=context_data.get('confidence_level', 3),
                user_id=context_data['user_id'],
                user_name=context_data.get('user_name'),
                user_role=context_data.get('user_role'),
                local_expertise_years=context_data.get('local_expertise_years')
            )
            
            db.session.add(context)
            db.session.commit()
            
            logger.info(f"Business context submitted by user {context_data['user_id']}")
            
            return {
                'success': True,
                'knowledge_id': context.knowledge_id,
                'message': 'Business context submitted successfully'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to submit business context: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def vote_on_suggestion(self, suggestion_id: int, user_id: str, vote: str) -> Dict[str, Any]:
        """Vote on correlation suggestions (upvote/downvote)"""
        try:
            suggestion = CorrelationSuggestions.query.get(suggestion_id)
            if not suggestion:
                return {'success': False, 'error': 'Suggestion not found'}
            
            # In a full implementation, you'd track individual votes to prevent double-voting
            # For now, we'll just increment the counters
            if vote.lower() == 'up':
                suggestion.upvotes += 1
            elif vote.lower() == 'down':
                suggestion.downvotes += 1
            else:
                return {'success': False, 'error': 'Invalid vote type'}
            
            db.session.commit()
            
            logger.info(f"User {user_id} voted {vote} on suggestion {suggestion_id}")
            
            return {
                'success': True,
                'upvotes': suggestion.upvotes,
                'downvotes': suggestion.downvotes,
                'vote_score': suggestion.upvotes - suggestion.downvotes
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to vote on suggestion: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_feedback_summary(self, days_back: int = 30) -> Dict[str, Any]:
        """Get summary of feedback activity and trends"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Overall feedback stats
            total_feedback = CorrelationFeedback.query.filter(
                CorrelationFeedback.submitted_date >= start_date
            ).count()
            
            unique_users = db.session.query(func.count(func.distinct(CorrelationFeedback.user_id))).filter(
                CorrelationFeedback.submitted_date >= start_date
            ).scalar()
            
            # Rating averages
            rating_stats = db.session.query(
                func.avg(CorrelationFeedback.relevance_rating).label('avg_relevance'),
                func.avg(CorrelationFeedback.accuracy_rating).label('avg_accuracy'),
                func.avg(CorrelationFeedback.usefulness_rating).label('avg_usefulness')
            ).filter(
                CorrelationFeedback.submitted_date >= start_date,
                CorrelationFeedback.relevance_rating.isnot(None)
            ).first()
            
            # Thumbs up/down stats
            thumbs_stats = db.session.query(
                func.sum(case([(CorrelationFeedback.thumbs_up_down == True, 1)], else_=0)).label('thumbs_up'),
                func.sum(case([(CorrelationFeedback.thumbs_up_down == False, 1)], else_=0)).label('thumbs_down')
            ).filter(
                CorrelationFeedback.submitted_date >= start_date,
                CorrelationFeedback.thumbs_up_down.isnot(None)
            ).first()
            
            # Prediction accuracy stats
            accuracy_stats = db.session.query(
                func.avg(PredictionValidation.accuracy_score).label('avg_accuracy'),
                func.count(PredictionValidation.validation_id).label('total_validations')
            ).filter(
                PredictionValidation.validation_date >= start_date
            ).first()
            
            # Suggestions stats
            suggestions_stats = db.session.query(
                func.count(CorrelationSuggestions.suggestion_id).label('total_suggestions'),
                func.sum(case([(CorrelationSuggestions.status == FeedbackStatus.IMPLEMENTED, 1)], else_=0)).label('implemented')
            ).filter(
                CorrelationSuggestions.submitted_date >= start_date
            ).first()
            
            # Top contributors
            top_contributors = db.session.query(
                CorrelationFeedback.user_name,
                func.count(CorrelationFeedback.feedback_id).label('feedback_count')
            ).filter(
                CorrelationFeedback.submitted_date >= start_date
            ).group_by(CorrelationFeedback.user_name).order_by(desc('feedback_count')).limit(5).all()
            
            return {
                'success': True,
                'summary_period_days': days_back,
                'total_feedback_submissions': total_feedback,
                'unique_contributors': unique_users or 0,
                'rating_averages': {
                    'relevance': float(rating_stats.avg_relevance) if rating_stats.avg_relevance else 0,
                    'accuracy': float(rating_stats.avg_accuracy) if rating_stats.avg_accuracy else 0,
                    'usefulness': float(rating_stats.avg_usefulness) if rating_stats.avg_usefulness else 0
                },
                'sentiment': {
                    'thumbs_up': int(thumbs_stats.thumbs_up) if thumbs_stats.thumbs_up else 0,
                    'thumbs_down': int(thumbs_stats.thumbs_down) if thumbs_stats.thumbs_down else 0
                },
                'prediction_accuracy': {
                    'average_accuracy': float(accuracy_stats.avg_accuracy) if accuracy_stats.avg_accuracy else 0,
                    'total_validations': int(accuracy_stats.total_validations) if accuracy_stats.total_validations else 0
                },
                'suggestions': {
                    'total_submitted': int(suggestions_stats.total_suggestions) if suggestions_stats.total_suggestions else 0,
                    'implemented': int(suggestions_stats.implemented) if suggestions_stats.implemented else 0,
                    'implementation_rate': round((suggestions_stats.implemented or 0) / max(1, suggestions_stats.total_suggestions or 1) * 100, 1)
                },
                'top_contributors': [
                    {'user_name': contrib.user_name, 'feedback_count': contrib.feedback_count}
                    for contrib in top_contributors
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get feedback summary: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_correlation_feedback(self, correlation_id: str = None, limit: int = 50) -> Dict[str, Any]:
        """Get feedback for specific correlation or all feedback"""
        try:
            query = CorrelationFeedback.query
            
            if correlation_id:
                query = query.filter(CorrelationFeedback.correlation_id == correlation_id)
            
            feedback_items = query.order_by(desc(CorrelationFeedback.submitted_date)).limit(limit).all()
            
            return {
                'success': True,
                'feedback': [item.to_dict() for item in feedback_items],
                'total_count': len(feedback_items)
            }
            
        except Exception as e:
            logger.error(f"Failed to get correlation feedback: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_suggestions(self, status: str = None, limit: int = 50) -> Dict[str, Any]:
        """Get correlation suggestions, optionally filtered by status"""
        try:
            query = CorrelationSuggestions.query
            
            if status:
                query = query.filter(CorrelationSuggestions.status == FeedbackStatus(status))
            
            suggestions = query.order_by(
                desc(CorrelationSuggestions.upvotes - CorrelationSuggestions.downvotes),
                desc(CorrelationSuggestions.submitted_date)
            ).limit(limit).all()
            
            return {
                'success': True,
                'suggestions': [suggestion.to_dict() for suggestion in suggestions],
                'total_count': len(suggestions)
            }
            
        except Exception as e:
            logger.error(f"Failed to get suggestions: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_business_context(self, context_type: str = None, store_id: str = None) -> Dict[str, Any]:
        """Get business context knowledge"""
        try:
            query = BusinessContextKnowledge.query
            
            if context_type:
                query = query.filter(BusinessContextKnowledge.context_type == context_type)
            
            if store_id:
                query = query.filter(or_(
                    BusinessContextKnowledge.store_id == store_id,
                    BusinessContextKnowledge.applies_globally == True
                ))
            
            context_items = query.order_by(desc(BusinessContextKnowledge.submitted_date)).limit(100).all()
            
            return {
                'success': True,
                'context_knowledge': [item.to_dict() for item in context_items],
                'total_count': len(context_items)
            }
            
        except Exception as e:
            logger.error(f"Failed to get business context: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_prediction_accuracy_trends(self, days_back: int = 90) -> Dict[str, Any]:
        """Get prediction accuracy trends over time"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Weekly accuracy trends
            weekly_accuracy = db.session.query(
                func.date_format(PredictionValidation.validation_date, '%Y-%u').label('week'),
                func.avg(PredictionValidation.accuracy_score).label('avg_accuracy'),
                func.count(PredictionValidation.validation_id).label('validation_count')
            ).filter(
                PredictionValidation.validation_date >= start_date
            ).group_by('week').order_by('week').all()
            
            # Accuracy by prediction type
            accuracy_by_type = db.session.query(
                PredictionValidation.prediction_type,
                func.avg(PredictionValidation.accuracy_score).label('avg_accuracy'),
                func.count(PredictionValidation.validation_id).label('validation_count')
            ).filter(
                PredictionValidation.validation_date >= start_date
            ).group_by(PredictionValidation.prediction_type).all()
            
            return {
                'success': True,
                'trends': {
                    'weekly_accuracy': [
                        {
                            'week': trend.week,
                            'avg_accuracy': float(trend.avg_accuracy),
                            'validation_count': trend.validation_count
                        }
                        for trend in weekly_accuracy
                    ],
                    'accuracy_by_type': [
                        {
                            'prediction_type': trend.prediction_type,
                            'avg_accuracy': float(trend.avg_accuracy),
                            'validation_count': trend.validation_count
                        }
                        for trend in accuracy_by_type
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get prediction accuracy trends: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _update_user_profile_on_feedback(self, user_id: str):
        """Update user profile statistics when feedback is submitted"""
        try:
            profile = UserFeedbackProfile.query.filter_by(user_id=user_id).first()
            if not profile:
                profile = UserFeedbackProfile(user_id=user_id)
                db.session.add(profile)
            
            profile.total_feedback_submitted = (profile.total_feedback_submitted or 0) + 1
            profile.last_activity_date = datetime.utcnow()
            
            if not profile.first_feedback_date:
                profile.first_feedback_date = datetime.utcnow()
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to update user profile for feedback: {e}")
    
    def _update_user_profile_on_validation(self, user_id: str):
        """Update user profile statistics when validation is submitted"""
        try:
            profile = UserFeedbackProfile.query.filter_by(user_id=user_id).first()
            if not profile:
                profile = UserFeedbackProfile(user_id=user_id)
                db.session.add(profile)
            
            profile.total_validations_provided = (profile.total_validations_provided or 0) + 1
            profile.last_activity_date = datetime.utcnow()
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to update user profile for validation: {e}")
    
    def _update_user_profile_on_suggestion(self, user_id: str):
        """Update user profile statistics when suggestion is submitted"""
        try:
            profile = UserFeedbackProfile.query.filter_by(user_id=user_id).first()
            if not profile:
                profile = UserFeedbackProfile(user_id=user_id)
                db.session.add(profile)
            
            profile.total_suggestions_submitted = (profile.total_suggestions_submitted or 0) + 1
            profile.last_activity_date = datetime.utcnow()
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to update user profile for suggestion: {e}")
    
    def generate_feedback_insights(self) -> Dict[str, Any]:
        """Generate actionable insights from feedback data"""
        try:
            insights = []
            
            # Most valuable correlations based on feedback
            valuable_correlations = db.session.query(
                CorrelationFeedback.correlation_id,
                func.avg(CorrelationFeedback.usefulness_rating).label('avg_usefulness'),
                func.count(CorrelationFeedback.feedback_id).label('feedback_count')
            ).filter(
                CorrelationFeedback.usefulness_rating.isnot(None),
                CorrelationFeedback.correlation_id.isnot(None)
            ).group_by(CorrelationFeedback.correlation_id).having(
                func.count(CorrelationFeedback.feedback_id) >= 3
            ).order_by(desc('avg_usefulness')).limit(5).all()
            
            if valuable_correlations:
                insights.append({
                    'type': 'valuable_correlations',
                    'title': 'Most Valuable Correlations',
                    'description': 'Correlations rated highest for business usefulness',
                    'data': [
                        {
                            'correlation_id': vc.correlation_id,
                            'avg_usefulness': float(vc.avg_usefulness),
                            'feedback_count': vc.feedback_count
                        }
                        for vc in valuable_correlations
                    ]
                })
            
            # Areas needing improvement
            low_accuracy = db.session.query(
                PredictionValidation.prediction_type,
                func.avg(PredictionValidation.accuracy_score).label('avg_accuracy')
            ).group_by(PredictionValidation.prediction_type).having(
                func.avg(PredictionValidation.accuracy_score) < 70
            ).all()
            
            if low_accuracy:
                insights.append({
                    'type': 'improvement_areas',
                    'title': 'Prediction Types Needing Improvement',
                    'description': 'Prediction types with accuracy below 70%',
                    'data': [
                        {
                            'prediction_type': la.prediction_type,
                            'avg_accuracy': float(la.avg_accuracy)
                        }
                        for la in low_accuracy
                    ]
                })
            
            # Most requested features
            top_suggestions = db.session.query(
                CorrelationSuggestions.suggestion_type,
                func.count(CorrelationSuggestions.suggestion_id).label('suggestion_count'),
                func.avg(CorrelationSuggestions.upvotes - CorrelationSuggestions.downvotes).label('avg_score')
            ).group_by(CorrelationSuggestions.suggestion_type).order_by(desc('suggestion_count')).limit(5).all()
            
            if top_suggestions:
                insights.append({
                    'type': 'requested_features',
                    'title': 'Most Requested Features',
                    'description': 'Feature types with highest suggestion volume',
                    'data': [
                        {
                            'suggestion_type': ts.suggestion_type,
                            'suggestion_count': ts.suggestion_count,
                            'avg_community_score': float(ts.avg_score) if ts.avg_score else 0
                        }
                        for ts in top_suggestions
                    ]
                })
            
            return {
                'success': True,
                'insights': insights,
                'generated_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate feedback insights: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Import case function for SQLite/MySQL compatibility
try:
    from sqlalchemy import case
except ImportError:
    def case(conditions, else_=None):
        """Fallback case function for older SQLAlchemy versions"""
        from sqlalchemy.sql import case as sql_case
        return sql_case(conditions, else_=else_)