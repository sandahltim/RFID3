# app/routes/performance.py
# Performance monitoring and system health dashboard

from flask import Blueprint, render_template, jsonify, request
from .. import db, cache
from ..services.logger import get_logger
from ..utils.exceptions import handle_api_error, DatabaseException
import psutil
import time
import sys
from datetime import datetime, timedelta
from sqlalchemy import text
from collections import defaultdict
import json

logger = get_logger(__name__)
performance_bp = Blueprint("performance", __name__)

# Performance metrics storage (in-memory for simplicity)
performance_metrics = {
    "request_times": defaultdict(list),
    "endpoint_calls": defaultdict(int),
    "error_counts": defaultdict(int),
    "last_reset": datetime.now(),
}


def track_performance(endpoint, response_time, status_code):
    """Track performance metrics for an endpoint."""
    current_time = datetime.now()

    # Store response time (keep last 100 entries)
    if len(performance_metrics["request_times"][endpoint]) >= 100:
        performance_metrics["request_times"][endpoint].pop(0)
    performance_metrics["request_times"][endpoint].append(
        {
            "time": response_time,
            "timestamp": current_time.isoformat(),
            "status": status_code,
        }
    )

    # Increment call count
    performance_metrics["endpoint_calls"][endpoint] += 1

    # Track errors
    if status_code >= 400:
        performance_metrics["error_counts"][endpoint] += 1


@performance_bp.route("/performance")
def performance_dashboard():
    """Performance monitoring dashboard page."""
    logger.info("Loading performance monitoring dashboard")
    return render_template("performance.html")


