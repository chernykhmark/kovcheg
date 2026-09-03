# texts.py

WELCOME = (
    "Привет друг 🫂 Этот бот поможет тебе купить билет на Новогодний Ковчег 2027!\n\n"
    "Пожалуйста следуй инструкциям 👍\n\n"
    "Билет - 1500 руб.\n"
    "Успей купить до 14 сентября.\n"
    "Потом будет дороже."
)

# Подписи пунктов клиентского меню (reply)
BTN_BUY = "🎫 Купить билет"
BTN_MY_TICKETS = "🎟 Мои билеты"
BTN_ASK = "❓ Задать вопрос"

# Подписи пунктов админ-меню (reply)
BTN_EXPORT = "📊 Экспорт в Excel"
BTN_BROADCAST = "📢 Рассылка"

ADMIN_MENU = "Админ-меню:"

# --- FAQ ---
FAQ_MENU = "Часто задаваемые вопросы. Выберите вопрос или задайте свой:"
BTN_ASK_OWN = "✍️ Задать свой вопрос"
BTN_BACK = "⬅️ Назад"
MAIN_MENU_BACK = "Главное меню"

# Список FAQ: (кнопка/вопрос, ответ)
FAQ_ITEMS = [
    ("Где будет проходить мероприятие?", "LovelyLoft - Москва, Большая Семёновская ул., 42, стр. 15."),
    ("Можно ли взять ребенка?", "Да, напишите нам через «Задать свой вопрос»."),
    ("Как оплатить билет?", "После оформления заказа бот пришлет реквизиты для оплаты."),
    ("Как получить билет?", "После подтверждения оплаты билет придет в PDF прямо в этот чат."),
    ("Можно ли вернуть билет?", "По вопросам возврата напишите нам через «Задать свой вопрос»."),
]

# --- Покупка (Этап 2) ---
BTN_CANCEL_FLOW = "❌ Отменить заказ"

# Правило одного активного заказа
ORDER_ON_REVIEW = "Ваша заявка на проверке. Дождитесь решения администратора."
ORDER_AWAITING_PAYMENT = (
    "Ваша заявка ожидает оплаты.\n"
    "Оплатите её по реквизитам из предыдущего сообщения и пришлите скриншот в этот чат."
)

# Шаги покупки
CHOOSE_TYPE = "Выберите тип билета:"
ENTER_QUANTITY = "Сколько билетов купить? Введите число (от 1 до 20):"
QUANTITY_INVALID = "Введите корректное число билетов (от 1 до 20)."
ENTER_NAME = "Введите Имя и Домашнюю группу:"
NAME_INVALID = "Имя не должно быть пустым. Введите имя:"
# Bug 1: сразу показываем пример формата (как при ошибке), без лишнего шага-описания.
ENTER_PHONE = "Введите номер телефона:"
PHONE_INVALID = "Неверный формат номера. Попробуйте еще раз:"

PURCHASE_CANCELLED = "Оформление заказа отменено."


def order_created(ticket_type_name: str, quantity: int,
                  total_amount: int, sbp_card: str, sbp_phone: str,
                  sbp_name: str, sbp_bank: str) -> str:
    """Одно сообщение: заказ + копируемые реквизиты СБП."""
    return (
        f"✅ Заявка оформлена.\n\n"
        f"Количество: {quantity}\n"
        f"Сумма к оплате: <b>{total_amount} ₽</b>\n\n"
        f"Переведите точную сумму <b>одним платежом</b>\n"
        f"💳 Оплата только по номеру карты\n\n"
        f"(нажмите на номер, чтобы скопировать):\n\n"
        #f"<code>{sbp_card}</code>\n\n"
        f"<code>{sbp_phone}</code>\n\n"
        f"{sbp_name}\n\n"
        f"{sbp_bank}\n\n"
        f"ПРИШЛИТЕ СКРИНШОТ ОПЛАТЫ В ЭТОТ ЧАТ\n"


    )

# --- Прием скрина / обработка заявки (Этап 3) ---
BTN_CONFIRM = "✅ Подтвердить"
BTN_REJECT = "❌ Отклонить"

