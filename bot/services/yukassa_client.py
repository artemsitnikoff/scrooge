import logging
import uuid

import httpx

from config import settings

logger = logging.getLogger(__name__)

YUKASSA_API = "https://api.yookassa.ru/v3"


class YukassaClient:
    def __init__(self):
        self._client = httpx.AsyncClient(
            base_url=YUKASSA_API,
            auth=(settings.yukassa_shop_id, settings.yukassa_secret_key),
            timeout=30,
        )

    async def close(self):
        await self._client.aclose()

    async def create_payment(
        self,
        amount: int,
        description: str,
        user_id: int,
        object_db_id: int,
        plan: str,
        email: str | None = None,
    ) -> dict:
        """Создать платёж и вернуть {id, confirmation_url}."""
        return_url = settings.web_base_url.rstrip("/") + "/dashboard/payment-result"
        idempotency_key = uuid.uuid4().hex

        payload = {
            "amount": {
                "value": f"{amount}.00",
                "currency": "RUB",
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url,
            },
            "capture": True,
            "description": description,
            "metadata": {
                "user_id": str(user_id),
                "object_db_id": str(object_db_id),
                "plan": plan,
            },
            "receipt": {
                "items": [
                    {
                        "description": description[:128],
                        "quantity": "1.00",
                        "amount": {
                            "value": f"{amount}.00",
                            "currency": "RUB",
                        },
                        "vat_code": 1,
                        "payment_mode": "full_payment",
                        "payment_subject": "service",
                    }
                ],
                "tax_system_code": 2,
                "customer": {"email": email or "noreply@utko-bot.ru"},
            },
        }

        resp = await self._client.post(
            "/payments",
            json=payload,
            headers={"Idempotence-Key": idempotency_key},
        )

        if resp.status_code != 200:
            logger.error("ЮKassa create_payment error: %s %s", resp.status_code, resp.text)
            raise Exception(f"Ошибка создания платежа: {resp.status_code}")

        data = resp.json()
        return {
            "id": data["id"],
            "confirmation_url": data["confirmation"]["confirmation_url"],
        }

    async def get_payment(self, payment_id: str) -> dict:
        """Получить статус платежа."""
        resp = await self._client.get(f"/payments/{payment_id}")
        if resp.status_code != 200:
            logger.error("ЮKassa get_payment error: %s %s", resp.status_code, resp.text)
            raise Exception(f"Ошибка получения платежа: {resp.status_code}")
        return resp.json()
