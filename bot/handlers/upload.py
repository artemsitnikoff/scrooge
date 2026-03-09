import os
import tempfile

from aiogram import Bot, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile, Message

import db
import keyboards
from services.file_parser import parse_file
from services.utko_client import UTKOClient

router = Router()

_EXAMPLE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "example.xlsx")


class Upload(StatesGroup):
    select_object = State()
    attach_file = State()
    confirm = State()


async def _send_example(message, text: str) -> None:
    """Отправить сообщение об ошибке + пример файла."""
    await message.answer(text)
    if os.path.exists(_EXAMPLE_PATH):
        await message.answer_document(
            FSInputFile(_EXAMPLE_PATH, filename="пример_весовой_контроль.xlsx"),
            caption="📎 Пример файла с правильными заголовками",
            reply_markup=keyboards.main_menu(),
        )


@router.callback_query(F.data == "upload_data")
async def start_upload(callback: CallbackQuery, state: FSMContext) -> None:
    key = await db.get_access_key(callback.from_user.id)
    if not key:
        await callback.answer(
            "⚠️ Сначала установите ключ доступа в Общих настройках", show_alert=True
        )
        return

    objects = await db.get_objects(callback.from_user.id)
    if not objects:
        await callback.message.answer(
            "📭 У вас нет объектов. Сначала добавьте объект.",
            reply_markup=keyboards.main_menu(),
        )
        await callback.answer()
        return

    if len(objects) == 1:
        await state.update_data(object_db_id=objects[0]["id"], object_name=objects[0]["name"])
        await state.set_state(Upload.attach_file)
        await callback.message.answer(
            f"🏭 Объект: «{objects[0]['name']}»\n\n📎 Прикрепите файл (.xlsx или .json):",
            reply_markup=keyboards.cancel(),
        )
    else:
        await state.set_state(Upload.select_object)
        await callback.message.answer(
            "Выберите объект:",
            reply_markup=keyboards.object_list(objects, "upload_obj"),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("upload_obj:"), Upload.select_object)
async def select_object(callback: CallbackQuery, state: FSMContext) -> None:
    pk = int(callback.data.split(":")[1])
    obj = await db.get_object(pk)
    if not obj:
        await callback.answer("Объект не найден", show_alert=True)
        return

    await state.update_data(object_db_id=pk, object_name=obj["name"])
    await state.set_state(Upload.attach_file)
    await callback.message.answer(
        f"🏭 Объект: «{obj['name']}»\n\n📎 Прикрепите файл (.xlsx или .json):",
        reply_markup=keyboards.cancel(),
    )
    await callback.answer()


@router.message(Upload.attach_file, F.document)
async def got_file(message: Message, state: FSMContext, bot: Bot) -> None:
    doc = message.document
    ext = os.path.splitext(doc.file_name or "")[1].lower()
    if ext not in (".xlsx", ".xls", ".json"):
        await message.answer("❌ Неподдерживаемый формат. Прикрепите .xlsx или .json файл.")
        return

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp_path = tmp.name

    try:
        await bot.download(doc, destination=tmp_path)
        valid_records, errors = parse_file(tmp_path)
    finally:
        os.unlink(tmp_path)

    if not valid_records and not errors:
        await _send_example(message, "📭 Файл пуст. Попробуйте другой файл.")
        return

    if not valid_records and errors:
        error_text = "\n".join(errors[:10])
        await _send_example(
            message,
            f"❌ Не найдено корректных записей.\n\nОшибки:\n{error_text}",
        )
        return

    await state.update_data(records=valid_records, error_count=len(errors))
    await state.set_state(Upload.confirm)

    data = await state.get_data()
    summary = f"🏭 Объект: «{data['object_name']}»\n\n"
    summary += f"📋 Записей: {len(valid_records)}\n"
    if errors:
        summary += f"⚠️ Ошибок: {len(errors)}\n"
        summary += "\n".join(errors[:5])
        if len(errors) > 5:
            summary += f"\n...и ещё {len(errors) - 5}"
        summary += "\n"
    summary += f"\n✅ Готово к отправке: {len(valid_records)}"

    await message.answer(summary, reply_markup=keyboards.confirm_send(len(valid_records)))


@router.message(Upload.attach_file)
async def no_file(message: Message) -> None:
    await message.answer("📎 Прикрепите файл (.xlsx или .json).")


@router.callback_query(F.data == "confirm_upload", Upload.confirm)
async def confirm_upload(
    callback: CallbackQuery, state: FSMContext, bot: Bot, utko_client: UTKOClient
) -> None:
    data = await state.get_data()
    records = data["records"]
    object_db_id = data["object_db_id"]
    await state.clear()

    obj = await db.get_object(object_db_id)
    access_key = await db.get_access_key(callback.from_user.id)

    sending_msg = await callback.message.answer(
        f"📡 Отправляем {len(records)} записей в ФГИС УТКО..."
    )

    success, message = await utko_client.send_records(
        obj["object_id"], access_key, records
    )

    await sending_msg.delete()

    if success:
        await callback.message.answer(
            f"✅ {len(records)} записей успешно отправлены в ФГИС УТКО!\n"
            f"🏭 Объект: «{obj['name']}»",
            reply_markup=keyboards.main_menu(),
        )
    else:
        await callback.message.answer(
            f"❌ Ошибка отправки в ФГИС УТКО\n\n"
            f"🏭 Объект: «{obj['name']}»\n"
            f"📋 Записей: {len(records)}\n"
            f"⚠️ {message}",
            reply_markup=keyboards.main_menu(),
        )
    await callback.answer()


@router.callback_query(F.data == "cancel_upload")
async def cancel_upload(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.answer("↩️ Загрузка отменена.", reply_markup=keyboards.main_menu())
    await callback.answer()
