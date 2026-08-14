-- db/schema.sql
CREATE TABLE IF NOT EXISTS events (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    date            TEXT NOT NULL,
    location        TEXT NOT NULL,
    description     TEXT,
    last_ticket_no  INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS ticket_types (
    id          SERIAL PRIMARY KEY,
    event_id    INT NOT NULL REFERENCES events(id),
    name        TEXT NOT NULL,
    price       NUMERIC(10, 2)  -- не используется для расчетов (сумма из .env)
);

CREATE TABLE IF NOT EXISTS orders (
    id                   SERIAL PRIMARY KEY,
    telegram_id          BIGINT NOT NULL,
    username             TEXT,
    buyer_name           TEXT NOT NULL,
    buyer_phone          TEXT NOT NULL,
    ticket_type_id       INT NOT NULL REFERENCES ticket_types(id),
    quantity             INT NOT NULL,
    total_amount         NUMERIC(10, 2) NOT NULL,
    status               TEXT NOT NULL DEFAULT 'new'
                         CHECK (status IN ('new', 'confirmed', 'rejected', 'cancelled', 'expired')),
    screenshot_file_id   TEXT,
    reject_reason        TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    review_chat_id       BIGINT,
    review_message_id    BIGINT,
    review_base_text     TEXT,
    review_is_caption    BOOLEAN
);

CREATE TABLE IF NOT EXISTS tickets (
    id              SERIAL PRIMARY KEY,
    order_id        INT NOT NULL REFERENCES orders(id),
    ticket_type_id  INT NOT NULL REFERENCES ticket_types(id),
    ticket_number   INT NOT NULL,
    pdf_file_id     TEXT
);

CREATE TABLE IF NOT EXISTS users (
    telegram_id BIGINT PRIMARY KEY,
    role        TEXT NOT NULL CHECK (role IN ('admin', 'observer'))
);

CREATE TABLE IF NOT EXISTS broadcasts (
    id                SERIAL PRIMARY KEY,
    text              TEXT NOT NULL,
    sent_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    recipients_count  INT NOT NULL DEFAULT 0,
    delivered_count   INT NOT NULL DEFAULT 0
);

-- Событие (одна строка). Заменить данными реального мероприятия.
INSERT INTO events (name, date, location, description, last_ticket_no)
SELECT 'Название мероприятия', '31 декабря 2025, 19:00', 'Москва, ул. Примерная, 1',
       'Описание мероприятия', 0
WHERE NOT EXISTS (SELECT 1 FROM events);

-- Тип билета (цена в БД не используется — берется из .env TICKET_PRICE).
INSERT INTO ticket_types (event_id, name, price)
SELECT 1, 'Танцпол', 0
WHERE NOT EXISTS (SELECT 1 FROM ticket_types);

-- Обновляет единственный прежний тип при повторном применении схемы.
UPDATE ticket_types
SET name = 'Танцпол'
WHERE name = 'Обычный билет';

-- Админ. ЗАМЕНИТЬ 111111111 на реальный telegram_id администратора.
INSERT INTO users (telegram_id, role)
VALUES (1030144895, 'admin')
ON CONFLICT (telegram_id) DO NOTHING;
