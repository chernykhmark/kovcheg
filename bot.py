# bot.py
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession   # + добавить

from config import settings
from db.pool import init_pool, close_pool
from middlewares import RoleMiddleware
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

    session = AiohttpSession(proxy="socks5://127.0.0.1:1080")   # + прокси
    bot = Bot(token=settings.BOT_TOKEN, session=session)        # изменено

    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(RoleMiddleware())
    dp.callback_query.middleware(RoleMiddleware())

    register_routers(dp)

    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await close_pool()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
