# handlers/payment.py
from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, BufferedInputFile

import texts
from config import settings
from states import PurchaseStates, RejectStates
from keyboards.client import cancel_flow_menu, main_menu, review_pending_menu
from keyboards.admin import order_review_kb
from services.pdf import generate_ticket_pdf, format_ticket_number
from db.queries import (
    get_active_order,
    get_order,
    get_event,
    get_ticket_type,
    save_screenshot,
    confirm_order,
    reject_order,
    set_reject_reason,
    next_ticket_number,
    create_ticket,
    set_ticket_pdf,
    get_pending_reject_order_by_message,
    set_reject_review_message,
)

router = Router()

MSK = ZoneInfo("Europe/Moscow")


# --- Прием скрина оплаты по активному заказу (в любом состоянии) ---
# Принимаем ТОЛЬКО фото. Документы (в т.ч. файлы-изображения) не принимаем.
@router.message(F.photo | F.document)
async def receive_screenshot(message: Message, state: FSMContext, bot: Bot):
    # Из личных чатов администраторов ничего не обрабатываем как клиентский скрин.
    if message.chat.id in settings.admin_ids:
        return

    active = await get_active_order(message.from_user.id)

    # Документ (файл) не принимаем — просим прислать картинкой. Пока заказ
    # ожидает скрин, не возвращаем основное меню, чтобы отмена оставалась видна.
    if message.document:
        await message.answer(
            "Пришлите скриншот оплаты именно картинкой (фото), а не файлом.",
            reply_markup=cancel_flow_menu() if active else main_menu(),
        )
        return

    if not active:
        await state.clear()
        await message.answer(texts.SCREENSHOT_NO_ORDER, reply_markup=main_menu())
        return

    order_id = active["id"]
    file_id = message.photo[-1].file_id

    saved = await save_screenshot(order_id, file_id)
    if not saved:
        await message.answer(texts.SCREENSHOT_ALREADY, reply_markup=review_pending_menu())
        await state.clear()
        return

    await state.clear()
    await message.answer(texts.SCREENSHOT_ACCEPTED, reply_markup=review_pending_menu())

    order = await get_order(order_id)
    ttype = await get_ticket_type(order["ticket_type_id"])
    ttype_name = ttype["name"] if ttype else "—"

    caption = texts.admin_new_order(
        order_id=order["id"],
        buyer_name=order["buyer_name"],
        buyer_phone=order["buyer_phone"],
        username=order["username"],
        ticket_type_name=ttype_name,
        quantity=order["quantity"],
        total_amount=int(order["total_amount"]),
    )
    for admin_id in settings.admin_ids:
        try:
            await bot.send_photo(
                chat_id=admin_id,
                photo=file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=order_review_kb(order["id"]),
            )
        except Exception:
            # Недоступность одного чата не должна мешать доставке второму админу.
            pass


