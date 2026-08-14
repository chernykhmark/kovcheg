# New Year Rave landing

Отдельный React-лендинг для продажи билетов через Telegram-бота. Сам бот и этот фронтенд независимы: собранные файлы можно раздавать с того же сервера через Nginx.

## Запуск

```bash
cd landing
npm install
npm run dev
```

Для production-сборки:

```bash
npm run build
```

Результат появится в `landing/dist`. Для локальной проверки собранной версии: `npm run preview`.

## Что менять

- `src/config.js` — адрес Telegram-бота, дата, площадка и соцсети.
- `src/data.js` — анонимный line-up и программа.
- `src/i18n.js` — все интерфейсные тексты на русском и английском.

## Деплой на Vercel

1. Импортируйте репозиторий в Vercel.
2. В поле **Root Directory** укажите `landing`.
3. Framework preset: **Vite**. Команда сборки — `npm run build`, папка публикации — `dist`.
4. Перед публикацией измените `telegramBotUrl` в `src/config.js` на настоящий адрес бота.

Для одного сервера загрузите содержимое `dist` в каталог сайта, а Telegram-бот продолжит работать как отдельный процесс.

## Открытие как Telegram Mini App

После публикации укажите HTTPS-адрес лендинга в корневом `.env` бота:

```env
WEB_APP_URL=https://example.com
```

После перезапуска бота в его главном меню появится кнопка «✨ Открыть афишу». Telegram требует для Mini App публичный HTTPS-адрес.
