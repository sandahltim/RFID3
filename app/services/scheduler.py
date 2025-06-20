# app/services/scheduler.py
# scheduler.py version: 2025-06-20-v3
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.refresh import incremental_refresh, full_refresh
from redis import Redis
from config import REDIS_URL
import time
import logging
import sys

# Configure logging
logger = logging.getLogger('scheduler')
logger.setLevel(logging.DEBUG)

# Remove existing handlers to avoid duplicates
logger.handlers = []

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
    lock_timeout = 120

    with app.app_context():
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
            max_wait = 30
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
                logger.warning("Full refresh lock not released after 30s, skipping startup refresh")

    def run_with_context():
        with app.app_context():
            try:
                logger.debug("Starting scheduled incremental refresh")
                incremental_refresh()
                logger.info("Scheduled incremental refresh completed successfully")
            except Exception as e:
                logger.error(f"Scheduled incremental refresh failed: {str(e)}", exc_info=True)
                raise

    logger.debug("Adding incremental refresh job to scheduler")
    scheduler.add_job(
        func=run_with_context,
        trigger='interval',
        seconds=30,
        id='incremental_refresh',
        replace_existing=True,
        coalesce=True,
        max_instances=2  # Increased to allow more concurrent runs
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