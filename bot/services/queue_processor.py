import asyncio
import json
import logging

from aiogram import Bot

import db
from config import settings
from services.utko_client import UTKOClient

logger = logging.getLogger(__name__)


async def run_queue_processor(bot: Bot, utko_client: UTKOClient) -> None:
    logger.info("Queue processor started (interval=%ds)", settings.queue_interval_seconds)

    while True:
        await asyncio.sleep(settings.queue_interval_seconds)
        try:
            await _process_batch(bot, utko_client)
        except Exception:
            logger.exception("Queue processor error")


async def _process_batch(bot: Bot, utko_client: UTKOClient) -> None:
    records = await db.get_pending_records(limit=50)
    if not records:
        return

    logger.info("Processing %d queued records", len(records))

    # Группируем по объекту
    by_object: dict[int, list[dict]] = {}
    for rec in records:
        by_object.setdefault(rec["object_db_id"], []).append(rec)

    for object_db_id, group in by_object.items():
        first = group[0]
        object_id = first["object_id"]
        access_key = first["access_key"]
        user_id = first["user_id"]

        payloads = [json.loads(r["payload"]) for r in group]
        success, message = await utko_client.send_records(
            object_id, access_key, payloads
        )

        new_status = "sent" if success else "error"
        for rec in group:
            await db.mark_record(rec["id"], new_status, None if success else message)

        if success:
            try:
                obj = await db.get_object(object_db_id)
                name = obj["name"] if obj else f"#{object_db_id}"
                await bot.send_message(
                    user_id,
                    f"✅ Отправлено {len(group)} записей для «{name}» в ФГИС УТКО.",
                )
            except Exception:
                logger.warning("Failed to notify user %d", user_id)
        else:
            failed = [r for r in group if r["attempts"] + 1 >= settings.max_retries]
            if failed:
                try:
                    obj = await db.get_object(object_db_id)
                    name = obj["name"] if obj else f"#{object_db_id}"
                    await bot.send_message(
                        user_id,
                        f"❌ Не удалось отправить {len(failed)} записей для «{name}».\n"
                        f"Ошибка: {message}",
                    )
                except Exception:
                    logger.warning("Failed to notify user %d", user_id)
