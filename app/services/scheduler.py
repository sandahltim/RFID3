# app/services/scheduler.py
# scheduler.py version: 2025-06-27-v7
from apscheduler.schedulers.background import BackgroundScheduler
from redis import Redis
from config import (
    REDIS_URL,
    INCREMENTAL_REFRESH_INTERVAL,
    FULL_REFRESH_INTERVAL,
    LOG_FILE,
)
from .. import db, cache


# Lazy import refresh functions to avoid startup issues
def get_refresh_functions():
    from .refresh import full_refresh, incremental_refresh

    return full_refresh, incremental_refresh


import logging
import os
import time
from sqlalchemy.sql import text
from datetime import datetime
from .logger import get_logger
from contextlib import contextmanager

# Configure logging with process ID
logger = get_logger(
    f"scheduler_{os.getpid()}",
    level=logging.DEBUG,
    log_file=LOG_FILE,
    add_handlers=os.getpid() == os.getppid(),
)

scheduler = BackgroundScheduler()


class LockError(Exception):
    """Raised when a Redis lock cannot be acquired."""

    pass


@contextmanager
def acquire_lock(redis_client, name, timeout):
    """Context manager for Redis locks with automatic cleanup."""
    if not redis_client.setnx(name, "1"):
        raise LockError(f"Could not acquire lock: {name}")
    try:
        redis_client.expire(name, timeout)
        yield
    finally:
        redis_client.delete(name)


