# app/services/scheduler.py
# scheduler.py version: 2025-06-20-v9
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.refresh import incremental_refresh, full_refresh
from redis import Redis
from config import REDIS_URL
import time
import logging
import sys
import os
from .. import db  # Import db from the application package
from sqlalchemy.sql import text

# Configure logging with process ID to avoid duplicates
logger = logging.getLogger(f'scheduler_{os.getpid()}')
logger.setLevel(logging.DEBUG)
if not logger.handlers and os.getpid() == os.getppid():  # Initialize only in main process
    # File handler for rfid_dashboard.log
    file_handler = logging.FileHandler('/home/tim/test_rfidpi/logs/rfid_dashboard.log')
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

scheduler = BackgroundScheduler()

def init_scheduler(app):
    logger.info("Initializing background scheduler")
    redis_client = Redis.from_url(REDIS_URL)
    lock_key = "full_refresh_lock"
    lock_timeout = 300

    def retry_database_connection():
        max_retries = 5
        for attempt in range(max_retries):
            try:
                with app.app_context():
                    db.session.execute(text("SELECT 1")).scalar()  # Use text() for SQL expression
                    return True
            except Exception as e:
                logger.warning(f"Database connection failed, retrying ({attempt + 1}/{max_retries}): {str(e)}")
                time.sleep(2 ** attempt)
        logger.error("Failed to establish database connection after retries")
        return False

    with app.app_context():
        if not retry_database_connection():
            logger.warning("Skipping scheduler initialization due to database connection failure")
            return

        logger.debug("Checking for full refresh lock")
        if redis_client.setnx(lock_key, 1):
            try:
                redis_client.expire(lock_key, lock_timeout)
                logger.info("Triggering full refresh on startup")
                full_refresh()
                logger.info("Full refresh on startup completed successfully")
            except Exception as e:
                logger.error(f"Full refresh on startup failed: {str(e)}", exc_info=True)
            finally:
                redis_client.delete(lock_key)
                logger.debug("Released full refresh lock")
        else:
            max_wait = 120
            waited = 0
            logger.info("Full refresh lock exists, waiting for release")
            while redis_client.exists(lock_key) and waited < max_wait:
                time.sleep(1)
                waited += 1
                logger.debug(f"Waiting for lock release, elapsed: {waited}s")
            if not redis_client.exists(lock_key):
                if redis_client.setnx(lock_key, 1):
                    try:
                        redis_client.expire(lock_key, lock_timeout)
                        logger.info("Triggering full refresh on startup (after wait)")
                        full_refresh()
                        logger.info("Full refresh on startup completed successfully")
                    except Exception as e:
                        logger.error(f"Full refresh on startup failed: {str(e)}", exc_info=True)
                    finally:
                        redis_client.delete(lock_key)
                        logger.debug("Released full refresh lock")
            else:
                logger.warning("Full refresh lock not released after 120s, forcing release and skipping startup refresh")
                redis_client.delete(lock_key)

    def run_with_context():
        with app.app_context():
            if retry_database_connection():
                logger.debug("Starting scheduled incremental refresh")
                incremental_refresh()
                logger.info("Scheduled incremental refresh completed successfully")
            else:
                logger.error("Skipping incremental refresh due to database connection failure")

    logger.debug("Adding incremental refresh job to scheduler")
    scheduler.add_job(
        func=run_with_context,
        trigger='interval',
        seconds=60,
        id='incremental_refresh',
        replace_existing=True,
        coalesce=True,
        max_instances=1
    )
    try:
        logger.debug("Starting scheduler")
        scheduler.start()
        logger.info("Background scheduler started for incremental refresh")
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