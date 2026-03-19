# SCROOGE — Telegram-бот + REST API для передачи данных весового контроля в ФГИС УТКО

## Суть продукта
Telegram-бот для операторов объектов обращения с ТКО (полигоны, сортировки, перегрузочные станции).
Проблема: объекты без стабильного интернета обязаны с 01.01.2026 передавать данные в ФГИС УТКО.
Загружаете файл → бот парсит, валидирует и сразу отправляет в ФГИС УТКО API.

## Стек
- **Python 3.13** — основной язык
- **FastAPI** — HTTP-сервер, REST API, Swagger (`/docs`)
- **aiogram 3.x** — Telegram-бот (polling или webhook через FastAPI)
- **SQLite + aiosqlite** — БД (WAL mode)
- **openpyxl** — парсинг Excel (.xlsx)
- **httpx** — HTTP-клиент для ФГИС УТКО API
- **pydantic / pydantic-settings** — валидация, конфигурация
- **uvicorn** — ASGI-сервер (БЕЗ reload — ломает aiogram роутеры)
- **Docker** — деплой

## Версия
Текущая: **1.3.0** — хранится в `bot/version.py` (единый источник правды).
Выводится в ответ на кнопку «Все команды».

## Репозиторий
https://github.com/artemsitnikoff/scrooge.git

## Структура проекта
```
SCROOGE/
├── CLAUDE.md
├── DEPLOY.md                     # Инструкция деплоя на прод
├── docker-compose.yml            # Docker Compose (сервис bot)
├── .gitignore
├── scrooge-landing.html          # Лендинг
├── bot/
│   ├── main.py                   # Точка входа: FastAPI app + aiogram (lifespan)
│   ├── version.py                # __version__ — единый источник версии
│   ├── config.py                 # Settings из .env (prefix SCROOGE_)
│   ├── bot_factory.py            # create_bot(), create_dispatcher() — фабрика из ArkadyJarvis
│   ├── middlewares.py            # ErrorMiddleware — глобальный перехват ошибок
│   ├── db.py                     # SQLite: init, CRUD (connect-per-call)
│   ├── models.py                 # Pydantic: WeighingRecord (валидация)
│   ├── keyboards.py              # Inline-кнопки Telegram
│   ├── Dockerfile                # Python 3.13-slim
│   ├── .dockerignore
│   ├── .env                      # Конфигурация (НЕ коммитить!)
│   ├── .env.example              # Шаблон переменных окружения
│   ├── requirements.txt          # Зависимости Python
│   ├── handlers/                 # Telegram-хэндлеры (aiogram)
│   │   ├── __init__.py           # setup_routers()
│   │   ├── start.py              # /start, /help, главное меню, «Все команды»
│   │   ├── settings.py           # Общие настройки: ключ доступа (set/delete)
│   │   ├── add_object.py         # Управление объектами: CRUD, FSM добавление/переименование
│   │   ├── upload.py             # FSM: загрузка файла + прямая отправка в УТКО
│   │   └── subscription.py       # Подписки: статус, тарифы, оферта, оплата (ЮKassa)
│   ├── api/                      # REST API (FastAPI) — Bearer token auth
│   │   ├── __init__.py           # Сборка роутеров + Bearer token middleware
│   │   ├── schemas.py            # Pydantic-схемы запросов/ответов
│   │   ├── objects.py            # CRUD объектов: /api/objects
│   │   ├── upload.py             # Загрузка файлов: /api/upload/{id}
│   │   └── status.py             # Статус: /api/status
│   ├── services/
│   │   ├── utko_client.py        # POST в ФГИС УТКО (multipart/form-data) + логирование
│   │   ├── file_parser.py        # Парсинг .xlsx/.json → WeighingRecord[]
│   │   ├── queue_processor.py    # (legacy) Обработка очереди
│   │   └── subscription_checker.py # Фоновая проверка истекающих подписок (уведомления)
│   └── data/
│       ├── example.xlsx          # Пример файла (отправляется при ошибках парсинга)
│       ├── utko_requests.log     # Полные логи запросов/ответов к ФГИС УТКО
│       └── scrooge.db            # SQLite БД (создаётся автоматически)
```

