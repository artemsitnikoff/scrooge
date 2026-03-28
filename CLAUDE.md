# SCROOGE — Telegram-бот + REST API + Веб-ЛК для передачи данных весового контроля в ФГИС УТКО

## Суть продукта
Telegram-бот + веб-кабинет для операторов объектов обращения с ТКО (полигоны, сортировки, перегрузочные станции).
Проблема: объекты без стабильного интернета обязаны с 01.01.2026 передавать данные в ФГИС УТКО.
Загружаете файл → бот/ЛК парсит, валидирует и сразу отправляет в ФГИС УТКО API.

## Стек
- **Python 3.13** — основной язык
- **FastAPI** — HTTP-сервер, REST API, Swagger (`/docs`)
- **aiogram 3.x** — Telegram-бот (polling или webhook через FastAPI)
- **Vue 3 + TypeScript + Vite** — SPA веб-ЛК (`/dashboard/`)
- **SQLite + aiosqlite** — БД (WAL mode)
- **PyJWT** — JWT-авторизация для ЛК
- **openpyxl** — парсинг Excel (.xlsx)
- **httpx** — HTTP-клиент для ФГИС УТКО API и ЮKassa API
- **pydantic / pydantic-settings** — валидация, конфигурация
- **email-validator** — валидация email (Pydantic EmailStr)
- **uvicorn** — ASGI-сервер (БЕЗ reload — ломает aiogram роутеры)
- **Docker** — деплой (multi-stage: Node + Python)

## Версия
Текущая: **1.5.0** — хранится в `bot/version.py` (единый источник правды).
Выводится в боте (кнопка «Все команды») и в ЛК (sidebar, получает через `/api/v2/auth/config`).

## Репозиторий
https://github.com/artemsitnikoff/scrooge.git

## Домен
https://utko-bot.ru — лендинг (nginx static) + ЛК (/dashboard/) + API (/api/)

