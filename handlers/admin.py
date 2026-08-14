# handlers/admin.py
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile

import texts
from states import BroadcastStates
from keyboards.admin import broadcast_confirm_kb
from services.excel import build_export_xlsx
from services.broadcast import run_broadcast

router = Router()

MSK = ZoneInfo("Europe/Moscow")


@router.message(F.text == texts.BTN_EXPORT)
async def export_excel(message: Message, role: str | None):
    # доступ только для admin/observer
    if role not in ("admin", "observer"):
        return

    xlsx_bytes = await build_export_xlsx()
    stamp = datetime.now(MSK).strftime("%Y%m%d_%H%M")
    doc = BufferedInputFile(xlsx_bytes, filename=f"tickets_{stamp}.xlsx")
    await message.answer_document(doc, caption=texts.EXPORT_CAPTION)


# --- Рассылка: старт (запрос текста) ---
@router.message(F.text == texts.BTN_BROADCAST)
async def broadcast_start(message: Message, state: FSMContext, role: str | None):
    # доступ только для admin/observer
    if role not in ("admin", "observer"):
        return
    await state.set_state(BroadcastStates.waiting_text)
    await message.answer(texts.BROADCAST_ENTER_TEXT)


# --- Рассылка: получен текст -> подтверждение ---
@router.message(BroadcastStates.waiting_text, F.text)
async def broadcast_text(message: Message, state: FSMContext):
    text = message.text
    await state.update_data(broadcast_text=text)
    await state.set_state(BroadcastStates.confirming)
    await message.answer(
        texts.broadcast_preview(text),
        reply_markup=broadcast_confirm_kb(),
    )


# --- Рассылка: отмена ---
@router.callback_query(BroadcastStates.confirming, F.data == "bcast:cancel")
async def broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(texts.BROADCAST_CANCELLED)
    await callback.answer()


# --- Рассылка: запуск ---
@router.callback_query(BroadcastStates.confirming, F.data == "bcast:send")
async def broadcast_send(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    text = data.get("broadcast_text", "")
    await state.clear()

    await callback.message.edit_text(texts.BROADCAST_STARTED)
    await callback.answer()

    recipients, delivered = await run_broadcast(bot, text)
    await callback.message.answer(texts.broadcast_result(recipients, delivered))