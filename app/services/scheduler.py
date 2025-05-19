from apscheduler.schedulers.background import BackgroundScheduler
from app.services.refresh import incremental_refresh, full_refresh

# Global scheduler instance
scheduler = BackgroundScheduler()

def init_scheduler(app):
    """Initialize APScheduler for incremental refreshes with the correct app context."""
    # Trigger a full refresh on startup
    with app.app_context():
        app.logger.info("Triggering full refresh on startup")
        full_refresh()
        app.logger.info("Full refresh on startup completed")
    
    # Wrap the incremental_refresh function with app context
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
        coalesce=True,  # Prevent overlapping executions
        max_instances=1  # Allow only one instance at a time
    )
    scheduler.start()
    app.logger.info("Background scheduler started for incremental refresh")

def get_scheduler():
    """Return the global scheduler instance."""
    return scheduler