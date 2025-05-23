from apscheduler.schedulers.background import BackgroundScheduler
from app.services.refresh import incremental_refresh, full_refresh
from redis import Redis
from config import REDIS_URL
import time

scheduler = BackgroundScheduler()

def init_scheduler(app):
    redis_client = Redis.from_url(REDIS_URL)
    lock_key = "full_refresh_lock"
    lock_timeout = 300

    with app.app_context():
        if redis_client.setnx(lock_key, 1):
            try:
                redis_client.expire(lock_key, lock_timeout)
                app.logger.info("Triggering full refresh on startup")
                full_refresh()
                app.logger.info("Full refresh on startup completed")
            finally:
                redis_client.delete(lock_key)
        else:
            max_wait = 30
            waited = 0
            while redis_client.exists(lock_key) and waited < max_wait:
                time.sleep(1)
                waited += 1
            if not redis_client.exists(lock_key):
                if redis_client.setnx(lock_key, 1):
                    try:
                        redis_client.expire(lock_key, lock_timeout)
                        app.logger.info("Triggering full refresh on startup")
                        full_refresh()
                        app.logger.info("Full refresh on startup completed")
                    finally:
                        redis_client.delete(lock_key)

    def run_with_context():
        with app.app_context():
            try:
                app.logger.debug("Starting scheduled incremental refresh")
                incremental_refresh()
                app.logger.debug("Scheduled incremental refresh completed")
            except Exception as e:
                app.logger.error(f"Scheduled incremental refresh failed: {str(e)}", exc_info=True)
                raise

    scheduler.add_job(
        func=run_with_context,
        trigger='interval',
        seconds=30,
        id='incremental_refresh',
        replace_existing=True,
        coalesce=True,
        max_instances=1
    )
    scheduler.start()
    app.logger.info("Background scheduler started for incremental refresh")

def get_scheduler():
    return scheduler
