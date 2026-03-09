import asyncio
import logging
import sys
import os
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(__file__))

import uvicorn
from aiogram.types import Update
from fastapi import FastAPI

from config import settings
from version import __version__
from db import init_db
from bot_factory import create_bot, create_dispatcher
from services.utko_client import UTKOClient
from api import router as api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

bot = None
dp = None
utko_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot, dp, utko_client

    await init_db()

    bot = create_bot()
    dp = create_dispatcher()

    # Service injection — доступны в хэндлерах как параметры функций
    utko_client = UTKOClient()
    dp["utko_client"] = utko_client

    if settings.webhook_url:
        webhook = settings.webhook_url.rstrip("/") + settings.webhook_path
        await bot.set_webhook(webhook)
        logger.info("Webhook set: %s", webhook)
    else:
        asyncio.create_task(dp.start_polling(bot))
        logger.info("Polling started")

    logger.info("SCROOGE v%s started on port %d", __version__, settings.port)
    yield

    if settings.webhook_url:
        await bot.delete_webhook()
    await utko_client.close()
    await bot.session.close()


app = FastAPI(
    title="SCROOGE API",
    description="API для бота передачи данных весового контроля в ФГИС УТКО",
    version=__version__,
    lifespan=lifespan,
)
app.include_router(api_router, prefix="/api")


@app.post(settings.webhook_path)
async def telegram_webhook(update: dict) -> dict:
    telegram_update = Update(**update)
    await dp.feed_update(bot=bot, update=telegram_update)
    return {"ok": True}


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.host, port=settings.port)