## Структура проекта
```
SCROOGE/
├── CLAUDE.md
├── DEPLOY.md                     # Инструкция деплоя на прод
├── docker-compose.yml            # Docker Compose (context: корень, dockerfile: bot/Dockerfile)
├── .gitignore
├── scrooge-landing.html          # Лендинг (копия)
├── frontend/                     # Vue.js SPA (Личный кабинет)
│   ├── package.json              # Зависимости фронта
│   ├── vite.config.ts            # Vite: proxy /api → :8111, base: /dashboard/
│   ├── tsconfig.json
│   ├── index.html
│   ├── src/
│   │   ├── main.ts               # Точка входа Vue
│   │   ├── App.vue               # Root component + toast notifications
│   │   ├── router/index.ts       # Vue Router: /login, /access-key, /objects, /upload, /subscription, /history
│   │   ├── stores/
│   │   │   ├── auth.ts           # Pinia: JWT tokens, user state, appVersion
│   │   │   └── notifications.ts  # Pinia: toast notifications
│   │   ├── api/
│   │   │   ├── client.ts         # Axios + JWT interceptor + auto-refresh
│   │   │   ├── auth.ts           # getAuthConfig, sendOtp, verifyOtp, telegramLogin
│   │   │   ├── accessKey.ts      # get/set/delete ключа доступа
│   │   │   ├── objects.ts        # CRUD объектов
│   │   │   ├── upload.ts         # Загрузка файла + подтверждение
│   │   │   ├── subscriptions.ts  # Подписки + создание платежа
│   │   │   └── history.ts        # История отправок
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.vue   # Навигация (navy sidebar)
│   │   │   │   └── AppLayout.vue # Sidebar + main content
│   │   │   └── auth/
│   │   │       ├── TelegramLogin.vue  # Telegram Login Widget
│   │   │       └── EmailLogin.vue     # Email + OTP форма
│   │   ├── views/
│   │   │   ├── LoginView.vue          # Страница входа
│   │   │   ├── AccessKeyView.vue      # Ключ доступа УТКО
│   │   │   ├── ObjectsView.vue        # Управление объектами
│   │   │   ├── UploadView.vue         # Загрузка данных + drag-n-drop
│   │   │   ├── SubscriptionView.vue   # Подписки + оплата
│   │   │   ├── HistoryView.vue        # История отправок + детали
│   │   │   └── PaymentResultView.vue  # Результат оплаты ЮKassa
│   │   └── assets/styles/main.css     # Дизайн-система из лендинга
│   └── dist/                     # Build output (не коммитится)
├── bot/
│   ├── main.py                   # Точка входа: FastAPI app + aiogram + static serving
│   ├── version.py                # __version__ — единый источник версии
│   ├── config.py                 # Settings из .env (prefix SCROOGE_)
│   ├── auth.py                   # JWT (PyJWT): создание/проверка токенов, Telegram Login Widget HMAC
│   ├── bot_factory.py            # create_bot(), create_dispatcher()
│   ├── middlewares.py            # ErrorMiddleware — глобальный перехват ошибок
│   ├── db.py                     # SQLite: init, CRUD (connect-per-call)
│   ├── models.py                 # Pydantic: WeighingRecord (валидация)
│   ├── keyboards.py              # Inline-кнопки Telegram
│   ├── Dockerfile                # Multi-stage: Node (frontend build) + Python 3.13-slim
│   ├── .env                      # Конфигурация (НЕ коммитить!)
│   ├── .env.example              # Шаблон переменных окружения
│   ├── requirements.txt          # Зависимости Python
│   ├── handlers/                 # Telegram-хэндлеры (aiogram)
│   │   ├── __init__.py           # setup_routers()
│   │   ├── start.py              # /start, /help, главное меню, «Все команды»
│   │   ├── settings.py           # Общие настройки: ключ доступа (set/delete)
│   │   ├── add_object.py         # Управление объектами: CRUD, FSM добавление/переименование
│   │   ├── upload.py             # FSM: загрузка файла + прямая отправка в УТКО + сохранение истории
│   │   ├── subscription.py       # Подписки: статус, тарифы, оферта, оплата (ЮKassa Telegram Invoice)
│   │   └── history.py            # История отправок: список + детали
│   ├── api/                      # REST API (FastAPI)
│   │   ├── __init__.py           # Сборка роутеров /api/ + Bearer token middleware
│   │   ├── schemas.py            # Pydantic-схемы запросов/ответов (v1)
│   │   ├── objects.py            # CRUD объектов: /api/objects (v1, Bearer)
│   │   ├── upload.py             # Загрузка файлов: /api/upload/{id} (v1, Bearer)
│   │   ├── status.py             # Статус: /api/status (v1, Bearer)
│   │   ├── dashboard.py          # Агрегатор роутеров /api/v2/ (ЛК)
│   │   ├── auth.py               # Auth endpoints: OTP, Telegram, refresh, config
│   │   ├── dash_access_key.py    # GET/PUT/DELETE /api/v2/access-key
│   │   ├── dash_objects.py       # CRUD /api/v2/objects
│   │   ├── dash_upload.py        # Upload + confirm /api/v2/upload/{id}
│   │   ├── dash_subscription.py  # Подписки + ЮKassa платежи /api/v2/subscriptions
│   │   ├── dash_history.py       # История отправок /api/v2/history
│   │   └── yukassa_webhook.py    # POST /api/yukassa/webhook
│   ├── services/
│   │   ├── utko_client.py        # POST в ФГИС УТКО (multipart/form-data) + логирование
│   │   ├── file_parser.py        # Парсинг .xlsx/.json → WeighingRecord[]
│   │   ├── yukassa_client.py     # HTTP API ЮKassa v3 (создание платежей)
│   │   ├── email_sender.py       # SMTP отправка OTP-кодов
│   │   ├── audit_log.py          # Аудит-лог действий пользователей → data/audit.log
│   │   ├── queue_processor.py    # (legacy) Обработка очереди
│   │   └── subscription_checker.py # Фоновая проверка истекающих подписок
│   └── data/
│       ├── example.xlsx          # Пример файла (скачивается через /api/v2/download/example)
│       ├── scrooge.db            # SQLite БД (создаётся автоматически)
│       ├── utko_requests.log     # Полные логи запросов/ответов к ФГИС УТКО
│       └── audit.log             # Аудит-лог действий пользователей ЛК
```

