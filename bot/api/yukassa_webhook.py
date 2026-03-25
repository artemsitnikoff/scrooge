import logging

from fastapi import APIRouter, Request

import db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["YuKassa Webhook"])


@router.post("/yukassa/webhook")
async def yukassa_webhook(request: Request):
    """Обработка уведомлений от ЮKassa о статусе платежа."""
    body = await request.json()
    event = body.get("event")
    obj = body.get("object", {})
    payment_id = obj.get("id")

    logger.info("ЮKassa webhook: event=%s, payment_id=%s", event, payment_id)

    if event == "payment.succeeded" and payment_id:
        wp = await db.get_web_payment_by_yukassa_id(payment_id)
        if not wp:
            logger.warning("ЮKassa webhook: платёж %s не найден в БД", payment_id)
            return {"ok": True}

        if wp["status"] == "succeeded":
            logger.info("ЮKassa webhook: платёж %s уже обработан", payment_id)
            return {"ok": True}

        # Активируем подписку
        await db.activate_subscription(
            object_db_id=wp["object_db_id"],
            user_id=wp["user_id"],
            plan=wp["plan"],
            payment_id=payment_id,
        )
        await db.update_web_payment_status(payment_id, "succeeded")
        logger.info(
            "ЮKassa webhook: подписка активирована, object=%s, plan=%s",
            wp["object_db_id"], wp["plan"],
        )

    elif event == "payment.canceled" and payment_id:
        await db.update_web_payment_status(payment_id, "canceled")
        logger.info("ЮKassa webhook: платёж %s отменён", payment_id)

    return {"ok": True}
