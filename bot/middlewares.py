import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import TelegramObject, Update

logger = logging.getLogger(__name__)


class ErrorMiddleware(BaseMiddleware):
    """Перехватывает все необработанные ошибки в хэндлерах."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                return  # игнорируем повторное редактирование
            logger.exception("Telegram API error")
        except Exception:
            logger.exception("Unhandled error in handler")
            # Попробуем отправить сообщение об ошибке
            try:
                if hasattr(event, "message") and event.message:
                    await event.message.answer(
                        "⚠️ Произошла ошибка. Попробуйте ещё раз или нажмите /start"
                    )
                elif hasattr(event, "answer"):
                    await event.answer(
                        "⚠️ Произошла ошибка", show_alert=True
                    )
            except Exception:
                pass
