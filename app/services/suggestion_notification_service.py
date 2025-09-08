"""
Suggestion Notification Service
Handle notifications and user engagement for the suggestion system
"""

from app import db
from app.models.suggestion_models import (
    SuggestionNotifications, UserSuggestions, SuggestionRewards, 
    SuggestionStatus, SuggestionCategory
)
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from sqlalchemy import func, desc

class SuggestionNotificationService:
    """Service for managing notifications and user engagement"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_notification(self, user_id: str, notification_type: str, 
                          title: str, message: str, suggestion_id: Optional[int] = None,
                          action_url: Optional[str] = None, action_text: Optional[str] = None) -> bool:
        """Create a new notification for a user"""
        try:
            notification = SuggestionNotifications(
                user_id=user_id,
                suggestion_id=suggestion_id,
                notification_type=notification_type,
                title=title,
                message=message,
                action_url=action_url,
                action_text=action_text
            )
            
            db.session.add(notification)
            db.session.commit()
            
            self.logger.info(f"Created notification for user {user_id}: {title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating notification: {str(e)}")
            db.session.rollback()
            return False
    
    def notify_suggestion_submitted(self, suggestion: UserSuggestions) -> bool:
        """Notify admins when a new suggestion is submitted"""
        try:
            # Get admin users (in real implementation, query from user management system)
            admin_users = self._get_admin_users()
            
            for admin_id in admin_users:
                title = f"New {suggestion.category.value.replace('_', ' ').title()} Suggestion"
                message = f"{suggestion.user_name} submitted: {suggestion.title}"
                action_url = f"/suggestions/admin#suggestion-{suggestion.suggestion_id}"
                
                self.create_notification(
                    user_id=admin_id,
                    notification_type='new_suggestion',
                    title=title,
                    message=message,
                    suggestion_id=suggestion.suggestion_id,
                    action_url=action_url,
                    action_text='Review Suggestion'
                )
            
            # Also notify the user that their suggestion was received
            self.create_notification(
                user_id=suggestion.user_id,
                notification_type='submission_received',
                title='Suggestion Received',
                message=f'Your suggestion "{suggestion.title}" has been submitted for review.',
                suggestion_id=suggestion.suggestion_id,
                action_url=f'/suggestions/view/{suggestion.suggestion_id}',
                action_text='View Suggestion'
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error notifying suggestion submission: {str(e)}")
            return False
    
    def notify_status_change(self, suggestion: UserSuggestions, old_status: SuggestionStatus, 
                           new_status: SuggestionStatus, admin_notes: str = None) -> bool:
        """Notify user when suggestion status changes"""
        try:
            status_messages = {
                SuggestionStatus.UNDER_REVIEW: {
                    'title': 'Suggestion Under Review',
                    'message': f'Your suggestion "{suggestion.title}" is now being reviewed by our analytics team.',
                    'emoji': '🔍'
                },
                SuggestionStatus.VALIDATED: {
                    'title': 'Suggestion Validated!',
                    'message': f'Great news! Your suggestion "{suggestion.title}" has been validated and shows statistical significance.',
                    'emoji': '✅'
                },
                SuggestionStatus.IMPLEMENTED: {
                    'title': 'Suggestion Implemented! 🎉',
                    'message': f'Congratulations! Your suggestion "{suggestion.title}" has been implemented in our analytics system.',
                    'emoji': '🚀'
                },
                SuggestionStatus.REJECTED: {
                    'title': 'Suggestion Update',
                    'message': f'Your suggestion "{suggestion.title}" has been reviewed. Check the details for feedback.',
                    'emoji': '📋'
                }
            }
            
            status_info = status_messages.get(new_status)
            if not status_info:
                return False
            
            message = status_info['message']
            if admin_notes:
                message += f"\n\nAdmin Notes: {admin_notes}"
            
            self.create_notification(
                user_id=suggestion.user_id,
                notification_type='status_update',
                title=status_info['title'],
                message=message,
                suggestion_id=suggestion.suggestion_id,
                action_url=f'/suggestions/view/{suggestion.suggestion_id}',
                action_text='View Details'
            )
            
            # Award badges/rewards for implementations
            if new_status == SuggestionStatus.IMPLEMENTED:
                self._award_implementation_reward(suggestion)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error notifying status change: {str(e)}")
            return False
    
    def notify_validation_completed(self, suggestion: UserSuggestions, validation_results: Dict) -> bool:
        """Notify user when ML validation is completed"""
        try:
            feasibility_score = validation_results.get('feasibility_score', 0)
            correlation = validation_results.get('results', {}).get('correlation_coefficient')
            
            if feasibility_score >= 70:
                title = 'Validation Success! 🎯'
                message = f'Your suggestion "{suggestion.title}" shows strong potential with {feasibility_score:.1f}% feasibility score.'
            elif feasibility_score >= 40:
                title = 'Validation Results Available'
                message = f'Your suggestion "{suggestion.title}" has been validated. Feasibility score: {feasibility_score:.1f}%'
            else:
                title = 'Validation Complete'
                message = f'Validation completed for "{suggestion.title}". Check results for detailed feedback.'
            
            if correlation is not None:
                message += f'\nCorrelation strength: {abs(correlation):.3f}'
            
            self.create_notification(
                user_id=suggestion.user_id,
                notification_type='validation_completed',
                title=title,
                message=message,
                suggestion_id=suggestion.suggestion_id,
                action_url=f'/suggestions/view/{suggestion.suggestion_id}',
                action_text='View Results'
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error notifying validation completion: {str(e)}")
            return False
    
    def notify_new_comment(self, suggestion: UserSuggestions, comment_user: str, comment_text: str) -> bool:
        """Notify suggestion author about new comments"""
        try:
            if comment_user == suggestion.user_id:
                return True  # Don't notify self
            
            self.create_notification(
                user_id=suggestion.user_id,
                notification_type='new_comment',
                title='New Comment on Your Suggestion',
                message=f'{comment_user} commented on "{suggestion.title}": {comment_text[:100]}...',
                suggestion_id=suggestion.suggestion_id,
                action_url=f'/suggestions/view/{suggestion.suggestion_id}#comments',
                action_text='View Comment'
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error notifying new comment: {str(e)}")
            return False
    
    def get_user_notifications(self, user_id: str, unread_only: bool = False, limit: int = 20) -> List[Dict]:
        """Get notifications for a user"""
        try:
            query = SuggestionNotifications.query.filter_by(user_id=user_id)
            
            if unread_only:
                query = query.filter_by(is_read=False)
            
            notifications = query.order_by(desc(SuggestionNotifications.created_date)).limit(limit).all()
            
            return [self._notification_to_dict(notif) for notif in notifications]
            
        except Exception as e:
            self.logger.error(f"Error getting user notifications: {str(e)}")
            return []
    
    def mark_notification_read(self, notification_id: int, user_id: str) -> bool:
        """Mark a notification as read"""
        try:
            notification = SuggestionNotifications.query.filter_by(
                notification_id=notification_id,
                user_id=user_id
            ).first()
            
            if notification:
                notification.is_read = True
                notification.read_date = datetime.utcnow()
                db.session.commit()
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error marking notification read: {str(e)}")
            return False
    
    def mark_all_notifications_read(self, user_id: str) -> bool:
        """Mark all notifications as read for a user"""
        try:
            SuggestionNotifications.query.filter_by(
                user_id=user_id,
                is_read=False
            ).update({
                'is_read': True,
                'read_date': datetime.utcnow()
            })
            
            db.session.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error marking all notifications read: {str(e)}")
            return False
    
    def send_weekly_digest(self, user_id: str) -> bool:
        """Send weekly digest of suggestion activity"""
        try:
            # Get user's suggestions and their activity from past week
            week_ago = datetime.utcnow() - timedelta(days=7)
            
            user_suggestions = UserSuggestions.query.filter(
                UserSuggestions.user_id == user_id,
                UserSuggestions.submitted_date >= week_ago
            ).all()
            
            if not user_suggestions:
                return True  # No activity to report
            
            # Create digest
            digest_content = self._create_weekly_digest(user_suggestions, week_ago)
            
            self.create_notification(
                user_id=user_id,
                notification_type='weekly_digest',
                title='Weekly Suggestions Digest',
                message=digest_content,
                action_url='/suggestions/my-suggestions',
                action_text='View My Suggestions'
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending weekly digest: {str(e)}")
            return False
    
    def _award_implementation_reward(self, suggestion: UserSuggestions) -> None:
        """Award reward for implemented suggestion"""
        try:
            # Determine reward based on suggestion characteristics
            reward_name = "Implementation Achievement"
            reward_description = f"Your suggestion '{suggestion.title}' was implemented!"
            
            # Enhanced rewards based on impact and category
            if suggestion.expected_business_impact == 'critical':
                reward_name = "Critical Impact Contributor"
                reward_description += " This high-impact suggestion is making a real difference."
            elif suggestion.category == SuggestionCategory.WEATHER_CORRELATION:
                reward_name = "Weather Analytics Expert"
                reward_description += " Your weather correlation insight is improving our forecasting."
            elif suggestion.category == SuggestionCategory.CUSTOMER_BEHAVIOR:
                reward_name = "Customer Insights Specialist"
                reward_description += " Your customer behavior analysis is enhancing our service."
            
            reward = SuggestionRewards(
                user_id=suggestion.user_id,
                suggestion_id=suggestion.suggestion_id,
                reward_type='badge',
                reward_name=reward_name,
                reward_description=reward_description,
                business_value_generated=suggestion.revenue_impact_estimate or 0,
                awarded_by='system'
            )
            
            db.session.add(reward)
            db.session.commit()
            
            self.logger.info(f"Awarded '{reward_name}' to user {suggestion.user_id}")
            
        except Exception as e:
            self.logger.error(f"Error awarding reward: {str(e)}")
    
    def _get_admin_users(self) -> List[str]:
        """Get list of admin user IDs (placeholder implementation)"""
        # In a real implementation, this would query your user management system
        return ['admin', 'analytics_admin', 'data_manager']
    
    def _notification_to_dict(self, notification: SuggestionNotifications) -> Dict:
        """Convert notification to dictionary"""
        return {
            'notification_id': notification.notification_id,
            'title': notification.title,
            'message': notification.message,
            'notification_type': notification.notification_type,
            'created_date': notification.created_date.isoformat() if notification.created_date else None,
            'is_read': notification.is_read,
            'action_url': notification.action_url,
            'action_text': notification.action_text,
            'suggestion_id': notification.suggestion_id
        }
    
    def _create_weekly_digest(self, suggestions: List[UserSuggestions], since_date: datetime) -> str:
        """Create weekly digest content"""
        digest_lines = [
            f"Here's your suggestion activity from the past week:",
            "",
            f"📊 Total Suggestions: {len(suggestions)}"
        ]
        
        # Group by status
        status_counts = {}
        for suggestion in suggestions:
            status = suggestion.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in status_counts.items():
            digest_lines.append(f"   • {status.replace('_', ' ').title()}: {count}")
        
        digest_lines.extend([
            "",
            "Keep sharing your insights! Your domain expertise is valuable to our analytics team.",
        ])
        
        return "\n".join(digest_lines)
    
    def get_notification_stats(self, user_id: str) -> Dict:
        """Get notification statistics for a user"""
        try:
            total_notifications = SuggestionNotifications.query.filter_by(user_id=user_id).count()
            unread_count = SuggestionNotifications.query.filter_by(user_id=user_id, is_read=False).count()
            
            # Get breakdown by type
            type_breakdown = db.session.query(
                SuggestionNotifications.notification_type,
                func.count(SuggestionNotifications.notification_id).label('count')
            ).filter_by(user_id=user_id).group_by(SuggestionNotifications.notification_type).all()
            
            return {
                'total_notifications': total_notifications,
                'unread_count': unread_count,
                'read_count': total_notifications - unread_count,
                'type_breakdown': [{'type': t[0], 'count': t[1]} for t in type_breakdown]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting notification stats: {str(e)}")
            return {'total_notifications': 0, 'unread_count': 0, 'read_count': 0, 'type_breakdown': []}
    
    def cleanup_old_notifications(self, days_to_keep: int = 90) -> int:
        """Clean up old notifications"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            deleted_count = SuggestionNotifications.query.filter(
                SuggestionNotifications.created_date < cutoff_date,
                SuggestionNotifications.is_read == True
            ).delete()
            
            db.session.commit()
            
            self.logger.info(f"Cleaned up {deleted_count} old notifications")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up notifications: {str(e)}")
            return 0