SCREENSHOT_ALREADY = "Скрин уже принят, ожидайте проверки."
SCREENSHOT_NO_ORDER = "Сначала оформите заказ."
SCREENSHOT_ACCEPTED = (
    "Скрин получен и отправлен на проверку. "
    "Ожидайте решения администратора."
)

# Всплывашки админ-колбэков
CB_ALREADY_HANDLED = "Заявка уже обработана"
CB_CONFIRMED = "Подтверждено"
CB_REJECTED = "Ответьте на сообщение заявки причиной отклонения"

# Уведомления клиенту
CLIENT_CONFIRMED = (
    "✅ Ваша оплата подтверждена! Ваши билеты — в сообщениях ниже."
)
CLIENT_TICKETS_HEADER = "🎟 Ваши билеты ({count} шт.):"


def ticket_caption(event_name: str, ticket_number: str, buyer_name: str) -> str:
    return (
        f"{event_name}\n"
        f"Билет №{ticket_number}\n"
        f"Имя: {buyer_name}"
    )


def client_rejected(reason: str) -> str:
    return f"❌ Ваш заказ отклонен.\nПричина: {reason}"


def admin_new_order(order_id: int, buyer_name: str, buyer_phone: str,
                    username: str | None, ticket_type_name: str,
                    quantity: int, total_amount: int) -> str:
    uname = f"@{username}" if username else "—"
    return (
        f"🆕 <b>Новая заявка №{order_id}</b>\n\n"
        f"Имя: {buyer_name}\n"
        f"Телефон: {buyer_phone}\n"
        f"Username: {uname}\n\n"
        f"Тип билета: {ticket_type_name}\n"
        f"Количество: {quantity}\n"
        f"Сумма: <b>{total_amount} ₽</b>"
    )


def admin_confirmed(base_text: str, username: str | None, hhmm: str) -> str:
    uname = f"@{username}" if username else "администратором"
    return f"{base_text}\n\n✅ Подтверждено {uname} в {hhmm}"


def admin_rejected(base_text: str, reason: str) -> str:
    return f"{base_text}\n\n❌ Отклонено: {reason}"


# Bug 3: явная инструкция админу, что нужно ОТВЕТИТЬ (reply) на это сообщение текстом причины.
ADMIN_WAITING_REASON = (
    "⏳ Заявка отклонена. "
    "<b>Ответьте на ЭТО сообщение</b> текстом причины отклонения — "
    "он будет отправлен клиенту."
)
REPLY_NOT_TO_REVIEW = (
    "Чтобы указать причину, ответьте именно на сообщение отклоненной заявки."
)

# --- Мои билеты (Этап 5) ---
NO_TICKETS = "У вас пока нет билетов."

# --- Экспорт в Excel (Этап 6) ---
EXPORT_CAPTION = "Выгрузка оплаченных билетов."

# --- Рассылка (Этап 7) ---
BTN_BROADCAST_SEND = "📤 Отправить"
BTN_BROADCAST_CANCEL = "❌ Отмена"

BROADCAST_ENTER_TEXT = "Введите текст рассылки:"
BROADCAST_CANCELLED = "Рассылка отменена."
BROADCAST_STARTED = "📢 Рассылка запущена, дождитесь итога..."


def broadcast_preview(text: str) -> str:
    return (
        "Проверьте текст рассылки:\n\n"
        "————————\n"
        f"{text}\n"
        "————————\n\n"
        "Отправить всем клиентам?"
    )


def broadcast_result(recipients_count: int, delivered_count: int) -> str:
    return (
        "✅ Рассылка завершена.\n"
        f"Получателей: {recipients_count}\n"
        f"Доставлено: {delivered_count}"
    )

# --- FAQ / Задать свой вопрос (Этап 8) ---
ASK_ENTER_QUESTION = (
    "Напишите ваш вопрос одним сообщением — мы передадим его администратору."
)
ASK_SENT = "✅ Вопрос отправлен. Администратор свяжется с вами."


def admin_new_question(buyer_name: str, username: str,
                       telegram_id: int, question: str) -> str:
    return (
        "❓ <b>Новый вопрос от клиента</b>\n\n"
        f"Имя: {buyer_name}\n"
        f"Username: {username}\n"
        f"Telegram ID: {telegram_id}\n\n"
        f"Вопрос:\n{question}"
    )
