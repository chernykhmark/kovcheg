# db/queries.py
from db.pool import get_pool


async def get_event() -> dict | None:
    pool = get_pool()
    row = await pool.fetchrow(
        "SELECT id, name, date, location, description, last_ticket_no FROM events LIMIT 1"
    )
    return dict(row) if row else None


async def get_ticket_types(event_id: int) -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        "SELECT id, event_id, name, price FROM ticket_types WHERE event_id = $1 ORDER BY id",
        event_id,
    )
    return [dict(r) for r in rows]


async def get_ticket_type(ticket_type_id: int) -> dict | None:
    pool = get_pool()
    row = await pool.fetchrow(
        "SELECT id, event_id, name, price FROM ticket_types WHERE id = $1",
        ticket_type_id,
    )
    return dict(row) if row else None


async def get_active_order(telegram_id: int) -> dict | None:
    """Активный заказ клиента = status='new'. Возвращает и заказы со скрином, и без."""
    pool = get_pool()
    row = await pool.fetchrow(
        """
        SELECT id, telegram_id, username, buyer_name, buyer_phone,
               ticket_type_id, quantity, total_amount, status,
               screenshot_file_id, created_at
        FROM orders
        WHERE telegram_id = $1 AND status = 'new'
        ORDER BY id DESC
        LIMIT 1
        """,
        telegram_id,
    )
    return dict(row) if row else None


async def get_order(order_id: int) -> dict | None:
    pool = get_pool()
    row = await pool.fetchrow(
        """
        SELECT id, telegram_id, username, buyer_name, buyer_phone,
               ticket_type_id, quantity, total_amount, status,
               screenshot_file_id, reject_reason, created_at
        FROM orders
        WHERE id = $1
        """,
        order_id,
    )
    return dict(row) if row else None


async def cancel_order(order_id: int) -> None:
    pool = get_pool()
    await pool.execute(
        "UPDATE orders SET status = 'cancelled' WHERE id = $1 AND status = 'new'",
        order_id,
    )


async def create_order(
    telegram_id: int,
    username: str | None,
    buyer_name: str,
    buyer_phone: str,
    ticket_type_id: int,
    quantity: int,
    total_amount: int,
) -> int:
    pool = get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO orders (telegram_id, username, buyer_name, buyer_phone,
                            ticket_type_id, quantity, total_amount, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7, 'new')
        RETURNING id
        """,
        telegram_id, username, buyer_name, buyer_phone,
        ticket_type_id, quantity, total_amount,
    )
    return row["id"]


async def save_screenshot(order_id: int, file_id: str) -> bool:
    """
    Привязывает скрин к заказу. Серверная защита от повторного скрина:
    обновляет только если заказ 'new' и скрин еще не сохранен.
    Возвращает True, если скрин записан; False, если уже был (или заказ не 'new').
    """
    pool = get_pool()
    row = await pool.fetchrow(
        """
        UPDATE orders
        SET screenshot_file_id = $2
        WHERE id = $1 AND status = 'new' AND screenshot_file_id IS NULL
        RETURNING id
        """,
        order_id, file_id,
    )
    return row is not None


async def confirm_order(order_id: int) -> bool:
    """Атомарное подтверждение. True — успех, False — уже обработан."""
    pool = get_pool()
    row = await pool.fetchrow(
        "UPDATE orders SET status = 'confirmed' WHERE id = $1 AND status = 'new' RETURNING id",
        order_id,
    )
    return row is not None


async def reject_order(order_id: int) -> bool:
    """Атомарное отклонение. True — успех, False — уже обработан."""
    pool = get_pool()
    row = await pool.fetchrow(
        "UPDATE orders SET status = 'rejected' WHERE id = $1 AND status = 'new' RETURNING id",
        order_id,
    )
    return row is not None


async def set_reject_reason(order_id: int, reason: str) -> None:
    pool = get_pool()
    await pool.execute(
        "UPDATE orders SET reject_reason = $2 WHERE id = $1",
        order_id, reason,
    )


async def next_ticket_number(event_id: int) -> int:
    """Атомарная выдача порядкового номера билета (п.9)."""
    pool = get_pool()
    row = await pool.fetchrow(
        "UPDATE events SET last_ticket_no = last_ticket_no + 1 WHERE id = $1 RETURNING last_ticket_no",
        event_id,
    )
    return row["last_ticket_no"]


async def create_ticket(order_id: int, ticket_type_id: int, ticket_number: int) -> int:
    pool = get_pool()
    row = await pool.fetchrow(
        """
        INSERT INTO tickets (order_id, ticket_type_id, ticket_number)
        VALUES ($1, $2, $3)
        RETURNING id
        """,
        order_id, ticket_type_id, ticket_number,
    )
    return row["id"]


async def set_ticket_pdf(ticket_id: int, pdf_file_id: str) -> None:
    pool = get_pool()
    await pool.execute(
        "UPDATE tickets SET pdf_file_id = $2 WHERE id = $1",
        ticket_id, pdf_file_id,
    )


async def get_tickets_by_order(order_id: int) -> list[dict]:
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT id, order_id, ticket_type_id, ticket_number, pdf_file_id
        FROM tickets
        WHERE order_id = $1
        ORDER BY ticket_number
        """,
        order_id,
    )
    return [dict(r) for r in rows]