## База данных (SQLite)
Таблицы:
- **users** — пользователи (telegram_id PK, access_key UUID, created_at). Ключ доступа ГЛОБАЛЬНЫЙ на пользователя.
- **objects** — объекты ТКО (id, user_id, name, object_id UUID, created_at). БЕЗ access_key — он в users.
- **subscriptions** — подписки (id, object_db_id FK, user_id, plan, activated_at, expires_at, payment_id, created_at).
- **accounts** — аккаунты ЛК (id, telegram_id UNIQUE nullable, email UNIQUE nullable, created_at). Связь Telegram↔email.
- **otp_codes** — коды для email-входа (id, email, code, expires_at, used, created_at).
- **web_payments** — веб-платежи ЮKassa (id, yukassa_payment_id UNIQUE, user_id, object_db_id, plan, amount, status, created_at).
- **upload_history** — история отправок (id, user_id, object_db_id, object_name, filename, record_count, error_count, records_json, utko_success, utko_response, source [bot/web], created_at).
- **queue** — (legacy, таблица есть но не используется).

Паттерн: connect-per-call (новое соединение на каждый запрос). Не использовать общий connection — ломает aiosqlite с потоками.

Для email-пользователей ЛК (без Telegram) создаётся синтетический telegram_id >= 9_000_000_000 в таблице users, чтобы переиспользовать все существующие функции db.py.

## Веб-ЛК (Личный кабинет)

### Дизайн-система (из лендинга /Users/artemsitnikov/SCROOGE_LANDING/)
```css
--gold: #F5A623;  --gold-dark: #D4851A;  --gold-light: #FFF8EC;
--navy: #0E1E3D;  --navy2: #162B52;
--text: #111827;  --muted: #6B7280;  --bg: #F9F8F5;
--border: #E5E1D5; --tg: #2AABEE;
--red: #DC2626;   --green: #16A34A;
Шрифты: Montserrat (заголовки, кнопки), Golos Text (текст)
Стиль: скруглённые карточки (border-radius: 16px), золотые акценты, тёмный sidebar
```

### Авторизация
1. **Email + OTP** — ввод email → 6-значный код на почту (SMTP) → JWT. Первый вход = регистрация.
2. **Telegram Login Widget** — один клик, привязка к telegram_id, все данные из бота видны сразу.

JWT: PyJWT (HS256), access token 24ч, refresh token 30д. Фронт хранит в localStorage, Axios interceptor автоматически обновляет.

### Sidebar (6 пунктов)
1. 🔑 Ключ доступа
2. 🏭 Объекты
3. 📤 Загрузить данные
4. 💳 Подписка
5. 📋 История
6. Выйти

### Страницы
- **LoginView** — Email OTP + Telegram Widget
- **AccessKeyView** — просмотр маскированного ключа, установка, удаление
- **ObjectsView** — список объектов с статусом подписки, добавление (UUID+имя), переименование, удаление
- **UploadView** — выбор объекта → drag-n-drop файла → preview записей/ошибок → подтверждение → отправка в УТКО. Кнопка скачивания примера файла.
- **SubscriptionView** — объекты с подписками (дни, статус), тарифы (месяц/год), оплата через ЮKassa redirect
- **HistoryView** — таблица всех отправок (дата, объект, файл, записей, статус, источник бот/веб). Кнопка «Подробнее» → модалка с данными из файла (таблица) и ответом ФГИС УТКО (разворачиваемый блок)
- **PaymentResultView** — проверка статуса оплаты после redirect от ЮKassa

## Подписки и оплата (ЮKassa)

### Тарифы
- **Месяц** — 2 900 ₽ (30 дней, 1 объект)
- **Год** — 29 000 ₽ (365 дней, 1 объект, экономия 5 800 ₽)

### Оплата в Telegram-боте
1. 💳 Подписка → показ объектов + тарифы
2. Оферта → «✅ Согласен, оплатить»
3. Telegram Invoice через ЮKassa (SCROOGE_PROVIDER_TOKEN)
4. Pre-checkout → автоподтверждение
5. Successful payment → activate_subscription()

### Оплата в ЛК (веб)
1. Выбор тарифа → POST /api/v2/subscriptions/pay
2. Создание платежа через ЮKassa HTTP API v3 (SCROOGE_YUKASSA_SHOP_ID + SECRET_KEY)
3. Redirect на ЮKassa → оплата → redirect обратно на /dashboard/payment-result
4. Webhook POST /api/yukassa/webhook → activate_subscription()

### ЮKassa / Фискализация
- receipt с customer.email обязателен (54-ФЗ)
- tax_system_code: **2** (УСН доход)
- vat_code: 1
- payment_subject: "service", payment_mode: "full_payment"

