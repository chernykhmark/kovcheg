# handlers/faq.py
import logging

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import texts
from config import settings
from states import AskQuestionStates
from keyboards.client import main_menu, faq_menu

router = Router()
logger = logging.getLogger(__name__)


# --- Открытие FAQ-подменю (кнопка «Задать вопрос») ---
# D-002: FAQ реализован как reply-подменю внутри «Задать вопрос».
@router.message(F.text == texts.BTN_ASK)
async def open_faq(message: Message):
    await message.answer(texts.FAQ_MENU, reply_markup=faq_menu())


# --- Ответы на готовые вопросы FAQ ---
@router.message(F.text.in_({q for q, _ in texts.FAQ_ITEMS}))
async def faq_answer(message: Message):
    answer = next(a for q, a in texts.FAQ_ITEMS if q == message.text)
    await message.answer(answer, reply_markup=faq_menu())


# --- «Задать свой вопрос»: запрос текста ---
@router.message(F.text == texts.BTN_ASK_OWN)
async def ask_own_start(message: Message, state: FSMContext):
    await state.set_state(AskQuestionStates.waiting_question)
    await message.answer(texts.ASK_ENTER_QUESTION, reply_markup=faq_menu())


# --- «Задать свой вопрос»: получен текст -> пересылка админу ---
@router.message(AskQuestionStates.waiting_question, F.text)
async def ask_own_receive(message: Message, state: FSMContext, bot: Bot):
    text = message.text.strip()

    # Отмена/возврат в меню из состояния вопроса.
    if text == texts.BTN_BACK:
        await state.clear()
        await message.answer(texts.FAQ_MENU, reply_markup=faq_menu())
        return

    await state.clear()

    from_user = message.from_user
    uname = f"@{from_user.username}" if from_user.username else "—"
    admin_text = texts.admin_new_question(
        buyer_name=from_user.full_name,
        username=uname,
        telegram_id=from_user.id,
        question=text,
    )
    for admin_id in settings.admin_ids:
        try:
            await bot.send_message(admin_id, admin_text, parse_mode="HTML")
        except Exception:
            # Недоступность одного чата не должна мешать доставке второму админу.
            logger.warning(
                "Не удалось отправить вопрос администратору %s",
                admin_id,
                exc_info=True,
            )

    await message.answer(texts.ASK_SENT, reply_markup=main_menu())


# --- Возврат из FAQ в главное меню ---
@router.message(F.text == texts.BTN_BACK)
async def faq_back(message: Message):
    await message.answer(texts.MAIN_MENU_BACK, reply_markup=main_menu())
