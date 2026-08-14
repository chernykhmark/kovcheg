# handlers/start.py
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

import texts
from keyboards.client import main_menu
from keyboards.admin import admin_menu

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, role: str | None):
    await message.answer(texts.WELCOME, reply_markup=main_menu())
    if role in ("admin", "observer"):
        await message.answer(texts.ADMIN_MENU, reply_markup=admin_menu())


@router.message(Command("admin"))
async def cmd_admin(message: Message, role: str | None):
    if role in ("admin", "observer"):
        await message.answer(texts.ADMIN_MENU, reply_markup=admin_menu())