# --- Подтверждение заявки + генерация и выдача PDF ---
@router.callback_query(F.data.startswith("confirm:"))
async def cb_confirm(callback: CallbackQuery, bot: Bot, role: str | None):
    if role != "admin" or callback.message.chat.id not in settings.admin_ids:
        await callback.answer("Это действие доступно только администраторам.", show_alert=True)
        return

    order_id = int(callback.data.split(":", 1)[1])

    ok = await confirm_order(order_id)
    if not ok:
        await callback.answer(texts.CB_ALREADY_HANDLED, show_alert=True)
        return

    order = await get_order(order_id)
    event = await get_event()
    ttype = await get_ticket_type(order["ticket_type_id"])
    ttype_name = ttype["name"] if ttype else "—"

    quantity = int(order["quantity"])

    try:
        # После отправки скрина клавиатура скрывается через ReplyKeyboardRemove.
        # Явно возвращаем главное меню после решения по заказу, иначе Telegram
        # продолжает держать клавиатуру скрытой у клиента.
        await bot.send_message(
            order["telegram_id"],
            texts.CLIENT_CONFIRMED,
            reply_markup=main_menu(),
        )
        await bot.send_message(
            order["telegram_id"],
            texts.CLIENT_TICKETS_HEADER.format(count=quantity),
        )
    except Exception:
        pass

    for _ in range(quantity):
        number = await next_ticket_number(event["id"])
        ticket_id = await create_ticket(order["id"], order["ticket_type_id"], number)
        pdf_bytes = generate_ticket_pdf(
            event_name=event["name"],
            event_date=str(event["date"]),
            event_location=event["location"],
            ticket_type_name=ttype_name,
            ticket_number=number,
            buyer_name=order["buyer_name"],
            buyer_phone=order["buyer_phone"],
        )
        num_str = format_ticket_number(number)
        doc = BufferedInputFile(pdf_bytes, filename=f"ticket_{num_str}.pdf")
        try:
            sent = await bot.send_document(
                order["telegram_id"],
                document=doc,
                caption=texts.ticket_caption(event["name"], num_str, order["buyer_name"]),
            )
            await set_ticket_pdf(ticket_id, sent.document.file_id)
        except Exception:
            pass

    hhmm = datetime.now(MSK).strftime("%H:%M")
    base = callback.message.caption or callback.message.text or ""
    new_text = texts.admin_confirmed(base, callback.from_user.username, hhmm)

    if callback.message.caption is not None:
        await callback.message.edit_caption(caption=new_text, parse_mode="HTML")
    else:
        await callback.message.edit_text(new_text, parse_mode="HTML")

    await callback.answer(texts.CB_CONFIRMED)


# --- Отклонение заявки: атомарный UPDATE + запрос причины через reply ---
@router.callback_query(F.data.startswith("reject:"))
async def cb_reject(callback: CallbackQuery, role: str | None):
    if role != "admin" or callback.message.chat.id not in settings.admin_ids:
        await callback.answer("Это действие доступно только администраторам.", show_alert=True)
        return

    order_id = int(callback.data.split(":", 1)[1])

    ok = await reject_order(order_id)
    if not ok:
        await callback.answer(texts.CB_ALREADY_HANDLED, show_alert=True)
        return

    base = callback.message.caption or callback.message.text or ""

    # Сохраняем координаты сообщения заявки, чтобы потом найти order_id по reply.
    is_caption = callback.message.caption is not None
    await set_reject_review_message(
        order_id=order_id,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        base_text=base,
        is_caption=is_caption,
    )

    if is_caption:
        await callback.message.edit_caption(
            caption=f"{base}\n\n{texts.ADMIN_WAITING_REASON}",
            parse_mode="HTML",
        )
    else:
        await callback.message.edit_text(
            f"{base}\n\n{texts.ADMIN_WAITING_REASON}",
            parse_mode="HTML",
        )

    await callback.answer(texts.CB_REJECTED, show_alert=True)


# --- Причина отклонения: любой reply на сообщение заявки в админ-чате ---
@router.message(
    F.chat.id.in_(settings.admin_ids),
    F.reply_to_message,
    F.text,
)
async def receive_reject_reason(message: Message, bot: Bot, role: str | None):
    if role != "admin" or message.chat.id not in settings.admin_ids:
        return

    reply = message.reply_to_message
    pending = await get_pending_reject_order_by_message(
        chat_id=message.chat.id,
        message_id=reply.message_id,
    )
    if not pending:
        # reply не на сообщение отклонённой заявки — игнорируем молча.
        return

    order_id = pending["id"]
    reason = message.text.strip()

    await set_reject_reason(order_id, reason)

    order = await get_order(order_id)

    try:
        await bot.send_message(
            order["telegram_id"],
            texts.client_rejected(reason),
            reply_markup=main_menu(),
        )
    except Exception:
        pass

    base = pending["review_base_text"]
    final_text = texts.admin_rejected(base, reason)
    try:
        if pending["review_is_caption"]:
            await bot.edit_message_caption(
                chat_id=pending["review_chat_id"],
                message_id=pending["review_message_id"],
                caption=final_text,
                parse_mode="HTML",
            )
        else:
            await bot.edit_message_text(
                chat_id=pending["review_chat_id"],
                message_id=pending["review_message_id"],
                text=final_text,
                parse_mode="HTML",
            )
    except Exception:
        pass

    await message.reply("Причина отправлена клиенту, заявка отклонена.")
