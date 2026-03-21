"""APScheduler setup: daily scrape at 05:00 CET, weekly source discovery.

AC-1: CronTrigger(hour=5, timezone='Europe/Budapest')
"""
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def run_scrape_job():
    """Full daily scrape pipeline: fetch active sources → scrape → score → enrich → save."""
    from ..database import SessionLocal
    from ..models.source import Source
    from ..models.audit_log import AuditLog
    from sqlalchemy import select
    import time

    start = time.monotonic()
    logger.info("[Scheduler] Starting daily scrape job")

    with SessionLocal() as db:
        db.add(AuditLog(event_type="scrape_start"))
        db.commit()

    articles_found = 0
    articles_saved = 0
    error_msg = None

    try:
        from ..scraper.runner import run_all_spiders
        stats = await run_all_spiders()
        articles_found = stats.get("found", 0)
        articles_saved = stats.get("saved", 0)
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[Scheduler] Scrape job failed: {e}")

    duration_ms = int((time.monotonic() - start) * 1000)

    with SessionLocal() as db:
        db.add(AuditLog(
            event_type="scrape_end",
            articles_found=articles_found,
            articles_saved=articles_saved,
            error_message=error_msg,
            duration_ms=duration_ms,
        ))
        # Update source last_scraped timestamps
        db.query(Source).filter(Source.active == True).update(
            {"last_scraped": datetime.now(timezone.utc)}
        )
        db.commit()

    logger.info(
        f"[Scheduler] Daily scrape complete — found: {articles_found}, "
        f"saved: {articles_saved}, duration: {duration_ms}ms"
    )


async def run_source_discovery():
    """Weekly AI-powered source discovery — finds and adds new Hungarian medical sources."""
    logger.info("[Scheduler] Starting source discovery job")
    try:
        from .source_discovery import run_discovery_and_save
        added = await run_discovery_and_save()
        logger.info(f"[Scheduler] Source discovery complete — added {added} new sources")
    except Exception as e:
        logger.error(f"[Scheduler] Source discovery failed: {e}")


def start_scheduler():
    # AC-1: daily at 05:00 CET (Europe/Budapest)
    scheduler.add_job(
        run_scrape_job,
        CronTrigger(hour=5, minute=0, timezone="Europe/Budapest"),
        id="daily_scrape",
        replace_existing=True,
    )
    # Weekly source discovery: Mondays at 06:00 CET
    scheduler.add_job(
        run_source_discovery,
        CronTrigger(day_of_week="mon", hour=6, timezone="Europe/Budapest"),
        id="weekly_source_discovery",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("[Scheduler] Started — daily scrape 05:00 CET, discovery Mondays 06:00")


def stop_scheduler():
    scheduler.shutdown(wait=False)
