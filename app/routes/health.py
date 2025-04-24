from flask import Blueprint, jsonify, current_app
from app import db, cache
from app.services.api_client import APIClient
from sqlalchemy.sql import text
import redis

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    status = {
        "database": "unknown",
        "redis": "unknown",
        "api": "unknown",
        "overall": "healthy"
    }

    # Check database
    try:
        db.session.execute(text("SELECT 1"))
        status["database"] = "healthy"
    except Exception as e:
        current_app.logger.error(f"Database health check failed: {str(e)}")
        status["database"] = f"unhealthy: {str(e)}"
        status["overall"] = "unhealthy"

    # Check Redis
    try:
        cache.set("health_check", "ok", timeout=1)
        if cache.get("health_check") == b"ok":
            status["redis"] = "healthy"
        else:
            status["redis"] = "unhealthy: failed to retrieve test value"
            status["overall"] = "unhealthy"
    except redis.RedisError as e:
        current_app.logger.error(f"Redis health check failed: {str(e)}")
        status["redis"] = f"unhealthy: {str(e)}"
        status["overall"] = "unhealthy"

    # Check API
    try:
        client = APIClient()
        client.authenticate()
        status["api"] = "healthy"
    except Exception as e:
        current_app.logger.error(f"API health check failed: {str(e)}")
        status["api"] = f"unhealthy: {str(e)}"
        status["overall"] = "unhealthy"

    status_code = 200 if status["overall"] == "healthy" else 503
    return jsonify(status), status_code