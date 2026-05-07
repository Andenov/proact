import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="UTC")


def start_scheduler():
    from app.jobs.tasks import run_daily_pipeline

    scheduler.add_job(
        run_daily_pipeline,
        trigger=CronTrigger(hour=6, minute=0),  # 06:00 UTC daily
        id="daily_pipeline",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — daily pipeline at 06:00 UTC")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
