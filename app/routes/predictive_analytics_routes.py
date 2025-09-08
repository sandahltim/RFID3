"""
Predictive Analytics Routes
Routes for serving the predictive analytics dashboard interface
"""

from flask import Blueprint, render_template
from datetime import datetime
from app.services.logger import get_logger

logger = get_logger(__name__)

predictive_routes_bp = Blueprint("predictive_routes", __name__, url_prefix="/predictive")

@predictive_routes_bp.route("/analytics")
def predictive_analytics():
    """Main predictive analytics dashboard view"""
    try:
        logger.info("Loading predictive analytics dashboard")
        
        # Add cache bust for JavaScript/CSS files
        cache_bust = str(int(datetime.now().timestamp()))
        
        return render_template("predictive_analytics.html", cache_bust=cache_bust)
        
    except Exception as e:
        logger.error(f"Error loading predictive analytics dashboard: {e}")
        return f"Error loading predictive analytics: {str(e)}", 500