### Оферта
URL: https://disk.yandex.ru/i/1gkKz_w5NkmmLA

## REST API v1 (/api/) — Bearer token
- Токен: `SCROOGE_API_TOKEN` в .env
- `POST   /api/objects/`          — создать объект
- `GET    /api/objects/?user_id=` — список объектов
- `GET    /api/objects/{id}`      — получить объект
- `DELETE /api/objects/{id}?user_id=` — удалить
- `POST   /api/upload/{object_id}` — загрузить файл
- `GET    /api/status/?user_id=`  — статус

## REST API v2 (/api/v2/) — JWT auth (ЛК)

### Auth (публичные)
- `GET  /api/v2/auth/config`           — bot_username, smtp_enabled, version
- `POST /api/v2/auth/email/send-otp`   — отправить OTP на email
- `POST /api/v2/auth/email/verify-otp` — проверить OTP → JWT
- `POST /api/v2/auth/telegram`         — Telegram Login Widget → JWT
- `POST /api/v2/auth/refresh`          — обновить access token

### Dashboard (JWT required)
- `GET/PUT/DELETE /api/v2/access-key`   — ключ доступа УТКО
- `GET/POST/PATCH/DELETE /api/v2/objects` — CRUD объектов
- `POST /api/v2/upload/{id}`            — загрузить файл → preview
- `POST /api/v2/upload/{id}/confirm`    — подтвердить → отправить в УТКО
- `GET  /api/v2/subscriptions`          — список подписок
- `POST /api/v2/subscriptions/pay`      — создать платёж ЮKassa
- `GET  /api/v2/subscriptions/payment-status/{id}` — статус платежа
- `GET  /api/v2/history`                — история отправок
- `GET  /api/v2/history/{id}`           — детали отправки (записи + ответ УТКО)
- `GET  /api/v2/download/example`       — скачать пример xlsx

### Webhook (без auth)
- `POST /api/yukassa/webhook`           — уведомление ЮKassa

## ФГИС УТКО API
- **Прод:** `https://api.utko.mnr.gov.ru/reo-weight-control-api/api/v1`
- **Тест:** `https://utko-uat-api.reo.ru/reo-weight-control-api/api/v1`
- **Endpoint:** `POST .../weight-controls/import`
- Content-Type: multipart/form-data, параметр `file` = JSON UTF-8
- JSON: `{ objectId, accessKey, weightControls: [...] }`
- Коды: 200=OK, 403=неверный ключ, 422=ошибка валидации
- Дубли по `weightControl.id` ФГИС пропускает автоматически
- Отправка СРАЗУ после подтверждения (без очереди)
- Логирование: `data/utko_requests.log`