## База данных (SQLite)
Три основные таблицы:
- **users** — пользователи (telegram_id PK, access_key UUID, created_at). Ключ доступа ГЛОБАЛЬНЫЙ на пользователя.
- **objects** — объекты ТКО (id, user_id, name, object_id UUID, created_at). БЕЗ access_key — он в users.
- **subscriptions** — подписки (id, object_db_id FK, user_id, plan, activated_at, expires_at, payment_id, created_at).
- **queue** — (legacy, таблица есть но не используется в основном флоу).

Паттерн: connect-per-call (новое соединение на каждый запрос). Не использовать общий connection — ломает aiosqlite с потоками.

## Подписки и оплата (ЮKassa)

### Тарифы
- **Месяц** — 2 900 ₽ (30 дней, 1 объект)
- **Год** — 29 000 ₽ (365 дней, 1 объект, экономия 5 800 ₽)

### Флоу оплаты
1. 💳 Подписка → показ всех объектов с статусами подписок + описание тарифов
2. Выбор тарифа (месяц/год) для конкретного объекта
3. Показ оферты (ссылка на Яндекс.Диск) + кнопка «✅ Согласен, оплатить»
4. Telegram Invoice через ЮKassa (provider_token)
5. Pre-checkout → автоподтверждение
6. Successful payment → активация подписки в БД
7. Если подписка активна — продление от конца текущей

### ЮKassa / Фискализация
- provider_data с receipt для чеков (54-ФЗ)
- tax_system_code: **2** (УСН доход)
- vat_code: 1
- payment_subject: "service", payment_mode: "full_payment"
- need_email: true, send_email_to_provider: true

### Оферта
URL: https://disk.yandex.ru/i/1gkKz_w5NkmmLA

### Проверка подписки
- Перед отправкой в УТКО проверяется `is_subscription_active(object_db_id)`
- Если подписка неактивна — предлагаются тарифы вместо отправки
- Фоновая задача `subscription_checker.py` ежедневно проверяет истекающие подписки (3 дня) и отправляет уведомления

## ФГИС УТКО API
- **Прод:** `https://api.utko.mnr.gov.ru/reo-weight-control-api/api/v1`
- **Тест:** `https://utko-uat-api.reo.ru/reo-weight-control-api/api/v1`
- **Endpoint:** `POST .../weight-controls/import`
- Content-Type: multipart/form-data, параметр `file` = JSON UTF-8
- JSON: `{ objectId, accessKey, weightControls: [...] }`
- Коды: 200=OK, 403=неверный ключ, 422=ошибка валидации
- Дубли по `weightControl.id` ФГИС пропускает автоматически
- Отправка происходит СРАЗУ после подтверждения пользователем (без очереди)
- **Логирование:** Полные запросы и ответы пишутся в `data/utko_requests.log`
- Base URL настраивается через `SCROOGE_UTKO_BASE_URL` в .env

## REST API
- Все эндпоинты защищены **Bearer token** аутентификацией
- Токен задаётся через `SCROOGE_API_TOKEN` в .env
- Если токен не настроен — API возвращает 403

### Эндпоинты
- `POST   /api/objects/`          — создать объект
- `GET    /api/objects/?user_id=` — список объектов пользователя
- `GET    /api/objects/{id}`      — получить объект
- `DELETE /api/objects/{id}?user_id=` — удалить объект
- `POST   /api/upload/{object_id}` — загрузить файл (multipart)
- `GET    /api/status/?user_id=`  — статус

## Конфигурация (.env)
```
SCROOGE_BOT_TOKEN=...              # Токен Telegram-бота
SCROOGE_HOST=0.0.0.0               # Хост FastAPI
SCROOGE_PORT=8111                  # Порт FastAPI (8000 занят другим проектом!)
SCROOGE_UTKO_BASE_URL=https://api.utko.mnr.gov.ru/reo-weight-control-api/api/v1
SCROOGE_API_TOKEN=...              # Bearer token для REST API
SCROOGE_PROVIDER_TOKEN=...         # ЮKassa provider token для Telegram Payments
SCROOGE_YUKASSA_SHOP_ID=...        # ID магазина ЮKassa
SCROOGE_YUKASSA_SECRET_KEY=...     # Секретный ключ ЮKassa
SCROOGE_WEBHOOK_URL=               # Пусто = polling, URL = webhook
SCROOGE_WEBHOOK_PATH=/webhook/telegram
```

