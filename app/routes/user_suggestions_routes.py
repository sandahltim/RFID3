"""
User Suggestions Routes
Web routes for the suggestion system interface
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app import db
from app.models.suggestion_models import UserSuggestions, SuggestionCategory, SuggestionStatus
from app.services.suggestion_validation_service import SuggestionValidationService
from datetime import datetime
import logging

# Create blueprint
suggestions_routes_bp = Blueprint('suggestions_routes', __name__, url_prefix='/suggestions')

@suggestions_routes_bp.route('/')
def suggestions_home():
    """Main suggestions dashboard - public view"""
    try:
        # Get recent suggestions for public display
        recent_suggestions = UserSuggestions.query.filter(
            UserSuggestions.status.in_([SuggestionStatus.IMPLEMENTED, SuggestionStatus.VALIDATED])
        ).order_by(UserSuggestions.submitted_date.desc()).limit(10).all()
        
        # Get statistics
        stats = {
            'total_suggestions': UserSuggestions.query.count(),
            'implemented': UserSuggestions.query.filter_by(status=SuggestionStatus.IMPLEMENTED).count(),
            'under_review': UserSuggestions.query.filter_by(status=SuggestionStatus.UNDER_REVIEW).count(),
            'categories': db.session.query(UserSuggestions.category, 
                                         db.func.count(UserSuggestions.suggestion_id).label('count'))\
                         .group_by(UserSuggestions.category).all()
        }
        
        return render_template('suggestions/suggestions_dashboard.html', 
                             recent_suggestions=recent_suggestions,
                             stats=stats)
    except Exception as e:
        logging.error(f"Error in suggestions home: {str(e)}")
        flash('Error loading suggestions dashboard', 'error')
        return redirect(url_for('home.index'))

@suggestions_routes_bp.route('/submit')
def submit_suggestion():
    """Suggestion submission form"""
    return render_template('suggestions/submit_suggestion.html')

@suggestions_routes_bp.route('/my-suggestions')
def my_suggestions():
    """User's own suggestions"""
    # In a real implementation, you would get the user_id from authentication
    # For now, we'll use a placeholder
    user_id = request.args.get('user_id', 'demo_user')
    
    try:
        user_suggestions = UserSuggestions.query.filter_by(user_id=user_id)\
                                               .order_by(UserSuggestions.submitted_date.desc()).all()
        
        return render_template('suggestions/my_suggestions.html', 
                             suggestions=user_suggestions,
                             user_id=user_id)
    except Exception as e:
        logging.error(f"Error loading user suggestions: {str(e)}")
        flash('Error loading your suggestions', 'error')
        return redirect(url_for('suggestions_routes.suggestions_home'))

@suggestions_routes_bp.route('/admin')
def admin_dashboard():
    """Admin dashboard for reviewing and managing suggestions"""
    # In a real implementation, you would check admin permissions here
    return render_template('suggestions/admin_dashboard.html')

@suggestions_routes_bp.route('/view/<int:suggestion_id>')
def view_suggestion(suggestion_id):
    """View detailed suggestion"""
    try:
        suggestion = UserSuggestions.query.get_or_404(suggestion_id)
        
        # Increment view count
        suggestion.view_count = (suggestion.view_count or 0) + 1
        db.session.commit()
        
        return render_template('suggestions/view_suggestion.html', 
                             suggestion=suggestion)
    except Exception as e:
        logging.error(f"Error viewing suggestion {suggestion_id}: {str(e)}")
        flash('Error loading suggestion', 'error')
        return redirect(url_for('suggestions_routes.suggestions_home'))

