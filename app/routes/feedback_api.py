"""
User Feedback API Endpoints
RESTful API for comprehensive user feedback on predictive analytics correlations
"""

from flask import Blueprint, request, jsonify, session
from datetime import datetime
from app.services.feedback_service import FeedbackService
from app.services.logger import get_logger
import json

logger = get_logger(__name__)

feedback_bp = Blueprint("feedback_api", __name__, url_prefix="/api/feedback")

# Initialize feedback service
feedback_service = FeedbackService()

def get_current_user():
    """Get current user information from session or request"""
    # In a real implementation, this would use proper authentication
    # For now, we'll use a simple approach
    user_id = request.headers.get('X-User-ID') or session.get('user_id') or 'anonymous'
    user_name = request.headers.get('X-User-Name') or session.get('user_name') or 'Anonymous User'
    user_role = request.headers.get('X-User-Role') or session.get('user_role') or 'User'
    
    return {
        'user_id': user_id,
        'user_name': user_name,
        'user_role': user_role
    }

@feedback_bp.route("/correlation", methods=["POST"])
def submit_correlation_feedback():
    """Submit feedback on correlation insights"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Add user information
        user_info = get_current_user()
        data.update(user_info)
        
        # Validate required fields
        if not data.get('user_id'):
            return jsonify({
                'success': False,
                'error': 'User ID is required'
            }), 400
        
        result = feedback_service.submit_correlation_feedback(data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error in submit_correlation_feedback: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@feedback_bp.route("/prediction-validation", methods=["POST"])
def submit_prediction_validation():
    """Submit validation of prediction accuracy"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Add user information
        user_info = get_current_user()
        data['validated_by'] = user_info['user_id']
        
        # Validate required fields
        required_fields = ['prediction_id', 'predicted_value', 'actual_value', 'prediction_date']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        result = feedback_service.submit_prediction_validation(data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error in submit_prediction_validation: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@feedback_bp.route("/suggestions", methods=["POST"])
def submit_correlation_suggestion():
    """Submit suggestion for new correlations or data sources"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Add user information
        user_info = get_current_user()
        data.update(user_info)
        
        # Validate required fields
        required_fields = ['title', 'description']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        result = feedback_service.submit_correlation_suggestion(data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error in submit_correlation_suggestion: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@feedback_bp.route("/suggestions/<int:suggestion_id>/vote", methods=["POST"])
def vote_on_suggestion(suggestion_id):
    """Vote on correlation suggestions"""
    try:
        data = request.get_json()
        vote = data.get('vote') if data else None
        
        if not vote or vote.lower() not in ['up', 'down']:
            return jsonify({
                'success': False,
                'error': 'Valid vote (up/down) is required'
            }), 400
        
        user_info = get_current_user()
        result = feedback_service.vote_on_suggestion(suggestion_id, user_info['user_id'], vote)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error in vote_on_suggestion: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@feedback_bp.route("/business-context", methods=["POST"])
def submit_business_context():
    """Submit business context and local knowledge"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        # Add user information
        user_info = get_current_user()
        data.update(user_info)
        
        # Validate required fields
        required_fields = ['title', 'description']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'success': False,
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400
        
        result = feedback_service.submit_business_context(data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
        
    except Exception as e:
        logger.error(f"Error in submit_business_context: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@feedback_bp.route("/summary")
def get_feedback_summary():
    """Get summary of feedback activity and trends"""
    try:
        days_back = int(request.args.get('days', 30))
        
        result = feedback_service.get_feedback_summary(days_back)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"Error in get_feedback_summary: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@feedback_bp.route("/correlation")
def get_correlation_feedback():
    """Get feedback for correlations"""
    try:
        correlation_id = request.args.get('correlation_id')
        limit = int(request.args.get('limit', 50))
        
        result = feedback_service.get_correlation_feedback(correlation_id, limit)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"Error in get_correlation_feedback: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@feedback_bp.route("/suggestions")
def get_suggestions():
    """Get correlation suggestions"""
    try:
        status = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        
        result = feedback_service.get_suggestions(status, limit)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"Error in get_suggestions: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@feedback_bp.route("/business-context")
def get_business_context():
    """Get business context knowledge"""
    try:
        context_type = request.args.get('context_type')
        store_code = request.args.get('store_code')
        
        result = feedback_service.get_business_context(context_type, store_code)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"Error in get_business_context: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@feedback_bp.route("/accuracy-trends")
def get_accuracy_trends():
    """Get prediction accuracy trends"""
    try:
        days_back = int(request.args.get('days', 90))
        
        result = feedback_service.get_prediction_accuracy_trends(days_back)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"Error in get_accuracy_trends: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@feedback_bp.route("/insights")
def get_feedback_insights():
    """Get actionable insights from feedback data"""
    try:
        result = feedback_service.generate_feedback_insights()
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 500
        
    except Exception as e:
        logger.error(f"Error in get_feedback_insights: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@feedback_bp.route("/analytics/dashboard")
def get_analytics_dashboard_data():
    """Get comprehensive analytics data for feedback dashboard"""
    try:
        days_back = int(request.args.get('days', 30))
        
        # Get multiple data sets for dashboard
        summary = feedback_service.get_feedback_summary(days_back)
        trends = feedback_service.get_prediction_accuracy_trends(days_back)
        insights = feedback_service.generate_feedback_insights()
        
        return jsonify({
            'success': True,
            'dashboard_data': {
                'summary': summary.get('data', summary) if summary['success'] else {},
                'accuracy_trends': trends.get('trends', {}) if trends['success'] else {},
                'insights': insights.get('insights', []) if insights['success'] else [],
                'generated_at': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in get_analytics_dashboard_data: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

# Utility endpoints for frontend integration

@feedback_bp.route("/options/feedback-types")
def get_feedback_types():
    """Get available feedback types"""
    return jsonify({
        'success': True,
        'feedback_types': [
            {'value': 'CORRELATION_RATING', 'label': 'Correlation Rating'},
            {'value': 'PREDICTION_VALIDATION', 'label': 'Prediction Validation'},
            {'value': 'BUSINESS_CONTEXT', 'label': 'Business Context'},
            {'value': 'CORRELATION_SUGGESTION', 'label': 'Correlation Suggestion'},
            {'value': 'DATA_SOURCE_SUGGESTION', 'label': 'Data Source Suggestion'}
        ]
    })

@feedback_bp.route("/options/suggestion-types")
def get_suggestion_types():
    """Get available suggestion types"""
    return jsonify({
        'success': True,
        'suggestion_types': [
            {'value': 'new_correlation', 'label': 'New Correlation'},
            {'value': 'data_source', 'label': 'New Data Source'},
            {'value': 'metric_enhancement', 'label': 'Metric Enhancement'}
        ]
    })

@feedback_bp.route("/options/context-types")
def get_context_types():
    """Get available context types"""
    return jsonify({
        'success': True,
        'context_types': [
            {'value': 'seasonal', 'label': 'Seasonal Patterns'},
            {'value': 'market', 'label': 'Market Conditions'},
            {'value': 'operational', 'label': 'Operational Knowledge'},
            {'value': 'external', 'label': 'External Factors'}
        ]
    })

# Error handler for the blueprint
@feedback_bp.errorhandler(Exception)
def handle_feedback_error(error):
    """Handle any unhandled errors in feedback API"""
    logger.error(f"Feedback API error: {error}")
    return jsonify({
        'success': False,
        'error': 'Internal server error in feedback system'
    }), 500