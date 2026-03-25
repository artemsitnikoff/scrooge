import asyncio
import logging
import sys
import os
from contextlib import asynccontextmanager

sys.path.insert(0, os.path.dirname(__file__))

import uvicorn
from aiogram.types import Update
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from config import settings
from version import __version__
from db import init_db
from bot_factory import create_bot, create_dispatcher
from services.utko_client import UTKOClient
from services.subscription_checker import run_subscription_checker
from api import router as api_router
from api.dashboard import router as dashboard_router
from api.yukassa_webhook import router as yukassa_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

bot = None
dp = None
utko_client = None
bot_username = ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot, dp, utko_client, bot_username

    await init_db()

    bot = create_bot()
    dp = create_dispatcher()

    # Получаем username бота для Telegram Login Widget
    bot_info = await bot.get_me()
    bot_username = bot_info.username or ""
    logger.info("Bot username: @%s", bot_username)

    # Service injection — доступны в хэндлерах как параметры функций
    utko_client = UTKOClient()
    dp["utko_client"] = utko_client

    asyncio.create_task(run_subscription_checker(bot))

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
app.include_router(dashboard_router, prefix="/api/v2")
app.include_router(yukassa_router, prefix="/api")


@app.post(settings.webhook_path)
async def telegram_webhook(update: dict) -> dict:
    telegram_update = Update(**update)
    await dp.feed_update(bot=bot, update=telegram_update)
    return {"ok": True}


# --- Личный кабинет (SPA) ---
_dashboard_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "dashboard")

if os.path.isdir(_dashboard_dir):
    _assets_dir = os.path.join(_dashboard_dir, "assets")
    if os.path.isdir(_assets_dir):
        app.mount("/dashboard/assets", StaticFiles(directory=_assets_dir), name="dashboard-assets")

    @app.get("/dashboard/{rest_of_path:path}")
    async def serve_dashboard(rest_of_path: str):
        return FileResponse(os.path.join(_dashboard_dir, "index.html"))

    @app.get("/dashboard")
    async def serve_dashboard_root():
        return FileResponse(os.path.join(_dashboard_dir, "index.html"))


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.host, port=settings.port)
