"""
Аудит-лог всех действий пользователей.
Пишет в data/audit.log в формате:
  2026-03-25 18:50:00 | AUTH | user=123 | email_otp_send | email=test@mail.ru | ok
"""

import logging
import os
from datetime import datetime

_LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "audit.log")


def _ensure_dir():
    os.makedirs(os.path.dirname(_LOG_PATH), exist_ok=True)


_logger = None


def _get_logger() -> logging.Logger:
    global _logger
    if _logger:
        return _logger
    _ensure_dir()
    _logger = logging.getLogger("audit")
    _logger.setLevel(logging.INFO)
    _logger.propagate = False
    handler = logging.FileHandler(_LOG_PATH, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(handler)
    return _logger


def log(category: str, user_id: int | str | None, action: str, **details):
    """Записать аудит-событие."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    parts = [now, category.upper(), f"user={user_id or '?'}"]
    parts.append(action)
    for k, v in details.items():
        parts.append(f"{k}={v}")
    line = " | ".join(parts)
    _get_logger().info(line)


# --- Удобные обёртки ---

def auth_event(user_id, action: str, **details):
    log("AUTH", user_id, action, **details)


def key_event(user_id, action: str, **details):
    log("KEY", user_id, action, **details)


def object_event(user_id, action: str, **details):
    log("OBJECT", user_id, action, **details)


def upload_event(user_id, action: str, **details):
    log("UPLOAD", user_id, action, **details)


def subscription_event(user_id, action: str, **details):
    log("SUB", user_id, action, **details)


def payment_event(user_id, action: str, **details):
    log("PAY", user_id, action, **details)
