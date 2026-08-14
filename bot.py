# bot.py
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from db.pool import init_pool, close_pool
from middlewares import RoleMiddleware
from services.scheduler import start_scheduler, stop_scheduler
from handlers import start, purchase, payment, tickets, admin, faq

logging.basicConfig(level=logging.INFO)


def register_routers(dp: Dispatcher) -> None:
    dp.include_router(start.router)
    dp.include_router(purchase.router)
    dp.include_router(payment.router)
    dp.include_router(tickets.router)
    dp.include_router(admin.router)
    dp.include_router(faq.router)


async def main() -> None:
    await init_pool()
    start_scheduler()

    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # middleware ролей на сообщения и колбэки
    dp.message.middleware(RoleMiddleware())
    dp.callback_query.middleware(RoleMiddleware())

    register_routers(dp)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        stop_scheduler()
        await close_pool()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())