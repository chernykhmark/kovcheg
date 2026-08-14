# services/broadcast.py
import asyncio
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError

from db.queries import get_broadcast_recipients, log_broadcast

logger = logging.getLogger(__name__)

# ~20 сообщений/сек -> пауза между отправками
SEND_DELAY = 0.05


async def run_broadcast(bot: Bot, text: str) -> tuple[int, int]:
    """
    Рассылка текста всем клиентам (п.12).
    Возвращает (recipients_count, delivered_count), пишет лог в broadcasts.
    """
    recipients = await get_broadcast_recipients()
    recipients_count = len(recipients)
    delivered = 0

    for tg_id in recipients:
        try:
            await bot.send_message(tg_id, text)
            delivered += 1
        except TelegramRetryAfter as e:
            # флуд-контроль: ждем и повторяем один раз
            await asyncio.sleep(e.retry_after)
            try:
                await bot.send_message(tg_id, text)
                delivered += 1
            except Exception:
                logger.warning("Broadcast: не доставлено %s после RetryAfter", tg_id)
        except TelegramForbiddenError:
            # клиент заблокировал бота — пропускаем, не считаем доставленным
            logger.info("Broadcast: %s заблокировал бота", tg_id)
        except Exception:
            logger.warning("Broadcast: ошибка отправки %s", tg_id, exc_info=True)

        await asyncio.sleep(SEND_DELAY)

    await log_broadcast(text, recipients_count, delivered)
    logger.info("Broadcast завершен: %s/%s", delivered, recipients_count)
    return recipients_count, delivered