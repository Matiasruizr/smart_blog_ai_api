import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import Settings

logger = logging.getLogger(__name__)


async def run_automation_cycle(settings: Settings) -> None:
    from app.services import email_service, trending_service

    logger.info("Automation cycle started")
    try:
        topics = await trending_service.run_trending_cycle(settings)
        logger.info("Scraped and ranked %d topics", len(topics))
        email_service.send_topic_suggestions(topics, settings)
        logger.info("Topic suggestion email sent to %s", settings.email_to_owner)
    except Exception as exc:
        logger.exception("Automation cycle failed: %s", exc)


def create_scheduler(settings: Settings) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_automation_cycle,
        trigger=IntervalTrigger(hours=settings.automation_interval_hours),
        kwargs={"settings": settings},
        id="automation_cycle",
        replace_existing=True,
    )
    return scheduler
