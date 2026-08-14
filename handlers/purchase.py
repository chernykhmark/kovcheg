# handlers/purchase.py
import re

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from states import PurchaseStates, AskQuestionStates
import texts
from config import settings
from keyboards.client import (
    main_menu,
    ticket_types_menu,
    cancel_flow_menu,
    review_pending_menu,
)
from db.queries import (
    get_event,
    get_ticket_types,
    get_active_order,
    cancel_order,
    create_order,
)

router = Router()

PHONE_RE = re.compile(r"^(\+7|8|7)\d{10}$")


def normalize_phone(raw: str) -> str | None:
    phone = re.sub(r"[\s\-()]", "", raw.strip())
    if not PHONE_RE.match(phone):
        return None
    digits = re.sub(r"\D", "", phone)
    return "+7" + digits[-10:]


async def _start_type_selection(message: Message, state: FSMContext):
    event = await get_event()
    if not event:
        await message.answer("Событие не настроено. Обратитесь к организатору.")
        await state.clear()
        return
    types = await get_ticket_types(event["id"])
    if not types:
        await message.answer("Типы билетов не настроены. Обратитесь к организатору.")
        await state.clear()
        return

    await state.update_data(event_id=event["id"])

    if len(types) == 1:
        chosen = types[0]
        await state.update_data(
            ticket_type_id=chosen["id"],
            ticket_type_name=chosen["name"],
        )
        await state.set_state(PurchaseStates.entering_quantity)
        await message.answer(texts.ENTER_QUANTITY, reply_markup=review_pending_menu())
        return

    await state.set_state(PurchaseStates.choosing_type)
    await message.answer(texts.CHOOSE_TYPE, reply_markup=ticket_types_menu(types))


# --- Вход в покупку ---
@router.message(F.text == texts.BTN_BUY)
async def start_purchase(message: Message, state: FSMContext):
    await state.clear()
    active = await get_active_order(message.from_user.id)
    if active:
        if active["screenshot_file_id"]:
            await state.clear()
            await message.answer(texts.ORDER_ON_REVIEW, reply_markup=review_pending_menu())
            return
        await state.set_state(PurchaseStates.waiting_screenshot)
        await state.update_data(order_id=active["id"])
        await message.answer(texts.ORDER_AWAITING_PAYMENT, reply_markup=cancel_flow_menu())
        return
    await _start_type_selection(message, state)


# ============================================================
# ВАЖНО: хэндлеры BTN_ASK и BTN_CANCEL_FLOW идут ВЫШЕ
# ловящих любой текст хэндлеров шагов.
# ============================================================

# --- "Задать вопрос" с любого шага. Заказ в БД сохраняется. ---
@router.message(PurchaseStates.choosing_type, F.text == texts.BTN_ASK)
@router.message(PurchaseStates.entering_quantity, F.text == texts.BTN_ASK)
@router.message(PurchaseStates.entering_name, F.text == texts.BTN_ASK)
@router.message(PurchaseStates.entering_phone, F.text == texts.BTN_ASK)
@router.message(PurchaseStates.waiting_screenshot, F.text == texts.BTN_ASK)
async def ask_during_purchase(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AskQuestionStates.waiting_question)
    await message.answer(texts.ASK_ENTER_QUESTION, reply_markup=main_menu())


# --- "Отменить" доступна только после создания заказа, до отправки скриншота ---
@router.message(PurchaseStates.waiting_screenshot, F.text == texts.BTN_CANCEL_FLOW)
async def cancel_purchase_flow(message: Message, state: FSMContext):
    data = await state.get_data()
    # На этапе оплаты заказ уже создан в БД, поэтому отменяем и его, а не
    # только локальное состояние диалога.
    if order_id := data.get("order_id"):
        await cancel_order(order_id)
    await state.clear()
    await message.answer(texts.PURCHASE_CANCELLED, reply_markup=main_menu())


# --- Выбор типа билета ---
@router.message(PurchaseStates.choosing_type)
async def choose_type(message: Message, state: FSMContext):
    data = await state.get_data()
    event_id = data.get("event_id")
    if event_id is None:
        await state.clear()
        await message.answer(texts.PURCHASE_CANCELLED, reply_markup=main_menu())
        return
    types = await get_ticket_types(event_id)
    chosen = next((t for t in types if t["name"] == message.text), None)
    if not chosen:
        await message.answer(texts.CHOOSE_TYPE, reply_markup=ticket_types_menu(types))
        return
    await state.update_data(ticket_type_id=chosen["id"], ticket_type_name=chosen["name"])
    await state.set_state(PurchaseStates.entering_quantity)
    await message.answer(texts.ENTER_QUANTITY, reply_markup=review_pending_menu())


# --- Ввод количества ---
@router.message(PurchaseStates.entering_quantity)
async def enter_quantity(message: Message, state: FSMContext):
    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer(texts.QUANTITY_INVALID)
        return
    qty = int(text)
    if qty < 1 or qty > 20:
        await message.answer(texts.QUANTITY_INVALID)
        return
    await state.update_data(quantity=qty)
    await state.set_state(PurchaseStates.entering_name)
    await message.answer(texts.ENTER_NAME)


# --- Ввод имени ---
@router.message(PurchaseStates.entering_name)
async def enter_name(message: Message, state: FSMContext):
    name = (message.text or "").strip()
    if not name:
        await message.answer(texts.NAME_INVALID)
        return
    await state.update_data(buyer_name=name)
    await state.set_state(PurchaseStates.entering_phone)
    await message.answer(texts.ENTER_PHONE)


# --- Ввод телефона + создание заказа ---
@router.message(PurchaseStates.entering_phone)
async def enter_phone(message: Message, state: FSMContext):
    phone = normalize_phone(message.text or "")
    if not phone:
        await message.answer(texts.PHONE_INVALID)
        return

    data = await state.get_data()
    quantity = data["quantity"]
    ticket_type_id = data["ticket_type_id"]
    ticket_type_name = data["ticket_type_name"]
    total_amount = settings.TICKET_PRICE * quantity

    order_id = await create_order(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        buyer_name=data["buyer_name"],
        buyer_phone=phone,
        ticket_type_id=ticket_type_id,
        quantity=quantity,
        total_amount=total_amount,
    )

    await state.set_state(PurchaseStates.waiting_screenshot)
    await state.update_data(order_id=order_id)

    await message.answer(
        texts.order_created(
            ticket_type_name=ticket_type_name,
            quantity=quantity,
            total_amount=total_amount,
            sbp_card=settings.SBP_CARD,
            sbp_phone=settings.SBP_PHONE,
            sbp_name=settings.SBP_NAME,
            sbp_bank=settings.SBP_BANK,
        ),
        # До получения скрина клиент видит только безопасную отмену заказа.
        reply_markup=cancel_flow_menu(),
        parse_mode="HTML",
    )
