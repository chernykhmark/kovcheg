# middlewares.py
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from db.pool import get_pool


class RoleMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        role = None
        if user is not None:
            pool = get_pool()
            role = await pool.fetchval(
                "SELECT role FROM users WHERE telegram_id = $1", user.id
            )
        data["role"] = role
        return await handler(event, data)