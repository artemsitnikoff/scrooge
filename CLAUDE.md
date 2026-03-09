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
Текущая: **1.0.0** — хранится в `bot/version.py` (единый источник правды).
Выводится в ответ на кнопку «Все команды».

## Репозиторий
https://github.com/artemsitnikoff/scrooge.git

## Структура проекта
```
SCROOGE/
├── CLAUDE.md
├── docker-compose.yml            # Docker Compose (сервис bot)
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
│   │   └── upload.py             # FSM: загрузка файла + прямая отправка в УТКО
│   ├── api/                      # REST API (FastAPI)
│   │   ├── __init__.py           # Сборка роутеров
│   │   ├── schemas.py            # Pydantic-схемы запросов/ответов
│   │   ├── objects.py            # CRUD объектов: /api/objects
│   │   ├── upload.py             # Загрузка файлов: /api/upload/{id}
│   │   └── status.py             # Статус: /api/status
│   ├── services/
│   │   ├── utko_client.py        # POST в ФГИС УТКО (multipart/form-data)
│   │   └── file_parser.py        # Парсинг .xlsx/.json → WeighingRecord[]
│   └── data/
│       ├── example.xlsx          # Пример файла (отправляется при ошибках парсинга)
│       └── scrooge.db            # SQLite БД (создаётся автоматически)
```

## База данных (SQLite)
Две таблицы:
- **users** — пользователи (telegram_id PK, access_key UUID, created_at). Ключ доступа ГЛОБАЛЬНЫЙ на пользователя.
- **objects** — объекты ТКО (id, user_id, name, object_id UUID, created_at). БЕЗ access_key — он в users.

Паттерн: connect-per-call (новое соединение на каждый запрос). Не использовать общий connection — ломает aiosqlite с потоками.

## ФГИС УТКО API
- **POST** `https://api.utko.mnr.gov.ru/reo-weight-control-api/api/v1/weight-controls/import`
- Content-Type: multipart/form-data, параметр `file` = JSON UTF-8
- JSON: `{ objectId, accessKey, weightControls: [...] }`
- Коды: 200=OK, 403=неверный ключ, 422=ошибка валидации
- Дубли по `weightControl.id` ФГИС пропускает автоматически
- Отправка происходит СРАЗУ после подтверждения пользователем (без очереди)

## Конфигурация (.env)
```
SCROOGE_BOT_TOKEN=...         # Токен Telegram-бота
SCROOGE_HOST=0.0.0.0          # Хост FastAPI
SCROOGE_PORT=8111             # Порт FastAPI (8000 занят другим проектом!)
SCROOGE_WEBHOOK_URL=          # Пусто = polling, URL = webhook
```

## Telegram-бот: меню и навигация

### Главное меню (4 кнопки)
1. ⚙️ Общие настройки — ключ доступа УТКО (глобальный)
2. 🏭 Управление объектами — список + добавление/удаление
3. 📤 Загрузить данные — FSM: выбор объекта → файл → подтверждение → прямая отправка
4. 📖 Все команды — справка + версия

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
- Проверка ключа доступа
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
nano bot/.env  # заполнить SCROOGE_BOT_TOKEN
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

## REST API эндпоинты
- `POST   /api/objects/`          — создать объект
- `GET    /api/objects/?user_id=` — список объектов пользователя
- `GET    /api/objects/{id}`      — получить объект
- `DELETE /api/objects/{id}?user_id=` — удалить объект
- `POST   /api/upload/{object_id}` — загрузить файл (multipart)
- `GET    /api/status/?user_id=`  — статус

## Правила разработки
- Всегда спрашивать перед принятием архитектурных решений
- Язык комментариев и сообщений бота: русский
- Не убивать чужие процессы на портах — выбрать другой порт
- Не использовать технический жаргон в сообщениях пользователю (не показывать UUID и т.п.)
- Версию апать при значимых изменениях