async def get_user_tickets(telegram_id: int) -> list[dict]:
    """
    Билеты клиента из подтвержденных заказов (Этап 5, п.14).
    Отдает поля для переотправки и fallback-перегенерации PDF.
    """
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT t.id AS ticket_id,
               t.pdf_file_id,
               t.ticket_number,
               o.buyer_name,
               o.buyer_phone,
               tt.name AS ticket_type_name
        FROM tickets t
        JOIN orders o ON o.id = t.order_id
        JOIN ticket_types tt ON tt.id = t.ticket_type_id
        WHERE o.telegram_id = $1 AND o.status = 'confirmed'
        ORDER BY t.ticket_number
        """,
        telegram_id,
    )
    return [dict(r) for r in rows]


async def get_export_rows() -> list[dict]:
    """
    Выборка для Excel-экспорта (Этап 6, п.10): одна строка = один билет
    из подтвержденных заказов.
    """
    pool = get_pool()
    rows = await pool.fetch(
        """
        SELECT o.buyer_name,
               o.buyer_phone,
               tt.name AS ticket_type_name,
               o.status,
               t.ticket_number
        FROM tickets t
        JOIN orders o ON o.id = t.order_id
        JOIN ticket_types tt ON tt.id = t.ticket_type_id
        WHERE o.status = 'confirmed'
        ORDER BY t.ticket_number
        """,
    )
    return [dict(r) for r in rows]


# db/queries.py  (добавить эти функции в конец файла)

async def get_broadcast_recipients() -> list[int]:
    """Уникальные telegram_id всех, кто хоть раз оформлял заказ (п.12)."""
    pool = get_pool()
    rows = await pool.fetch("SELECT DISTINCT telegram_id FROM orders")
    return [r["telegram_id"] for r in rows]


async def log_broadcast(text: str, recipients_count: int, delivered_count: int) -> None:
    """Лог рассылки (п.12, таблица broadcasts). sent_at = now() (UTC)."""
    pool = get_pool()
    await pool.execute(
        """
        INSERT INTO broadcasts (text, sent_at, recipients_count, delivered_count)
        VALUES ($1, now(), $2, $3)
        """,
        text, recipients_count, delivered_count,
    )


# db/queries.py  (добавить в конец файла)

async def get_admin_telegram_id() -> int | None:
    """Первый пользователь с ролью admin (п.13 — вопрос уходит админу в личку)."""
    pool = get_pool()
    return await pool.fetchval(
        "SELECT telegram_id FROM users WHERE role = 'admin' ORDER BY telegram_id LIMIT 1"
    )


# db/queries.py  (добавить в конец файла)

async def expire_old_orders() -> int:
    """
    Помечает expired неоплаченные заказы старше 1 месяца (п.11).
    Возвращает число затронутых строк.
    """
    pool = get_pool()
    result = await pool.execute(
        """
        UPDATE orders SET status = 'expired'
        WHERE status = 'new' AND created_at < now() - interval '1 month'
        """
    )
    # asyncpg возвращает строку вида "UPDATE 5" — берем число.
    return int(result.split()[-1])


# db/queries.py  (ДОБАВИТЬ эти функции в конец файла — Bug 3)

async def set_reject_review_message(
    order_id: int,
    chat_id: int,
    message_id: int,
    base_text: str,
    is_caption: bool,
) -> None:
    """
    Bug 3: сохраняем координаты сообщения заявки в админ-чате,
    чтобы потом по reply найти order_id и отредактировать нужное сообщение.
    """
    pool = get_pool()
    await pool.execute(
        """
        UPDATE orders
        SET review_chat_id = $2,
            review_message_id = $3,
            review_base_text = $4,
            review_is_caption = $5
        WHERE id = $1
        """,
        order_id, chat_id, message_id, base_text, is_caption,
    )


async def get_pending_reject_order_by_message(chat_id: int, message_id: int) -> dict | None:
    """
    Bug 3: находит отклонённый заказ, ожидающий причину, по координатам
    сообщения заявки (на которое ответили reply). Только status='rejected'
    и ещё без reject_reason.
    """
    pool = get_pool()
    row = await pool.fetchrow(
        """
        SELECT id, review_chat_id, review_message_id,
               review_base_text, review_is_caption
        FROM orders
        WHERE review_chat_id = $1
          AND review_message_id = $2
          AND status = 'rejected'
          AND reject_reason IS NULL
        LIMIT 1
        """,
        chat_id, message_id,
    )
    return dict(row) if row else None
