import random
import string
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

import db
from auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_telegram_login,
)
from config import settings
from services.email_sender import is_smtp_configured, send_otp_email

router = APIRouter(prefix="/auth", tags=["Auth"])


# --- Схемы ---

class EmailSendOtpRequest(BaseModel):
    email: EmailStr


class EmailVerifyOtpRequest(BaseModel):
    email: EmailStr
    code: str


class TelegramLoginRequest(BaseModel):
    id: int
    first_name: str = ""
    last_name: str = ""
    username: str = ""
    photo_url: str = ""
    auth_date: int
    hash: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user_id: int
    account_id: int


class ConfigResponse(BaseModel):
    bot_username: str
    smtp_enabled: bool


# --- Endpoints ---

@router.get("/config", response_model=ConfigResponse)
async def get_auth_config():
    import main
    return ConfigResponse(
        bot_username=main.bot_username,
        smtp_enabled=is_smtp_configured(),
    )


@router.post("/email/send-otp")
async def send_otp(req: EmailSendOtpRequest):
    if not is_smtp_configured():
        raise HTTPException(status_code=503, detail="Email-вход не настроен")

    code = "".join(random.choices(string.digits, k=6))
    expires_at = (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    await db.create_otp(req.email, code, expires_at)

    sent = send_otp_email(req.email, code)
    if not sent:
        raise HTTPException(status_code=500, detail="Не удалось отправить код")

    return {"ok": True, "message": "Код отправлен на почту"}


@router.post("/email/verify-otp", response_model=TokenResponse)
async def verify_otp(req: EmailVerifyOtpRequest):
    valid = await db.verify_otp(req.email, req.code)
    if not valid:
        raise HTTPException(status_code=400, detail="Неверный или просроченный код")

    account = await db.get_or_create_account_by_email(req.email)
    user_id = account["telegram_id"]

    return TokenResponse(
        access_token=create_access_token(account["id"], user_id),
        refresh_token=create_refresh_token(account["id"], user_id),
        user_id=user_id,
        account_id=account["id"],
    )


@router.post("/telegram", response_model=TokenResponse)
async def telegram_login(req: TelegramLoginRequest):
    data = req.model_dump()
    telegram_id = data["id"]

    if not verify_telegram_login(data):
        raise HTTPException(status_code=400, detail="Невалидные данные Telegram")

    account = await db.get_or_create_account_by_telegram(telegram_id)
    user_id = account["telegram_id"]

    return TokenResponse(
        access_token=create_access_token(account["id"], user_id),
        refresh_token=create_refresh_token(account["id"], user_id),
        user_id=user_id,
        account_id=account["id"],
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(req: RefreshRequest):
    payload = decode_token(req.refresh_token, "refresh")
    account_id = payload["sub"]
    user_id = payload["uid"]

    account = await db.get_account(account_id)
    if not account:
        raise HTTPException(status_code=401, detail="Аккаунт не найден")

    return TokenResponse(
        access_token=create_access_token(account_id, user_id),
        refresh_token=create_refresh_token(account_id, user_id),
        user_id=user_id,
        account_id=account_id,
    )
