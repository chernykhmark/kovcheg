# keyboards/admin.py
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

import texts


def admin_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=texts.BTN_EXPORT)],
            [KeyboardButton(text=texts.BTN_BROADCAST)],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def order_review_kb(order_id: int) -> InlineKeyboardMarkup:
    """Кнопки под заявкой в админ-чате."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=texts.BTN_CONFIRM, callback_data=f"confirm:{order_id}"
                ),
                InlineKeyboardButton(
                    text=texts.BTN_REJECT, callback_data=f"reject:{order_id}"
                ),
            ]
        ]
    )


def broadcast_confirm_kb() -> InlineKeyboardMarkup:
    """Подтверждение запуска рассылки."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=texts.BTN_BROADCAST_SEND, callback_data="bcast:send"
                ),
                InlineKeyboardButton(
                    text=texts.BTN_BROADCAST_CANCEL, callback_data="bcast:cancel"
                ),
            ]
        ]
    )