## Конфигурация (.env)
```
SCROOGE_BOT_TOKEN=...              # Токен Telegram-бота
SCROOGE_HOST=0.0.0.0               # Хост FastAPI
SCROOGE_PORT=8111                  # Порт FastAPI (8000 занят!)
SCROOGE_UTKO_BASE_URL=https://api.utko.mnr.gov.ru/reo-weight-control-api/api/v1
SCROOGE_API_TOKEN=...              # Bearer token для REST API v1
SCROOGE_PROVIDER_TOKEN=...         # ЮKassa provider token для Telegram Payments
SCROOGE_YUKASSA_SHOP_ID=...        # ID магазина ЮKassa (для веб-оплаты)
SCROOGE_YUKASSA_SECRET_KEY=...     # Секретный ключ ЮKassa
SCROOGE_WEBHOOK_URL=               # Пусто = polling, URL = webhook
SCROOGE_WEBHOOK_PATH=/webhook/telegram
# Личный кабинет
SCROOGE_JWT_SECRET=...             # JWT секрет для авторизации ЛК
SCROOGE_WEB_BASE_URL=https://utko-bot.ru  # Для return_url ЮKassa
# SMTP для email OTP (если пусто — email-вход отключён)
SCROOGE_SMTP_HOST=smtp.yandex.ru
SCROOGE_SMTP_PORT=465
SCROOGE_SMTP_USER=...
SCROOGE_SMTP_PASSWORD=...          # Пароль приложения (не пароль почты!)
SCROOGE_SMTP_FROM=...
```
**ВАЖНО:** Все переменные с префиксом `SCROOGE_`. Для Яндекс SMTP нужен пароль приложения (2FA → https://id.yandex.ru/security/app-passwords).

## Telegram-бот: меню и навигация

### Главное меню (6 кнопок)
1. ⚙️ Общие настройки — ключ доступа УТКО (глобальный)
2. 🏭 Управление объектами — список + добавление/удаление
3. 📤 Загрузить данные — FSM: выбор объекта → файл → подтверждение → прямая отправка
4. 💳 Подписка — статус подписок, тарифы, оплата
5. 📋 История отправок — последние 10 отправок, детали + ответ УТКО
6. 📖 Все команды — справка + версия

### Правила UX
- Все callbacks используют `message.answer()` (новое сообщение), НЕ `edit_text()`
- Кнопка «↩️ Меню» — возврат в главное меню
- Кнопка «↩️ Отмена» — выход из FSM
- Бейдж «Подписка неактивна» — красный (badge-danger)

## Логирование
- **data/utko_requests.log** — полные запросы/ответы к ФГИС УТКО
- **data/audit.log** — аудит действий пользователей ЛК (AUTH, KEY, OBJECT, UPLOAD, SUB, PAY)
- **docker compose logs** — системные логи (aiogram, FastAPI, SMTP)

## Архитектурные паттерны
- **bot_factory.py** — create_bot() и create_dispatcher(), не на уровне модуля
- **ErrorMiddleware** — глобальный перехват ошибок
- **Service injection** через dp[] (dp["utko_client"])
- **version.py** — единый источник версии (бот + ЛК через API)
- **FastAPI lifespan** для startup/shutdown
- **uvicorn без reload** — ломает aiogram роутеры
- **Multi-stage Dockerfile** — Node (build frontend) + Python (app)
- **API v1/v2** — v1 Bearer token для внешних клиентов, v2 JWT для ЛК
- **accounts table** — мост между Telegram и email идентификацией

## Известные особенности / фиксы
- PyJWT: `sub` claim должен быть **string**, не int
- Telegram Login Widget: фильтровать пустые значения Pydantic перед HMAC
- ЮKassa: `customer.email` обязателен в receipt (54-ФЗ)
- Telegram Widget: нужно `/setdomain` через @BotFather
- `email-validator` нужен для Pydantic EmailStr
- `bot_username` получается из `bot.get_me()` при старте, не из token.split

## Валидация
- Госномер: regex `^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$` — строгий, 12 букв РФ. «П» НЕ входит.
- Вес: число > 0
- UUID объекта и ключа: стандартный формат 8-4-4-4-12
- Excel: гибкий маппинг заголовков (русские + английские)

## Запуск

### Локально (бэкенд)
```bash
cd bot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env  # заполнить
.venv/bin/python main.py
```

### Локально (фронт, отдельный терминал)
```bash
cd frontend
npm install
npm run dev    # http://localhost:5173/dashboard/ (proxy → :8111)
```

### Деплой (Docker)
```bash
git clone https://github.com/artemsitnikoff/scrooge.git
cd scrooge
cp bot/.env.example bot/.env
nano bot/.env  # заполнить
mkdir -p data
docker compose up -d --build
```

### Обновление на сервере
```bash
cd ~/scrooge && git pull && docker compose up -d --build
```

### Полезные команды
```bash
docker compose logs -f                          # Логи в реальном времени
docker compose logs --tail=50                   # Последние 50 строк
docker compose exec bot cat data/audit.log      # Аудит-лог действий
docker compose ps                               # Статус контейнера
docker compose down                             # Остановить
docker compose exec bot bash                    # Зайти в контейнер
```

### Nginx (прод, utko-bot.ru)
```nginx
location /dashboard/ {
    proxy_pass http://127.0.0.1:8111;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
location /api/ {
    proxy_pass http://127.0.0.1:8111;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    client_max_body_size 20M;
}
```

## Правила разработки
- Всегда спрашивать перед принятием архитектурных решений
- Язык комментариев и сообщений бота: русский
- Не убивать чужие процессы на портах — выбрать другой порт
- Не использовать технический жаргон в сообщениях пользователю (не показывать UUID и т.п.)
- Версию апать при значимых изменениях (единственный источник: bot/version.py)
- Бейдж «Подписка неактивна» — красный, не жёлтый
