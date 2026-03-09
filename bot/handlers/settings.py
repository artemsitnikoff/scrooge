import re

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

import db
import keyboards

router = Router()

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)


class Settings(StatesGroup):
    access_key = State()


@router.callback_query(F.data == "settings")
async def show_settings(callback: CallbackQuery) -> None:
    key = await db.get_access_key(callback.from_user.id)
    if key:
        masked = key[:8] + "..." + key[-4:]
        text = f"⚙️ Общие настройки\n\n🔑 Текущий ключ: {masked}"
    else:
        text = "⚙️ Общие настройки\n\n❌ Ключ доступа не установлен"
    await callback.message.answer(text, reply_markup=keyboards.settings_menu(has_key=bool(key)))
    await callback.answer()


@router.callback_query(F.data == "set_access_key")
async def start_set_key(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Settings.access_key)
    await callback.message.answer(
        "🔑 Введите ключ доступа от РЭО\n"
        "(формат: 550e8400-e29b-41d4-a716-446655440000):",
        reply_markup=keyboards.cancel(),
    )
    await callback.answer()


@router.message(Settings.access_key)
async def got_access_key(message: Message, state: FSMContext) -> None:
    val = message.text.strip()
    if not UUID_RE.match(val):
        await message.answer(
            "❌ Неверный формат ключа.\n"
            "Пример: 550e8400-e29b-41d4-a716-446655440000"
        )
        return
    await db.set_access_key(message.from_user.id, val)
    await state.clear()
    await message.answer(
        "✅ Ключ доступа сохранён.",
        reply_markup=keyboards.main_menu(),
    )


@router.callback_query(F.data == "delete_access_key")
async def delete_key(callback: CallbackQuery) -> None:
    await db.set_access_key(callback.from_user.id, None)
    await callback.message.answer(
        "🗑 Ключ доступа удалён.",
        reply_markup=keyboards.main_menu(),
    )
    await callback.answer()
