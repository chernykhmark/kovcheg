# keyboards/client.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, WebAppInfo

import texts
from config import settings


def main_menu() -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text=texts.BTN_BUY)]]
    # Telegram открывает Web App только по HTTPS URL. Оставляем настройку
    # необязательной, чтобы старый бот продолжал работать до деплоя лендинга.
    if settings.WEB_APP_URL:
        keyboard.append([
            KeyboardButton(
                text=texts.BTN_EVENT_PAGE,
                web_app=WebAppInfo(url=settings.WEB_APP_URL),
            )
        ])
    keyboard.extend([
        [KeyboardButton(text=texts.BTN_MY_TICKETS)],
        [KeyboardButton(text=texts.BTN_ASK)],
    ])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        is_persistent=True,
    )


def faq_menu() -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text=q)] for q, _ in texts.FAQ_ITEMS]
    keyboard.append([KeyboardButton(text=texts.BTN_ASK_OWN)])
    keyboard.append([KeyboardButton(text=texts.BTN_BACK)])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        is_persistent=True,
    )


def review_pending_menu() -> ReplyKeyboardRemove:
    """Скрывает действия, которые бесполезны, пока заявку проверяют."""
    return ReplyKeyboardRemove(remove_keyboard=True)


def ticket_types_menu(ticket_types: list[dict]) -> ReplyKeyboardMarkup:
    """Выбор типа билета. Сейчас тип один, но клавиатура универсальна."""
    keyboard = [[KeyboardButton(text=t["name"])] for t in ticket_types]
    keyboard.append([KeyboardButton(text=texts.BTN_CANCEL_FLOW)])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        is_persistent=True,
    )


def cancel_flow_menu() -> ReplyKeyboardMarkup:
    """Клавиатура с одной кнопкой отмены во время шагов ввода."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=texts.BTN_CANCEL_FLOW)]],
        resize_keyboard=True,
        is_persistent=True,
    )
