import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.blocking import BlockingScheduler

from app.config.loader import sync_sources
from app.core.settings import get_settings
from app.db.session import SessionLocal, init_db
from app.models import Source
from app.services.ingestion import run_source_scrape


async def run_all_sources() -> None:
    db = SessionLocal()
    try:
        sync_sources(db)
        sources = db.query(Source).filter(Source.enabled.is_(True)).all()
        for source in sources:
            await run_source_scrape(db, source)
    finally:
        db.close()


def start_scheduler() -> None:
    settings = get_settings()
    init_db()
    hour, minute = [int(part) for part in settings.daily_scrape_time.split(":", 1)]
    scheduler = BlockingScheduler(timezone=ZoneInfo(settings.app_timezone))
    scheduler.add_job(lambda: asyncio.run(run_all_sources()), "cron", hour=hour, minute=minute, id="daily_scrape", replace_existing=True)
    print(f"Scheduler ready. Daily scrape at {settings.daily_scrape_time} {settings.app_timezone}.")
    if settings.scrape_enabled:
        scheduler.start()
    else:
        print("SCRAPE_ENABLED=false; worker is idle.")
