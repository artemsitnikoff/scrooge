import asyncio
import logging

from aiogram import Bot

import db
import keyboards

logger = logging.getLogger(__name__)

# Проверка раз в день (86400 секунд)
_CHECK_INTERVAL = 86400


async def run_subscription_checker(bot: Bot) -> None:
    logger.info("Subscription checker started")

    while True:
        await asyncio.sleep(_CHECK_INTERVAL)
        try:
            await _check_expiring(bot)
        except Exception:
            logger.exception("Subscription checker error")


async def _check_expiring(bot: Bot) -> None:
    expiring = await db.get_expiring_subscriptions(days=3)
    if not expiring:
        return

    logger.info("Found %d expiring subscriptions", len(expiring))

    for sub in expiring:
        exp_date = sub["expires_at"][:10]
        try:
            await bot.send_message(
                sub["user_id"],
                f"⚠️ Подписка на объект «{sub['object_name']}» "
                f"истекает {exp_date}.\n\n"
                "Продлите, чтобы продолжить передачу данных в ФГИС УТКО.",
                reply_markup=keyboards.subscription_renew(sub["obj_pk"]),
            )
        except Exception:
            logger.warning("Failed to notify user %d about expiring subscription", sub["user_id"])
