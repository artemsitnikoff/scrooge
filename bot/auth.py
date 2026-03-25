import hashlib
import hmac
import time
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config import settings

_security = HTTPBearer(auto_error=False)

ACCESS_TOKEN_EXPIRE = timedelta(hours=24)
REFRESH_TOKEN_EXPIRE = timedelta(days=30)


def _get_secret() -> str:
    if not settings.jwt_secret:
        raise HTTPException(status_code=503, detail="JWT not configured")
    return settings.jwt_secret


def create_access_token(account_id: int, user_id: int) -> str:
    payload = {
        "sub": str(account_id),
        "uid": user_id,
        "exp": datetime.utcnow() + ACCESS_TOKEN_EXPIRE,
        "type": "access",
    }
    return jwt.encode(payload, _get_secret(), algorithm="HS256")


def create_refresh_token(account_id: int, user_id: int) -> str:
    payload = {
        "sub": str(account_id),
        "uid": user_id,
        "exp": datetime.utcnow() + REFRESH_TOKEN_EXPIRE,
        "type": "refresh",
    }
    return jwt.encode(payload, _get_secret(), algorithm="HS256")


def decode_token(token: str, expected_type: str = "access") -> dict:
    try:
        payload = jwt.decode(token, _get_secret(), algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Токен истёк")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Невалидный токен")

    if payload.get("type") != expected_type:
        raise HTTPException(status_code=401, detail="Неверный тип токена")
    return payload


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_security),
) -> dict:
    if not creds:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    payload = decode_token(creds.credentials, "access")
    return {"account_id": int(payload["sub"]), "user_id": payload["uid"]}


def verify_telegram_login(data: dict) -> bool:
    """Проверка данных Telegram Login Widget через HMAC-SHA256."""
    check_hash = data.pop("hash", None)
    if not check_hash:
        return False

    # Проверка auth_date (не старше 1 дня)
    auth_date = data.get("auth_date")
    if auth_date and (time.time() - int(auth_date)) > 86400:
        return False

    # Убираем пустые значения — Telegram их не передаёт,
    # а Pydantic заполняет дефолтами, что ломает HMAC
    filtered = {k: v for k, v in data.items() if v is not None and v != ""}

    # HMAC verification
    secret = hashlib.sha256(settings.bot_token.encode()).digest()
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(filtered.items()))
    h = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    return h == check_hash
