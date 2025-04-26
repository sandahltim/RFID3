from flask import Blueprint, jsonify, current_app
from app import db, cache
from app.services.api_client import APIClient
from sqlalchemy.sql import text
import redis
import requests
import logging
import sys

# Configure logging
logger = logging.getLogger('health')
logger.setLevel(logging.INFO)

# Remove existing handlers to avoid duplicates
logger.handlers = []

# File handler for rfid_dashboard.log
file_handler = logging.FileHandler('/home/tim/test_rfidpi/logs/rfid_dashboard.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

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
        auth_response = client.authenticate()
        logger.info(f"API authentication response: {auth_response}")
        current_app.logger.info(f"API authentication response: {auth_response}")
        status["api"] = "healthy"
    except requests.exceptions.RequestException as e:
        logger.error(f"API health check failed (RequestException): {str(e)}", exc_info=True)
        current_app.logger.error(f"API health check failed (RequestException): {str(e)}", exc_info=True)
        status["api"] = f"unhealthy: {str(e)}"
        status["overall"] = "unhealthy"
    except Exception as e:
        logger.error(f"API health check failed (General Exception): {str(e)}", exc_info=True)
        current_app.logger.error(f"API health check failed (General Exception): {str(e)}", exc_info=True)
        status["api"] = f"unhealthy: {str(e)}"
        status["overall"] = "unhealthy"

    status_code = 200 if status["overall"] == "healthy" else 503
    logger.info(f"Health check completed: {status}")
    current_app.logger.info(f"Health check completed: {status}")
    return jsonify(status), status_code