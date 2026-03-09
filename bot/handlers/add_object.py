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


class AddObject(StatesGroup):
    object_id = State()
    name = State()


class RenameObject(StatesGroup):
    new_name = State()


# --- Список объектов ---

@router.callback_query(F.data == "objects")
async def show_objects(callback: CallbackQuery) -> None:
    objects = await db.get_objects(callback.from_user.id)
    if objects:
        text = f"🏭 Ваши объекты ({len(objects)}):"
    else:
        text = "📭 У вас пока нет объектов."
    await callback.message.answer(text, reply_markup=keyboards.objects_menu(objects))
    await callback.answer()


# --- Карточка объекта ---

@router.callback_query(F.data.startswith("obj_info:"))
async def show_object_info(callback: CallbackQuery) -> None:
    pk = int(callback.data.split(":")[1])
    obj = await db.get_object(pk)
    if not obj:
        await callback.answer("Объект не найден", show_alert=True)
        return
    text = (
        f"🏭 {obj['name']}\n\n"
        f"🔗 ID: {obj['object_id']}\n"
        f"📅 Добавлен: {obj['created_at']}"
    )
    await callback.message.answer(text, reply_markup=keyboards.object_card(pk))
    await callback.answer()


# --- Переименование ---

@router.callback_query(F.data.startswith("rename_obj:"))
async def start_rename(callback: CallbackQuery, state: FSMContext) -> None:
    pk = int(callback.data.split(":")[1])
    obj = await db.get_object(pk)
    if not obj:
        await callback.answer("Объект не найден", show_alert=True)
        return
    await state.set_state(RenameObject.new_name)
    await state.update_data(object_pk=pk)
    await callback.message.answer(
        f"✏️ Текущее название: «{obj['name']}»\n\n"
        "Введите новое название:",
        reply_markup=keyboards.cancel(),
    )
    await callback.answer()


@router.message(RenameObject.new_name)
async def got_new_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if not name:
        await message.answer("❌ Название не может быть пустым.")
        return
    data = await state.get_data()
    await db.rename_object(data["object_pk"], message.from_user.id, name)
    await state.clear()
    await message.answer(
        f"✅ Объект переименован в «{name}».",
        reply_markup=keyboards.main_menu(),
    )


# --- Добавление объекта ---

@router.callback_query(F.data == "add_object")
async def start_add(callback: CallbackQuery, state: FSMContext) -> None:
    key = await db.get_access_key(callback.from_user.id)
    if not key:
        await callback.answer(
            "⚠️ Сначала установите ключ доступа в Общих настройках", show_alert=True
        )
        return

    await state.set_state(AddObject.object_id)
    await callback.message.answer(
        "➕ Вставьте идентификатор объекта из ФГИС УТКО\n\n"
        "Его можно найти в личном кабинете ФГИС УТКО\n"
        "или в письме от ППК РЭО.",
        reply_markup=keyboards.cancel(),
    )
    await callback.answer()


@router.message(AddObject.object_id)
async def got_object_id(message: Message, state: FSMContext) -> None:
    val = message.text.strip()
    if not UUID_RE.match(val):
        await message.answer(
            "❌ Неверный формат.\n"
            "Идентификатор выглядит так:\n"
            "a6895e88-ed34-4ae0-829b-8f7dca4dbbec"
        )
        return
    await state.update_data(object_id=val)
    await state.set_state(AddObject.name)
    await message.answer(
        "📝 Введите название объекта\n"
        "(например, «Полигон Северный»)\n\n"
        "Или нажмите /skip чтобы пропустить.",
        reply_markup=keyboards.cancel(),
    )


@router.message(AddObject.name)
async def got_name(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if message.text.strip() == "/skip":
        name = data["object_id"][:8] + "..."
    else:
        name = message.text.strip()
        if not name:
            await message.answer("❌ Название не может быть пустым. Попробуйте ещё раз или /skip:")
            return

    await db.add_object(
        user_id=message.from_user.id,
        name=name,
        object_id=data["object_id"],
    )
    await state.clear()
    await message.answer(
        f"✅ Объект «{name}» добавлен.",
        reply_markup=keyboards.main_menu(),
    )


# --- Удаление объекта ---

@router.callback_query(F.data == "delete_objects")
async def show_delete_list(callback: CallbackQuery) -> None:
    objects = await db.get_objects(callback.from_user.id)
    if not objects:
        await callback.answer("📭 Нет объектов для удаления", show_alert=True)
        return
    await callback.message.answer(
        "🗑 Выберите объект для удаления:",
        reply_markup=keyboards.object_list(objects, "del_obj"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("del_obj:"))
async def confirm_delete(callback: CallbackQuery) -> None:
    pk = int(callback.data.split(":")[1])
    obj = await db.get_object(pk)
    if not obj:
        await callback.answer("Объект не найден", show_alert=True)
        return
    await callback.message.answer(
        f"❓ Удалить объект «{obj['name']}»?",
        reply_markup=keyboards.confirm_delete(pk),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_del:"))
async def do_delete(callback: CallbackQuery) -> None:
    pk = int(callback.data.split(":")[1])
    obj = await db.get_object(pk)
    deleted = await db.delete_object(pk, callback.from_user.id)
    if deleted:
        name = obj["name"] if obj else f"#{pk}"
        await callback.message.answer(
            f"🗑 Объект «{name}» удалён.",
            reply_markup=keyboards.main_menu(),
        )
    else:
        await callback.answer("Объект не найден", show_alert=True)
    await callback.answer()


# --- Отмена FSM ---

@router.callback_query(F.data == "cancel_fsm")
async def cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer(
        "↩️ Действие отменено.",
        reply_markup=keyboards.main_menu(),
    )
    await callback.answer()
