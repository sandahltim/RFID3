from flask import Blueprint, jsonify, current_app
from app import db, cache
from app.services.api_client import APIClient
from app.services.logger import get_logger
from sqlalchemy.sql import text
import redis
import requests

logger = get_logger(__name__)

health_bp = Blueprint('health', __name__)

# Version marker
logger.info("Deployed health.py version: 2025-04-25-v1")

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
        logger.info("Database health check passed")
        current_app.logger.info("Database health check passed")
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}", exc_info=True)
        current_app.logger.error(f"Database health check failed: {str(e)}", exc_info=True)
        status["database"] = f"unhealthy: {str(e)}"
        status["overall"] = "unhealthy"
    finally:
        pass  # Flask-SQLAlchemy automatically manages session lifecycle

    # Check Redis
    try:
        cache.set("health_check", "ok", timeout=1)
        if cache.get("health_check") == b"ok":
            status["redis"] = "healthy"
            logger.info("Redis health check passed")
            current_app.logger.info("Redis health check passed")
        else:
            logger.error("Redis health check failed: retrieved value mismatch")
            current_app.logger.error("Redis health check failed: retrieved value mismatch")
            status["redis"] = "unhealthy: failed to retrieve test value"
            status["overall"] = "unhealthy"
    except redis.RedisError as e:
        logger.error(f"Redis health check failed: {str(e)}", exc_info=True)
        current_app.logger.error(f"Redis health check failed: {str(e)}", exc_info=True)
        status["redis"] = f"unhealthy: {str(e)}"
        status["overall"] = "unhealthy"

    # Check API
    try:
        client = APIClient()
        ping_url = f"{client.base_url}{client.item_master_endpoint}"
        headers = {"Authorization": f"Bearer {client.token}"}
        ping_response = requests.get(
            ping_url,
            headers=headers,
            params={"limit": 1},
            timeout=5,
        )
        logger.info(f"API ping response status: {ping_response.status_code}")
        current_app.logger.info(
            f"API ping response status: {ping_response.status_code}"
        )
        if ping_response.status_code == 200:
            status["api"] = "healthy"
        else:
            status["api"] = (
                f"unhealthy: status {ping_response.status_code}"
            )
            status["overall"] = "unhealthy"
    except requests.exceptions.RequestException as e:
        logger.error(
            f"API health check failed (RequestException): {str(e)}", exc_info=True
        )
        current_app.logger.error(
            f"API health check failed (RequestException): {str(e)}", exc_info=True
        )
        status["api"] = f"unhealthy: {str(e)}"
        status["overall"] = "unhealthy"
    except Exception as e:
        logger.error(
            f"API health check failed (General Exception): {str(e)}", exc_info=True
        )
        current_app.logger.error(
            f"API health check failed (General Exception): {str(e)}", exc_info=True
        )
        status["api"] = f"unhealthy: {str(e)}"
        status["overall"] = "unhealthy"

    status_code = 200 if status["overall"] == "healthy" else 503
    logger.info(f"Health check completed: {status}")
    current_app.logger.info(f"Health check completed: {status}")
    return jsonify(status), status_code
