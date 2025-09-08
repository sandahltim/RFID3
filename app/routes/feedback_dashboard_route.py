"""
Feedback Dashboard Route
Route handler for the feedback analytics dashboard
"""

from flask import Blueprint, render_template, jsonify, request
from app.services.feedback_service import FeedbackService
from app.services.logger import get_logger

logger = get_logger(__name__)

feedback_dashboard_bp = Blueprint("feedback_dashboard", __name__)

feedback_service = FeedbackService()

@feedback_dashboard_bp.route("/feedback/dashboard")
def feedback_dashboard():
    """Render the feedback analytics dashboard"""
    try:
        return render_template(
            "feedback_dashboard.html",
            cache_bust=1000  # Cache busting for development
        )
    except Exception as e:
        logger.error(f"Error rendering feedback dashboard: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to load feedback dashboard'
        }), 500