@suggestions_routes_bp.route('/category/<category>')
def suggestions_by_category(category):
    """View suggestions filtered by category"""
    try:
        # Validate category
        try:
            category_enum = SuggestionCategory(category)
        except ValueError:
            flash('Invalid category', 'error')
            return redirect(url_for('suggestions_routes.suggestions_home'))
        
        suggestions = UserSuggestions.query.filter_by(category=category_enum)\
                                          .order_by(UserSuggestions.submitted_date.desc()).all()
        
        return render_template('suggestions/category_suggestions.html',
                             suggestions=suggestions,
                             category=category,
                             category_name=category.replace('_', ' ').title())
    except Exception as e:
        logging.error(f"Error loading category suggestions: {str(e)}")
        flash('Error loading category suggestions', 'error')
        return redirect(url_for('suggestions_routes.suggestions_home'))

@suggestions_routes_bp.route('/validate/<int:suggestion_id>')
def validate_suggestion_route(suggestion_id):
    """Trigger validation for a specific suggestion"""
    try:
        suggestion = UserSuggestions.query.get_or_404(suggestion_id)
        
        # Initialize validation service
        validation_service = SuggestionValidationService()
        
        # Run validation (this could be made async for better UX)
        validation_results = validation_service.validate_suggestion(suggestion_id)
        
        if 'error' in validation_results:
            flash(f'Validation error: {validation_results["error"]}', 'error')
        else:
            flash('Validation completed successfully', 'success')
        
        return redirect(url_for('suggestions_routes.view_suggestion', suggestion_id=suggestion_id))
        
    except Exception as e:
        logging.error(f"Error validating suggestion {suggestion_id}: {str(e)}")
        flash('Error running validation', 'error')
        return redirect(url_for('suggestions_routes.suggestions_home'))

@suggestions_routes_bp.route('/leaderboard')
def leaderboard():
    """Contributors leaderboard"""
    try:
        # Get top contributors
        top_contributors = db.session.query(
            UserSuggestions.user_name,
            UserSuggestions.user_role,
            UserSuggestions.store_location,
            db.func.count(UserSuggestions.suggestion_id).label('total_suggestions'),
            db.func.sum(UserSuggestions.upvotes - UserSuggestions.downvotes).label('total_votes'),
            db.func.sum(db.case(
                [(UserSuggestions.status == SuggestionStatus.IMPLEMENTED, 1)],
                else_=0
            )).label('implemented_count')
        ).group_by(
            UserSuggestions.user_name,
            UserSuggestions.user_role,
            UserSuggestions.store_location
        ).order_by(db.desc('implemented_count'), db.desc('total_suggestions')).limit(20).all()
        
        # Get recent implementations
        recent_implementations = UserSuggestions.query.filter_by(status=SuggestionStatus.IMPLEMENTED)\
                                                    .order_by(UserSuggestions.implementation_date.desc())\
                                                    .limit(10).all()
        
        return render_template('suggestions/leaderboard.html',
                             top_contributors=top_contributors,
                             recent_implementations=recent_implementations)
    except Exception as e:
        logging.error(f"Error loading leaderboard: {str(e)}")
        flash('Error loading leaderboard', 'error')
        return redirect(url_for('suggestions_routes.suggestions_home'))

@suggestions_routes_bp.route('/analytics')
def suggestions_analytics():
    """Analytics dashboard for suggestions system"""
    try:
        # This could be expanded to show comprehensive analytics
        return render_template('suggestions/analytics.html')
    except Exception as e:
        logging.error(f"Error loading analytics: {str(e)}")
        flash('Error loading analytics', 'error')
        return redirect(url_for('suggestions_routes.suggestions_home'))

@suggestions_routes_bp.route('/help')
def help_guide():
    """Help guide for using the suggestion system"""
    return render_template('suggestions/help.html')

# Error handlers
@suggestions_routes_bp.errorhandler(404)
def not_found(error):
    flash('Suggestion not found', 'error')
    return redirect(url_for('suggestions_routes.suggestions_home'))

@suggestions_routes_bp.errorhandler(500)
def internal_error(error):
    flash('Internal server error', 'error')
    return redirect(url_for('suggestions_routes.suggestions_home'))