## Telegram-бот: меню и навигация

### Главное меню (5 кнопок)
1. ⚙️ Общие настройки — ключ доступа УТКО (глобальный)
2. 🏭 Управление объектами — список + добавление/удаление
3. 📤 Загрузить данные — FSM: выбор объекта → файл → подтверждение → прямая отправка
4. 💳 Подписка — статус подписок, тарифы, оплата
5. 📖 Все команды — справка + версия

### Управление объектами
- Список объектов (каждый — кнопка → карточка)
- ➕ Добавить — FSM: сначала UUID объекта, потом название (опционально /skip)
- 🗑 Удалить — выбор → подтверждение
- Карточка объекта: ✏️ Изменить название, 🗑 Удалить, ↩️ Объекты

### Общие настройки
- Показывает текущий ключ (маскированный: первые 8 + ... + последние 4) или «не установлен»
- Кнопка «Ввести ключ» (если нет) или «Удалить ключ» (если есть)
- Перед загрузкой данных и добавлением объекта проверяется наличие ключа

### Загрузка данных
- Проверка ключа доступа и активной подписки
- Авто-выбор если 1 объект
- Поддержка .xlsx, .xls, .json
- При ошибках парсинга отправляет example.xlsx как образец + кнопка Меню
- После подтверждения — прямая отправка в ФГИС УТКО (без очереди)
- Результат (успех/ошибка) показывается сразу

### Правила UX
- Все callbacks используют `message.answer()` (новое сообщение), НЕ `edit_text()` — чтобы избежать "message is not modified"
- Кнопка «↩️ Меню» — возврат в главное меню
- Кнопка «↩️ Отмена» — выход из FSM

## Архитектурные паттерны (из ArkadyJarvis)
- **bot_factory.py** — create_bot() и create_dispatcher(), не на уровне модуля
- **ErrorMiddleware** — глобальный перехват ошибок (на message и callback_query)
  - TelegramBadRequest "message is not modified" — игнорируется тихо
  - Все остальные — логируются + пользователю отправляется дружелюбное сообщение
- **Service injection** через dp[] (например dp["utko_client"])
- **version.py** — отдельный файл для версии
- **FastAPI lifespan** (не on_event) для startup/shutdown
- **uvicorn без reload** — reload ломает aiogram роутеры при повторном импорте

## Валидация
- Госномер: regex `^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$` — строгий, только 12 букв реальных номерных знаков РФ. Буква «П» НЕ входит в допустимые.
- Вес: число > 0
- UUID объекта и ключа: стандартный формат 8-4-4-4-12
- Excel: гибкий маппинг заголовков (русские + английские названия колонок)

## Запуск

### Первоначальная установка (локально)
```bash
cd bot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env  # заполнить SCROOGE_BOT_TOKEN
```

### Запуск локально
```bash
cd bot
.venv/bin/python main.py
```
**ВАЖНО:** Запускать ТОЛЬКО через `.venv/bin/python`, НЕ через системный `python3` — зависимости установлены в venv.

### Перезапуск (kill + start)
```bash
lsof -ti :8111 | xargs kill -9   # убить старый процесс
sleep 1
cd bot && .venv/bin/python main.py
```

### Деплой (Docker)
```bash
git clone https://github.com/artemsitnikoff/scrooge.git
cd scrooge
cp bot/.env.example bot/.env
nano bot/.env  # заполнить переменные
mkdir -p data
docker compose up -d --build
```

### Обновление на сервере
```bash
cd ~/scrooge && git pull && docker compose up -d --build
```

### Полезные команды
```bash
docker compose logs -f          # Логи в реальном времени
docker compose ps               # Статус контейнера
docker compose down             # Остановить (данные сохраняются)
docker compose exec bot bash    # Зайти в контейнер
```

- Swagger UI: http://localhost:8111/docs
- Telegram-бот: polling (по умолчанию) или webhook

## Правила разработки
- Всегда спрашивать перед принятием архитектурных решений
- Язык комментариев и сообщений бота: русский
- Не убивать чужие процессы на портах — выбрать другой порт
- Не использовать технический жаргон в сообщениях пользователю (не показывать UUID и т.п.)
- Версию апать при значимых изменениях
