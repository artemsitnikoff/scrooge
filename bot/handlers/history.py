from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

import db
import keyboards

router = Router()


@router.callback_query(F.data == "history")
async def show_history(callback: CallbackQuery) -> None:
    items = await db.get_upload_history(callback.from_user.id, limit=10)

    if not items:
        await callback.message.answer(
            "📋 История отправок пуста.\n\nЗдесь будут отображаться все передачи данных в ФГИС УТКО.",
            reply_markup=keyboards.back_to_menu(),
        )
        await callback.answer()
        return

    text = "📋 **История отправок** (последние 10):\n\n"
    for item in items:
        status = "✅" if item["utko_success"] else "❌"
        source = "🤖" if item["source"] == "bot" else "🌐"
        date = item["created_at"][:16].replace("T", " ")
        text += (
            f"{status} {source} **{item['object_name']}**\n"
            f"   📅 {date} · 📄 {item['record_count']} зап."
        )
        if item["filename"]:
            text += f" · {item['filename']}"
        text += "\n\n"

    buttons = []
    for item in items[:5]:
        status = "✅" if item["utko_success"] else "❌"
        label = f"{status} {item['object_name']} ({item['record_count']} зап.)"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"history_detail:{item['id']}")])

    buttons.append([InlineKeyboardButton(text="↩️ Меню", callback_data="main_menu")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


@router.callback_query(F.data.startswith("history_detail:"))
async def history_detail(callback: CallbackQuery) -> None:
    history_id = int(callback.data.split(":")[1])
    item = await db.get_upload_history_detail(history_id, callback.from_user.id)

    if not item:
        await callback.answer("Запись не найдена", show_alert=True)
        return

    status = "✅ Успешно" if item["utko_success"] else "❌ Ошибка"
    source = "🤖 Бот" if item["source"] == "bot" else "🌐 Веб"
    date = item["created_at"][:16].replace("T", " ")

    text = (
        f"📋 **Детали отправки**\n\n"
        f"🏭 Объект: **{item['object_name']}**\n"
        f"📅 Дата: {date}\n"
        f"📄 Файл: {item['filename'] or '—'}\n"
        f"📊 Записей: {item['record_count']}\n"
        f"📍 Статус: {status}\n"
        f"📱 Источник: {source}\n"
    )

    # Показываем первые 5 записей
    records = item.get("records", [])
    if records:
        text += "\n**Данные:**\n"
        for i, rec in enumerate(records[:5], 1):
            plate = rec.get("registrationNumber", "—")
            weight = rec.get("garbageWeight", "—")
            text += f"  {i}. {plate} · {weight} кг\n"
        if len(records) > 5:
            text += f"  ...и ещё {len(records) - 5}\n"

    # Ответ УТКО (сокращённый)
    if item.get("utko_response"):
        resp = item["utko_response"][:500]
        text += f"\n**Ответ ФГИС УТКО:**\n`{resp}`"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="↩️ К истории", callback_data="history")],
        [InlineKeyboardButton(text="↩️ Меню", callback_data="main_menu")],
    ])

    await callback.message.answer(text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()
