from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app

def init_scheduler():
    """Initialize APScheduler for incremental refreshes."""
    from app.services.refresh import incremental_refresh  # Delayed import
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=incremental_refresh,
        trigger='interval',
        seconds=30,
        id='incremental_refresh',
        replace_existing=True
    )
    scheduler.start()
    current_app.logger.info("Background scheduler started for incremental refresh")