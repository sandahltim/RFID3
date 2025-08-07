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
from .refresh import full_refresh, incremental_refresh
import logging
import os
import time
from sqlalchemy.sql import text
from datetime import datetime
from .logger import get_logger

# Configure logging with process ID
logger = get_logger(
    f'scheduler_{os.getpid()}',
    level=logging.DEBUG,
    log_file=LOG_FILE,
    add_handlers=os.getpid() == os.getppid(),
)

scheduler = BackgroundScheduler()

def init_scheduler(app):
    logger.info("Initializing background scheduler")
    redis_client = Redis.from_url(REDIS_URL)
    lock_key = "full_refresh_lock"
    incremental_lock_key = "incremental_refresh_lock"
    lock_timeout = 300

    def retry_database_connection():
        max_retries = 5
        for attempt in range(max_retries):
            try:
                with app.app_context():
                    db.session.execute(text("SELECT 1")).scalar()
                    logger.info("Database connection test successful")
                    return True
            except Exception as e:
                logger.warning(f"Database connection failed, retrying ({attempt + 1}/{max_retries}): {str(e)}")
                time.sleep(2 ** attempt)
        logger.error("Failed to establish database connection after retries")
        return False

    # Run full refresh on startup
    with app.app_context():
        if retry_database_connection():
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
        else:
            logger.warning("Skipping full refresh due to database connection failure")

    def run_with_context():
        with app.app_context():
            if redis_client.get("full_refresh_lock") or redis_client.get(incremental_lock_key):
                logger.debug("Full refresh or incremental refresh in progress, skipping incremental refresh")
                return
            if retry_database_connection():
                if redis_client.setnx(incremental_lock_key, 1):
                    try:
                        redis_client.expire(incremental_lock_key, lock_timeout)
                        logger.debug("Starting scheduled incremental refresh (item master + transactions)")
                        incremental_refresh()
                        logger.info("Scheduled incremental refresh completed successfully")
                    except Exception as e:
                        logger.error(f"Incremental refresh failed: {str(e)}", exc_info=True)
                    finally:
                        redis_client.delete(incremental_lock_key)
                        logger.debug("Released incremental refresh lock")
                else:
                    logger.debug("Incremental refresh lock exists, skipping refresh")
            else:
                logger.error("Skipping incremental refresh due to database connection failure")

    def run_full_refresh():
        with app.app_context():
            if redis_client.get(incremental_lock_key):
                logger.debug("Incremental refresh in progress, skipping full refresh")
                return
            if retry_database_connection():
                if redis_client.setnx(lock_key, 1):
                    try:
                        redis_client.expire(lock_key, lock_timeout)
                        logger.debug("Starting scheduled full refresh (item master, transactions, seed data)")
                        full_refresh()
                        logger.info("Scheduled full refresh completed successfully")
                    except Exception as e:
                        logger.error(f"Full refresh failed: {str(e)}", exc_info=True)
                    finally:
                        redis_client.delete(lock_key)
                        logger.debug("Released full refresh lock")
                else:
                    logger.debug("Full refresh lock exists, skipping refresh")
            else:
                logger.error("Skipping full refresh due to database connection failure")

    # Schedule incremental refresh based on INCREMENTAL_REFRESH_INTERVAL
    logger.debug(
        f"Adding incremental refresh job to scheduler with interval {INCREMENTAL_REFRESH_INTERVAL} seconds"
    )
    scheduler.add_job(
        func=run_with_context,
        trigger='interval',
        seconds=INCREMENTAL_REFRESH_INTERVAL,
        id='incremental_refresh',
        replace_existing=True,
        coalesce=True,
        max_instances=1
    )

    # Schedule full refresh based on FULL_REFRESH_INTERVAL
    logger.debug(
        f"Adding full refresh job to scheduler with interval {FULL_REFRESH_INTERVAL} seconds"
    )
    scheduler.add_job(
        func=run_full_refresh,
        trigger='interval',
        seconds=FULL_REFRESH_INTERVAL,
        id='full_refresh',
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
    try:
        logger.debug("Starting scheduler")
        scheduler.start()
        logger.info(
            f"Background scheduler started for incremental refresh (item master + transactions) every {INCREMENTAL_REFRESH_INTERVAL} seconds and full refresh (item master, transactions, seed data) every {FULL_REFRESH_INTERVAL} seconds"
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
