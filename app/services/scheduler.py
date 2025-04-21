from apscheduler.schedulers.background import BackgroundScheduler
from app.services.refresh import incremental_refresh, full_refresh

def init_scheduler(app):
    """Initialize APScheduler for incremental refreshes with the correct app context."""
    scheduler = BackgroundScheduler()
    
    # Trigger a full refresh on startup
    with app.app_context():
        app.logger.info("Triggering full refresh on startup")
        full_refresh()
        app.logger.info("Full refresh on startup completed")
    
    # Wrap the incremental_refresh function with app context
    def run_with_context():
        with app.app_context():
            incremental_refresh()

    scheduler.add_job(
        func=run_with_context,
        trigger='interval',
        seconds=30,
        id='incremental_refresh',
        replace_existing=True
    )
    scheduler.start()
    app.logger.info("Background scheduler started for incremental refresh")