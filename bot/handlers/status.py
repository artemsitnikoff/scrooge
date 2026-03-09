from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

import db
import keyboards

router = Router()


def _format_status(stats: list[dict], errors: list[dict]) -> str:
    if not stats:
        return "📭 У вас нет объектов. Добавьте объект через меню."

    parts = ["📊 Статус объектов:\n"]
    for s in stats:
        last = s["last_sent"][:16] if s["last_sent"] else "—"
        parts.append(
            f"🏭 {s['name']}\n"
            f"<pre>"
            f"┌───────────────┬────────┐\n"
            f"│ Отправлено    │ {s['sent']:>6} │\n"
            f"│ В очереди     │ {s['pending']:>6} │\n"
            f"│ Ошибок        │ {s['errors']:>6} │\n"
            f"│ Последняя     │ {last:>6} │\n"
            f"└───────────────┴────────┘"
            f"</pre>"
        )

    if errors:
        parts.append("\n❌ Последние ошибки:")
        for e in errors:
            ts = e["updated_at"][:16] if e["updated_at"] else ""
            parts.append(f"• {e['name']} ({ts})\n  {e['error']}")

    return "\n".join(parts)


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    stats = await db.get_queue_stats(message.from_user.id)
    errors = await db.get_recent_errors(message.from_user.id)
    await message.answer(
        _format_status(stats, errors),
        parse_mode=ParseMode.HTML,
        reply_markup=keyboards.main_menu(),
    )


@router.callback_query(F.data == "status")
async def cb_status(callback: CallbackQuery) -> None:
    stats = await db.get_queue_stats(callback.from_user.id)
    errors = await db.get_recent_errors(callback.from_user.id)
    await callback.message.answer(
        _format_status(stats, errors),
        parse_mode=ParseMode.HTML,
        reply_markup=keyboards.main_menu(),
    )
    await callback.answer()
