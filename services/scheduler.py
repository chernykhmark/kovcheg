# services/scheduler.py
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from db.queries import expire_old_orders

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _expire_job() -> None:
    """Ежесуточный джоб авто-expire (п.11). Клиента не уведомляем."""
    count = await expire_old_orders()
    logger.info("Авто-expire: помечено expired заказов: %s", count)


def start_scheduler() -> AsyncIOScheduler:
    """Запуск планировщика: джоб раз в сутки (03:00 МСК)."""
    global _scheduler
    _scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    _scheduler.add_job(
        _expire_job,
        trigger=CronTrigger(hour=3, minute=0),
        id="expire_old_orders",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler запущен (авто-expire раз в сутки в 03:00 МСК).")
    return _scheduler


def stop_scheduler() -> None:
    """Остановка планировщика."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler остановлен.")