def init_scheduler(app):
    logger.info("Initializing background scheduler")
    redis_client = Redis.from_url(REDIS_URL)
    csv_import_lock_key = "csv_import_lock"
    csv_import_lock_timeout = 1800  # 30 minutes for CSV import
    lock_key = "full_refresh_lock"
    incremental_lock_key = "incremental_refresh_lock"
    lock_timeout = 300  # 5 minutes for incremental refresh
    full_refresh_lock_timeout = 1800  # 30 minutes for full refresh

    def retry_database_connection():
        max_retries = 5
        for attempt in range(max_retries):
            try:
                with app.app_context():
                    db.session.execute(text("SELECT 1")).scalar()
                    logger.info("Database connection test successful")
                    return True
            except Exception as e:
                logger.warning(
                    f"Database connection failed, retrying ({attempt + 1}/{max_retries}): {str(e)}"
                )
                time.sleep(2**attempt)
        logger.error("Failed to establish database connection after retries")
        return False

    # TEMPORARILY DISABLED for bug testing
    # with app.app_context():
    #     if retry_database_connection():
    #         logger.debug("Checking for full refresh lock")
    #         try:
    #             with acquire_lock(redis_client, lock_key, lock_timeout):
    #                 logger.info("Triggering full refresh on startup (backup fallback enabled)")
    #                 full_refresh, _ = get_refresh_functions()
    #                 full_refresh()
    #                 logger.info("Full refresh on startup completed successfully")
    # except LockError:
    #     logger.info("Full refresh lock exists, waiting for release")
    #     max_wait = 120
    #     waited = 0
    #     while redis_client.exists(lock_key) and waited < max_wait:
    #         time.sleep(1)
    #         waited += 1
    #         logger.debug(f"Waiting for lock release, elapsed: {waited}s")
    #
    #     # Try again after waiting
    #     try:
    #         with acquire_lock(redis_client, lock_key, lock_timeout):
    #             logger.info("Triggering full refresh on startup (after wait, backup fallback enabled)")
    #             full_refresh, _ = get_refresh_functions()
    #             full_refresh()
    #             logger.info("Full refresh on startup completed successfully")
    #     except LockError:
    #         logger.warning("Full refresh lock still exists after waiting, forcing release and skipping startup refresh")
    #         redis_client.delete(lock_key)
    # else:
    #     logger.warning("Skipping full refresh due to database connection failure")

    def run_with_context():
        with app.app_context():
            if redis_client.get("full_refresh_lock") or redis_client.get(
                incremental_lock_key
            ):
                logger.debug(
                    "Full refresh or incremental refresh in progress, skipping incremental refresh"
                )
                return
            if retry_database_connection():
                try:
                    with acquire_lock(redis_client, incremental_lock_key, lock_timeout):
                        logger.debug(
                            "Starting scheduled incremental refresh (item master + transactions)"
                        )
                        _, incremental_refresh = get_refresh_functions()
                        incremental_refresh()
                        logger.info(
                            "Scheduled incremental refresh completed successfully"
                        )
                except LockError:
                    logger.debug("Incremental refresh lock exists, skipping refresh")
                except Exception as e:
                    logger.error(f"Incremental refresh failed: {str(e)}", exc_info=True)
            else:
                logger.error(
                    "Skipping incremental refresh due to database connection failure"
                )

    def run_full_refresh():
        with app.app_context():
            if redis_client.get(incremental_lock_key):
                logger.debug("Incremental refresh in progress, skipping full refresh")
                return
            if retry_database_connection():
                try:
                    with acquire_lock(redis_client, lock_key, full_refresh_lock_timeout):
                        logger.debug(
                            "Starting scheduled full refresh (item master, transactions, seed data)"
                        )
                        full_refresh, _ = get_refresh_functions()
                        full_refresh()
                        logger.info("Scheduled full refresh completed successfully")
                except LockError:
                    logger.debug("Full refresh lock exists, skipping refresh")
                except Exception as e:
                    logger.error(f"Full refresh failed: {str(e)}", exc_info=True)
            else:
                logger.error("Skipping full refresh due to database connection failure")

    # Schedule incremental refresh based on INCREMENTAL_REFRESH_INTERVAL
    logger.debug(
        f"Adding incremental refresh job to scheduler with interval {INCREMENTAL_REFRESH_INTERVAL} seconds"
    )
    scheduler.add_job(
        func=run_with_context,
        trigger="interval",
        seconds=INCREMENTAL_REFRESH_INTERVAL,
        id="incremental_refresh",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )

    # Schedule full refresh based on FULL_REFRESH_INTERVAL
    logger.debug(
        f"Adding full refresh job to scheduler with interval {FULL_REFRESH_INTERVAL} seconds"
    )
    scheduler.add_job(
        func=run_full_refresh,
        trigger="interval",
        seconds=FULL_REFRESH_INTERVAL,
        id="full_refresh",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )

    # Define Tuesday CSV import function within scheduler scope
    def run_tuesday_csv_imports():
        """Run comprehensive CSV imports for all POS data - Tuesdays at 8am"""
        with app.app_context():
            # Skip if any existing refresh is running
            if redis_client.get("full_refresh_lock") or redis_client.get(incremental_lock_key) or redis_client.get(csv_import_lock_key):
                logger.debug("Other operations in progress, skipping CSV import")
                return
            if retry_database_connection():
                try:
                    with acquire_lock(redis_client, csv_import_lock_key, csv_import_lock_timeout):
                        logger.info("🚀 Starting Tuesday 8am CSV imports (all POS files)")
                        
                        from .fixed_pos_import_service import fixed_pos_import_service

                        import_results = fixed_pos_import_service.import_all_pos_data()
                        successful = import_results.get("total_imported", 0)
                        failed = import_results.get("total_failed", 0)
                        logger.info(f"🏁 Tuesday CSV imports completed: {successful} imported, {failed} failed")
                        
                except LockError:
                    logger.debug("CSV import lock exists, skipping import")
                except Exception as e:
                    logger.error(f"Tuesday CSV import failed: {str(e)}", exc_info=True)
            else:
                logger.error("Skipping CSV import due to database connection failure")

    # Schedule Tuesday 8am CSV import
    logger.info("Adding Tuesday 8am CSV import job to scheduler")
    scheduler.add_job(
        func=run_tuesday_csv_imports,
        trigger="cron",
        day_of_week="tue",
        hour=8,
        minute=0,
        id="tuesday_csv_import",
        replace_existing=True,
        coalesce=True,
        max_instances=1
    )
    try:
        logger.debug("Starting scheduler")
        scheduler.start()
        logger.info(
            f"Background scheduler started:\n- Incremental refresh (item master + transactions) every {INCREMENTAL_REFRESH_INTERVAL} seconds\n- Full refresh (item master, transactions, seed data) every {FULL_REFRESH_INTERVAL} seconds\n- Tuesday 8am CSV import for all POS data files"
        )
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}", exc_info=True)
        raise

    # Ensure scheduler shuts down with the app
    import atexit

    atexit.register(lambda: scheduler.shutdown())
    logger.info("Registered scheduler shutdown hook")


def get_scheduler():
    logger.debug("Returning scheduler instance")
    return scheduler

