import io
import json
import logging
import os
from datetime import datetime

import httpx

from config import settings

logger = logging.getLogger(__name__)

_LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
_LOG_FILE = os.path.join(_LOG_DIR, "utko_requests.log")


def _log_to_file(direction: str, data: str) -> None:
    """Пишем запросы и ответы УТКО в файл."""
    os.makedirs(_LOG_DIR, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with open(_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n{'='*80}\n")
        f.write(f"[{ts}] {direction}\n")
        f.write(f"{'='*80}\n")
        f.write(data)
        f.write("\n")


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

        # Логируем запрос
        _log_to_file("REQUEST", (
            f"URL: {self._endpoint}\n"
            f"Method: POST (multipart/form-data)\n"
            f"Object ID: {object_id}\n"
            f"Access Key: {access_key[:8]}...{access_key[-4:] if len(access_key) > 12 else ''}\n"
            f"Records: {len(records)}\n"
            f"Payload:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
        ))

        try:
            resp = await self._client.post(
                self._endpoint,
                files={"file": ("data.json", io.BytesIO(file_bytes), "application/json")},
            )

            # Логируем ответ
            _log_to_file("RESPONSE", (
                f"Status: {resp.status_code}\n"
                f"Headers: {dict(resp.headers)}\n"
                f"Body:\n{resp.text}"
            ))

            if resp.status_code == 200:
                logger.info("UTKO OK: %d records sent for object %s", len(records), object_id)
                return True, "OK"
            elif resp.status_code == 403:
                logger.warning("UTKO 403: invalid access key for object %s", object_id)
                return False, "Неверный accessKey (403)"
            elif resp.status_code == 422:
                body = resp.text[:500]
                logger.warning("UTKO 422: validation error: %s", body)
                return False, f"Ошибка валидации (422): {body}"
            else:
                logger.error("UTKO %d: %s", resp.status_code, resp.text[:500])
                return False, f"HTTP {resp.status_code}: {resp.text[:500]}"

        except httpx.TimeoutException:
            _log_to_file("ERROR", "Таймаут соединения")
            return False, "Таймаут соединения с ФГИС УТКО"
        except httpx.ConnectError as e:
            _log_to_file("ERROR", f"Нет соединения: {e}")
            return False, "Нет соединения с ФГИС УТКО"
        except Exception as e:
            _log_to_file("ERROR", f"Exception: {e}")
            logger.exception("Ошибка отправки в ФГИС УТКО")
            return False, str(e)

    async def close(self) -> None:
        await self._client.aclose()