@performance_bp.route("/api/performance/system", methods=["GET"])
@handle_api_error
def get_system_metrics():
    """Get system-level performance metrics."""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Process-specific metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        process_cpu = process.cpu_percent()

        # Python metrics
        python_version = sys.version
        thread_count = len(process.threads())

        return jsonify(
            {
                "system": {
                    "cpu_percent": cpu_percent,
                    "memory_total": memory.total,
                    "memory_available": memory.available,
                    "memory_percent": memory.percent,
                    "disk_total": disk.total,
                    "disk_free": disk.free,
                    "disk_percent": (disk.used / disk.total) * 100,
                },
                "process": {
                    "memory_rss": process_memory.rss,
                    "memory_vms": process_memory.vms,
                    "cpu_percent": process_cpu,
                    "thread_count": thread_count,
                    "python_version": python_version,
                },
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Failed to get system metrics: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@performance_bp.route("/api/performance/database", methods=["GET"])
@handle_api_error
def get_database_metrics():
    """Get database performance metrics."""
    try:
        metrics = {}

        # Connection pool status (if available)
        try:
            # Get database connection info
            result = db.session.execute(text("SELECT version();"))
            db_version = result.scalar()
            metrics["database_version"] = db_version
        except Exception as e:
            metrics["database_version"] = f"Error: {str(e)}"

        # Table sizes and row counts
        try:
            tables = ["id_item_master", "id_transactions", "inventory_health_alerts"]
            table_stats = {}

            for table in tables:
                try:
                    # Get row count
                    count_result = db.session.execute(
                        text(f"SELECT COUNT(*) FROM {table}")
                    )
                    row_count = count_result.scalar()
                    table_stats[table] = {"row_count": row_count}
                except Exception as e:
                    table_stats[table] = {"error": str(e)}

            metrics["table_stats"] = table_stats
        except Exception as e:
            metrics["table_stats_error"] = str(e)

        # Recent query performance (simplified)
        metrics["connection_status"] = "healthy"
        metrics["timestamp"] = datetime.now().isoformat()

        return jsonify(metrics)

    except Exception as e:
        logger.error(f"Failed to get database metrics: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@performance_bp.route("/api/performance/application", methods=["GET"])
@handle_api_error
def get_application_metrics():
    """Get application-level performance metrics."""
    try:
        current_time = datetime.now()

        # Calculate averages for each endpoint
        endpoint_stats = {}
        for endpoint, times in performance_metrics["request_times"].items():
            if times:
                avg_time = sum(entry["time"] for entry in times) / len(times)
                max_time = max(entry["time"] for entry in times)
                min_time = min(entry["time"] for entry in times)

                # Recent performance (last 10 requests)
                recent_times = times[-10:]
                recent_avg = (
                    sum(entry["time"] for entry in recent_times) / len(recent_times)
                    if recent_times
                    else 0
                )

                endpoint_stats[endpoint] = {
                    "call_count": performance_metrics["endpoint_calls"][endpoint],
                    "error_count": performance_metrics["error_counts"][endpoint],
                    "avg_response_time": round(avg_time, 3),
                    "max_response_time": round(max_time, 3),
                    "min_response_time": round(min_time, 3),
                    "recent_avg_response_time": round(recent_avg, 3),
                    "error_rate": (
                        (
                            performance_metrics["error_counts"][endpoint]
                            / performance_metrics["endpoint_calls"][endpoint]
                            * 100
                        )
                        if performance_metrics["endpoint_calls"][endpoint] > 0
                        else 0
                    ),
                }

        # Cache metrics
        cache_stats = {}
        try:
            # Redis info (if available)
            redis_info = (
                cache.connection_pool.connection_kwargs
                if hasattr(cache, "connection_pool")
                else {}
            )
            cache_stats["redis_host"] = redis_info.get("host", "unknown")
            cache_stats["redis_port"] = redis_info.get("port", "unknown")
        except Exception as e:
            cache_stats["redis_error"] = str(e)

        return jsonify(
            {
                "uptime_since": performance_metrics["last_reset"].isoformat(),
                "current_time": current_time.isoformat(),
                "endpoints": endpoint_stats,
                "total_requests": sum(performance_metrics["endpoint_calls"].values()),
                "total_errors": sum(performance_metrics["error_counts"].values()),
                "cache": cache_stats,
            }
        )

    except Exception as e:
        logger.error(f"Failed to get application metrics: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@performance_bp.route("/api/performance/reset", methods=["POST"])
@handle_api_error
def reset_performance_metrics():
    """Reset performance metrics (for testing/maintenance)."""
    try:
        global performance_metrics
        performance_metrics = {
            "request_times": defaultdict(list),
            "endpoint_calls": defaultdict(int),
            "error_counts": defaultdict(int),
            "last_reset": datetime.now(),
        }

        logger.info("Performance metrics reset")
        return jsonify({"message": "Performance metrics reset successfully"})

    except Exception as e:
        logger.error(f"Failed to reset performance metrics: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# Middleware to automatically track performance
def track_request_performance():
    """Middleware to automatically track request performance."""

    def before_request():
        request.start_time = time.time()

    def after_request(response):
        if hasattr(request, "start_time"):
            response_time = (
                time.time() - request.start_time
            ) * 1000  # Convert to milliseconds
            endpoint = request.endpoint or "unknown"

            # Track the performance
            track_performance(endpoint, response_time, response.status_code)

            # Add performance headers
            response.headers["X-Response-Time"] = f"{response_time:.3f}ms"

        return response

    return before_request, after_request


# Helper function to get performance summary
def get_performance_summary():
    """Get a quick performance summary for health checks."""
    try:
        total_requests = sum(performance_metrics["endpoint_calls"].values())
        total_errors = sum(performance_metrics["error_counts"].values())
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0

        # Calculate average response time across all endpoints
        all_times = []
        for times in performance_metrics["request_times"].values():
            all_times.extend([entry["time"] for entry in times])

        avg_response_time = sum(all_times) / len(all_times) if all_times else 0

        # System health
        cpu_percent = psutil.cpu_percent()
        memory_percent = psutil.virtual_memory().percent

        return {
            "status": (
                "healthy" if error_rate < 5 and avg_response_time < 1000 else "degraded"
            ),
            "total_requests": total_requests,
            "error_rate": round(error_rate, 2),
            "avg_response_time": round(avg_response_time, 2),
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "uptime_minutes": (
                datetime.now() - performance_metrics["last_reset"]
            ).total_seconds()
            / 60,
        }
    except Exception as e:
        logger.error(f"Failed to generate performance summary: {str(e)}")
        return {"status": "error", "error": str(e)}
