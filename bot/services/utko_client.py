import io
import json
import logging

import httpx

from config import settings

logger = logging.getLogger(__name__)


class UTKOClient:
    def __init__(self) -> None:
        self._endpoint = f"{settings.utko_base_url}/weight-controls/import"
        self._client = httpx.AsyncClient(timeout=30)

    async def send_records(
        self, object_id: str, access_key: str, records: list[dict]
    ) -> tuple[bool, str]:
        """Отправляет записи в ФГИС УТКО. Возвращает (success, message)."""
        payload = {
            "objectId": object_id,
            "accessKey": access_key,
            "weightControls": records,
        }
        file_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        try:
            resp = await self._client.post(
                self._endpoint,
                files={"file": ("data.json", io.BytesIO(file_bytes), "application/json")},
            )

            if resp.status_code == 200:
                return True, "OK"
            elif resp.status_code == 403:
                return False, "Неверный accessKey (403)"
            elif resp.status_code == 422:
                body = resp.text[:500]
                return False, f"Ошибка валидации (422): {body}"
            else:
                return False, f"HTTP {resp.status_code}: {resp.text[:500]}"

        except httpx.TimeoutException:
            return False, "Таймаут соединения с ФГИС УТКО"
        except httpx.ConnectError:
            return False, "Нет соединения с ФГИС УТКО"
        except Exception as e:
            logger.exception("Ошибка отправки в ФГИС УТКО")
            return False, str(e)

    async def close(self) -> None:
        await self._client.aclose()
