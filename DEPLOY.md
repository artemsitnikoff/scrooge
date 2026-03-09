# Деплой SCROOGE

## Требования к серверу

- Docker + Docker Compose
- Git

## Первоначальная установка

### 1. Клонировать репозиторий

```bash
git clone https://github.com/artemsitnikoff/scrooge.git
cd scrooge
```

### 2. Настроить .env

```bash
cp bot/.env.example bot/.env
nano bot/.env
```

Заполнить обязательные переменные:
- `SCROOGE_BOT_TOKEN` — токен Telegram-бота от @BotFather
- `SCROOGE_PORT` — порт (по умолчанию 8111)

### 3. Создать папку для данных

```bash
mkdir -p data
```

### 4. Запустить

```bash
docker compose up -d --build
```

Проверить:
```bash
# Swagger UI
curl localhost:8111/docs

# Логи
docker compose logs -f
```

## Обновление (деплой новой версии)

```bash
cd ~/scrooge
git pull
docker compose up -d --build
```

Одной строкой:
```bash
cd ~/scrooge && git pull && docker compose up -d --build
```

### Проверка после обновления

```bash
# Swagger
curl -s localhost:8111/docs | head -3

# Логи
docker compose logs --tail=50

# Статус контейнера
docker compose ps
```

## Перенос данных с Mac на сервер

```bash
# На Mac — скопировать базу на сервер
scp bot/data/scrooge.db user@server:~/scrooge/data/
```

На сервере убедиться, что папка `data/` существует:
```bash
mkdir -p data
```

## Полезные команды

```bash
# Логи в реальном времени
docker compose logs -f

# Перезапуск без пересборки
docker compose restart

# Остановить (данные сохраняются)
docker compose down

# Пересобрать и запустить
docker compose up -d --build

# Зайти в контейнер
docker compose exec bot bash
```

## Бэкап базы данных

```bash
# Скопировать с сервера
scp user@server:~/scrooge/data/scrooge.db ./backup_$(date +%Y%m%d).db
```

## Структура data/

```
data/
  scrooge.db       # SQLite база (пользователи, объекты)
```

Файл персистентен через Docker volume (`./data:/app/data`). При `docker compose down` данные сохраняются.
